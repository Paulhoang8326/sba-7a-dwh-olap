# Kiểm chứng ngày 2026-09-23

## Đã chạy

- `python -m src.main`: toàn bộ 388.338 dòng, sinh 9 bảng, quality log, mart và mining input.
- `python -m unittest discover -s tests -v`: 3 tests PASS. Kiểm tra số dòng/khóa duy nhất, FK fact và snowflake, date roles, đối soát tổng nguồn–fact–mart, count outcome; fixture kiểm tra thiếu lãi suất/ngày, trùng dòng, county trùng tên khác bang, sector gộp.
- `python -m src.mining`: chạy Dummy, Logistic Regression, Decision Tree; chọn Tree theo validation; kết quả thực nghiệm trong `mining_baseline.json`.
- `git diff --check`: không có lỗi whitespace; Git cảnh báo chuyển LF/CRLF do cấu hình Windows.

Runtime: dùng Python bundled của Codex cho profiling, môi trường `.venv` cục bộ kế thừa các thư viện phân tích và cài scikit-learn riêng để chạy mining. Người dùng có thể tạo venv chuẩn mới và cài `requirements.txt`. Không thay đổi thư viện bundled.

## Chưa chạy

DDL SQL Server, SSIS native ETL, SSAS cube/process, MDX, Excel Pivot, Power BI, Looker Studio. SQL Server và SSAS được phát hiện nhưng dịch vụ đang dừng tại lúc khảo sát. Không xem các file hướng dẫn/MDX là bằng chứng những phần này đã hoàn thành.

## Tái lập và dữ liệu

SHA-256 input trong `data_profile.json`; nguồn nguyên vẹn ở `data/raw/foia/`. Output CSV bị Git ignore, cần chạy lại sau clone và lấy đúng source. PDF tham khảo cũng giữ cục bộ, không đẩy tự động. Nội dung đề tài mental health đã được loại khỏi working tree mới và vẫn còn trong lịch sử Git.

Pipeline là full build snapshot, không có hỗ trợ resume/incremental. SQL dùng DECIMAL(24,6) cho monetary values để không mất phần lẻ nguồn; Python/CSV là floating point, đối soát với dung sai số học. Nghiệm thu SQL/SSAS còn phải đối chiếu số tiền tại precision đã chọn.
