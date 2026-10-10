# SSIS

> Cập nhật 2026-10-10: **input SSIS 388.338×52 đã chuẩn bị và kiểm chứng**. Chương 1 giữ nguyên TSV 38 cột. Dùng [kế hoạch Chương 2](../../docs/etl/chapter2_ssis_plan.md) cho Fact_Loan + 8 Dim_*; database/package target chưa chạy.

Tái tạo input từ repository root bằng `python -m src.etl.prepare_ssis_input`. Output mặc định `data/staging/chapter2/sba7a_ssis_input.tsv` cùng manifest local, được Git ignore. Script không ghi đè files hiện có; `--output` cho phép chỉ định đường dẫn mới.

Thiết kế mới: Flat File → Data Conversion/Derived Column → Dimensions trước → tám Lookups → Fact → đối soát. [Hướng dẫn prototype](../../docs/archive/olap/03_implementation.md) chỉ tham khảo lịch sử, không dùng schema snowflake đó làm target.
Lưu project `.dtproj`, package `.dtsx`, connection manager và parameters tại đây sau khi dựng trong Visual Studio.
Hiện chưa có project SSIS đã thực thi. Python prototype không thay thế project này.
