#!/usr/bin/env python3
"""
Advanced Search Tool - Enhanced Version
Searches across Elexon BSC Parties, BMRS Units, and NESO datasets
Features: Caching, fuzzy matching, AND/OR modes, BigQuery integration
"""

import os
import time
import json
import sqlite3
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from rapidfuzz import fuzz, process
from ckanapi import RemoteCKAN
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.cloud import bigquery

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

ELEXON_API_KEY = os.getenv("ELEXON_API_KEY")
SHEETS_CRED_FILE = os.getenv("SHEETS_CRED_FILE", "inner-cinema-credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
DEST_SHEET = os.getenv("DEST_SHEET", "Search")
DEST_RANGE = f"{DEST_SHEET}!A5:K20"  # Expanded to 16 rows, 11 columns

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# CKAN base for NESO
NESO_CKAN_BASE = "https://api.neso.energy/api/3/action"

# Cache parameters
CACHE_DB = "search_cache.db"
CACHE_TTL = 86400  # 24 hours
FUZZY_THRESHOLD = 70  # Minimum fuzzy match score

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SearchResult:
    """Structured search result"""
    type: str           # Party, BMUnit, NESOProject, BigQuery
    id: str             # Unique identifier
    name: str           # Display name
    role: str           # Role/category
    extra: str          # Additional info
    score: int          # Fuzzy match score (0-100)
    source: str         # ELEXON, BMRS, NESO, BigQuery
    capacity_mw: str = ""      # For generators
    fuel_type: str = ""        # For generators
    status: str = ""           # Active/Inactive

    def to_row(self) -> List[str]:
        """Convert to sheet row"""
        return [
            self.type, self.id, self.name, self.role, self.extra,
            str(self.score), self.source, self.capacity_mw,
            self.fuel_type, self.status, ""
        ]

# ============================================================================
# CACHE LAYER
# ============================================================================

class CacheManager:
    """SQLite-based cache with TTL"""

    def __init__(self, db_path: str = CACHE_DB, ttl: int = CACHE_TTL):
        self.db_path = db_path
        self.ttl = ttl
        self.conn = self._init_db()

    def _init_db(self) -> sqlite3.Connection:
        """Initialize cache database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_store (
                key TEXT PRIMARY KEY,
                data TEXT,
                timestamp REAL,
                ttl INTEGER
            )
        """)
        # Add index for faster lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_store(timestamp)")
        conn.commit()
        return conn

    def get(self, key: str) -> Optional[dict]:
        """Get cached data if not expired"""
        cur = self.conn.cursor()
        cur.execute("SELECT data, timestamp, ttl FROM cache_store WHERE key=?", (key,))
        row = cur.fetchone()

        if row:
            data, ts, ttl = row
            age = time.time() - ts
            if age < ttl:
                return json.loads(data)
            else:
                # Delete expired entry
                self.delete(key)
        return None

    def set(self, key: str, data: dict, ttl: Optional[int] = None):
        """Set cached data with optional custom TTL"""
        ttl = ttl or self.ttl
        self.conn.execute(
            "REPLACE INTO cache_store (key, data, timestamp, ttl) VALUES (?,?,?,?)",
            (key, json.dumps(data), time.time(), ttl)
        )
        self.conn.commit()

    def delete(self, key: str):
        """Delete cache entry"""
        self.conn.execute("DELETE FROM cache_store WHERE key=?", (key,))
        self.conn.commit()

    def clear_expired(self):
        """Clear all expired entries"""
        self.conn.execute(
            "DELETE FROM cache_store WHERE (? - timestamp) > ttl",
            (time.time(),)
        )
        self.conn.commit()

    def stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cache_store")
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM cache_store WHERE (? - timestamp) < ttl",
            (time.time(),)
        )
        valid = cur.fetchone()[0]

        return {"total": total, "valid": valid, "expired": total - valid}

# ============================================================================
# DATA FETCHERS
# ============================================================================

