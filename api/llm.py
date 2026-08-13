"""Client tipis ke Ollama untuk generate narasi dari chunk yang di-retrieve.

Skeleton - lihat ROADMAP.md §3 (model kandidat, batas RAM 16GB Mac Mini M4)
dan §5 (default produksi: Qwen2.5 7B; TinyLlama sebagai kandidat eksperimental).

Batasan yang WAJIB dipatuhi implementasi nyata (ROADMAP.md §3):
- context window dibatasi 4K-8K token (jangan pakai default besar - boros KV cache
  di RAM 16GB yang sudah mepet)
- concurrency dibatasi ke 1 request pada satu waktu (queue, bukan paralel)
- system prompt HARUS eksplisit melarang mengarang angka/rujukan (pola sama
  dengan system prompt Opsi B §2.1 di Roadmap-Pengembangan-Berikutnya.md /
  Desain-AI-Executive-Insight-Opsi-B.md milik medinovav2)
"""

from __future__ import annotations

import os


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")


def generate_narrative(system_prompt: str, user_payload: dict) -> dict:
    """Panggil Ollama, minta output terstruktur sesuai skema di ROADMAP.md §7.

    TODO Fase 4:
    - pakai client `ollama` python package, format=json (structured output)
    - batasi num_ctx sesuai CONTEXT_WINDOW_TOKENS dari .env
    - tangani timeout/error -> kembalikan grounded=False + catatan error,
      JANGAN biarkan exception bocor ke response (ROADMAP.md §10 kill switch/fallback)
    """
    raise NotImplementedError("TODO: Fase 4 - panggilan Ollama + structured output")
