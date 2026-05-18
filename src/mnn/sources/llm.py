"""OpenAI-compatible LLM client (Ollama local + Ollama Cloud)."""
from openai import AsyncOpenAI

from mnn.config import settings


def _base_url(api_url: str) -> str:
    api_url = api_url.rstrip("/")
    if api_url.endswith("/v1"):
        return api_url
    return api_url.removesuffix("/api") + "/v1"


def async_client() -> AsyncOpenAI:
    s = settings()
    return AsyncOpenAI(base_url=_base_url(s.llm_api_url), api_key=s.llm_api_key)