class ElexonFetcher:
    """Fetch Elexon BSC Parties data"""

    def __init__(self, cache: CacheManager):
        self.cache = cache

    def fetch_parties(self) -> pd.DataFrame:
        """Fetch BSC signatories with caching"""
        cache_key = "elexon_parties_v2"
        cached = self.cache.get(cache_key)

        if cached:
            return pd.DataFrame(cached)

        print("📥 Fetching Elexon BSC Parties...")
        url = "https://www.elexon.co.uk/bsc/about/elexon-key-contacts/bsc-signatories-qualified-persons/?export=bsc-signatories"

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            df = pd.read_html(resp.text)[0]

            # Normalize data
            df["all_aliases"] = df["Party Name"].str.upper().fillna("")
            df["normalized_roles"] = df["Party Roles"].str.split(",").apply(
                lambda r: [x.strip() for x in r] if isinstance(r, list) else []
            )

            self.cache.set(cache_key, df.to_dict("records"))
            print(f"   ✅ Loaded {len(df)} parties")
            return df

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return pd.DataFrame()

class BMRSFetcher:
    """Fetch BMRS BM Units data"""

    def __init__(self, cache: CacheManager, api_key: str):
        self.cache = cache
        self.api_key = api_key

    def fetch_bmunits(self) -> pd.DataFrame:
        """Fetch BM Units with caching"""
        cache_key = "bm_units_v2"
        cached = self.cache.get(cache_key)

        if cached:
            return pd.DataFrame(cached)

        print("📥 Fetching BMRS BM Units...")
        url = f"https://bmrs.elexon.co.uk/api/v1/reference/bmunits/all?APIKey={self.api_key}"

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            df = pd.DataFrame(data.get("response", []))

            if not df.empty:
                # Add normalized columns
                df["search_text"] = (
                    df["bMUnitID"].astype(str) + " " +
                    df.get("unitName", "").astype(str)
                ).str.lower()

            self.cache.set(cache_key, df.to_dict("records"))
            print(f"   ✅ Loaded {len(df)} BM Units")
            return df

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return pd.DataFrame()

class NESOFetcher:
    """Fetch NESO project/asset data"""

    def __init__(self, cache: CacheManager):
        self.cache = cache
        self.client = RemoteCKAN(NESO_CKAN_BASE)

    def sql_search(self, resource_id: str, term: str, columns: List[str]) -> pd.DataFrame:
        """Use CKAN DataStore SQL to search"""
        # Build WHERE clause for multiple columns
        where_clauses = [f'LOWER("{col}") LIKE LOWER(\'%{term}%\')' for col in columns]
        where_sql = " OR ".join(where_clauses)

        sql = f'SELECT * FROM "{resource_id}" WHERE {where_sql} LIMIT 100'

        try:
            res = self.client.action.datastore_search_sql(sql=sql)
            return pd.DataFrame(res.get("records", []))
        except Exception as e:
            return pd.DataFrame()

    def fetch_projects(self, term: str) -> List[Tuple[str, str, pd.DataFrame]]:
        """Search NESO datasets"""
        cache_key = f"neso_{term}_v2"
        cached = self.cache.get(cache_key)

        if cached:
            return [(r["id"], r["title"], pd.DataFrame(r["records"])) for r in cached]

        print(f"📥 Searching NESO for '{term}'...")

        try:
            datasets = self.client.action.package_search(q=term, rows=10)["results"]
            results = []

            for ds in datasets:
                for resource in ds.get("resources", [])[:3]:  # Limit resources per dataset
                    # Try common column names
                    df_res = self.sql_search(
                        resource["id"],
                        term,
                        ["projectName", "customerName", "name", "title", "assetName"]
                    )

                    if not df_res.empty:
                        results.append((ds["id"], ds["title"], df_res))

            # Cache results
            cache_data = [
                {"id": pid, "title": title, "records": df.to_dict("records")}
                for pid, title, df in results
            ]
            self.cache.set(cache_key, cache_data, ttl=3600)  # 1 hour TTL for searches

            print(f"   ✅ Found {len(results)} datasets")
            return results

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []

