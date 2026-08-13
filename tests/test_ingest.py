"""Test parse_chunk terhadap file corpus nyata.

Butuh dependencies penuh terinstall (`pip install -r requirements.txt`) karena
ingest.ingest mengimpor chromadb & sentence-transformers di level modul -
lihat ROADMAP.md §11 (Fase 2). Jalankan: `pytest tests/`.
"""

from ingest.ingest import CORPUS_DIR, load_chunk_files, parse_chunk


def test_load_chunk_files_skips_template_and_readme():
    files = load_chunk_files()
    names = {f.name for f in files}
    assert "_TEMPLATE.md" not in names
    assert "README.md" not in names
    assert len(files) >= 6  # 6 chunk seed dari ragdoc, lihat corpus/interpretasi_lab/


def test_parse_chunk_valid_file():
    path = CORPUS_DIR / "interpretasi_lab" / "lab_kolesterol_total_tinggi.md"
    chunk = parse_chunk(path)
    assert chunk is not None
    assert chunk.id == "lab_kolesterol_total_tinggi"
    assert chunk.metadata["parameter"] == "Kolesterol Total"
    assert chunk.metadata["arah"] == "di_atas_normal"
    assert chunk.metadata["istilah_klinis"] == "Hiperkolesterolemia"
    assert "Hiperkolesterolemia" in chunk.body or "kolesterol" in chunk.body.lower()


def test_parse_chunk_all_seed_files_have_required_fields():
    required = {"id", "kategori", "parameter", "arah", "istilah_klinis", "sumber"}
    for path in load_chunk_files():
        chunk = parse_chunk(path)
        assert chunk is not None, f"{path} gagal parse - cek field wajib"
        assert required.issubset(chunk.metadata.keys())


def test_no_chunk_exists_for_kolesterol_total_rendah():
    """Sengaja tidak ada chunk untuk kombinasi ini (data kosong di sumber asli,
    lihat corpus/interpretasi_lab/lab_kolesterol_total_tinggi.md) - retrieval
    untuk kombinasi ini harus grounded=False, bukan mengarang jawaban."""
    ids = {parse_chunk(p).id for p in load_chunk_files()}
    assert "lab_kolesterol_total_rendah" not in ids
