"""Tests de la validación no destructiva (SPEC-0002).

Nunca ejecutan nuclei ni tocan la red: el runner/validator se inyecta. El gating
de scope se prueba contra `enforce_scope` real, con `load_scope` mockeado para
que el resultado no dependa del entorno ni de un scope.txt local.
"""
import json

import pytest
from fastapi.testclient import TestClient

from inter.validator import (
    NucleiValidator, Validator, ValidatorUnavailable, validate_findings,
    redact_snippet, CONFIRMED, LIKELY, NOT_CONFIRMED, NOT_TESTED,
)
from src.core import scope as scope_mod
from src.api.main import app
from src.api.routers import validation as validation_router


# --- redact_snippet ---

def test_redact_enmascara_secretos():
    out = redact_snippet('password: hunter2 y token=abc.def.ghi')
    assert "hunter2" not in out
    assert "abc.def.ghi" not in out
    assert "[REDACTADO]" in out


def test_redact_trunca_largo():
    out = redact_snippet("A" * 500, max_len=100)
    assert len(out) <= 120
    assert out.endswith("[truncado]")


def test_redact_vacio():
    assert redact_snippet("") == ""
    assert redact_snippet(None) == ""


# --- NucleiValidator con runner inyectado (sin red) ---

def _finding(port=80, service="http", banner="nginx"):
    return {"port": port, "service": service, "banner": banner}


def test_match_directo_es_confirmed():
    linea = json.dumps({
        "port": 80, "matched-at": "10.0.0.1:80",
        "template-id": "exposed-config",
        "info": {"severity": "high", "tags": ["exposure"], "name": "Config expuesta"},
        "curl-command": "curl -s http://10.0.0.1/.env",
        "extracted-results": ["DB_PASSWORD=secreto"],
    })
    v = NucleiValidator(runner=lambda target: linea)
    out = v.validate("10.0.0.1", [_finding()])
    assert out[0]["status"] == CONFIRMED
    assert out[0]["evidence"]["reproduce"].startswith("curl")
    assert out[0]["evidence"]["template"] == "exposed-config"
    # La evidencia va redactada: no se filtra el secreto extraído.
    assert "secreto" not in out[0]["evidence"]["snippet"]


def test_match_por_version_es_likely():
    linea = json.dumps({
        "port": 80, "matched-at": "10.0.0.1:80", "template-id": "nginx-version",
        "info": {"severity": "info", "tags": ["version", "tech"], "name": "nginx"},
    })
    v = NucleiValidator(runner=lambda target: linea)
    out = v.validate("10.0.0.1", [_finding()])
    assert out[0]["status"] == LIKELY


def test_sin_match_es_not_confirmed():
    v = NucleiValidator(runner=lambda target: "")  # nuclei no reportó nada
    out = v.validate("10.0.0.1", [_finding()])
    assert out[0]["status"] == NOT_CONFIRMED


def test_backend_ausente_degrada_a_not_tested():
    def _raise(target):
        raise ValidatorUnavailable("nuclei no está")
    v = NucleiValidator(runner=_raise)
    out = v.validate("10.0.0.1", [_finding(), _finding(443, "https")])
    assert all(r["status"] == NOT_TESTED for r in out)


def test_parse_ignora_lineas_no_json():
    raw = 'basura no json\n{"port":80,"matched-at":"10.0.0.1:80","info":{}}\nmás basura'
    matches = NucleiValidator._parse(raw)
    assert len(matches) == 1
    assert matches[0]["port"] == 80


def test_fallo_inesperado_del_backend_no_rompe():
    def _boom(target):
        raise RuntimeError("explotó algo raro")
    out = NucleiValidator(runner=_boom).validate("10.0.0.1", [_finding()])
    assert out[0]["status"] == NOT_TESTED


# --- Gating de scope ESTRICTO en el endpoint ---

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _body(target="10.0.0.1"):
    return {"target": target, "findings": [{"port": 80, "service": "http", "banner": "nginx"}]}


def test_validate_sin_scope_estricto_rechaza_403(client, monkeypatch):
    monkeypatch.setattr(scope_mod, "load_scope", lambda: [])  # sin scope definido
    r = client.post("/api/validate", json=_body())
    assert r.status_code == 403


def test_validate_fuera_de_scope_rechaza_403(client, monkeypatch):
    monkeypatch.setattr(scope_mod, "load_scope", lambda: ["10.0.0.2"])
    r = client.post("/api/validate", json=_body("10.0.0.1"))
    assert r.status_code == 403


def test_validate_en_scope_ok(client, monkeypatch):
    monkeypatch.setattr(scope_mod, "load_scope", lambda: ["10.0.0.1"])
    fake = [{"port": 80, "service": "http", "status": CONFIRMED,
             "evidence": {"reproduce": "curl ...", "snippet": "", "template": "t"}, "source": "nuclei"}]
    monkeypatch.setattr(validation_router, "validate_findings", lambda t, f: fake)
    r = client.post("/api/validate", json=_body("10.0.0.1"))
    assert r.status_code == 200
    assert r.json() == {"results": fake}


# --- validate_findings: inyección del validador ---

def test_validate_findings_usa_validador_inyectado():
    class _Fake(Validator):
        def validate(self, target, findings):
            return [{"port": f["port"], "status": CONFIRMED} for f in findings]

    out = validate_findings("10.0.0.1", [_finding()], validator=_Fake())
    assert out[0]["status"] == CONFIRMED
