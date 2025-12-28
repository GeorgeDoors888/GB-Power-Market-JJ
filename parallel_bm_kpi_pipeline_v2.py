#!/usr/bin/env python3
"""
BM KPI Pipeline v2 - Full Specification Implementation
Implements all 19 KPIs from bm_kpi_definitions.md:
- 7 Market KPIs (KPI_MKT_001-007)
- 8 BMU KPIs (KPI_BMU_001-008)
- 4 Stack KPIs (KPI_STACK_001-004)
- 365-day benchmarking (mean/min/max/p10/p50/p90/stdev/z-score)
- "Today so far" mode (00:00→now)
"""
import os
import sys
import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from alert_utils import send_alert, wrap_with_alerts
import pytz

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
CLIENT = bigquery.Client(project="inner-cinema-476211-u9", location="US")
UK_TZ = pytz.timezone("Europe/London")

# =============================================================================
# DATA FETCHING (BOALF, BOD, BOAV, EBOCF)
# =============================================================================

def fetch_boalf_batch(start_date, end_date):
    """Fetch BOALF (acceptance-level dispatch)"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        bmUnit,
        acceptanceNumber,
        acceptanceTime,
        deemedBidOfferFlag,
        soFlag,
        storFlag,
        rrFlag,
        bidOfferLevelFrom,
        bidOfferLevelTo
    FROM `uk_energy_prod.bmrs_boalf_complete`
    WHERE settlementDate BETWEEN {start_date} AND {end_date}
    """
    return CLIENT.query(query, job_config=bigquery.QueryJobConfig(use_query_cache=True)).to_dataframe()

def fetch_bod_batch(start_date, end_date):
    """Fetch BOD (bid-offer stack)"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        bmUnit,
        pairId,
        bidOfferPairNumber,
        offerPrice,
        bidPrice,
        offerLevelFrom,
        offerLevelTo,
        bidLevelFrom,
        bidLevelTo
    FROM `uk_energy_prod.bmrs_bod`
    WHERE settlementDate BETWEEN {start_date} AND {end_date}
    """
    return CLIENT.query(query, job_config=bigquery.QueryJobConfig(use_query_cache=True)).to_dataframe()

def fetch_boav_batch(start_date, end_date):
    """Fetch BOAV (settlement acceptance volumes)"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        bmUnit,
        acceptanceNumber,
        bidOfferAcceptanceVolume,
        bidOfferAcceptanceNumber
    FROM `uk_energy_prod.bmrs_boav`
    WHERE settlementDate BETWEEN {start_date} AND {end_date}
    """
    return CLIENT.query(query, job_config=bigquery.QueryJobConfig(use_query_cache=True)).to_dataframe()

def fetch_ebocf_batch(start_date, end_date):
    """Fetch EBOCF (indicative BMU cashflows)"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        bmUnit,
        bidOfferCashflow,
        bidOfferNumber
    FROM `uk_energy_prod.bmrs_ebocf`
    WHERE settlementDate BETWEEN {start_date} AND {end_date}
    """
    return CLIENT.query(query, job_config=bigquery.QueryJobConfig(use_query_cache=True)).to_dataframe()

# =============================================================================
# MARKET KPIs (KPI_MKT_001-007)
# =============================================================================

