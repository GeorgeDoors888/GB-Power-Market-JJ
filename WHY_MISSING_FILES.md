# 🔍 Why Only 153,212 Files Indexed (Out of 200,000+)

**Date:** November 3, 2025  
**Investigation:** File Filter Analysis

---

## The Issue: MIME Type Filter

Your current `DRIVE_CRAWL_Q` filter is **very restrictive** and only indexes these file types:

### ✅ Currently Indexed File Types:
1. `application/pdf` - PDFs ✅
2. `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - Word (.docx) ✅
3. `application/vnd.openxmlformats-officedocument.presentationml.presentation` - PowerPoint (.pptx) ✅
4. `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` - Excel (.xlsx) ✅
5. `application/vnd.google-apps.document` - Google Docs ✅
6. `application/vnd.google-apps.spreadsheet` - Google Sheets ✅
7. `application/vnd.google-apps.presentation` - Google Slides ✅

### ❌ File Types EXCLUDED (Missing ~50,000+ files):

From the scan of first 50,000 files, I found these are **NOT being indexed**:

1. **9,109 text files** (`text/plain`) - `.txt`, `.log`, `.md`, etc.
2. **8,823 HTML files** (`text/html`) - `.html`, `.htm`
3. **3,264 binary files** (`application/octet-stream`) - Various formats
4. **2,593 Python files** (`text/x-python`) - `.py` files
5. **1,452 Python bytecode** (`application/x-python-code`) - `.pyc`
6. **1,386 C header files** (`text/x-chdr`) - `.h` files
7. **807 CSV files** (`text/csv`) - Spreadsheet data
8. **595 Word macro files** (`application/vnd.ms-word.document.macroenabled.12`) - `.docm`
9. **554 PNG images** (`image/png`)
10. **264 old Excel files** (`application/vnd.ms-excel`) - `.xls` (old format)
11. **242 XML files** (`text/xml` or `application/xml`)
12. **198 Java files** (`text/x-java`)
13. **174 ZIP archives** (`application/zip`)
14. **142 OpenDocument files** (`application/vnd.oasis.opendocument.text`) - `.odt`
15. **126 JSON files** (`application/json`)

And many more...

---

## Current Stats (First 50,000 Files Scanned):

- **Total files found:** 50,000+ (scan still running)
- **Files matching filter:** ~17,321 PDFs + ~1,364 Excel + ~443 Sheets + ~295 Word = **~20,000**
- **Files excluded:** ~30,000+ (60% of files!)

---

## Solutions

### Option 1: Index ALL File Types (Recommended for Complete Coverage)

Remove the MIME type filter completely to index everything:

**Update .env:**
```bash
# Old (restrictive):
DRIVE_CRAWL_Q=(mimeType='application/pdf' or ...) and trashed=false

# New (index everything):
DRIVE_CRAWL_Q=trashed=false
```

**Pros:**
- ✅ Index ALL 200,000+ files
- ✅ No files missed
- ✅ Complete Drive coverage

**Cons:**
- ⚠️ Will index images, code, binaries (may not need text extraction for all)
- ⚠️ Larger BigQuery table
- ⚠️ Longer indexing time

---

### Option 2: Expand Filter (Add Important Types)

Keep the filter but add commonly useful file types:

**Update .env:**
```bash
DRIVE_CRAWL_Q=(
  mimeType='application/pdf' or 
  mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or 
  mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or 
  mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation' or 
  mimeType='application/vnd.google-apps.document' or 
  mimeType='application/vnd.google-apps.spreadsheet' or 
  mimeType='application/vnd.google-apps.presentation' or
  mimeType='text/plain' or                    # Text files
  mimeType='text/html' or                     # HTML files
  mimeType='text/csv' or                      # CSV files
  mimeType='application/vnd.ms-excel' or      # Old Excel (.xls)
  mimeType='application/vnd.ms-word.document.macroenabled.12' or  # Word macro files
  mimeType='text/markdown' or                 # Markdown files
  mimeType='application/json' or              # JSON files
  mimeType='application/xml' or               # XML files
  mimeType='text/xml'                         # XML text
) and trashed=false
```

**Pros:**
- ✅ Adds ~15,000-20,000 more useful files
- ✅ Still excludes images, binaries, code
- ✅ Focused on document types

**Cons:**
- ⚠️ Still misses some files
- ⚠️ More complex filter

---

### Option 3: Keep Current Filter (Document-Only)

Keep indexing only Office/PDF/Google files:

**Current state:**
- 153,212 documents indexed
- Focused on primary business documents
- Excludes code, images, data files

**Best for:**
- Document management systems
- When you only care about readable documents
- Minimizing noise from code/data files

---

## Recommendation

Based on your goal of indexing "the entire Google Drive," I recommend:

### **Option 1: Index Everything**

This will capture all 200,000+ files including:
- All PDFs and Office docs (already indexed)
- Text files, code files, data files
- Everything else in your Drive

**How to implement:**

1. **Update the filter:**
   ```bash
   # Edit .env
   DRIVE_CRAWL_Q=trashed=false
   ```

2. **Clear existing data** (optional - to avoid duplicates):
   ```bash
   # Truncate table
   ssh root@94.237.55.15 'docker exec driveindexer python3 -c "
   from dotenv import load_dotenv; load_dotenv(\"/app/.env\")
   import sys; sys.path.insert(0, \"/app\")
   from src.auth.google_auth import bq_client
   bq = bq_client()
   bq.query(\"DELETE FROM \\\`inner-cinema-476211-u9.uk_energy_insights.documents\\\` WHERE TRUE\").result()
   print(\"Table cleared\")
   "'
   ```

3. **Re-run indexing:**
   ```bash
   ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli index-drive'
   ```

This should index all 200,000+ files!

---

## What Do You Want?

Let me know which option you prefer:

1. **Index EVERYTHING** (all 200,000+ files) → I'll update the filter
2. **Expand to include text/CSV/JSON** (add ~20,000 more files) → I'll add those types
3. **Keep current** (documents only) → You already have 153,212 docs

**Which would you like?** 🤔
