"""Application-support knowledge base (data/kb_app) indexed with Gemini embeddings."""

import chromadb

from msp_ops_copilot import embeddings, rag

KB_APP = rag.ROOT / "data" / "kb_app"
COLLECTION = "app_kb"


def _collection(reset: bool = False):
    db = chromadb.PersistentClient(path=str(rag.ROOT / ".chroma"))
    if reset:
        try:
            db.delete_collection(COLLECTION)
        except Exception:
            pass
    return db.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def ingest() -> int:
    ids, docs, metas = [], [], []
    for path in sorted(KB_APP.glob("*.md")):
        for i, (title, text) in enumerate(rag.chunk(path)):
            ids.append(f"{path.stem}-{i}")
            docs.append(text)
            metas.append({"source": path.name, "section": title})
    _collection(reset=True).add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings.embed(docs))
    return len(ids)


def retrieve(query: str, k: int = 3) -> list[dict]:
    res = _collection().query(query_embeddings=embeddings.embed([query]), n_results=k)
    return [
        {"text": d, "source": m["source"], "section": m["section"]}
        for d, m in zip(res["documents"][0], res["metadatas"][0])
    ]


if __name__ == "__main__":
    print(f"indexed {ingest()} sections")
