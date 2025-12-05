#!/usr/bin/env python3
"""
BigQuery Document Search for Revenue Settlement and Virtual Lead Party (VLP)
Searches document_chunks table in uk_energy_prod dataset
"""

import os
import sys
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from bigquery_config import (
    BIGQUERY_PROJECT_ID,
    BIGQUERY_DATASET,
    BIGQUERY_TABLE,
    CREDENTIALS_PATH,
    TABLE_REFERENCE,
    REVENUE_SETTLEMENT_TERMS,
    VLP_TERMS,
    DOCUMENT_SOURCES,
    OUTPUT_CSV,
    OUTPUT_JSON,
    MAX_RESULTS,
)


def initialize_client():
    """Initialize BigQuery client with credentials"""
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH
    
    return bigquery.Client(project=BIGQUERY_PROJECT_ID)


def build_search_query():
    """
    Build SQL query to search for revenue settlement and VLP documents
    Uses JOIN with document_metadata to get URLs
    """
    query = f"""
    WITH matched_chunks AS (
        SELECT 
            dc.*,
            dm.filename as document_name,
            dm.source_url as url,
            dm.source_domain,
            -- Calculate relevance score
            CASE 
                WHEN LOWER(dc.content) LIKE '%revenue%settlement%' THEN 1
                WHEN LOWER(dc.content) LIKE '%settlement%revenue%' THEN 1
                ELSE 0
            END +
            CASE 
                WHEN LOWER(dc.content) LIKE '%virtual%lead%party%' THEN 2
                WHEN LOWER(dc.content) LIKE '%vlp%' THEN 2
                ELSE 0
            END AS relevance_score
        FROM `{TABLE_REFERENCE}` dc
        LEFT JOIN `{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET}.document_metadata` dm
            ON dc.doc_id = dm.doc_id
        WHERE 
            (
                -- Revenue settlement keywords
                LOWER(dc.content) LIKE '%revenue%settlement%' OR
                LOWER(dc.content) LIKE '%settlement%revenue%' OR
                LOWER(dc.content) LIKE '%energy%settlement%' OR
                LOWER(dc.content) LIKE '%financial%settlement%' OR
                LOWER(dc.content) LIKE '%settlement%mechanism%' OR
                LOWER(dc.content) LIKE '%settlement%calculation%'
            )
            OR
            (
                -- VLP keywords
                LOWER(dc.content) LIKE '%virtual%lead%party%' OR
                LOWER(dc.content) LIKE '%vlp%' OR
                (LOWER(dc.content) LIKE '%virtual%' AND LOWER(dc.content) LIKE '%lead%') OR
                LOWER(dc.content) LIKE '%lead%party%'
            )
    ),
    source_filtered AS (
        SELECT *
        FROM matched_chunks
        WHERE 
            LOWER(source) LIKE '%bsc%' OR
            LOWER(source) LIKE '%ofgem%' OR
            LOWER(source) LIKE '%neso%' OR
            LOWER(source) LIKE '%elexon%' OR
            LOWER(document_name) LIKE '%bsc%' OR
            LOWER(document_name) LIKE '%ofgem%' OR
            LOWER(document_name) LIKE '%neso%'
    )
    SELECT 
        doc_id as document_id,
        document_name,
        source,
        url,
        chunk_id,
        content as chunk_text,
        relevance_score,
        -- Extract a snippet around the match
        SUBSTR(content, 1, 500) as snippet
    FROM source_filtered
    WHERE relevance_score > 0
    ORDER BY relevance_score DESC, document_name, chunk_id
    LIMIT {MAX_RESULTS}
    """
    
    return query


def execute_search(client):
    """
    Execute the BigQuery search and return results
    """
    print("=" * 100)
    print("BigQuery Document Search: Revenue Settlement & Virtual Lead Party (VLP)")
    print("=" * 100)
    print(f"\n🔍 Searching BigQuery table: {TABLE_REFERENCE}")
    print(f"   Project: {BIGQUERY_PROJECT_ID}")
    print(f"   Dataset: {BIGQUERY_DATASET}")
    print(f"   Table: {BIGQUERY_TABLE}")
    print(f"\n📝 Search criteria:")
    print(f"   • Revenue settlement keywords: {', '.join(REVENUE_SETTLEMENT_TERMS[:3])}...")
    print(f"   • VLP keywords: {', '.join(VLP_TERMS[:3])}...")
    print(f"   • Sources: {', '.join(['BSC', 'Ofgem', 'NESO'])}")
    print(f"\n⏳ Executing query...\n")
    
    try:
        query = build_search_query()
        query_job = client.query(query)
        results = query_job.result()
        df = results.to_dataframe()
        
        return df
    
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return None


def display_results(df):
    """
    Display search results in formatted output
    """
    if df is None or df.empty:
        print("❌ No documents found matching the criteria")
        print("\n💡 Suggestions:")
        print("   • Check if documents have been ingested into BigQuery")
        print("   • Verify source names match (BSC, Ofgem, NESO)")
        print("   • Run test_bigquery_connection.py to verify data")
        return
    
    print(f"✅ Found {len(df)} matching chunks from {df['document_id'].nunique()} unique documents\n")
    print("=" * 100)
    
    # Group by document
    for doc_id in df['document_id'].unique():
        doc_chunks = df[df['document_id'] == doc_id]
        first_chunk = doc_chunks.iloc[0]
        
        print(f"\n📄 Document: {first_chunk['document_name']}")
        print(f"   Source: {first_chunk['source']}")
        if pd.notna(first_chunk.get('url')) and first_chunk.get('url'):
            print(f"   URL: {first_chunk['url']}")
        print(f"   Document ID: {doc_id}")
        print(f"   Matching chunks: {len(doc_chunks)}")
        print(f"   Max relevance: {doc_chunks['relevance_score'].max()}")
        
        # Show top snippet
        top_chunk = doc_chunks.nlargest(1, 'relevance_score').iloc[0]
        snippet = top_chunk['snippet'].replace('\n', ' ').strip()
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        print(f"   Snippet: {snippet}")
        print("-" * 100)
    
    return df


