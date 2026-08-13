"""Seed data simulasi untuk dashboard - dijalankan dari root repo.

Memanggil FUNGSI PRODUKSI ASLI `common.audit_log.log_request()`, sama persis
yang dipanggil `api/main.py` tiap request nyata - bukan insert langsung ke
Django ORM. Jadi skrip ini juga jadi verifikasi tambahan bahwa audit_log.py
benar-benar bisa menulis ke MySQL sungguhan, bukan cuma lolos syntax-check.

Data yang disimulasikan sengaja campuran: parameter yang SUDAH ada chunk-nya
di corpus/interpretasi_lab/ (grounded=True mayoritas) dan yang BELUM
(grounded=False) - supaya panel "parameter paling sering tidak grounded" di
dashboard punya data yang realistis untuk didemokan.

Pemakaian:
    python scripts/seed_demo_data.py --count 100
"""

from __future__ import annotations

import argparse
import datetime as dt
import random

from common import audit_log

# Parameter yang SUDAH punya chunk (lihat corpus/interpretasi_lab/) - lihat
# ROADMAP.md §6 untuk daftar lengkapnya.
GROUNDED_PARAMS = [
    ("HB (Hemoglobin)", "di_bawah_normal", "Anemia"),
    ("HB (Hemoglobin)", "di_atas_normal", "Polisitemia"),
    ("Trombosit", "di_bawah_normal", "Trombositopenia"),
    ("Gula Darah Puasa", "di_atas_normal", "Hiperglikemia"),
    ("Kolesterol Total", "di_atas_normal", "Hiperkolesterolemia"),
    ("Kolinesterase", "di_bawah_normal", "Kolinesterase menurun"),
]

# Parameter yang BELUM punya chunk (menunggu Excel sumber, ROADMAP.md §12) -
# disimulasikan supaya ada temuan grounded=False yang realistis.
UNGROUNDED_PARAMS = [
    ("Trigliserida", "di_atas_normal"),
    ("Asam Urat", "di_atas_normal"),
    ("Kreatinin", "di_atas_normal"),
    ("SGOT", "di_atas_normal"),
    ("SGPT", "di_atas_normal"),
    ("LDL", "di_atas_normal"),
    ("Kolesterol Total", "di_bawah_normal"),  # sengaja tidak ada rujukannya (lihat corpus)
    ("Gula Darah 2 Jam PP", "di_atas_normal"),
]

MODELS = ["qwen2.5:7b"] * 8 + ["llama3.1:8b"] * 2 + ["tinyllama"] * 1  # bobot: mayoritas default


def _fake_case_ref(i: int) -> str:
    return f"MCU-2026-{10000 + i:05d}"


def _random_requested_at() -> dt.datetime:
    now = dt.datetime.now(dt.timezone.utc)
    delta = dt.timedelta(
        days=random.randint(0, 7),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return now - delta


def _simulate_one(i: int) -> None:
    requested_at = _random_requested_at()
    model_used = random.choice(MODELS)

    n_findings = random.randint(1, 4)
    entries: list[audit_log.FindingLogEntry] = []
    simulate_error = random.random() < 0.05  # ~5% error rate

    for _ in range(n_findings):
        if random.random() < 0.65:  # ~65% dari temuan adalah parameter yang grounded
            parameter, arah, istilah = random.choice(GROUNDED_PARAMS)
            entries.append(audit_log.FindingLogEntry(
                parameter=parameter, arah=arah, grounded=True, istilah_klinis=istilah,
                narasi_excerpt=f"[SIMULASI] Draf narasi untuk {parameter} ({arah}) - {istilah}...",
            ))
        else:
            parameter, arah = random.choice(UNGROUNDED_PARAMS)
            entries.append(audit_log.FindingLogEntry(
                parameter=parameter, arah=arah, grounded=False,
                catatan="Belum ada rujukan internal untuk kombinasi parameter+arah ini",
            ))

    grounded_count = sum(1 for e in entries if e.grounded)
    # Latensi kasar: ~1.5-3.5 detik overhead + ~5-9 detik per temuan yang butuh
    # panggilan LLM (kelas 7-8B di Mac Mini, lihat ROADMAP.md §3), plus noise.
    latency_ms = int(random.uniform(1500, 3500) + grounded_count * random.uniform(5000, 9000))
    responded_at = requested_at + dt.timedelta(milliseconds=latency_ms)

    error_message = None
    if simulate_error:
        error_message = "[SIMULASI] ConnectionError: Ollama tidak merespons dalam batas waktu"
        status = "error"
    elif grounded_count == len(entries):
        status = "success"
    else:
        status = "partial"

    audit_log.log_request(
        case_ref=_fake_case_ref(i),
        requested_at=requested_at,
        responded_at=responded_at,
        model_used=model_used,
        status=status,
        findings=entries,
        error_message=error_message,
        source_ip=f"10.20.0.{random.randint(2, 254)}",  # simulasi IP Server A di VPN privat
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()

    for i in range(args.count):
        _simulate_one(i)
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{args.count} tersimulasi...")

    print(f"Selesai: {args.count} request simulasi ditulis ke MySQL ({audit_log.settings.mysql_database}).")


if __name__ == "__main__":
    main()
