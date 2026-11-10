---
name: pdf-document-extraction
description: "Document text extraction and editing: text-based PDFs via pymupdf, scanned/image-based PDFs via qlmanage+vision (macOS), marker-pdf (GPU-only, not on every machine), nano-pdf for natural-language edits, python-docx for Word, python-pptx for PowerPoint."
version: 1.0.0
license: MIT
author: "the maintainers"
---
# Document Processing — PDFs, Word, PowerPoint

Extract text from and edit documents: PDFs (text-based and scanned), Word documents, and PowerPoint presentations.

---

## ⚠️ macOS PDF Extraction — iCloud Sync Lock Workaround

**On the maintainer's Mac:** PDFs in `~/Library/Mobile Documents/` (iCloud-synced) can be locked by the sync daemon. `pypdf`, `pymupdf`, `textutil`, and `cupsfilter` all fail with "Resource deadlock avoided" or empty output.

**Use `qlmanage` + vision_analyze instead.** Full workflow in `references/ocr-and-documents.md`.

---

## PDFs — Text Extraction

### pypdf (Primary — text-based PDFs, no install required)

**Preferred on the maintainer's Mac** — `pypdf` is a built-in stdlib-adjacent package that works without separate installation. Always available via `python3 -c "import pypdf"`.

```python
import pypdf

reader = pypdf.PdfReader('/path/to/document.pdf')
print(f"Pages: {len(reader.pages)}")
text = ''
for page in reader.pages:
    text += (page.extract_text() or '') + '\n'
print(text)
```

**For keyword search** across all pages:
```python
import pypdf
reader = pypdf.PdfReader('/path/to.pdf')
keyword = 'EARLY TERMINATION'
for i, page in enumerate(reader.pages):
    t = page.extract_text() or ''
    if keyword.upper() in t.upper():
        print(f"Page {i+1}: found '{keyword}'")
        print(t[:500])
```

### pymupdf (Lightweight — text-based PDFs only; NOT for scanned documents)

```bash
pip install pymupdf pymupdf4llg

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

### marker-pdf (High-Quality OCR — GPU required, NOT available on the maintainer's MacBook)

```bash
pip install marker-pdf

# Standard
python marker-pdf document.pdf

# Scanned PDF (OCR)
python marker-pdf scanned.pdf
```

**Requires:** NVIDIA GPU (RTX 4090/A100 class) with 12GB+ VRAM. On the maintainer's MacBook this will fail — do NOT attempt. Use `qlmanage` + `vision_analyze` instead (see above).

### Feature Comparison

| Feature | pymupdf | qlmanage+vision |
|---------|---------|-----------------|
| Text-based PDF | ✅ | ✅ |
| Scanned PDF (OCR) | ❌ | ✅ |
| iCloud-locked PDFs | ❌ | ✅ |
| Tables | Basic | ✅ (via vision) |
| Equations/LaTeX | ❌ | ✅ (via vision) |
| Install size | ~25MB | Built-in macOS |

**Decision:** Try `pymupdf` first for text-based PDFs. For anything else on macOS — especially iCloud-synced files — use `qlmanage` + `vision_analyze`. For the maintainer's Mac, marker-pdf is NOT a viable option.

---

## PDFs — Edit Text

### nano-pdf (Natural Language Edits)

```bash
pip install nano-pdf

# Edit PDF with natural language
nano-pdf edit document.pdf --page 1 --prompt "Fix the typo 'teh' to 'the'"

# View pages
nano-pdf view document.pdf --pages 1-3

# Extract text
nano-pdf extract document.pdf --pages all
```

---

## Word Documents — python-docx

For structured content where term/title/question are in separate runs of the same paragraph (flashcards, vocab lists, quiz Q&A), `para.text` flattens the structure and regex on the flat string produces wrong splits. Inspect `para.runs` directly and split on the run boundary. Full recipe in `references/docx-run-level-extraction.md`.

```bash
pip install python-docx

python3 << 'EOF'
from docx import Document

doc = Document('document.docx')
for para in doc.paragraphs:
    print(para.text)

# Access tables
for table in doc.tables:
    for row in table.rows:
        print([cell.text for cell in row.cells])
EOF
```

---

## PowerPoint — python-pptx

```bash
pip install python-pptx

python3 << 'EOF'
from pptx import Presentation

prs = Presentation('presentation.pptx')
for i, slide in enumerate(prs.slides):
    print(f"=== Slide {i+1} ===")
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(shape.text)
        if shape.has_table:
            for row in shape.table.rows:
                print([cell.text for cell in row.cells])
EOF
```

---

## Split, Merge, Search PDFs

```python
# Split: extract pages 1-5
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")

# Merge
result = pymupdf.open()
for path in ["a.pdf", "b.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")

# Search across pages
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
```

---

## Related Skills

- **`ocr-and-documents`** — Full pymupdf/marker-pdf reference with scripts
- **`nano-pdf`** — Natural language PDF editing