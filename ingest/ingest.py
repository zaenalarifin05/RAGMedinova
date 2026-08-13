"""Ingest pipeline: corpus/*.md -> embed (bge-m3) -> upsert ke ChromaDB.

Skeleton — belum diimplementasikan, menunggu corpus nyata (ROADMAP.md Fase 1-2).
Lihat ROADMAP.md §6 untuk desain pipeline lengkap dan §4 untuk alasan skema
metadata (parameter/arah) yang dipakai untuk filter deterministik saat retrieval.

Rencana alur:
1. Walk semua file .md di ../corpus/**/*.md (skip _TEMPLATE.md dan README.md).
2. Parse YAML frontmatter (id, kategori, parameter, arah, istilah_klinis,
   sumber, relevansi_k3) + body markdown.
3. Validasi: id unik, field wajib terisi (kalau kosong, skip + log warning -
   JANGAN memaksa isi kosong, prinsip anti-halusinasi di ROADMAP.md §1/§4).
4. Embed body text pakai sentence-transformers (BAAI/bge-m3).
5. Upsert ke koleksi Chroma di CHROMA_PERSIST_DIR, id = frontmatter id,
   metadata = seluruh field frontmatter (dipakai untuk filter di api/retrieval.py).

Dijalankan manual (`python ingest/ingest.py`) tiap kali corpus/ berubah.
"""

from __future__ import annotations

import pathlib

CORPUS_DIR = pathlib.Path(__file__).resolve().parent.parent / "corpus"


def load_chunk_files() -> list[pathlib.Path]:
    """Kumpulkan semua file .md di corpus/, skip template & README."""
    raise NotImplementedError("TODO: Fase 2 - walk corpus/, filter _TEMPLATE.md dan README.md")


def parse_chunk(path: pathlib.Path) -> dict:
    """Parse satu file chunk: frontmatter YAML + body markdown."""
    raise NotImplementedError("TODO: Fase 2 - parse frontmatter (pyyaml) + body")


def embed_and_upsert(chunks: list[dict]) -> None:
    """Embed body tiap chunk (bge-m3) dan upsert ke ChromaDB dengan metadata."""
    raise NotImplementedError("TODO: Fase 2 - sentence-transformers + chromadb upsert")


def main() -> None:
    files = load_chunk_files()
    chunks = [parse_chunk(f) for f in files]
    embed_and_upsert(chunks)


if __name__ == "__main__":
    main()
