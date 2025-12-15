#!/usr/bin/env python3
import pandas as pd
import re
from datetime import datetime

INPUT_FILE = "/home/shared/FullMacBackup/Land Regristry/clean_directors_list_20251114_1204.csv"
OUTPUT_FILE = f"property_directors_crm_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

print("="*70)
print("PROPERTY DIRECTORS CRM EXPORT (FAST)")
print("="*70)
print()

print(f"📂 Loading: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)
print(f"✅ Loaded {len(df):,} records\n")

# Vectorized name parsing
def split_name_fast(name):
    if ',' in name:
        parts = name.split(',', 1)
        surname = parts[0].strip()
        forename = parts[1].strip().split()[0] if parts[1].strip() else ""
        return forename, surname
    else:
        parts = name.strip().split()
        if len(parts) >= 2:
            return parts[0], ' '.join(parts[1:])
        return parts[0] if parts else "", ""

print("🔄 Processing names...")
names = df['director_name'].str.replace(r'\b(Sir|Dame|Dr|Mr|Mrs|Ms|Miss|Lord|Lady|OBE|MBE|CBE|KBE|DBE|PhD|MD|BSc|MSc|BA|MA)\b\.?', '', regex=True, flags=re.IGNORECASE)
split_names = names.apply(split_name_fast)
df['first_name'] = split_names.str[0]
df['last_name'] = split_names.str[1]

print("🔄 Formatting roles...")
df['title'] = df['director_role'].str.replace('director', 'Director', case=False).str.replace('secretary', 'Company Secretary', case=False).fillna('Director')

# Create CRM format
crm_df = pd.DataFrame({
    'First Name': df['first_name'],
    'Last Name': df['last_name'],
    'Title': df['title'],
    'Company Name': df['company_name'],
    'Email': '',
    'Phone': '',
    'Stage': 'Cold',
    'Person Linkedin Url': ''
})

print("🔄 Removing duplicates...")
crm_df = crm_df.drop_duplicates(subset=['First Name', 'Last Name', 'Company Name'])

print(f"💾 Saving to: {OUTPUT_FILE}")
crm_df.to_csv(OUTPUT_FILE, index=False)

print(f"\n✅ COMPLETE - {len(crm_df):,} records saved")
print(f"\n📋 Sample (first 15 rows):\n")
print(crm_df.head(15).to_string(index=False))

print(f"\n📈 Summary:")
print(f"   Directors: {len(crm_df):,}")
print(f"   Companies: {crm_df['Company Name'].nunique():,}")
print(f"   Top titles: {dict(crm_df['Title'].value_counts().head(5))}")
