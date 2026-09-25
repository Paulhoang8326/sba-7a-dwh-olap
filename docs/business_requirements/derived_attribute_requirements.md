# Derived & Technical Attribute Requirements

**Mục đích:** đầu vào cho Attribute Mapping, chưa chốt bảng Fact/Dimension hoặc star schema. BQ và KPI tham chiếu [19 BQ](business_questions_selection.md), [KPI Catalog](kpi_catalog.md), [Business Rules](business_rules.md); trường nguồn theo [Data Dictionary](../data_understanding/data_dictionary.md) và sheet `7(a) Data Dictionary` của workbook SBA. `CORE` nghĩa là phục vụ một BQ chính hoặc lineage/đối soát tối thiểu; `OPTIONAL` là hữu ích nhưng không bắt buộc; `DEFERRED` cần nguồn/quyết định bổ sung. Storage là **loại nơi lưu khả dĩ**, không phải tên bảng đã chốt. `PROPOSED` chỉ là chính sách đồ án, `OPEN` chưa đủ căn cứ.

## Thuộc tính dẫn xuất và derived measures

| Attribute Name; Type | Source Attributes; Derivation Logic | Related BQs; KPIs | Business Value; Data Quality Dependencies | Proposed Storage; Necessity; Decision Status |
|---|---|---|---|---|
| `FiscalYear` (time) | `ApprovalDate`, `ApprovalFY`; `year(date)+1` nếu tháng 10–12, khác thì `year(date)`; **không tạo cột dư** nếu dùng `ApprovalFY`; so hai giá trị để phát hiện lệch | BQ01, BQ03 và mọi BQ theo FY; K02, K04 | FY nguồn đã có; chỉ cần kiểm chứng và trục ngày. Ngày phải parse và khớp FY | Date Dimension cho fiscal year của ngày; `ApprovalFY` giữ như nguồn/mapping; CORE cho kiểm FY, không cần cột fact `FiscalYear` riêng; PROPOSED |
| `FiscalQuarter` (time) | `ApprovalDate`; Q1=10–12, Q2=01–03, Q3=04–06, Q4=07–09 | BQ01; K02 | Drill FY→quý; cần parse ngày/khớp FY | Date Dimension; CORE; PROPOSED |
| `FiscalMonth` (time) | `ApprovalDate`; `((month(date)+2) mod 12)+1`, 10→1, 09→12 | BQ01, BQ03; K02, K04 | Drill đến tháng và cửa sổ FYTD; kiểm ngày/FY | Date Dimension; CORE; PROPOSED |
| `CalendarYear` (time) | `ApprovalDate`; `year(date)` | Không bắt buộc cho 19 BQ; — | Hữu ích khi xem ngày dân sự; không lồng dưới FY | Date Dimension nếu đã có ngày; OPTIONAL; PROPOSED |
| `CalendarQuarter` (time) | `ApprovalDate`; `ceil(month/3)` | Không bắt buộc; — | Không cần cho trục FY chính | Date Dimension; OPTIONAL; PROPOSED |
| `CalendarMonth` (time) | `ApprovalDate`; `month(date)` | Không bắt buộc; — | Hữu ích nhãn ngày, không thay fiscal month | Date Dimension; OPTIONAL; PROPOSED |
| `FiscalYTDFlag` (dynamic time predicate) | `ApprovalDate`, `ApprovalFY`, ngày cắt phân tích; `FiscalMonthDay(ApprovalDate) ≤ FiscalMonthDay(cutoff)` trong FY được chọn. Ngày cắt của FY2026 là 30/06; so FY2025 cùng 01/10–30/06 | BQ03; K04 | So cùng cửa sổ. Cờ cố định tại ETL sai khi đổi cutoff/snapshot | Query/Semantic Layer; CORE như **logic**, không lưu boolean cố định; PROPOSED |
| `LoanSizeBand` (loan characteristic) | `GrossApproval`; ánh xạ các khoảng không chồng lấn, đủ bao phủ, theo bảng ngưỡng **chưa chốt**; 0/NULL riêng nếu xuất hiện | BQ04, BQ18, BQ23; K01, K02, K05, K11, K12 | Phân bố vốn và status theo cỡ; không gọi ngưỡng chính thức SBA. Cần quyết định ngưỡng và kiểm min/max | Business/Loan Characteristics Dimension **hoặc** Query/Semantic Layer; CORE cho 3 BQ nhưng logic OPEN; OPEN |
| `TermBand` (loan characteristic) | `TermInMonths`; khoảng tháng không chồng lấn, đủ bao phủ, `0` và NULL riêng; ngưỡng **chưa chốt** | BQ16; K01, K02, K05 | Cơ cấu kỳ hạn; DQ07 11 dòng bằng 0 | Business/Loan Characteristics Dimension **hoặc** Query/Semantic Layer; CORE nhưng logic OPEN; OPEN |
| `NaicsSectorCode` (industry mapping) | `NaicsCode` dạng text; prefix 2 ký tự chỉ là **ứng viên**, kiểm code/version và dải sector gộp qua reference | BQ12; BQ07, BQ14, BQ21–BQ22 nếu roll-up; K01, K02, K05 | Drill sector→code; mã 6 ký tự chưa chứng minh version/hiệu lực | Industry Dimension; CORE cho BQ12 nhưng mapping OPEN; OPEN |
| `NaicsSectorName` (industry reference) | `NaicsCode` + bảng sector đúng version; **không** lấy `NaicsDescription` của code 6 ký tự làm tên sector | BQ12; các BQ roll-up sector; K01, K02, K05 | Nhãn báo cáo có nguồn; thiếu reference/version hiện tại | Industry Dimension sau khi có reference; DEFERRED; OPEN |
| `NonSBAGuaranteedApproval` (derived financial measure) | `GrossApproval − SBAGuaranteedApproval` trên từng dòng; tổng phải khớp hiệu hai tổng | BQ08; K07 | Truy vấn nhanh, kiểm đối soát hai amount; kiểm giá trị âm/bất thường | Fact Measure **hoặc** Query/Semantic Layer; CORE là **công thức**, lưu vật lý OPTIONAL; PROPOSED |
| `LoanAgeAtSnapshot` (duration) | `ApprovalDate`, `AsOfDate`; số tháng/ngày quan sát, cần quy tắc làm tròn nếu công bố | BQ20–BQ23 để nêu tuổi cohort; K12, K13 diễn giải | Hỗ trợ cảnh báo censoring, không thay cohort FY; ngày phải hợp lệ | Query/Semantic Layer; OPTIONAL (có thể hiển thị tuổi cohort từ ngày cắt và FY); PROPOSED |
| `ApprovalToFirstDisbursementDays` (duration) | `FirstDisbursementDate − ApprovalDate` nếu hai ngày hợp lệ và không âm | Không BQ chính; — | Phân tích giải ngân mở rộng; thiếu 71.186 ngày, DQ06 | Query/Semantic Layer; DEFERRED; OPEN |

