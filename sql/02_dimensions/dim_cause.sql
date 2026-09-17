-- ====================================================================
-- Dimension: Dim_Cause
-- ====================================================================

DROP TABLE IF EXISTS dwh.dim_cause CASCADE;
CREATE TABLE dwh.dim_cause (
    cause_key SERIAL PRIMARY KEY,
    cause_id INT NOT NULL UNIQUE,
    cause_name VARCHAR(255) NOT NULL,
    cause_category VARCHAR(150),
    is_overall_total BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE dwh.dim_cause IS 'Chieu Benh ly: Danh muc cac roi loan tam ly, phan loai nhom roi loan va co danh dau benh tong hop';
