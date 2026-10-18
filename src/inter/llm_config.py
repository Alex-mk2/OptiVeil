"""Configuración centralizada del cliente LLM de OptiVeil.

Unifica el acceso al proveedor de IA para que `IA_analyzer` e `IA_offensive`
compartan credenciales, endpoint y manejo de errores en un solo lugar.

Por defecto OptiVeil usa GitHub Models (endpoint de Azure AI Inference) con un
token personal. El token se busca en este orden de prioridad:

    OPTIVEIL_AI_TOKEN  ->  GITHUB_TOKEN  ->  OPENAI_API_KEY

Esto mantiene compatibilidad con configuraciones previas sin ambigüedad.
"""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BASE_URL = "https://models.inference.ai.azure.com"
DEFAULT_ANALYST_MODEL = "gpt-4o-mini"
DEFAULT_OFFENSIVE_MODEL = "gpt-5-mini"

_TOKEN_ENV_PRIORITY = ("OPTIVEIL_AI_TOKEN", "GITHUB_TOKEN", "OPENAI_API_KEY")


class LLMConfigError(RuntimeError):
    """Se lanza cuando falta configuración imprescindible del LLM."""


def get_ai_token() -> str | None:
    """Devuelve el primer token disponible según el orden de prioridad."""
    for env_name in _TOKEN_ENV_PRIORITY:
        token = os.getenv(env_name)
        if token:
            return token
    return None


def build_llm(model: str, temperature: float = 0.2) -> ChatOpenAI:
    """Crea un cliente ChatOpenAI configurado contra el proveedor de OptiVeil.

    Lanza LLMConfigError si no hay token, para que el llamador pueda degradar
    con un mensaje claro en vez de fallar con un error opaco del SDK.
    """
    token = get_ai_token()
    if not token:
        raise LLMConfigError(
            "Token de IA no configurado. Define OPTIVEIL_AI_TOKEN "
            "(o GITHUB_TOKEN / OPENAI_API_KEY) en tu entorno o .env."
        )

    base_url = os.getenv("OPTIVEIL_AI_BASE_URL", DEFAULT_BASE_URL)
    return ChatOpenAI(
        model_name=model,
        openai_api_key=token,
        temperature=temperature,
        base_url=base_url,
    )
