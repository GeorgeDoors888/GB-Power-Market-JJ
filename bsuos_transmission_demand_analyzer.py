#!/usr/bin/env python3
"""
BSUoS Transmission Connected Demand Cost Analyzer
Identifies and analyzes BSUoS costs specifically for transmission connected demand
"""

import logging
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from google.cloud import bigquery

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class BSUoSTransmissionDemandAnalyzer:
    def __init__(
        self, project_id="jibber-jabber-knowledge", dataset_id="uk_energy_insights"
    ):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)

    def get_current_bsuos_tariffs(self):
        """Get current BSUoS tariffs for transmission connected demand"""
        query = f"""
        SELECT
            publication,
            fixed_tariff_title,
            published_date,
            fixed_tariff_start_date,
            fixed_tariff_end_date,
            fixed_tariff___mwh as tariff_pounds_per_mwh
        FROM `{self.project_id}.{self.dataset_id}.neso_neso_portal__bsuos_fixed_tariffs__balancing_services_use_of_system_charges_bsuos_tariffs`
        ORDER BY fixed_tariff_start_date DESC
        """

        try:
            logger.info("🔍 Fetching current BSUoS fixed tariffs...")
            result = self.client.query(query).to_dataframe()

            if not result.empty:
                # Convert date columns
                result["published_date"] = pd.to_datetime(result["published_date"])
                result["fixed_tariff_start_date"] = pd.to_datetime(
                    result["fixed_tariff_start_date"]
                )
                result["fixed_tariff_end_date"] = pd.to_datetime(
                    result["fixed_tariff_end_date"]
                )

                # Find current active tariff
                today = datetime.now().date()
                current_tariffs = result[
                    (result["fixed_tariff_start_date"].dt.date <= today)
                    & (result["fixed_tariff_end_date"].dt.date >= today)
                ]

                return result, current_tariffs
            else:
                logger.warning("No BSUoS tariff data found")
                return pd.DataFrame(), pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching BSUoS tariffs: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def get_monthly_forecasts(self, months=12):
        """Get recent monthly BSUoS forecasts"""
        # Get the most recent forecast tables
        forecast_tables = [
            "neso_neso_portal__bsuos_monthly_forecast_monthly_bsuos_forecast_summary_september_2025",
            "neso_neso_portal__bsuos_monthly_forecast_monthly_bsuos_forecast_summary_august_2025",
            "neso_neso_portal__bsuos_monthly_forecast_monthly_bsuos_forecast_summary_july_2025",
            "neso_neso_portal__bsuos_monthly_forecast_monthly_bsuos_forecast_summary_june_2025",
        ]

        all_forecasts = []

        for table in forecast_tables:
            try:
                query = f"""
                SELECT
                    month,
                    energy_imbalance__m,
                    positive_reserve__m,
                    negative_reserve__m,
                    frequency_control__m,
                    constraints__m,
                    estimated_bsuos_volume__twh,
                    '{table}' as source_table
                FROM `{self.project_id}.{self.dataset_id}.{table}`
                WHERE month IS NOT NULL
                ORDER BY month
                """

                result = self.client.query(query).to_dataframe()
                if not result.empty:
                    all_forecasts.append(result)
                    logger.info(f"✅ Found {len(result)} forecast records in {table}")

            except Exception as e:
                logger.warning(f"Could not access {table}: {str(e)[:100]}...")

        if all_forecasts:
            combined_forecasts = pd.concat(all_forecasts, ignore_index=True)
            # Convert month to datetime
            combined_forecasts["month"] = pd.to_datetime(
                combined_forecasts["month"], format="%d/%m/%Y"
            )
            return combined_forecasts
        else:
            logger.warning("No forecast data found")
            return pd.DataFrame()

    def calculate_transmission_demand_costs(self, demand_mwh_annual=1000000):
        """Calculate BSUoS costs for a transmission connected demand customer"""
        logger.info(
            f"💰 Calculating BSUoS costs for {demand_mwh_annual:,} MWh annual demand"
        )

        # Get current tariffs
        all_tariffs, current_tariffs = self.get_current_bsuos_tariffs()

        results = {
            "annual_demand_mwh": demand_mwh_annual,
            "current_tariff_analysis": {},
            "forecast_analysis": {},
            "cost_breakdown": {},
        }

        if not current_tariffs.empty:
            current_tariff = current_tariffs.iloc[0]
            tariff_rate = current_tariff["tariff_pounds_per_mwh"]

            annual_cost = demand_mwh_annual * tariff_rate
            monthly_cost = annual_cost / 12
            daily_cost = annual_cost / 365

            results["current_tariff_analysis"] = {
                "tariff_title": current_tariff["fixed_tariff_title"],
                "tariff_rate_pounds_per_mwh": tariff_rate,
                "valid_from": current_tariff["fixed_tariff_start_date"].strftime(
                    "%Y-%m-%d"
                ),
                "valid_to": current_tariff["fixed_tariff_end_date"].strftime(
                    "%Y-%m-%d"
                ),
                "annual_cost_pounds": annual_cost,
                "monthly_cost_pounds": monthly_cost,
                "daily_cost_pounds": daily_cost,
                "cost_per_mwh": tariff_rate,
            }

            logger.info(f"📊 Current BSUoS tariff: £{tariff_rate:.2f}/MWh")
            logger.info(
                f"💷 Annual cost for {demand_mwh_annual:,} MWh: £{annual_cost:,.2f}"
            )

        # Get forecast data
        forecasts = self.get_monthly_forecasts()
        if not forecasts.empty:
            # Calculate implied tariff rates from forecasts
            forecasts["total_costs_m"] = (
                forecasts["energy_imbalance__m"].fillna(0)
                + forecasts["positive_reserve__m"].fillna(0)
                + forecasts["negative_reserve__m"].fillna(0)
                + forecasts["frequency_control__m"].fillna(0)
                + forecasts["constraints__m"].fillna(0)
            )

            forecasts["implied_tariff_pounds_per_mwh"] = (
                forecasts["total_costs_m"] * 1000000  # Convert £m to £
            ) / (
                forecasts["estimated_bsuos_volume__twh"] * 1000000
            )  # Convert TWh to MWh

            # Calculate costs for our demand
            forecasts["customer_monthly_cost"] = (
                demand_mwh_annual / 12 * forecasts["implied_tariff_pounds_per_mwh"]
            )

            results["forecast_analysis"] = {
                "forecast_months": len(forecasts),
                "avg_implied_tariff_pounds_per_mwh": forecasts[
                    "implied_tariff_pounds_per_mwh"
                ].mean(),
                "min_tariff": forecasts["implied_tariff_pounds_per_mwh"].min(),
                "max_tariff": forecasts["implied_tariff_pounds_per_mwh"].max(),
                "avg_monthly_cost": forecasts["customer_monthly_cost"].mean(),
                "forecast_detail": forecasts[
                    ["month", "implied_tariff_pounds_per_mwh", "customer_monthly_cost"]
                ].to_dict("records"),
            }

        return results, all_tariffs, forecasts

    def generate_transmission_demand_report(
        self, demand_scenarios=[500000, 1000000, 5000000]
    ):
        """Generate comprehensive BSUoS cost report for transmission connected demand"""
        logger.info("📋 Generating BSUoS Transmission Connected Demand Report...")

        print("🔍 BSUoS COSTS FOR TRANSMISSION CONNECTED DEMAND")
        print("=" * 70)
        print()

        # Current tariff overview
        all_tariffs, current_tariffs = self.get_current_bsuos_tariffs()

        if not current_tariffs.empty:
            print("💰 CURRENT BSUoS FIXED TARIFFS:")
            current = current_tariffs.iloc[0]
            print(f"   • Tariff: {current['fixed_tariff_title']}")
            print(f"   • Rate: £{current['tariff_pounds_per_mwh']:.2f}/MWh")
            print(
                f"   • Valid: {current['fixed_tariff_start_date'].strftime('%Y-%m-%d')} to {current['fixed_tariff_end_date'].strftime('%Y-%m-%d')}"
            )
            print()

        # Historical tariff progression
        if not all_tariffs.empty:
            print("📈 HISTORICAL BSUoS TARIFF PROGRESSION:")
            for _, tariff in all_tariffs.iterrows():
                print(
                    f"   • {tariff['fixed_tariff_title']}: £{tariff['tariff_pounds_per_mwh']:.2f}/MWh "
                    f"({tariff['fixed_tariff_start_date'].strftime('%Y-%m-%d')} to {tariff['fixed_tariff_end_date'].strftime('%Y-%m-%d')})"
                )
            print()

        # Cost analysis for different demand scenarios
        print("💡 COST ANALYSIS FOR TRANSMISSION CONNECTED CUSTOMERS:")
        print()

        for demand_mwh in demand_scenarios:
            results, _, forecasts = self.calculate_transmission_demand_costs(demand_mwh)

            print(f"🏭 Customer with {demand_mwh:,} MWh annual demand:")

            if results["current_tariff_analysis"]:
                current = results["current_tariff_analysis"]
                print(f"   • Annual BSUoS cost: £{current['annual_cost_pounds']:,.2f}")
                print(
                    f"   • Monthly BSUoS cost: £{current['monthly_cost_pounds']:,.2f}"
                )
                print(f"   • Daily BSUoS cost: £{current['daily_cost_pounds']:,.2f}")

            if results["forecast_analysis"]:
                forecast = results["forecast_analysis"]
                print(
                    f"   • Forecast avg monthly: £{forecast['avg_monthly_cost']:,.2f}"
                )
                print(
                    f"   • Forecast tariff range: £{forecast['min_tariff']:.2f} - £{forecast['max_tariff']:.2f}/MWh"
                )

            print()

        # Cost breakdown components
        forecasts = self.get_monthly_forecasts()
        if not forecasts.empty:
            print("📊 BSUoS COST COMPONENT BREAKDOWN (Latest Forecasts):")

            latest_forecast = forecasts.iloc[-1]  # Most recent
            total_cost = (
                latest_forecast["energy_imbalance__m"]
                + latest_forecast["positive_reserve__m"]
                + latest_forecast["negative_reserve__m"]
                + latest_forecast["frequency_control__m"]
                + latest_forecast["constraints__m"]
            )

            components = {
                "Energy Imbalance": latest_forecast["energy_imbalance__m"],
                "Positive Reserve": latest_forecast["positive_reserve__m"],
                "Negative Reserve": latest_forecast["negative_reserve__m"],
                "Frequency Control": latest_forecast["frequency_control__m"],
                "Constraints": latest_forecast["constraints__m"],
            }

            for component, cost in components.items():
                percentage = (cost / total_cost) * 100 if total_cost > 0 else 0
                print(f"   • {component}: £{cost:.1f}m ({percentage:.1f}%)")

            print(f"   • Total Monthly Cost: £{total_cost:.1f}m")
            print(
                f"   • Estimated Volume: {latest_forecast['estimated_bsuos_volume__twh']:.1f} TWh"
            )
            print()

        print("ℹ️  BSUoS TRANSMISSION CONNECTED DEMAND KEY POINTS:")
        print(
            "   • BSUoS charges apply to all transmission connected demand (>100MW typically)"
        )
        print("   • Charged per MWh of electricity consumed")
        print(
            "   • Covers costs of balancing supply and demand on the transmission system"
        )
        print("   • Fixed tariffs set in advance, updated periodically")
        print(
            "   • Major cost components: energy imbalance, reserves, frequency control, constraints"
        )
        print(
            "   • Costs recovered from all transmission users (generators pay negative BSUoS)"
        )


def main():
    """Main execution function"""
    logger.info("🚀 Starting BSUoS Transmission Connected Demand Analysis...")

    analyzer = BSUoSTransmissionDemandAnalyzer()

    # Generate comprehensive report
    analyzer.generate_transmission_demand_report()

    logger.info("✅ BSUoS analysis complete!")


if __name__ == "__main__":
    main()
