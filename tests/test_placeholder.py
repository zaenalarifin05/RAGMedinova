"""Placeholder — belum ada test nyata sampai retrieval.py/main.py diimplementasikan (Fase 4).

Rencana test (lihat ROADMAP.md §13 Rencana Verifikasi):
- retrieval: parameter+arah yang punya chunk -> exact match, presisi 100%
- retrieval: parameter+arah yang TIDAK punya chunk -> grounded=False, bukan exception/halu
- api: request tanpa Bearer token yang valid -> 401
- api: Ollama tidak reachable -> response tetap terstruktur (fallback), bukan 500 polos
"""


def test_placeholder() -> None:
    assert True
