"""Does retrieval find the right impact-matrix section for each ticket?

For every labelled ticket that names an app/menu, embed "subject + description" and check
whether the matching section of impact-matrix.md ranks first (top-1) or in the top 3.
Compares embedding models so we choose with data, not opinion.
"""

import csv
import math
import os
import sys

from openai import OpenAI

from msp_ops_copilot import rag
from msp_ops_copilot.llm import PROVIDERS

TICKETS = rag.ROOT / "data" / "golden" / "tickets.csv"
MATRIX = rag.ROOT / "data" / "kb_app" / "impact-matrix.md"


def minilm(texts: list[str]) -> list[list[float]]:
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    return [list(map(float, v)) for v in DefaultEmbeddingFunction()(texts)]


def gemini(texts: list[str]) -> list[list[float]]:
    p = PROVIDERS["gemini"]
    client = OpenAI(base_url=p.base_url, api_key=os.environ[p.api_key_env])
    model = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
    out = []
    for i in range(0, len(texts), 50):  # modest batches to respect free-tier limits
        out += [d.embedding for d in client.embeddings.create(model=model, input=texts[i : i + 50]).data]
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


if __name__ == "__main__":
    for name in sys.argv[1:] or ["minilm", "gemini"]:
        r = evaluate({"minilm": minilm, "gemini": gemini}[name])
        print(f"{name}: top-1 {r['top1']}/{r['n']}  top-3 {r['top3']}/{r['n']}")
        for m in r["misses"]:
            print("   miss", m)
