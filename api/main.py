"""FastAPI app - Server B (AI Tier) untuk draft interpretasi lab.

Kontrak lengkap ada di ROADMAP.md §7. Endpoint ini dipanggil oleh
MacMiniRagProvider dari medinovav2 (ROADMAP.md §8).

Jalankan (dari root repo): `uvicorn api.main:app --host 0.0.0.0 --port 8000`
"""

from __future__ import annotations

import asyncio
import datetime as dt

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from api import llm, retrieval
from common import audit_log
from common.config import settings

app = FastAPI(title="medinova-rag-lab", version="0.1.0")

# Concurrency guard - ROADMAP.md §3: Mac Mini 16GB, batasi request paralel
# supaya KV cache Ollama tidak melipatgandakan pemakaian RAM.
_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)


class AbnormalFinding(BaseModel):
    parameter: str
    arah: str  # "di_atas_normal" | "di_bawah_normal"
    value: float | None = None
    unit: str | None = None
    reference_range: str | None = None


class Context(BaseModel):
    age: int | None = None
    gender: str | None = None
    occupation_hazard_category: str | None = None


class LabInterpretationRequest(BaseModel):
    case_ref: str
    context: Context
    abnormal_findings: list[AbnormalFinding]


def verify_token(authorization: str | None = Header(default=None)) -> None:
    if not settings.api_auth_token:
        # Belum dikonfigurasi (mis. saat dev lokal) - tolak by default, jangan
        # diam-diam terbuka tanpa auth.
        raise HTTPException(status_code=500, detail="API_AUTH_TOKEN belum dikonfigurasi di server")
    expected = f"Bearer {settings.api_auth_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/v1/lab-interpretation", dependencies=[Depends(verify_token)])
async def lab_interpretation(payload: LabInterpretationRequest, request: Request) -> dict:
    """Lihat ROADMAP.md §7 untuk skema request/response lengkap.

    Tiap request dicatat ke MySQL lewat common.audit_log setelah response
    tersusun (lihat dashboard/ untuk UI baca log ini) - kegagalan logging
    tidak pernah menggagalkan response ke Server A (fail-open, ROADMAP §10).
    """
    requested_at = dt.datetime.now(dt.timezone.utc)
    log_entries: list[audit_log.FindingLogEntry] = []
    error_message: str | None = None

    async with _semaphore:
        findings_out = []
        for finding in payload.abnormal_findings:
            retrieved = retrieval.retrieve_by_parameter_arah(finding.parameter, finding.arah)

            if not retrieved.grounded:
                catatan = (
                    "Belum ada rujukan internal untuk kombinasi parameter+arah ini "
                    "- perlu ditinjau manual, TIDAK di-generate oleh AI"
                )
                findings_out.append({
                    "parameter": finding.parameter,
                    "arah": finding.arah,
                    "grounded": False,
                    "catatan": catatan,
                })
                log_entries.append(audit_log.FindingLogEntry(
                    parameter=finding.parameter, arah=finding.arah, grounded=False, catatan=catatan,
                ))
                continue

            narrative = await asyncio.to_thread(
                llm.generate_narrative,
                retrieved.body,
                finding.parameter,
                finding.arah,
                retrieved.istilah_klinis,
            )

            if "error" in narrative:
                catatan = f"Gagal generate narasi via LLM: {narrative['error']}"
                error_message = narrative["error"]
                findings_out.append({
                    "parameter": finding.parameter,
                    "arah": finding.arah,
                    "grounded": False,
                    "catatan": catatan,
                })
                log_entries.append(audit_log.FindingLogEntry(
                    parameter=finding.parameter, arah=finding.arah, grounded=False, catatan=catatan,
                ))
                continue

            findings_out.append({
                "parameter": finding.parameter,
                "arah": finding.arah,
                "istilah_klinis": retrieved.istilah_klinis,
                "narasi": narrative.get("narasi"),
                "saran_pasien": narrative.get("saran_pasien"),
                "tindak_lanjut": narrative.get("tindak_lanjut"),
                "pemeriksaan_lanjutan": narrative.get("pemeriksaan_lanjutan", []),
                "sumber": retrieved.sumber,
                "grounded": True,
            })
            log_entries.append(audit_log.FindingLogEntry(
                parameter=finding.parameter, arah=finding.arah, grounded=True,
                istilah_klinis=retrieved.istilah_klinis, narasi_excerpt=narrative.get("narasi"),
            ))

        responded_at = dt.datetime.now(dt.timezone.utc)
        grounded_all = all(e.grounded for e in log_entries) if log_entries else True
        status = "error" if error_message else ("success" if grounded_all else "partial")

        await asyncio.to_thread(
            audit_log.log_request,
            payload.case_ref, requested_at, responded_at, settings.ollama_model,
            status, log_entries, error_message,
            request.client.host if request.client else None,
        )

        return {
            "case_ref": payload.case_ref,
            "findings": findings_out,
            "model_used": settings.ollama_model,
            "generated_at": responded_at.isoformat(),
        }
