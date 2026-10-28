"""Backend de validación por exposición de rutas (SPEC-0007).

Busca, de forma NO destructiva, rutas HTTP que filtran información sensible:
hace GET benignos a una lista curada de rutas de alto valor y pasa cada respuesta
por el matcher de datos sensibles. Encuentra y reporta con evidencia redactada;
NO explota, NO autentica, NO usa métodos distintos de GET, NO sigue redirecciones
fuera del host. El gating de autorización (scope estricto) vive en el router.
"""
from __future__ import annotations

import logging
import os
import ssl
import urllib.error
import urllib.request

from src.inter.validator import Validator, _result, redact_snippet, CONFIRMED
from src.inter.sensitive_data import find_sensitive

logger = logging.getLogger("optiveil.exposure")

# Servicios/puertos considerados HTTP(S). El resto de hallazgos se ignoran.
_HTTP_SERVICES = {"http", "https", "http-proxy", "https-alt", "http-alt", "www", "http-mgmt"}
_HTTP_PORTS = {80, 443, 3000, 5000, 8000, 8008, 8080, 8081, 8088, 8443, 8888, 9000}
_HTTPS_PORTS = {443, 8443}

_MAX_BODY = 200_000  # bytes de respuesta que leemos (cap de memoria)

_PATHS_FILE = os.path.join(os.path.dirname(__file__), "data", "sensitive_paths.txt")


def _load_paths() -> list[str]:
    with open(_PATHS_FILE, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip() and not ln.strip().startswith("#")]


SENSITIVE_PATHS = _load_paths()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """No seguir redirecciones: evita saltar a otro host (3xx se trata como error)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_fetch(url: str, timeout: float):
    """GET no destructivo. Devuelve (status, body) o None si falla. Sin redirecciones.

    TLS sin verificar a propósito: los objetivos de auditoría suelen tener certs
    self-signed; aquí solo se lee contenido, no se confía en la identidad.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "OptiVeil/validate"})
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, resp.read(_MAX_BODY).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:  # 3xx no seguido, 4xx, 5xx
        try:
            body = e.read(_MAX_BODY).decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception:
        return None


class SensitiveRouteValidator(Validator):
    """Forced browsing NO destructivo sobre una lista curada de rutas sensibles."""

    def __init__(self, timeout: float = 5.0, paths: list[str] | None = None, fetcher=None):
        self._timeout = timeout
        self._paths = paths if paths is not None else SENSITIVE_PATHS
        # fetcher inyectable para testear sin red.
        self._fetcher = fetcher or _default_fetch

    @staticmethod
    def _is_http(finding: dict) -> bool:
        service = str(finding.get("service", "")).lower()
        try:
            port = int(finding.get("port"))
        except (TypeError, ValueError):
            port = None
        return service in _HTTP_SERVICES or port in _HTTP_PORTS

    @staticmethod
    def _base_url(target: str, finding: dict) -> str:
        service = str(finding.get("service", "")).lower()
        try:
            port = int(finding.get("port"))
        except (TypeError, ValueError):
            port = 80
        scheme = "https" if (service == "https" or port in _HTTPS_PORTS) else "http"
        if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
            return f"{scheme}://{target}"
        return f"{scheme}://{target}:{port}"

    def validate(self, target: str, findings: list[dict]) -> list[dict]:
        results: list[dict] = []
        http_findings = [f for f in findings if self._is_http(f)]
        if not http_findings:
            return results  # este backend solo aporta sobre servicios HTTP

        for finding in http_findings:
            base = self._base_url(target, finding)
            for path in self._paths:
                url = base + path
                try:
                    fetched = self._fetcher(url, self._timeout)
                except Exception:  # un fallo de red nunca rompe la validación
                    logger.debug("fetch falló en %s", url, exc_info=True)
                    continue
                if not fetched:
                    continue
                status, body = fetched
                if status != 200 or not body:
                    continue  # 404/redirect/vacío: no es exposición
                matches = find_sensitive(body)
                if not matches:
                    continue
                kinds = sorted({m["kind"] for m in matches})
                severity = "high" if any(k in ("rut", "secret", "email") for k in kinds) else "medium"
                results.append(_result(
                    finding,
                    CONFIRMED,
                    evidence={
                        "reproduce": f"GET {url}",
                        "snippet": redact_snippet(body),
                        "matches": matches,
                    },
                    source="sensitive-route",
                    name=f"Exposición en {path}",
                    severity=severity,
                    location=url,
                    vuln_class="exposición de datos sensibles",
                ))
        return results


def find_exposed_routes(target: str, findings: list[dict],
                        validator: SensitiveRouteValidator | None = None) -> list[dict]:
    """Punto de entrada: corre el backend de exposición de rutas."""
    v = validator or SensitiveRouteValidator()
    return v.validate(target, findings)
