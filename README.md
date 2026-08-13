# medinova-rag-lab

Server B (AI Tier) untuk fitur draft interpretasi hasil lab MCU — RAG + LLM on-premise, target deployment Mac Mini (Apple Silicon). Aplikasi terpisah dari `medinovav2` (Server A, Laravel + MySQL, tidak berubah); kedua sisi hanya bicara lewat HTTP API.

**Baca `ROADMAP.md` dulu sebelum menyentuh kode ini** — dokumen itu berisi analisis, keputusan arsitektur, dan alasan di baliknya. Logika `ingest/` dan `api/` sudah diimplementasikan (bukan skeleton kosong lagi), tapi **belum diuji end-to-end** — butuh dependency penuh (ChromaDB, Ollama) yang hanya bisa diverifikasi di lingkungan dengan model LLM benar-benar jalan (Mac Mini). Corpus baru berisi 6 dari ~40 chunk Interpretasi Lab yang direncanakan.

## Struktur

```
common/             config bersama (.env) dipakai ingest/ dan api/
corpus/             sumber kebenaran RAG — markdown + YAML frontmatter, satu file = satu chunk (6/~40 terisi)
ingest/             ingest.py — parse corpus/ → embed (bge-m3) → upsert ke ChromaDB (sudah diimplementasikan)
api/                FastAPI: retrieval hybrid + panggilan Ollama + structured output (sudah diimplementasikan)
data/vectorstore/   persistence ChromaDB (gitignored, derived dari corpus/)
scripts/            POC_PROCEDURE.md + benchmark_model.py untuk POC LLM serving di Mac Mini
tests/              test_ingest.py — parse_chunk terhadap 6 chunk corpus nyata
```

## Status

Kode inti (`ingest/`, `api/`) sudah diimplementasikan dan lolos syntax-check + test parsing corpus, tapi belum diuji end-to-end (butuh ChromaDB/Ollama nyata). Lihat §11 di `ROADMAP.md` untuk status detail per fase.

## Cara mulai (di Mac Mini)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # isi API_AUTH_TOKEN, sesuaikan OLLAMA_MODEL kalau perlu

# 1. POC model LLM dulu (scripts/POC_PROCEDURE.md) - pilih model produksi
# 2. Ingest corpus yang sudah ada (baru 6 chunk, lihat corpus/README.md)
python -m ingest.ingest

# 3. Jalankan API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Test parsing corpus (tidak butuh Ollama/ChromaDB berjalan)
pytest tests/
```

## Prasyarat sebelum produksi

1. POC LLM Serving dijalankan nyata di Mac Mini (`scripts/POC_PROCEDURE.md`) — belum dieksekusi.
2. Sisa ~34 chunk Interpretasi Lab + kategori lain diisi — butuh `Excel_Hasil_MCU-interpretasi_dan_tindak_lanjut.xlsx` (lihat `ROADMAP.md` §12).
3. Topologi jaringan Mac Mini ↔ `medinovav2` dipastikan (`ROADMAP.md` §14).
