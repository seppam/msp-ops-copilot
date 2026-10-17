"""Does retrieval find the right impact-matrix section for each ticket?

For every labelled ticket that names an app/menu, embed "subject + description" and check
whether the matching section of impact-matrix.md ranks first (top-1) or in the top 3.
Compares embedding models so we choose with data, not opinion.
"""

import csv
import json
import math
import os
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from msp_ops_copilot import rag
from msp_ops_copilot.llm import PROVIDERS

HISTORY = rag.ROOT / "experiments" / "history.jsonl"
FASTEMBED_CACHE = Path.home() / ".cache" / "fastembed"
STATS = {"api_calls": 0, "chars_embedded": 0}
LOCAL_MODELS = {
    "local-multilingual-minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "local-potion-multilingual": "minishlab/potion-multilingual-128M",
}
TICKETS = rag.ROOT / "data" / "golden" / "tickets.csv"
MATRIX = rag.ROOT / "data" / "kb_app" / "impact-matrix.md"


def minilm(texts: list[str]) -> list[list[float]]:
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    STATS["chars_embedded"] += sum(map(len, texts))
    return [list(map(float, v)) for v in DefaultEmbeddingFunction()(texts)]


def local(model_name: str):
    def embed(texts: list[str]) -> list[list[float]]:
        from fastembed import TextEmbedding

        STATS["chars_embedded"] += sum(map(len, texts))
        model = TextEmbedding(model_name=model_name, cache_dir=str(FASTEMBED_CACHE))
        return [list(map(float, v)) for v in model.embed(texts)]

    return embed


def gemini(texts: list[str]) -> list[list[float]]:
    p = PROVIDERS["gemini"]
    client = OpenAI(base_url=p.base_url, api_key=os.environ[p.api_key_env])
    model = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
    out = []
    for i in range(0, len(texts), 50):  # modest batches to respect free-tier limits
        out += [d.embedding for d in client.embeddings.create(model=model, input=texts[i : i + 50]).data]
        STATS["api_calls"] += 1
    STATS["chars_embedded"] += sum(map(len, texts))
    return out


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def expected_section(app: str, menu: str, titles: list[str]) -> str | None:
    hits = [t for t in titles if app and t.startswith(app) and (menu in t or t.startswith(menu))]
    return hits[0] if hits else None


def evaluate(embed) -> dict:
    sections = rag.chunk(MATRIX)
    titles = [t for t, _ in sections]
    tickets = list(csv.DictReader(open(TICKETS, encoding="utf-8-sig")))
    cases = [(t, expected_section(t["app"], t["menu"], titles)) for t in tickets]
    cases = [(t, exp) for t, exp in cases if exp]
    vectors = embed([text for _, text in sections] + [f"{t['subject']}. {t['description']}" for t, _ in cases])
    sec_vecs, q_vecs = vectors[: len(sections)], vectors[len(sections) :]
    top1 = top3 = 0
    misses = []
    for (ticket, exp), q in zip(cases, q_vecs):
        ranked = [titles[i] for i in sorted(range(len(titles)), key=lambda i: -cosine(q, sec_vecs[i]))]
        top1 += ranked[0] == exp
        top3 += exp in ranked[:3]
        if ranked[0] != exp:
            misses.append(f"{ticket['id']}: expected '{exp}', got '{ranked[0]}'")
    return {"n": len(cases), "top1": top1, "top3": top3, "misses": misses}


def disk_mb(name: str) -> float | None:
    """Size of the downloaded local model on disk (None for cloud/other)."""
    if name not in LOCAL_MODELS:
        return None
    key = LOCAL_MODELS[name].split("/")[-1].lower()
    # Cache entries are links into a shared blobs folder: follow them and count each real file once.
    real_files = {f.resolve() for d in FASTEMBED_CACHE.glob("*") if key in d.name.lower() for f in d.rglob("*") if f.is_file()}
    total = sum(f.stat().st_size for f in real_files)
    return round(total / 1e6) if total else None


def log_run(name: str, result: dict, seconds: float) -> None:
    """Append one experiment record. Peak memory is for this whole process, so run one embedder per process."""
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=rag.ROOT).stdout.strip()
    record = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": commit,
        "experiment": "retrieval-impact-matrix",
        "name": name,
        "n": result["n"], "top1": result["top1"], "top3": result["top3"],
        "seconds": round(seconds, 1),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6),  # bytes on macOS
        "api_calls": STATS["api_calls"], "chars_embedded": STATS["chars_embedded"],
        "model_disk_mb": disk_mb(name),
        "misses": result["misses"],
    }
    HISTORY.parent.mkdir(exist_ok=True)
    with HISTORY.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


EMBEDDERS = {"minilm": minilm, "gemini": gemini, **{k: local(v) for k, v in LOCAL_MODELS.items()}}

if __name__ == "__main__":
    name = sys.argv[1]
    started = time.perf_counter()
    r = evaluate(EMBEDDERS[name])
    seconds = time.perf_counter() - started
    log_run(name, r, seconds)
    print(f"{name}: top-1 {r['top1']}/{r['n']}  top-3 {r['top3']}/{r['n']}  ({seconds:.1f}s)")
    for m in r["misses"]:
        print("   miss", m)