def compute_market_kpis(boalf, bod, boav, ebocf, start_date, end_date):
    """Compute all 7 market-level KPIs"""
    kpis = {
        "start_date": start_date,
        "end_date": end_date,
        "computation_timestamp": datetime.now()
    }
    
    # KPI_MKT_001: Total BM Cashflow (£)
    kpis["total_bm_cashflow"] = ebocf["bidOfferCashflow"].sum() if not ebocf.empty else 0
    
    # KPI_MKT_002: Total Accepted Volume (MWh)
    kpis["total_accepted_mwh"] = boav["bidOfferAcceptanceVolume"].sum() if not boav.empty else 0
    
    # KPI_MKT_003: System Direction (Net MWh) - offers minus bids
    if not ebocf.empty:
        # Positive cashflow = offers (system buying), negative = bids (system selling)
        offer_mwh = boav[ebocf["bidOfferCashflow"] > 0]["bidOfferAcceptanceVolume"].sum()
        bid_mwh = boav[ebocf["bidOfferCashflow"] < 0]["bidOfferAcceptanceVolume"].sum()
        kpis["system_direction_mwh"] = offer_mwh - bid_mwh
    else:
        kpis["system_direction_mwh"] = 0
    
    # KPI_MKT_004: Energy-weighted Price (EWAP) (£/MWh)
    if kpis["total_accepted_mwh"] > 0:
        kpis["ewap_overall"] = kpis["total_bm_cashflow"] / kpis["total_accepted_mwh"]
    else:
        kpis["ewap_overall"] = 0
    
    # KPI_MKT_005: Dispatch Intensity (acceptances/hour)
    hours_elapsed = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).total_seconds() / 3600
    kpis["dispatch_intensity"] = len(boalf) / hours_elapsed if hours_elapsed > 0 else 0
    
    # KPI_MKT_006: Concentration (Top 1 / Top 5 share of £)
    if not ebocf.empty:
        bmu_cashflows = ebocf.groupby("bmUnit")["bidOfferCashflow"].sum().sort_values(ascending=False)
        total_cf = bmu_cashflows.sum()
        kpis["top1_share"] = bmu_cashflows.iloc[0] / total_cf if total_cf > 0 else 0
        kpis["top5_share"] = bmu_cashflows.head(5).sum() / total_cf if total_cf > 0 else 0
    else:
        kpis["top1_share"] = 0
        kpis["top5_share"] = 0
    
    # KPI_MKT_007: Workhorse index (Active SPs/48)
    if not boav.empty:
        active_sps = boav[boav["bidOfferAcceptanceVolume"] > 0]["settlementPeriod"].nunique()
        kpis["workhorse_index"] = active_sps / 48
    else:
        kpis["workhorse_index"] = 0
    
    return kpis

# =============================================================================
# BMU KPIs (KPI_BMU_001-008)
# =============================================================================

def compute_bmu_kpis(bmu_name, boalf, bod, boav, ebocf, start_date, end_date):
    """Compute all 8 BMU-level KPIs for a single BMU"""
    # Filter to this BMU
    bmu_boalf = boalf[boalf["bmUnit"] == bmu_name]
    bmu_boav = boav[boav["bmUnit"] == bmu_name]
    bmu_ebocf = ebocf[ebocf["bmUnit"] == bmu_name]
    
    kpis = {
        "bmu_name": bmu_name,
        "start_date": start_date,
        "end_date": end_date,
        "computation_timestamp": datetime.now()
    }
    
    # KPI_BMU_001: Net BM Revenue (£)
    kpis["net_bm_revenue"] = bmu_ebocf["bidOfferCashflow"].sum() if not bmu_ebocf.empty else 0
    
    # KPI_BMU_002: Discharge Revenue / Charge Revenue
    if not bmu_ebocf.empty:
        kpis["discharge_revenue"] = bmu_ebocf[bmu_ebocf["bidOfferCashflow"] > 0]["bidOfferCashflow"].sum()
        kpis["charge_revenue"] = abs(bmu_ebocf[bmu_ebocf["bidOfferCashflow"] < 0]["bidOfferCashflow"].sum())
    else:
        kpis["discharge_revenue"] = 0
        kpis["charge_revenue"] = 0
    
    # KPI_BMU_003: Volume (MWh) / Net MWh
    if not bmu_boav.empty:
        kpis["offer_mwh"] = bmu_boav[bmu_boav["bidOfferAcceptanceVolume"] > 0]["bidOfferAcceptanceVolume"].sum()
        kpis["bid_mwh"] = abs(bmu_boav[bmu_boav["bidOfferAcceptanceVolume"] < 0]["bidOfferAcceptanceVolume"].sum())
        kpis["net_mwh"] = kpis["offer_mwh"] - kpis["bid_mwh"]
    else:
        kpis["offer_mwh"] = 0
        kpis["bid_mwh"] = 0
        kpis["net_mwh"] = 0
    
    # KPI_BMU_004: £/MWh (EWAP)
    total_mwh = kpis["offer_mwh"] + kpis["bid_mwh"]
    kpis["ewap"] = kpis["net_bm_revenue"] / total_mwh if total_mwh > 0 else 0
    
    # KPI_BMU_005: Active SPs / 48
    if not bmu_boav.empty:
        active_sps = bmu_boav[abs(bmu_boav["bidOfferAcceptanceVolume"]) > 0]["settlementPeriod"].nunique()
        kpis["active_sps"] = active_sps
        kpis["active_sp_ratio"] = active_sps / 48
    else:
        kpis["active_sps"] = 0
        kpis["active_sp_ratio"] = 0
    
    # KPI_BMU_006: Acceptance Count
    kpis["acceptance_count"] = len(bmu_boalf)
    
    # KPI_BMU_007: Granularity (MWh per acceptance)
    kpis["granularity"] = total_mwh / kpis["acceptance_count"] if kpis["acceptance_count"] > 0 else 0
    
    # KPI_BMU_008: Time-of-day profile (morning 06:00-16:00 share)
    if not bmu_boav.empty:
        morning_sps = range(13, 33)  # SP13-32 = 06:00-16:00
        morning_mwh = bmu_boav[bmu_boav["settlementPeriod"].isin(morning_sps)]["bidOfferAcceptanceVolume"].sum()
        kpis["morning_share"] = abs(morning_mwh) / total_mwh if total_mwh > 0 else 0
    else:
        kpis["morning_share"] = 0
    
    return kpis

