#!/usr/bin/env python3
"""
FR Revenue Optimiser for BESS
==============================
Optimizes frequency response revenue by choosing between DC, DM, DR per EFA block
based on availability revenue minus degradation cost.

Services:
- DC (Dynamic Containment): £2.82/MW/h average
- DM (Dynamic Moderation): £4.00/MW/h average  
- DR (Dynamic Regulation): £4.45/MW/h average

For 2.5 MW battery:
- DC: £7.05/hour = £169/day = £5,058/month
- DM: £10/hour = £240/day = £7,200/month
- DR: £11.13/hour = £267/day = £8,014/month

Author: George Major
Date: 1 December 2025
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
import os
import datetime as dt

from google.cloud import bigquery
import pandas as pd


@dataclass
class BESSAsset:
    """Battery Energy Storage System asset configuration"""
    asset_id: str
    p_max_mw: float
    e_max_mwh: float
    roundtrip_efficiency: float
    degradation_cost_gbp_per_mwh: float
    fr_utilisation_factor: float
    min_price_threshold_gbp_per_mw_h: float = 0.0


class FRRevenueOptimiser:
    """
    Optimises FR revenue by choosing between DC, DM, DR per EFA block
    for a given BESS asset, based on availability price minus degradation cost.
    
    Key Logic:
    - For each EFA block, calculate net margin for each service
    - Net margin = (availability revenue) - (degradation cost)
    - Pick service with highest positive margin (or IDLE if all negative)
    """

    def __init__(
        self,
        project_id: str = "inner-cinema-476211-u9",
        dataset_id: str = "uk_energy_prod",
        fr_prices_table: str = "fr_clearing_prices",
        asset_table: str = "bess_asset_config",
        schedule_table: Optional[str] = "bess_fr_schedule",
    ):
        self.project_id = project_id
        self.dataset_id = dataset_id
        
        # Set credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
        
        self.client = bigquery.Client(project=project_id, location="US")
        self.fr_prices_table = f"{project_id}.{dataset_id}.{fr_prices_table}"
        self.asset_table = f"{project_id}.{dataset_id}.{asset_table}"
        self.schedule_table = f"{project_id}.{dataset_id}.{schedule_table}" if schedule_table else None
        
        print(f"✅ FR Revenue Optimiser initialized")
        print(f"   Project: {project_id}")
        print(f"   Dataset: {dataset_id}")

    # ------------------------------------------------------------------
    # Helpers to load inputs
    # ------------------------------------------------------------------
    def load_asset(self, asset_id: str) -> BESSAsset:
        """Load BESS asset configuration from BigQuery"""
        query = f"""
        SELECT *
        FROM `{self.asset_table}`
        WHERE asset_id = @asset_id
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("asset_id", "STRING", asset_id)]
        )
        df = self.client.query(query, job_config=job_config).to_dataframe()
        if df.empty:
            raise ValueError(f"No asset found with asset_id={asset_id}")

        row = df.iloc[0]
        return BESSAsset(
            asset_id=row["asset_id"],
            p_max_mw=row["p_max_mw"],
            e_max_mwh=row["e_max_mwh"],
            roundtrip_efficiency=row["roundtrip_efficiency"],
            degradation_cost_gbp_per_mwh=row["degradation_cost_gbp_per_mwh"],
            fr_utilisation_factor=row["fr_utilisation_factor"],
            min_price_threshold_gbp_per_mw_h=row.get("min_price_threshold_gbp_per_mw_h", 0.0),
        )

    def load_fr_prices(
        self,
        start_date: dt.date,
        end_date: dt.date,
    ) -> pd.DataFrame:
        """
        Load FR clearing prices between start_date and end_date (inclusive).
        Expects one row per service per EFA block.
        """
        query = f"""
        SELECT
          efa_date,
          efa_block,
          service,
          clearing_price_gbp_per_mw_h,
          block_start,
          block_end
        FROM `{self.fr_prices_table}`
        WHERE efa_date BETWEEN @start_date AND @end_date
        ORDER BY efa_date, efa_block, service
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        df = self.client.query(query, job_config=job_config).to_dataframe()
        if df.empty:
            raise ValueError(f"No FR price data between {start_date} and {end_date}")
        return df

    # ------------------------------------------------------------------
    # Core optimisation
    # ------------------------------------------------------------------
    def optimise(
        self,
        asset_id: str,
        start_date: dt.date,
        end_date: dt.date,
        write_to_bigquery: bool = False,
    ) -> pd.DataFrame:
        """
        Run optimization for given asset and date range.
        
        Returns DataFrame with optimal service selection per EFA block.
        """
        print(f"\n🔄 Running FR optimization for {asset_id}")
        print(f"   Date range: {start_date} to {end_date}")
        
        asset = self.load_asset(asset_id)
        print(f"   Asset: {asset.p_max_mw} MW / {asset.e_max_mwh} MWh")
        print(f"   Efficiency: {asset.roundtrip_efficiency*100:.0f}%")
        print(f"   Degradation: £{asset.degradation_cost_gbp_per_mwh}/MWh")
        
        prices = self.load_fr_prices(start_date, end_date)
        print(f"   Loaded {len(prices)} price records")

        # Pivot so we have DC/DM/DR columns per efa_date + efa_block
        pivot = (
            prices.pivot_table(
                index=["efa_date", "efa_block", "block_start", "block_end"],
                columns="service",
                values="clearing_price_gbp_per_mw_h",
                aggfunc="max",
            )
            .reset_index()
            .rename_axis(None, axis=1)
        )

        # Ensure DC/DM/DR columns exist even if some are missing
        for col in ["DC", "DM", "DR"]:
            if col not in pivot.columns:
                pivot[col] = None

        results = []

        for _, row in pivot.iterrows():
            efa_date = row["efa_date"]
            efa_block = row["efa_block"]
            block_start = row["block_start"]
            block_end = row["block_end"]

            # Duration in hours (EFA is typically 4 hours)
            block_hours = (block_end - block_start).total_seconds() / 3600.0

            service_candidates = ["DC", "DM", "DR"]
            best_service = "IDLE"
            best_net = 0.0
            best_avail = 0.0
            best_deg = 0.0

            for svc in service_candidates:
                price = row.get(svc)
                if price is None or pd.isna(price):
                    continue

                # Skip if below minimum price threshold
                if price < asset.min_price_threshold_gbp_per_mw_h:
                    continue

                # Availability revenue = MW × £/MW/h × hours
                avail_rev = asset.p_max_mw * price * block_hours

                # Degradation cost - approximate using FR utilisation factor
                # FR causes some cycling but not full charge/discharge
                # Throughput = p_max × hours × utilisation_factor
                throughput_mwh = asset.p_max_mw * block_hours * asset.fr_utilisation_factor
                deg_cost = throughput_mwh * asset.degradation_cost_gbp_per_mwh

                net = avail_rev - deg_cost

                if net > best_net:
                    best_net = net
                    best_service = svc
                    best_avail = avail_rev
                    best_deg = deg_cost

            results.append(
                {
                    "asset_id": asset.asset_id,
                    "efa_date": efa_date,
                    "efa_block": efa_block,
                    "block_start": block_start,
                    "block_end": block_end,
                    "best_service": best_service,
                    "p_mw": asset.p_max_mw if best_service != "IDLE" else 0.0,
                    "availability_revenue_gbp": round(best_avail, 2),
                    "degradation_cost_gbp": round(best_deg, 2),
                    "net_margin_gbp": round(best_net, 2),
                    "dc_price_gbp_per_mw_h": row.get("DC"),
                    "dm_price_gbp_per_mw_h": row.get("DM"),
                    "dr_price_gbp_per_mw_h": row.get("DR"),
                    "created_at": dt.datetime.utcnow(),
                }
            )

        df = pd.DataFrame(results)
        
        # Summary statistics
        print(f"\n📊 Optimization Results:")
        print(f"   Total blocks: {len(df)}")
        print(f"   Service selection:")
        for svc in ["DC", "DM", "DR", "IDLE"]:
            count = len(df[df['best_service'] == svc])
            if count > 0:
                print(f"     {svc}: {count} blocks ({count/len(df)*100:.1f}%)")
        
        total_revenue = df['availability_revenue_gbp'].sum()
        total_deg = df['degradation_cost_gbp'].sum()
        total_net = df['net_margin_gbp'].sum()
        
        print(f"\n💰 Revenue Summary:")
        print(f"   Availability revenue: £{total_revenue:,.2f}")
        print(f"   Degradation cost:     £{total_deg:,.2f}")
        print(f"   Net margin:           £{total_net:,.2f}")

        if write_to_bigquery and self.schedule_table:
            self._write_schedule_to_bigquery(df)

        return df

    # ------------------------------------------------------------------
    def _write_schedule_to_bigquery(self, df: pd.DataFrame):
        """Write optimization results to BigQuery"""
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )
        job = self.client.load_table_from_dataframe(df, self.schedule_table, job_config=job_config)
        job.result()
        print(f"✅ Wrote {len(df)} FR schedule rows to {self.schedule_table}")

    # ------------------------------------------------------------------
    def get_monthly_summary(self, schedule_df: pd.DataFrame) -> pd.DataFrame:
        """Generate monthly revenue summary from schedule"""
        schedule_df['month'] = pd.to_datetime(schedule_df['efa_date']).dt.to_period('M')
        
        summary = schedule_df.groupby('month').agg({
            'availability_revenue_gbp': 'sum',
            'degradation_cost_gbp': 'sum',
            'net_margin_gbp': 'sum',
        }).round(2)
        
        summary.columns = ['Revenue (£)', 'Degradation (£)', 'Net Margin (£)']
        return summary


def main():
    """Example usage"""
    
    # Initialize optimizer
    optimiser = FRRevenueOptimiser(
        project_id="inner-cinema-476211-u9",
        dataset_id="uk_energy_prod"
    )
    
    # Define asset ID and date range
    asset_id = "BESS_2P5MW_5MWH"
    start = dt.date(2025, 1, 1)
    end = dt.date(2025, 1, 31)
    
    # Run optimization
    schedule_df = optimiser.optimise(
        asset_id=asset_id,
        start_date=start,
        end_date=end,
        write_to_bigquery=False,  # Set True to persist to BigQuery
    )
    
    # Show sample results
    print(f"\n📋 Sample Schedule (first 20 blocks):")
    print(schedule_df.head(20).to_string(index=False))
    
    # Monthly summary
    monthly = optimiser.get_monthly_summary(schedule_df)
    print(f"\n📅 Monthly Summary:")
    print(monthly)
    
    # Export to CSV
    output_file = f"fr_schedule_{asset_id}_{start}_{end}.csv"
    schedule_df.to_csv(output_file, index=False)
    print(f"\n✅ Results exported to: {output_file}")


if __name__ == "__main__":
    main()
