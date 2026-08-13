"""Konfigurasi bersama untuk ingest/ dan api/ - dibaca dari .env (lihat .env.example).

Dipakai oleh kedua sisi supaya nama koleksi Chroma dan model embedding selalu
konsisten antara proses ingest dan proses retrieval saat runtime (ROADMAP.md §6).
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO_ROOT / "corpus"

# Nama koleksi Chroma - satu koleksi untuk seluruh corpus, dibedakan lewat
# metadata (kategori/parameter/arah), bukan lewat banyak koleksi terpisah.
CHROMA_COLLECTION_NAME = "mcu_rag_corpus"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    embedding_model: str = "BAAI/bge-m3"
    chroma_persist_dir: str = "./data/vectorstore"
    context_window_tokens: int = 8192
    api_auth_token: str = ""
    max_concurrent_requests: int = 1

    # MySQL - audit log untuk dashboard (dashboard/), lihat common/audit_log.py.
    # Server B TIDAK PERNAH menyimpan kredensial MySQL milik medinovav2 (Server A) -
    # ini database terpisah, khusus log traffic LLM, tanpa data pasien.
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "medinova_rag_logs"
    mysql_user: str = "rag_dashboard"
    mysql_password: str = ""

    @property
    def chroma_persist_path(self) -> Path:
        p = Path(self.chroma_persist_dir)
        return p if p.is_absolute() else REPO_ROOT / p


settings = Settings()
