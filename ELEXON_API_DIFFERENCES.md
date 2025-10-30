# Elexon API Differences and Special Handling

This document outlines the key differences and special handling required for various Elexon datasets discovered during the development of the ingestion script.

## Summary of Key Findings

The Elexon APIs (both the older BMRS and the newer Insights API) are not uniform. Different datasets require different endpoints, parameters, and sometimes entirely different API calls. This document serves as a reference for these variations.

---

## 1. Bid-Offer Data (`BOD`)

-   **API Endpoint:** Uses a special `/stream` endpoint.
-   **URL:** `/datasets/BOD/stream`
-   **Parameters:**
    -   Requires `settlementPeriodFrom` and `settlementPeriodTo` to be included in the request, in addition to the `from` and `to` date/time parameters.
-   **Implementation:** The script was modified to use the `/stream` endpoint and include the settlement period parameters specifically for the `BOD` dataset.

---

## 2. Insights API Datasets

Certain datasets are not available through the standard BMRS API and must be fetched from the Elexon Insights API, which has a different base URL and path structure.

-   **Datasets:**
    -   `DEMAND_FORECAST`
    -   `WIND_SOLAR_GEN`
    -   `SURPLUS_MARGIN`
-   **Endpoint Paths:**
    -   `DEMAND_FORECAST`: `/forecast/demand/total/day-ahead`
    -   `WIND_SOLAR_GEN`: `/generation/actual/per-type/wind-and-solar`
    -   `SURPLUS_MARGIN`: `/forecast/surplus/daily`
-   **Implementation:** The script now has a dedicated function to handle requests to the Insights API for these specific datasets.

---

## 3. Schema Mismatches (`BOALF`, `FREQ`, `FUELINST`)

-   **Issue:** During the initial comprehensive test, these datasets failed to load into BigQuery due to a `BadRequest: Provided Schema does not match Table` error. This indicated that the existing tables in BigQuery had a different schema than the data being ingested.
-   **Resolution:** The existing tables for `BOALF`, `FREQ`, and `FUELINST` were deleted from BigQuery. Upon re-running the ingestion, the script automatically created new tables with the correct schema.

---

## 4. `pyarrow` Data Type Errors (`RURI`)

-   **Issue:** The `RURI` dataset initially failed with a `pyarrow.lib.ArrowInvalid: Could not convert 'None' with type str: tried to convert to double` error. This was caused by `None` values in columns that were expected to be numeric.
-   **Resolution:** The data sanitization step (`_sanitize_for_bq`) was improved to handle `None` values and correctly convert data types before loading into BigQuery, making the process more robust.

---

This documentation captures the main issues and their resolutions, providing a clearer understanding of the specific requirements for different Elexon datasets.
