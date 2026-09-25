# Yêu cầu phân tích OLAP ứng viên

Tài liệu này mô tả **khả năng phân tích**, chưa thiết kế fact/dimension hay Star Schema. Căn cứ thuộc tính và chất lượng: [Data Dictionary](../data_understanding/data_dictionary.md), [Data Profiling](../data_understanding/data_profiling_report.md), [Data Quality Report](../data_understanding/data_quality_report.md). 24 Business Questions và feasibility chi tiết nằm trong [catalog](business_questions_catalog.md).

## Trục phân tích và hierarchy

| Trục | Thuộc tính nguồn hiện có | Hierarchy/nhóm có thể dùng | Điều kiện và giới hạn |
|---|---|---|---|
| Thời gian phê duyệt | `ApprovalDate`, `ApprovalFY` | FY → quý tài chính → tháng tài chính → ngày; cũng có thể năm dương lịch → quý dương lịch → tháng → ngày | Chỉ FY và ngày có sẵn; quý/tháng tài chính phải dẫn xuất bằng quy tắc FY bắt đầu tháng 10 và đối chiếu `ApprovalFY`. Không đặt quý dương lịch dưới FY. FY2026 có dữ liệu đến 30/06. |
| Snapshot | `AsOfDate` | Một điểm thời gian duy nhất | Không drill-down lịch sử trạng thái; slicer snapshot hiện chỉ có một giá trị. |
| Địa lý dự án | `ProjectState`, `ProjectCounty`, `CongressionalDistrict` | State → county; state → congressional district là nhánh phân tích khác | State/county có sẵn nhưng khóa county phải gồm state + county. Congressional district không mặc nhiên là cấp con của county; ranh giới có thể giao nhau. `CongressionalDistrict` thiếu 24 dòng (DQ05). |
| Địa lý người vay/lender | `BorrState`, `BorrCity`, `BankState`, `BankCity` | State → city nếu xác minh chuẩn tên và khóa | Không gộp ba địa chỉ borrower/bank/project vào cùng một cây địa lý; city có thể trùng tên, thay đổi cách viết. |
| Ngành | `NaicsCode`, `NaicsDescription` | Sector code (2 ký tự đầu, đề xuất) → NAICS 6 chữ số | Sector name và cấu trúc cấp giữa 2–6 chữ số cần mapping NAICS đúng phiên bản từ nguồn ngoài. Chưa có bảng sector chính thức trong CSV; không coi mô tả NAICS là tên sector. |
| Lender hiện tại | `LocationID`, `BankName`, `BankState` | Danh sách lender theo `LocationID`; có thể nhóm theo bank state | `LocationID` là lender ID, không phải LoanID. `BankName` là lender hiện được gán; bank state là thuộc tính địa chỉ, không phải cấp tổ chức đã xác minh. |
| Khoản vay/chương trình | `ProcessingMethod`, `GrossApproval`, `TermInMonths`, `FixedorVariableInterestInd`, `RevolverStatus`, `CollateralInd` | Method; nhóm quy mô vốn; nhóm kỳ hạn; rate/revolver/collateral flag | Nhóm quy mô và kỳ hạn là dẫn xuất cần ngưỡng công bố. Workbook có mã method, CSV có nhãn; Y/N của một số cờ cần xác minh. 11 dòng kỳ hạn 0 (DQ07). |
| Doanh nghiệp | `BusinessType`, `BusinessAge`, `FranchiseCode`, `FranchiseName` | Type/age là phân loại song song; franchise nếu áp dụng | Không có thứ bậc type→age. `BusinessAge` có 186 thiếu và nhãn `Unanswered`; franchise thiếu phần lớn, blank chưa chắc là không thuộc franchise. |
| Kết quả tại snapshot | `LoanStatus`, `PaidInFullDate`, `ChargeOffDate`, `GrossChargeOffAmount` | Status là phân loại; ngày PIF/charge-off có thể lập trục thời gian sự kiện riêng | Không đặt status dưới FY như lịch sử trạng thái. CSV dùng `P I F`, workbook ghi `PIF` (DQ11). DQ09–DQ13 ảnh hưởng ngày sự kiện; `GrossChargeOffAmount` không phải net loss. |

## Measures và thuộc tính dẫn xuất có thể cần

