"""Tests del módulo ofensivo: extracción/validación de la hoja de ruta y endpoints."""
import json

import pytest
from fastapi.testclient import TestClient

from inter.IA_offensive import extract_json_block, parse_roadmap, generate_attack_path
from inter import IA_offensive
from src.api.schemas import normalize_risk, AttackStep
from src.api.main import app
from src.api.routers import strategy as strategy_router


@pytest.fixture(autouse=True)
def _reset_structured_cache():
    """Resetea el cache de capacidad de structured output entre tests."""
    IA_offensive._structured_supported = None
    yield
    IA_offensive._structured_supported = None


# --- extract_json_block ---

def test_extrae_json_plano():
    assert json.loads(extract_json_block('{"steps": []}')) == {"steps": []}


def test_extrae_json_con_fence():
    out = extract_json_block('```json\n{"steps": [1]}\n```')
    assert json.loads(out) == {"steps": [1]}


def test_extrae_json_con_prosa_alrededor():
    txt = 'Aquí tienes:\n```json\n{"a": 1}\n```\nEspero que ayude.'
    assert json.loads(extract_json_block(txt)) == {"a": 1}


def test_extrae_json_anidado_y_con_llaves_en_strings():
    txt = '{"k": "valor con } llave", "nested": {"x": 1}}'
    assert json.loads(extract_json_block(txt)) == {"k": "valor con } llave", "nested": {"x": 1}}


def test_sin_json_lanza_error():
    with pytest.raises(ValueError):
        extract_json_block("no hay json aquí")


def test_json_incompleto_lanza_error():
    with pytest.raises(ValueError):
        extract_json_block('{"steps": [')


# --- normalize_risk / schema ---

@pytest.mark.parametrize("entrada,esperado", [
    ("high", "alto"), ("ALTO", "alto"), ("critical", "alto"),
    ("medium", "medio"), ("moderado", "medio"),
    ("low", "bajo"), ("info", "bajo"),
    ("desconocido", "medio"), (None, "medio"),
])
def test_normalize_risk(entrada, esperado):
    assert normalize_risk(entrada) == esperado


def test_attackstep_normaliza_y_rellena_defaults():
    s = AttackStep(id=1, phase="Recon", action="scan", risk="HIGH")
    assert s.risk == "alto"
    assert s.justification == ""


# --- parse_roadmap ---

def test_parse_roadmap_valida_y_normaliza():
    raw = '{"steps":[{"id":1,"phase":"Recon","action":"x","risk":"high","justification":"y"}]}'
    out = parse_roadmap(raw)
    assert out["steps"][0]["risk"] == "alto"


def test_parse_roadmap_json_invalido_lanza():
    with pytest.raises(Exception):
        parse_roadmap("esto no es json")


# --- generate_attack_path con LLM mockeado ---

class _FakeMsg:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    """LLM falso sin structured output: fuerza el camino de parseo manual."""
    def __init__(self, content):
        self._content = content

    def invoke(self, _messages):
        return _FakeMsg(self._content)


class _StructuredRunnable:
    def __init__(self, obj):
        self._obj = obj

    def invoke(self, _messages):
        return self._obj


class _FakeStructuredLLM:
    """LLM falso que SÍ soporta with_structured_output (devuelve el modelo)."""
    def __init__(self, obj):
        self._obj = obj

    def with_structured_output(self, _schema):
        return _StructuredRunnable(self._obj)

    def invoke(self, _messages):  # no debería llamarse en el camino estructurado
        raise AssertionError("no debería usar invoke crudo cuando hay structured output")


# cve_fetcher falso para no tocar red en los tests.
_NO_CVES = lambda *a, **k: []


