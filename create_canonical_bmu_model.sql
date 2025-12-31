-- Canonical BMU Reference Model
-- Merges dim_bmu, bmu_metadata, and bmu_registration_data into single source of truth

CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_canonical` AS

WITH latest_metadata AS (
  SELECT
    nationalGridBmUnit,
    bmUnitId,
    bmUnitType,
    leadPartyName,
    fuelType,
    powerStationType,
    registeredCapacity,
    gspGroup,
    technology,
    effectiveFrom,
    effectiveTo,
    ROW_NUMBER() OVER (PARTITION BY nationalGridBmUnit ORDER BY effectiveFrom DESC) as rn
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata`
),

active_metadata AS (
  SELECT * EXCEPT(rn)
  FROM latest_metadata
  WHERE rn = 1
)

SELECT
  -- Primary identifiers
  COALESCE(d.bm_unit_id, m.nationalGridBmUnit, r.nationalgridbmunit) as bmu_id,
  COALESCE(d.national_grid_bmu_id, m.nationalGridBmUnit, r.nationalgridbmunit) as ng_bmu_id,
  COALESCE(r.elexonbmunit, d.bm_unit_id) as elexon_bmu_id,
  COALESCE(r.eic) as eic_code,

  -- Unit details
  COALESCE(d.bmu_name, r.bmunitname) as bmu_name,
  COALESCE(d.bm_unit_type, m.bmUnitType, r.bmunittype) as bmu_type,

  -- Party information
  COALESCE(d.lead_party_name, m.leadPartyName, r.leadpartyname) as lead_party_name,
  COALESCE(d.lead_party_id, r.leadpartyid) as lead_party_id,

  -- Party classification
  CASE
    WHEN COALESCE(d.lead_party_name, m.leadPartyName, r.leadpartyname) IN
         ('Flexitricity Limited', 'Limejump Energy Limited', 'Kiwi Power Limited',
          'Open Energi Limited', 'Upside Energy Limited', 'Moixa Energy Holdings Limited')
    THEN 'VLP'
    WHEN COALESCE(d.bm_unit_type, m.bmUnitType, r.bmunittype) IN ('G', 'E')
    THEN 'Generator'
    WHEN COALESCE(d.bm_unit_type, m.bmUnitType, r.bmunittype) = 'T'
    THEN 'Interconnector'
    WHEN COALESCE(d.bm_unit_type, m.bmUnitType, r.bmunittype) = 'S'
    THEN 'Supplier'
    ELSE 'Other'
  END as party_classification,

  -- Fuel type hierarchy
  COALESCE(d.fuel_type, m.fuelType, r.fueltype) as fuel_type_raw,
  CASE
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%WIND%' THEN 'Wind'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%SOLAR%' THEN 'Solar'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%BATTER%' THEN 'Battery'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%CCGT%' THEN 'Gas'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%OCGT%' THEN 'Gas'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%GAS%' THEN 'Gas'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%COAL%' THEN 'Coal'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%NUCLEAR%' THEN 'Nuclear'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%HYDRO%' THEN 'Hydro'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%BIOMASS%' THEN 'Biomass'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%INTERCONN%' THEN 'Interconnector'
    WHEN UPPER(COALESCE(d.fuel_type, m.fuelType, r.fueltype)) LIKE '%PUMP%' THEN 'Pumped Storage'
    ELSE 'Other'
  END as fuel_type_category,

  COALESCE(m.technology, d.generation_type) as technology,
  COALESCE(m.powerStationType) as power_station_type,

  -- Capacity
  COALESCE(d.generation_capacity_mw, r.generationcapacity, m.registeredCapacity) as generation_capacity_mw,
  COALESCE(d.demand_capacity_mw, r.demandcapacity) as demand_capacity_mw,
  GREATEST(
    COALESCE(d.generation_capacity_mw, 0),
    COALESCE(r.generationcapacity, 0),
    COALESCE(m.registeredCapacity, 0),
    COALESCE(d.demand_capacity_mw, 0),
    COALESCE(r.demandcapacity, 0)
  ) as max_capacity_mw,

  -- Location
  COALESCE(d.gsp_group, m.gspGroup) as gsp_group,

  -- Flags
  COALESCE(d.fpn_flag, r.fpnflag) as fpn_flag,
  COALESCE(d.production_consumption_flag, r.productionorconsumptionflag) as production_consumption_flag,
  d.is_traditional_generator,

  -- Loss factors
  COALESCE(r.transmissionlossfactor) as transmission_loss_factor,

  -- Import/Export capabilities (from registration)
  r.workingdaycreditassessmentimportcapability as working_day_import_capability,
  r.nonworkingdaycreditassessmentimportcapability as non_working_day_import_capability,
  r.workingdaycreditassessmentexportcapability as working_day_export_capability,
  r.nonworkingdaycreditassessmentexportcapability as non_working_day_export_capability,

  -- Effective dates
  m.effectiveFrom as effective_from,
  m.effectiveTo as effective_to,
  CASE WHEN m.effectiveTo IS NULL THEN TRUE ELSE FALSE END as is_active,

  -- Source flags
  CASE WHEN d.bm_unit_id IS NOT NULL THEN TRUE ELSE FALSE END as in_dim_bmu,
  CASE WHEN m.nationalGridBmUnit IS NOT NULL THEN TRUE ELSE FALSE END as in_metadata,
  CASE WHEN r.nationalgridbmunit IS NOT NULL THEN TRUE ELSE FALSE END as in_registration,

  -- Metadata
  CURRENT_TIMESTAMP() as created_at

FROM `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` d
FULL OUTER JOIN active_metadata m
  ON d.bm_unit_id = m.nationalGridBmUnit
FULL OUTER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` r
  ON COALESCE(d.bm_unit_id, m.nationalGridBmUnit) = r.nationalgridbmunit

WHERE COALESCE(d.bm_unit_id, m.nationalGridBmUnit, r.nationalgridbmunit) IS NOT NULL;

-- Create indexes for common queries
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_active` AS
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_canonical`
WHERE is_active = TRUE;

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators` AS
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_canonical`
WHERE party_classification = 'Generator' AND is_active = TRUE;

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_vlp` AS
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_canonical`
WHERE party_classification = 'VLP' AND is_active = TRUE;

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_batteries` AS
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_canonical`
WHERE fuel_type_category = 'Battery' AND is_active = TRUE;
