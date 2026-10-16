"""One place that knows how to talk to an LLM provider.

Groq and Gemini both expose an OpenAI-compatible API, so the same `openai`
client works for both -- only base_url, api_key and model change. The same
trick lets us point at Ollama / vLLM / llama.cpp later (they are
OpenAI-compatible too), which is how "local AI" is supported without
running a model on this machine.
"""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
for _name in ("httpx", "httpx2"):
    logging.getLogger(_name).setLevel(logging.WARNING)


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key_env: str
    model_env: str


PROVIDERS = {
    "groq": Provider(
        "groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "GROQ_MODEL"
    ),
    "gemini": Provider(
        "gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
    ),
}


def get_client() -> tuple[OpenAI, str]:
    """Return (client, model) for the provider chosen by LLM_PROVIDER."""
    provider = PROVIDERS[os.getenv("LLM_PROVIDER", "groq")]
    api_key = os.getenv(provider.api_key_env, "")
    if not api_key:
        raise SystemExit(f"{provider.api_key_env} is empty. Fill it in .env first.")
    return OpenAI(base_url=provider.base_url, api_key=api_key), os.environ[provider.model_env]
