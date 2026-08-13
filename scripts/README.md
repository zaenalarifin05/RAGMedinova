Ops scripts (belum ada isinya — Fase 3, ROADMAP.md §11):

- `start_ollama.sh` — pastikan Ollama jalan + model default (`qwen2.5:7b`) sudah di-pull
- `healthcheck.sh` — cek `/healthz` API + status Ollama, dipakai untuk kill switch/fallback (ROADMAP.md §10)
- `benchmark_model.py` — ukur token/detik untuk tiap model kandidat di §5/§14 POC, bandingkan dengan estimasi §3
