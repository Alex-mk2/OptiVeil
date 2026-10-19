"""Tests de la config centralizada del LLM."""
import pytest

from inter import llm_config
from inter.llm_config import get_ai_token, build_llm, LLMConfigError


ALL_TOKENS = ("OPTIVEIL_AI_TOKEN", "GITHUB_TOKEN", "OPENAI_API_KEY")


@pytest.fixture
def clean_env(monkeypatch):
    for name in ALL_TOKENS:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_prioridad_optiveil_sobre_openai(clean_env):
    clean_env.setenv("OPENAI_API_KEY", "openai")
    clean_env.setenv("OPTIVEIL_AI_TOKEN", "optiveil")
    assert get_ai_token() == "optiveil"


def test_github_token_se_ignora(clean_env):
    # GitHub Models fue retirado: GITHUB_TOKEN ya no es un token de IA válido.
    clean_env.setenv("GITHUB_TOKEN", "github")
    assert get_ai_token() is None


def test_fallback_a_openai(clean_env):
    clean_env.setenv("OPENAI_API_KEY", "openai")
    assert get_ai_token() == "openai"


def test_sin_token_devuelve_none(clean_env):
    assert get_ai_token() is None


def test_build_llm_sin_token_lanza_error(clean_env):
    with pytest.raises(LLMConfigError):
        build_llm(model="gpt-4o-mini")


def test_build_llm_con_token_no_lanza(clean_env):
    clean_env.setenv("OPTIVEIL_AI_TOKEN", "token-de-prueba")
    llm = build_llm(model=llm_config.DEFAULT_ANALYST_MODEL)
    assert llm is not None
