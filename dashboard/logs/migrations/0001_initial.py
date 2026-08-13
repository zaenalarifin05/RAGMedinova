"""Migration awal - ditulis tangan (belum pernah dijalankan `makemigrations`
karena Django tidak terinstall di lingkungan penulisan kode ini). Verifikasi
`python manage.py migrate` dulu di lingkungan dengan dependency lengkap
sebelum dipakai produksi - lihat dashboard/README.md.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LlmRequestLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("case_ref", models.CharField(db_index=True, max_length=100)),
                ("requested_at", models.DateTimeField(db_index=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("latency_ms", models.IntegerField(blank=True, null=True)),
                ("model_used", models.CharField(blank=True, default="", max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("success", "Success - semua temuan grounded"),
                            ("partial", "Partial - ada temuan tidak grounded"),
                            ("error", "Error - LLM/pipeline gagal"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True, null=True)),
                ("findings_total", models.IntegerField(default=0)),
                ("findings_grounded", models.IntegerField(default=0)),
                ("findings_ungrounded", models.IntegerField(default=0)),
                ("source_ip", models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                "db_table": "llm_request_log",
                "ordering": ["-requested_at"],
            },
        ),
        migrations.CreateModel(
            name="LlmFindingLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("parameter", models.CharField(max_length=150)),
                ("arah", models.CharField(max_length=30)),
                ("grounded", models.BooleanField()),
                ("istilah_klinis", models.CharField(blank=True, max_length=150, null=True)),
                ("narasi_excerpt", models.TextField(blank=True, null=True)),
                ("catatan", models.TextField(blank=True, null=True)),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="findings",
                        to="logs.llmrequestlog",
                    ),
                ),
            ],
            options={
                "db_table": "llm_finding_log",
            },
        ),
    ]
