from livekit.plugins import openai

from .. import config


def build_llm() -> openai.LLM:
    return openai.LLM.with_ollama(
        model=config.OLLAMA_MODEL,
        base_url=config.OLLAMA_BASE_URL,
    )
