# Database bàn giao

> Cập nhật 2026-10-10: [model và field contract](../docs/dimensional_model/candidate_schema.md) và DBML đã thống nhất DECIMAL(18,3), TermBandKey BIGINT theo report. Physical schema Fact_Loan chưa tạo; triển khai tiếp theo [kế hoạch Chương 2](../docs/etl/chapter2_ssis_plan.md). SQL 01/02 giữ nguyên là prototype.

> **PREVIOUS PROTOTYPE DDL:** `sql/01_warehouse.sql` và `sql/02_validation.sql` áp dụng cho snowflake cũ, không tạo [candidate schema hiện hành](../docs/dimensional_model/candidate_schema.md). Chưa có database/cube candidate được triển khai.

Chưa tạo MDF/LDF. DDL: `sql/01_warehouse.sql`; đối soát: `sql/02_validation.sql`.
Hoàn thiện database trên SQL Server rồi xuất theo [checklist](../docs/archive/other/07_delivery.md).
