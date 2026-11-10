# ocr-and-documents — PDF Text Extraction

Extract text from PDFs using pymupdf and marker-pdf.

## macOS PDF Text Extraction — Bypassing iCloud Sync Locks

On the maintainer's Mac, PDFs in `~/Library/Mobile Documents/` (iCloud-synced) can be locked by the sync daemon. Standard tools (`pypdf`, `pymupdf`, `textutil`, `cupsfilter`) fail with "Resource deadlock avoided" or empty output.

**The working approach — two steps:**

**Step 1: Render PDF pages to images with `qlmanage`**
```bash
mkdir -p /tmp/pdf_render
qlmanage -t -s 2000 -o /tmp/pdf_render "/path/to/locked.pdf"
# Output: /tmp/pdf_render/filename.pdf.png (one per page if multi-page)
```

**Step 2: Read with vision_analyze**
```python
# Analyze each page with vision
vision_analyze(image_url="/tmp/pdf_render/page1.png", question="Extract all text from this document")
```

**Why this works:** `qlmanage` uses macOS's native Quick Look engine, which accesses PDFs at the filesystem level bypassing the iCloud sync daemon's file locks. Works for scanned/image-based PDFs that `pypdf` and `pymupdf` cannot read.

**Fallback — `qlmanage` full preview:**
```bash
qlmanage -p "/path/to/locked.pdf" 2>&1 | head -5
```
Can time out on large files — if so, use thumbnail mode above.

## pymupdf (Lightweight — text-based PDFs only)

```bash
pip install pymupdf pymupdf4llm

# Plain text
python pymupdf document.pdf

# Markdown
python pymupdf document.pdf --markdown

# Tables
python pymupdf document.pdf --tables

# Images
python pymupdf document.pdf --images out/

# Specific pages
python pymupdf document.pdf --pages 0-4
```

**Limitation:** pymupdf and pypdf can only extract text from text-based PDFs. Scanned/image-based PDFs return empty. For those, use the `qlmanage` + vision_analyze workflow above.

## marker-pdf (GPU required — NOT available on the maintainer's MacBook)

```bash
pip install marker-pdf

# Standard
python marker-pdf document.pdf

# Scanned PDF (OCR)
python marker-pdf scanned.pdf
```

**Requires:** NVIDIA GPU (RTX 4090/A100 class) with 12GB+ VRAM. On the maintainer's MacBook (no GPU), this will fail. Do NOT attempt to install — use the `qlmanage` + vision_analyze workflow instead.

## Feature Comparison

| Feature | pymupdf | qlmanage+vision |
|---------|---------|-----------------|
| Text-based PDF | ✅ | ✅ |
| Scanned PDF (OCR) | ❌ | ✅ |
| iCloud-locked PDFs | ❌ | ✅ |
| Tables | Basic | Via vision |
| Equations/LaTeX | ❌ | Via vision |
| Install size | ~25MB | Built-in macOS |
