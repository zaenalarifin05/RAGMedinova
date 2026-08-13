"""Skema tabel audit log traffic LLM - INI YANG OTORITATIF.

FastAPI (common/audit_log.py) menulis ke tabel yang sama lewat SQL mentah
(bukan Django ORM, supaya proses request tidak perlu memuat Django) - nama
tabel dan kolom di sini HARUS tetap sinkron dengan query INSERT di
common/audit_log.py kalau field berubah.

Tidak ada data pasien di sini sama sekali (lihat ROADMAP.md §9) - hanya
metadata traffic: parameter+arah yang ditanya, status grounded, latensi.
"""

from django.db import models


class LlmRequestLog(models.Model):
    STATUS_CHOICES = [
        ("success", "Success - semua temuan grounded"),
        ("partial", "Partial - ada temuan tidak grounded"),
        ("error", "Error - LLM/pipeline gagal"),
    ]

    case_ref = models.CharField(max_length=100, db_index=True)
    requested_at = models.DateTimeField(db_index=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    error_message = models.TextField(null=True, blank=True)
    findings_total = models.IntegerField(default=0)
    findings_grounded = models.IntegerField(default=0)
    findings_ungrounded = models.IntegerField(default=0)
    source_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "llm_request_log"
        ordering = ["-requested_at"]

    def __str__(self) -> str:
        return f"{self.case_ref} @ {self.requested_at:%Y-%m-%d %H:%M} ({self.status})"


class LlmFindingLog(models.Model):
    request = models.ForeignKey(LlmRequestLog, related_name="findings", on_delete=models.CASCADE)
    parameter = models.CharField(max_length=150)
    arah = models.CharField(max_length=30)
    grounded = models.BooleanField()
    istilah_klinis = models.CharField(max_length=150, null=True, blank=True)
    narasi_excerpt = models.TextField(null=True, blank=True)
    catatan = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "llm_finding_log"

    def __str__(self) -> str:
        return f"{self.parameter} ({self.arah}) - {'grounded' if self.grounded else 'TIDAK grounded'}"
