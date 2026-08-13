# Dashboard Traffic LLM

Django app untuk observasi & review lalu lintas request/response ke LLM on-premise (`api/` FastAPI) — dijalankan di Server B yang sama (Mac Mini), sebagai proses terpisah dari FastAPI. Tidak menyimpan data pasien: hanya metadata traffic (parameter+arah yang ditanya, status grounded, latensi, model). Latar belakang keputusan ada di `ROADMAP.md` §10 prinsip #8 (audit log & redaksi).

## Bagaimana logging bekerja

`api/main.py` (FastAPI) menulis langsung ke tabel MySQL lewat `common/audit_log.py` (raw SQL via PyMySQL) — **bukan** lewat Django. Django di sini murni lapisan baca: admin bawaan (`/admin/`) untuk filter/cari detail, plus satu halaman ringkasan (`/`) untuk sekali-lihat. Skema tabel didefinisikan di `logs/models.py` — kalau field berubah di sana, query `INSERT` di `common/audit_log.py` harus disesuaikan juga (dicatat sebagai komentar di kedua file).

Prinsip fail-open: kalau MySQL tidak reachable, FastAPI tetap merespons ke Server A — logging cuma dicatat gagal ke stderr, tidak pernah menggagalkan fitur inti.

## Setup

```bash
# 1. Buat database + user MySQL (sekali saja)
mysql -u root -p -e "CREATE DATABASE medinova_rag_logs CHARACTER SET utf8mb4;"
mysql -u root -p -e "CREATE USER 'rag_dashboard'@'localhost' IDENTIFIED BY 'ganti-ini';"
mysql -u root -p -e "GRANT ALL ON medinova_rag_logs.* TO 'rag_dashboard'@'localhost';"

# 2. Isi .env di root repo (MYSQL_*, DJANGO_SECRET_KEY - lihat .env.example)

# 3. Install dependency (sama satu requirements.txt dengan FastAPI, dari root repo)
pip install -r ../requirements.txt

# 4. Migrasi skema + buat akun admin
cd dashboard
python manage.py migrate
python manage.py createsuperuser

# 5. Jalankan (port beda dari FastAPI yang di 8000)
python manage.py runserver 0.0.0.0:8001
```

Buka `http://127.0.0.1:8001/` untuk ringkasan, `http://127.0.0.1:8001/admin/` untuk detail per-request/per-temuan dengan filter.

## Yang ditampilkan di halaman ringkasan

- Volume request 24 jam / 7 hari, rerata latensi, tingkat grounded
- Breakdown status (success/partial/error)
- **Parameter yang paling sering `grounded: false`** — daftar ini langsung memberi tahu parameter mana di `corpus/` yang paling sering ditanyakan tapi belum ada rujukannya, jadi bisa jadi input prioritas untuk melengkapi corpus (ROADMAP.md §12)
- Request terbaru dengan tautan ke detail di admin

## Status

Skeleton lengkap (models, admin, view, migration ditulis tangan) — **belum diverifikasi jalan** karena Django/PyMySQL/MySQL tidak tersedia di lingkungan penulisan kode ini. Jalankan `python manage.py migrate` di lingkungan dengan dependency lengkap sebelum dipakai, dan bandingkan hasil migrasi dengan `logs/migrations/0001_initial.py` (kalau ada perbedaan skema, migration ini yang perlu diperbaiki, bukan `common/audit_log.py` yang jadi acuan).
