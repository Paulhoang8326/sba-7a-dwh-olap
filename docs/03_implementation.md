# SSIS và SSAS: hướng dẫn dựng project thật

## Môi trường

SQL Server Developer Database Engine và SSAS **Multidimensional**, SSMS, Visual Studio với Integration Services/Analysis Services Projects tương thích. Các dịch vụ MSSQLSERVER và MSSQLServerOLAPService được phát hiện trên máy khi khảo sát nhưng đang dừng; chưa khởi động, chưa triển khai database/cube.

Chọn SQL Server 2019 nếu cô bắt buộc mining trong SSAS/DMX. Data Mining đã bị loại khỏi SSAS 2022; nếu dùng 2022+, phần mining làm Python khi được cô chấp nhận. Nguồn: [Microsoft về Data Mining](https://learn.microsoft.com/en-us/analysis-services/data-mining/data-mining-services-and-data-sources?view=asallproducts-allversions). Cube multidimensional và mining là hai phần khác nhau.

## SSIS chính thức từ CSV gốc

Project đề xuất `Source/SSIS/SBA7aETL.dtproj`; package `LoadSnapshot.dtsx`. Chưa tạo các file này trong repo. Python là bản chuẩn kiểm chứng transformation, không được dùng Execute Process chạy Python rồi gọi đó là toàn bộ SSIS.

1. Parameter: RawFilePath, SnapshotDate, SqlConnection. Execute SQL Task mở batch, lưu SourceFile/SHA256/AsOfDate/StartTime/Status. Không lưu mật khẩu vào project.
2. Flat File Connection Manager: UTF-8, dấu phẩy, qualifier `"`, first row column names. Import toàn bộ 42 cột dạng text Unicode vào `staging.LoanRaw`, thêm BatchID và SourceRowNumber. ZIP/NAICS/LocationID giữ text. Tạo staging từ metadata nguồn, không ép kiểu ngay ở source.
3. Data Flow: Derived Column TRIM; chuẩn hóa P I F → PIF; Data Conversion hoặc Script Component parse ISO dates và numeric invariant. Error Output ghi BatchID, SourceRowNumber, Field, RawValue, Reason. Không bỏ lỗi âm thầm.
4. Conditional Split: required date/amount invalid → reject + fail batch sau khi ghi lỗi; missing optional date/rate → NULL; blank category → Unknown. Các cảnh báo zero term/rate và event dates mâu thuẫn vẫn giữ bản ghi kèm log. Phân biệt warning với reject.
5. Derive FiscalYear theo tháng 10; kiểm tra đối chiếu ApprovalFY. Derive sector mã gộp; record count, outcome flags, các tử/mẫu số của measures theo `src/main.py`.
6. Aggregate DISTINCT tuple cho dimension, cấp surrogate key. Nạp State/Sector/Date trước, County/Industry sau, rồi Lender/Business/LoanProfile. Lookup cache full dùng đúng composite natural key. Không join chỉ bằng CountyName hoặc NaicsCode khi description khác nhau.
7. Nạp fact cuối, lookup 5 date roles, thiếu ngày optional → NULL. Record SourceRowNumber từ raw, không đánh lại sau sort. Sort trong SSIS không bật Remove duplicate rows trên fact.
8. Kiểm tra RowCount raw = fact + rejected. Bản nguồn đã chạy Python có rejected=0, fact=388338. Đối soát tổng tiền, status, năm và orphan keys theo `sql/02_validation.sql`; batch chỉ Success khi qua kiểm tra.
9. Commit batch rồi process cube; failure rollback hoặc giữ ở staging để sửa. Thiết kế full refresh: database đích riêng, xóa fact trước dimensions **trong transaction có backup** khi thực hiện lần chạy tiếp. Không tự append snapshot thứ hai.
10. Chụp Control Flow, từng Data Flow, error path, execution results, row counts và kết quả đối soát vào báo cáo.

### Nạp prototype để dựng cube sớm

Chạy Python để tạo CSV. Dùng Flat File Source → Data Conversion → OLE DB Destination trong thứ tự: DimDate, DimState, DimSector, DimCounty, DimIndustry, DimLender, DimBusiness, DimLoanProfile, FactLoanSnapshot. Map theo tên cột; khóa đã có trong CSV, không tạo identity mới. Đặt kiểu DECIMAL đủ scale (nguồn bảo lãnh có phần lẻ nhỏ hơn cent), optional dates/rate là nullable. Giữ NULL khi input rỗng, dùng fast load và Check Constraints. Prototype này hỗ trợ dựng cube trước, **không thay quy trình SSIS từ raw** ở trên.

## Hợp đồng cube cho MDX

Cube Name: `SBA Lending`. Measure group `Loan Snapshot`. Nguồn DSV là 9 bảng `dwh`, giữ cả hai nhánh snowflake. Quan hệ snowflake dùng join PK/FK 1:N; không thêm quan hệ fact → State/Sector độc lập tạo đường join trùng.

Tên dimension/attribute phải khớp chính xác:

| Cube dimension | Attribute hierarchy dùng trong MDX | KeyColumns / NameColumn |
|---|---|---|
| Approval Date | Fiscal Year, Calendar Year, Calendar Quarter, Month, Date | FiscalYear; CalendarYear; (CalendarYear, CalendarQuarter); (CalendarYear, MonthNumber); DateKey |
| Project Geography | State, County | StateCode; CountyKey (caption ProjectCounty) |
| Industry | Sector, NAICS | SectorCode; IndustryKey (caption NaicsDescription) |
| Lender | Lender | LenderKey (caption BankName) |
| Business | Business Type, Business Age | BusinessType; BusinessAge |
| Loan Profile | Status, Processing Method, Rate Type, Collateral | LoanStatus; ProcessingMethod; FixedorVariableInterestInd; CollateralInd |

Dimension key của Project Geography là CountyKey, Industry là IndustryKey. DimDate key DateKey. Thêm role-playing `First Disbursement Date`, `Paid In Full Date`, `Charge Off Date`, `As Of Date`.

Natural user hierarchies:

- `[Approval Date].[Calendar]`: Calendar Year → Calendar Quarter → Month → Date. Month NameColumn dùng YearMonth; sort theo key. Quarter và Month dùng composite keys như bảng.
- `[Project Geography].[Geography]`: State → County, quan hệ County → State.
- `[Industry].[Classification]`: Sector → NAICS, quan hệ IndustryKey → SectorCode.

Đặt attribute relationships từ leaf lên parent; không nối FiscalYear trực tiếp với CalendarYear vì tháng 10–12 thuộc năm tài chính kế tiếp. Có thể thêm hierarchy fiscal riêng với composite FiscalYear/FiscalQuarter/FiscalMonth.

Tạo SUM measures tên đúng theo bảng measures trong `02_warehouse_design.md`. Các auxiliary measures: `Interest Weighted Amount`, `Interest Known Approval`, `Term Total`, `Disbursement Days Total`, `Disbursement Observed Count`. Ẩn các auxiliary khỏi người dùng sau khi kiểm tra. Không chọn InitialInterestRate SUM trong wizard.

Cube calculations: copy `Source/SSAS/calculations.mdx` vào Calculations Script sau `CALCULATE;` (không lặp CALCULATE). Đặt FormatString tiền `#,##0.00`, count `#,##0`, tỷ lệ `0.00%`. Tỷ lệ chia 0 trả NULL.

Enable UnknownMember (Visible), NullProcessing=UnknownMember cho date roles thiếu. Khóa ngày không tồn tại mà không phải NULL là lỗi cần sửa, không IgnoreError toàn bộ. Process Dimensions rồi Cube, kiểm tra tổng và từng FY/status với SQL. Có thể partition theo Approval FY, không cần phân tán/multiple fact cho 388k dòng.

Tạo drillthrough action trả SourceRowNumber, dates, project state, NAICS, amounts; không cần name/address cá nhân. Query 15 dùng DRILLTHROUGH cần quyền Read + Drillthrough. Chạy từng SELECT/DRILLTHROUGH riêng trong SSMS MDX.

Chưa thực thi DDL, MDX hay process SSAS tại thời điểm chuyển repo. Tên trong MDX là hợp đồng để dựng cube, không phải tên đã khám phá từ server đang chạy.
