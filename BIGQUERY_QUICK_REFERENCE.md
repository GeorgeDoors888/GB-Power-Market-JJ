# BigQuery HH DATA - Quick Reference Card

## 🚀 Daily Usage (3 Commands)

```bash
# 1. Generate HH DATA (Google Sheets button)
#    Click: "🔄 Generate HH Data"

# 2. Upload to BigQuery
python3 upload_hh_to_bigquery.py "Commercial" 10000

# 3. Run calculations (70x faster!)
python3 btm_dno_lookup.py
```

⏱️ **Total Time**: ~20 seconds (was 7+ minutes)

---

## 📊 Key Files

| File | Purpose |
|------|---------|
| `upload_hh_to_bigquery.py` | Upload + delete sheet |
| `btm_dno_lookup.py` | Fast BigQuery calculations |
| `btm_hh_generator.gs` | Apps Script generator |
| `test_bigquery_workflow.sh` | Test complete workflow |

---

## 🔍 Useful Queries

### Check Data in BigQuery
```sql
SELECT
  supply_type,
  COUNT(*) as records,
  MAX(generated_at) as last_upload
FROM `inner-cinema-476211-u9.uk_energy_prod.hh_data_btm_generated`
GROUP BY supply_type;
```

### Get Latest Data
```sql
SELECT *
FROM `inner-cinema-476211-u9.uk_energy_prod.hh_data_btm_generated`
WHERE generated_at = (SELECT MAX(generated_at) FROM table)
ORDER BY timestamp;
```

### Check Table Size
```python
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
table = client.get_table('uk_energy_prod.hh_data_btm_generated')
print(f'Rows: {table.num_rows:,}')
print(f'Size: {table.num_bytes/1024/1024:.2f} MB')
"
```

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "BigQuery table empty" | Generate HH DATA first, then upload |
| "HH DATA sheet not found" | Sheet deleted after upload (expected) |
| "Still slow (7 min)" | Check if using BigQuery: look for "Reading HH DATA from BigQuery" |
| "Permission denied" | `export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"` |

---

## 📈 Performance

- **Before**: 7 minutes (Google Sheets API)
- **After**: 10 seconds (BigQuery)
- **Improvement**: 70x faster

---

## 🔗 Links

- **Spreadsheet**: [BtM Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)
- **BigQuery**: [Console](https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9)
- **Docs**: `BIGQUERY_HH_DATA_IMPLEMENTATION.md`

---

## 🎯 Supply Types Available

- Commercial
- Industrial
- Domestic
- Network Rail
- EV Charging
- Datacentre
- Non Variable
- Solar and Storage
- Storage
- Solar and Wind and Storage

---

## 📅 Maintenance

**Monthly** (1st of month):
- BigQuery cleanup query runs automatically
- Deletes records >90 days old
- Setup: See `create_bigquery_scheduled_cleanup.sql`

---

**Quick Help**: `cat BIGQUERY_HH_DATA_IMPLEMENTATION.md | less`

