-- ====================================================================
-- Dimension: Dim_Time
-- ====================================================================

DROP TABLE IF EXISTS dwh.dim_time CASCADE;
CREATE TABLE dwh.dim_time (
    time_key INT PRIMARY KEY,
    year INT NOT NULL UNIQUE,
    period_phase VARCHAR(50)
);

COMMENT ON TABLE dwh.dim_time IS 'Chieu Thoi gian theo tung nam (2013-2023) va giai doan truoc/trong/sau COVID-19';
