# SSIS

> Đồng bộ 2026-10-02: report mô tả preprocessing đã hoàn tất; standardized TSV/lookup artifacts chưa có trong checkout. Xem [preprocessing](../../docs/data_understanding/preprocessing_plan.md) và [Open Issues](../../docs/00_current_status.md#open-issues-report-va-implementation) trước khi mapping Fact_Loan + 8 Dim_*. Chưa tạo package trong task này.

> **PREVIOUS PROTOTYPE GUIDANCE — DEPRECATED AS CURRENT:** Link hướng dẫn dưới đây dùng schema snowflake cũ. Chưa có project SSIS/ETL cho [candidate schema](../../docs/dimensional_model/candidate_schema.md). Preprocessing mới có kết quả trong report nhưng artifact chưa có để kiểm trong checkout. Xem [Current Status](../../docs/00_current_status.md).

Thiết kế package, mapping và thứ tự nạp: [hướng dẫn triển khai](../../docs/archive/olap/03_implementation.md).
Lưu project `.dtproj`, package `.dtsx`, connection manager và parameters tại đây sau khi dựng trong Visual Studio.
Hiện chưa có project SSIS đã thực thi. Python prototype không thay thế project này.