class BigQueryFetcher:
    """Fetch data from BigQuery tables"""

    def __init__(self, cache: CacheManager):
        self.cache = cache
        self.client = bigquery.Client(project=PROJECT_ID, location="US")

    def search_parties(self, term: str) -> pd.DataFrame:
        """Search dim_party table"""
        cache_key = f"bq_party_{term}"
        cached = self.cache.get(cache_key)

        if cached:
            return pd.DataFrame(cached)

        query = f"""
        SELECT
            party_id, party_name, is_vlp, is_vtp,
            party_categories, last_updated
        FROM `{PROJECT_ID}.{DATASET}.dim_party`
        WHERE LOWER(party_name) LIKE LOWER('%{term}%')
        LIMIT 20
        """

        try:
            df = self.client.query(query).to_dataframe()
            self.cache.set(cache_key, df.to_dict("records"), ttl=3600)
            return df
        except Exception as e:
            print(f"   ⚠️ BigQuery error: {e}")
            return pd.DataFrame()

    def search_bmunits(self, term: str) -> pd.DataFrame:
        """Search BMU registration data"""
        cache_key = f"bq_bmu_{term}"
        cached = self.cache.get(cache_key)

        if cached:
            return pd.DataFrame(cached)

        query = f"""
        SELECT DISTINCT
            elexonbmunit, leadpartyname, nationalgridsystemzones,
            fueltype, registeredcapacity
        FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
        WHERE LOWER(elexonbmunit) LIKE LOWER('%{term}%')
           OR LOWER(leadpartyname) LIKE LOWER('%{term}%')
        LIMIT 50
        """

        try:
            df = self.client.query(query).to_dataframe()
            self.cache.set(cache_key, df.to_dict("records"), ttl=3600)
            return df
        except Exception as e:
            print(f"   ⚠️ BigQuery error: {e}")
            return pd.DataFrame()

# ============================================================================
# SEARCH ENGINE
# ============================================================================

