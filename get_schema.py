from google.cloud import bigquery


def get_table_schema(project_id, dataset_id, table_id):
    """Prints the schema of a BigQuery table."""
    try:
        client = bigquery.Client(project=project_id)
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        table = client.get_table(table_ref)
        print(f"Schema for table {table_ref}:")
        for field in table.schema:
            print(f"- {field.name}: {field.field_type}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    get_table_schema(
        "jibber-jabber-knowledge", "elexon_data_landing_zone", "bmrs_wind_solar_gen"
    )