# =============================================================================
# STACK KPIs (KPI_STACK_001-004)
# =============================================================================

def compute_stack_kpis(bod, start_date, end_date, bmu_name=None):
    """Compute all 4 stack KPIs (market or BMU level)"""
    if bmu_name:
        bod = bod[bod["bmUnit"] == bmu_name]
    
    kpis = {
        "bmu_name": bmu_name or "MARKET",
        "start_date": start_date,
        "end_date": end_date,
        "computation_timestamp": datetime.now()
    }
    
    if bod.empty:
        kpis["stack_depth"] = 0
        kpis["defensive_share"] = 0
        kpis["offered_flex_mw"] = 0
        kpis["indicative_spread"] = 0
        return kpis
    
    # KPI_STACK_001: Stack Depth (pairs per SP)
    pairs_per_sp = bod.groupby(["settlementDate", "settlementPeriod"])["pairId"].nunique().mean()
    kpis["stack_depth"] = pairs_per_sp
    
    # KPI_STACK_002: Defensive Pricing Share (%)
    defensive_threshold = 9999
    defensive_count = len(bod[(abs(bod["offerPrice"]) >= defensive_threshold) | 
                               (abs(bod["bidPrice"]) >= defensive_threshold)])
    kpis["defensive_share"] = defensive_count / len(bod) if len(bod) > 0 else 0
    
    # KPI_STACK_003: Offered Flex MW
    bod["offer_flex"] = abs(bod["offerLevelTo"] - bod["offerLevelFrom"])
    bod["bid_flex"] = abs(bod["bidLevelTo"] - bod["bidLevelFrom"])
    kpis["offered_flex_mw"] = (bod["offer_flex"].sum() + bod["bid_flex"].sum()) / 2
    
    # KPI_STACK_004: Indicative Spread (Offer−Bid)
    non_defensive = bod[(abs(bod["offerPrice"]) < defensive_threshold) & 
                        (abs(bod["bidPrice"]) < defensive_threshold)]
    if not non_defensive.empty:
        kpis["indicative_spread"] = (non_defensive["offerPrice"] - non_defensive["bidPrice"]).median()
    else:
        kpis["indicative_spread"] = 0
    
    return kpis

# =============================================================================
# BENCHMARKING (365-day stats)
# =============================================================================

