import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from .llm_config import build_llm, LLMConfigError, DEFAULT_OFFENSIVE_MODEL
from .cve_intel import fetch_cves
from src.api.schemas import AttackRoadmap, normalize_risk


logger = logging.getLogger("optiveil.offensive")

# Peso base por nivel de riesgo del servicio para la priorización.
RISK_PRIORITY = {"alto": 30, "medio": 20, "bajo": 10}


def normalize_findings(hallazgos) -> list[dict]:
    """Acepta dicts (del engine) o strings (compat) y los uniforma a dicts."""
    out = []
    for h in hallazgos or []:
        if isinstance(h, dict):
            out.append({
                "port": h.get("port"),
                "service": h.get("service", "unknown"),
                "banner": h.get("banner") or "",
                "risk": h.get("risk", ""),
            })
        else:
            out.append({"port": None, "service": "unknown", "banner": str(h), "risk": ""})
    return out


def finding_priority(finding: dict, cves: list) -> float:
    """Score de priorización: riesgo del servicio + mayor CVSS de sus CVEs."""
    risk_tokens = (finding.get("risk") or "").split()
    risk = normalize_risk(risk_tokens[0]) if risk_tokens else "medio"
    base = RISK_PRIORITY.get(risk, 15)
    scores = [c.get("score") for c in (cves or []) if isinstance(c.get("score"), (int, float))]
    max_cvss = max(scores) if scores else 0.0
    return round(base + max_cvss * 7, 2)


def enrich_and_prioritize(findings: list, cve_fetcher=fetch_cves, max_lookups: int = 8) -> list[dict]:
    """Adjunta CVEs reales a cada hallazgo y los ordena por prioridad desc.

    Deduplica las consultas por banner/servicio y acota el número de lookups
    para no saturar el NVD ni disparar la latencia.
    """
    cache: dict[str, list] = {}
    enriched = []
    for f in findings:
        key = (f.get("banner") or f.get("service") or "").strip()
        if key and key not in cache and len(cache) < max_lookups:
            cache[key] = cve_fetcher(key)
        cves = cache.get(key, [])
        enriched.append({**f, "cves": cves, "priority": finding_priority(f, cves)})
    enriched.sort(key=lambda x: x["priority"], reverse=True)
    return enriched


def _render_findings(enriched: list[dict]) -> str:
    """Formatea los hallazgos enriquecidos para el prompt del estratega."""
    lines = []
    for f in enriched:
        cve_txt = ", ".join(
            f"{c['id']}(CVSS {c.get('score')})" for c in f.get("cves", [])
        ) or "sin CVEs conocidos"
        lines.append(
            f"- [prioridad {f['priority']}] Puerto {f.get('port')} "
            f"{f.get('service')} | banner: {f.get('banner') or 'N/A'} | "
            f"riesgo: {f.get('risk') or 'N/A'} | CVEs: {cve_txt}"
        )
    return "\n".join(lines) if lines else "(sin hallazgos)"


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


# Capacidad de salida estructurada del proveedor, cacheada por proceso:
# None = desconocida, True = soportada, False = no soportada (se omite el
# intento para no pagar una generación extra en cada petición).
_structured_supported = None


def _roadmap_from_llm(llm, messages) -> dict:
    """Obtiene la hoja de ruta del LLM priorizando salida estructurada.

    1) Si el proveedor la soporta, `with_structured_output(AttackRoadmap)`
       devuelve el objeto ya validado en UNA sola generación.
    2) Si no la soporta, se cae al invoke crudo + parseo tolerante y se recuerda
       (cache) para no reintentar el camino estructurado en futuras peticiones:
       así se evita la doble generación (clave de rendimiento).
    """
    global _structured_supported
    if _structured_supported is not False:
        try:
            structured = llm.with_structured_output(AttackRoadmap)
            result = structured.invoke(messages)
            _structured_supported = True
            if isinstance(result, AttackRoadmap):
                return result.model_dump()
            return AttackRoadmap.model_validate(result).model_dump()
        except (ValueError, json.JSONDecodeError, ValidationError):
            raise  # estructurado funcionó pero el contenido no validó
        except Exception as e:
            _structured_supported = False
            logger.info("structured_output no soportado (%s); desactivado para la sesión", e)

    respuesta = llm.invoke(messages)
    return parse_roadmap(respuesta.content)


def generate_attack_path(hallazgos: list, noise_score: float, cve_fetcher=fetch_cves):
    """Genera una hoja de ruta purple-team fundamentada en CVEs reales.

    Enriquece los hallazgos con CVEs del NVD y los prioriza (CVSS + riesgo)
    antes de pedir al LLM una ruta mapeada a MITRE ATT&CK, con detección y
    mitigación por paso. `cve_fetcher` es inyectable para tests.
    """
    enriched = enrich_and_prioritize(normalize_findings(hallazgos), cve_fetcher=cve_fetcher)

    prompt_estratega = f"""
    ACTÚA COMO UN SENIOR PENTESTER / RED TEAM LEAD en un engagement AUTORIZADO.
    Transforma los hallazgos (ya priorizados y con CVEs reales) en una ruta de
    ataque lógica para un informe purple-team.

    REGLAS:
    1. Responde ÚNICAMENTE con un objeto JSON puro, sin markdown ni prosa.
    2. Ataca primero los hallazgos de mayor prioridad.
    3. Fundamenta cada paso en los CVEs provistos; NO inventes CVEs.
    4. Coherencia con el ruido (Noise Score: {noise_score:.2f}): ruido bajo =>
       tácticas sigilosas; ruido alto => tácticas rápidas/agresivas.
    5. Cada paso DEBE incluir: mitre_technique (ID ATT&CK, p.ej. T1190),
       detection (cómo lo vería un blue team) y mitigation (contramedida).
    6. Devuelve como MÁXIMO 5 pasos, los más relevantes. Sé conciso.
    """

    try:
        # max_tokens acota la salida -> menos tokens que generar = más rápido.
        llm = build_llm(model=DEFAULT_OFFENSIVE_MODEL, temperature=0.2, max_tokens=1024)
    except LLMConfigError as e:
        logger.warning("IA ofensiva sin token: %s", e)
        return _fallback("Error de Configuración IA", "Configurar token de IA", "medio", str(e))

    query = f"""
    Hallazgos priorizados:
    {_render_findings(enriched)}

    Genera el JSON con esta estructura exacta:
    {{
      "steps": [
        {{
          "id": 1, "phase": "Reconocimiento", "action": "...", "risk": "alto",
          "justification": "...", "mitre_technique": "T1190",
          "cve_refs": ["CVE-2021-XXXX"], "detection": "...", "mitigation": "..."
        }}
      ]
    }}
    """

    messages = [SystemMessage(content=prompt_estratega), HumanMessage(content=query)]
    try:
        roadmap = _roadmap_from_llm(llm, messages)
    except (ValueError, json.JSONDecodeError, ValidationError) as e:
        logger.error("La IA no devolvió una hoja de ruta válida: %s", e)
        return _fallback("Error de Parseo", "Revisar logs del backend", "alto",
                         "La IA no devolvió una hoja de ruta JSON válida.")
    except Exception as e:
        logger.exception("Fallo en la inferencia de IA ofensiva")
        return _fallback("Error de Conexión IA", "Fallo en LLM", "medio",
                         f"Error detectado: {str(e)[:80]}")

    # Adjunta el ranking de hallazgos para trazabilidad en el reporte/frontend.
    roadmap["prioritized_findings"] = [
        {k: f[k] for k in ("port", "service", "banner", "risk", "priority", "cves")}
        for f in enriched
    ]
    return roadmap
