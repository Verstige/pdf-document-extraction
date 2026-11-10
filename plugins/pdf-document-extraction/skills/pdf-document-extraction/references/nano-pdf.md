# nano-pdf — Natural Language PDF Editing

Edit PDF text using natural language commands.

## Setup

```bash
pip install nano-pdf
```

## Commands

```bash
# Edit PDF with natural language
nano-pdf edit document.pdf --page 1 --prompt "Fix the typo 'teh' to 'the'"

# View pages
nano-pdf view document.pdf --pages 1-3

# Extract text
nano-pdf extract document.pdf --pages all
```