#!/usr/bin/env python3
"""
Google Search CLI Tool for Energy Research
==========================================

Command-line interface for the Google Search API integration.
Uses your jibber_jabber_key.json service account credentials.

Usage examples:
    python search_cli.py news "renewable energy" --days 7
    python search_cli.py company "National Grid" --include-bmrs
    python search_cli.py gov "energy transition" --file-type pdf
    python search_cli.py trends "battery storage" --days 14
"""

import argparse
import json
import sys
from datetime import datetime

from energy_research_engine import EnergyResearchEngine
from google_search_api import GoogleSearchAPI


def search_news(args):
    """Search for energy news."""
    search_api = GoogleSearchAPI()

    keywords = args.query.split() if isinstance(args.query, str) else args.query

    results = search_api.search_energy_news(
        keywords=keywords, days_back=args.days, max_results=args.max_results
    )

    print(f"📰 News Search Results: '{' '.join(keywords)}'")
    print(
        f"   Found {len(results.get('items', []))} articles from last {args.days} days"
    )
    print("=" * 60)

    for i, item in enumerate(results.get("items", []), 1):
        print(f"\n{i}. {item['title']}")
        print(f"   🔗 {item['link']}")
        print(f"   📝 {item['snippet']}")
        if item.get("display_link"):
            print(f"   🏢 {item['display_link']}")


def search_company(args):
    """Search for energy company information."""
    if args.include_bmrs:
        research_engine = EnergyResearchEngine()
        results = research_engine.research_energy_company(args.query)

        print(f"🏢 Company Research: '{args.query}'")
        print("=" * 60)

        # BMRS data
        bmrs_data = results["bmrs_data"]
        if bmrs_data["found"]:
            print(f"\n📊 BMRS Data:")
            print(f"   Found {bmrs_data['total_units']} BM units")
            for unit in bmrs_data["bm_units"][:3]:
                print(
                    f"   • {unit['bm_unit_id']}: {unit['fuel_type']} ({unit['data_points']} records)"
                )

        # News
        news_items = results["news"].get("items", [])
        if news_items:
            print(f"\n📰 Recent News ({len(news_items)} articles):")
            for item in news_items[: args.max_results]:
                print(f"   • {item['title']}")
                print(f"     {item['link']}")

        # Government documents
        gov_items = results["government_documents"].get("pdf", {}).get("items", [])
        if gov_items:
            print(f"\n📄 Government Documents ({len(gov_items)} PDFs):")
            for item in gov_items[:3]:
                print(f"   • {item['title']}")
                print(f"     {item['link']}")
    else:
        search_api = GoogleSearchAPI()
        results = search_api.search_energy_companies(
            company_name=args.query, max_results=args.max_results
        )

        print(f"🏢 Company Search: '{args.query}'")
        print(f"   Found {len(results.get('items', []))} results")
        print("=" * 60)

        for i, item in enumerate(results.get("items", []), 1):
            print(f"\n{i}. {item['title']}")
            print(f"   🔗 {item['link']}")
            print(f"   📝 {item['snippet']}")


def search_government(args):
    """Search government documents."""
    search_api = GoogleSearchAPI()

    file_types = [args.file_type] if args.file_type else ["pdf"]

    results = search_api.search_government_documents(
        topic=args.query, file_types=file_types, max_results=args.max_results
    )

    print(f"🏛️ Government Document Search: '{args.query}'")
    print("=" * 60)

    for file_type, file_results in results.items():
        items = file_results.get("items", [])
        if items:
            print(f"\n📄 {file_type.upper()} Documents ({len(items)} found):")
            for i, item in enumerate(items, 1):
                print(f"\n{i}. {item['title']}")
                print(f"   🔗 {item['link']}")
                print(f"   📝 {item['snippet'][:150]}...")