class SearchEngine:
    """Advanced search with fuzzy matching and multi-source"""

    def __init__(self, cache: CacheManager, api_key: str):
        self.cache = cache
        self.elexon = ElexonFetcher(cache)
        self.bmrs = BMRSFetcher(cache, api_key)
        self.neso = NESOFetcher(cache)
        self.bigquery = BigQueryFetcher(cache)

    def fuzzy_score(self, term: str, text: str) -> int:
        """Calculate fuzzy match score"""
        if not term or not text:
            return 0
        return fuzz.token_sort_ratio(term.lower(), str(text).lower())

    def search_parties(self, term: str, categories: Optional[List[str]] = None) -> List[SearchResult]:
        """Search BSC parties"""
        parties = self.elexon.fetch_parties()
        results = []

        if parties.empty:
            return results

        for _, p in parties.iterrows():
            score = self.fuzzy_score(term, p["Party Name"])

            if score >= FUZZY_THRESHOLD:
                # Check category filter
                if categories:
                    if not any(c in p["normalized_roles"] for c in categories):
                        continue

                results.append(SearchResult(
                    type="BSC Party",
                    id=str(p["Party ID"]),
                    name=p["Party Name"],
                    role=", ".join(p["normalized_roles"][:3]),  # Limit roles
                    extra=p.get("Qualification Status", ""),
                    score=score,
                    source="ELEXON",
                    status="Active"
                ))

        return results

    def search_bmunits(self, term: str) -> List[SearchResult]:
        """Search BM Units"""
        units = self.bmrs.fetch_bmunits()
        results = []

        if units.empty:
            return results

        # Use rapidfuzz for efficient fuzzy matching
        if "search_text" in units.columns:
            matches = process.extract(
                term.lower(),
                units["search_text"].tolist(),
                scorer=fuzz.token_sort_ratio,
                limit=20,
                score_cutoff=FUZZY_THRESHOLD
            )

            for match_text, score, idx in matches:
                u = units.iloc[idx]
                results.append(SearchResult(
                    type="BM Unit",
                    id=str(u["bMUnitID"]),
                    name=u.get("unitName", ""),
                    role=u.get("leadParty", ""),
                    extra=u.get("nationalGrid", ""),
                    score=score,
                    source="BMRS",
                    capacity_mw=str(u.get("nominalCapacity", "")),
                    fuel_type=u.get("fuelType", "")
                ))

        return results

    def search_neso(self, term: str) -> List[SearchResult]:
        """Search NESO projects"""
        projects = self.neso.fetch_projects(term)
        results = []

        for pid, title, df_records in projects:
            for _, row in df_records.iterrows():
                project_name = row.get("projectName", row.get("name", ""))
                customer = row.get("customerName", row.get("customer", ""))

                results.append(SearchResult(
                    type="NESO Project",
                    id=pid,
                    name=title[:50],  # Truncate long titles
                    role=customer[:30],
                    extra=project_name[:50],
                    score=self.fuzzy_score(term, project_name),
                    source="NESO",
                    capacity_mw=str(row.get("capacity", "")),
                    status=row.get("status", "")
                ))

        return results

    def search_bigquery(self, term: str) -> List[SearchResult]:
        """Search BigQuery tables"""
        results = []

        # Search parties
        parties = self.bigquery.search_parties(term)
        for _, p in parties.iterrows():
            vlp_vtp = []
            if p.get("is_vlp"): vlp_vtp.append("VLP")
            if p.get("is_vtp"): vlp_vtp.append("VTP")

            results.append(SearchResult(
                type="BQ Party",
                id=str(p["party_id"]),
                name=p["party_name"],
                role=" + ".join(vlp_vtp) if vlp_vtp else "Party",
                extra=p.get("party_categories", "")[:50],
                score=self.fuzzy_score(term, p["party_name"]),
                source="BigQuery",
                status="Active"
            ))

        # Search BMUs
        bmunits = self.bigquery.search_bmunits(term)
        for _, u in bmunits.iterrows():
            results.append(SearchResult(
                type="BQ BMUnit",
                id=str(u["elexonbmunit"]),
                name=str(u["leadpartyname"]),
                role=u.get("nationalgridsystemzones", "")[:30],
                extra="",
                score=self.fuzzy_score(term, u["elexonbmunit"]),
                source="BigQuery",
                capacity_mw=str(u.get("registeredcapacity", "")),
                fuel_type=u.get("fueltype", "")
            ))

        return results

    def search(
        self,
        term: Optional[str] = None,
        categories: Optional[List[str]] = None,
        bm_unit: Optional[str] = None,
        neso_term: Optional[str] = None,
        use_bigquery: bool = True,
        mode: str = "OR"  # OR or AND
    ) -> List[SearchResult]:
        """
        Execute search across all sources

        Args:
            term: General search term for parties
            categories: Filter by party categories
            bm_unit: BM Unit ID filter
            neso_term: NESO-specific search
            use_bigquery: Include BigQuery results
            mode: "OR" (any match) or "AND" (all filters must match)
        """
        all_results = []

        # Collect results from all sources
        if term:
            all_results.extend(self.search_parties(term, categories))

        if bm_unit:
            all_results.extend(self.search_bmunits(bm_unit))

        if neso_term:
            all_results.extend(self.search_neso(neso_term))

        if use_bigquery and (term or bm_unit):
            search_term = term or bm_unit
            all_results.extend(self.search_bigquery(search_term))

        # Apply AND mode filtering if needed
        if mode == "AND" and len([x for x in [term, categories, bm_unit, neso_term] if x]) > 1:
            # Complex AND logic - ensure results match multiple criteria
            filtered = []
            for r in all_results:
                matches = 0
                if term and term.lower() in r.name.lower():
                    matches += 1
                if categories and any(c in r.role for c in categories):
                    matches += 1
                if bm_unit and bm_unit.lower() in r.id.lower():
                    matches += 1
                if neso_term and r.source == "NESO":
                    matches += 1

                # Require at least 2 matches for AND mode
                if matches >= 2:
                    filtered.append(r)

            all_results = filtered

        # Sort by score and deduplicate
        sorted_results = sorted(all_results, key=lambda x: x.score, reverse=True)

        # Remove duplicates by ID
        seen = set()
        unique_results = []
        for r in sorted_results:
            key = f"{r.source}:{r.id}"
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results[:50]  # Limit to top 50

# ============================================================================
# GOOGLE SHEETS INTEGRATION
# ============================================================================

