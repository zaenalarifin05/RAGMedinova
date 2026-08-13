"""Hybrid retrieval: filter metadata (deterministik) + semantic search (fallback).

Lihat ROADMAP.md §4 untuk desain lengkap. Ringkasan:

1. Filter metadata dulu (`retrieve_by_parameter_arah`): exact match parameter+arah
   di Chroma via `collection.get(where=...)` - TIDAK butuh embedding sama sekali,
   karena ini lookup deterministik, bukan similarity search. Presisi 100%.
2. Kalau tidak ketemu -> grounded=False. JANGAN fallback ke semantic search untuk
   kombinasi parameter+arah yang terstruktur ini (prinsip anti-halusinasi §4:
   kombinasi tanpa rujukan harus dilaporkan apa adanya, bukan "dicari-cari").
3. `retrieve_semantic` dipakai HANYA untuk kategori naratif (mis. pemeriksaan
   fisik) yang query-nya tidak seketat parameter+arah - lazy-load embedding
   model supaya tidak membebani RAM 16GB Mac Mini saat tidak dipakai (§3).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import chromadb

from common.config import CHROMA_COLLECTION_NAME, settings


@dataclass
class RetrievedChunk:
    grounded: bool
    id: str | None = None
    istilah_klinis: str | None = None
    body: str | None = None
    sumber: str | None = None


def _get_collection():
    client = chromadb.PersistentClient(path=str(settings.chroma_persist_path))
    return client.get_or_create_collection(CHROMA_COLLECTION_NAME)


@lru_cache(maxsize=1)
def _get_embedding_model():
    """Lazy-load, cache setelah dipanggil pertama kali - lihat ROADMAP.md §3
    (mitigasi RAM 16GB: embedding model hanya dimuat saat semantic search
    benar-benar dipakai, bukan saat startup)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def retrieve_by_parameter_arah(parameter: str, arah: str) -> RetrievedChunk:
    """Filter metadata deterministik - lihat docstring modul ini poin 1-2."""
    collection = _get_collection()
    result = collection.get(
        where={"$and": [{"parameter": parameter}, {"arah": arah}]},
        include=["documents", "metadatas"],
    )

    if not result["ids"]:
        return RetrievedChunk(grounded=False)

    metadata = result["metadatas"][0]
    return RetrievedChunk(
        grounded=True,
        id=result["ids"][0],
        istilah_klinis=metadata.get("istilah_klinis"),
        body=result["documents"][0],
        sumber=metadata.get("sumber"),
    )


def retrieve_semantic(query_text: str, kategori: str, top_k: int = 3) -> list[RetrievedChunk]:
    """Semantic search fallback untuk kategori non-parameter+arah (mis. pemeriksaan fisik)."""
    collection = _get_collection()
    model = _get_embedding_model()
    query_embedding = model.encode([query_text], normalize_embeddings=True).tolist()

    result = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where={"kategori": kategori},
        include=["documents", "metadatas"],
    )

    ids = result["ids"][0] if result["ids"] else []
    if not ids:
        return [RetrievedChunk(grounded=False)]

    return [
        RetrievedChunk(
            grounded=True,
            id=ids[i],
            istilah_klinis=result["metadatas"][0][i].get("istilah_klinis"),
            body=result["documents"][0][i],
            sumber=result["metadatas"][0][i].get("sumber"),
        )
        for i in range(len(ids))
    ]
