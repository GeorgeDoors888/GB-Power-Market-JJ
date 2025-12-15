from google.cloud import bigquery
import json

def verify_ps_value():
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    # First, let's find the correct timestamp column
    print("Checking table schema...")
    schema_query = """
    SELECT column_name
    FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'publication_dashboard_live'
    """
    try:
        schema_job = client.query(schema_query)
        columns = [row.column_name for row in schema_job]
        print(f"Columns found: {columns}")
        
        # Guess the timestamp column
        ts_col = None
        # Prefer 'startTime' or 'settlementDate' or 'timestamp'
        candidates = ['startTime', 'settlementDate', 'timestamp', 'publishTime', 'created_at']
        
        for cand in candidates:
            if cand in columns:
                ts_col = cand
                break
        
        if not ts_col:
            for col in columns:
                if 'time' in col.lower() or 'date' in col.lower():
                    ts_col = col
                    break
        
        if not ts_col:
            print("Could not identify a timestamp column. Using the first column for ordering if possible.")
            ts_col = columns[0] if columns else None

        if ts_col:
            print(f"Using '{ts_col}' as the time column.")
            query = f"""
            SELECT {ts_col}, generation_mix
            FROM `inner-cinema-476211-u9.uk_energy_prod.publication_dashboard_live`
            ORDER BY {ts_col} DESC
            LIMIT 1
            """
            
            print("Running data query...")
            job = client.query(query)
            rows = list(job)
            
            if not rows:
                print("No data found in table.")
                return

            row = rows[0]
            # Access the timestamp column dynamically
            ts_val = getattr(row, ts_col)
            print(f"Most recent {ts_col}: {ts_val}")
            
            gen_mix = row.generation_mix
            
            data = gen_mix
            if isinstance(gen_mix, str):
                try:
                    data = json.loads(gen_mix)
                except json.JSONDecodeError:
                    print("Failed to parse JSON string")
                    print(gen_mix)
                    return
            
            print(f"Data type: {type(data)}")
            
            # Search for PS
            ps_entry = None
            if isinstance(data, list):
                for item in data:
                    # Handle both dict (JSON) and Row (Struct)
                    fuel = None
                    if isinstance(item, dict):
                        fuel = item.get('fuel')
                    else:
                        # BigQuery Row object
                        fuel = item.get('fuel') if hasattr(item, 'get') else getattr(item, 'fuel', None)
                    
                    if fuel == 'PS':
                        ps_entry = item
                        break
            
            if ps_entry:
                print(f"\nFound PS Entry: {ps_entry}")
                
                # Extract value
                val = None
                if isinstance(ps_entry, dict):
                    val = ps_entry.get('generation') or ps_entry.get('mw')
                else:
                    val = getattr(ps_entry, 'generation', None) or getattr(ps_entry, 'mw', None)
                    
                print(f"Raw Value (MW): {val}")
                
                if val is not None:
                    try:
                        gw = float(val) / 1000.0
                        print(f"Calculated GW: {gw}")
                    except ValueError:
                        print("Could not convert value to float.")
            else:
                print("\n'PS' (Pumped Storage) not found in generation_mix.")
                print("Full content:")
                print(data)
        else:
            print("No columns found in table.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    verify_ps_value()