class SheetsWriter:
    """Write results to Google Sheets"""

    def __init__(self, cred_file: str, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        credentials = Credentials.from_service_account_file(
            cred_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        self.service = build("sheets", "v4", credentials=credentials)

    def create_search_sheet_if_needed(self):
        """Create Search sheet if it doesn't exist"""
        try:
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            sheets = sheet_metadata.get('sheets', [])
            search_exists = any(s['properties']['title'] == DEST_SHEET for s in sheets)

            if not search_exists:
                print(f"📄 Creating '{DEST_SHEET}' sheet...")
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': DEST_SHEET,
                                'gridProperties': {
                                    'rowCount': 100,
                                    'columnCount': 11
                                }
                            }
                        }
                    }]
                }
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                print("   ✅ Created")
        except Exception as e:
            print(f"   ⚠️ Could not create sheet: {e}")

    def format_header(self, results: List[SearchResult]) -> List[List[str]]:
        """Create header rows"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return [
            ["🔍 ADVANCED SEARCH RESULTS", "", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", "", ""],
            [f"Generated: {timestamp}", f"Results: {len(results)}", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", "", ""],
            ["Type", "ID", "Name", "Role", "Extra", "Score", "Source", "Capacity (MW)", "Fuel Type", "Status", ""]
        ]

    def format_matrix(self, results: List[SearchResult], max_rows: int = 16) -> List[List[str]]:
        """Format results as matrix"""
        header = self.format_header(results)
        data = [r.to_row() for r in results[:max_rows]]

        # Pad to fill sheet
        while len(data) < max_rows:
            data.append([""] * 11)

        return header + data

    def update_sheet(self, results: List[SearchResult]):
        """Write results to sheet"""
        self.create_search_sheet_if_needed()

        matrix = self.format_matrix(results, max_rows=16)
        body = {"values": matrix}

        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{DEST_SHEET}!A1:K21",
            valueInputOption="RAW",
            body=body
        ).execute()

        # Apply formatting
        self._apply_formatting()

    def _apply_formatting(self):
        """Apply formatting to Search sheet"""
        try:
            # Get sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            sheet_id = None
            for s in sheet_metadata.get('sheets', []):
                if s['properties']['title'] == DEST_SHEET:
                    sheet_id = s['properties']['sheetId']
                    break

            if not sheet_id:
                return

            requests = [
                # Header row (row 1)
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
                                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14},
                                'horizontalAlignment': 'CENTER'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                    }
                },
                # Column headers (row 5)
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 4,
                            'endRowIndex': 5
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                                'textFormat': {'bold': True},
                                'horizontalAlignment': 'CENTER'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                    }
                }
            ]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
        except Exception as e:
            print(f"   ⚠️ Could not apply formatting: {e}")

# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """Main CLI interface"""
    print("=" * 80)
    print("🔍 ADVANCED SEARCH TOOL - Enhanced Version")
    print("=" * 80)

    # Initialize
    cache = CacheManager()
    cache.clear_expired()

    print(f"\n📊 Cache stats: {cache.stats()}")
    print()

    # Get search parameters
    term = input("Party/Name search (text): ").strip() or None

    cat_in = input("Categories (Supplier,Generator,VLP,VTP comma separated): ").strip()
    categories = [c.strip() for c in cat_in.split(",")] if cat_in else None

    bm = input("BM Unit ID filter: ").strip() or None
    neso = input("NESO asset/project search term: ").strip() or None

    use_bq_input = input("Include BigQuery results? (Y/n): ").strip().lower()
    use_bq = use_bq_input != 'n'

    mode_input = input("Search mode (OR/AND) [OR]: ").strip().upper()
    mode = "AND" if mode_input == "AND" else "OR"

    print("\n" + "=" * 80)
    print(f"🔍 Searching with mode: {mode}")
    print("=" * 80)

    # Execute search
    engine = SearchEngine(cache, ELEXON_API_KEY)
    results = engine.search(
        term=term,
        categories=categories,
        bm_unit=bm,
        neso_term=neso,
        use_bigquery=use_bq,
        mode=mode
    )

    print(f"\n✅ Found {len(results)} results")

    # Display top results
    if results:
        print("\n" + "=" * 80)
        print("TOP 10 RESULTS:")
        print("=" * 80)
        for i, r in enumerate(results[:10], 1):
            print(f"{i:2d}. [{r.score:3d}] {r.type:15s} | {r.name[:40]:40s} | {r.source}")

    # Write to Google Sheets
    print("\n📊 Writing to Google Sheets...")
    writer = SheetsWriter(SHEETS_CRED_FILE, SPREADSHEET_ID)
    writer.update_sheet(results)

    print(f"\n✅ Results written to '{DEST_SHEET}' sheet successfully!")
    print(f"📄 Sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Search cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
