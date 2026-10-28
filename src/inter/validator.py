"""Validación NO destructiva de explotabilidad (SPEC-0002).

Confirma, de forma no destructiva, si un hallazgo priorizado es realmente
explotable, mediante observación activa: enviar una petición benigna y leer la
respuesta. Lo que hace a mano un pentester con `curl` para demostrar, p. ej., un
information disclosure, aquí se automatiza y, sobre todo, se adjunta la EVIDENCIA
reproducible que sostiene el reporte.

Límites por diseño (no negociables):
- Nada que modifique estado del objetivo: sin explotación real, sin escritura/
  borrado, sin DoS, sin fuerza bruta.
- OptiVeil ORQUESTA herramientas vetadas (nuclei); no implementa exploits propios.
- La evidencia es sensible: se redacta/trunca y nunca se vierte en artefactos
  versionados ni en el audit log.

El gating de autorización (scope estricto) vive en la capa de API (el router
llama a `enforce_scope(..., strict=True)`), no aquí.
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from abc import ABC, abstractmethod

logger = logging.getLogger("optiveil.validator")

# Estados del veredicto, de mayor a menor certeza.
CONFIRMED = "confirmed"          # observación directa: el check disparó
LIKELY = "likely"               # heurística (p. ej. detección por versión)
NOT_CONFIRMED = "not_confirmed"  # se probó y no se confirmó
NOT_TESTED = "not_tested"        # no se pudo probar (backend ausente/error)

# Tags de nuclei que NO son no-destructivos: se excluyen siempre.
_UNSAFE_TAGS = ("dos", "intrusive", "fuzz", "brute-force", "bruteforce")

_SNIPPET_MAX = 300  # longitud máxima del fragmento de evidencia

# Caracteres válidos para un tag de nuclei. El `service` viene del fingerprint
# (input no confiable): se sanea antes de construir el comando (SPEC-0003).
_TAG_RE = re.compile(r"[^a-z0-9-]")


class ValidatorUnavailable(RuntimeError):
    """El backend de validación no está disponible (p. ej. binario ausente)."""


def redact_snippet(text, max_len: int = _SNIPPET_MAX) -> str:
    """Trunca la evidencia y enmascara secretos evidentes.

    La evidencia puede contener los propios datos filtrados; esto es una red de
    seguridad para no verterlos tal cual en un reporte, no un redactor perfecto.
    """
    if not text:
        return ""
    s = str(text)
    s = re.sub(
        r'(?i)(password|passwd|token|secret|api[_-]?key|authorization)(\s*[:=]\s*)\S+',
        r'\1\2[REDACTADO]', s,
    )
    if len(s) > max_len:
        s = s[:max_len] + "...[truncado]"
    return s


def _result(finding: dict, status: str, evidence: dict | None = None, source: str = "") -> dict:
    return {
        "port": finding.get("port"),
        "service": finding.get("service", "unknown"),
        "status": status,
        "evidence": evidence or {},
        "source": source,
    }


class Validator(ABC):
    """Interfaz de backend de validación. Pluggable: hoy nuclei, mañana otro."""

    @abstractmethod
    def validate(self, target: str, findings: list[dict]) -> list[dict]:
        """Devuelve un resultado (dict) por hallazgo. No debe lanzar por fallos
        del backend: degrada a NOT_TESTED."""


class NucleiValidator(Validator):
    """Backend basado en nuclei, acotado a plantillas de detección no intrusivas."""

    def __init__(self, binary: str = "nuclei", timeout: int = 120, runner=None):
        self._binary = binary
        self._timeout = timeout
        # runner inyectable para tests (evita ejecutar nuclei y tocar la red).
        self._runner = runner or self._run_nuclei

    @staticmethod
    def _service_tags(findings: list[dict]) -> list[str]:
        """Tags de nuclei derivados del servicio de cada hallazgo, saneados.

        Zero-trust: el `service` viene del fingerprint; se reduce a `[a-z0-9-]`.
        Distintos y en orden de aparición.
        """
        tags: list[str] = []
        for f in findings:
            tag = _TAG_RE.sub("", str(f.get("service", "")).lower())
            if tag and tag not in tags:
                tags.append(tag)
        return tags

    def _run_nuclei(self, target: str, tags: list[str]) -> str:
        if shutil.which(self._binary) is None:
            raise ValidatorUnavailable(
                f"nuclei no encontrado en PATH ('{self._binary}'). Instálalo "
                "o usa otro backend de validación."
            )
        # -tags: solo plantillas del servicio del hallazgo (no el catálogo entero).
        # -disable-update-check / -no-update-templates: sin red en caliente; evita
        # que el chequeo de plantillas contra GitHub estanque la corrida (SPEC-0003).
        cmd = [
            self._binary, "-u", target, "-jsonl", "-silent",
            "-tags", ",".join(tags),
            "-etags", ",".join(_UNSAFE_TAGS),  # excluye lo no seguro
            "-timeout", "10",
            "-disable-update-check", "-no-update-templates",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self._timeout)
        return proc.stdout

    def validate(self, target: str, findings: list[dict]) -> list[dict]:
        tags = self._service_tags(findings)
        if not tags:
            # Sin un servicio mapeable no acotamos: antes que correr el catálogo
            # completo (lento, ruidoso), degradamos honesto a "no probado".
            return [_result(f, NOT_TESTED,
                            {"error": "sin plantillas acotadas para el servicio"},
                            "nuclei") for f in findings]
        try:
            raw = self._runner(target, tags)
        except ValidatorUnavailable as e:
            logger.warning("Validación no disponible: %s", e)
            return [_result(f, NOT_TESTED, {"error": str(e)[:120]}, "nuclei") for f in findings]
        except Exception as e:  # nunca romper la petición por un fallo del backend
            logger.exception("Fallo ejecutando el backend de validación")
            return [_result(f, NOT_TESTED, {"error": str(e)[:120]}, "nuclei") for f in findings]

        matches = self._parse(raw)
        return self._map(findings, matches)

    @staticmethod
    def _parse(raw: str) -> list[dict]:
        """Parsea la salida JSONL de nuclei (una línea JSON por match).

        Zero-trust: ignora líneas que no sean JSON válido.
        """
        out = []
        for line in (raw or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    @staticmethod
    def _map(findings: list[dict], matches: list[dict]) -> list[dict]:
        """Asocia los matches de nuclei a cada hallazgo por puerto."""
        results = []
        for f in findings:
            port = f.get("port")
            hit = None
            for m in matches:
                mport = m.get("port")
                matched_at = str(m.get("matched-at") or m.get("host") or "")
                if (mport and str(mport) == str(port)) or (port and f":{port}" in matched_at):
                    hit = m
                    break

            if not hit:
                results.append(_result(f, NOT_CONFIRMED, source="nuclei"))
                continue

            info = hit.get("info") or {}
            tags = info.get("tags") or []
            # Una detección por versión es "probable"; un match de comportamiento
            # directo es "confirmado".
            version_only = any(t in ("version", "tech") for t in tags)
            status = LIKELY if version_only else CONFIRMED
            evidence = {
                "reproduce": str(hit.get("curl-command") or hit.get("matched-at") or ""),
                "snippet": redact_snippet(hit.get("extracted-results") or info.get("name") or ""),
                "template": hit.get("template-id", ""),
            }
            results.append(_result(f, status, evidence, "nuclei"))
        return results


def validate_findings(target: str, findings: list[dict], validator: Validator | None = None) -> list[dict]:
    """Punto de entrada para la capa de API. `validator` es inyectable en tests."""
    v = validator or NucleiValidator()
    return v.validate(target, findings)
