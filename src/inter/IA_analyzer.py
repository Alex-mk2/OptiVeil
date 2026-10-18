import json
from langchain_core.messages import HumanMessage, SystemMessage
from .llm_config import build_llm, LLMConfigError, DEFAULT_ANALYST_MODEL


def analyze_audit(ruta_json: str):
    """Toma el JSON generado por OptiVeil y usa IA para redactar un reporte táctico."""
    try:
        with open(ruta_json, 'r', encoding="utf-8") as f:
            datos_auditoria = json.load(f)
    except Exception as e:
        return f"Error al leer la evidencia: {e}"

    try:
        llm = build_llm(model=DEFAULT_ANALYST_MODEL, temperature=0.2)
    except LLMConfigError as e:
        return f"Error: {e}"


    prompt_analista = """
    Eres el Analista Principal de Ciberseguridad (Purple Team) del framework OptiVeil.
    TU OBJETIVO: Analizar el JSON resultante de un escaneo de red sigiloso y redactar un Reporte Ejecutivo.

    REGLAS ESTRICTAS DE OPERACIÓN:
    1. Mantén un tono técnico, clínico y profesional. No inventes vulnerabilidades que no existan.
    2. Para cada puerto abierto y servicio identificado (ej. FTP, HTTP, SSH), evalúa el riesgo.
    3. Si detectas servicios en texto plano (como FTP o Telnet), clasifícalos como CRÍTICOS y recomienda cifrado (SFTP/SSH).
    4. Proporciona una sección de "Mitigación" con pasos accionables para el administrador del sistema.
    5. Formatea tu respuesta estrictamente en Markdown.
    """

    query_a_evaluar = f"""
    --- EVIDENCIA DE RED (JSON) ---
    {json.dumps(datos_auditoria, indent=2)}
    
    Por favor, genera el Reporte Ejecutivo de Mitigación basado en estos hallazgos.
    """
    try:
        respuesta = llm.invoke([
            SystemMessage(content=prompt_analista),
            HumanMessage(content=query_a_evaluar)
        ])
        return respuesta.content
    except Exception as e:
        return f"Error en la inferencia de IA: {e}"
    
    