def test_generate_attack_path_exito(monkeypatch):
    content = ('{"steps":[{"id":1,"phase":"Recon","action":"enum","risk":"medium",'
               '"justification":"base","mitre_technique":"T1046"}]}')
    monkeypatch.setattr(IA_offensive, "build_llm", lambda **kw: _FakeLLM(content))
    out = generate_attack_path([{"port": 22, "service": "ssh", "banner": "OpenSSH"}],
                               noise_score=3.0, cve_fetcher=_NO_CVES)
    assert out["steps"][0]["phase"] == "Recon"
    assert out["steps"][0]["risk"] == "medio"
    assert out["steps"][0]["mitre_technique"] == "T1046"
    assert "prioritized_findings" in out


class _CountingLLM:
    """Cuenta intentos de structured output (que fallan) e invokes crudos."""
    def __init__(self, content):
        self._content = content
        self.structured_calls = 0
        self.invoke_calls = 0

    def with_structured_output(self, _schema):
        self.structured_calls += 1
        raise RuntimeError("structured output no soportado")

    def invoke(self, _messages):
        self.invoke_calls += 1
        return _FakeMsg(self._content)


def test_structured_output_se_cachea_tras_fallo():
    content = '{"steps":[{"id":1,"phase":"R","action":"a","risk":"bajo","justification":"j"}]}'
    llm = _CountingLLM(content)

    IA_offensive._roadmap_from_llm(llm, [])
    assert IA_offensive._structured_supported is False
    assert llm.structured_calls == 1
    assert llm.invoke_calls == 1

    # Segunda petición: ya NO reintenta el camino estructurado (evita doble gen).
    IA_offensive._roadmap_from_llm(llm, [])
    assert llm.structured_calls == 1  # sin incremento
    assert llm.invoke_calls == 2


def test_generate_attack_path_structured_output(monkeypatch):
    from src.api.schemas import AttackRoadmap
    rm = AttackRoadmap.model_validate({"steps": [
        {"id": 1, "phase": "Explotación", "action": "exploit", "risk": "high",
         "justification": "cve", "mitre_technique": "T1190", "cve_refs": ["CVE-2021-1"]}
    ]})
    monkeypatch.setattr(IA_offensive, "build_llm", lambda **kw: _FakeStructuredLLM(rm))
    out = generate_attack_path([{"port": 80, "service": "http", "banner": "nginx"}],
                               noise_score=2.0, cve_fetcher=_NO_CVES)
    assert out["steps"][0]["mitre_technique"] == "T1190"
    assert out["steps"][0]["cve_refs"] == ["CVE-2021-1"]
    assert out["steps"][0]["risk"] == "alto"


def test_generate_attack_path_json_malo_devuelve_fallback(monkeypatch):
    monkeypatch.setattr(IA_offensive, "build_llm", lambda **kw: _FakeLLM("lo siento, no puedo"))
    out = generate_attack_path([], noise_score=5.0, cve_fetcher=_NO_CVES)
    assert out["steps"][0]["phase"] == "Error de Parseo"


def test_generate_attack_path_sin_token_devuelve_fallback(monkeypatch):
    from inter.llm_config import LLMConfigError

    def _raise(**kw):
        raise LLMConfigError("sin token")

    monkeypatch.setattr(IA_offensive, "build_llm", _raise)
    out = generate_attack_path([], noise_score=5.0, cve_fetcher=_NO_CVES)
    assert "Configuración" in out["steps"][0]["phase"]


# --- Endpoints ---

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_strategy_live_usa_motor_mockeado(client, monkeypatch):
    fake = {"steps": [{"id": 1, "phase": "Recon", "action": "x", "risk": "alto", "justification": "y"}]}
    monkeypatch.setattr(strategy_router, "generate_attack_path", lambda h, n: fake)
    r = client.post("/api/strategy/live", json={
        "target": "10.0.0.1", "stealth": 7,
        "findings": [{"port": 22, "service": "ssh", "banner": "OpenSSH"}],
    })
    assert r.status_code == 200
    assert r.json() == fake


def test_strategy_get_inexistente_404(client):
    r = client.get("/api/strategy/203.0.113.77")
    assert r.status_code == 404
