# Roadmap Aplikasi RAG LLM On-Premise — Target Deployment Mac Mini

> **Status: rancangan/desain, belum ada kode yang berfungsi (skeleton saja).** Ini adalah salinan kerja dari dokumen yang aslinya ditulis di repo `medinovav2` (`Roadmap-RAG-LLM-OnPremise-MacMini.md`) — mulai sekarang, **dokumen di repo ini (`medinova-rag-lab/ROADMAP.md`) adalah versi yang diupdate seiring implementasi berjalan**, supaya proyek ini tetap portable (bisa dipindah ke Mac Mini tanpa bergantung ke folder `medinovav2`). Dokumen ini kelanjutan dari `Roadmap-LLM-OnPremise.md` §Skenario 2 (dua server terpisah, ditulis di repo `medinovav2`) — di sini Skenario 2 dikonkretkan: **Server A** adalah `medinovav2` (Laravel + MySQL, repo terpisah, tidak berubah), **Server B** adalah aplikasi di repo ini, dijalankan di **Mac Mini (Apple Silicon)**. Sumber materi RAG yang dipakai sebagai acuan pola chunking: `ragdoc/contoh_rag_interpretasi_lab.md.pdf` di repo `medinovav2` (dianalisis di §1).

---

## 1. Analisis Dokumen Contoh (`ragdoc/`)

Dokumen contoh yang sudah disiapkan menunjukkan pola chunking konkret dari sheet "Interpretasi Lab" (file `Excel_Hasil_MCU-interpretasi_dan_tindak_lanjut.xlsx`, 5 chunk contoh dari ~40 parameter). Poin penting yang saya catat dari situ, karena langsung menentukan desain di bawah:

- **Ini genuinely butuh vector search**, beda dari kasus `CDSS-Scoring-Rules.md` di Opsi B. Korpusnya banyak-dokumen (Interpretasi Lab ~40 param × 2 arah ≈ 60–80 chunk, ditambah sheet Diagnosis, Ax & Fisik, Rumus Pemx Fisik Lanjut, Kategori K1-K5, plus regulasi eksternal) — bukan satu file kecil yang cukup disertakan penuh ke prompt.
- **Skema chunk sudah didefinisikan**: satu chunk = satu parameter + satu arah, dengan frontmatter YAML terstruktur (`id`, `kategori`, `parameter`, `arah`, `istilah_klinis`, `sumber`, opsional `relevansi_k3`) + isi prosa (makna klinis, saran pasien, tindak lanjut, pemeriksaan lanjutan, paket terkait).
- **Retrieval idealnya hybrid**: filter metadata (`parameter` + `arah`) dulu — karena saat sistem generate draft interpretasi, `parameter`+`arah` yang abnormal **sudah diketahui pasti** dari data lab pasien (bukan perlu ditebak lewat semantic search) — baru pencarian semantik dipakai untuk kasus yang query-nya tidak seketat itu (mis. sheet Ax & Fisik yang lebih naratif).
- **Field kosong di sumber tidak boleh dipaksa diisi LLM** — prinsip anti-halusinasi eksplisit dari dokumen contoh (contoh: "Kolesterol Total di bawah normal" memang tidak ada rujukannya di sheet asli, jadi chunk-nya sengaja tidak dibuat).
- **Field `sumber` = provenance wajib** untuk audit klinis — dokter yang mereview draft AI harus bisa menelusuri rujukan asalnya.
- **Prasyarat yang masih kosong** (dicatat eksplisit oleh dokumen contoh sendiri):
  - Sheet "Diagnosis" (kriteria pre-diabetes/diabetes, pre-hipertensi/hipertensi, sindrom metabolik) masih **stub** — kolom "Hasil" kosong, perlu diisi ambang batas angka dulu sebelum bisa jadi sumber RAG yang valid.
  - Regulasi eksternal (Permenaker No. 5/2018, kriteria JNC 8, kriteria PERKENI) perlu diambil dari sumber resmi langsung — tidak boleh disalin mentah dari web karena isu lisensi.
  - ~35 parameter Interpretasi Lab lainnya belum dibuatkan chunk-nya (baru 5 contoh).

