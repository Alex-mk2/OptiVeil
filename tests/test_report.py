"""Tests del renderizador Markdown de la hoja de ruta de ataque."""
from utils.generate_report import render_roadmap_markdown


def test_roadmap_vacio_devuelve_cadena_vacia():
    assert render_roadmap_markdown({}) == ""
    assert render_roadmap_markdown({"steps": []}) == ""


def test_roadmap_completo_incluye_campos_purple():
    roadmap = {
        "steps": [{
            "id": 1, "phase": "Explotación", "action": "exploit SMB",
            "risk": "alto", "justification": "RCE conocida",
            "mitre_technique": "T1210", "cve_refs": ["CVE-2017-0144"],
            "detection": "IDS firma EternalBlue", "mitigation": "Parchear MS17-010",
        }],
        "prioritized_findings": [
            {"port": 445, "service": "smb", "risk": "CRITICAL (...)",
             "priority": 98.3, "cves": [{"id": "CVE-2017-0144"}]}
        ],
    }
    md = render_roadmap_markdown(roadmap)
    assert "## 🎯 Ruta de Ataque" in md
    assert "T1210" in md
    assert "CVE-2017-0144" in md
    assert "Detección (Blue Team)" in md
    assert "Mitigación" in md
    assert "Hallazgos priorizados" in md
    assert "98.3" in md


def test_roadmap_sin_campos_opcionales_no_rompe():
    roadmap = {"steps": [{"id": 1, "phase": "Recon", "action": "scan", "risk": "medio"}]}
    md = render_roadmap_markdown(roadmap)
    assert "Fase 1: Recon" in md
    assert "MITRE" not in md  # no se añade si no hay técnica
