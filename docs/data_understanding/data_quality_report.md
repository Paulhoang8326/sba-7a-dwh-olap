# Báo cáo chất lượng dữ liệu

Các hàng là dấu hiệu hoặc điểm cần xác minh trên snapshot 30/06/2026. Không có thao tác làm sạch. Tỷ lệ lấy trên toàn bộ bản ghi; một dòng có thể nằm trong nhiều vấn đề.

| ID | Attribute | Issue | Affected Records | Percentage | Potential Impact | Suggested Treatment |
|---|---|---|---|---|---|---|
| DQ01 | InitialInterestRate | Giá trị thiếu, chưa rõ lý do | 8 | 0.0021 | Giảm mức phủ khi phân tích theo thuộc tính | Xác minh với nguồn và giữ riêng nhóm thiếu |
| DQ02 | FixedorVariableInterestInd | Giá trị thiếu, chưa rõ lý do | 8 | 0.0021 | Giảm mức phủ khi phân tích theo thuộc tính | Xác minh với nguồn và giữ riêng nhóm thiếu |
| DQ03 | BusinessType | Giá trị thiếu, chưa rõ lý do | 34 | 0.0088 | Giảm mức phủ khi phân tích theo thuộc tính | Xác minh với nguồn và giữ riêng nhóm thiếu |
| DQ04 | BusinessAge | Giá trị thiếu, chưa rõ lý do | 186 | 0.0479 | Giảm mức phủ khi phân tích theo thuộc tính | Xác minh với nguồn và giữ riêng nhóm thiếu |
| DQ05 | CongressionalDistrict | Giá trị thiếu, chưa rõ lý do | 24 | 0.0062 | Giảm mức phủ khi phân tích theo thuộc tính | Xác minh với nguồn và giữ riêng nhóm thiếu |
| DQ06 | FirstDisbursementDate | P I F nhưng thiếu ngày giải ngân đầu tiên | 3 | 0.0008 | Không xác định được mốc giải ngân | Xác minh khả năng ngày không được cung cấp |
| DQ07 | TermInMonths | Kỳ hạn bằng 0 | 11 | 0.0028 | Phân tích kỳ hạn bị méo | Kiểm tra quy tắc nghiệp vụ của sản phẩm |
| DQ08 | InitialInterestRate | Lãi suất ban đầu bằng 0 | 87 | 0.0224 | Phân tích lãi suất bị méo | Xác minh lãi suất thật hay mã thiếu |
| DQ09 | ChargeOffDate | CHGOFF nhưng thiếu ngày | 5 | 0.0013 | Thiếu mốc thời gian kết quả | Kiểm tra độ trễ cập nhật nguồn |
| DQ10 | PaidInFullDate | Có ngày PIF nhưng trạng thái không phải P I F | 1 | 0.0003 | Mâu thuẫn trạng thái/ngày | Đối chiếu độ trễ và quy tắc trạng thái |
| DQ11 | LoanStatus | Nhãn P I F khác mã PIF trong workbook | 68201 | 17.5623 | Đối chiếu mã và tổng hợp trạng thái cần mapping có tài liệu | Xác nhận P I F tương ứng PIF theo SBA |
| DQ12 | PaidInFullDate | Ngày trước ApprovalDate | 2 | 0.0005 | Trình tự thời gian bất thường | Đối chiếu hồ sơ và quy tắc thời gian |
| DQ13 | ChargeOffDate | Ngày sau AsOfDate | 22 | 0.0057 | Sự kiện xảy ra sau snapshot | Xác minh cập nhật hoặc ngày nguồn |
| DQ14 | Program | Có khoảng trắng đầu/cuối | 388338 | 100.0 | Tạo nhãn phân loại trùng nghĩa | Đối chiếu dạng gốc trước khi chuẩn hóa |
| DQ15 | All attributes | Bản ghi trùng hoàn toàn (tính cả bản gốc) | 687 | 0.1769 | Đếm dòng có thể cao hơn đếm khoản vay nếu trùng thực | Cần mã khoản vay hoặc đối soát SBA trước khi kết luận |

## Các giới hạn trước giai đoạn kế tiếp

- Chưa có public LoanID đáng tin cậy; không được đồng nhất số dòng với số khoản vay duy nhất.
- Các giá trị trống mang tính điều kiện nghiệp vụ cần phân biệt theo LoanStatus và loại lender; xem `missing_values.csv`.
- FY2026 mới tới 30/06/2026; kết quả của cohort mới chịu thời gian quan sát ngắn.
- Snapshot hiện tại không cho phép suy ra lịch sử thay đổi trạng thái, dư nợ hiện tại, thu hồi hoặc tổn thất ròng.
- Xác minh mapping mã chưa được workbook giải thích trước khi định nghĩa KPI/chuyển đổi.