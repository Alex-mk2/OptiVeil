"""SPEC-0007: búsqueda de rutas que exponen info sensible + veredicto enriquecido.

Nunca toca la red: el fetcher HTTP y el runner de nuclei se inyectan.
"""
import json

import pytest
from fastapi.testclient import TestClient

from inter.exposure import SensitiveRouteValidator
from inter.validator import NucleiValidator, CONFIRMED, LIKELY
from src.core import scope as scope_mod
from src.api.main import app
from src.api.routers import validation as validation_router

RUT_VALIDO = "12.345.678-5"


def _http_finding(port=80, service="http"):
    return {"port": port, "service": service, "banner": ""}


# --- SensitiveRouteValidator (fetcher mockeado) ---

def test_ruta_con_rut_es_confirmed_y_redactada():
    def fetcher(url, timeout):
        return (200, f"cliente rut {RUT_VALIDO}") if url.endswith("/.env") else (404, "")
    out = SensitiveRouteValidator(fetcher=fetcher).validate("10.0.0.1", [_http_finding()])
    assert len(out) == 1
    r = out[0]
    assert r["status"] == CONFIRMED
    assert r["vuln_class"] == "exposición de datos sensibles"
    assert r["location"].endswith("/.env")
    dump = json.dumps(r, ensure_ascii=False)
    assert "12345678" not in dump and "12.345.678" not in dump  # evidencia redactada


def test_404_no_genera_hallazgo():
    out = SensitiveRouteValidator(fetcher=lambda u, t: (404, "")).validate("10.0.0.1", [_http_finding()])
    assert out == []


def test_rut_invalido_no_dispara():
    out = SensitiveRouteValidator(fetcher=lambda u, t: (200, "rut 12.345.678-9")).validate(
        "10.0.0.1", [_http_finding()])
    assert out == []


def test_redirect_no_es_hallazgo():
    out = SensitiveRouteValidator(fetcher=lambda u, t: (302, "Location: http://evil.test")).validate(
        "10.0.0.1", [_http_finding()])
    assert out == []


def test_solo_consulta_el_host_objetivo():
    urls = []
    def fetcher(url, timeout):
        urls.append(url)
        return (404, "")
    SensitiveRouteValidator(fetcher=fetcher, paths=["/.env", "/config.json"]).validate(
        "10.0.0.1", [_http_finding()])
    assert urls and all(u.startswith("http://10.0.0.1") for u in urls)


def test_finding_no_http_se_omite():
    calls = []
    def fetcher(url, timeout):
        calls.append(url)
        return (200, RUT_VALIDO)
    out = SensitiveRouteValidator(fetcher=fetcher).validate(
        "10.0.0.1", [{"port": 22, "service": "ssh", "banner": ""}])
    assert out == [] and calls == []


def test_fetcher_error_no_rompe():
    def fetcher(url, timeout):
        raise RuntimeError("boom")
    out = SensitiveRouteValidator(fetcher=fetcher, paths=["/.env"]).validate("10.0.0.1", [_http_finding()])
    assert out == []


# --- Reclasificación y enriquecimiento del veredicto (nuclei) ---

def _nuclei(obj):
    return NucleiValidator(runner=lambda target, tags: json.dumps(obj))


def test_cve_sin_contenido_es_likely():
    r = _nuclei({
        "port": 80, "matched-at": "10.0.0.1:80/x", "template-id": "cve-2021-1",
        "info": {"severity": "high", "tags": ["cve"], "name": "Algún CVE"},
    }).validate("10.0.0.1", [_http_finding()])[0]
    assert r["status"] == LIKELY
    assert r["severity"] == "high"
    assert r["location"] == "10.0.0.1:80/x"
    assert r["vuln_class"] == "cve"


def test_contenido_observado_es_confirmed():
    r = _nuclei({
        "port": 80, "matched-at": "10.0.0.1:80/panel", "template-id": "exposed",
        "info": {"severity": "medium", "tags": ["exposure"], "name": "Expuesto"},
        "extracted-results": ["contenido real observado"],
    }).validate("10.0.0.1", [_http_finding()])[0]
    assert r["status"] == CONFIRMED
    assert r["vuln_class"] == "exposición"
    assert r["location"] == "10.0.0.1:80/panel"


def test_pii_en_contenido_nuclei_es_datos_sensibles():
    r = _nuclei({
        "port": 80, "matched-at": "10.0.0.1:80/api", "template-id": "generic",
        "info": {"severity": "info", "tags": ["exposure"], "name": "x"},
        "extracted-results": [f"rut {RUT_VALIDO}"],
    }).validate("10.0.0.1", [_http_finding()])[0]
    assert r["status"] == CONFIRMED
    assert r["vuln_class"] == "exposición de datos sensibles"
    assert "12345678" not in json.dumps(r, ensure_ascii=False)


def test_severidad_desconocida_no_rompe():
    r = _nuclei({
        "port": 80, "matched-at": "10.0.0.1:80", "template-id": "t",
        "info": {"tags": ["exposure"], "name": "x"},  # sin severity
        "extracted-results": ["algo"],
    }).validate("10.0.0.1", [_http_finding()])[0]
    assert r["severity"] == "unknown"


# --- Endpoint /api/validate: fusiona backends y respeta el scope ---

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_validate_fusiona_ambos_backends(client, monkeypatch):
    monkeypatch.setattr(scope_mod, "load_scope", lambda: ["10.0.0.1"])
    monkeypatch.setattr(validation_router, "validate_findings",
                        lambda t, f: [{"port": 80, "source": "nuclei", "status": "likely"}])
    monkeypatch.setattr(validation_router, "find_exposed_routes",
                        lambda t, f: [{"port": 80, "source": "sensitive-route", "status": "confirmed"}])
    r = client.post("/api/validate", json={
        "target": "10.0.0.1", "findings": [{"port": 80, "service": "http", "banner": ""}]})
    assert r.status_code == 200
    assert {x["source"] for x in r.json()["results"]} == {"nuclei", "sensitive-route"}


def test_scope_bloquea_antes_de_cualquier_backend(client, monkeypatch):
    monkeypatch.setattr(scope_mod, "load_scope", lambda: ["10.0.0.2"])  # target fuera de scope
    tocado = {"v": False}
    def _spy(t, f):
        tocado["v"] = True
        return []
    monkeypatch.setattr(validation_router, "validate_findings", _spy)
    monkeypatch.setattr(validation_router, "find_exposed_routes", _spy)
    r = client.post("/api/validate", json={
        "target": "10.0.0.1", "findings": [{"port": 80, "service": "http", "banner": ""}]})
    assert r.status_code == 403
    assert tocado["v"] is False  # ni GET ni nuclei: se cortó en el scope
