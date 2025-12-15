#!/usr/bin/env python3
"""
Extract Property Company Directors in CRM Format
Queries BigQuery to get all UK property-owning companies and their directors
Outputs in CRM-ready format with columns: First Name, Last Name, Title, Company Name, Email, Phone, Stage, Person Linkedin Url
"""

from google.cloud import bigquery
import pandas as pd
import re
from datetime import datetime
import os

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "companies_house"
OUTPUT_FILE = f"property_directors_crm_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

def parse_director_name(full_name):
    """Parse director name into first and last name"""
    if not full_name or pd.isna(full_name):
        return "Unknown", "Unknown"
    
    name = str(full_name).strip()
    
    # Remove common titles and suffixes
    name = re.sub(r'\b(Sir|Dame|Dr|Mr|Mrs|Ms|Miss|Lord|Lady)\b\.?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\b(OBE|MBE|CBE|KBE|DBE|PhD|MD|BSc|MSc|BA|MA)\b\.?', '', name, flags=re.IGNORECASE)
    name = name.strip()
    
    # Handle comma-separated names (surname, forename)
    if ',' in name:
        parts = [p.strip() for p in name.split(',')]
        if len(parts) >= 2:
            surname = parts[0].strip()
            forenames = parts[1].strip()
            first_name_parts = forenames.split()
            first_name = first_name_parts[0] if first_name_parts else forenames
            return first_name, surname
    
    # Handle space-separated names
    name_parts = name.split()
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        return first_name, last_name
    elif len(name_parts) == 1:
        return name_parts[0], ""
    
    return "Unknown", "Unknown"

def format_role_as_title(role):
    """Format director role as professional title"""
    if not role or pd.isna(role):
        return "Director"
    
    role = str(role).lower().strip()
    
    role_mapping = {
        'director': 'Director',
        'managing director': 'Managing Director',
        'chief executive': 'Chief Executive Officer',
        'ceo': 'Chief Executive Officer',
        'chairman': 'Chairman',
        'chairwoman': 'Chairwoman',
        'secretary': 'Company Secretary',
        'chief financial officer': 'Chief Financial Officer',
        'cfo': 'Chief Financial Officer',
        'chief operating officer': 'Chief Operating Officer',
        'coo': 'Chief Operating Officer',
    }
    
    return role_mapping.get(role, role.title())

