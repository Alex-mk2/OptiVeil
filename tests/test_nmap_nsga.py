"""SPEC-0005: /api/nmap deriva su timing de NSGA-II (no de presets -T).

Se mockea el motor (config determinista) y `subprocess.run` (captura el argv sin
tocar la red). El scope se fija a 10.0.0.0/8 para que el target pase enforce_scope
sin depender del .env del desarrollador.
"""
import pytest
from fastapi.testclient import TestClient

import src.api.routers.scanner as scanner_mod
from src.api.main import app


class _FakeProc:
    stdout = "<nmaprun></nmaprun>"


@pytest.fixture
def captura_nmap(monkeypatch):
    """Mockea NSGA-II + subprocess.run. Devuelve el dict donde cae el argv."""
    comando = {}

    monkeypatch.setattr(scanner_mod, "run_nsga_ii", lambda target_ports: ("X", "F"))

    def _fake_select(X, F, stealth_level):
        return {"config": {
            "wait_time_ms": 250.6, "packet_size": 512, "threads": 3,
            "metrics": {"noise_score": 1.23, "estimated_time_sec": 4.5},
        }}

    monkeypatch.setattr(scanner_mod, "select_best_configuration", _fake_select)

    def _fake_run(cmd, *a, **k):
        comando["argv"] = cmd
        return _FakeProc()

    monkeypatch.setattr(scanner_mod.subprocess, "run", _fake_run)
    monkeypatch.setenv("OPTIVEIL_SCOPE", "10.0.0.0/8")
    return comando


def test_nmap_mapea_config_nsga_a_flags(captura_nmap):
    with TestClient(app) as c:
        r = c.post("/api/nmap", json={"target": "10.0.0.5", "stealth": 7, "ports": 100})
    assert r.status_code == 200
    argv = captura_nmap["argv"]
    # los tres parámetros del motor, mapeados a los flags equivalentes de nmap
    assert argv[argv.index("--scan-delay") + 1] == "251ms"      # round(250.6)
    assert argv[argv.index("--max-parallelism") + 1] == "3"     # threads
    assert argv[argv.index("--data-length") + 1] == "512"       # packet_size


def test_nmap_sin_presets_de_timing(captura_nmap):
    with TestClient(app) as c:
        r = c.post("/api/nmap", json={"target": "10.0.0.5", "stealth": 9, "ports": 100})
    assert r.status_code == 200
    argv = captura_nmap["argv"]
    assert not any(t in argv for t in ("-T0", "-T1", "-T2", "-T3", "-T4", "-T5"))


def test_nmap_respuesta_incluye_config_nsga(captura_nmap):
    with TestClient(app) as c:
        r = c.post("/api/nmap", json={"target": "10.0.0.5", "stealth": 5, "ports": 100})
    cfg = r.json()["nsga_config"]
    assert cfg["scan_delay_ms"] == 251
    assert cfg["max_parallelism"] == 3
    assert cfg["data_length"] == 512
    assert cfg["noise_score"] == 1.23


def test_nmap_reenvia_puertos_y_stealth_al_motor(monkeypatch):
    """El router pasa el nº de puertos a run_nsga_ii y el stealth a la selección."""
    visto = {}

    def _run(target_ports):
        visto["ports"] = target_ports
        return ("X", "F")

    def _sel(X, F, stealth_level):
        visto["stealth"] = stealth_level
        return {"config": {"wait_time_ms": 10.0, "packet_size": 64, "threads": 1,
                           "metrics": {"noise_score": 0.0, "estimated_time_sec": 0.0}}}

    monkeypatch.setattr(scanner_mod, "run_nsga_ii", _run)
    monkeypatch.setattr(scanner_mod, "select_best_configuration", _sel)
    monkeypatch.setattr(scanner_mod.subprocess, "run", lambda *a, **k: _FakeProc())
    monkeypatch.setenv("OPTIVEIL_SCOPE", "10.0.0.0/8")

    with TestClient(app) as c:
        c.post("/api/nmap", json={"target": "10.0.0.5", "stealth": 8, "ports": 100})
    assert visto["ports"] == 100
    assert visto["stealth"] == 8


def test_nmap_fuera_de_scope_no_calcula_nsga(monkeypatch):
    """enforce_scope corta antes de invocar al motor y a nmap (regresión SPEC-0004)."""
    def _no_llamar(*a, **k):
        raise AssertionError("no debe calcularse NSGA ni ejecutarse nmap fuera de scope")

    monkeypatch.setattr(scanner_mod, "run_nsga_ii", _no_llamar)
    monkeypatch.setattr(scanner_mod.subprocess, "run", _no_llamar)
    monkeypatch.setenv("OPTIVEIL_SCOPE", "10.0.0.0/8")

    with TestClient(app) as c:
        r = c.post("/api/nmap", json={"target": "8.8.8.8", "stealth": 5, "ports": 100})
    assert r.status_code == 403
