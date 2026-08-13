# Pola Chunk Corpus

Satu file markdown = satu chunk = satu parameter + satu arah (lihat `ROADMAP.md` §1 dan §4 di root repo). Jangan gabung dua arah (rendah/tinggi) dalam satu file, dan jangan buat isi untuk kombinasi yang tidak ada rujukannya di sumber asli (prinsip anti-halusinasi).

Format tiap file:

```markdown
---
id: lab_kolesterol_total_tinggi
kategori: interpretasi_lab
parameter: Kolesterol Total
arah: di_atas_normal
istilah_klinis: Hiperkolesterolemia
sumber: Internal - sheet Interpretasi Lab, kolom Kolesterol Total
relevansi_k3: null
---

**Makna klinis:** ...

**Saran untuk pasien:** ...

**Tindak lanjut:** ...

**Pemeriksaan lanjutan yang mungkin diperlukan:** ...

**Paket pemeriksaan terkait:** ...
```

Lihat `interpretasi_lab/_TEMPLATE.md` untuk template siap-isi, dan `medinovav2/ragdoc/contoh_rag_interpretasi_lab.md.pdf` untuk 5 contoh lengkap yang jadi acuan pola ini.

## Subfolder

| Folder | Isi | Prioritas (lihat ROADMAP.md §11 Fase 1–2, §12) |
|---|---|---|
| `interpretasi_lab/` | ~40 parameter lab × arah (rendah/tinggi) | Tinggi — mulai dari sini |
| `diagnosis/` | Kriteria pre-diabetes/diabetes, pre-hipertensi/hipertensi, sindrom metabolik | Tinggi, tapi **sumbernya masih stub** — perlu diisi ambang batas dulu (rujukan PERKENI/JNC 8) sebelum dibuat chunk |
| `pemeriksaan_fisik/` | Logika interpretasi Ax & Fisik + Rumus Pemx Fisik Lanjut | Sedang |
| `kategori_kesehatan/` | Kriteria & template rekomendasi K1–K5 | Tinggi |
| `regulasi_eksternal/` | Permenaker 5/2018, JNC 8, PERKENI — **ambil dari sumber resmi, jangan salin mentah dari web** (isu lisensi) | Menengah, prasyarat sebagian isi `diagnosis/` |