Đây là mô tả phép tính **ứng viên**, chưa chốt định nghĩa KPI hoặc nơi lưu trữ:

| Measure/thuộc tính ứng viên | Thuộc tính nguồn | Điều kiện diễn giải |
|---|---|---|
| Số dòng công bố | Một dòng CSV | `COUNT(*)`; không gọi là số khoản vay duy nhất (DQ15). |
| Tổng vốn phê duyệt, tổng bảo lãnh phê duyệt | `GrossApproval`, `SBAGuaranteedApproval` | Cùng tập lọc/status; không phải giải ngân hay giá trị đã chi trả. |
| Quy mô phê duyệt bình quân trên dòng | `GrossApproval` | `SUM(GrossApproval)/COUNT(*)`; ghi rõ tập trạng thái. |
| Tỷ trọng bảo lãnh | `SBAGuaranteedApproval`, `GrossApproval` | Tỷ số hai tổng, mẫu số > 0; không bình quân tỷ lệ từng dòng. |
| Phần vốn phê duyệt không SBA bảo lãnh | `GrossApproval`, `SBAGuaranteedApproval` | Hiệu hai tổng cùng lát cắt; không phải dư nợ lender. |
| Tỷ trọng state/nhóm trong FY | `GrossApproval`, `ApprovalFY`, `ProjectState` hoặc nhóm | Mẫu số cố định là tổng vốn của cùng FY/phạm vi lọc; không cộng các tỷ lệ. |
| Tăng trưởng FY, cùng kỳ FY | `ApprovalDate`, `ApprovalFY`, `GrossApproval` | So cùng loại cửa sổ thời gian; FY2026 chỉ so cùng kỳ đến 30/06. |
| Fiscal quarter/month | `ApprovalDate`, `ApprovalFY` | Quy tắc FY bắt đầu 01/10, xác nhận với FY nguồn; không trộn quý dương lịch. |
| Nhóm quy mô, nhóm kỳ hạn | `GrossApproval`, `TermInMonths` | Ngưỡng nhóm là quyết định phân tích, không phải thuộc tính SBA có sẵn; giữ kỳ hạn 0 riêng. |
| Sector code | `NaicsCode` | Hai ký tự đầu là dẫn xuất kỹ thuật; tên sector, version và tính hợp lệ cần mapping nguồn ngoài. |
| Count theo status và tỷ trọng outcome quan sát | `LoanStatus`, `ApprovalFY`, `AsOfDate` | Dùng nhãn nguồn hoặc mapping đã xác nhận; công bố mẫu số, tuổi cohort và trạng thái bao gồm. |
| Tổng gross charge-off | `GrossChargeOffAmount`, `LoanStatus` | Không trừ thu hồi; nếu phân tích theo `ChargeOffDate`, xử lý DQ09/DQ13 trước. |
| Việc làm được báo cáo, vốn/việc làm | `JobsSupported`, `GrossApproval` | `JobsSupported` là lender tự khai; tỷ số chỉ khi mẫu số việc làm > 0, không phải hiệu quả nhân quả. |
| Lãi suất ban đầu theo nhóm | `InitialInterestRate`, `FixedorVariableInterestInd`, `ProcessingMethod` | Chốt đơn vị, xử lý 0/thiếu (DQ01–DQ02, DQ08); trung bình có/không trọng số là hai câu hỏi khác nhau. |

## Ma trận thao tác cho từng Business Question

`Roll-up` = gộp theo cấp cao hơn; `Drill-down` = mở cấp chi tiết; `Slice` = lọc một giá trị; `Dice` = lọc nhiều trục; `Pivot` = đổi trục trình bày. Các thao tác ghi dưới đây là ví dụ **có ý nghĩa cho câu hỏi**, không phải yêu cầu mọi biểu đồ thực hiện đủ năm thao tác. Điều kiện feasibility của từng BQ vẫn áp dụng.

