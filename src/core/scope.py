"""Autorización: control de alcance (scope) y registro de auditoría.

Para un uso responsable de OptiVeil, permite restringir las operaciones a un
conjunto de objetivos autorizados y deja traza de cada petición.

- Scope: se define en `OPTIVEIL_SCOPE` (lista separada por comas) o en el
  archivo de `OPTIVEIL_SCOPE_FILE` (por defecto `scope.txt` si existe). Admite
  IPs exactas, redes CIDR y hostnames. Si NO hay scope definido, no se
  restringe (pero se registra), para no romper el uso en laboratorio.
- Audit log: una línea JSON por petición en `results/audit.log`.
"""
import ipaddress
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger("optiveil.scope")

DEFAULT_SCOPE_FILE = "scope.txt"
AUDIT_LOG_PATH = "results/audit.log"


def parse_scope(lines) -> list:
    """Extrae entradas de scope, ignorando blancos y comentarios (`#`)."""
    entries = []
    for raw in lines or []:
        entry = raw.strip()
        if entry and not entry.startswith("#"):
            entries.append(entry)
    return entries


def load_scope() -> list:
    """Carga el scope desde la variable de entorno o el archivo."""
    raw = os.getenv("OPTIVEIL_SCOPE")
    if raw:
        return parse_scope(raw.replace(",", "\n").splitlines())
    path = os.getenv("OPTIVEIL_SCOPE_FILE", DEFAULT_SCOPE_FILE)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return parse_scope(f.readlines())
    return []


def is_in_scope(target: str, entries: list, strict: bool = False) -> bool:
    """¿El objetivo está autorizado?

    Sin scope definido: en modo normal se permite (uso en laboratorio); en modo
    `strict` se DENIEGA. El modo estricto es para acciones activas/intrusivas
    (p. ej. validación de explotabilidad), donde operar "sin scope" es un riesgo
    que no debe depender de la buena fe del operador.
    """
    if not entries:
        return not strict

    try:
        ip = ipaddress.ip_address(target)
    except ValueError:
        # hostname: coincidencia exacta
        return target in entries

    for e in entries:
        try:
            if "/" in e:
                if ip in ipaddress.ip_network(e, strict=False):
                    return True
            elif ipaddress.ip_address(e) == ip:
                return True
        except ValueError:
            continue  # entrada no-IP, no aplica a un target IP
    return False


def audit_log(action: str, target: str, allowed: bool, detail: str = "",
              path: str = AUDIT_LOG_PATH) -> None:
    """Registra la petición (append) como una línea JSON. No lanza."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "action": action,
            "target": target,
            "allowed": allowed,
            "detail": detail,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:  # nunca romper la operación por el logging
        logger.warning("No se pudo escribir el audit log: %s", e)


def enforce_scope(action: str, target: str, strict: bool = False):
    """Comprueba el scope y registra la auditoría. Lanza si está fuera de scope.

    Con `strict=True`, un scope no definido se rechaza (ver `is_in_scope`).
    """
    from fastapi import HTTPException

    entries = load_scope()
    allowed = is_in_scope(target, entries, strict=strict)
    if not entries:
        detail = "modo estricto: scope no definido => denegado" if strict else "sin scope definido"
    else:
        detail = ""
    audit_log(action, target, allowed, detail=detail)
    if not allowed:
        raise HTTPException(status_code=403,
                            detail=f"Objetivo '{target}' fuera del scope autorizado")
