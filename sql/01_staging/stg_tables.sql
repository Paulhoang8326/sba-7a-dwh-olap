-- ====================================================================
-- Staging Tables DDL
-- ====================================================================

-- 1. Bang Staging cho danh muc quoc gia
DROP TABLE IF EXISTS staging.stg_quocgia;
CREATE TABLE staging.stg_quocgia (
    location_name VARCHAR(255),
    iso3 VARCHAR(10),
    region VARCHAR(255),
    income_group VARCHAR(100)
);

-- 2. Bang Staging cho chi so kinh te xa hoi
DROP TABLE IF EXISTS staging.stg_kinhtexahoi;
CREATE TABLE staging.stg_kinhtexahoi (
    location_name VARCHAR(255),
    iso3 VARCHAR(10),
    year NUMERIC,
    gdp_per_capita_usd NUMERIC,
    population NUMERIC,
    gdp_total_usd NUMERIC
);

-- 3. Bang Staging cho du lieu GBD Mental Health
DROP TABLE IF EXISTS staging.stg_gbd_mental_health;
CREATE TABLE staging.stg_gbd_mental_health (
    population_group_id INT,
    population_group_name VARCHAR(100),
    measure_id INT,
    measure_name VARCHAR(255),
    location_id INT,
    location_name VARCHAR(255),
    sex_id INT,
    sex_name VARCHAR(50),
    age_id INT,
    age_name VARCHAR(100),
    cause_id INT,
    cause_name VARCHAR(255),
    metric_id INT,
    metric_name VARCHAR(50),
    year INT,
    val NUMERIC,
    upper NUMERIC,
    lower NUMERIC
);
