-- ====================================================================
-- Project: Mental Health DWH & OLAP System (IS217)
-- Description: Khoi tao cac Schema cho Data Warehouse
-- ====================================================================

-- 1. Tao cac Schema theo kien truc phan tang
CREATE SCHEMA IF NOT EXISTS staging;
COMMENT ON SCHEMA staging IS 'Tang Staging: Luu tru tam du lieu tho trich xuat tu cac file CSV';

CREATE SCHEMA IF NOT EXISTS dwh;
COMMENT ON SCHEMA dwh IS 'Tang Data Warehouse: Luu tru cac bang Dimension va Fact theo chuan Star Schema / Constellation';

CREATE SCHEMA IF NOT EXISTS marts;
COMMENT ON SCHEMA marts IS 'Tang Data Marts: Luu tru cac View/Bang tong hop phuc vu truc tiep cho OLAP Reporting va Dashboard';
