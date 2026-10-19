# Release notes

## v1.1.0 — 2026-09-16 — Online web reading documentation and NJU GSE Lecture 4

- Added NJU GSE 2026 Lecture 4 (软件仓库管理（二）) in both PDF and verified web-article formats.
- Documented the dual-format web/PDF reader, bundled PDF.js viewer, local reading-position persistence, mobile layout, and conversion verification rules in `README.md`, `README.en.md`, and `docs/development/web-reading.md`.

## v1.0.1 — 2026-09-13 — Readable slide panels for composite lecture recordings

- Re-cropped 221 composite (camera-plus-slides) figures across NJU GSE Lectures 2–3 and CMU 11-768 Lectures 1–4 using `scripts/frame_filter.py layout` so slide text renders at full column width.
- Preserved blackboard panels alongside slides where the lecture discussion references board writing, and regenerated the corresponding PDFs and `web_source` profiles.
- Updated `scripts/web_notes.py` to support multi-image figures during HTML conversion.

## v1.0.0 — 2026-09-13 — First tagged release

- End-to-end pipeline turning YouTube, Bilibili, and X/Twitter lecture videos into reader-first Chinese LaTeX notes and compiled PDFs.
- Five-stage subtitle fallback: manual CC, automatic captions (`clean_subs.py`, `check_srt_health.py`), burned-in subtitle OCR (`ocr_hardsubs.py`), local ASR (`transcribe_x_asr.py`, `transcribe_whisper.py`), and dictionary/LLM correction (`correct_srt.py`, `llm_correct_srt.py`).
- Automatic overlay and composite-panel measurement (`frame_filter.py`), numerical-claim verification (`extract_claims.py`), three-way figure checks (`verify_figures.py`), and one-shot delivery gate (`verify_notes.py`).
- Catalog-driven course library (`build_site.py`, `site_catalog.py`, `web_notes.py`) with dual-format HTML/PDF reading and containerized community PDF contribution checks (`pdf_inspector.py`).
- Semantic versioning via `VERSION`, `scripts/release_notes.py`, and automated GitHub Releases (`.github/workflows/release.yml`).
