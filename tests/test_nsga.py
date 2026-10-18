"""Tests del motor evolutivo: selección de config y función de fitness."""
import numpy as np
import pytest

from modules.stealth.nsga_II import (
    select_best_configuration,
    OptiVeilSthealthProblem,
)


@pytest.fixture
def sample_front():
    # F = [noise, time]. Ruidos distintos a propósito para ordenar sin ambigüedad.
    X = np.array([
        [1000.0, 200.0, 2.0],   # idx 0
        [4000.0, 500.0, 1.0],   # idx 1
        [2000.0, 300.0, 5.0],   # idx 2
    ])
    F = np.array([
        [5.0, 10.0],   # idx 0 noise=5
        [1.0, 40.0],   # idx 1 noise=1 (mínimo)
        [3.0, 20.0],   # idx 2 noise=3
    ])
    return X, F


def test_max_stealth_selecciona_menor_ruido(sample_front):
    X, F = sample_front
    out = select_best_configuration(X, F, stealth_level=10)
    assert out["config"]["metrics"]["noise_score"] == pytest.approx(F[:, 0].min())


def test_min_stealth_selecciona_mayor_ruido(sample_front):
    X, F = sample_front
    out = select_best_configuration(X, F, stealth_level=1)
    assert out["config"]["metrics"]["noise_score"] == pytest.approx(F[:, 0].max())


@pytest.mark.parametrize("nivel", [-5, 0, 50, 999])
def test_stealth_fuera_de_rango_se_clampa(sample_front, nivel):
    X, F = sample_front
    out = select_best_configuration(X, F, stealth_level=nivel)
    noise = out["config"]["metrics"]["noise_score"]
    assert F[:, 0].min() <= noise <= F[:, 0].max()


def test_config_tiene_tipos_correctos(sample_front):
    X, F = sample_front
    cfg = select_best_configuration(X, F, stealth_level=5)["config"]
    assert isinstance(cfg["wait_time_ms"], float)
    assert isinstance(cfg["packet_size"], int)
    assert isinstance(cfg["threads"], int)


def test_pareto_front_conserva_todas_las_soluciones(sample_front):
    X, F = sample_front
    out = select_best_configuration(X, F, stealth_level=5)
    assert len(out["pareto_front"]) == len(F)


# --- Función de fitness (regla de minimización) ---

def _evaluate(x, target_ports=100):
    problem = OptiVeilSthealthProblem(target_ports=target_ports)
    out = {}
    problem._evaluate(np.array(x, dtype=float), out)
    return out["F"]


def test_fitness_formula_base():
    ruido, tiempo = _evaluate([1000.0, 200.0, 10.0], target_ports=100)
    assert ruido == pytest.approx(10.0)   # (1000/1000)*10
    assert tiempo == pytest.approx(10.0)  # (100/10)*(1000/1000)


def test_paquete_pequeno_penaliza_ruido():
    ruido_grande, _ = _evaluate([1000.0, 200.0, 10.0])
    ruido_pequeno, _ = _evaluate([1000.0, 64.0, 10.0])
    assert ruido_pequeno == pytest.approx(ruido_grande * 1.5)


def test_mas_espera_reduce_ruido():
    ruido_rapido, _ = _evaluate([500.0, 200.0, 10.0])
    ruido_lento, _ = _evaluate([2000.0, 200.0, 10.0])
    assert ruido_lento < ruido_rapido
