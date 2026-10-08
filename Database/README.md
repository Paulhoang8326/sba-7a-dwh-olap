# Database bàn giao

> SQL documentation hiện hành: [model và field contract theo report](../docs/dimensional_model/candidate_schema.md). SQL 01/02 giữ nguyên là prototype; physical schema Fact_Loan chưa có. Precision DECIMAL(18,3), TermBandKey BIGINT trong report còn cần review với DBML, không dùng DBML decimal(19,2) để nạp tiền 3dp.

> **PREVIOUS PROTOTYPE DDL:** `sql/01_warehouse.sql` và `sql/02_validation.sql` áp dụng cho snowflake cũ, không tạo [candidate schema hiện hành](../docs/dimensional_model/candidate_schema.md). Chưa có database/cube candidate được triển khai.

Chưa tạo MDF/LDF. DDL: `sql/01_warehouse.sql`; đối soát: `sql/02_validation.sql`.
Hoàn thiện database trên SQL Server rồi xuất theo [checklist](../docs/archive/other/07_delivery.md).
