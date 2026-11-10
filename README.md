# PDF & Document Extraction: Text, Scans, and Edits

> Get text out of real documents. Text PDFs, scanned pages, images and Office files, plus natural-language edits that preserve the original layout.

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg) ![Claude Code](https://img.shields.io/badge/Claude_Code-skill-blueviolet.svg) [![Available on Agensi](https://img.shields.io/badge/Agensi-%245-ff5a5f.svg)](https://agensi.io/skills/pdf-document-extraction-text-scans-and-edits)

## What it does

Document text extraction and editing: text-based PDFs via pymupdf, scanned/image-based PDFs via qlmanage+vision (macOS), marker-pdf (GPU-only, not on every machine), nano-pdf for natural-language edits, python-docx for Word, python-pptx for PowerPoint.

Extract text from and edit documents: PDFs (text-based and scanned), Word documents, and PowerPoint presentations.

## The failure it prevents

Working this by hand means rediscovering the same edge cases every time. They are written down here instead, with the fix for each one.

## When to use it

- extract text from a PDF or a scanned page
- edit a document with natural-language instructions
- convert Office files into usable text

## What's inside

```
plugins/
└── pdf-document-extraction/
    ├── .claude-plugin/plugin.json
    └── skills/pdf-document-extraction/
        ├── SKILL.md
        ├── references/            (3 files)
        │   └── docx-run-level-extraction.md
        │   └── nano-pdf.md
        │   └── ocr-and-documents.md
        ├── scripts/                (1 files)
        │   └── docx-to-sql-education.py
```

## Install

Add this repo as a Claude Code marketplace, then install the skill:

```bash
claude plugin marketplace add Verstige/pdf-document-extraction
claude plugin install pdf-document-extraction@pdf-document-extraction
```

Or copy the skill straight into your skills directory:

```bash
git clone https://github.com/Verstige/pdf-document-extraction.git
cp -R pdf-document-extraction/plugins/pdf-document-extraction/skills/pdf-document-extraction ~/.claude/skills/
```

## Usage

The skill activates on the work it describes. Ask for the outcome, and it
supplies the method:

```
> "extract text from a PDF or a scanned page"
```

## Reference material

Loaded on demand — the skill only reads what the task needs.

| File | Covers |
| --- | --- |
| `docx-run-level-extraction.md` | Docx Run-Level Extraction — When `para.text` Lies |
| `nano-pdf.md` | nano-pdf — Natural Language PDF Editing |
| `ocr-and-documents.md` | ocr-and-documents — PDF Text Extraction |

## License

MIT. See [LICENSE](LICENSE).

---

**Also available as a paid skill on Agensi** — $5. Install it with one command, no clone required:

[agensi.io/skills/pdf-document-extraction-text-scans-and-edits](https://agensi.io/skills/pdf-document-extraction-text-scans-and-edits)

Part of the [Verstige](https://github.com/Verstige) skills portfolio. More at [github.com/Verstige](https://github.com/Verstige).
