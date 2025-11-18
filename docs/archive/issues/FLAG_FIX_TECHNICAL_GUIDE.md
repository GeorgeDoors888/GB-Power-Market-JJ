# Interconnector Flags - Technical Guide

## ❌ Problem: Flags Keep Breaking

**Symptoms:**
- Flags appear as single character: `🇫` instead of `🇫🇷`
- Flags show duplicate/broken: `🇫 🇫` instead of `🇫🇷`
- Flags disappear completely after updates

**Root Causes:**

### 1. **Google Sheets API Input Mode**
```python
# ❌ WRONG - Corrupts multi-byte emoji
sheets.values().update(
    valueInputOption='USER_ENTERED',  # Interprets and corrupts emojis
    body={'values': data}
)

# ✅ CORRECT - Preserves exact emoji bytes
sheets.values().update(
    valueInputOption='RAW',  # Writes exact bytes, no interpretation
    body={'values': data}
)
```

### 2. **Country Flag Emoji Structure**
Country flags are **2-character Unicode sequences**:
- 🇫🇷 = U+1F1EB (🇫) + U+1F1F7 (🇷) = France
- 🇮🇪 = U+1F1EE (🇮) + U+1F1EA (🇪) = Ireland
- 🇳🇱 = U+1F1F3 (🇳) + U+1F1F1 (🇱) = Netherlands

When Google Sheets uses `USER_ENTERED` mode, it may:
- Split the 2-character sequence
- Drop the second character
- Duplicate characters incorrectly

### 3. **External Data Sources**
If interconnector data comes from tables that already have broken flags, they propagate unless cleaned.

---

## ✅ Solution: Permanent Fix

### **Quick Fix Script**
```bash
python3 fix_interconnector_flags_permanent.py
```

This script:
1. Reads current interconnector data (Dashboard D8:E17)
2. Strips ALL existing emoji characters (including broken ones)
3. Adds complete 2-character country flags using mapping
4. Writes with `valueInputOption='RAW'` mode

**Time to run**: ~2 seconds

---

## 🔧 Implementation Guide

### **Flag Mapping (Copy-Paste Ready)**
```python
FLAG_MAP = {
    'ElecLink': '🇫🇷',     # France
    'IFA': '🇫🇷',          # France  
    'IFA2': '🇫🇷',         # France
    'East-West': '🇮🇪',    # Ireland
    'Greenlink': '🇮🇪',    # Ireland
    'Moyle': '🇮🇪',        # Northern Ireland (uses Ireland flag)
    'BritNed': '🇳🇱',      # Netherlands
    'Nemo': '🇧🇪',         # Belgium
    'NSL': '🇳🇴',          # Norway
    'Viking': '🇩🇰'        # Denmark (Viking Link)
}
```

### **Cleaning Existing Flags**
```python
def clean_broken_flags(text):
    """Remove all emoji characters from text"""
    clean_text = text
    for char in text:
        if ord(char) > 127000:  # Unicode emoji range
            clean_text = clean_text.replace(char, '')
    return clean_text.strip()

# Example
broken = "🇫 ElecLink (France)"  # Broken flag
clean = clean_broken_flags(broken)  # "ElecLink (France)"
fixed = f"🇫🇷 {clean}"  # "🇫🇷 ElecLink (France)"
```

### **Writing with RAW Mode**
```python
from googleapiclient.discovery import build

# Prepare data with complete flags
data = [
    ['🇫🇷 ElecLink (France)', '999 MW Import'],
    ['🇮🇪 East-West (Ireland)', '0 MW Balanced'],
    # ... etc
]

# Write using RAW mode (CRITICAL!)
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!D8:E17',
    valueInputOption='RAW',  # Must be RAW, not USER_ENTERED
    body={'values': data}
).execute()
```

---

## 🔍 Verification

### **Check Flag Completeness**
```bash
python3 verify_flags.py
```

**Expected Output:**
```
Row 8: ✅ COMPLETE - 🇫🇷 ElecLink (France)
Row 9: ✅ COMPLETE - 🇮🇪 East-West (Ireland)
Row 10: ✅ COMPLETE - 🇫🇷 IFA (France)
...
```

### **Manual Verification**
Open Dashboard in Google Sheets:
- Check column D, rows 8-17
- Each interconnector should have **complete** 2-character flag
- If you see single characters (🇫 instead of 🇫🇷), flags are broken

---

## 🛠️ Prevention Strategy

### **1. Always Use RAW Mode for Emojis**
```python
# Template for any script writing emojis
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!D8:E17',
    valueInputOption='RAW',  # <--- CRITICAL
    body={'values': data}
).execute()
```

### **2. Clean Source Data First**
```python
# Before using data from BigQuery or other sources
def prepare_interconnector_name(raw_name):
    """Clean and add proper flag"""
    # Strip existing broken flags
    clean = clean_broken_flags(raw_name)
    
    # Match and add complete flag
    for key, flag in FLAG_MAP.items():
        if key in clean:
            return f"{flag} {clean}"
    
    return clean  # Fallback: no flag
```

