#!/usr/bin/env python3
"""
Simple Property Directors Export
Uses existing Companies House directors data that already has company numbers
"""

from google.cloud import bigquery
import pandas as pd
import re
from datetime import datetime
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "companies_house"
OUTPUT_FILE = f"property_directors_crm_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

def parse_name(full_name):
    """Parse director name into first and last name"""
    if not full_name or pd.isna(full_name):
        return "Unknown", "Unknown"
    
    name = str(full_name).strip()
    name = re.sub(r'\b(Sir|Dame|Dr|Mr|Mrs|Ms|Miss|Lord|Lady|OBE|MBE|CBE|KBE|DBE|PhD|MD|BSc|MSc|BA|MA)\b\.?', '', name, flags=re.IGNORECASE)
    name = name.strip()
    
    # Handle "SURNAME, Firstname" format
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
    
    return "Unknown", "Unknown"

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

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser("~/.config/google-cloud/bigquery-credentials.json")

print("="*70)
print("PROPERTY COMPANY DIRECTORS EXPORT")
print("="*70)
print()

client = bigquery.Client(project=PROJECT_ID)

# Simple query: Get all active directors from companies that own property
# We'll identify property companies by matching names with land registry
query = f"""
WITH property_company_names AS (
    -- Get all unique company-like property owners
    SELECT DISTINCT
        UPPER(TRIM(proprietor_name_1)) as property_owner_upper,
        proprietor_name_1 as original_name,
        COUNT(DISTINCT title_number) as property_count
    FROM `{PROJECT_ID}.{DATASET_ID}.land_registry_uk_companies`
    WHERE proprietor_name_1 IS NOT NULL
        AND (
            UPPER(proprietor_name_1) LIKE '%LIMITED%' 
            OR UPPER(proprietor_name_1) LIKE '%LTD%'
            OR UPPER(proprietor_name_1) LIKE '%LLP%'
            OR UPPER(proprietor_name_1) LIKE '%PLC%'
        )
    GROUP BY proprietor_name_1
),

matching_companies AS (
    -- Match company names to get company numbers
    SELECT DISTINCT
        c.company_number,
        c.company_name,
        pc.property_count
    FROM `{PROJECT_ID}.{DATASET_ID}.companies` c
    INNER JOIN property_company_names pc
        ON UPPER(TRIM(c.company_name)) = pc.property_owner_upper
)

-- Get all active directors for these companies
SELECT 
    d.name as director_name,
    d.role as director_role,
    d.company_number,
    mc.company_name,
    mc.property_count,
    d.nationality,
    d.occupation
FROM `{PROJECT_ID}.{DATASET_ID}.directors` d
INNER JOIN matching_companies mc
    ON d.company_number = mc.company_number
WHERE d.is_active = TRUE
ORDER BY mc.property_count DESC, mc.company_name, d.name
"""

print(f"🔍 Querying BigQuery for property company directors...")
print(f"   Project: {PROJECT_ID}")
print(f"   Dataset: {DATASET_ID}")
print()

try:
    query_job = client.query(query)
    df = query_job.result().to_dataframe()
    
    print(f"✅ Retrieved {len(df):,} director records")
    print()
    
    if len(df) == 0:
        print("❌ No matching companies found")
        print("\nTrying alternative approach - just get all directors with property keywords in company name...")
        
        # Alternative: Just search for companies with property-related keywords
        alt_query = f"""
        SELECT 
            d.name as director_name,
            d.role as director_role,
            d.company_number,
            c.company_name,
            0 as property_count,
            d.nationality,
            d.occupation
        FROM `{PROJECT_ID}.{DATASET_ID}.directors` d
        INNER JOIN `{PROJECT_ID}.{DATASET_ID}.companies` c
            ON d.company_number = c.company_number
        WHERE d.is_active = TRUE
            AND (
                UPPER(c.company_name) LIKE '%PROPERTY%'
                OR UPPER(c.company_name) LIKE '%PROPERTIES%'
                OR UPPER(c.company_name) LIKE '%HOUSING%'
                OR UPPER(c.company_name) LIKE '%ESTATE%'
                OR UPPER(c.company_name) LIKE '%LAND%'
            )
        ORDER BY c.company_name, d.name
        LIMIT 50000
        """
        
        df = client.query(alt_query).result().to_dataframe()
        print(f"✅ Found {len(df):,} directors from property-related companies")
        print()
    
    # Parse names and format
    print("🔄 Formatting data for CRM...")
    df[['first_name', 'last_name']] = df['director_name'].apply(lambda x: pd.Series(parse_name(x)))
    df['title'] = df['director_role'].apply(format_role)
    
    # Create CRM DataFrame
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
    
    # Save
    output_path = os.path.join(os.getcwd(), OUTPUT_FILE)
    crm_df.to_csv(output_path, index=False)
    
    print(f"✅ Saved to: {output_path}")
    print(f"📊 Total records: {len(crm_df):,}")
    print()
    
    # Sample
    print("📋 Sample records:")
    print(crm_df.head(15).to_string(index=False))
    print()
    
    # Stats
    print("📈 Statistics:")
    print(f"   Unique companies: {crm_df['Company Name'].nunique():,}")
    print(f"   Unique directors: {(crm_df['First Name'] + ' ' + crm_df['Last Name']).nunique():,}")
    print(f"   Top 5 titles:")
    for title, count in crm_df['Title'].value_counts().head(5).items():
        print(f"      - {title}: {count:,}")
    
    print()
    print("✅ COMPLETE!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
