CREATE OR REPLACE VIEW `{{PROJECT}}.{{DATASET}}.vw_bod_vwap_hh` AS
SELECT DATE(settlementDate) d, settlementPeriod sp,
       AVG(NULLIF(offerPrice,0)) offer_avg,
       AVG(NULLIF(bidPrice,0))   bid_avg
FROM `{{PROJECT}}.{{DATASET}}.bmrs_bod`
GROUP BY d, sp;