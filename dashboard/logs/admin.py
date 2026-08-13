from django.contrib import admin

from .models import LlmFindingLog, LlmRequestLog


class LlmFindingLogInline(admin.TabularInline):
    model = LlmFindingLog
    extra = 0
    readonly_fields = ["parameter", "arah", "grounded", "istilah_klinis", "narasi_excerpt", "catatan"]
    can_delete = False


@admin.register(LlmRequestLog)
class LlmRequestLogAdmin(admin.ModelAdmin):
    list_display = [
        "case_ref", "requested_at", "status", "latency_ms",
        "findings_total", "findings_grounded", "findings_ungrounded", "model_used",
    ]
    list_filter = ["status", "model_used", "requested_at"]
    search_fields = ["case_ref", "error_message"]
    date_hierarchy = "requested_at"
    readonly_fields = [f.name for f in LlmRequestLog._meta.fields]
    inlines = [LlmFindingLogInline]

    def has_add_permission(self, request):
        # Log hanya ditulis oleh api/main.py lewat common/audit_log.py, bukan
        # lewat admin - cegah entri manual yang bisa mengaburkan audit trail.
        return False


@admin.register(LlmFindingLog)
class LlmFindingLogAdmin(admin.ModelAdmin):
    list_display = ["request", "parameter", "arah", "grounded", "istilah_klinis"]
    list_filter = ["grounded", "parameter", "arah"]
    search_fields = ["parameter", "narasi_excerpt"]
    readonly_fields = [f.name for f in LlmFindingLog._meta.fields]

    def has_add_permission(self, request):
        return False
