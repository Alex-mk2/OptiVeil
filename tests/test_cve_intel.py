"""Tests de inteligencia de CVEs (parser NVD) y priorización de hallazgos."""
import pytest

from inter.cve_intel import parse_nvd
from inter.IA_offensive import normalize_findings, finding_priority, enrich_and_prioritize


def _nvd(metric_key, score, severity):
    return {
        "vulnerabilities": [
            {"cve": {
                "id": "CVE-2021-1234",
                "descriptions": [{"lang": "en", "value": "demo"}],
                "metrics": {metric_key: [{"cvssData": {"baseScore": score, "baseSeverity": severity}}]},
            }}
        ]
    }


@pytest.mark.parametrize("key", ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"])
def test_parse_nvd_soporta_versiones_cvss(key):
    out = parse_nvd(_nvd(key, 9.8, "CRITICAL"))
    assert out[0]["id"] == "CVE-2021-1234"
    assert out[0]["score"] == 9.8
    assert out[0]["severity"] == "CRITICAL"


def test_parse_nvd_sin_metricas():
    data = {"vulnerabilities": [{"cve": {"id": "CVE-X", "descriptions": []}}]}
    out = parse_nvd(data)
    assert out[0]["score"] is None
    assert out[0]["severity"] == "UNKNOWN"


def test_parse_nvd_respeta_limit():
    data = {"vulnerabilities": [{"cve": {"id": f"CVE-{i}"}} for i in range(10)]}
    assert len(parse_nvd(data, limit=3)) == 3


def test_parse_nvd_vacio():
    assert parse_nvd({}) == []
    assert parse_nvd(None) == []


# --- normalize_findings ---

def test_normalize_findings_acepta_dicts_y_strings():
    out = normalize_findings([{"port": 22, "service": "ssh", "banner": "x", "risk": "HIGH (...)"},
                              "Puerto 80 http"])
    assert out[0]["service"] == "ssh"
    assert out[1]["banner"] == "Puerto 80 http"


# --- finding_priority ---

def test_priority_sube_con_cvss():
    f = {"risk": "MEDIUM (...)"}
    baja = finding_priority(f, [])
    alta = finding_priority(f, [{"score": 9.0}])
    assert alta > baja


def test_priority_riesgo_critico_pesa_mas_que_bajo():
    alto = finding_priority({"risk": "CRITICAL (...)"}, [])
    bajo = finding_priority({"risk": "LOW (...)"}, [])
    assert alto > bajo


# --- enrich_and_prioritize ---

def test_enrich_ordena_por_prioridad_desc_y_deduplica():
    findings = [
        {"port": 80, "service": "http", "banner": "nginx", "risk": "LOW (...)"},
        {"port": 445, "service": "smb", "banner": "samba", "risk": "CRITICAL (...)"},
        {"port": 139, "service": "smb", "banner": "samba", "risk": "CRITICAL (...)"},
    ]
    calls = []

    def fake_fetch(key, **kw):
        calls.append(key)
        return [{"id": "CVE-1", "score": 9.9}] if key == "samba" else []

    out = enrich_and_prioritize(findings, cve_fetcher=fake_fetch)
    # smb (crítico + CVSS alto) va primero
    assert out[0]["service"] == "smb"
    # 'samba' se consultó una sola vez pese a aparecer en dos hallazgos
    assert calls.count("samba") == 1