**Vật lý so với truy vấn:** band và sector có thể lưu để bảo đảm một quy tắc nhất quán, tăng tốc nhóm/lọc, nhưng sửa ngưỡng/reference sẽ đòi tái xử lý. Tính ở semantic layer cho phép đổi ngưỡng và version không nạp lại, đổi lại phải kiểm mọi truy vấn cùng dùng một mapping. `NonSBAGuaranteedApproval` có thể lưu để đối soát và tái sử dụng; hiệu hai SUM tại truy vấn tránh một cột vật lý dư. `FiscalYTDFlag` phải là predicate theo tham số cutoff, không phải boolean cố định cho 30/06/2026.

## Technical attributes và surrogate keys

`Fact` trong bảng là **khả năng lưu cho grain dòng nguồn tại một snapshot**, không phê chuẩn tên bảng hay cấu trúc. “Có” ở cột truy vết/DQ/ETL nêu lợi ích của thuộc tính, không khẳng định đã triển khai. Dữ liệu nguồn giữ bất biến.

| Attribute | Purpose; Need/Priority | Lineage; Exact duplicate; ETL check | Fact?; Staging/Audit alternative | Decision Status |
|---|---|---|---|---|
| `LoanSnapshotKey` | Khóa thay thế nội bộ cho **dòng nguồn tại snapshot**; CORE/cao nếu triển khai fact dòng | Truy vết qua join audit; phân biệt dòng trùng; kiểm PK/unique | Có thể là PK fact; không là SBA LoanID và không dùng nối khoản vay giữa snapshots | PROPOSED; prototype gọi `LoanRowKey` |
| `SourceRowNumber` | Số dòng dữ liệu nguồn; CORE/cao | Lineage trực tiếp, giữ hai dòng giống hệt, kiểm số dòng nạp | Nên lưu fact hoặc quan hệ fact→audit một-một; giữ cả `SourceFileName`/ID file. Quy định: header = dòng vật lý 1, bản ghi đầu = 2; nếu parser hỗ trợ CSV multiline thì lưu thêm ordinal bản ghi và byte offset để tránh nhầm dòng vật lý | PROPOSED |
| `SourceFileName` | Định danh file/snapshot; CORE/cao | Ghép với số dòng thành nguồn duy nhất; đối soát batch/file | Fact có thể lưu file ID; tên/đường dẫn/checksum trong staging/audit. Không coi basename một mình là bất biến khi cùng tên bị thay nội dung | PROPOSED |
| `SourceRowHash` | Hash nội dung dòng chuẩn **được định nghĩa rõ**; OPTIONAL/trung bình | Tìm exact duplicate, kiểm drift; không chứng minh cùng LoanID | Staging/Audit ưu tiên; fact không bắt buộc. Cần ghi thuật toán, tập cột, encoding, canonicalization; hash trùng có thể có nhiều dòng | PROPOSED |
| `ETLBatchID` | Nhóm một lần nạp; CORE/cao khi xây ETL | Lineage batch, counts/rejects, replay | Fact lưu FK/ID batch hoặc liên kết qua audit; thông tin batch chi tiết ở audit | PROPOSED |
| `ETLLoadTimestamp` | Thời điểm hệ thống nạp, khác `AsOfDate`; OPTIONAL/trung bình | Kiểm lượt nạp, thời gian xử lý; không xử lý duplicate trực tiếp | Audit batch là đủ cho full rebuild một snapshot; fact không bắt buộc | PROPOSED |
| `DataQualityFlag` | Tập mã DQ theo dòng hoặc severity; CORE như yêu cầu audit, nhưng không nhất thiết một boolean | Truy vết DQ07–DQ15, so số lỗi ETL; không phải tiêu chí loại dòng tự động | Staging/Audit dạng nhiều issue/dòng; fact chỉ lưu flag/tổng hợp nếu report cần slicer DQ | PROPOSED |
| `RecordCount` | Hằng 1 mỗi dòng làm thành phần K01; CORE ở semantic contract | Kiểm tổng dòng và duplicate giữ nguyên; đối soát fact | Fact measure 1 **hoặc** `COUNT(*)` trong query; lưu vật lý OPTIONAL | PROPOSED |
| Dimension surrogate keys | Khóa nội bộ ổn định cho các chiều được chọn; CORE khi có dimensions/cao | Kiểm referential integrity, unknown members; không giải quyết exact duplicate/LoanID | Chỉ lưu FK trong fact khi mô hình được chốt; business codes (`LocationID`, NAICS) vẫn giữ text trong dimension/staging | PROPOSED |