def search_trends(args):
    """Search market trends."""
    research_engine = EnergyResearchEngine()

    results = research_engine.research_market_trends(
        topic=args.query, days_back=args.days
    )

    print(f"📈 Market Trends Analysis: '{args.query}'")
    print(f"   Analyzing last {args.days} days")
    print("=" * 60)

    # News trends
    news_items = results["news_articles"].get("items", [])
    print(f"\n📰 Recent News Trends ({len(news_items)} articles):")
    for item in news_items[: args.max_results]:
        print(f"   • {item['title']}")
        print(f"     {item['display_link']} - {item['link']}")

    # Research reports
    report_items = results["research_reports"].get("items", [])
    if report_items:
        print(f"\n📊 Research Reports ({len(report_items)} found):")
        for item in report_items[:3]:
            print(f"   • {item['title']}")
            print(f"     {item['link']}")

    # BMRS trends
    bmrs_trends = results["bmrs_trends"]
    if bmrs_trends.get("found"):
        print(f"\n🔢 BMRS Data Trends:")
        print(f"   Analyzed tables: {', '.join(bmrs_trends['tables_analyzed'])}")
        print(f"   Data points: {len(bmrs_trends['data'])} records")


def search_regulatory(args):
    """Search for regulatory updates."""
    research_engine = EnergyResearchEngine()

    keywords = args.query.split() if args.query else None
    results = research_engine.find_regulatory_updates(keywords)

    print("⚖️ Regulatory Updates Search")
    if keywords:
        print(f"   Keywords: {', '.join(keywords)}")
    print("=" * 60)

    for site, site_results in results["results"].items():
        items = site_results.get("items", [])
        if items:
            print(f"\n🏛️ {site} ({len(items)} documents):")
            for item in items[: args.max_results]:
                print(f"   • {item['title']}")
                print(f"     {item['link']}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Google Search API CLI for Energy Research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search_cli.py news "renewable energy wind" --days 7
  python search_cli.py company "National Grid" --include-bmrs --max-results 10
  python search_cli.py gov "net zero strategy" --file-type pdf
  python search_cli.py trends "battery storage" --days 14
  python search_cli.py regulatory --max-results 5
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Search commands")

    # News search
    news_parser = subparsers.add_parser("news", help="Search energy news")
    news_parser.add_argument("query", help="Search query (keywords)")
    news_parser.add_argument(
        "--days", type=int, default=7, help="Days back to search (default: 7)"
    )
    news_parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum results (default: 10)"
    )

    # Company search
    company_parser = subparsers.add_parser("company", help="Search energy company info")
    company_parser.add_argument("query", help="Company name")
    company_parser.add_argument(
        "--include-bmrs", action="store_true", help="Include BMRS data analysis"
    )
    company_parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum results (default: 10)"
    )

    # Government documents
    gov_parser = subparsers.add_parser("gov", help="Search government documents")
    gov_parser.add_argument("query", help="Search topic")
    gov_parser.add_argument(
        "--file-type", choices=["pdf", "doc", "xls"], help="File type filter"
    )
    gov_parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum results (default: 10)"
    )

    # Market trends
    trends_parser = subparsers.add_parser("trends", help="Analyze market trends")
    trends_parser.add_argument("query", help="Topic to analyze")
    trends_parser.add_argument(
        "--days", type=int, default=14, help="Days back to analyze (default: 14)"
    )
    trends_parser.add_argument(
        "--max-results",
        type=int,
        default=8,
        help="Maximum results per category (default: 8)",
    )

    # Regulatory updates
    reg_parser = subparsers.add_parser("regulatory", help="Find regulatory updates")
    reg_parser.add_argument("query", nargs="?", help="Specific keywords (optional)")
    reg_parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum results per site (default: 5)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # Check if search engine is configured
        if not os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
            print("❌ Google Search Engine ID not configured")
            print("   Run: python setup_google_search.py")
            return 1

        # Execute command
        if args.command == "news":
            search_news(args)
        elif args.command == "company":
            search_company(args)
        elif args.command == "gov":
            search_government(args)
        elif args.command == "trends":
            search_trends(args)
        elif args.command == "regulatory":
            search_regulatory(args)

        print(
            f"\n✅ Search completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    except KeyboardInterrupt:
        print("\n⏹️ Search cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        print("   💡 Make sure you've run setup_google_search.py first")
        return 1


if __name__ == "__main__":
    import os

    sys.exit(main())
