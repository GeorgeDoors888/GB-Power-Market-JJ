#!/usr/bin/env python3
"""
Parallel BM KPI Data Pipeline - Dell R630 (32 cores)
Leverages multiprocessing to maximize throughput for BigQuery operations
Author: George Major
Date: Dec 21, 2025
"""

import os
import sys
import logging
from datetime import datetime, timedelta, date
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import time
from google.cloud import bigquery
import pandas as pd
from typing import List, Dict, Tuple, Optional

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
MAX_WORKERS = 28  # Leave 4 cores for system
BATCH_SIZE = 7    # Days per batch (28 workers × 7 days = 196 days parallel)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/parallel_pipeline_{datetime.now():%Y%m%d_%H%M%S}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'


class ParallelBMKPIPipeline:
    """Parallel data pipeline for BM KPI processing"""

    def __init__(self, max_workers: int = MAX_WORKERS):
        self.max_workers = max_workers
        self.client = bigquery.Client(project=PROJECT_ID, location='US')
        logger.info(f"Initialized with {max_workers} workers (Dell has {cpu_count()} cores)")

    def get_date_ranges(self, start_date: date, end_date: date, batch_days: int = BATCH_SIZE) -> List[Tuple[date, date]]:
        """Split date range into batches for parallel processing"""
        ranges = []
        current = start_date

        while current <= end_date:
            batch_end = min(current + timedelta(days=batch_days - 1), end_date)
            ranges.append((current, batch_end))
            current = batch_end + timedelta(days=1)

        logger.info(f"Split {(end_date - start_date).days + 1} days into {len(ranges)} batches of ~{batch_days} days")
        return ranges

    def process_boalf_batch(self, date_range: Tuple[date, date]) -> Dict:
        """Process BOALF data for a date range (runs in parallel)"""
        start_date, end_date = date_range
        worker_client = bigquery.Client(project=PROJECT_ID, location='US')

        try:
            logger.info(f"[Worker] Processing BOALF {start_date} to {end_date}")

            query = f"""
            SELECT
                DATE(acceptanceTime) as date,
                bmUnit,
                COUNT(*) as acceptance_count,
                SUM(acceptanceVolume) as total_volume,
                AVG(acceptancePrice) as avg_price,
                MIN(acceptancePrice) as min_price,
                MAX(acceptancePrice) as max_price,
                SUM(CASE WHEN acceptanceType = 'OFFER' THEN acceptanceVolume ELSE 0 END) as offer_volume,
                SUM(CASE WHEN acceptanceType = 'BID' THEN acceptanceVolume ELSE 0 END) as bid_volume
            FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
            WHERE DATE(acceptanceTime) BETWEEN '{start_date}' AND '{end_date}'
                AND validation_flag = 'Valid'
            GROUP BY date, bmUnit
            """

            df = worker_client.query(query).to_dataframe()

            result = {
                'date_range': f"{start_date}_{end_date}",
                'rows': len(df),
                'dates': df['date'].nunique() if not df.empty else 0,
                'units': df['bmUnit'].nunique() if not df.empty else 0,
                'total_volume': df['total_volume'].sum() if not df.empty else 0,
                'data': df
            }

            logger.info(f"[Worker] ✅ {start_date}-{end_date}: {result['rows']} rows, {result['units']} units")
            return result

        except Exception as e:
            logger.error(f"[Worker] ❌ Error processing {start_date}-{end_date}: {e}")
            return {'date_range': f"{start_date}_{end_date}", 'error': str(e), 'data': pd.DataFrame()}

    def process_bod_batch(self, date_range: Tuple[date, date]) -> Dict:
        """Process BOD (bid-offer) data for a date range"""
        start_date, end_date = date_range
        worker_client = bigquery.Client(project=PROJECT_ID, location='US')

        try:
            logger.info(f"[Worker] Processing BOD {start_date} to {end_date}")

            query = f"""
            SELECT
                DATE(timeFrom) as date,
                bmUnit,
                COUNT(*) as submission_count,
                AVG(offer) as avg_offer_price,
                AVG(bid) as avg_bid_price,
                COUNT(DISTINCT pairId) as unique_pairs
            FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
            WHERE DATE(timeFrom) BETWEEN '{start_date}' AND '{end_date}'
                AND offer IS NOT NULL
                AND bid IS NOT NULL
            GROUP BY date, bmUnit
            """

            df = worker_client.query(query).to_dataframe()

            result = {
                'date_range': f"{start_date}_{end_date}",
                'rows': len(df),
                'data': df
            }

            logger.info(f"[Worker] ✅ BOD {start_date}-{end_date}: {result['rows']} rows")
            return result

        except Exception as e:
            logger.error(f"[Worker] ❌ Error processing BOD {start_date}-{end_date}: {e}")
            return {'date_range': f"{start_date}_{end_date}", 'error': str(e), 'data': pd.DataFrame()}

    def process_boav_batch(self, date_range: Tuple[date, date]) -> Dict:
        """Process BOAV (BM volumes) data for a date range"""
        start_date, end_date = date_range
        worker_client = bigquery.Client(project=PROJECT_ID, location='US')

        try:
            logger.info(f"[Worker] Processing BOAV {start_date} to {end_date}")

            query = f"""
            SELECT
                CAST(settlementDate AS DATE) as date,
                bmUnit,
                SUM(totalVolumeAccepted) as total_volume,
                COUNT(*) as record_count
            FROM `{PROJECT_ID}.{DATASET}.bmrs_boav`
            WHERE CAST(settlementDate AS DATE) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY date, bmUnit
            """

            df = worker_client.query(query).to_dataframe()

            result = {
                'date_range': f"{start_date}_{end_date}",
                'rows': len(df),
                'data': df
            }

            logger.info(f"[Worker] ✅ BOAV {start_date}-{end_date}: {result['rows']} rows")
            return result

        except Exception as e:
            logger.error(f"[Worker] ❌ Error processing BOAV {start_date}-{end_date}: {e}")
            return {'date_range': f"{start_date}_{end_date}", 'error': str(e), 'data': pd.DataFrame()}

    def merge_results(self, results: List[Dict]) -> pd.DataFrame:
        """Merge results from parallel workers"""
        logger.info(f"Merging {len(results)} result batches...")

        valid_results = [r for r in results if 'error' not in r and not r['data'].empty]

        if not valid_results:
            logger.warning("No valid results to merge!")
            return pd.DataFrame()

        merged_df = pd.concat([r['data'] for r in valid_results], ignore_index=True)

        logger.info(f"✅ Merged into {len(merged_df)} total rows")
        return merged_df

    def run_parallel_boalf(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Run BOALF processing in parallel across all cores"""
        logger.info(f"⚡ Starting parallel BOALF processing: {start_date} to {end_date}")
        logger.info(f"   Using {self.max_workers} workers on {cpu_count()} cores")

        start_time = time.time()
        date_ranges = self.get_date_ranges(start_date, end_date)

        # Use ThreadPoolExecutor for I/O-bound BigQuery operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_boalf_batch, dr): dr for dr in date_ranges}

            results = []
            completed = 0

            for future in as_completed(futures):
                completed += 1
                result = future.result()
                results.append(result)

                if 'error' not in result:
                    logger.info(f"Progress: {completed}/{len(date_ranges)} batches ({completed*100//len(date_ranges)}%)")

        merged_df = self.merge_results(results)
        elapsed = time.time() - start_time

        logger.info(f"✅ BOALF complete: {len(merged_df)} rows in {elapsed:.1f}s ({len(merged_df)/elapsed:.0f} rows/sec)")
        return merged_df

    def run_parallel_bod(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Run BOD processing in parallel"""
        logger.info(f"⚡ Starting parallel BOD processing: {start_date} to {end_date}")

        start_time = time.time()
        date_ranges = self.get_date_ranges(start_date, end_date)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_bod_batch, dr): dr for dr in date_ranges}
            results = [future.result() for future in as_completed(futures)]

        merged_df = self.merge_results(results)
        elapsed = time.time() - start_time

        logger.info(f"✅ BOD complete: {len(merged_df)} rows in {elapsed:.1f}s")
        return merged_df

    def run_parallel_boav(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Run BOAV processing in parallel"""
        logger.info(f"⚡ Starting parallel BOAV processing: {start_date} to {end_date}")

        start_time = time.time()
        date_ranges = self.get_date_ranges(start_date, end_date)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_boav_batch, dr): dr for dr in date_ranges}
            results = [future.result() for future in as_completed(futures)]

        merged_df = self.merge_results(results)
        elapsed = time.time() - start_time

        logger.info(f"✅ BOAV complete: {len(merged_df)} rows in {elapsed:.1f}s")
        return merged_df


    def process_ebocf_batch(self, date_range: Tuple[date, date]) -> Dict:
        """Process EBOCF (indicative cashflows) for a date range"""
        start_date, end_date = date_range
        worker_client = bigquery.Client(project=PROJECT_ID, location='US')

        try:
            logger.info(f"[Worker] Processing EBOCF {start_date} to {end_date}")

            query = f"""
            SELECT
                settlementDate as date,
                                bmUnit,
                SUM(CASE WHEN bidOfferPairCashflows > 0 THEN bidOfferPairCashflows ELSE 0 END) as offer_cashflow,
                SUM(CASE WHEN bidOfferPairCashflows < 0 THEN ABS(bidOfferPairCashflows) ELSE 0 END) as bid_cashflow,
                SUM(bidOfferPairCashflows) as net_cashflow
            FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
            WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY settlementDate, bmUnit
            """

            df = worker_client.query(query).to_dataframe()

            result = {
                'date_range': f"{start_date}_{end_date}",
                'rows': len(df),
                'data': df
            }

            logger.info(f"[Worker] ✅ EBOCF {start_date}-{end_date}: {result['rows']} rows")
            return result

        except Exception as e:
            logger.error(f"[Worker] ❌ Error processing EBOCF {start_date}-{end_date}: {e}")
            return {'date_range': f"{start_date}_{end_date}", 'error': str(e), 'data': pd.DataFrame()}

    def run_parallel_ebocf(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Run EBOCF processing in parallel"""
        logger.info(f"⚡ Starting parallel EBOCF processing: {start_date} to {end_date}")

        start_time = time.time()
        date_ranges = self.get_date_ranges(start_date, end_date)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_ebocf_batch, dr): dr for dr in date_ranges}
            results = [future.result() for future in as_completed(futures)]

        merged_df = self.merge_results(results)
        elapsed = time.time() - start_time

        logger.info(f"✅ EBOCF complete: {len(merged_df)} rows in {elapsed:.1f}s")
        return merged_df

    def generate_bm_kpis(self, boalf_df: pd.DataFrame, bod_df: pd.DataFrame, boav_df: pd.DataFrame, ebocf_df: pd.DataFrame) -> pd.DataFrame:
        """Generate BM KPIs from processed data"""
        logger.info("🔧 Generating BM KPIs from processed data...")

        # Merge datasets (suffixes handle duplicate column names)
        kpi_df = boalf_df.merge(bod_df, on=['date', 'bmUnit'], how='outer', suffixes=('_boalf', '_bod'))
        kpi_df = kpi_df.merge(boav_df, on=['date', 'bmUnit'], how='outer', suffixes=('', '_boav'))

        # Calculate KPIs - using actual column names after merge:
        # total_volume = from BOALF (acceptances)
        # total_volume_boav = from BOAV (all BM volumes)
        # submission_count = from BOD (bid-offer pairs submitted)
        # acceptance_count = from BOALF (acceptances)
        
        kpi_df['acceptance_rate'] = kpi_df['acceptance_count'] / kpi_df['submission_count'].replace(0, pd.NA)
        kpi_df['bid_offer_spread'] = kpi_df['avg_offer_price'] - kpi_df['avg_bid_price']
        
        # Revenue estimate using BOALF volume and price
        kpi_df['revenue_estimate_gbp'] = kpi_df['total_volume'] * kpi_df['avg_price']
        

        # ========== MARKET KPIS (7 new KPIs from spec) ==========
        logger.info("🔧 Computing Market KPIs (7 KPIs)...")
        
        # Group EBOCF and BOAV by date for market-level metrics
        if not ebocf_df.empty:
            ebocf_daily = ebocf_df.groupby('date').agg({
                'net_cashflow': 'sum',
                'offer_cashflow': 'sum',
                'bid_cashflow': 'sum'
            }).reset_index()
        else:
            ebocf_daily = pd.DataFrame()
        
        if not boav_df.empty:
            boav_daily = boav_df.groupby('date').agg({
                'total_volume': 'sum',
            }).reset_index()
        else:
            boav_daily = pd.DataFrame()
        
        market_kpis = []
        
        for date_val in kpi_df['date'].unique():
            ebocf_day = ebocf_df[ebocf_df['date'] == date_val] if not ebocf_df.empty else pd.DataFrame()
            boav_day = boav_df[boav_df['date'] == date_val] if not boav_df.empty else pd.DataFrame()
            boalf_day = boalf_df[boalf_df['date'] == date_val] if not boalf_df.empty else pd.DataFrame()
            
            # KPI_MKT_001: Total BM Cashflow (£)
            total_cashflow = ebocf_day['net_cashflow'].sum() if not ebocf_day.empty else 0
            
            # KPI_MKT_002: Total Accepted Volume (MWh)
            total_mwh = boav_day['total_volume'].sum() if not boav_day.empty else 0
            
            # KPI_MKT_004: EWAP
            ewap = total_cashflow / total_mwh if total_mwh > 0 else 0
            
            # KPI_MKT_005: Dispatch Intensity
            acceptances = len(boalf_day)
            dispatch_intensity = acceptances / 24.0
            
            # KPI_MKT_006: Concentration
            if not ebocf_day.empty:
                bmu_cf = ebocf_day.groupby('bmUnit')['net_cashflow'].sum().sort_values(ascending=False)
                total_cf = bmu_cf.sum()
                top1_share = (bmu_cf.iloc[0] / total_cf * 100) if total_cf > 0 and len(bmu_cf) > 0 else 0
                top5_share = (bmu_cf.head(5).sum() / total_cf * 100) if total_cf > 0 and len(bmu_cf) >= 5 else 0
            else:
                top1_share = 0
                top5_share = 0
            
            market_kpis.append({
                'date': date_val,
                'mkt_total_bm_cashflow_gbp': total_cashflow,
                'mkt_total_accepted_mwh': total_mwh,
                'mkt_ewap_gbp_per_mwh': ewap,
                'mkt_dispatch_intensity_per_hour': dispatch_intensity,
                'mkt_top1_concentration_pct': top1_share,
                'mkt_top5_concentration_pct': top5_share
            })
        
        market_kpis_df = pd.DataFrame(market_kpis)
        kpi_df = kpi_df.merge(market_kpis_df, on='date', how='left')
        logger.info(f"✅ Added 7 Market KPIs to {len(kpi_df)} unit-days")

        # Fill NaN with 0 for numeric columns
        numeric_cols = kpi_df.select_dtypes(include=['float64', 'int64']).columns
        kpi_df[numeric_cols] = kpi_df[numeric_cols].fillna(0)

        logger.info(f"✅ Generated KPIs for {len(kpi_df)} unit-days")
        return kpi_df

    def save_results(self, df: pd.DataFrame, table_name: str):
        """Save results to BigQuery"""
        logger.info(f"💾 Saving {len(df)} rows to {table_name}...")

        table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"

        job_config = bigquery.LoadJobConfig( 
            write_disposition="WRITE_TRUNCATE",
            create_disposition="CREATE_IF_NEEDED"
        )

        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        logger.info(f"✅ Saved to {table_id}")

    def run_full_pipeline(self, lookback_days: int = 90):
        """Run the complete parallel BM KPI pipeline"""
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        logger.info("╔═══════════════════════════════════════════════════════════════╗")
        logger.info("║       Parallel BM KPI Pipeline - Dell R630 (32 cores)        ║")
        logger.info("╚═══════════════════════════════════════════════════════════════╝")
        logger.info(f"Period: {start_date} to {end_date} ({lookback_days} days)")
        logger.info(f"Workers: {self.max_workers} / {cpu_count()} cores available")
        logger.info("")

        total_start = time.time()

        # Step 1: Process BOALF in parallel
        boalf_df = self.run_parallel_boalf(start_date, end_date)

        # Step 2: Process BOD in parallel
        bod_df = self.run_parallel_bod(start_date, end_date)

        # Step 3: Process BOAV in parallel
        boav_df = self.run_parallel_boav(start_date, end_date)

        # Step 3b: Process EBOCF in parallel
        ebocf_df = self.run_parallel_ebocf(start_date, end_date)

        # Step 4: Generate KPIs
        kpi_df = self.generate_bm_kpis(boalf_df, bod_df, boav_df, ebocf_df)

        # Step 5: Save results
        self.save_results(kpi_df, 'bm_kpi_summary')

        total_elapsed = time.time() - total_start

        logger.info("")
        logger.info("═══════════════════════════════════════════════════════════════")
        logger.info(f"✅ PIPELINE COMPLETE in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
        logger.info(f"   BOALF: {len(boalf_df)} rows")
        logger.info(f"   BOD:   {len(bod_df)} rows")
        logger.info(f"   BOAV:  {len(boav_df)} rows")
        logger.info(f"   EBOCF: {len(ebocf_df)} rows")
        logger.info(f"   KPIs:  {len(kpi_df)} rows")
        logger.info(f"   Output: {PROJECT_ID}.{DATASET}.bm_kpi_summary")
        logger.info("═══════════════════════════════════════════════════════════════")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Parallel BM KPI Pipeline for Dell R630')
    parser.add_argument('--days', type=int, default=90, help='Days to process (default: 90)')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f'Max workers (default: {MAX_WORKERS})')
    parser.add_argument('--test', action='store_true', help='Test mode (7 days, 4 workers)')

    args = parser.parse_args()

    if args.test:
        logger.info("🧪 TEST MODE: 7 days, 4 workers")
        args.days = 7
        args.workers = 4

    pipeline = ParallelBMKPIPipeline(max_workers=args.workers)
    pipeline.run_full_pipeline(lookback_days=args.days)


if __name__ == '__main__':
    main()
