import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from .llm_config import build_llm, LLMConfigError, DEFAULT_OFFENSIVE_MODEL
from src.api.schemas import AttackRoadmap


logger = logging.getLogger("optiveil.offensive")


def extract_json_block(text: str) -> str:
    """Extrae el primer objeto JSON balanceado de la respuesta del LLM.

    Tolera fences ```json ... ``` y prosa alrededor. Rastrea el balance de
    llaves respetando las cadenas, en vez de una regex frágil.
    """
    s = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", s, re.DOTALL)
    if fence:
        s = fence.group(1).strip()

    start = s.find("{")
    if start == -1:
        raise ValueError("No se encontró ningún objeto JSON en la respuesta")

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]

    raise ValueError("El objeto JSON de la respuesta está incompleto")


def parse_roadmap(raw_text: str) -> dict:
    """Convierte el texto crudo del LLM en una hoja de ruta validada.

    Lanza ValueError/JSONDecodeError/ValidationError si no es parseable; el
    llamador decide el fallback.
    """
    block = extract_json_block(raw_text)
    data = json.loads(block)
    return AttackRoadmap.model_validate(data).model_dump()


def _fallback(phase: str, action: str, risk: str, justification: str) -> dict:
    """Hoja de ruta mínima con forma válida para que el frontend no se rompa."""
    return {"steps": [{"id": 1, "phase": phase, "action": action,
                       "risk": risk, "justification": justification}]}


def generate_attack_path(hallazgos: list, noise_score: float):
    prompt_estratega = f"""
    ACTÚA COMO UN SENIOR PENTESTER / RED TEAM LEAD.
    Tu objetivo es transformar hallazgos técnicos en una ruta de ataque lógica.

    REGLAS:
    1. Formatea la respuesta ÚNICAMENTE como un objeto JSON puro sin formato markdown.
    2. No incluyas explicaciones fuera del JSON. Ningún "Aquí tienes..." o "Entendido...".
    3. La ruta debe ser coherente con el nivel de ruido (Noise Score: {noise_score:.2f}).
       - Si el ruido es bajo (priorizamos f1), sugiere tácticas sigilosas.
       - Si el ruido es alto (priorizamos f2), sugiere tácticas rápidas y agresivas.
    """

    try:
        llm = build_llm(model=DEFAULT_OFFENSIVE_MODEL, temperature=0.2)
    except LLMConfigError as e:
        logger.warning("IA ofensiva sin token: %s", e)
        return _fallback("Error de Configuración IA", "Configurar token de IA", "medio", str(e))

    query = f"""
    Hallazgos detectados: {hallazgos}
    Genera el JSON con esta estructura exacta:
    {{
      "steps": [
        {{ "id": 1, "phase": "Reconocimiento", "action": "...", "risk": "alto", "justification": "..." }}
      ]
    }}
    """

    try:
        respuesta = llm.invoke([
            SystemMessage(content=prompt_estratega),
            HumanMessage(content=query),
        ])
    except Exception as e:
        logger.exception("Fallo en la inferencia de IA ofensiva")
        return _fallback("Error de Conexión IA", "Fallo en LLM", "medio",
                         f"Error detectado: {str(e)[:80]}")

    try:
        return parse_roadmap(respuesta.content)
    except (ValueError, json.JSONDecodeError, ValidationError) as e:
        logger.error("La IA no devolvió un JSON válido: %s | contenido: %s",
                     e, (respuesta.content or "")[:300])
        return _fallback("Error de Parseo", "Revisar logs del backend", "alto",
                         "La IA no devolvió una hoja de ruta JSON válida.")
