# BigQuery Validation Queries

# Verify row count and column integrity for bmrs_uou2t3yw
declare dataset_name string default "uk_energy_insights";
declare table_name string default "bmrs_uou2t3yw";

select count(*) as row_count, count(column_name) as column_count
from `jibber-jabber-knowledge`.`uk_energy_insights.INFORMATION_SCHEMA.COLUMNS`
where table_schema = dataset_name and table_name = table_name;

# Investigate skipped datasets MILS and MELS
select *
from `jibber-jabber-knowledge.uk_energy_insights.bmrs_mils`
limit 10;

select *
from `jibber-jabber-knowledge.uk_energy_insights.bmrs_mels`
limit 10;
