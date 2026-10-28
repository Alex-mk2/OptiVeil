"""SPEC-0006: Frente de Pareto interactivo.

Cubre el endpoint `GET /api/strategy/pareto` (frente con la config de cada punto,
sin tocar ningún target), los helpers de solo lectura del motor y la consistencia
entre los rangos de `ScanConfig` (API) y `CONFIG_BOUNDS` (motor). NSGA-II se
mockea donde haría falta correrlo, así los tests son rápidos y deterministas.
"""
import numpy as np
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

import src.api.routers.strategy as strategy_mod
from src.api.main import app
from src.api.schemas import ScanConfig
from modules.stealth.nsga_II import (
    pareto_front_with_configs,
    metrics_for_config,
    CONFIG_BOUNDS,
)


# Frente determinista: X = [wait_time_ms, packet_size, threads], F = [noise, time].
# Ruidos distintos a propósito para ordenar sin ambigüedad.
_X = np.array([
    [1000.0, 256.0, 4.0],   # idx 0 noise=2
    [2000.0, 128.0, 2.0],   # idx 1 noise=1 (mínimo)
    [500.0, 512.0, 8.0],    # idx 2 noise=5
])
_F = np.array([
    [2.0, 10.0],
    [1.0, 20.0],
    [5.0, 4.0],
])


# --- Helpers del motor (solo lectura) ---

def test_pareto_front_with_configs_ordena_y_adjunta_config():
    pts = pareto_front_with_configs(_X, _F)
    assert len(pts) == len(_F)
    noises = [p["noise"] for p in pts]
    assert noises == sorted(noises)                       # ordenado por ruido asc
    assert pts[0]["noise"] == pytest.approx(_F[:, 0].min())
    cfg = pts[0]["config"]
    assert set(cfg) == {"wait_time_ms", "packet_size", "threads"}
    assert isinstance(cfg["packet_size"], int) and isinstance(cfg["threads"], int)
    assert "index" in pts[0] and "time" in pts[0]


def test_metrics_for_config_usa_la_formula_del_problema():
    # Mismos valores que test_fitness_formula_base en test_nsga.py.
    m = metrics_for_config({"wait_time_ms": 1000.0, "packet_size": 200, "threads": 10}, 100)
    assert m["noise_score"] == pytest.approx(10.0)
    assert m["estimated_time_sec"] == pytest.approx(10.0)


# --- Consistencia API <-> motor (evita deriva de rangos) ---

def test_scanconfig_bounds_espejo_de_config_bounds():
    base = {"wait_time_ms": 100, "packet_size": 256, "threads": 4}
    for field, (lo, hi) in CONFIG_BOUNDS.items():
        ScanConfig(**{**base, field: lo})   # borde inferior: válido
        ScanConfig(**{**base, field: hi})   # borde superior: válido
        with pytest.raises(ValidationError):
            ScanConfig(**{**base, field: lo - 1})
        with pytest.raises(ValidationError):
            ScanConfig(**{**base, field: hi + 1})


# --- Endpoint del frente ---

def test_pareto_endpoint_devuelve_frente_con_config(monkeypatch):
    monkeypatch.setattr(strategy_mod, "run_nsga_ii", lambda target_ports: (_X, _F))
    with TestClient(app) as c:
        r = c.get("/api/strategy/pareto", params={"ports": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["ports"] == 50
    front = body["pareto_front"]
    assert len(front) == 3
    noises = [p["noise"] for p in front]
    assert noises == sorted(noises)
    assert noises[0] == pytest.approx(1.0)
    p0 = front[0]
    assert set(p0["config"]) == {"wait_time_ms", "packet_size", "threads"}


@pytest.mark.parametrize("ports", [0, -1, 70000])
def test_pareto_ports_invalido_422(ports):
    # La validación de Query (ge=1, le=65535) corta antes del handler: no corre NSGA.
    with TestClient(app) as c:
        r = c.get("/api/strategy/pareto", params={"ports": ports})
    assert r.status_code == 422
