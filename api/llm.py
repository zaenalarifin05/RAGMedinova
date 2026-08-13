"""Client tipis ke Ollama untuk generate narasi dari chunk yang di-retrieve.

Lihat ROADMAP.md §3 (model kandidat, batas RAM 16GB Mac Mini M4) dan §5
(default produksi: Qwen2.5 7B).

Batasan yang dipatuhi di sini (ROADMAP.md §3):
- context window dibatasi via settings.context_window_tokens (default 8192,
  jangan pakai default besar Ollama - boros KV cache di RAM 16GB yang mepet)
- system prompt eksplisit melarang mengarang angka/rujukan (pola sama dengan
  system prompt Opsi B §2.1 di medinovav2/Desain-AI-Executive-Insight-Opsi-B.md)
- kegagalan (timeout, model tidak jalan, dst.) TIDAK bocor sebagai exception
  ke caller - dikembalikan sebagai dict dengan "error", supaya main.py bisa
  tetap merespons terstruktur (ROADMAP.md §10 kill switch/fallback)
"""

from __future__ import annotations

import json

import ollama

from common.config import settings

SYSTEM_PROMPT = """\
Anda adalah asisten penulisan draf interpretasi hasil laboratorium MCU untuk \
tim medis, dalam Bahasa Indonesia formal. Draf ini akan direview dan \
difinalisasi oleh dokter sebelum dipakai - Anda TIDAK membuat keputusan \
klinis final.

ATURAN WAJIB:
- Sumber informasi Anda HANYA teks rujukan yang diberikan di bawah (bagian \
  "RUJUKAN"). JANGAN gunakan pengetahuan medis umum Anda untuk menambah \
  detail yang tidak ada di rujukan tersebut.
- JANGAN mengarang angka, nilai ambang batas, atau nama pemeriksaan yang \
  tidak disebut eksplisit di rujukan.
- Susun ulang isi rujukan menjadi narasi yang mengalir, TANPA mengubah makna \
  klinisnya atau menambah klaim baru.
- Keluarkan HANYA JSON sesuai skema yang diminta - tidak ada teks di luar JSON.
"""


def generate_narrative(rujukan_text: str, parameter: str, arah: str, istilah_klinis: str) -> dict:
    """Panggil Ollama, minta narasi terstruktur dari satu chunk rujukan yang grounded.

    Return dict dengan keys: narasi, saran_pasien, tindak_lanjut,
    pemeriksaan_lanjutan (list[str]). Kalau gagal, return dict dengan key "error".
    """
    user_prompt = (
        f"RUJUKAN untuk parameter '{parameter}' (arah: {arah}, istilah klinis: "
        f"{istilah_klinis}):\n\n{rujukan_text}\n\n"
        "Tulis ulang jadi JSON dengan skema persis:\n"
        '{"narasi": "...", "saran_pasien": "...", "tindak_lanjut": "...", '
        '"pemeriksaan_lanjutan": ["...", "..."]}'
    )

    try:
        client = ollama.Client(host=settings.ollama_host)
        response = client.chat(
            model=settings.ollama_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            format="json",
            options={"num_ctx": settings.context_window_tokens},
        )
        return json.loads(response["message"]["content"])
    except Exception as exc:  # noqa: BLE001 - sengaja luas, lihat docstring modul
        return {"error": f"{type(exc).__name__}: {exc}"}