### **3. Validate After Updates**
```python
# After any Dashboard update
import subprocess
result = subprocess.run(['python3', 'verify_flags.py'], capture_output=True)
if b'BROKEN' in result.stdout:
    print("⚠️ Flags broken, running fix...")
    subprocess.run(['python3', 'fix_interconnector_flags_permanent.py'])
```

### **4. Include in Update Scripts**
```python
# In update_dashboard_preserve_layout.py or similar

# After querying interconnector data
ic_data = get_interconnector_data()  # From BigQuery

# Clean and fix flags
ic_rows = []
for row in ic_data:
    ic_name = row['interconnector']
    ic_flow = row['flow']
    
    # Clean existing flags
    clean_name = clean_broken_flags(ic_name)
    
    # Add complete flag
    for key, flag in FLAG_MAP.items():
        if key in clean_name:
            ic_rows.append([f"{flag} {clean_name}", ic_flow])
            break

# Write with RAW mode
sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!D8:E17',
    valueInputOption='RAW',  # <--- CRITICAL
    body={'values': ic_rows}
).execute()
```

---

## 📊 Technical Details

### **Unicode Structure**
```python
# France flag: 🇫🇷
flag_fr = '\U0001F1EB\U0001F1F7'
print(len(flag_fr))  # 2 characters
print(ord(flag_fr[0]))  # 127467 (Regional Indicator F)
print(ord(flag_fr[1]))  # 127479 (Regional Indicator R)

# Regional indicators: U+1F1E6 to U+1F1FF (A-Z)
# Combine two to make country flag
```

### **Why RAW Mode Works**
- `USER_ENTERED`: Sheets interprets content (formulas, dates, **emojis**)
  - May reformat or split multi-byte characters
  - Unpredictable with complex Unicode sequences
  
- `RAW`: Sheets writes **exact bytes** without interpretation
  - Preserves multi-byte emoji sequences
  - No formatting, no interpretation
  - What you send is what gets stored

### **Detection Algorithm**
```python
def is_flag_complete(text):
    """Check if country flags are complete (2 chars each)"""
    flag_chars = [c for c in text if ord(c) > 127000]
    # Country flags should have 2 emoji chars
    return len(flag_chars) >= 2

# Examples
is_flag_complete("🇫🇷 ElecLink")  # True (2 chars)
is_flag_complete("🇫 ElecLink")    # False (1 char, broken)
is_flag_complete("ElecLink")      # False (no flag)
```

---

## 🚨 Common Mistakes

### **Mistake 1: Using USER_ENTERED**
```python
# ❌ This will break flags
sheets.values().update(
    valueInputOption='USER_ENTERED',
    body={'values': [['🇫🇷 ElecLink']]}
)
# Result: May become "🇫 ElecLink" (broken)
```

### **Mistake 2: Not Cleaning Source Data**
```python
# ❌ If source already has broken flags
source_data = "🇫 ElecLink (France)"
new_data = f"🇫🇷 {source_data}"  # "🇫🇷 🇫 ElecLink" (duplicate broken)

# ✅ Clean first
clean = clean_broken_flags(source_data)  # "ElecLink (France)"
new_data = f"🇫🇷 {clean}"  # "🇫🇷 ElecLink (France)" (correct)
```

### **Mistake 3: Assuming Flags Stay Fixed**
```python
# ❌ Fix once and forget
fix_flags()
# Later: another script overwrites with USER_ENTERED mode
update_other_data()  # Uses USER_ENTERED
# Result: Flags broken again

# ✅ Always use RAW mode in ALL scripts
```

---

## 📁 Related Files

| File | Purpose |
|------|---------|
| `fix_interconnector_flags_permanent.py` | Main fix script (run when flags break) |
| `verify_flags.py` | Check if flags are complete |
| `update_dashboard_preserve_layout.py` | Main update script (uses RAW mode) |
| `FLAG_FIX_TECHNICAL_GUIDE.md` | This document |

---

## ✅ Checklist: Flag-Safe Updates

Before updating Dashboard with interconnector data:

- [ ] Read source data
- [ ] Clean existing broken flags using `clean_broken_flags()`
- [ ] Apply complete flags using `FLAG_MAP`
- [ ] Use `valueInputOption='RAW'` when writing
- [ ] Verify with `verify_flags.py` after update
- [ ] If broken, run `fix_interconnector_flags_permanent.py`

---

## 🎯 Summary

**Problem**: Country flag emojis are 2-character Unicode sequences that get corrupted by Google Sheets `USER_ENTERED` mode

**Solution**: 
1. Clean existing flags (strip all emoji chars)
2. Add complete 2-character flags from mapping
3. Write using `valueInputOption='RAW'`

**Prevention**: Always use RAW mode when writing any emoji characters to Google Sheets

**Quick Fix**: `python3 fix_interconnector_flags_permanent.py` (2 seconds)

**Verification**: `python3 verify_flags.py` (check all flags complete)

---

**Last Updated**: November 10, 2025  
**Status**: ✅ All flags fixed and documented  
**Next Issue**: Run fix script immediately if flags break again
