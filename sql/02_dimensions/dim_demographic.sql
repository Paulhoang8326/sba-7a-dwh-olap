-- ====================================================================
-- Dimension: Dim_Demographic
-- ====================================================================

DROP TABLE IF EXISTS dwh.dim_demographic CASCADE;
CREATE TABLE dwh.dim_demographic (
    demographic_key SERIAL PRIMARY KEY,
    sex_id INT NOT NULL,
    sex_name VARCHAR(50) NOT NULL,
    age_id INT NOT NULL,
    age_name VARCHAR(100) NOT NULL,
    CONSTRAINT uq_demographic UNIQUE (sex_id, age_id)
);

COMMENT ON TABLE dwh.dim_demographic IS 'Chieu Nhan khau hoc: Gioi tinh (Male, Female) va Nhom tuoi (20-54 years)';
