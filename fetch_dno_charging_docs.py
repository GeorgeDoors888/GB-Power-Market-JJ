#!/usr/bin/env python3
"""
Fetch DUoS Charging Methodology and Tariff Documents for All 14 UK DNO License Areas

This script downloads charging methodology PDFs and Excel tariff schedules from:
- DNO websites (official sources)
- OpenDataSoft portals (where available)
- Ofgem data portal

Target documents:
- Use of System Charging Statements
- DUoS Tariff Schedules (by year)
- Connection Charging Methodologies
- Tariff Structure Annexes

Output structure:
  dno_charging_documents/
    ├── UKPN-LPN/
    ├── UKPN-EPN/
    ├── UKPN-SPN/
    ├── ENWL/
    ├── NPg-NE/
    ├── NPg-Y/
    ├── SP-Distribution/
    ├── SP-Manweb/
    ├── SSE-SHEPD/
    ├── SSE-SEPD/
    ├── NGED-WM/
    ├── NGED-EM/
    ├── NGED-SW/
    └── NGED-SWales/
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# DNO License Area Configuration
DNO_CONFIG = [
    {
        "mpan_id": "12",
        "dno_key": "UKPN-LPN",
        "dno_name": "UK Power Networks (London)",
        "short_code": "LPN",
        "market_id": "LOND",
        "gsp_group": "C",
        "gsp_name": "London",
        "website": "https://www.ukpowernetworks.co.uk",
        "data_portal": "https://ukpowernetworks.opendatasoft.com"
    },
    {
        "mpan_id": "10",
        "dno_key": "UKPN-EPN",
        "dno_name": "UK Power Networks (Eastern)",
        "short_code": "EPN",
        "market_id": "EELC",
        "gsp_group": "A",
        "gsp_name": "Eastern",
        "website": "https://www.ukpowernetworks.co.uk",
        "data_portal": "https://ukpowernetworks.opendatasoft.com"
    },
    {
        "mpan_id": "19",
        "dno_key": "UKPN-SPN",
        "dno_name": "UK Power Networks (South Eastern)",
        "short_code": "SPN",
        "market_id": "SEEB",
        "gsp_group": "J",
        "gsp_name": "South Eastern",
        "website": "https://www.ukpowernetworks.co.uk",
        "data_portal": "https://ukpowernetworks.opendatasoft.com"
    },
    {
        "mpan_id": "16",
        "dno_key": "ENWL",
        "dno_name": "Electricity North West",
        "short_code": "ENWL",
        "market_id": "NORW",
        "gsp_group": "G",
        "gsp_name": "North West",
        "website": "https://www.enwl.co.uk",
        "data_portal": "https://enwl.opendatasoft.com"
    },
    {
        "mpan_id": "15",
        "dno_key": "NPg-NE",
        "dno_name": "Northern Powergrid (North East)",
        "short_code": "NE",
        "market_id": "NEEB",
        "gsp_group": "F",
        "gsp_name": "North East",
        "website": "https://www.northernpowergrid.com",
        "data_portal": "https://northernpowergrid.opendatasoft.com"
    },
    {
        "mpan_id": "23",
        "dno_key": "NPg-Y",
        "dno_name": "Northern Powergrid (Yorkshire)",
        "short_code": "Y",
        "market_id": "YELG",
        "gsp_group": "M",
        "gsp_name": "Yorkshire",
        "website": "https://www.northernpowergrid.com",
        "data_portal": "https://northernpowergrid.opendatasoft.com"
    },
    {
        "mpan_id": "18",
        "dno_key": "SP-Distribution",
        "dno_name": "SP Energy Networks (SPD)",
        "short_code": "SPD",
        "market_id": "SPOW",
        "gsp_group": "N",
        "gsp_name": "South Scotland",
        "website": "https://www.spenergynetworks.co.uk",
        "data_portal": None  # SPEN no public portal found
    },
    {
        "mpan_id": "13",
        "dno_key": "SP-Manweb",
        "dno_name": "SP Energy Networks (SPM)",
        "short_code": "SPM",
        "market_id": "MANW",
        "gsp_group": "D",
        "gsp_name": "Merseyside & North Wales",
        "website": "https://www.spenergynetworks.co.uk",
        "data_portal": None
    },
    {
        "mpan_id": "17",
        "dno_key": "SSE-SHEPD",
        "dno_name": "Scottish Hydro Electric Power Distribution (SHEPD)",
        "short_code": "SHEPD",
        "market_id": "HYDE",
        "gsp_group": "P",
        "gsp_name": "North Scotland",
        "website": "https://www.ssen.co.uk",
        "data_portal": "https://ssen-transmissionnetwork.opendatasoft.com"  # Transmission, not distribution
    },
    {
        "mpan_id": "20",
        "dno_key": "SSE-SEPD",
        "dno_name": "Southern Electric Power Distribution (SEPD)",
        "short_code": "SEPD",
        "market_id": "SOUT",
        "gsp_group": "H",
        "gsp_name": "Southern",
        "website": "https://www.ssen.co.uk",
        "data_portal": "https://ssen-transmissionnetwork.opendatasoft.com"
    },
    {
        "mpan_id": "14",
        "dno_key": "NGED-WM",
        "dno_name": "National Grid Electricity Distribution – West Midlands (WMID)",
        "short_code": "WMID",
        "market_id": "MIDE",
        "gsp_group": "E",
        "gsp_name": "West Midlands",
        "website": "https://www.nationalgrid.com/electricity-distribution",
        "data_portal": None  # NGED no public OpenDataSoft portal
    },
    {
        "mpan_id": "11",
        "dno_key": "NGED-EM",
        "dno_name": "National Grid Electricity Distribution – East Midlands (EMID)",
        "short_code": "EMID",
        "market_id": "EMEB",
        "gsp_group": "B",
        "gsp_name": "East Midlands",
        "website": "https://www.nationalgrid.com/electricity-distribution",
        "data_portal": None
    },
    {
        "mpan_id": "22",
        "dno_key": "NGED-SW",
        "dno_name": "National Grid Electricity Distribution – South West (SWEST)",
        "short_code": "SWEST",
        "market_id": "SWEB",
        "gsp_group": "L",
        "gsp_name": "South Western",
        "website": "https://www.nationalgrid.com/electricity-distribution",
        "data_portal": None
    },
    {
        "mpan_id": "21",
        "dno_key": "NGED-SWales",
        "dno_name": "National Grid Electricity Distribution – South Wales (SWALES)",
        "short_code": "SWALES",
        "market_id": "SWAE",
        "gsp_group": "K",
        "gsp_name": "South Wales",
        "website": "https://www.nationalgrid.com/electricity-distribution",
        "data_portal": None
    }
]

# Known charging document URLs (manually curated)
CHARGING_DOC_URLS = {
    "UKPN": {
        "base_url": "https://www.ukpowernetworks.co.uk/internet/en/about-us/documents/",
        "duos_charges": "https://www.ukpowernetworks.co.uk/electricity/distribution-use-of-system-charges",
        "connection_charges": "https://www.ukpowernetworks.co.uk/electricity/network-connection-charges"
    },
    "ENWL": {
        "base_url": "https://www.enwl.co.uk/about-us/regulatory-information/",
        "duos_charges": "https://www.enwl.co.uk/about-us/regulatory-information/distribution-use-of-system-duos-charges/",
        "connection_charges": "https://www.enwl.co.uk/go-net-zero/connections/connection-charging/"
    },
    "NPg": {
        "base_url": "https://www.northernpowergrid.com/downloads",
        "duos_charges": "https://www.northernpowergrid.com/asset-management/network-pricing",
        "connection_charges": "https://www.northernpowergrid.com/downloads"
    },
    "SPEN": {
        "base_url": "https://www.spenergynetworks.co.uk/pages/distribution_charges.aspx",
        "duos_charges": "https://www.spenergynetworks.co.uk/pages/distribution_charges.aspx",
        "connection_charges": "https://www.spenergynetworks.co.uk/pages/connection_charging.aspx"
    },
    "SSEN": {
        "base_url": "https://www.ssen.co.uk/about-ssen/dso-distribution-system-operator/charging-and-connections/",
        "duos_charges": "https://www.ssen.co.uk/about-ssen/dso-distribution-system-operator/charging-and-connections/distribution-use-of-system-duos-charging/",
        "connection_charges": "https://www.ssen.co.uk/about-ssen/dso-distribution-system-operator/charging-and-connections/connection-charging/"
    },
    "NGED": {
        "base_url": "https://www.nationalgrid.com/electricity-distribution/connections/connection-charges",
        "duos_charges": "https://www.nationalgrid.com/electricity-distribution/network-and-assets/distribution-use-of-system-duos-charges",
        "connection_charges": "https://www.nationalgrid.com/electricity-distribution/connections/connection-charges"
    }
}


class DNOChargingDocFetcher:
    """Fetch charging methodology documents from DNO sources"""
    
    def __init__(self, output_dir: str = "dno_charging_documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        
    def create_dno_folders(self):
        """Create folder structure for all 14 DNO license areas"""
        for dno in DNO_CONFIG:
            dno_dir = self.output_dir / dno["dno_key"]
            dno_dir.mkdir(exist_ok=True)
            
            # Create metadata file
            metadata = {
                "mpan_id": dno["mpan_id"],
                "dno_key": dno["dno_key"],
                "dno_name": dno["dno_name"],
                "short_code": dno["short_code"],
                "market_id": dno["market_id"],
                "gsp_group": dno["gsp_group"],
                "gsp_name": dno["gsp_name"],
                "website": dno["website"],
                "data_portal": dno["data_portal"],
                "documents": [],
                "last_updated": datetime.now().isoformat()
            }
            
            metadata_file = dno_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        print(f"✅ Created folder structure for {len(DNO_CONFIG)} DNO license areas")
        
    def fetch_from_opendatasoft(self, dno: Dict) -> List[Dict]:
        """Fetch charging documents from OpenDataSoft API"""
        if not dno.get("data_portal"):
            return []
            
        documents = []
        api_url = f"{dno['data_portal']}/api/explore/v2.1/catalog/datasets"
        
        # Search for charging-related datasets
        search_terms = ["duos", "charges", "tariff", "connection", "use of system", "charging"]
        
        try:
            params = {
                "limit": 100,
                "refine": None
            }
            
            response = self.session.get(api_url, params=params, timeout=10, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                datasets = data.get("results", [])
                
                # Filter for charging-related datasets
                for dataset in datasets:
                    dataset_id = dataset.get("dataset_id", "")
                    title = dataset.get("metas", {}).get("default", {}).get("title", "").lower()
                    
                    # Check if dataset is charging-related
                    if any(term in title for term in search_terms):
                        documents.append({
                            "dataset_id": dataset_id,
                            "title": dataset.get("metas", {}).get("default", {}).get("title", ""),
                            "description": dataset.get("metas", {}).get("default", {}).get("description", ""),
                            "source": "opendatasoft",
                            "url": f"{dno['data_portal']}/explore/dataset/{dataset_id}"
                        })
                        
                print(f"  Found {len(documents)} charging datasets for {dno['dno_key']}")
                
        except Exception as e:
            print(f"  ⚠️  Error fetching from OpenDataSoft for {dno['dno_key']}: {e}")
            
        return documents
        
    def download_document(self, url: str, output_path: Path) -> bool:
        """Download a document from URL"""
        try:
            response = self.session.get(url, timeout=30, verify=False)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"    ⚠️  Error downloading {url}: {e}")
        return False
        
    def fetch_all_dno_documents(self):
        """Fetch charging documents for all 14 DNO license areas"""
        print(f"\n{'='*70}")
        print("FETCHING CHARGING DOCUMENTS FOR ALL 14 DNO LICENSE AREAS")
        print(f"{'='*70}\n")
        
        summary = {
            "total_dnos": len(DNO_CONFIG),
            "dnos_with_docs": 0,
            "total_documents": 0,
            "by_dno": {}
        }
        
        for dno in DNO_CONFIG:
            print(f"\n[{dno['mpan_id']}] {dno['dno_key']} - {dno['dno_name']}")
            print(f"  GSP Group: {dno['gsp_group']} ({dno['gsp_name']})")
            
            dno_dir = self.output_dir / dno["dno_key"]
            documents = []
            
            # Try OpenDataSoft portal first
            if dno.get("data_portal"):
                print(f"  📡 Checking OpenDataSoft portal...")
                ods_docs = self.fetch_from_opendatasoft(dno)
                documents.extend(ods_docs)
                
            # Update metadata
            metadata_file = dno_dir / "metadata.json"
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            metadata["documents"] = documents
            metadata["document_count"] = len(documents)
            metadata["last_updated"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            # Update summary
            summary["by_dno"][dno["dno_key"]] = {
                "dno_name": dno["dno_name"],
                "document_count": len(documents),
                "has_portal": dno.get("data_portal") is not None
            }
            
            if len(documents) > 0:
                summary["dnos_with_docs"] += 1
                summary["total_documents"] += len(documents)
                print(f"  ✅ Found {len(documents)} documents")
            else:
                print(f"  ⚠️  No documents found via API")
                
            time.sleep(1)  # Rate limiting
            
        # Save summary
        summary_file = self.output_dir / "fetch_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n{'='*70}")
        print("FETCH SUMMARY")
        print(f"{'='*70}")
        print(f"Total DNOs processed: {summary['total_dnos']}")
        print(f"DNOs with documents: {summary['dnos_with_docs']}")
        print(f"Total documents found: {summary['total_documents']}")
        print(f"\n📄 Summary saved to: {summary_file}")
        
        return summary
        

def main():
    """Main execution"""
    fetcher = DNOChargingDocFetcher()
    
    # Create folder structure
    fetcher.create_dno_folders()
    
    # Fetch documents
    summary = fetcher.fetch_all_dno_documents()
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("1. Manual download: Visit DNO websites for documents not available via API")
    print("2. Review metadata.json files in each DNO folder")
    print("3. Run document parser to extract tariff data")
    print("4. Generate Google Sheets with structured tariff data")
    print("5. Ingest to BigQuery for analysis")
    

if __name__ == "__main__":
    main()
