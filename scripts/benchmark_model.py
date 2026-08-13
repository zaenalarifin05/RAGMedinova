"""Benchmark token/detik untuk satu model Ollama - dijalankan di Mac Mini.

Bagian dari prosedur POC di scripts/POC_PROCEDURE.md (ROADMAP.md §11 Fase 3).
Pakai prompt & panjang output yang mendekati kasus nyata (narasi ~500-800
token, sesuai contoh di Desain-AI-Executive-Insight-Opsi-B.md §2.3 milik
medinovav2) supaya hasilnya sebanding dengan estimasi di ROADMAP.md §3.

Pemakaian:
    python scripts/benchmark_model.py --model qwen2.5:7b
"""

from __future__ import annotations

import argparse
import time

import ollama

BENCHMARK_PROMPT = (
    "Tulis narasi edukasi kesehatan sepanjang sekitar 600 kata dalam Bahasa "
    "Indonesia formal tentang pentingnya pemeriksaan kesehatan berkala di "
    "tempat kerja, mencakup manfaat deteksi dini, contoh pemeriksaan yang "
    "umum dilakukan, dan rekomendasi tindak lanjut bagi karyawan."
)


def run_benchmark(model: str, host: str) -> None:
    client = ollama.Client(host=host)

    print(f"Model: {model}")
    print("Memanggil Ollama (termasuk waktu load model kalau belum di-cache)...")

    start = time.perf_counter()
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": BENCHMARK_PROMPT}],
    )
    elapsed = time.perf_counter() - start

    eval_count = response.get("eval_count")
    eval_duration_ns = response.get("eval_duration")

    print(f"Total waktu (termasuk overhead): {elapsed:.1f} detik")
    if eval_count and eval_duration_ns:
        tok_per_sec = eval_count / (eval_duration_ns / 1e9)
        print(f"Token dihasilkan: {eval_count}")
        print(f"Kecepatan generate murni: {tok_per_sec:.1f} token/detik")
        print(f"Estimasi di ROADMAP.md §3: ~15-20 token/detik untuk kelas 7-8B di M4 dasar")
    else:
        print("Ollama tidak mengembalikan eval_count/eval_duration - cek versi Ollama.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Nama model Ollama, mis. qwen2.5:7b")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    run_benchmark(args.model, args.host)
