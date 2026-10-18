import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
from .llm_config import build_llm, LLMConfigError, DEFAULT_OFFENSIVE_MODEL


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
        return {
            "steps": [
                {"id": 1, "phase": "Error de Configuración IA", "action": "Configurar token de IA",
                 "risk": "medio", "justification": str(e)}
            ]
        }

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
            HumanMessage(content=query)
        ])
        contenido_limpio = re.sub(r'^```json\s*|\s*```$', '', respuesta.content.strip(), flags=re.MULTILINE)
        return json.loads(contenido_limpio)
        
        
    except json.JSONDecodeError as e:
        print(f"Error de Parseo JSON desde IA: {respuesta.content}")
        return {
            "steps": [
                { "id": 1, "phase": "Error de Parseo", "action": "Revisar consola del backend", "risk": "alto", "justification": "La IA no devolvió un JSON puro." }
            ]
        }
    except Exception as e:
        print(f"Error General en IA_offensive: {str(e)}")
        return {
            "steps": [
                { "id": 1, "phase": "Error de Conexión IA", "action": f"Fallo en LLM", "risk": "medio", "justification": f"Error detectado: {str(e)[:80]}" }
            ]
        }