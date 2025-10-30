#!/usr/bin/env python3
"""
Google Search + BMRS Data Integration Example
===========================================

This example shows how to combine Google Search API with your BMRS energy data
to create enhanced insights and research capabilities.

Features:
- Search for news about energy companies in your BMRS data
- Find government documents related to energy markets
- Research renewable energy developments
- Correlate search trends with energy data
"""

import json
import os
from datetime import datetime, timedelta

from google.cloud import bigquery

from google_search_api import GoogleSearchAPI


class EnergyResearchEngine:
    """Combines BMRS data with Google Search for enhanced energy research."""

    def __init__(self):
        self.search_api = GoogleSearchAPI()
        self.bq_client = bigquery.Client(project="jibber-jabber-knowledge")

    def research_energy_company(self, company_name: str) -> dict:
        """Research an energy company using both BMRS data and web search."""

        print(f"🔍 Researching energy company: {company_name}")

        # 1. Get BMRS data for company
        bmrs_data = self._get_company_bmrs_data(company_name)

        # 2. Search for recent news
        news_results = self.search_api.search_energy_news(
            keywords=[company_name, f"{company_name} energy"],
            days_back=30,
            max_results=10,
        )

        # 3. Find government documents
        gov_docs = self.search_api.search_government_documents(
            topic=f"{company_name} energy", file_types=["pdf"], max_results=5
        )

        # 4. General web search
        web_results = self.search_api.search_energy_companies(
            company_name=company_name,
            context="electricity generation transmission",
            max_results=10,
        )

        return {
            "company": company_name,
            "timestamp": datetime.now().isoformat(),
            "bmrs_data": bmrs_data,
            "news": news_results,
            "government_documents": gov_docs,
            "web_results": web_results,
        }

    def _get_company_bmrs_data(self, company_name: str) -> dict:
        """Get BMRS data for a specific company."""

        # Search for company in BM units data
        try:
            query = f"""
            SELECT DISTINCT
                bm_unit_id,
                fuel_type,
                registered_resource_name,
                COUNT(*) as data_points
            FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_*`
            WHERE UPPER(registered_resource_name) LIKE UPPER('%{company_name}%')
               OR UPPER(bm_unit_id) LIKE UPPER('%{company_name}%')
            GROUP BY bm_unit_id, fuel_type, registered_resource_name
            ORDER BY data_points DESC
            LIMIT 10
            """

            results = self.bq_client.query(query).to_dataframe()

            if not results.empty:
                return {
                    "found": True,
                    "bm_units": results.to_dict("records"),
                    "total_units": len(results),
                    "query_time": datetime.now().isoformat(),
                }
            else:
                return {"found": False, "message": "No BMRS data found for company"}

        except Exception as e:
            return {"found": False, "error": str(e)}

    def research_market_trends(self, topic: str, days_back: int = 14) -> dict:
        """Research market trends combining search and BMRS data."""

        print(f"📈 Researching market trends: {topic}")

        # Search for recent news and analysis
        news_results = self.search_api.search(
            query=f"{topic} UK energy market",
            num_results=15,
            search_type="news",
            date_restrict=f"d{days_back}",
            country="countryUK",
        )

        # Find analyst reports and research
        research_results = self.search_api.search(
            query=f"{topic} energy analysis report",
            num_results=10,
            file_type="pdf",
            date_restrict=f"d{days_back * 2}",  # Longer timeframe for reports
            country="countryUK",
        )

        # Get related BMRS data trends
        bmrs_trends = self._get_bmrs_trends(topic, days_back)

        return {
            "topic": topic,
            "timeframe_days": days_back,
            "news_articles": news_results,
            "research_reports": research_results,
            "bmrs_trends": bmrs_trends,
            "timestamp": datetime.now().isoformat(),
        }

    def _get_bmrs_trends(self, topic: str, days_back: int) -> dict:
        """Get BMRS data trends related to the topic."""

        try:
            # Map topics to BMRS data types
            topic_mapping = {
                "wind": ["bmrs_windfor", "bmrs_fuelinst"],
                "solar": ["bmrs_fuelinst"],
                "battery": ["bmrs_mils", "bmrs_mels"],
                "demand": ["bmrs_itsdo", "bmrs_mid"],
                "frequency": ["bmrs_freq"],
                "balancing": ["bmrs_bod", "bmrs_boalf"],
            }

            relevant_tables = []
            for key, tables in topic_mapping.items():
                if key.lower() in topic.lower():
                    relevant_tables.extend(tables)

            if not relevant_tables:
                return {"found": False, "message": "No relevant BMRS data types found"}

            # Query recent data from relevant tables
            table_union = " UNION ALL ".join(
                [
                    f"SELECT '{table}' as table_name, settlement_date, COUNT(*) as records FROM `jibber-jabber-knowledge.uk_energy_insights.{table}` WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY) GROUP BY settlement_date"
                    for table in relevant_tables[:3]  # Limit to prevent complex queries
                ]
            )

            query = f"""
            SELECT
                table_name,
                settlement_date,
                records
            FROM ({table_union})
            ORDER BY settlement_date DESC, table_name
            LIMIT 50
            """

            results = self.bq_client.query(query).to_dataframe()

            return {
                "found": True,
                "data": results.to_dict("records"),
                "tables_analyzed": relevant_tables[:3],
                "days_analyzed": days_back,
            }

        except Exception as e:
            return {"found": False, "error": str(e)}

    def find_regulatory_updates(self, keywords=None) -> dict:
        """Find recent regulatory updates affecting energy markets."""

        if not keywords:
            keywords = [
                "ofgem",
                "energy regulation",
                "electricity market reform",
                "capacity market",
                "balancing services",
                "grid code",
            ]

        print(f"⚖️ Searching for regulatory updates...")

        # Search Ofgem and government sites
        regulatory_results = {}

        sites_to_search = [
            "ofgem.gov.uk",
            "gov.uk",
            "elexon.co.uk",
            "nationalgrideso.com",
        ]

        for site in sites_to_search:
            site_results = self.search_api.search(
                query=" OR ".join([f'"{kw}"' for kw in keywords]),
                num_results=10,
                site_search=site,
                date_restrict="m3",  # Last 3 months
                country="countryUK",
            )
            regulatory_results[site] = site_results

        return {
            "keywords_searched": keywords,
            "sites_searched": sites_to_search,
            "results": regulatory_results,
            "timestamp": datetime.now().isoformat(),
        }