Ini artinya §12 (prasyarat) di dokumen ini **bukan sekadar checklist teknis** — ada pekerjaan non-teknis (isi ambang batas Diagnosis, kumpulkan teks regulasi resmi) yang harus selesai duluan sebelum ingest pipeline punya sumber yang valid untuk semua kategori.

---

## 2. Posisi dalam Arsitektur (Skenario 2, dikonkretkan)

```
┌─────────────────────────────┐                          ┌───────────────────────────────────┐
│  Server A — medinovav2       │   Jaringan privat/VPN     │  Server B — Mac Mini (Apple        │
│  (TIDAK BERUBAH)             │◀════ (Tailscale/WireGuard│  Silicon) — APLIKASI BARU,          │
│                               │      mTLS-equivalent) ══▶│  repo terpisah (repo ini)          │
│  Laravel + MySQL              │                          │                                     │
│  CdssService, McuRecordService│──── POST payload agregat│  FastAPI (orkestrasi RAG)           │
│  (data pasien tetap di sini) │      abnormal findings ─▶│  Chroma (vector store, embedded)    │
│                               │                          │  Ollama (LLM serving, Metal)        │
│  Kredensial DB: hanya di sini│                          │  TIDAK punya kredensial DB pasien    │
└─────────────────────────────┘                          └───────────────────────────────────┘
```

Prinsip dari `Roadmap-LLM-OnPremise.md` §Skenario 2 tetap berlaku penuh di sini: **Server B tidak pernah menyimpan/mengakses kredensial database pasien** — hanya menerima payload lewat API (parameter lab yang abnormal + arahnya + konteks agregat), generate draft interpretasi, kembalikan hasil terstruktur. Kalau Mac Mini disusupi, penyerang tidak otomatis dapat akses data pasien.

