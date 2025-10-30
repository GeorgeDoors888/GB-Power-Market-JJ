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


def analyze_renewable_correlation(client, dataset_id, end_date_str):
    """
    Analyzes the correlation between renewable generation (wind + solar) and market prices.
    """
    print(
        "\\n--- Analyzing Correlation: Renewable Generation vs. Price (Last 7 Days) ---"
    )
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime("%Y-%m-%d")

    query = f"""
    WITH prices AS (
        -- Select and average the price for each settlement period to handle multiple providers
        SELECT
            settlementDate,
            settlementPeriod,
            AVG(price) as market_price
        FROM
            `{client.project}.{dataset_id}.bmrs_mid`
        WHERE
            settlementDate BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND dataProvider = 'APXMIDP' -- Use a consistent data provider
        GROUP BY
            settlementDate,
            settlementPeriod
    ),
    renewables AS (
        -- Sum the generation from wind and solar for each settlement period
        SELECT
            settlementDate,
            settlementPeriod,
            SUM(generation) as renewable_generation
        FROM
            `{client.project}.{dataset_id}.bmrs_fuelinst`
        WHERE
            settlementDate BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND fuelType IN ('WIND', 'SOLAR')
        GROUP BY
            settlementDate,
            settlementPeriod
    )
    -- Join the two datasets to align price with generation
    SELECT
        p.settlementDate,
        p.settlementPeriod,
        p.market_price,
        r.renewable_generation
    FROM
        prices p
    JOIN
        renewables r ON p.settlementDate = r.settlementDate AND p.settlementPeriod = r.settlementPeriod
    ORDER BY
        p.settlementDate, p.settlementPeriod
    """
    try:
        df = client.query(query).to_dataframe()
        if df.empty:
            print("No data found for correlation analysis in the last 7 days.")
            return

        # Calculate the correlation
        correlation = df["market_price"].corr(df["renewable_generation"])

        print(
            f"\\nCorrelation between Market Price and Renewable Generation: {correlation:.4f}\\n"
        )

        # Interpret the result
        print("Interpretation:")
        if correlation < -0.5:
            print("There is a strong negative correlation.")
            print(
                "This means that as wind and solar generation increases, the market price tends to decrease significantly."
            )
            print(
                "This is the expected outcome in a well-functioning market: high supply of cheap renewable energy drives down prices."
            )
        elif correlation < -0.2:
            print("There is a moderate negative correlation.")
            print(
                "This means that as wind and solar generation increases, the market price tends to decrease."
            )
        elif correlation > 0.2:
            print("There is a moderate positive correlation.")
            print(
                "This suggests other factors might be more influential on price, or that high demand is driving both high prices and the need for all available generation."
            )
        else:
            print("There is a weak or no significant correlation.")
            print(
                "This suggests that over this period, other factors (like demand, conventional generator outages, or interconnector flows) had a more dominant effect on price than renewable output."
            )

    except Exception as e:
        print(f"An error occurred during the correlation analysis: {e}")


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

    analyze_renewable_correlation(client, dataset_id, analysis_date_str)


if __name__ == "__main__":
    main()