| BQ ID | Thao tác OLAP phù hợp | Đường drill/roll hoặc lát cắt minh họa |
|---|---|---|
| BQ01 | Roll-up, drill-down, slice, pivot | Tháng tài chính → quý → FY; slice state; pivot FY × state. |
| BQ02 | Roll-up, dice, pivot | FY × method; gộp method lên toàn danh mục; dice state + FY. |
| BQ03 | Roll-up, slice, pivot | Tháng cùng kỳ → FYTD; slice state; pivot FY × state. |
| BQ04 | Slice, dice, pivot | Nhóm quy mô × `BusinessAge`; slice FY. |
| BQ05 | Drill-down, slice, pivot | FY → tháng tài chính; slice state; pivot tháng × FY. |
| BQ06 | Roll-up, slice, pivot | Method → toàn chương trình; FY × method. |
| BQ07 | Roll-up, drill-down, dice, pivot | Sector → NAICS nếu mapping đã xác minh; FY + state; pivot state × ngành. |
| BQ08 | Roll-up, slice, pivot | Lender → toàn bộ lender hiện tại; slice method; pivot lender × FY. |
| BQ09 | Slice, dice, pivot | Nhóm quy mô × method, lọc FY. |
| BQ10 | Roll-up, drill-down, slice, pivot | State → county; slice FY; pivot state × FY. |
| BQ11 | Roll-up, slice, pivot | State → toàn bộ state trong FY; lọc FY, đổi trục state/FY. |
| BQ12 | Roll-up, drill-down, dice, pivot | Sector → NAICS có mapping; state + FY; pivot ngành × state. |
| BQ13 | Slice, dice, pivot | `BorrState` × `ProjectState`, lọc FY; không coi hai trường là một hierarchy. |
| BQ14 | Roll-up, drill-down, dice, pivot | NAICS → sector có mapping; lọc state + FY. |
| BQ15 | Roll-up, slice, pivot | Lender hiện tại → tổng; FY × lender, Top N trong lát cắt FY. |
| BQ16 | Slice, dice, pivot | Nhóm kỳ hạn × method, lọc FY. |
| BQ17 | Slice, dice, pivot | `BusinessAge` × `BusinessType`, lọc state + FY; không tạo hierarchy giả. |
| BQ18 | Slice, dice, pivot | Rate type × method, lọc nhóm quy mô; không roll-up lãi suất bằng cách cộng. |
| BQ19 | Slice, dice, pivot | Collateral flag × method, lọc FY. |
| BQ20 | Roll-up, slice, pivot | Status → tổng dòng trong cùng cohort; slice FY/method; không drill qua thời gian trạng thái. |
| BQ21 | Roll-up, drill-down, dice, pivot | State và NAICS → sector nếu mapping; lọc cohort FY; giữ mẫu số cùng lát cắt. |
| BQ22 | Roll-up, drill-down, slice, pivot | NAICS → sector nếu mapping; state × cohort; ngày charge-off chỉ sau kiểm tra DQ. |
| BQ23 | Slice, dice, pivot | Cohort FY × nhóm quy mô, lọc state; tỷ trọng tính lại theo cell. |
| BQ24 | Slice, dice, pivot | State × business age trên **tập resolved**, lọc cohort FY; giữ count mẫu số. |

## Ranh giới OLAP

- Tổng số tiền và count là phép cộng được theo lát cắt không chồng lấn; **tỷ lệ, bình quân, tăng trưởng phải tính lại từ thành phần** ở từng mức roll-up.
- `LoanStatus` là thuộc tính tại một snapshot. Pivot FY × status cho biết status **hiện tại của các cohort FY**, không cho biết status tại cuối từng FY.
- Các hierarchy sector/NAICS và fiscal quarter/month là đề xuất cần dẫn xuất/đối chiếu; không có sẵn đầy đủ dưới dạng cột CSV. State→county có hai trường nhưng phải dùng khóa ghép để tránh county trùng tên.
- Bộ lọc lender dùng `LocationID` của **lender hiện được gán**. Không có chiều thời gian thay đổi lender trong snapshot này.
- DQ14: `Program` có khoảng trắng đầu ở toàn bộ dòng và chỉ biểu diễn 7(a); không đề xuất hierarchy chương trình từ một giá trị. Nếu sau này thêm nguồn 504, phải xác nhận nhãn/chương trình trước khi so sánh. DQ06 (`FirstDisbursementDate` thiếu ở 3 dòng `P I F`) không tác động trực tiếp 24 câu hỏi hiện tại vì không câu nào tính thời gian từ phê duyệt đến giải ngân; sẽ áp dụng nếu mở rộng phân tích giải ngân.