def demo_energy_research():
    """Demonstrate the energy research capabilities."""

    try:
        research_engine = EnergyResearchEngine()

        print("🔬 Energy Research Engine Demo")
        print("=" * 50)

        # Example 1: Research a specific company
        print("\n1️⃣ Researching National Grid...")
        company_research = research_engine.research_energy_company("National Grid")

        bmrs_data = company_research["bmrs_data"]
        if bmrs_data["found"]:
            print(f"   📊 Found {bmrs_data['total_units']} BM units")
            print(
                f"   📰 Found {len(company_research['news'].get('items', []))} news articles"
            )
            print(
                f"   📄 Found {len(company_research['government_documents'].get('pdf', {}).get('items', []))} government documents"
            )

        # Example 2: Market trends research
        print("\n2️⃣ Researching battery storage trends...")
        trends_research = research_engine.research_market_trends(
            "battery storage", days_back=7
        )

        print(
            f"   📈 Found {len(trends_research['news_articles'].get('items', []))} recent articles"
        )
        print(
            f"   📋 Found {len(trends_research['research_reports'].get('items', []))} research reports"
        )

        bmrs_trends = trends_research["bmrs_trends"]
        if bmrs_trends["found"]:
            print(f"   🔢 Analyzed {len(bmrs_trends['tables_analyzed'])} BMRS datasets")

        # Example 3: Regulatory updates
        print("\n3️⃣ Finding regulatory updates...")
        regulatory_updates = research_engine.find_regulatory_updates()

        total_regulatory = sum(
            len(results.get("items", []))
            for results in regulatory_updates["results"].values()
        )
        print(f"   ⚖️ Found {total_regulatory} regulatory documents")

        print(f"\n✅ Research demo completed!")
        print(f"   💡 This shows how Google Search enhances your BMRS data analysis")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\n📋 Make sure to run setup_google_search.py first!")


if __name__ == "__main__":
    demo_energy_research()
