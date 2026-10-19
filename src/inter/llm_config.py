"""Configuración centralizada del cliente LLM de OptiVeil.

Unifica el acceso al proveedor de IA para que `IA_analyzer` e `IA_offensive`
compartan credenciales, endpoint y manejo de errores en un solo lugar.

Por defecto OptiVeil usa OpenAI (api.openai.com). GitHub Models fue retirado
(30/07/2026), por eso ya no se usa su endpoint ni GITHUB_TOKEN. El token se
busca en este orden de prioridad:

    OPTIVEIL_AI_TOKEN  ->  OPENAI_API_KEY

Para otro proveedor compatible con OpenAI (Azure AI Foundry, Ollama/LM Studio,
etc.) define OPTIVEIL_AI_BASE_URL; por defecto se usa el endpoint de OpenAI.
"""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Modelos por defecto (OpenAI). Sobreescribibles por entorno.
DEFAULT_ANALYST_MODEL = os.getenv("OPTIVEIL_ANALYST_MODEL", "gpt-4o-mini")
DEFAULT_OFFENSIVE_MODEL = os.getenv("OPTIVEIL_OFFENSIVE_MODEL", "gpt-4o-mini")

_TOKEN_ENV_PRIORITY = ("OPTIVEIL_AI_TOKEN", "OPENAI_API_KEY")


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
            "(o OPENAI_API_KEY) en tu entorno o .env."
        )

    # base_url opcional: por defecto la SDK usa el endpoint de OpenAI.
    base_url = os.getenv("OPTIVEIL_AI_BASE_URL") or None
    kwargs = {"model_name": model, "openai_api_key": token, "temperature": temperature}
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)
