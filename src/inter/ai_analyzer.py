import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv()


def analizar_auditoria(ruta_json: str):
    """Toma el JSON generado por OptiVeil y usa IA para redactar un reporte táctico."""
    try:
        with open(ruta_json, 'r') as f:
            datos_auditoria = json.load(f)
    except Exception as e:
        return f"Error al leer la evidencia: {e}"

    
    api_key = os.getenv("GITHUB_TOKEN") 
    if not api_key:
        return "Error: Token de IA no configurado en el entorno."

    llm = ChatOpenAI(
        model_name="gpt-4o-mini", 
        openai_api_key=api_key, 
        temperature=0.2, 
        base_url="https://models.inference.ai.azure.com" 
    )

    
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