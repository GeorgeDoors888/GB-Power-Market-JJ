# ChatGPT PDF Access Guide

*Last Updated: November 17, 2025*

## ✅ What Changed

Updated `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` to include PDF document search capability.

## 📊 PDF Documents in BigQuery

**Table**: `inner-cinema-476211-u9.uk_energy_prod.document_chunks`  
**Total**: 8 PDFs, 3,880 searchable chunks

### Available PDFs:

**✅ Complete (all chunks present):**
1. **consumer_engagement_survey_2016_-_data_tables_0.pdf** - 1,096 chunks (11.66 MB)
2. **DCUSA v16.1_.pdf** - 578 chunks (6.16 MB) - Distribution Connection & Use of System Agreement
3. **Coforge_s_BP2_midscheme_review_of_ESO_Digital_Data_and_Technology_performance.pdf** - 218 chunks (10.41 MB)
4. **FSO_Modification_NETA IDD Part 1_v53.2.pdf** - 210 chunks (3.79 MB)

**⚠️ Partial (incomplete uploads):**
5. **00_The_Full_Grid_Code 2.pdf** - 692/934 chunks (74%, 13.65 MB)
6. **Complete CUSC - 02 October 2024_0.pdf** - 618/847 chunks (73%, 15.23 MB)
7. **CU3E6E~1_0.PDF** - 459/846 chunks (54%, 15.29 MB)
8. **Enforcement Guidelines v11 March 2023.pdf** - 9/65 chunks (14%, 0.79 MB)

---

## 🔍 How ChatGPT Finds PDFs Now

### Before (❌ Didn't Work):
```sql
-- Wrong table, wrong columns
SELECT filename FROM documentation_url_registry WHERE ...
```

### After (✅ Works):
```sql
-- Correct table with JSON metadata parsing
SELECT 
  JSON_VALUE(metadata, '$.filename') as filename,
  COUNT(*) as chunks
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE JSON_VALUE(metadata, '$.mime_type') = 'application/pdf'
GROUP BY filename
```

---

## 📝 Updated ChatGPT Instructions

### New Sections Added:

1. **Two Documentation Systems** - Clarifies GitHub files vs PDF chunks
2. **PDF Document Discovery** - Query to list all PDFs
3. **PDF Content Search** - Full-text search within PDFs
4. **Pattern 5: PDF Content Search** - Workflow for searching documents
5. **Available PDF Documents** - List of 8 PDFs with status

### Key Queries ChatGPT Can Now Use:

#### List All PDFs
```sql
SELECT 
  JSON_VALUE(metadata, '$.filename') as filename,
  COUNT(*) as chunks,
  JSON_VALUE(metadata, '$.file_size') as file_size,
  JSON_VALUE(metadata, '$.drive_url') as url
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE JSON_VALUE(metadata, '$.mime_type') = 'application/pdf'
GROUP BY filename, file_size, url
ORDER BY CAST(JSON_VALUE(metadata, '$.file_size') AS INT64) DESC
```

#### Search PDF Content
```sql
SELECT 
  JSON_VALUE(metadata, '$.filename') as filename,
  chunk_index,
  LEFT(content, 200) as preview
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE JSON_VALUE(metadata, '$.mime_type') = 'application/pdf'
  AND LOWER(content) LIKE '%search term%'
LIMIT 10
```

#### Get Specific PDF Chunks
```sql
SELECT 
  chunk_index,
  content
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE JSON_VALUE(metadata, '$.filename') = 'DCUSA v16.1_.pdf'
ORDER BY chunk_index
LIMIT 50
```

---

## 🧪 Testing

### Test via Railway Endpoint
```bash
./test_chatgpt_pdf_search.sh
```

This tests:
1. List all PDFs (should return 8 files)
2. Search for "grid code" (should find matches in Grid Code PDF)

### Test ChatGPT Understanding

Ask ChatGPT:
- "List all available PDF documents"
- "Search for 'frequency response' in the Grid Code PDF"
- "Show me excerpts from the CUSC document about balancing"
- "What PDFs do we have about distribution connections?"

---

## 🎯 What ChatGPT Can Do Now

### PDF Discovery
✅ List all 8 PDF documents with chunk counts  
✅ Show file sizes and Drive URLs  
✅ Identify which PDFs are complete vs partial

### Content Search
✅ Full-text search across all 3,880 chunks  
✅ Find specific terms (e.g., "grid code", "frequency", "balancing")  
✅ Return excerpts with context (200 chars preview)  
✅ Show chunk numbers for reference

### Document Reading
✅ Read specific chunks by index  
✅ Read sequential chunks to get full context  
✅ Extract information from regulatory documents  
✅ Compare information across multiple PDFs

---

## 🔄 Next Steps

### To Deploy to ChatGPT:
1. Copy updated `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`
2. Paste into ChatGPT Custom GPT instructions
3. Save and test with PDF queries

### To Test:
```bash
# Run automated test
./test_chatgpt_pdf_search.sh

# Manual Railway test
curl -X POST "https://jibber-jabber-production.up.railway.app/query_bigquery" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT JSON_VALUE(metadata, '\''$.filename'\'') as filename, COUNT(*) as chunks FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks` WHERE JSON_VALUE(metadata, '\''$.mime_type'\'') = '\''application/pdf'\'' GROUP BY filename"}'
```

---

## 📚 Related Files

- `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` - Updated instructions (✅ Done)
- `test_chatgpt_pdf_search.sh` - Automated testing script (✅ Created)
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Railway backend documentation
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data architecture reference

---

## 🐛 Troubleshooting

### ChatGPT can't find PDFs
- Verify using `document_chunks` table, not `documentation_url_registry`
- Verify JSON_VALUE syntax for metadata parsing
- Check Railway endpoint is accessible

### Search returns no results
- Verify search term exists in content
- Use `LOWER()` for case-insensitive search
- Try broader search terms first

### Partial PDFs missing chunks
- Some PDFs were incompletely uploaded to BigQuery
- Use chunk count to verify completeness
- Grid Code (74%), CUSC (73%), others vary

---

**Status**: ✅ **READY TO DEPLOY**  
**Updated File**: `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`  
**Test Script**: `test_chatgpt_pdf_search.sh`  
**Next Action**: Update ChatGPT Custom GPT with new instructions
