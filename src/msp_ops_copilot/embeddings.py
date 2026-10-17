"""Gemini embeddings with a disk cache, so repeated experiments do not spend quota again."""

import hashlib
import json
import os
from pathlib import Path

from openai import OpenAI

from msp_ops_copilot.llm import PROVIDERS

CACHE_FILE = Path(__file__).resolve().parents[2] / ".cache" / "embeddings.json"
STATS = {"api_calls": 0, "cache_hits": 0, "chars_embedded": 0}
_cache: dict[str, list[float]] | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    return _cache


def embed(texts: list[str]) -> list[list[float]]:
    model = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
    cache = _load()
    keys = [hashlib.sha1(f"{model}\n{t}".encode()).hexdigest() for t in texts]
    missing = [(k, t) for k, t in dict(zip(keys, texts)).items() if k not in cache]
    STATS["cache_hits"] += len(texts) - len(missing)
    if missing:
        p = PROVIDERS["gemini"]
        client = OpenAI(base_url=p.base_url, api_key=os.environ[p.api_key_env])
        for i in range(0, len(missing), 50):
            batch = missing[i : i + 50]
            data = client.embeddings.create(model=model, input=[t for _, t in batch]).data
            for (k, t), d in zip(batch, data):
                cache[k] = d.embedding
                STATS["chars_embedded"] += len(t)
            STATS["api_calls"] += 1
        CACHE_FILE.parent.mkdir(exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache))
    return [cache[k] for k in keys]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / ((sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5))
