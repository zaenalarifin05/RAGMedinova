"""Dashboard observasi traffic LLM - lihat ROADMAP.md §10 prinsip #8.

Satu halaman ringkasan (bukan SPA): statistik agregat + daftar temuan yang
paling sering TIDAK grounded (sinyal langsung parameter mana di corpus yang
paling butuh dilengkapi duluan, lihat ROADMAP.md §12) + daftar request terbaru.
Detail per-request/per-finding sebaiknya dilihat lewat Django admin (/admin/),
yang sudah dapat filter+search gratis - halaman ini murni untuk "sekali lihat".
"""

from __future__ import annotations

import datetime as dt

from django.db.models import Avg, Count
from django.shortcuts import render
from django.utils import timezone

from .models import LlmFindingLog, LlmRequestLog


def overview(request):
    now = timezone.now()
    since_24h = now - dt.timedelta(hours=24)
    since_7d = now - dt.timedelta(days=7)

    recent_7d = LlmRequestLog.objects.filter(requested_at__gte=since_7d)
    total_24h = LlmRequestLog.objects.filter(requested_at__gte=since_24h).count()
    total_7d = recent_7d.count()

    status_breakdown = list(recent_7d.values("status").annotate(count=Count("id")).order_by("-count"))
    avg_latency_ms = recent_7d.aggregate(avg=Avg("latency_ms"))["avg"]

    findings_7d = LlmFindingLog.objects.filter(request__requested_at__gte=since_7d)
    findings_total = findings_7d.count()
    findings_grounded = findings_7d.filter(grounded=True).count()
    grounded_rate = (findings_grounded / findings_total * 100) if findings_total else None

    top_ungrounded = (
        findings_7d.filter(grounded=False)
        .values("parameter", "arah")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    recent_requests = LlmRequestLog.objects.all()[:25]

    context = {
        "total_24h": total_24h,
        "total_7d": total_7d,
        "status_breakdown": status_breakdown,
        "avg_latency_ms": round(avg_latency_ms) if avg_latency_ms else None,
        "grounded_rate": round(grounded_rate, 1) if grounded_rate is not None else None,
        "findings_total_7d": findings_total,
        "top_ungrounded": top_ungrounded,
        "recent_requests": recent_requests,
    }
    return render(request, "logs/overview.html", context)
