# medinova-rag-lab

Server B (AI Tier) untuk fitur draft interpretasi hasil lab MCU — RAG + LLM on-premise, target deployment Mac Mini (Apple Silicon). Aplikasi terpisah dari `medinovav2` (Server A, Laravel + MySQL, tidak berubah); kedua sisi hanya bicara lewat HTTP API.

**Baca `ROADMAP.md` dulu sebelum menyentuh kode ini** — dokumen itu berisi analisis, keputusan arsitektur, dan alasan di baliknya. Repo ini masih tahap skeleton: struktur folder dan kerangka kode sudah ada, tapi logika ingest/retrieval/API belum diisi (menunggu Fase 1–2 di roadmap: lengkapi corpus + isi ambang batas data yang masih kosong).

## Struktur

```
corpus/            sumber kebenaran RAG — markdown + YAML frontmatter, satu file = satu chunk
ingest/             script parse corpus/ → embed → upsert ke ChromaDB
api/                FastAPI: retrieval hybrid + panggilan Ollama + structured output
data/vectorstore/   persistence ChromaDB (gitignored, derived dari corpus/)
scripts/            ops: start Ollama, healthcheck, benchmark model
tests/
```

## Status

Skeleton saja — lihat §11 di `ROADMAP.md` untuk status per fase.

## Prasyarat sebelum bisa dijalankan

1. Mac Mini dengan Ollama terinstall (lihat `ROADMAP.md` §3 untuk kandidat model & pertimbangan RAM).
2. Corpus di `corpus/` sudah diisi (belum ada isinya sama sekali saat ini — lihat `ROADMAP.md` §12 untuk prasyarat data yang masih kosong).
3. Python 3.11+, `pip install -r requirements.txt`.
