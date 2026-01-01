#!/usr/bin/env python3
"""
Fast Search API - Direct BigQuery
Returns results in 2-3 seconds instead of minutes
Includes caching for 5-minute TTL
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery
from datetime import datetime, timedelta
import os
import hashlib
import json

app = Flask(__name__)
CORS(app)

# Search result cache (5-minute TTL)
SEARCH_CACHE = {}
CACHE_TTL = 300  # 5 minutes in seconds

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
PORT = 5002

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID, location="US")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Fast Search API (Direct BigQuery)',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/search', methods=['POST'])
def execute_search():
    """
    Fast search using direct BigQuery queries
    Includes 5-minute result caching
    
    Request Body:
    {
        "party": "Drax",              // Party name search
        "type": "BM Unit",            // BSC Party, BM Unit, TEC Project
        "role": "VLP",                // CUSC/BSC role
        "bmu": "E_FARNB-1",           // Specific BMU ID
        "organization": "Flexgen",    // Organization name
        "fuel": "Battery",            // Fuel type
        "gsp": "_A",                  // GSP region
        "dno": "EPN",                 // DNO operator
        "voltage": "HV",              // Voltage level
        "cap_min": 10,                // Minimum capacity (MW)
        "cap_max": 100                // Maximum capacity (MW)
    }
    """
    try:
        data = request.get_json() or {}
        
        # Generate cache key from search criteria
        cache_key = hashlib.md5(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        # Check cache
        if cache_key in SEARCH_CACHE:
            cached_result, cache_time = SEARCH_CACHE[cache_key]
            age_seconds = (datetime.now() - cache_time).total_seconds()
            if age_seconds < CACHE_TTL:
                # Cache hit - return cached result with indicator
                cached_result['cached'] = True
                cached_result['cache_age_seconds'] = int(age_seconds)
                return jsonify(cached_result)
            else:
                # Cache expired - remove entry
                del SEARCH_CACHE[cache_key]
        
        # Build search conditions
        conditions = []
        params = []
        
        # Party name search (searches across multiple fields)
        if data.get('party'):
            party_term = f"%{data['party']}%"
            conditions.append("""(
                LOWER(name) LIKE LOWER(@party) OR
                LOWER(identifier) LIKE LOWER(@party) OR
                LOWER(organization) LIKE LOWER(@party) OR
                LOWER(fuel_type) LIKE LOWER(@party) OR
                LOWER(role) LIKE LOWER(@party)
            )""")
            params.append(bigquery.ScalarQueryParameter("party", "STRING", party_term))
        
        # Organization search
        if data.get('organization'):
            org_term = f"%{data['organization']}%"
            conditions.append("LOWER(organization) LIKE LOWER(@organization)")
            params.append(bigquery.ScalarQueryParameter("organization", "STRING", org_term))
        
        # BMU ID search
        if data.get('bmu'):
            bmu_term = f"%{data['bmu']}%"
            conditions.append("LOWER(identifier) LIKE LOWER(@bmu)")
            params.append(bigquery.ScalarQueryParameter("bmu", "STRING", bmu_term))
        
        # Fuel type search
        if data.get('fuel'):
            fuel_term = f"%{data['fuel']}%"
            conditions.append("LOWER(fuel_type) LIKE LOWER(@fuel)")
            params.append(bigquery.ScalarQueryParameter("fuel", "STRING", fuel_term))
        
        # Role search
        if data.get('role'):
            role_term = f"%{data['role']}%"
            conditions.append("LOWER(role) LIKE LOWER(@role)")
            params.append(bigquery.ScalarQueryParameter("role", "STRING", role_term))
        
        # Capacity filters
        if data.get('cap_min'):
            conditions.append("capacity >= @cap_min")
            params.append(bigquery.ScalarQueryParameter("cap_min", "FLOAT64", float(data['cap_min'])))
        
        if data.get('cap_max'):
            conditions.append("capacity <= @cap_max")
            params.append(bigquery.ScalarQueryParameter("cap_max", "FLOAT64", float(data['cap_max'])))
        
        # GSP region filter
        if data.get('gsp'):
            gsp_term = f"%{data['gsp']}%"
            conditions.append("LOWER(extra_info) LIKE LOWER(@gsp)")
            params.append(bigquery.ScalarQueryParameter("gsp", "STRING", gsp_term))
        
        # Build WHERE clause
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Main query - search across generators, parties, and active balancing units
        query = f"""
        WITH generators AS (
            SELECT 
                'BM Unit' as record_type,
                bmu_id as identifier,
                COALESCE(bmu_name, bmu_id, 'Unknown') as name,
                CASE 
                    WHEN LOWER(fuel_type_category) LIKE '%battery%' THEN 'Battery Storage'
                    WHEN LOWER(fuel_type_category) LIKE '%wind%' THEN 'Wind'
                    WHEN LOWER(fuel_type_category) LIKE '%solar%' THEN 'Solar'
                    ELSE fuel_type_category
                END as role,
                lead_party_name as organization,
                CONCAT(COALESCE(fuel_type_category, 'Unknown'), ' - ', COALESCE(CAST(max_capacity_mw AS STRING), 'N/A'), ' MW') as extra_info,
                CAST(max_capacity_mw AS STRING) as capacity,
                fuel_type_category as fuel_type,
                CASE WHEN is_active THEN 'Active' ELSE 'Inactive' END as status,
                'NESO/ELEXON' as source,
                95 as score
            FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators`
            WHERE is_active = TRUE
        ),
        parties AS (
            SELECT 
                'BSC Party' as record_type,
                party_id as identifier,
                party_name as name,
                'BSC Party' as role,
                party_name as organization,
                CONCAT('Party ID: ', party_id) as extra_info,
                CAST(NULL AS STRING) as capacity,
                CAST(NULL AS STRING) as fuel_type,
                'Active' as status,
                'ELEXON BSC' as source,
                90 as score
            FROM `{PROJECT_ID}.{DATASET}.dim_party`
        ),
        active_balancing_units AS (
            -- Find BM units active in balancing (last 30 days) that might not be in ref_bmu_generators
            SELECT DISTINCT
                'BM Unit' as record_type,
                bmUnit as identifier,
                bmUnit as name,
                'Balancing Active' as role,
                'Unknown' as organization,
                CONCAT('Active in balancing - Last seen: ', FORMAT_TIMESTAMP('%Y-%m-%d', MAX(acceptanceTime))) as extra_info,
                CAST(NULL AS STRING) as capacity,
                CAST(NULL AS STRING) as fuel_type,
                'Active' as status,
                'BOALF' as source,
                85 as score
            FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
            WHERE acceptanceTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            AND validation_flag = 'Valid'
            AND bmUnit NOT IN (SELECT bmu_id FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators` WHERE is_active = TRUE)
            GROUP BY bmUnit
        ),
        all_records AS (
            SELECT * FROM generators
            UNION ALL
            SELECT * FROM parties
            UNION ALL
            SELECT * FROM active_balancing_units
        )
        SELECT 
            record_type,
            identifier,
            name,
            role,
            organization,
            extra_info,
            capacity,
            fuel_type,
            status,
            source,
            score
        FROM all_records
        WHERE {where_clause}
        ORDER BY score DESC, name ASC
        LIMIT 100
        """
        
        # Execute query
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        # Format results
        records = []
        for row in results:
            records.append({
                'type': row.record_type,
                'id': row.identifier,
                'name': row.name,
                'role': row.role or '',
                'organization': row.organization or '',
                'extra': row.extra_info or '',
                'capacity': str(row.capacity) if row.capacity else '',
                'fuel': row.fuel_type or '',
                'status': row.status or '',
                'source': row.source or '',
                'score': row.score
            })
        
        # Build response
        response = {
            'success': True,
            'results': records,
            'count': len(records),
            'timestamp': datetime.now().isoformat(),
            'query_time': f'{query_job.total_bytes_processed / 1024 / 1024:.2f} MB processed',
            'cached': False
        }
        
        # Store in cache
        SEARCH_CACHE[cache_key] = (response, datetime.now())
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/tables', methods=['GET'])
def list_tables():
    """List available BigQuery tables for debugging"""
    try:
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET}")
        table_list = [table.table_id for table in tables]
        return jsonify({
            'success': True,
            'tables': table_list[:20],  # First 20 tables
            'count': len(table_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ FAST SEARCH API - Direct BigQuery
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 Starting server on port {PORT}
📊 BigQuery Project: {PROJECT_ID}
📁 Dataset: {DATASET}

Endpoints:
  GET  /health       - Health check
  POST /search       - Execute search (2-3 second response)
  GET  /tables       - List available tables

⚡ This version queries BigQuery directly - much faster!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
