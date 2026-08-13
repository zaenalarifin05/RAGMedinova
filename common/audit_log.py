"""Tulis log request/response LLM ke MySQL, dibaca oleh dashboard Django (dashboard/).

Desain penting: FastAPI menulis LANGSUNG ke tabel MySQL yang skemanya
didefinisikan oleh migration Django (dashboard/logs/models.py, db_table
eksplisit) - FastAPI TIDAK memuat framework Django sama sekali, cukup PyMySQL.
Django murni jadi lapisan baca/tampil (admin + dashboard view).

Prinsip fail-open (sesuai ROADMAP.md §10 kill switch/fallback): kalau MySQL
tidak reachable atau gagal tulis, response utama ke Server A TETAP jalan -
logging adalah fungsi sekunder untuk observability, bukan boleh jadi titik
gagal untuk fitur inti. Kegagalan logging hanya dicatat ke stderr.
"""

from __future__ import annotations

import datetime as dt
import sys
from dataclasses import dataclass

import pymysql

from common.config import settings


@dataclass
class FindingLogEntry:
    parameter: str
    arah: str
    grounded: bool
    istilah_klinis: str | None = None
    narasi_excerpt: str | None = None
    catatan: str | None = None


def _get_connection():
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        autocommit=True,
        connect_timeout=3,
    )


def log_request(
    case_ref: str,
    requested_at: dt.datetime,
    responded_at: dt.datetime,
    model_used: str,
    status: str,  # "success" | "partial" | "error"
    findings: list[FindingLogEntry],
    error_message: str | None = None,
    source_ip: str | None = None,
) -> None:
    """Tulis satu baris request + baris temuan terkait. Tidak melempar exception
    ke caller - kegagalan logging tidak boleh menggagalkan response utama."""
    try:
        latency_ms = int((responded_at - requested_at).total_seconds() * 1000)
        grounded_count = sum(1 for f in findings if f.grounded)

        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO llm_request_log
                        (case_ref, requested_at, responded_at, latency_ms, model_used,
                         status, error_message, findings_total, findings_grounded,
                         findings_ungrounded, source_ip)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        case_ref, requested_at, responded_at, latency_ms, model_used,
                        status, error_message, len(findings), grounded_count,
                        len(findings) - grounded_count, source_ip,
                    ),
                )
                request_log_id = cur.lastrowid

                for f in findings:
                    cur.execute(
                        """
                        INSERT INTO llm_finding_log
                            (request_id, parameter, arah, grounded, istilah_klinis,
                             narasi_excerpt, catatan)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            request_log_id, f.parameter, f.arah, f.grounded,
                            f.istilah_klinis, f.narasi_excerpt, f.catatan,
                        ),
                    )
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 - sengaja luas, lihat docstring modul
        print(f"[audit_log] gagal menulis log (diabaikan, respons utama tetap jalan): {exc}", file=sys.stderr)