def query_property_directors():
    """Query BigQuery for property-owning companies and directors"""
    print("🔄 Connecting to BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # First, extract company numbers from property owner names
    # UK company numbers are typically in format: "(CO. NO. 12345678)" or similar
    query = f"""
    WITH property_companies AS (
        -- Extract company numbers from proprietor names
        SELECT DISTINCT
            REGEXP_EXTRACT(proprietor_name_1, r'\\((?:CO\\.? NO\\.?|COMPANY NO\\.?|REG(?:D)?\\.? NO\\.?)\\s*([0-9A-Z]{{6,8}})\\)') as company_number,
            proprietor_name_1 as company_name,
            COUNT(DISTINCT title_number) as property_count
        FROM `{PROJECT_ID}.{DATASET_ID}.land_registry_uk_companies`
        WHERE proprietor_name_1 IS NOT NULL
            AND proprietor_name_1 != ''
            AND REGEXP_CONTAINS(proprietor_name_1, r'\\((?:CO\\.? NO\\.?|COMPANY NO\\.?|REG(?:D)?\\.? NO\\.?)\\s*[0-9A-Z]{{6,8}}\\)')
        GROUP BY company_number, company_name
        HAVING company_number IS NOT NULL
    ),
    
    -- Also get companies from the companies table that match
    companies_with_directors AS (
        SELECT DISTINCT
            c.company_number,
            c.company_name
        FROM `{PROJECT_ID}.{DATASET_ID}.companies` c
        WHERE EXISTS (
            SELECT 1 
            FROM `{PROJECT_ID}.{DATASET_ID}.land_registry_uk_companies` lr
            WHERE REGEXP_EXTRACT(lr.proprietor_name_1, r'\\((?:CO\\.? NO\\.?|COMPANY NO\\.?|REG(?:D)?\\.? NO\\.?)\\s*([0-9A-Z]{{6,8}})\\)') = c.company_number
        )
    )
    
    SELECT 
        d.name as director_name,
        d.role as director_role,
        d.company_number,
        COALESCE(cwd.company_name, pc.company_name) as company_name,
        COALESCE(pc.property_count, 0) as property_count,
        d.appointed_on,
        d.resigned_on,
        d.is_active
    FROM `{PROJECT_ID}.{DATASET_ID}.directors` d
    LEFT JOIN property_companies pc 
        ON d.company_number = pc.company_number
    LEFT JOIN companies_with_directors cwd
        ON d.company_number = cwd.company_number
    WHERE (pc.company_number IS NOT NULL OR cwd.company_number IS NOT NULL)
        AND (d.is_active = TRUE OR d.resigned_on IS NULL)
    ORDER BY property_count DESC, company_name, d.name
    LIMIT 100000
    """
    
    print("🔍 Executing BigQuery query...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Dataset: {DATASET_ID}")
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert to DataFrame
        df = results.to_dataframe()
        print(f"✅ Retrieved {len(df):,} director records")
        
        return df
        
    except Exception as e:
        print(f"❌ BigQuery query failed: {e}")
        return None

def format_for_crm(df):
    """Format DataFrame to match CRM CSV structure"""
    print("🔄 Formatting data for CRM...")
    
    # Parse names
    df[['first_name', 'last_name']] = df['director_name'].apply(
        lambda x: pd.Series(parse_director_name(x))
    )
    
    # Format roles
    df['title'] = df['director_role'].apply(format_role_as_title)
    
    # Create CRM-formatted DataFrame
    crm_df = pd.DataFrame({
        'First Name': df['first_name'],
        'Last Name': df['last_name'],
        'Title': df['title'],
        'Company Name': df['company_name'],
        'Email': '',  # Not available in Companies House data
        'Phone': '',  # Not available in Companies House data
        'Stage': 'Cold',  # Default to Cold
        'Person Linkedin Url': ''  # Not available
    })
    
    print(f"✅ Formatted {len(crm_df):,} records")
    
    return crm_df

def main():
    print("=" * 70)
    print("UK PROPERTY COMPANY DIRECTORS - CRM FORMAT EXTRACTOR")
    print("=" * 70)
    print()
    
    # Check credentials
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        print("⚠️  GOOGLE_APPLICATION_CREDENTIALS not set")
        credentials_path = os.path.expanduser("~/.config/google-cloud/bigquery-credentials.json")
        if os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            print(f"✅ Using credentials from: {credentials_path}")
        else:
            print(f"❌ Credentials not found at: {credentials_path}")
            return
    else:
        print(f"✅ Using credentials from: {credentials_path}")
    
    print()
    
    # Query BigQuery
    df = query_property_directors()
    
    if df is None or len(df) == 0:
        print("❌ No data retrieved")
        return
    
    print()
    
    # Format for CRM
    crm_df = format_for_crm(df)
    
    print()
    
    # Save to CSV
    output_path = os.path.join(os.getcwd(), OUTPUT_FILE)
    crm_df.to_csv(output_path, index=False)
    
    print(f"💾 Saved to: {output_path}")
    print(f"📊 Total records: {len(crm_df):,}")
    print()
    
    # Show sample
    print("📋 Sample records:")
    print(crm_df.head(10).to_string(index=False))
    print()
    
    # Statistics
    print("📈 Statistics:")
    print(f"   Unique companies: {crm_df['Company Name'].nunique():,}")
    print(f"   Unique directors: {(crm_df['First Name'] + ' ' + crm_df['Last Name']).nunique():,}")
    print(f"   Top titles: {crm_df['Title'].value_counts().head(5).to_dict()}")
    print()
    print("✅ COMPLETE!")

if __name__ == "__main__":
    main()