**Perbedaan dari Skenario 2 generik di roadmap sebelumnya**: di sana Server B diasumsikan server GPU datacenter-grade di jaringan privat/VLAN yang sama dengan Server A. Di sini Server B adalah **satu Mac Mini** — kemungkinan besar tidak berada di rack/data center yang sama dengan hosting `medinovav2`. Karena itu "jaringan privat" di sini saya rekomendasikan direalisasikan lewat **Tailscale atau WireGuard** (VPN mesh terenkripsi, setara mTLS secara fungsional) — bukan VLAN fisik — supaya tetap aman walau kedua server secara lokasi fisik terpisah (mis. Mac Mini di kantor, `medinovav2` di hosting/cloud). Kalau ternyata nanti keduanya memang satu LAN, VPN tetap boleh dipakai (defense-in-depth, prinsip #3 di roadmap keamanan) — tidak ada downside.

---

## 3. Pertimbangan Khusus Apple Silicon

Mac Mini memakai **unified memory** (RAM dipakai bersama CPU+GPU, bukan VRAM terpisah seperti GPU diskrit) — ini menentukan model terbesar yang layak dijalankan:

| Ukuran model (quantized 4-bit) | Perkiraan kebutuhan RAM | Muat di Mac Mini dengan RAM 16GB | 24GB | 32GB+ |
|---|---|---|---|---|
| 7–8B (Llama 3.1 8B, Qwen2.5 7B) | ~5–6GB | ✅ | ✅ | ✅ |
| 14B (Qwen2.5 14B) | ~9GB | ⚠️ mepet (harus sisakan RAM utk OS+embedding+vector store) | ✅ | ✅ |
| 32B (Qwen2.5 32B) | ~19GB | ❌ | ⚠️ mepet | ✅ |

> **Konfirmasi (2026-08-13): RAM Mac Mini yang tersedia sementara = 16GB.** Ini menentukan pilihan kelas model — lihat perkiraan budget RAM di bawah, dan revisi daftar kandidat di §5.
>
> | Komponen | Perkiraan RAM |
> |---|---|
> | macOS + proses latar belakang | ~3–4GB |
> | Model 8B (4-bit) + KV cache (context pendek) | ~6–7GB |
> | Embedding model (bge-m3) | ~1–2GB |
> | ChromaDB + FastAPI | ~0.3GB |
> | **Total** | **~11–13GB dari 16GB** — masih ada headroom tapi tidak banyak |
>
> **Keputusan**: kelas **7–8B jadi kandidat produksi default** di hardware ini; **14B didrop dari kandidat default** (hanya boleh dicoba sebagai pembanding kualitas/referensi batas atas, bukan pilihan produksi — risiko *swapping* ke SSD kalau dipaksakan, bikin latency tidak stabil). Mitigasi tambahan supaya 16GB ini tetap aman dipakai:
> - **Context window dibatasi** (4K–8K token) — kebutuhan RAG di sini pendek (payload agregat + beberapa chunk), tidak perlu context besar yang memboroskan KV cache.
> - **Concurrency dibatasi ke 1 request pada satu waktu** — servis ini untuk draft interpretasi dokter (trafik rendah), antre satu-satu lebih aman daripada proses paralel yang melipatgandakan KV cache.
> - **Embedding model di-lazy-load** — karena retrieval utama deterministik (filter metadata parameter+arah, §4), model embedding hanya dimuat saat benar-benar dibutuhkan (fallback semantic search), dilepas dari memori setelah idle untuk menghemat ~1–2GB.
>
> Kalau Mac Mini ini nanti jadi permanen untuk produksi (bukan sementara), upgrade ke 24GB akan memberi margin jauh lebih aman (14B jadi layak, concurrency lebih longgar) — dicatat sebagai pertimbangan upgrade di masa depan, bukan blocker untuk mulai POC sekarang.

> **Konfirmasi (2026-08-13): spesifikasi lengkap — Mac Mini M4 (varian dasar, bukan Pro/Max), 10-core CPU / 10-core GPU, RAM 16GB, SSD 256GB (SKU MU9D3ID).**
>
> Yang penting dari spek ini di luar RAM (§3 di atas): **M4 dasar punya bandwidth memori ~120GB/s** — jauh di bawah M4 Pro (~273GB/s) atau M4 Max (~546GB/s). Ini relevan karena generate token LLM (batch=1, kasus kita) umumnya *memory-bandwidth-bound*, bukan compute-bound — jadi kecepatan generate lebih ditentukan bandwidth ini daripada jumlah core GPU.
>
> **Perkiraan kecepatan** untuk model 8B kuantisasi 4-bit (~4.5GB bobot aktif per token): bandwidth 120GB/s ÷ ~4.5GB ≈ 26 token/detik teoretis maksimum; realistis (dengan overhead) diperkirakan **~15–20 token/detik**. Untuk narasi draft interpretasi sepanjang ~500–800 token (skala serupa contoh narasi Opsi B §2.3), ini berarti **~25–50 detik per generate** — cukup untuk alur "generate draft, dokter menunggu sebentar" yang memang sudah diasumsikan pakai loading state (bukan real-time chat), tapi bukan instan. Kalau nanti kecepatan ini dirasa terlalu lambat setelah POC, upgrade ke varian Pro (bandwidth jauh lebih tinggi) adalah opsi, bukan migrasi arsitektur.
>
> **SSD 256GB** — cukup untuk kebutuhan awal (model 8B ~4.7GB per kandidat, corpus + vector store kemungkinan hanya puluhan–ratusan MB, lihat estimasi ukuran korpus di §1), tapi mepet kalau menyimpan banyak model sekaligus untuk perbandingan POC (§11 Fase 3). Disiplin housekeeping: hapus model kandidat yang tidak terpilih setelah POC selesai, jangan biarkan menumpuk di cache Ollama.

**Ollama vs MLX** — dua pilihan serving engine yang jalan native di Apple Silicon (Metal):
- **Ollama**: paling cepat untuk mulai — CLI simpel, model library siap pakai, expose REST API kompatibel format OpenAI (memudahkan kalau nanti mau tukar provider ke Claude/Skenario 0 lewat abstraksi `LlmNarrativeProvider` yang sama, sesuai rekomendasi `Roadmap-LLM-OnPremise.md`). Backend-nya tetap llama.cpp + Metal.
- **MLX** (`mlx-lm`, framework native Apple): umumnya lebih cepat di Apple Silicon karena dioptimalkan langsung untuk unified memory, model pre-quantized banyak tersedia di `mlx-community` (Hugging Face).

**Rekomendasi**: mulai dari **Ollama** untuk kecepatan implementasi dan kemudahan ops (Fase 2 di §11) — kalau setelah POC latency-nya jadi masalah, migrasi ke MLX adalah optimisasi lanjutan, bukan prasyarat awal.

---

## 4. Desain RAG: Hybrid Metadata Filter + Semantic Search

Berbeda dari Opsi B (cukup "RAG statis" karena sumbernya satu file kecil), di sini retrieval sungguhan diperlukan — tapi **tidak perlu murni semantic search** untuk sebagian besar kasus, karena struktur data lab pasien sudah memberi kunci pencarian yang pasti:

```
1. Sistem (Server A) tahu persis parameter+arah yang abnormal dari CdssService
   (mis. "Kolesterol Total" + "di_atas_normal") — ini sudah terstruktur, bukan teks bebas.
2. Server B: filter metadata dulu → cari chunk dengan parameter=X DAN arah=Y (exact match,
   bukan similarity search) → kalau ketemu, langsung dipakai (retrieval presisi 100%,
   sesuai prinsip #1 dokumen contoh: chunk granular per parameter+arah).
3. Semantic search (embedding similarity) dipakai untuk kasus yang query-nya TIDAK
   seketat itu — mis. temuan pemeriksaan fisik/anamnesis (sheet "Ax dan fisik") yang
   sifatnya lebih naratif, atau saat butuh konteks tambahan lintas-parameter
   (mis. korelasi kolesterol+GDP+asam urat untuk narasi sindrom metabolik).
4. Kalau filter metadata TIDAK menemukan chunk (parameter/arah tidak ada rujukannya,
   seperti kasus "Kolesterol Total di bawah normal" yang sengaja tidak dibuat) →
   sistem HARUS melaporkan "belum ada rujukan untuk kondisi ini" ke response,
   BUKAN membiarkan LLM mengarang jawaban. Ini prinsip anti-halusinasi #3 dari
   dokumen contoh — diimplementasikan sebagai pengecekan eksplisit di kode,
   bukan diserahkan ke "harapan" bahwa LLM akan patuh instruksi prompt saja.
```

Pendekatan ini juga menjelaskan kenapa embedding model & vector store tidak perlu yang berat/skala besar — korpus totalnya kemungkinan hanya beberapa ratus chunk (lihat estimasi §1), dan sebagian besar retrieval-nya deterministik (lookup, bukan similarity search).

---

## 5. Stack Teknis yang Direkomendasikan

| Komponen | Rekomendasi | Alasan |
|---|---|---|
| LLM serving | **Ollama** (opsi lanjutan: MLX) | Ops paling sederhana, REST API OpenAI-compatible, native Metal |
| Model kandidat (POC) | Llama 3.1 8B, Qwen2.5 7B, + minimal satu fine-tune Bahasa Indonesia kelas 7–9B (Komodo-7B/Sahabat-AI) — **kelas 8B jadi default karena RAM Mac Mini 16GB (§3)**, Qwen2.5 14B hanya dicoba sebagai pembanding kualitas, bukan kandidat produksi | Kualitas Bahasa Indonesia medis harus diuji, bukan diasumsikan; ukuran model dibatasi realita RAM yang tersedia |
| Embedding model | **BAAI/bge-m3** (multilingual, terbukti kuat untuk Bahasa Indonesia) via `sentence-transformers` | Model embedding Ollama bawaan (nomic-embed-text, mxbai-embed-large) condong Bahasa Inggris — kurang cocok untuk istilah medis Indonesia. Ini alasan utama orkestrasi dipisah ke layer Python sendiri, bukan bergantung penuh ke API Ollama |
| Vector store | **ChromaDB** (mode embedded, persist ke disk) | Korpus kecil (ratusan chunk) → tidak butuh vector DB server terpisah (Qdrant/Milvus berlebihan, YAGNI). Chroma dukung metadata filter native — pas untuk pola hybrid di §4 |
| Orkestrasi RAG + API | **Python + FastAPI** | Ekosistem RAG (sentence-transformers, chromadb, ollama client) paling matang di Python; dipisah dari Laravel karena memang aplikasi terpisah sesuai instruksi |
| Koneksi Server A ↔ B | **Tailscale/WireGuard** + API key/token | Setara mTLS secara fungsional, jalan lintas lokasi fisik (lihat §2) |
| Kontrol versi corpus | Markdown + YAML frontmatter di git, folder terpisah (§9) | Bisa di-review lewat pull request oleh dokter/analis medis sebelum di-ingest — memenuhi prinsip "update berkala perlu review klinis" dari dokumen contoh |

> **Keputusan (2026-08-13): default produksi tetap Qwen2.5 7B.** TinyLlama (~1.1B) ditambahkan sebagai **kandidat eksperimental opsional** di Fase 3 POC (§11) — bukan pengganti default. Alasannya dicatat di sini supaya tidak diulang-tanya nanti:
>
> | | Qwen2.5 7B (default) | TinyLlama 1.1B (eksperimental) |
> |---|---|---|
> | RAM (4-bit) | ~4–5GB | ~0.6–0.7GB |
> | Perkiraan kecepatan di M4 dasar | ~15–20 tok/s | jauh lebih cepat (model kecil, baca bobot jauh lebih sedikit dari bandwidth yang sama) |
> | Taat instruksi kompleks (aturan anti-halusinasi §4, output JSON terstruktur) | Cukup andal | Berisiko tinggi — kelas ~1B umumnya kesulitan konsisten patuh instruksi rumit multi-aturan |
> | Kualitas narasi Bahasa Indonesia medis + penalaran korelasi (contoh §2.3 Opsi B) | Perlu diuji, tapi realistis | Kemungkinan besar tidak memadai — reasoning korelasi antar-parameter baru stabil di atas ~3B |
>
> Task inti fitur ini (narasi klinis yang wajib taat grounding + tidak boleh mengarang angka + output terstruktur) justru paling sensitif terhadap ukuran model kecil. TinyLlama tetap layak dicoba di POC — murah untuk diuji, dan kalau ternyata cukup untuk sub-task yang lebih sederhana, itu opsi "tier cepat" berguna di masa depan — tapi harus lolos kriteria verifikasi §13 yang sama (tidak mengarang angka, taat struktur output) sebelum dipertimbangkan serius, bukan diasumsikan cukup karena hemat resource.

---

## 6. Pipeline Ingest Corpus

```
Excel_Hasil_MCU-interpretasi_dan_tindak_lanjut.xlsx (sumber asli, dikelola manual)
        │
        ▼  (semi-otomatis: script baca Excel → draf chunk markdown,
        │   TAPI wajib direview dokter/analis sebelum commit — bukan auto-publish)
        ▼
corpus/interpretasi_lab/*.md   (satu file = satu chunk, YAML frontmatter + prosa,
corpus/diagnosis/*.md           persis pola di ragdoc §1 — file ini SUMBER KEBENARAN,
corpus/pemeriksaan_fisik/*.md   version-controlled, diff-review-able)
corpus/kategori_kesehatan/*.md
corpus/regulasi_eksternal/*.md
        │
        ▼  script ingest.py: parse frontmatter + body → embed (bge-m3) → upsert Chroma
        ▼
data/vectorstore/  (Chroma persistence, di-gitignore — hasil derive dari corpus/,
                     selalu bisa dibangun ulang dari corpus/ kalau perlu)
```

Re-ingest dijalankan tiap kali ada perubahan di `corpus/` (manual command dulu, mis. `make ingest`; job terjadwal/CI opsional belakangan — YAGNI di awal).

---

## 7. Kontrak API Server A ↔ Server B

```
POST https://<mac-mini-tailscale-host>/v1/lab-interpretation
Authorization: Bearer <token internal, disimpan di .env Server A>

Request:
{
  "case_ref": "<referensi internal, BUKAN No. RM/nama pasien>",
  "context": { "age": 34, "gender": "L", "occupation_hazard_category": "kimia" },
  "abnormal_findings": [
    { "parameter": "Kolesterol Total", "arah": "di_atas_normal", "value": 245, "unit": "mg/dL", "reference_range": "<200" }
  ]
}

Response:
{
  "case_ref": "...",
  "findings": [
    {
      "parameter": "Kolesterol Total", "arah": "di_atas_normal",
      "istilah_klinis": "Hiperkolesterolemia",
      "narasi": "...", "saran_pasien": "...", "tindak_lanjut": "...",
      "pemeriksaan_lanjutan": [...],
      "sumber": "Internal - sheet Interpretasi Lab, kolom Kolesterol Total",
      "grounded": true
    },
    {
      "parameter": "...", "arah": "...",
      "grounded": false,
      "catatan": "Belum ada rujukan internal untuk kombinasi parameter+arah ini — perlu ditinjau manual, TIDAK di-generate oleh AI"
    }
  ],
  "model_used": "llama3.1:8b", "generated_at": "..."
}
```

Prinsip privasi sama persis dengan Opsi B §9: payload **tidak pernah** berisi No. RM/nama pasien — hanya `case_ref` internal + data klinis agregat. Field `grounded: false` adalah implementasi eksplisit dari prinsip anti-halusinasi §4 — Server A **wajib** menampilkan kasus ini sebagai "perlu review manual dokter", bukan menyembunyikannya.

---

## 8. Integrasi ke `medinovav2` (Server A)

- Sesuai pola provider abstraction yang sudah direkomendasikan di `Roadmap-LLM-OnPremise.md`: tambah interface `LabInterpretationProvider` (baru, domain berbeda dari `LlmNarrativeProvider` milik Executive Insight) dengan implementasi `MacMiniRagProvider` yang memanggil API di §7.
- Hasil ditampilkan sebagai **draft** di alur review hasil lab yang sudah ada (dekat `waiting_authorization`/langkah otorisasi dokter) — bukan otomatis masuk ke rekam medis final. Ini konsisten dengan prinsip #4 dokumen contoh RAG (keputusan klinis akhir tetap manusia) dan pola existing di proyek ini (laporan MCU tetap butuh otorisasi dokter sebelum final).
- Tidak menyentuh `CdssService`/`McuRecordService` yang sudah ada — fitur ini murni lapisan tambahan di atas hasil yang sudah dihitung, sama prinsipnya dengan Opsi B §3 ("lapisan agregasi data tidak disentuh sama sekali").

---

## 9. Struktur Project Folder (repo ini)

```
medinova-rag-lab/                 (repo ini, sibling dari medinovav2)
├── corpus/
│   ├── interpretasi_lab/
│   ├── diagnosis/
│   ├── pemeriksaan_fisik/
│   ├── kategori_kesehatan/
│   └── regulasi_eksternal/
├── ingest/
│   └── ingest.py                 (parse corpus/ → embed → upsert Chroma)
├── api/
│   ├── main.py                   (FastAPI app)
│   ├── retrieval.py               (hybrid filter + semantic search, §4)
│   └── llm.py                    (client ke Ollama)
├── data/vectorstore/              (gitignored, derived dari corpus/)
├── scripts/                      (start Ollama, healthcheck, benchmark model)
├── tests/
├── .env.example
└── README.md
```

✅ **Scaffold sudah dibuat (2026-08-13)** — baru struktur folder + file skeleton/placeholder, belum ada logika ingest/retrieval/API yang berfungsi (menunggu corpus nyata dari Fase 1–2).

---

## 10. Keamanan — Adaptasi 13 Prinsip ke Konteks Mac Mini

Mengacu ke `Roadmap-LLM-OnPremise.md` §Keamanan (repo `medinovav2`), poin yang butuh penyesuaian spesifik untuk Mac Mini (bukan server rack datacenter):

- **Enkripsi at-rest**: aktifkan **FileVault** (setara disk encryption di macOS).
- **Segmentasi jaringan**: karena kemungkinan tidak satu LAN dengan Server A, pakai **Tailscale/WireGuard** (§2) — Mac Mini tidak boleh punya port yang di-forward ke internet publik sama sekali.
- **Firewall**: macOS Application Firewall + batasi hanya interface VPN yang boleh terima koneksi masuk ke port API.
- **Matikan telemetry**: Ollama punya opsi telemetry — pastikan dimatikan/diblok di level firewall, sesuai prinsip #5 di roadmap acuan.
- **Keamanan fisik**: karena Mac Mini kemungkinan besar di kantor/meja kerja (bukan data center), catat siapa yang punya akses fisik — relevan khususnya kalau nanti device dibawa-bawa atau ditaruh di area yang tidak terkunci.
- **Least privilege kredensial**: dipenuhi by design — Server B tidak pernah menyimpan kredensial MySQL milik `medinovav2` (§2, §7).
- **Kill switch/fallback**: kalau Mac Mini down/tidak reachable, alur review lab di Server A harus tetap jalan tanpa fitur AI (draft interpretasi jadi kosong/"tidak tersedia", bukan alur lab-nya ikut error).

---

## 11. Fase Roadmap

| Fase | Isi | Prasyarat | Status |
|---|---|---|---|
| 0. Prasyarat & Scoping | Konfirmasi spek Mac Mini, topologi jaringan, lokasi folder repo (§14) | — | ✅ Sebagian besar selesai (spek Mac Mini, lokasi folder); topologi jaringan masih terbuka |
| 1. Lengkapi Sumber Data | Isi ambang batas sheet "Diagnosis" (masih stub), kumpulkan teks resmi regulasi eksternal (Permenaker 5/2018, JNC 8, PERKENI) dari sumber primer | Kerja non-teknis, perlu dokter/analis medis | Belum mulai |
| 2. Corpus & Ingest Pipeline | Bangun chunk markdown untuk seluruh ~40 parameter Interpretasi Lab (pola sama seperti 5 contoh di ragdoc), tulis `ingest.py`, verifikasi retrieval manual (query per parameter+arah, cek chunk yang benar kembali, cek kasus kosong tidak dipaksa) | Fase 1 (khusus sheet Diagnosis) | Skeleton `ingest.py` sudah ada, logika belum diisi |
| 3. LLM Serving POC | Install Ollama, uji 2–3 model kandidat (§5) untuk kualitas narasi Bahasa Indonesia medis, benchmark latency di hardware Mac Mini sungguhan | Fase 0 | Belum mulai |
| 4. RAG Orchestration API | FastAPI: retrieval hybrid (§4), prompt construction (aturan anti-halusinasi eksplisit, mirip system prompt Opsi B §2.1), structured output, field `grounded`/`sumber` | Fase 2, 3 | Skeleton `api/` sudah ada, logika belum diisi |
| 5. Integrasi Server A | `LabInterpretationProvider` + `MacMiniRagProvider` di `medinovav2`, tampil sebagai draft di alur review lab | Fase 4 | Belum mulai |
| 6. Security Hardening | §10 diterapkan penuh sebelum data sungguhan (walau agregat) lewat jaringan | Sebelum go-live pilot | Belum mulai |
| 7. Verifikasi & Pilot | Bandingkan draft AI vs interpretasi dokter untuk sample data (anonim), pastikan nol angka/rujukan yang dikarang, pilot 1 dokter dulu | Fase 5, 6 | Belum mulai |
| 8. Perluasan Corpus (lanjutan) | Tambah sheet Ax&Fisik, Rumus Pemx Lanjut, Kategori K1-K5, regulasi eksternal; evaluasi apakah Executive Insight (Opsi B) ikut dipindah ke infra RAG yang sama supaya tidak ada dua mekanisme RAG terpisah | Fase 7 selesai + hasil pilot positif | Belum mulai |

---

## 12. Prasyarat yang Masih Kosong (diringkas dari §1)

1. Sheet "Diagnosis" — kolom "Hasil" kosong, ambang batas pre-diabetes/diabetes/pre-hipertensi/hipertensi/sindrom metabolik perlu diisi dulu (rujukan: kriteria PERKENI untuk diabetes, JNC 8 untuk hipertensi).
2. Teks resmi Permenaker No. 5/2018, JNC 8, PERKENI — harus diambil dari sumber primer, bukan disalin dari web.
3. ~35 parameter Interpretasi Lab lainnya (di luar 5 contoh) belum dibuatkan chunk markdown-nya.
4. Topologi jaringan Mac Mini ↔ hosting `medinovav2` — lihat §14.

---

## 13. Rencana Verifikasi (sebelum dianggap "selesai")

1. Untuk setiap parameter+arah yang punya chunk, query retrieval mengembalikan chunk yang benar (exact metadata match) — 100% presisi, karena ini deterministik.
2. Untuk parameter+arah yang **tidak** punya chunk (sengaja kosong di sumber), response API mengembalikan `grounded: false` — bukan LLM mengarang isi.
3. Cross-check ≥10 kasus histori nyata (data lab abnormal, anonim) — narasi AI dibandingkan interpretasi dokter yang sudah ada, cek tidak ada angka/rujukan yang dikarang.
4. Simulasikan Mac Mini tidak reachable dari Server A — pastikan alur review lab tetap jalan (fallback §10).
5. Uji fisik: pastikan Mac Mini tidak reachable dari internet publik (scan port dari luar jaringan VPN).

---

## 14. Keputusan yang Perlu Dikonfirmasi

1. ~~**Spesifikasi Mac Mini** (chip M-series & RAM)~~ — ✅ **Dikonfirmasi (2026-08-13): Mac Mini M4 dasar, 10-core CPU/10-core GPU, RAM 16GB, SSD 256GB (SKU MU9D3ID), sementara.**
2. **Topologi jaringan** — Mac Mini akan satu LAN dengan hosting `medinovav2`, atau lokasi fisik terpisah? Menentukan detail setup Tailscale/WireGuard di §2.
3. ~~**Nama & lokasi folder project baru**~~ — ✅ **Dibuat (2026-08-13): `D:\Learn\medinova-rag-lab`** (repo ini).
4. **Urutan pengerjaan corpus** — mulai dari sheet "Interpretasi Lab" dulu (paling siap, prioritas "Tinggi" menurut catatan ragdoc) sebelum sheet lain yang masih perlu dilengkapi (Diagnosis) atau prioritas sedang (Ax&Fisik)? Dokumen ini mengasumsikan ya.
5. **Siapa yang mengerjakan §12.1–12.2** (isi ambang batas Diagnosis, kumpulkan teks regulasi resmi)? Ini kerja klinis/non-teknis, di luar scope coding — perlu ditentukan siapa PIC-nya sebelum Fase 2 bisa lengkap untuk semua kategori (walau Fase 2 bisa mulai duluan khusus sheet Interpretasi Lab yang sudah siap).

Setelah keputusan yang tersisa dikonfirmasi, langkah berikutnya adalah mulai Fase 1 (isi sumber data) dan Fase 2 (bangun corpus + ingest pipeline untuk sheet Interpretasi Lab).
