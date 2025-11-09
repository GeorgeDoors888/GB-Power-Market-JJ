CREATE OR REPLACE VIEW `{{PROJECT}}.{{DATASET}}.vw_ic_net_hh` AS
SELECT DATE(settlementDate) d, settlementPeriod sp, SUM(generation) ic_net_mw
FROM `{{PROJECT}}.{{DATASET}}.bmrs_indgen_iris`
WHERE fuelType IN ('IFA','IFA2','NSL','Moyle','BritNed','Eleclink','EWIC','Viking','NEMO')
GROUP BY d, sp;