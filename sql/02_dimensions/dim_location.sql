-- ====================================================================
-- Dimension: Dim_Location
-- ====================================================================

DROP TABLE IF EXISTS dwh.dim_location CASCADE;
CREATE TABLE dwh.dim_location (
    location_key SERIAL PRIMARY KEY,
    location_id INT,
    location_name VARCHAR(255) NOT NULL UNIQUE,
    iso3 VARCHAR(10),
    region VARCHAR(150),
    income_group VARCHAR(100)
);

CREATE INDEX idx_dim_location_region ON dwh.dim_location(region);
CREATE INDEX idx_dim_location_income ON dwh.dim_location(income_group);

COMMENT ON TABLE dwh.dim_location IS 'Chieu Khong gian / Dia ly va Phan loai thu nhap cua World Bank';
