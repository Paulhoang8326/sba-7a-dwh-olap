# Đánh giá dataset và đề xuất đề tài

## Đề tài nên chọn

**Xây dựng hệ thống Kho dữ liệu và OLAP hỗ trợ phân tích danh mục tín dụng, bảo lãnh và kết quả khoản vay SBA 7(a) tại Hoa Kỳ giai đoạn FY2020–FY2026.** Ba trục nghiệp vụ: phân bổ vốn; ngành/địa phương/bên cho vay; kết quả khoản vay và việc làm được hỗ trợ. Đây là phân tích học thuật dữ liệu danh mục, không phải mô hình ra quyết định cấp tín dụng thực tế.

## Đối chiếu yêu cầu

| Tiêu chí | Bằng chứng từ dữ liệu cục bộ | Đánh giá |
|---|---|---|
| Có thời gian | ApprovalDate 2019-10-01 đến 2026-06-30; 5 cột ngày | Rất phù hợp cho Year/Quarter/Month/Day, cohort và thời gian giải ngân |
| Lớn | 388.338 dòng, 181.130.871 byte | Đủ thực hành ETL, partition, cube; cô quyết định ngưỡng chấm, không có bảo đảm điểm |
| Cột đa dạng | 42 cột, tiền, ngày, ngân hàng, ngành, địa lý, doanh nghiệp, cờ | Phù hợp |
| Nhiều measures | 3 số tiền gốc, JobsSupported, lãi suất, kỳ hạn; thêm count, duration, ratio | Mạnh hơn dataset chỉ có một giá trị phân loại |
| Snowflake | County → State; Industry → Sector | Chuẩn hóa có ý nghĩa, không tách bảng chỉ để đủ số |
| 7–8 dimension | 8 bảng dimension + 1 fact | Nếu cô muốn 7–8 bảng tổng cộng, có thể gộp Sector vào Industry để còn 8 bảng |
| Nhãn class | LoanStatus: CHGOFF / PIF trên tập đã kết thúc | Có sẵn nhưng phải xử lý censoring và leakage |

FY2020: 42.298; FY2021: 51.856; FY2022: 47.678; FY2023: 57.362; FY2024: 70.242; FY2025: 78.078; FY2026: 40.824 dòng. FY của Mỹ bắt đầu tháng 10 năm trước. FY2026 chỉ đến tháng 6: so sánh FYTD cùng 9 tháng, không kết luận giảm từ tổng năm chưa hoàn tất.

## Những điều quyết định tính đúng của đồ án

1. `LocationID` là mã **lender** theo sheet `7(a) Data Dictionary`, không phải mã loan. Có 2.338 giá trị trên 388.338 dòng. Không dùng làm PK fact.
2. Nguồn không có public LoanID. Grain triển khai: một dòng công bố trong một file snapshot. `LoanRowKey`/`SourceRowNumber` cùng SHA-256 truy vết nguồn. Không khẳng định COUNT là số khoản vay duy nhất đã khử trùng.
3. Có 392 dòng dư nếu `drop_duplicates`, thuộc 689 dòng trong nhóm thuộc tính giống nhau. Giữ nguyên và gắn cờ; không đủ bằng chứng để xóa.
4. Đây là snapshot tại 2026-06-30. Status theo năm phê duyệt nghĩa là **kết quả hiện tại của cohort**, không phải status đã biết vào năm phê duyệt. Nhiều snapshot tương lai sẽ không được append thẳng vào fact này.
5. BankName là ngân hàng **đang được gán khoản vay**. Không gọi là ngân hàng phê duyệt ban đầu; không dùng lender hiện tại để mô hình hóa thông tin tại thời điểm cấp tín dụng.
6. `GrossApproval` là giá trị khoản vay được phê duyệt, không phải doanh thu, dư nợ hiện tại, tiền đã giải ngân hay lợi nhuận. Có cả CANCLD: báo riêng tổng mọi bản ghi và tổng loại khoản hủy.
7. `GrossChargeOffAmount` gồm phần bảo lãnh và không bảo lãnh, không phải tổn thất ròng của SBA. Không có recovery/repayment/cashflow để tính lợi nhuận hoặc LGD thật.
8. `JobsSupported` là việc làm tạo mới + duy trì do lender tự khai, không được SBA kiểm toán. Tổng là tổng báo cáo theo khoản vay, không phải số người duy nhất hay tác động nhân quả.

## Chất lượng và nhãn

| Trạng thái nguồn | Dòng | Xử lý |
|---|---:|---|
| EXEMPT | 242.061 | Thông tin trạng thái thuộc diện miễn công bố; không phải nhãn good |
| P I F | 68.201 | Chuẩn hóa thành PIF; class 0 trong tập đã kết thúc |
| CHGOFF | 6.893 | Class 1 trong tập đã kết thúc |
| CANCLD | 50.104 | Khoản hủy; phân tích riêng, loại khỏi binary outcome |
| COMMIT | 21.079 | Chưa giải ngân; loại khỏi binary outcome |

Tập nhãn ban đầu 75.094 dòng, positive khoảng 9,18%. Đây là tỷ lệ charge-off **trong nhóm PIF+CHGOFF**, không phải xác suất vỡ nợ của cả danh mục.

Thiếu FirstDisbursementDate: 71.186; InitialInterestRate: 8; SoldSecMrktInd: 271.574. Blank ≠ No. Thiếu FranchiseCode không chứng minh chắc chắn doanh nghiệp không thuộc franchise. Mã ZIP/FDIC/NAICS đọc dạng chuỗi để giữ số 0 đầu.

Pipeline còn phát hiện: 87 lãi suất bằng 0; 11 kỳ hạn bằng 0; 22 ngày charge-off nằm ngoài [ApprovalDate, AsOfDate]; 2 ngày paid-in-full ngoài khoảng; 5 CHGOFF thiếu ngày charge-off. Giữ số liệu và quality log, không âm thầm sửa. Duration chỉ dùng ngày hợp lệ. Trước mining theo cửa sổ thời gian phải loại/xử lý các bản ghi ngày bất nhất.

## Phạm vi và tiến độ gợi ý

1. Chốt từ điển, quy tắc và đối soát với cô; xác nhận data mining dùng Python hay bắt buộc SSAS/DMX.
2. Hoàn thiện SQL Server + SSIS từ CSV gốc, chụp control flow/data flow và số dòng qua từng bước.
3. Dựng cube, kiểm tra measures, relationship và unknown date members; chạy 15 manual + 15 MDX + 5 Pivot.
4. Xây 3 báo cáo mỗi công cụ; đối chiếu cùng filter để số liệu khớp.
5. Baseline mining, đánh giá giới hạn, báo cáo và video. Chỉ mở rộng dữ liệu các năm cũ nếu cần tăng thời gian theo dõi outcome; không cần thêm file chỉ để tăng kích thước.

Ưu tiên tính đúng của grain, measures và câu hỏi nghiệp vụ hơn số lượng dashboard hoặc thuật toán.