**Khóa dòng tối thiểu:** `(SourceFileID/content checksum, SourceRecordOrdinal)` phải duy nhất trong lần nhập; `SourceRowNumber` giữ đúng vị trí file để người đọc truy ngược. Nếu có CSV chứa newline trong ô quoted, ordinal bản ghi và số dòng vật lý khác nhau: parser phải ghi cả hai hoặc xác nhận nguồn không có multiline trước khi dùng một cột. Không dùng `SourceRowHash` hoặc `LoanSnapshotKey` để nối các snapshot như cùng một khoản vay. Multi-snapshot cần hợp đồng grain/lineage mới, ngoài phạm vi này. [Prototype hiện tại](../02_warehouse_design.md) dùng `LoanRowKey` và `SourceRowNumber` cho một file; tên `LoanSnapshotKey` ở đây là yêu cầu khái niệm, chưa đổi code/DDL.

## Attribute Requirements Matrix — 19 BQ

Mỗi hàng nối `BQ → KPI → cột nguồn → dẫn xuất/logic → loại storage khả dĩ`. `RecordCount` kỹ thuật ngầm phục vụ mọi hàng dùng K01/K03/K12; `AsOfDate` ngầm định cho mọi KPI snapshot. Các cột “derived” có nhãn `(OPEN)` chưa được chốt. `Fact Measure`/`Dimension`/`Query` chỉ là **loại**, không phải thiết kế bảng.

