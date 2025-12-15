#!/usr/bin/env python3
"""
Export ALL Directors from Companies That Own UK Property
Uses the clean_directors_list.csv which already links directors to property counts
"""

import pandas as pd
import re
from datetime import datetime

# Load the existing directors list from Land Registry directory
INPUT_FILE = "/home/shared/FullMacBackup/Land Regristry/clean_directors_list_20251114_1204.csv"
OUTPUT_FILE = f"property_directors_crm_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

def parse_name(full_name):
    """Parse director name into first and last name"""
    if not full_name or pd.isna(full_name):
        return "Unknown", "Unknown"
    
    name = str(full_name).strip()
    name = re.sub(r'\b(Sir|Dame|Dr|Mr|Mrs|Ms|Miss|Lord|Lady|OBE|MBE|CBE|KBE|DBE|PhD|MD|BSc|MSc|BA|MA)\b\.?', '', name, flags=re.IGNORECASE)
    name = name.strip()
    
    # Handle "SURNAME, Firstname" format (common in Companies House data)
    if ',' in name:
        parts = [p.strip() for p in name.split(',', 1)]
        if len(parts) == 2:
            surname, forename = parts[0], parts[1]
            first_name = forename.split()[0] if forename.split() else forename
            return first_name, surname
    
    # Handle "Firstname Lastname" format
    parts = name.split()
    if len(parts) >= 2:
        return parts[0], ' '.join(parts[1:])
    elif len(parts) == 1:
        return parts[0], ""
    
    return name, ""

def format_role(role):
    """Format director role as professional title"""
    if not role or pd.isna(role):
        return "Director"
    
    role = str(role).lower().strip()
    
    mapping = {
        'director': 'Director',
        'managing director': 'Managing Director',
        'chief executive': 'Chief Executive Officer',
        'ceo': 'CEO',
        'chairman': 'Chairman',
        'chairwoman': 'Chairwoman',  
        'secretary': 'Company Secretary',
        'cfo': 'Chief Financial Officer',
        'coo': 'Chief Operating Officer',
    }
    
    for key, value in mapping.items():
        if key in role:
            return value
    
    return role.title()

print("="*70)
print("PROPERTY COMPANY DIRECTORS - CRM FORMAT EXPORT")
print("="*70)
print()

print(f"📂 Loading data from: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)

print(f"✅ Loaded {len(df):,} director records")
print(f"   Companies: {df['company_number'].nunique():,}")
print(f"   Total properties: {df['property_count'].sum():,}")
print()

# Parse names
print("🔄 Parsing names...")
df[['first_name', 'last_name']] = df['director_name'].apply(lambda x: pd.Series(parse_name(x)))

# Format roles
print("🔄 Formatting titles...")
df['title'] = df['director_role'].apply(format_role)

# Create CRM-formatted DataFrame matching your template
crm_df = pd.DataFrame({
    'First Name': df['first_name'],
    'Last Name': df['last_name'],
    'Title': df['title'],
    'Company Name': df['company_name'],
    'Email': '',  # Not available in Companies House public data
    'Phone': '',  # Not available in Companies House public data
    'Stage': 'Cold',  # Default stage
    'Person Linkedin Url': ''  # Not available
})

# Remove duplicates
print("🔄 Removing duplicates...")
before = len(crm_df)
crm_df = crm_df.drop_duplicates(subset=['First Name', 'Last Name', 'Company Name'])
after = len(crm_df)
print(f"   Removed {before - after:,} duplicate records")
print()

# Save to CSV
print(f"💾 Saving to: {OUTPUT_FILE}")
crm_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Saved {len(crm_df):,} records")
print()

# Show sample
print("📋 Sample records (first 20):")
print(crm_df.head(20).to_string(index=False))
print()

# Statistics
print("📈 Statistics:")
print(f"   Total directors: {len(crm_df):,}")
print(f"   Unique companies: {crm_df['Company Name'].nunique():,}")
print(f"   Unique people: {(crm_df['First Name'] + ' ' + crm_df['Last Name']).nunique():,}")
print()
print("   Top 10 titles:")
for i, (title, count) in enumerate(crm_df['Title'].value_counts().head(10).items(), 1):
    print(f"      {i}. {title}: {count:,}")
print()
print("   Top 10 companies by director count:")
for i, (company, count) in enumerate(crm_df['Company Name'].value_counts().head(10).items(), 1):
    print(f"      {i}. {company}: {count} directors")

print()
print("✅ COMPLETE!")
print(f"📁 Output file: {OUTPUT_FILE}")