def generate_summary(df):
    """
    Generate summary statistics
    """
    if df is None or df.empty:
        return
    
    print("\n" + "=" * 100)
    print("📊 Summary Statistics")
    print("=" * 100)
    
    print(f"\n• Total matching chunks: {len(df)}")
    print(f"• Unique documents: {df['document_id'].nunique()}")
    
    print(f"\n📁 Documents by source:")
    source_counts = df.groupby('source')['document_id'].nunique().sort_values(ascending=False)
    for source, count in source_counts.items():
        print(f"   • {source}: {count} documents")
    
    print(f"\n⭐ Top documents by relevance:")
    top_docs = df.groupby(['document_name', 'source']).agg({
        'relevance_score': 'max',
        'chunk_id': 'count'
    }).nlargest(5, 'relevance_score')
    
    for (doc_name, source), row in top_docs.iterrows():
        print(f"   • {doc_name[:60]:60s} (Source: {source:10s}, Score: {row['relevance_score']}, Chunks: {row['chunk_id']})")


def export_results(df):
    """
    Export results to CSV and JSON
    """
    if df is None or df.empty:
        return
    
    try:
        # Export to CSV
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n💾 Results exported to CSV: {OUTPUT_CSV}")
        
        # Create a summary JSON with unique documents
        docs_summary = []
        for doc_id in df['document_id'].unique():
            doc_chunks = df[df['document_id'] == doc_id]
            first_chunk = doc_chunks.iloc[0]
            
            doc_info = {
                'document_id': doc_id,
                'document_name': first_chunk['document_name'],
                'source': first_chunk['source'],
                'url': first_chunk.get('url', ''),
                'matching_chunks': len(doc_chunks),
                'max_relevance_score': int(doc_chunks['relevance_score'].max()),
                'snippets': doc_chunks.nlargest(3, 'relevance_score')['snippet'].tolist()
            }
            docs_summary.append(doc_info)
        
        # Export to JSON
        import json
        with open(OUTPUT_JSON, 'w') as f:
            json.dump({
                'search_date': datetime.now().isoformat(),
                'total_chunks': len(df),
                'unique_documents': len(docs_summary),
                'documents': docs_summary
            }, f, indent=2)
        
        print(f"💾 Summary exported to JSON: {OUTPUT_JSON}")
        
    except Exception as e:
        print(f"❌ Error exporting results: {e}")


def create_document_list():
    """
    Create a simple list of unique documents with URLs
    """
    client = initialize_client()
    df = execute_search(client)
    
    if df is None or df.empty:
        return
    
    # Create document list
    print("\n" + "=" * 100)
    print("📋 Document List with URLs")
    print("=" * 100)
    
    doc_list = []
    for doc_id in df['document_id'].unique():
        doc_chunks = df[df['document_id'] == doc_id]
        first_chunk = doc_chunks.iloc[0]
        
        doc_list.append({
            'document_name': first_chunk['document_name'],
            'source': first_chunk['source'],
            'url': first_chunk.get('url', 'N/A'),
            'relevance': int(doc_chunks['relevance_score'].max())
        })
    
    # Sort by relevance
    doc_list.sort(key=lambda x: x['relevance'], reverse=True)
    
    print("\nDocuments found (sorted by relevance):\n")
    for i, doc in enumerate(doc_list, 1):
        print(f"{i}. {doc['document_name']}")
        print(f"   Source: {doc['source']}")
        print(f"   URL: {doc['url']}")
        print(f"   Relevance: {'⭐' * doc['relevance']}")
        print()
    
    # Save to simple text file
    with open('document_list.txt', 'w') as f:
        f.write("Revenue Settlement & VLP Documents\n")
        f.write("=" * 80 + "\n\n")
        for i, doc in enumerate(doc_list, 1):
            f.write(f"{i}. {doc['document_name']}\n")
            f.write(f"   Source: {doc['source']}\n")
            f.write(f"   URL: {doc['url']}\n")
            f.write(f"   Relevance: {doc['relevance']}/3\n\n")
    
    print(f"💾 Document list saved to: document_list.txt")


def main():
    """
    Main execution function
    """
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: python bigquery_document_search.py")
        print("\nSearches BigQuery for documents related to:")
        print("  • Revenue settlement")
        print("  • Virtual Lead Party (VLP)")
        print("\nFilters by sources: BSC, Ofgem, NESO")
        print("\nOutputs:")
        print("  • bigquery_search_results.csv - Full results")
        print("  • bigquery_search_results.json - Summary with URLs")
        print("  • document_list.txt - Simple document list")
        return
    
    # Initialize client
    client = initialize_client()
    
    # Execute search
    df = execute_search(client)
    
    # Display results
    display_results(df)
    
    # Generate summary
    generate_summary(df)
    
    # Export results
    export_results(df)
    
    # Create document list
    if df is not None and not df.empty:
        create_document_list()
    
    print("\n" + "=" * 100)
    print("✅ Search Complete!")
    print("=" * 100)
    print("\n")


if __name__ == "__main__":
    main()
