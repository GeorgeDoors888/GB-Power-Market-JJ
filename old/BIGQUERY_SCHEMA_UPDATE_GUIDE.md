# BigQuery Ingestion Guide: Schema Updates

This document outlines the necessary changes for the data ingestion process to align with the new, strongly-typed BigQuery schemas. All tables in the `uk_energy_insights` dataset have been updated.

**Failure to adhere to these new types will cause ingestion pipelines to fail.**

## Summary of Type Changes

The following conversions must be applied to the data **before** it is sent to BigQuery. The ingestion script needs to be modified to perform these transformations.

### Key Data Type Mappings:

*   **Dates:** All columns intended for dates must be formatted as `YYYY-MM-DD` strings and loaded into `DATE` columns.
    *   **Example Columns:** `settlementDate`, `forecastDate`, `measurementDate`
    *   **Action:** Ensure any date parsing in the ingestion script outputs a string in this exact format.

*   **Timestamps:** All columns for specific date-times must be formatted as `YYYY-MM-DD HH:MM:SS` (UTC) and loaded into `TIMESTAMP` columns.
    *   **Example Columns:** `_ingested_utc`, `timeFrom`, `timeTo`, `publishTime`
    *   **Action:** Convert date-time objects or strings into this standard format.

*   **Numeric Values:** Columns containing decimal numbers have been converted from `FLOAT` to `NUMERIC` for precision. Columns with whole numbers have been converted from `INTEGER` to `INT64`.
    *   **Example Columns (NUMERIC):** `price`, `volume`, `generation`, `demand`, `temperature`
    *   **Example Columns (INT64):** `levelFrom`, `levelTo`, `settlementPeriod`
    *   **Action:** Ensure data is sent as a valid number, not a string. The client library will handle the conversion.

*   **Booleans:** Columns representing true/false states are now `BOOL`.
    *   **Example Columns:** `amendmentFlag`, `soFlag`, `storFlag`
    *   **Action:** Convert values like "true"/"false", "Y"/"N", 1/0 into actual boolean `True` or `False` in the ingestion script.

## Action Plan for Ingestion Scripts

1.  **Identify the Ingestion Code:** Locate the script(s) responsible for loading data into the `uk_energy_insights` dataset. This is likely a Python script using the `google-cloud-bigquery` library.

2.  **Review `elexon_column_suggestions.csv`:** This file is the source of truth for the new schema. Use it as a reference for every table and column.

3.  **Implement Pre-processing Logic:** Before the `client.load_table_from_dataframe()` or equivalent function is called, add data transformation steps.

    *   **Use pandas for Transformation:** If the data is in a pandas DataFrame, this is the ideal place to perform the conversions.

    *   **Example pandas Transformations:**
        ```python
        # Example for a 'settlementDate' column
        df['settlementDate'] = pd.to_datetime(df['settlementDate']).dt.strftime('%Y-%m-%d')

        # Example for a 'publishTime' column
        df['publishTime'] = pd.to_datetime(df['publishTime']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Example for a numeric conversion
        df['price'] = pd.to_numeric(df['price'], errors='coerce')

        # Example for a boolean conversion
        df['soFlag'] = df['soFlag'].astype(bool)
        ```

4.  **Test Thoroughly:** Before deploying the updated ingestion script, test it with sample data to ensure all columns are converted to their new target types correctly. Check for errors, especially with `SAFE_CAST` or `errors='coerce'` which might produce `NULL` values if the data is unclean.

By implementing these changes in the ingestion pipeline, you will ensure data integrity and prevent future loading errors.

## REMIT Data Schema

The REMIT data from Elexon IRIS has a more complex structure than most BMRS datasets, including nested fields and arrays. Below are the schema details and recommendations for loading REMIT data into BigQuery:

### Table Structure: `bmrs_remit`

#### Top-Level Fields:

| Field Name            | BigQuery Type | Description                             |
| --------------------- | ------------- | --------------------------------------- |
| `publishTime`         | TIMESTAMP     | When the message was published          |
| `mrid`                | STRING        | Message Reference ID                    |
| `revisionNumber`      | INT64         | Version of the message                  |
| `createdTime`         | TIMESTAMP     | When the message was created            |
| `messageType`         | STRING        | Type of message                         |
| `messageHeading`      | STRING        | Summary heading                         |
| `eventType`           | STRING        | Category of event                       |
| `unavailabilityType`  | STRING        | "Planned" or "Unplanned"                |
| `participantId`       | STRING        | ID of the market participant            |
| `assetId`             | STRING        | Identifier for the affected asset       |
| `assetType`           | STRING        | Type of asset                           |
| `affectedUnit`        | STRING        | Name of the affected unit               |
| `affectedUnitEIC`     | STRING        | Energy Identification Code              |
| `biddingZone`         | STRING        | Market bidding zone                     |
| `fuelType`            | STRING        | Type of fuel used                       |
| `normalCapacity`      | NUMERIC       | Normal operating capacity in MW         |
| `availableCapacity`   | NUMERIC       | Available capacity during the event     |
| `unavailableCapacity` | NUMERIC       | Capacity unavailable during the event   |
| `eventStatus`         | STRING        | Status of the event                     |
| `eventStartTime`      | TIMESTAMP     | Start time of the unavailability        |
| `eventEndTime`        | TIMESTAMP     | Expected end time of the unavailability |
| `cause`               | STRING        | Reason for the unavailability           |
| `relatedInformation`  | STRING        | Additional details                      |
| `_ingested_utc`       | TIMESTAMP     | When the record was ingested            |

#### Nested Fields - `outageProfile` (RECORD ARRAY):

| Field Name  | BigQuery Type | Description                           |
| ----------- | ------------- | ------------------------------------- |
| `startTime` | TIMESTAMP     | Beginning of a period                 |
| `endTime`   | TIMESTAMP     | End of a period                       |
| `capacity`  | NUMERIC       | Available capacity during this period |

### Implementation Notes:

1. The `outageProfile` field should be handled as a RECORD ARRAY in BigQuery:
   ```python
   # When creating the table schema
   from google.cloud import bigquery

   schema = [
       # ... other fields ...
       bigquery.SchemaField("outageProfile", "RECORD", mode="REPEATED", fields=[
           bigquery.SchemaField("startTime", "TIMESTAMP"),
           bigquery.SchemaField("endTime", "TIMESTAMP"),
           bigquery.SchemaField("capacity", "NUMERIC"),
       ]),
   ]
   ```

2. When loading from JSON files, ensure the nested structure is preserved:
   ```python
   # Example using pandas with JSON normalization for nested structures
   import pandas as pd
   from google.cloud import bigquery

   # Load REMIT JSON file
   with open('path/to/remit_file.json', 'r') as f:
       data = json.load(f)

   # Convert to DataFrame
   df = pd.json_normalize(data)

   # Handle date/time fields
   time_fields = ['publishTime', 'createdTime', 'eventStartTime', 'eventEndTime']
   for field in time_fields:
       if field in df.columns:
           df[field] = pd.to_datetime(df[field])

   # Load to BigQuery preserving the nested structure
   client = bigquery.Client()
   job_config = bigquery.LoadJobConfig(schema=schema)

   job = client.load_table_from_json(
       data,
       'project.dataset.bmrs_remit',
       job_config=job_config
   )
   ```

See [REMIT_DATA_DOCUMENTATION.md](/REMIT_DATA_DOCUMENTATION.md) for detailed information about the structure and significance of this data.
