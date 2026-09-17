-- ====================================================================
-- Fact: Fact_Mental_Health
-- Do hat (Grain): 1 dong ung voi 1 benh, 1 nhan khau hoc tai 1 quoc gia trong 1 nam
-- ====================================================================

DROP TABLE IF EXISTS dwh.fact_mental_health CASCADE;
CREATE TABLE dwh.fact_mental_health (
    fact_id BIGSERIAL PRIMARY KEY,
    location_key INT NOT NULL REFERENCES dwh.dim_location(location_key),
    time_key INT NOT NULL REFERENCES dwh.dim_time(time_key),
    cause_key INT NOT NULL REFERENCES dwh.dim_cause(cause_key),
    demographic_key INT NOT NULL REFERENCES dwh.dim_demographic(demographic_key),
    
    -- DALYs measures
    dalys_number NUMERIC(18, 4),
    dalys_percent NUMERIC(18, 8),
    dalys_lower NUMERIC(18, 4),
    dalys_upper NUMERIC(18, 4),
    
    -- Prevalence measures
    prevalence_number NUMERIC(18, 4),
    prevalence_percent NUMERIC(18, 8),
    prevalence_lower NUMERIC(18, 4),
    prevalence_upper NUMERIC(18, 4)
);

CREATE INDEX idx_fact_mh_loc ON dwh.fact_mental_health(location_key);
CREATE INDEX idx_fact_mh_time ON dwh.fact_mental_health(time_key);
CREATE INDEX idx_fact_mh_cause ON dwh.fact_mental_health(cause_key);
CREATE INDEX idx_fact_mh_demo ON dwh.fact_mental_health(demographic_key);

COMMENT ON TABLE dwh.fact_mental_health IS 'Bang Fact luu tru cac chi so ve ganh nang benh tat (DALYs va Prevalence) da duoc pivot theo cot';
