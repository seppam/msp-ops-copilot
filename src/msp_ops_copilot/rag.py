"""Step 6: a small RAG pipeline over the markdown knowledge base.

ingest : split each doc into sections -> embed -> store in Chroma (local files)
search : embed the question -> nearest sections, with their source names
ask    : give those sections to the LLM and require it to answer only from them

Chroma's default embedding model runs locally on CPU (no API quota used).
"""

import argparse
import re
from pathlib import Path

import chromadb

from msp_ops_copilot.llm import get_client

ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "data" / "kb"
COLLECTION = "msp_kb"


def _collection(reset: bool = False):
    db = chromadb.PersistentClient(path=str(ROOT / ".chroma"))
    if reset:
        try:
            db.delete_collection(COLLECTION)
        except Exception:
            pass
    return db.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def chunk(path: Path) -> list[tuple[str, str]]:
    """Split a markdown file at '## ' headings. Returns (section_title, text)."""
    text = path.read_text()
    doc_title = re.match(r"# (.+)", text).group(1)
    parts = re.split(r"^## ", text, flags=re.M)[1:]
    chunks = []
    for part in parts:
        title, _, body = part.partition("\n")
        # Prefix the document title so the chunk is understandable on its own.
        chunks.append((title.strip(), f"{doc_title} / {title.strip()}\n{body.strip()}"))
    return chunks


def ingest() -> int:
    col = _collection(reset=True)  # rebuild from scratch: safe to run repeatedly
    ids, docs, metas = [], [], []
    for path in sorted(KB_DIR.glob("*.md")):
        for i, (title, text) in enumerate(chunk(path)):
            ids.append(f"{path.stem}-{i}")
            docs.append(text)
            metas.append({"source": path.name, "section": title})
    col.add(ids=ids, documents=docs, metadatas=metas)
    return len(ids)


def search(query: str, k: int = 3) -> list[dict]:
    res = _collection().query(query_texts=[query], n_results=k)
    return [
        {"text": d, "source": m["source"], "section": m["section"], "distance": round(dist, 3)}
        for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def ask(question: str, k: int = 3) -> str:
    hits = search(question, k)
    context = "\n\n".join(f"[{h['source']} > {h['section']}]\n{h['text']}" for h in hits)
    client, model = get_client()
    reply = client.chat.completions.create(
        model=model,
        max_tokens=600,
        messages=[
            {"role": "system", "content": (
                "Answer using ONLY the context below. Cite sources as [file > section]. "
                "If the context does not contain the answer, say you could not find it in the knowledge base."
                f"\n\nContext:\n{context}"
            )},
            {"role": "user", "content": question},
        ],
    )
    return reply.choices[0].message.content


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["ingest", "search", "ask"])
    parser.add_argument("text", nargs="*")
    args = parser.parse_args()
    if args.command == "ingest":
        print(f"indexed {ingest()} sections")
    elif args.command == "search":
        for h in search(" ".join(args.text)):
            print(f"{h['distance']}  {h['source']} > {h['section']}")
    else:
        print(ask(" ".join(args.text)))
