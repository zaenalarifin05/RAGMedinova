# Prosedur POC LLM Serving (Fase 3, ROADMAP.md §11)

Dijalankan langsung di Mac Mini (M4 dasar, 10-core CPU/10-core GPU, 16GB RAM, 256GB SSD) — bukan di mesin dev. Tujuan: pilih model produksi (default dugaan: Qwen2.5 7B, ROADMAP.md §5) berdasarkan hasil nyata, bukan asumsi, dan validasi estimasi kecepatan `~15–20 token/detik` di ROADMAP.md §3.

## 1. Install Ollama

```bash
brew install ollama
# atau download installer dari ollama.com kalau tidak pakai Homebrew
ollama serve   # jalankan di background/terminal terpisah, atau lewat app menu bar
```

Verifikasi:
```bash
curl http://127.0.0.1:11434/api/tags
```

## 2. Pull model kandidat

Sesuai ROADMAP.md §5/§14 — kelas 7–8B karena RAM 16GB, 14B hanya pembanding kualitas (jangan produksi):

```bash
ollama pull qwen2.5:7b        # default produksi (kandidat utama)
ollama pull llama3.1:8b       # pembanding
ollama pull tinyllama          # eksperimental, cek RAM/kecepatan vs kualitas (ROADMAP.md §5)
# fine-tune Bahasa Indonesia (Komodo-7B / Sahabat-AI) - cek ketersediaan tag Ollama-nya dulu,
# kalau tidak ada di library resmi, mungkin perlu import GGUF manual (ollama create)
```

**Housekeeping SSD 256GB** (ROADMAP.md §3): setelah POC selesai dan model produksi dipilih, hapus kandidat yang tidak dipakai:
```bash
ollama rm llama3.1:8b tinyllama   # contoh, sesuaikan dengan hasil POC
```

## 3. Jalankan benchmark

Dari root repo (`medinova-rag-lab`), pakai script `scripts/benchmark_model.py`:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install ollama
python scripts/benchmark_model.py --model qwen2.5:7b
python scripts/benchmark_model.py --model llama3.1:8b
python scripts/benchmark_model.py --model tinyllama
```

Script ini mengukur token/detik nyata dan membandingkan dengan estimasi `~15–20 tok/s` di ROADMAP.md §3. Kalau hasilnya jauh meleset (mis. jauh lebih lambat karena thermal throttling atau proses lain jalan bersamaan), catat kondisinya.

## 4. Uji kualitas narasi (bukan cuma kecepatan)

Untuk tiap model kandidat, generate narasi dari salah satu chunk contoh di `corpus/interpretasi_lab/lab_kolesterol_total_tinggi.md` memakai prompt yang persis sama dengan `api/llm.py::SYSTEM_PROMPT` + `generate_narrative()`. Cek manual terhadap kriteria di ROADMAP.md §13:

- [ ] Tidak ada angka yang dikarang (bandingkan dengan isi chunk asli)
- [ ] Tidak ada rujukan/istilah yang tidak ada di chunk
- [ ] Output valid JSON sesuai skema (`narasi`, `saran_pasien`, `tindak_lanjut`, `pemeriksaan_lanjutan`)
- [ ] Bahasa Indonesia natural, bukan terjemahan kaku

Model yang gagal salah satu kriteria di atas **tidak layak jadi default produksi**, walau cepat/hemat RAM (ROADMAP.md §5, catatan soal TinyLlama).

## 5. Catat hasil

Isi tabel ini di `ROADMAP.md` §11 (update baris Fase 3) atau di sini setelah POC selesai:

| Model | Token/detik nyata | RAM terpakai (Activity Monitor) | Lolos kriteria kualitas §13? | Catatan |
|---|---|---|---|---|
| qwen2.5:7b | | | | |
| llama3.1:8b | | | | |
| tinyllama | | | | |

Model terpilih jadi default di `.env` (`OLLAMA_MODEL=...`).
