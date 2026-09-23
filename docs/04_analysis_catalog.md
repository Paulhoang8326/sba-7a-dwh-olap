# 15 câu manual và 5 Excel Pivot

Tất cả câu hỏi mô tả bản snapshot 2026-06-30. Measure Count là dòng công bố. Không gọi rate trên resolved loans là rate toàn danh mục. Cùng câu hỏi có thể kiểm chứng bằng manual và MDX nhưng phải lưu bằng chứng thực hiện hai cách riêng biệt.

## Manual trong cube browser/SSMS

Nếu phiên bản SSDT Browser không có đủ pivot UI, dùng SSMS MDX Query Designer ở chế độ đồ họa cho drag/drop/filter. Các thao tác Top N, sort, calculated measures dùng UI được hỗ trợ; chụp điều kiện đã cấu hình. MDX Query # tương ứng nằm trong `Source/SSAS/15_queries.mdx`.

| # | Câu hỏi nghiệp vụ | Thao tác thực hiện và tiêu chí kiểm tra |
|---|---|---|
| 01 | Quy mô vốn phê duyệt/bảo lãnh theo FY thay đổi thế nào? | Rows Fiscal Year; Measures Count/Gross/Guaranteed; roll-up tới All rồi mở từng năm; tổng All bằng SQL |
| 02 | Quý nào năm dương lịch 2024 có nhiều vốn? | Calendar hierarchy → 2024 → expand Quarter; drill-down, tổng quý bằng năm |
| 03 | Phân bổ vốn theo bang/lãnh thổ trong FY2024? | Rows State; filter FY2024; Count/Gross; slice |
| 04 | Ngành 72 ở CA/TX trong FY2023–2024 khác nhau thế nào? | State và FY trên rows; chọn CA, TX, FY2023, FY2024; Sector=72; dice |
| 05 | Cơ cấu ngành theo từng FY? | Sector rows, FY columns, Gross; đổi chỗ rows/columns để pivot; tổng không đổi |
| 06 | 10 lender hiện tại có vốn FY2024 lớn nhất? | FY2024, Lender rows, Top 10 Gross desc; giữ key để phân biệt tên trùng |
| 07 | Bang nào có tỷ lệ CHGOFF trên resolved >10%, đủ 100 hồ sơ? | State rows; Resolved Count và Rate; lọc cả hai điều kiện, không chỉ rate |
| 08 | Trong CA, county nào nhận vốn nhiều? | Geography expand CA → County, Gross/Jobs; drill-down snowflake |
| 09 | Tăng trưởng vốn YoY FY2021–2025? | Tạo calculated measure theo công thức Q09; Fiscal Year rows; loại FY2026 khỏi so sánh năm đầy đủ |
| 10 | Vốn lũy kế từng tháng năm dương lịch 2025? | Calendar 2025 → Month; calculated Calendar YTD; tháng 12 bằng tổng năm |
| 11 | Tỷ trọng mỗi bang trong tổng FY2024? | FY2024; State rows; calculated State Share theo Q11; tổng share ~100% |
| 12 | Lãi suất ban đầu theo method và fixed/variable? | Processing Method × Rate Type; Weighted Initial Rate/Average Loan, sort Gross desc |
| 13 | Hồ sơ tuổi/loại hình doanh nghiệp gắn với việc làm và kỳ hạn thế nào? | Business Age × Type; Jobs/Approval Per Job/Average Term; ẩn cell không có Count |
| 14 | Lender nào có thời gian giải ngân bình quân thấp nhất? | Lender rows, Average Disbursement Days; filter Observed Count>=100; Bottom 10 |
| 15 | Kiểm tra các bản ghi đóng góp vào ô CA/FY2024? | Chọn ô Gross, Drillthrough action/Show Details; tối đa 100, truy vết SourceRowNumber |

Câu 09–11 cần thêm query-scoped calculated members vào cube nếu muốn thao tác hoàn toàn bằng UI. Giữ tên/công thức tương ứng trong Q09–Q11; không chỉ chạy MDX rồi gắn nhãn manual. Các câu trên bao phủ roll-up, drill-down, slice, dice, pivot, ranking, filtering, time intelligence, calculated measure và drillthrough; cô có thể yêu cầu taxonomy riêng cần đối chiếu khi duyệt đề cương.

## Excel Pivot: 5 truy vấn trên SSAS

Excel → Data → Get Data/From Database → Analysis Services → server → SBA Lending → PivotTable. Lưu connection trong `Source/Excel/SBA_Lending_Pivots.xlsx`. Không tạo bảng tổng hợp CSV rồi gọi là Pivot truy vấn cube. Mỗi sheet có câu hỏi, filters, thời điểm snapshot, nhận xét và ảnh kết quả.

| Sheet | Rows | Columns | Values | Filter / thao tác |
|---|---|---|---|---|
| P01_Portfolio | Fiscal Year | — | Count, Gross, Guaranteed | Status; so sánh đủ năm, ghi FY2026 partial |
| P02_Geography | State → County | Fiscal Year | Gross | Expand CA, slice FY2024; đối soát Q03/Q08 |
| P03_Industry | Sector → NAICS | — | Jobs, Approval Per Job | FY2024; Top 10 ngành theo Gross |
| P04_Outcome | Business Age | Status | Count, Charge Off Amount | PIF/CHGOFF; tỷ lệ lấy cube measure, không average tỷ lệ dòng |
| P05_Lender | Lender | Rate Type | Weighted Initial Rate, Average Disbursement Days | Observed Count>=100; sort và slicer method |

Lưu workbook, đóng/mở lại và Refresh All, kiểm tra kết nối còn dùng được. Phiên bản Excel phải hỗ trợ kết nối Analysis Services. Ảnh chụp bảng không thay thế file Pivot thật.
