# 📄 API Documentation Export Guide

## Overview

This guide explains how to export the `drive-bq-indexer/API.md` documentation to various formats for external sharing.

## Quick Export (PDF)

### Option 1: Using the Script (Recommended)

```bash
./export_api_pdf.sh
```

**Requirements:**
- macOS: `brew install pandoc wkhtmltopdf`
- Linux: `apt-get install pandoc wkhtmltopdf`

**Output:** `API_OVERVIEW.pdf` (read-only, shareable)

---

### Option 2: Manual Pandoc

```bash
pandoc drive-bq-indexer/API.md \
    -o API_OVERVIEW.pdf \
    --metadata title="Energy Jibber Jabber API Overview" \
    --toc \
    -V geometry:margin=1in
```

---

### Option 3: GitHub Online (No Installation)

1. Open: https://github.com/GeorgeDoors888/overarch-jibber-jabber/blob/main/drive-bq-indexer/API.md
2. Click **Print** in browser (Cmd+P / Ctrl+P)
3. Save as PDF

---

## Export to Other Formats

### HTML (Standalone)

```bash
pandoc drive-bq-indexer/API.md \
    -o API_OVERVIEW.html \
    --standalone \
    --toc \
    --css=style.css \
    --metadata title="Energy Jibber Jabber API"
```

### Word Document (DOCX)

```bash
pandoc drive-bq-indexer/API.md \
    -o API_OVERVIEW.docx \
    --toc \
    --metadata title="Energy Jibber Jabber API"
```

### Plain Text

```bash
pandoc drive-bq-indexer/API.md \
    -o API_OVERVIEW.txt \
    --wrap=auto
```

---

## Sharing Methods

### 1. Email Attachment

```bash
# Create PDF
./export_api_pdf.sh

# Attach API_OVERVIEW.pdf to email
```

**Pros:** Direct, no account needed  
**Cons:** File gets outdated

---

### 2. Google Drive (Recommended)

```bash
# Create PDF
./export_api_pdf.sh

# Upload to shared folder
# Set link sharing: "Anyone with the link can view"
```

**Pros:** Always accessible, can update  
**Cons:** Requires Google account

---

### 3. GitHub Public Link (Best for Developers)

Share this link (always up-to-date):
```
https://github.com/GeorgeDoors888/overarch-jibber-jabber/blob/main/drive-bq-indexer/API.md
```

**Pros:** Always latest version, no export needed  
**Cons:** Requires GitHub account

---

### 4. Static Website Hosting

```bash
# Convert to HTML
pandoc drive-bq-indexer/API.md \
    -o index.html \
    --standalone \
    --toc

# Host on:
# - GitHub Pages
# - Netlify
# - Vercel
# - S3 + CloudFront
```

**Pros:** Public URL, professional  
**Cons:** Requires hosting setup

---

## Automation Options

### Auto-Generate on Commit

Add to `.github/workflows/docs.yml`:

```yaml
name: Generate API Docs
on:
  push:
    paths:
      - 'drive-bq-indexer/API.md'
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install pandoc
        run: sudo apt-get install pandoc wkhtmltopdf
      - name: Generate PDF
        run: ./export_api_pdf.sh
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: API_OVERVIEW
          path: API_OVERVIEW.pdf
```

---

## Best Practices

### For Internal Team

✅ **Share GitHub link** (always up-to-date)
```
https://github.com/GeorgeDoors888/overarch-jibber-jabber/blob/main/drive-bq-indexer/API.md
```

### For External Partners

✅ **Generate PDF** with date stamp
```bash
pandoc drive-bq-indexer/API.md \
    -o "API_OVERVIEW_$(date +%Y-%m-%d).pdf" \
    --metadata title="Energy Jibber Jabber API" \
    --metadata date="$(date +%Y-%m-%d)"
```

### For Customers/Stakeholders

✅ **Host on static site** or Google Drive
- Professional appearance
- Easy to find
- Can track views

---

## Troubleshooting

### "pandoc: command not found"

**macOS:**
```bash
brew install pandoc
```

**Linux:**
```bash
sudo apt-get install pandoc
```

### "wkhtmltopdf: command not found"

**macOS:**
```bash
brew install wkhtmltopdf
```

**Linux:**
```bash
sudo apt-get install wkhtmltopdf
```

### PDF looks broken

Try LaTeX engine instead:
```bash
pandoc drive-bq-indexer/API.md -o API_OVERVIEW.pdf
# (wkhtmltopdf not needed)
```

Or use GitHub's print feature (Option 3 above)

---

## File Locations

- **Source:** `drive-bq-indexer/API.md`
- **Export Script:** `export_api_pdf.sh`
- **Output:** `API_OVERVIEW.pdf` (gitignored)
- **GitHub URL:** https://github.com/GeorgeDoors888/overarch-jibber-jabber/blob/main/drive-bq-indexer/API.md

---

**Last Updated:** November 5, 2025  
**Maintainer:** GB Power Market Team
