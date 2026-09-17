-- ====================================================================
-- Fact: Fact_SocioEconomic
-- Do hat (Grain): 1 dong ung voi 1 quoc gia trong 1 nam
-- ====================================================================

DROP TABLE IF EXISTS dwh.fact_socioeconomic CASCADE;
CREATE TABLE dwh.fact_socioeconomic (
    fact_se_id SERIAL PRIMARY KEY,
    location_key INT NOT NULL REFERENCES dwh.dim_location(location_key),
    time_key INT NOT NULL REFERENCES dwh.dim_time(time_key),
    
    population NUMERIC(18, 2),
    gdp_per_capita_usd NUMERIC(18, 2),
    gdp_total_usd NUMERIC(24, 2),
    
    CONSTRAINT uq_fact_socioeconomic UNIQUE (location_key, time_key)
);

CREATE INDEX idx_fact_se_loc ON dwh.fact_socioeconomic(location_key);
CREATE INDEX idx_fact_se_time ON dwh.fact_socioeconomic(time_key);

COMMENT ON TABLE dwh.fact_socioeconomic IS 'Bang Fact luu tru chi so kinh te xa hoi (GDP, Dan so) theo quoc gia va nam, tranh fan-out duplication';
