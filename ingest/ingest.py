"""Ingest pipeline: corpus/*.md -> embed (bge-m3) -> upsert ke ChromaDB.

Jalankan dari root repo: `python -m ingest.ingest`

Lihat ROADMAP.md §6 untuk desain pipeline dan §4 untuk alasan skema metadata
(parameter/arah) yang dipakai untuk filter deterministik saat retrieval.

Field kosong TIDAK dipaksa diisi (prinsip anti-halusinasi, ROADMAP.md §1/§4):
chunk yang field wajibnya kosong di-skip dengan warning, bukan diproses paksa.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import chromadb
import yaml
from sentence_transformers import SentenceTransformer

from common.config import CHROMA_COLLECTION_NAME, CORPUS_DIR, settings

REQUIRED_FIELDS = ["id", "kategori", "parameter", "arah", "istilah_klinis", "sumber"]
SKIP_FILENAMES = {"_TEMPLATE.md", "README.md"}


@dataclass
class Chunk:
    id: str
    metadata: dict
    body: str


def load_chunk_files() -> list:
    """Kumpulkan semua file .md di corpus/, skip template & README."""
    return sorted(
        p for p in CORPUS_DIR.rglob("*.md")
        if p.name not in SKIP_FILENAMES
    )


def parse_chunk(path) -> Chunk | None:
    """Parse satu file chunk: frontmatter YAML + body markdown.

    Return None (dengan warning ke stderr) kalau frontmatter tidak valid atau
    field wajib kosong - TIDAK dipaksa diproses (prinsip anti-halusinasi).
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        print(f"[skip] {path}: tidak ada frontmatter YAML", file=sys.stderr)
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"[skip] {path}: frontmatter tidak lengkap (kurang '---' penutup)", file=sys.stderr)
        return None

    _, frontmatter_raw, body = parts
    try:
        frontmatter = yaml.safe_load(frontmatter_raw) or {}
    except yaml.YAMLError as exc:
        print(f"[skip] {path}: frontmatter YAML tidak valid ({exc})", file=sys.stderr)
        return None

    missing = [f for f in REQUIRED_FIELDS if not frontmatter.get(f)]
    if missing:
        print(f"[skip] {path}: field wajib kosong: {missing}", file=sys.stderr)
        return None

    metadata = {k: v for k, v in frontmatter.items() if v is not None}
    return Chunk(id=str(frontmatter["id"]), metadata=metadata, body=body.strip())


def embed_and_upsert(chunks: list[Chunk]) -> None:
    """Embed body tiap chunk (bge-m3) dan upsert ke ChromaDB dengan metadata."""
    if not chunks:
        print("Tidak ada chunk valid untuk di-ingest.", file=sys.stderr)
        return

    print(f"Memuat model embedding {settings.embedding_model} ...")
    model = SentenceTransformer(settings.embedding_model)

    client = chromadb.PersistentClient(path=str(settings.chroma_persist_path))
    collection = client.get_or_create_collection(CHROMA_COLLECTION_NAME)

    embeddings = model.encode([c.body for c in chunks], normalize_embeddings=True).tolist()

    collection.upsert(
        ids=[c.id for c in chunks],
        embeddings=embeddings,
        documents=[c.body for c in chunks],
        metadatas=[c.metadata for c in chunks],
    )
    print(f"Upsert selesai: {len(chunks)} chunk ke koleksi '{CHROMA_COLLECTION_NAME}'.")


def main() -> None:
    files = load_chunk_files()
    print(f"Ditemukan {len(files)} file .md di corpus/")

    chunks = [c for c in (parse_chunk(f) for f in files) if c is not None]
    print(f"{len(chunks)} chunk valid, {len(files) - len(chunks)} di-skip.")

    embed_and_upsert(chunks)


if __name__ == "__main__":
    main()