| BQ | KPI | Source Attributes | Derived Attributes / logic | Potential Storage |
|---|---|---|---|---|
| BQ01 | K02 | `GrossApproval`, `ApprovalDate`, `ApprovalFY`, `ProjectState` | `FiscalQuarter`, `FiscalMonth`; kiểm FY | Fact Measure + Date Dimension + project geography |
| BQ02 | K01, K03 | `GrossApproval`, `ApprovalFY`, `ProcessingMethod` | `RecordCount`; average từ hai tổng | Fact Measure + Business/Loan Characteristics Dimension + Query/Semantic Layer |
| BQ03 | K04 | `GrossApproval`, `ApprovalDate`, `ApprovalFY`, `ProjectState`, `AsOfDate` | `FiscalYTDFlag` logic động; fiscal month | Fact Measure + Date Dimension + Query/Semantic Layer |
| BQ04 | K01, K02, K05 | `GrossApproval`, `ApprovalFY`, `BusinessAge` | `LoanSizeBand` (OPEN), `RecordCount`, parent share | Fact Measure + Business/Loan Characteristics Dimension hoặc Query/Semantic Layer |
| BQ06 | K06 | `SBAGuaranteedApproval`, `ApprovalFY`, `ProcessingMethod` | — | Fact Measure + Date Dimension + Business/Loan Characteristics Dimension |
| BQ07 | K08 | `SBAGuaranteedApproval`, `GrossApproval`, `ApprovalFY`, `ProjectState`, `NaicsCode` | Tỷ số hai tổng; `NaicsSectorCode` nếu roll-up (OPEN) | Fact Measure + Industry Dimension + Query/Semantic Layer |
| BQ08 | K07 | `GrossApproval`, `SBAGuaranteedApproval`, `LocationID`, `BankName`, `ProcessingMethod` | `NonSBAGuaranteedApproval` | Fact Measure hoặc Query/Semantic Layer; lender dimension dự kiến |
| BQ10 | K01, K02 | `GrossApproval`, `ProjectState`, `ProjectCounty`, `ApprovalFY` | `RecordCount`; county ghép state | Fact Measure + project geography; Date Dimension |
| BQ11 | K05 | `GrossApproval`, `ProjectState`, `ApprovalFY` | Parent share = mọi state trong FY | Fact Measure + Query/Semantic Layer; project geography |
| BQ12 | K01, K02, K05 | `GrossApproval`, `NaicsCode`, `NaicsDescription`, `ProjectState`, `ApprovalFY` | `NaicsSectorCode` (OPEN); `NaicsSectorName` sau reference | Fact Measure + Industry Dimension + Query/Semantic Layer |
| BQ14 | K09, K10 | `JobsSupported`, `GrossApproval`, `NaicsCode`, `ProjectState`, `ApprovalFY` | Tỷ số khi jobs tổng >0; sector nếu roll-up (OPEN) | Fact Measure + Industry Dimension + Query/Semantic Layer |
| BQ15 | K01, K02, K05 | `LocationID`, `BankName`, `GrossApproval`, `ApprovalFY` | Parent share; Top N xếp K02 | Fact Measure + lender dimension + Query/Semantic Layer |
| BQ16 | K01, K02, K05 | `TermInMonths`, `GrossApproval`, `ProcessingMethod`, `ApprovalFY` | `TermBand` (OPEN), `RecordCount`, parent share | Fact Measure + Business/Loan Characteristics Dimension hoặc Query/Semantic Layer |
| BQ17 | K01, K02 | `BusinessType`, `BusinessAge`, `GrossApproval`, `ApprovalFY`, `ProjectState` | `RecordCount`; missing/Unanswered riêng | Fact Measure + Business/Loan Characteristics Dimension |
| BQ18 | K11, K01 | `InitialInterestRate`, `FixedorVariableInterestInd`, `ProcessingMethod`, `GrossApproval` | `LoanSizeBand` (OPEN); rate sum/count có rate | Fact Measure hoặc Query/Semantic Layer + Business/Loan Characteristics Dimension |
| BQ20 | K01, K12 | `LoanStatus`, `ApprovalFY`, `ProcessingMethod`, `AsOfDate` | Count status/mọi status; mapping `P I F` (OPEN) | Fact Measure hoặc `COUNT(*)` + Query/Semantic Layer |
| BQ21 | K12 | `LoanStatus`, `ApprovalFY`, `ProjectState`, `NaicsCode`, `AsOfDate` | `CHGOFF` count/mọi status; sector nếu roll-up (OPEN); tuổi cohort tùy chọn | Query/Semantic Layer + Industry Dimension |
| BQ22 | K13, K01 | `GrossChargeOffAmount`, `LoanStatus`, `ChargeOffDate`, `ApprovalFY`, `ProjectState`, `NaicsCode` | DQ event-date flag; sector nếu roll-up (OPEN) | Fact Measure + Staging/Audit + Industry Dimension |
| BQ23 | K12 | `LoanStatus`, `GrossApproval`, `ApprovalFY`, `AsOfDate` | `P I F` count/mọi status; `LoanSizeBand` (OPEN) | Query/Semantic Layer + Business/Loan Characteristics Dimension |

**CORE coverage:** fiscal time → BQ01/BQ03; `LoanSizeBand` → BQ04/BQ18/BQ23; `TermBand` → BQ16; `NaicsSectorCode` → BQ12; `NonSBAGuaranteedApproval` → BQ08; `FiscalYTDFlag` là logic BQ03. Technical CORE (`SourceRowNumber`, file ID, batch, quality audit, count, surrogate keys khi có dimension) phục vụ lineage/đối soát bắt buộc. Không có derived CORE vô chủ. Các trường calendar, sector name, duration không bắt buộc để trả lời 19 BQ ở cấp mã nguồn hiện tại; riêng BQ12 muốn tên sector chính thức phải bổ sung reference.