def compute_365d_benchmarks(table_name, metric_col, start_date):
    """Compute 365-day benchmarks: mean/min/max/p10/p50/p90/stdev"""
    end_date_365 = (pd.to_datetime(start_date) - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date_365 = (pd.to_datetime(end_date_365) - timedelta(days=364)).strftime("%Y-%m-%d")
    
    query = f"""
    SELECT {metric_col}
    FROM `uk_energy_prod.{table_name}`
    WHERE start_date BETWEEN {start_date_365} AND {end_date_365}
    AND {metric_col} IS NOT NULL
    """
    
    df = CLIENT.query(query, job_config=bigquery.QueryJobConfig(use_query_cache=True)).to_dataframe()
    
    if df.empty:
        return {
            "mean": 0, "min": 0, "max": 0,
            "p10": 0, "p50": 0, "p90": 0,
            "stdev": 0, "count": 0
        }
    
    return {
        "mean": df[metric_col].mean(),
        "min": df[metric_col].min(),
        "max": df[metric_col].max(),
        "p10": df[metric_col].quantile(0.1),
        "p50": df[metric_col].quantile(0.5),
        "p90": df[metric_col].quantile(0.9),
        "stdev": df[metric_col].std(),
        "count": len(df)
    }

# =============================================================================
# TODAY SO FAR MODE
# =============================================================================

def get_today_so_far_window():
    """Get start/end for Today so far (00:00 UK time → now)"""
    now_uk = datetime.now(UK_TZ)
    start_uk = now_uk.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_uk.strftime("%Y-%m-%d"), now_uk.strftime("%Y-%m-%d %H:%M:%S")

# =============================================================================
# MAIN PIPELINE
# =============================================================================

@wrap_with_alerts
def process_date_range(start_date, end_date, mode="daily"):
    """Process KPIs for a date range"""
    print(f"Processing {start_date} to {end_date} ({mode} mode)...")
    
    # Fetch all data sources in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            "boalf": executor.submit(fetch_boalf_batch, start_date, end_date),
            "bod": executor.submit(fetch_bod_batch, start_date, end_date),
            "boav": executor.submit(fetch_boav_batch, start_date, end_date),
            "ebocf": executor.submit(fetch_ebocf_batch, start_date, end_date)
        }
        data = {k: f.result() for k, f in futures.items()}
    
    print(f"  Fetched: BOALF={len(data[boalf])}, BOD={len(data[bod])}, " +
          f"BOAV={len(data[boav])}, EBOCF={len(data[ebocf])}")
    
    # Compute market KPIs
    market_kpis = compute_market_kpis(
        data["boalf"], data["bod"], data["boav"], data["ebocf"],
        start_date, end_date
    )
    
    # Compute stack KPIs (market level)
    stack_kpis = compute_stack_kpis(data["bod"], start_date, end_date)
    
    # Compute BMU KPIs for top BMUs
    top_bmus = data["ebocf"].groupby("bmUnit")["bidOfferCashflow"].sum().nlargest(20).index.tolist()
    
    bmu_kpis_list = []
    for bmu in top_bmus:
        bmu_kpi = compute_bmu_kpis(
            bmu, data["boalf"], data["bod"], data["boav"], data["ebocf"],
            start_date, end_date
        )
        bmu_kpis_list.append(bmu_kpi)
    
    # Save to BigQuery
    save_kpis_to_bigquery(market_kpis, stack_kpis, bmu_kpis_list)
    
    print(f"✅ Completed {start_date} to {end_date}")
    return market_kpis, stack_kpis, bmu_kpis_list

def save_kpis_to_bigquery(market_kpis, stack_kpis, bmu_kpis_list):
    """Save all KPIs to BigQuery tables"""
    # Market KPIs
    df_market = pd.DataFrame([market_kpis])
    CLIENT.load_table_from_dataframe(
        df_market, "uk_energy_prod.bm_market_kpis",
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    )
    
    # Stack KPIs
    df_stack = pd.DataFrame([stack_kpis])
    CLIENT.load_table_from_dataframe(
        df_stack, "uk_energy_prod.bm_stack_kpis",
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    )
    
    # BMU KPIs
    if bmu_kpis_list:
        df_bmu = pd.DataFrame(bmu_kpis_list)
        CLIENT.load_table_from_dataframe(
            df_bmu, "uk_energy_prod.bm_bmu_kpis",
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        )

@wrap_with_alerts
def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "today":
        # Today so far mode
        start_date, end_time = get_today_so_far_window()
        print(f"🔵 TODAY SO FAR MODE: {start_date} 00:00 → {end_time}")
        process_date_range(start_date, datetime.now().strftime("%Y-%m-%d"), mode="today")
    else:
        # Historical backfill mode (last 90 days in 7-day batches)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        print(f"🔵 BACKFILL MODE: {start_str} to {end_str}")
        
        date_ranges = []
        current = start_date
        while current < end_date:
            batch_end = min(current + timedelta(days=7), end_date)
            date_ranges.append((current.strftime("%Y-%m-%d"), batch_end.strftime("%Y-%m-%d")))
            current = batch_end + timedelta(days=1)
        
        # Process in parallel (28 workers)
        with ThreadPoolExecutor(max_workers=28) as executor:
            futures = [executor.submit(process_date_range, start, end) 
                      for start, end in date_ranges]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    send_alert(f"Batch failed: {e}", level="ERROR")

if __name__ == "__main__":
    main()
