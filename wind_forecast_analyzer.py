import os
from datetime import datetime, timedelta

import pandas as pd
from google.cloud import bigquery


def get_gcp_project_id():
    """Gets the GCP project ID from the environment."""
    project_id = os.environ.get("GCP_PROJECT")
    if not project_id:
        import subprocess

        try:
            project_id = (
                subprocess.check_output(
                    ["gcloud", "config", "get-value", "project"], stderr=subprocess.PIPE
                )
                .strip()
                .decode("utf-8")
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "jibber-jabber-knowledge"  # Hardcoded fallback
    return project_id


def analyze_wind_forecast_correlation(client, dataset_id, end_date_str):
    """
    Analyzes the correlation between the wind generation forecast and the actual wind generation.
    """
    print("\\n--- Analyzing Wind Forecast Accuracy (Last 7 Days) ---")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime("%Y-%m-%d")

    query = f"""
    WITH forecast AS (
        -- Get the latest forecast for each settlement period
        SELECT
            TIMESTAMP(startTime) as settlement_time,
            generation as forecast_generation
        FROM
            `{client.project}.{dataset_id}.bmrs_windfor`
        WHERE
            DATE(startTime) BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND publishTime = (
                SELECT MAX(publishTime)
                FROM `{client.project}.{dataset_id}.bmrs_windfor` AS sub
                WHERE sub.startTime = `{client.project}.{dataset_id}.bmrs_windfor`.startTime
            )
    ),
    actual AS (
        -- Get the actual wind generation for each settlement period
        SELECT
            TIMESTAMP(startTime) as settlement_time,
            generation as actual_generation
        FROM
            `{client.project}.{dataset_id}.bmrs_fuelinst`
        WHERE
            DATE(startTime) BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND fuelType = 'WIND'
    )
    -- Join the forecast and actual data
    SELECT
        f.settlement_time,
        f.forecast_generation,
        a.actual_generation
    FROM
        forecast f
    JOIN
        actual a ON f.settlement_time = a.settlement_time
    ORDER BY
        f.settlement_time
    """
    try:
        df = client.query(query).to_dataframe()
        if df.empty:
            print(
                "No data found for wind forecast correlation analysis in the last 7 days."
            )
            return

        # Calculate the correlation
        correlation = df["forecast_generation"].corr(df["actual_generation"])

        # Calculate Mean Absolute Error (MAE)
        mae = (df["forecast_generation"] - df["actual_generation"]).abs().mean()

        print(
            f"\\nCorrelation between Forecast and Actual Wind Generation: {correlation:.4f}"
        )
        print(f"Mean Absolute Error (MAE): {mae:.2f} MW\\n")

        # Interpret the result
        print("Interpretation:")
        if correlation > 0.9:
            print(
                "There is a very strong positive correlation. The forecast is highly accurate."
            )
        elif correlation > 0.7:
            print(
                "There is a strong positive correlation. The forecast is generally reliable."
            )
        else:
            print(
                "There is a moderate or weak correlation. The forecast has limited accuracy."
            )

        print(
            "The MAE shows that, on average, the forecast is off by about "
            f"{int(round(mae, -2))} MW. This gives a measure of the typical forecast error."
        )

    except Exception as e:
        print(f"An error occurred during the wind forecast correlation analysis: {e}")


def main():
    """Main function to run the analysis."""
    project_id = get_gcp_project_id()
    dataset_id = "uk_energy_insights"

    if not project_id:
        print("GCP_PROJECT environment variable not set.")
        return

    print(f"Using project: {project_id}, dataset: {dataset_id}")

    try:
        client = bigquery.Client(project=project_id)
    except Exception as e:
        print(f"Failed to create BigQuery client: {e}")
        print(
            "Please ensure you are authenticated with Google Cloud CLI ('gcloud auth application-default login')"
        )
        return

    # Use yesterday's date for a complete day's data
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    analysis_date_str = yesterday.strftime("%Y-%m-%d")

    print(f"Analyzing data up to {analysis_date_str}")

    analyze_wind_forecast_correlation(client, dataset_id, analysis_date_str)


if __name__ == "__main__":
    main()
