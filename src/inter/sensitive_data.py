"""Detección de datos sensibles en respuestas (SPEC-0007).

Puro, sin red: recibe texto (el cuerpo de una respuesta ya obtenida) y devuelve
qué datos sensibles aparecen, **ya enmascarados**. No implementa exploits ni ataca;
solo reconoce fugas para reportarlas con evidencia redactada.

Clases detectadas: RUT chileno válido (módulo 11), correos, secretos (token/clave/
api-key) y firmas de exposición (archivo tipo `.env`, listado de directorio).
"""
from __future__ import annotations

import re

# --- Patrones ---
# RUT: 12.345.678-5 | 12345678-5 | 1234567-K. Captura cuerpo y dígito verificador.
_RUT_RE = re.compile(r"\b(\d{1,2}(?:\.\d{3}){2}|\d{7,8})-([\dkK])\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key|authorization)\b\s*[:=]\s*\S+"
)
# Línea tipo CLAVE=valor (variable de entorno). Firma de un `.env` expuesto.
_ENV_RE = re.compile(r"(?m)^[A-Z][A-Z0-9_]{2,}=\S+")
# Listado de directorio típico (Apache/nginx/python http.server).
_DIRLIST_RE = re.compile(r"(?i)<title>\s*(?:index of|directory listing for)")


def validate_rut(body: str, dv: str) -> bool:
    """Valida el dígito verificador de un RUT por módulo 11.

    Evita falsos positivos: un número cualquiera con guion no pasa salvo que su DV
    sea correcto.
    """
    cuerpo = body.replace(".", "")
    if not cuerpo.isdigit():
        return False
    suma = 0
    for i, ch in enumerate(reversed(cuerpo)):
        suma += int(ch) * (2 + i % 6)  # factores 2..7 cíclicos
    resto = 11 - (suma % 11)
    esperado = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    return esperado == dv.upper()


def _mask(s: str, keep_start: int = 2, keep_end: int = 1) -> str:
    """Enmascara el centro de un valor, conservando pistas mínimas."""
    s = str(s)
    if len(s) <= keep_start + keep_end:
        return "*" * len(s)
    return s[:keep_start] + "…" + s[-keep_end:]


def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return (local[:1] or "*") + "***@" + domain


def find_sensitive(text: str) -> list[dict]:
    """Devuelve los datos sensibles hallados en `text`, ya enmascarados.

    Cada entrada: {"kind": <clase>, "redacted": <valor enmascarado>}. Lista vacía
    si no hay nada. Nunca devuelve el dato en claro.
    """
    if not text:
        return []
    out: list[dict] = []
    vistos: set[tuple[str, str]] = set()

    def _add(kind: str, redacted: str):
        clave = (kind, redacted)
        if clave not in vistos:
            vistos.add(clave)
            out.append({"kind": kind, "redacted": redacted})

    for m in _RUT_RE.finditer(text):
        body, dv = m.group(1), m.group(2)
        if validate_rut(body, dv):
            _add("rut", f"{_mask(body.replace('.', ''))}-{dv.upper()}")

    for m in _EMAIL_RE.finditer(text):
        _add("email", _mask_email(m.group(0)))

    for m in _SECRET_RE.finditer(text):
        # Solo la clave; el valor nunca sale.
        clave = re.split(r"\s*[:=]", m.group(0), 1)[0].strip()
        _add("secret", f"{clave}=[REDACTADO]")

    if _DIRLIST_RE.search(text):
        _add("directory-listing", "<listado de directorio>")

    if len(_ENV_RE.findall(text)) >= 1:
        _add("env-file", "<variables de entorno expuestas>")

    return out


def mask_pii_in_text(text: str) -> str:
    """Enmascara RUTs y correos dentro de un texto (para redactar evidencia).

    Enmascara **cualquier** token con forma de RUT (válido o no): sobre-redactar un
    fragmento de evidencia es preferible a filtrar un dato personal.
    """
    if not text:
        return text
    text = _RUT_RE.sub(lambda m: f"{_mask(m.group(1).replace('.', ''))}-{m.group(2).upper()}", text)
    text = _EMAIL_RE.sub(lambda m: _mask_email(m.group(0)), text)
    return text
