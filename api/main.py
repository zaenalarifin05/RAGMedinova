"""FastAPI app - Server B (AI Tier) untuk draft interpretasi lab.

Skeleton - kontrak lengkap ada di ROADMAP.md §7. Endpoint ini yang akan
dipanggil MacMiniRagProvider dari medinovav2 (ROADMAP.md §8).

Belum diimplementasikan: auth (Bearer token dari .env API_AUTH_TOKEN),
retrieval (retrieval.py), pemanggilan LLM (llm.py), rate limiting/concurrency
guard (ROADMAP.md §3, §10).
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="medinova-rag-lab", version="0.0.0-skeleton")


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


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/v1/lab-interpretation")
def lab_interpretation(payload: LabInterpretationRequest) -> dict:
    """Lihat ROADMAP.md §7 untuk skema request/response lengkap.

    TODO Fase 4:
    1. Validasi Authorization: Bearer <API_AUTH_TOKEN>
    2. Untuk tiap abnormal_findings: retrieval.retrieve_by_parameter_arah()
    3. Susun prompt (grounding rules + chunk yang ditemukan) -> llm.generate_narrative()
    4. Untuk chunk yang tidak ketemu -> findings[i].grounded = False, JANGAN panggil LLM
       untuk mengarang isinya (ROADMAP.md §4 prinsip anti-halusinasi)
    5. Batasi concurrency ke MAX_CONCURRENT_REQUESTS (.env, default 1)
    """
    raise NotImplementedError("TODO: Fase 4 - lihat urutan di docstring di atas")
