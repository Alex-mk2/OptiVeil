"""Inteligencia de CVEs vía NVD (NIST).

Extrae la consulta a la API del NVD a una función reutilizable para que tanto
el endpoint `/cve` como el estratega ofensivo la compartan. El parseo es una
función pura (testeable sin red).
"""
import logging

import requests

logger = logging.getLogger("optiveil.cve")

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def parse_nvd(data: dict, limit: int = 5) -> list[dict]:
    """Normaliza la respuesta del NVD a una lista de CVEs resumidos.

    Soporta CVSS v3.1, v3.0 y v2 (en ese orden de preferencia). Función pura.
    """
    out = []
    for item in (data or {}).get("vulnerabilities", [])[:limit]:
        cve = item.get("cve", {})
        descs = cve.get("descriptions", [])
        descripcion = next(
            (d.get("value") for d in descs if d.get("lang") == "en"),
            descs[0].get("value") if descs else "Sin descripción",
        )
        metrics = cve.get("metrics", {})
        score, severity = None, "UNKNOWN"
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if metrics.get(key):
                cvss = metrics[key][0].get("cvssData", {})
                score = cvss.get("baseScore")
                severity = cvss.get("baseSeverity") or metrics[key][0].get("baseSeverity", "UNKNOWN")
                break
        out.append({
            "id": cve.get("id", "Desconocido"),
            "description": descripcion,
            "score": score,
            "severity": severity,
        })
    return out


def fetch_cves(service_banner: str, timeout: int = 15, limit: int = 5) -> list[dict]:
    """Consulta el NVD por un banner de servicio. Devuelve [] ante fallo o vacío.

    No lanza: el estratega debe poder seguir aunque el NVD esté caído.
    """
    if not service_banner or not service_banner.strip():
        return []
    try:
        resp = requests.get(
            NVD_URL,
            params={"keywordSearch": service_banner, "resultsPerPage": limit},
            timeout=timeout,
        )
        resp.raise_for_status()
        return parse_nvd(resp.json(), limit=limit)
    except Exception as e:
        logger.warning("Fallo al consultar NVD para '%s': %s", service_banner, e)
        return []
