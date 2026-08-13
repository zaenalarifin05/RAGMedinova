"""Hybrid retrieval: filter metadata (deterministik) + semantic search (fallback).

Skeleton — lihat ROADMAP.md §4 untuk desain lengkap.

Alur yang direncanakan untuk setiap abnormal_finding di request (ROADMAP.md §7):
1. Filter metadata dulu: cari chunk di Chroma dengan metadata parameter==X DAN
   arah==Y (exact match, bukan similarity search). Ini presisi 100% karena
   parameter+arah pasien sudah diketahui pasti dari data lab (bukan perlu ditebak).
2. Kalau ketemu -> pakai langsung, tandai grounded=True.
3. Kalau TIDAK ketemu -> JANGAN fallback ke semantic search untuk kasus
   parameter+arah yang terstruktur ini (itu prinsip anti-halusinasi §4:
   kombinasi yang tidak ada rujukannya harus dilaporkan grounded=False,
   bukan "dicari-cari" jawabannya lewat similarity search).
4. Semantic search dipakai HANYA untuk kategori lain yang query-nya tidak
   seketat parameter+arah (mis. temuan pemeriksaan fisik/anamnesis yang lebih
   naratif) - lihat corpus/pemeriksaan_fisik/.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    grounded: bool
    istilah_klinis: str | None = None
    narasi_source_text: str | None = None
    sumber: str | None = None


def retrieve_by_parameter_arah(parameter: str, arah: str) -> RetrievedChunk:
    """Filter metadata deterministik - lihat docstring modul ini poin 1-3."""
    raise NotImplementedError("TODO: Fase 4 - query Chroma dengan where={parameter, arah}")


def retrieve_semantic(query_text: str, kategori: str) -> list[RetrievedChunk]:
    """Semantic search fallback untuk kategori non-parameter+arah (mis. pemeriksaan fisik)."""
    raise NotImplementedError("TODO: Fase 4 - embed query_text (lazy-load bge-m3) + similarity search")
