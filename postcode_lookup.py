import json
import os
import re

import geopandas as gpd
import pandas as pd
import requests
from google.cloud import bigquery
from shapely.geometry import Point


def get_postcode_data(postcode):
    """
    Fetches the longitude and latitude for a given UK postcode.
    """
    response = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
    if response.status_code == 200:
        data = response.json()["result"]
        return data["longitude"], data["latitude"]
    else:
        return None, None


def extract_outward_code(postcode):
    """
    Extracts the outward code (first part) from a UK postcode.
    """
    # Remove all spaces and take the first part (before the last number)
    cleaned = postcode.replace(" ", "").upper()
    match = re.search(r"^(.*?[A-Z]+)(\d[A-Z]{2}|\d{2}[A-Z]?)$", cleaned)
    if match:
        return match.group(1)
    return cleaned  # Return the full code if we can't parse it correctly


def get_outward_code_mapping(outward_code):
    """
    Retrieves the cached DNO/GSP mapping for a given outward code from BigQuery.
    Returns None if the outward code is not in the cache.
    """
    # Setup BigQuery client
    credentials_path = os.path.expanduser(
        "~/.config/gcloud/application_default_credentials.json"
    )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    client = bigquery.Client(project="jibber-jabber-knowledge")

    # Query for the outward code mapping
    query = f"""
        SELECT outward_code, dno, gsp, is_boundary
        FROM `jibber-jabber-knowledge.uk_energy_insights.postcode_dno_gsp_mapping`
        WHERE outward_code = '{outward_code}'
    """

    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"Error querying BigQuery: {e}")
        return None


