# Business Objectives – SBA 7(a) FOIA

## Bối cảnh và căn cứ

Đây là **đề xuất yêu cầu cho đồ án**, chưa phải yêu cầu được SBA xác nhận. Nguồn phân tích là một CSV 7(a), 388.338 dòng × 42 thuộc tính, `ApprovalFY` FY2020–FY2026, `AsOfDate` 30/06/2026. Định nghĩa thuộc tính dựa vào workbook SBA `data/raw/foia/7a_504_foia_data_dictionary.xlsx`, sheet `7(a) Data Dictionary`, và [Data Dictionary](../data_understanding/data_dictionary.md). Số liệu, missing và dấu hiệu chất lượng dựa trên [Data Overview](../data_understanding/data_overview.md), [Data Profiling](../data_understanding/data_profiling_report.md) và [Data Quality Report](../data_understanding/data_quality_report.md).

Tài liệu `docs/01_feasibility.md` cũ nêu 689 dòng trong nhóm trùng/392 dòng dư sau chuẩn hóa; **profiling hiện tại trên chuỗi gốc** nêu 687 dòng/391 dòng dư. Hai cách đếm không tương đương. Tài liệu này dùng số liệu hiện tại và không suy diễn khoản vay duy nhất từ cả hai con số.

## Mục tiêu nghiệp vụ đề xuất

| ID | Nhóm | Business Objective | Giá trị và vấn đề có thể làm rõ | Vai trò sử dụng giả định | Giới hạn dữ liệu |
|---|---|---|---|---|---|
| G01 | Loan Approval | Theo dõi quy mô, nhịp và cơ cấu **vốn được phê duyệt** theo thời gian và đặc điểm hồ sơ. | Quan sát số dòng công bố, tổng `GrossApproval`, quy mô bình quân trên dòng và phân bố khoản phê duyệt; tìm giai đoạn hoặc phân khúc biến động để điều tra. | Nhóm phân tích danh mục; giảng viên/người đánh giá đồ án. | Không có LoanID; `GrossApproval` không phải tiền đã giải ngân. FY2026 chỉ đến 30/06/2026. Khoản `CANCLD` vẫn có thể có giá trị phê duyệt, cần nói rõ phạm vi trạng thái. |
| G02 | SBA Guarantee | Mô tả quy mô và cơ cấu **bảo lãnh khi phê duyệt** của SBA. | So sánh `SBAGuaranteedApproval` với `GrossApproval` theo FY, `ProcessingMethod`, địa lý và quy mô; xem phần vốn phê duyệt không được SBA bảo lãnh. | Nhóm phân tích chương trình, báo cáo quản trị giả định. | Không có giá trị bảo lãnh đã chi trả, dư nợ hoặc tổn thất ròng. Tỷ lệ tổng hợp phải là tỷ số của hai tổng, không bình quân tỷ lệ từng dòng. |
| G03 | Geographic & Industry | Quan sát phân bổ vốn phê duyệt và việc làm **được lender báo cáo** theo địa điểm dự án và NAICS. | Xác định mức tập trung theo `ProjectState`, `ProjectCounty`, `NaicsCode`; so cơ cấu ngành giữa địa phương và thời kỳ. | Nhóm nghiên cứu vùng/ngành; người xây dựng báo cáo đồ án. | `ProjectState` khác nơi người vay và lender. `JobsSupported` là ước lượng tự khai, không phải tác động nhân quả. Nhóm NAICS sector cần quy tắc tách/mapping và phiên bản mã được xác minh. |
| G04 | Loan Portfolio Composition | Mô tả cơ cấu danh mục bản ghi công bố theo lender **hiện được gán**, kỳ hạn và đặc điểm hồ sơ. | Xem mức tập trung theo `LocationID`/`BankName`, `TermInMonths`, `BusinessType`, `BusinessAge`, kiểu lãi suất và tài sản bảo đảm. | Nhóm phân tích danh mục; người thiết kế dashboard học thuật. | `BankName` là lender hiện được gán, không chắc là lender phê duyệt ban đầu. `BusinessAge` có nhãn chưa giải thích đầy đủ; kỳ hạn 0 và lãi suất 0 cần xác minh (DQ07–DQ08). |
| G05 | Loan Status & Outcomes | Mô tả trạng thái và charge-off **đã quan sát tại một snapshot** theo cohort phê duyệt và các phân khúc. | So cơ cấu `LoanStatus`, số dòng `CHGOFF`/`P I F` và `GrossChargeOffAmount` giữa FY, địa lý, ngành; phát hiện chênh lệch cần phân tích thêm. | Nhóm theo dõi kết quả danh mục giả định; người đánh giá bài toán OLAP. | Cohort mới bị quan sát ngắn; đây không phải tỷ lệ vỡ nợ cuối cùng. `GrossChargeOffAmount` là gross, không phải net loss; ngày sự kiện có bất thường DQ09–DQ13. |

Các vai trò trên chỉ mô tả người có thể dùng sản phẩm học thuật. Không xem là nhu cầu đã được SBA khảo sát hoặc phê duyệt.

## Quy tắc diễn giải chung

1. `COUNT(*)` được gọi là **số bản ghi khoản vay được công bố**. 687 dòng trong nhóm trùng hoàn toàn (DQ15) không đủ để xác định khoản vay duy nhất hay để loại bản ghi.
2. `ApprovalFY` là năm tài chính nguồn; `ApprovalDate` có thể dùng lập tháng/quý tài chính theo quy tắc FY bắt đầu tháng 10. FY2026 mới có dữ liệu tới 30/06/2026. So tăng trưởng cả năm chỉ dùng FY đầy đủ; nếu cần FY2026, so cùng kỳ với điều kiện thời gian rõ ràng.
3. `AsOfDate` chỉ có một giá trị. `LoanStatus` là trạng thái tại snapshot, không phải trạng thái lịch sử ở từng `ApprovalFY`. CSV dùng `P I F`, workbook dùng `PIF` (DQ11); phải tài liệu hóa quy tắc tương ứng trước khi chốt KPI.
4. `GrossApproval` và `SBAGuaranteedApproval` là mức **phê duyệt**, không phải dòng tiền giải ngân hay thanh toán bảo lãnh. `FirstDisbursementDate` chỉ là ngày giải ngân đầu tiên, không có giá trị giải ngân.
5. Không có dữ liệu để tính dư nợ hiện tại, lịch sử hoàn trả, thu hồi, tổn thất ròng, xác suất vỡ nợ cuối cùng hoặc tác động nhân quả của SBA.
6. Mọi phép chia cần ghi mẫu số, trạng thái được bao gồm, cách xử lý ô trống và đơn vị phân tích. Các measures trong danh mục câu hỏi là **ứng viên**, chưa phải KPI Catalog chính thức.