def update_outward_code_mapping(outward_code, dno, gsp, is_boundary=True):
    """
    Updates the outward code mapping in BigQuery.
    If the outward code exists, updates its info.
    If not, inserts a new record.
    """
    # Setup BigQuery client
    credentials_path = os.path.expanduser(
        "~/.config/gcloud/application_default_credentials.json"
    )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    client = bigquery.Client(project="jibber-jabber-knowledge")

    # Check if the table exists
    table_id = "jibber-jabber-knowledge.uk_energy_insights.postcode_dno_gsp_mapping"
    try:
        client.get_table(table_id)
    except Exception:
        # Create the table if it doesn't exist
        schema = [
            bigquery.SchemaField("outward_code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("dno", "STRING"),
            bigquery.SchemaField("gsp", "STRING"),
            bigquery.SchemaField("is_boundary", "BOOLEAN"),
            bigquery.SchemaField("last_updated", "TIMESTAMP"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)

    # Prepare the data for insertion/update
    rows_to_insert = [
        {
            "outward_code": outward_code,
            "dno": dno,
            "gsp": gsp,
            "is_boundary": is_boundary,
            "last_updated": bigquery.ScalarQueryParameter(
                None, "TIMESTAMP", "CURRENT_TIMESTAMP"
            ),
        }
    ]

    # Insert or update the data
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"Errors inserting into BigQuery: {errors}")
        return False
    return True


def find_dno_gsp(postcode, gis_path="system_regulatory/gis"):
    """
    Finds the DNO and GSP for a given postcode.

    Uses a two-step approach:
    1. First checks if the outward code (first part of postcode) is firmly within a single DNO/GSP
    2. If near a boundary or unclear, does a detailed lookup with the full postcode
    """
    # Extract the outward code for first-pass check
    outward_code = extract_outward_code(postcode)

    # Check if this outward code is in our cached mapping
    # (We'll implement this cache in BigQuery)
    mapping = get_outward_code_mapping(outward_code)

    if mapping and mapping["is_boundary"] == False:
        # If the outward code is fully within a single DNO and GSP, return that data
        return {
            "postcode": postcode,
            "dno": mapping["dno"],
            "gsp": mapping["gsp"],
            "is_boundary": False,
            "method": "outward_code_lookup",
        }

    # If we're here, either the outward code wasn't in our cache,
    # or it's near a boundary and needs detailed checking
    lon, lat = get_postcode_data(postcode)
    if not lon or not lat:
        return {
            "postcode": postcode,
            "dno": None,
            "gsp": None,
            "error": f"Could not find coordinates for postcode: {postcode}",
        }

    point = Point(lon, lat)

    # Find the DNO
    dno_file = os.path.join(gis_path, "dno_license_areas_20200506_simplified.geojson")
    dno_gdf = gpd.read_file(dno_file)
    dno_gdf = dno_gdf.to_crs(epsg=4326)
    dno = dno_gdf[dno_gdf.contains(point)]

    dno_name = None
    if not dno.empty:
        dno_name = dno.iloc[0]["LongName"]

    # Find the GSP
    gsp_file = os.path.join(gis_path, "GSP_regions_4326_20250102_simplified.geojson")
    gsp_gdf = gpd.read_file(gsp_file)
    gsp = gsp_gdf[gsp_gdf.contains(point)]

    gsp_group = None
    if not gsp.empty:
        gsp_group = gsp.iloc[0]["GSPGroup"]

    # If this is a boundary case, update our cache for this outward code
    if not mapping:
        # Mark this outward code as a boundary case for future lookups
        update_outward_code_mapping(outward_code, dno_name, gsp_group, is_boundary=True)

    return {
        "postcode": postcode,
        "dno": dno_name,
        "gsp": gsp_group,
        "is_boundary": True,
        "method": "detailed_lookup",
    }


def batch_process_postcodes(postcodes):
    """
    Process a batch of postcodes and return their DNO/GSP information.
    This is more efficient for multiple lookups.
    """
    results = []
    for postcode in postcodes:
        result = find_dno_gsp(postcode)
        results.append(result)
    return results


def create_flask_api():
    """
    Creates a Flask API that Google Sheets can call to process postcodes.

    The API has endpoints:
    - /lookup/postcode?postcode=SW1A1AA - Single postcode lookup
    - /lookup/batch - POST endpoint for batch processing
    """
    from flask import Flask, jsonify, request

    app = Flask(__name__)

    @app.route("/lookup/postcode", methods=["GET"])
    def lookup_postcode():
        postcode = request.args.get("postcode")
        if not postcode:
            return jsonify({"error": "No postcode provided"}), 400

        result = find_dno_gsp(postcode)
        return jsonify(result)

    @app.route("/lookup/batch", methods=["POST"])
    def batch_lookup():
        data = request.get_json()
        if not data or "postcodes" not in data:
            return jsonify({"error": "No postcodes provided"}), 400

        postcodes = data["postcodes"]
        results = batch_process_postcodes(postcodes)
        return jsonify({"results": results})

    return app


if __name__ == "__main__":
    import sys

    # If run with --api flag, start the Flask API server
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        app = create_flask_api()
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
        app.run(host="0.0.0.0", port=port)

    # If run with --batch flag, process postcodes from a file
    elif len(sys.argv) > 2 and sys.argv[1] == "--batch":
        input_file = sys.argv[2]
        with open(input_file, "r") as f:
            postcodes = [line.strip() for line in f.readlines()]

        results = batch_process_postcodes(postcodes)

        # Output format can be specified
        output_format = sys.argv[3] if len(sys.argv) > 3 else "json"

        if output_format == "csv":
            import csv

            output_file = sys.argv[4] if len(sys.argv) > 4 else "results.csv"
            with open(output_file, "w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["postcode", "dno", "gsp", "is_boundary", "method"]
                )
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            print(f"Results written to {output_file}")
        else:
            output_file = sys.argv[4] if len(sys.argv) > 4 else "results.json"
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Results written to {output_file}")

    # If run with a single postcode argument, process it directly
    elif len(sys.argv) > 1:
        postcode = sys.argv[1]
        result = find_dno_gsp(postcode)
        print(json.dumps(result, indent=2))

    # Otherwise, show usage information
    else:
        print("Usage:")
        print(
            "  python postcode_lookup.py SW1A1AA                   # Look up a single postcode"
        )
        print(
            "  python postcode_lookup.py --batch postcodes.txt     # Process a batch of postcodes"
        )
        print(
            "  python postcode_lookup.py --api 5000                # Start the API server on port 5000"
        )
