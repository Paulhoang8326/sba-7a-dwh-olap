> **HISTORICAL REFERENCE — NOT CURRENT CONTRACT.** Giữ nguyên nội dung đóng góp từ `main` để tham khảo lịch sử. Các tên bảng, số Dimensions và trạng thái implementation bên dưới không thay thế [trạng thái hiện hành](../00_current_status.md), [schema hiện hành](../dimensional_model/candidate_schema.md) hoặc [kế hoạch SSIS Chương 2](../etl/chapter2_ssis_plan.md). Chương 1 hiện là `CHAPTER 1 READY TO FREEZE`; preprocessing đã tích hợp và TSV đã tái lập, warehouse/SSIS chưa triển khai.

# ETL Implementation Plan — SBA 7(a) → FactLoanSnapshot + 8 Dim

> **PLANNED / NOT IMPLEMENTED**, lập 2026-09-30. Kế hoạch triển khai tiền xử lý (Python) và ETL (SSIS → SQL Server) cho [Target Schema Proposal 1F+8D](../dimensional_model/candidate_schema.md), theo [Preprocessing Plan](../data_understanding/preprocessing_plan.md), [Business Rule Register](../business_requirements/business_rule_register.md) và [Measure Contract](../business_requirements/measure_contract_q1_q15.md). Cách tổ chức SSIS (Execute SQL Task drop/create → Data Flow Task từng Dim → Fact có Lookup → precedence constraints) tham khảo Chương 1–2 của `references/[6]_IS217Q11_23520009_23520753.pdf` (đồ án TMDB), đối chiếu thêm Chương 2 của 4 đồ án còn lại trong `references/` (cả 5 đều lọc trùng Dim bằng Sort). Chưa có file code/SQL/SSIS nào dưới đây được tạo. Cập nhật 2026-10-01: D1–D4 đã chốt (§8).

## 1. Vấn đề mã định danh (ID)

### 1.1 Dataset có và không có gì

| Loại ID | Có trong nguồn? | Ghi chú |
|---|---|---|
| Mã khoản vay (LoanID) | **Không** | SBA FOIA không công bố LoanID. |
| Mã khách hàng/borrower | **Không** | Chỉ có `BorrName`, `BorrStreet`, `BorrCity`, `BorrState`, `BorrZip` (text). `BorrName` có 323.752 giá trị khác nhau trên 388.338 dòng. |
| Mã lender | **Có** — `LocationID` | Natural key cho `DimLender` (2.338 giá trị, 1 LocationID ↔ 1 bộ thuộc tính bank trong snapshot này). Giữ dạng text, không mất số 0 đầu. |
| Mã ngành | **Có** — `NaicsCode` | Natural key (cùng `NaicsDescription`) cho `DimIndustry`. |
| Mã ngày | Tự sinh được | `DateKey = YYYYMMDD` từ `ApprovalDate`. |

### 1.2 Phải tự tạo — và KHÔNG được tạo

**Tự tạo (bắt buộc):**

| Key | Tạo ở đâu | Cách tạo | Vai trò |
|---|---|---|---|
| `SourceRecordOrdinal` | Python preprocessing | Số thứ tự bản ghi 1..388.338 theo thứ tự đọc CSV (đếm **record**, không đếm dòng vật lý — 16 record có ô nhiều dòng) | Lineage: truy ngược từ fact về đúng dòng nguồn. |
| `SourceFileID` | Python/SSIS | Mã file (vd. `FOIA_7a_FY2020_Present_asof_260630`) + SHA-256 trong manifest | Cùng `SourceRecordOrdinal` tạo `UNIQUE` → chạy lại không nhân đôi fact. |
| `LoanSnapshotKey` | SQL Server | `INT IDENTITY(1,1)` trên `FactLoanSnapshot` (giống `FACT_ID` tự tăng trong đồ án tham khảo) | Surrogate PK của fact. **Không phải SBA LoanID.** |
| `GeographyKey`, `IndustryKey`, `LenderKey`, `LoanProfileKey`, `LoanStatusKey`, `TermBandKey`, `BusinessKey` | SQL Server | `INT IDENTITY(1,1)` khi insert các tổ hợp distinct (giống `GENRE_ID`, `COUNTRY_ID`… trong đồ án tham khảo) | Surrogate PK của Dim; fact lấy qua Lookup. |
| Unknown member | SQL seed | Key `0` ở mọi Dim (`SET IDENTITY_INSERT ON`) | Fact không bị mất dòng khi lookup trượt; đếm được bao nhiêu dòng rơi vào Unknown. |
| `DuplicateGroupID` (audit) | Python | Hash của 42 cột raw → đánh số nhóm | Chỉ để **gắn cờ** 687 dòng trùng (296 nhóm). Không phải LoanID, không dùng để xóa. |

**Không tạo `CustomerID`/`BorrowerID`.** Lý do:

1. Không có cơ sở đáng tin để gom borrower: cùng doanh nghiệp có thể viết tên khác (`INC` / `INC.` / `LLC`), khác doanh nghiệp có thể trùng tên; ghép tên + địa chỉ vẫn là suy đoán. Profiling đã thấy 3.316 dòng trùng composite yếu nhưng không chứng minh được là cùng khoản vay.
2. Không câu nào trong Q1–Q15 cần đơn vị borrower; mọi count là **published records**.
3. Schema đã duyệt ghi rõ `DimBusiness` là *phân loại* (BusinessType × BusinessAge, 22 tổ hợp), **không** định danh borrower và **không** chứa `BorrName`/địa chỉ ([candidate_schema.md](../dimensional_model/candidate_schema.md)).
4. `Borr*` là thông tin nhận dạng (PII) — không đưa vào kho.

Nếu sau này thật sự cần phân tích theo borrower, đó là một business rule mới (quy tắc chuẩn hóa tên, ngưỡng khớp, cách xử lý nhập nhằng) phải duyệt riêng, không nằm trong plan này.

### 1.3 Khác biệt quan trọng so với đồ án tham khảo

| Đồ án TMDB | Dự án SBA | Lý do |
|---|---|---|
| Có sẵn `MOVIE_ID` từ nguồn | Không có ID khoản vay → dùng `IDENTITY` + `SourceRecordOrdinal` | Nguồn khác nhau. |
| Fact dùng **Sort → Remove rows with duplicate sort values** theo `MOVIE_ID` | Fact **tuyệt đối không** dùng Sort-remove-duplicates | BR-POP-01: giữ mọi published record, kể cả 687 dòng exact duplicate. Chỉ dùng Sort-dedupe khi dựng **Dim**. |
| Python làm sạch rồi lọc còn 30.475 dòng | Không loại dòng; đầu ra phải còn đúng **388.338** | Preprocessing plan: không `dropna()`/`drop_duplicates()` toàn bảng. |
| Có Bridge table (phim nhiều thể loại) | Không cần Bridge | Mỗi dòng SBA có đúng 1 giá trị cho mỗi Dim. |
| `Dim_Date` sinh từ ngày distinct trong file | `DimDate` sinh liên tục bằng SQL (đủ mọi ngày của FY2020–FY2026) + thuộc tính fiscal | Q1/Q6 cần fiscal quarter và FYTD liên tục. |

## 2. Kiến trúc tổng thể

```text
data/raw/foia/FOIA_7a_...csv (bất biến)
  │  [Phase 1 — Python]  src/etl/preprocess.py
  ▼
data/staging/sba7a_standardized.tsv   + reports/preprocessing/{manifest.json, dq_issues.csv, reconciliation.csv}
  │  [Phase 3 — SSIS]  Source/SSIS/SBA7A_ETL/Package.dtsx
  ▼
SQL Server DB SBA7A_DWH
  stg.LoanStandardized  →  dwh.Dim* (8)  →  dwh.FactLoanSnapshot
  │  [Phase 4 — SQL]  sql/dwh/04_validate.sql
  ▼
Đối soát 388.338 dòng, tổng tiền, FY/status  →  sẵn sàng cho SSAS (ngoài phạm vi plan này)
```

Công cụ: Python 3 + pandas (đã có trong `requirements.txt`), SQL Server + SSMS, Visual Studio 2022 + SQL Server Integration Services Projects extension (như đồ án tham khảo). Phase 1, 2, 4 viết/chạy thử được trong repo; Phase 3 phải dựng trên máy Windows có Visual Studio.

## 3. Phase 1 — Tiền xử lý bằng Python

**File dự kiến:** `src/etl/preprocess.py`, `tests/test_preprocess.py`, `notebooks/01_preprocessing.ipynb` (minh họa cho báo cáo, P1.17). Lệnh chạy dự kiến: `python -m src.etl.preprocess`.

Khác biệt có chủ đích so với các đồ án tham khảo (để trình bày trong Chương 1): **không** xóa dòng trùng, **không** `dropna()`, **không** điền giá trị trung bình, **không** lọc bớt năm, **không** xóa dòng bất thường. Các trường hợp này chỉ gắn cờ trong `dq_issues.csv`, vì xóa sẽ làm tổng tiền lệch so với nguồn SBA công bố (BR-POP-01).

| Bước | Map với | Xử lý | Kiểm tra/đầu ra |
|---|---|---|---|
| P1.1 Manifest | PRE-01 | Tính SHA-256, đọc header, so 42 cột với danh sách kỳ vọng; đọc `dtype=str, keep_default_na=False` | `manifest.json`: checksum, 388.338 rows, 42 cols, thời gian chạy, rule version. Sai checksum/schema → dừng. |
| P1.2 Ordinal | PRE-01 | Thêm `SourceRecordOrdinal` 1..N, `SourceFileID` | N = 388.338. |
| P1.3 Trim + blank→NULL | PRE-03 | Trim khoảng trắng đầu/cuối (vd. `Program` = `" 7A"`); chuỗi rỗng → NULL. Giữ nguyên chữ hoa/thường. | So cardinality trước/sau trim từng cột phân tích. |
| P1.4 Ô nhiều dòng | — | Thay `\r`, `\n`, `\t` trong text bằng một khoảng trắng | 16 record multiline; sau bước này file output 1 record = 1 dòng (SSIS Flat File Source đọc ổn định hơn). |
| P1.5 Parse kiểu | PRE-02 | 5 cột ngày → `date` ISO; `GrossApproval`, `SBAGuaranteedApproval`, `GrossChargeOffAmount` → decimal, tối thiểu 2 chữ số lẻ, **không làm tròn** (D4: giữ độ chính xác gốc, 2 dòng có 3 chữ số lẻ gắn cờ `AMOUNT_SCALE_GT_2`); `TermInMonths`, `JobsSupported` → int (kiểm phần lẻ = 0); `LocationID`, `NaicsCode`, ZIP, FDIC/NCUA, district giữ **text** | Parse lỗi → ghi `dq_issues.csv`, không sửa raw. |
| P1.6 Date/FY | PRE-04 | `FiscalYearDerived` từ `ApprovalDate` (tháng ≥10 → năm+1), so với `ApprovalFY`; cờ `ChargeOffDate > AsOfDate` (22), `PaidInFullDate < ApprovalDate` (2), `CHGOFF` thiếu ngày (5) | Chỉ gắn cờ, không đổi/xóa. |
| P1.7 Numeric | PRE-05 | Cờ amount âm, `SBAGuaranteedApproval > GrossApproval`, term = 0 (11), rate = 0 (87) | Giữ 0 khác NULL. |
| P1.8 Duplicate | PRE-06 | `RowHash` trên 42 cột raw → `DuplicateGroupID`, `IsExactDuplicate` | 687 dòng / 296 nhóm; **không xóa**. |
| P1.9 Status | PRE-07, BR-STATUS-01 | `RawStatus` = nguồn; `CanonicalStatus`: `P I F`→`PIF`, còn lại giữ nguyên | 5 giá trị raw, không có giá trị lạ (lạ → `UNMAPPED`). |
| P1.10 TermBand | PRE-09, BR-TERM-01 | `TermBandCode`: `ZERO`=0, `SHORT`=1–60, `MEDIUM`=61–119, `TERM_120`=120, `LONG`=121–240, `VERY_LONG`>240, `MISSING`, `INVALID` | Tổng các band = 388.338; `TERM_120` = 236.672. |
| P1.11 NAICS Sector | PRE-08, BR-NAICS-01 | **D1 = A (đã chốt).** Tạo `NaicsSectorCode` từ 2 số đầu, gộp dải 31–33 / 44–45 / 48–49 (ví dụ `311811` → `31-33`); `SectorMappingStatus = 'CANDIDATE_UNVERIFIED'`; `NaicsSectorName = NULL`. Mã không đủ 6 số/không phải số → `NaicsSectorCode = NULL`, status `UNMAPPED`. Bước xác minh sau: xem §9 bước 5 | Đếm số dòng theo `SectorMappingStatus`; không gắn `VERIFIED` khi chưa có reference. |
| P1.12 Business | BR-BUSINESS-01 | Giữ `BusinessTypeRaw`, `BusinessAgeRaw`; thêm `*ValueStatus` = `PRESENT` / `MISSING`; `Unanswered` là giá trị PRESENT, khác MISSING | 22 tổ hợp. |
| P1.13 Lookup token | — | Với cột dùng làm business key của Dim, NULL → token hiển thị `(Missing)` trong **cột lookup riêng**; cột raw vẫn NULL | Tránh việc Lookup SSIS không khớp NULL = NULL (xem §7 R3). |
| P1.14 Export + reconcile | PRE-10 | Chỉ xuất các cột kho cần (không `Borr*`, không `Bank` address, không franchise) ra TSV UTF-8 có header | `reconciliation.csv`: rows, `SUM` 4 measure, count theo FY và status — raw vs standardized phải bằng nhau. |
| P1.15 Bảng chọn cột | — | Liệt kê đủ 42 cột nguồn: số ô trống, % trống, số giá trị khác nhau (tính từ dữ liệu), quyết định `KEEP`/`DROP`, cột đích trong TSV, lý do (`PII`, `NGOAI_PHAM_VI_Q1_Q15`, `THIEU_TREN_50PCT`, `HANG_SO`, `CHI_DUNG_DQ`…). Quyết định lấy từ danh sách cột TSV thực tế, không gõ tay | `reports/preprocessing/column_selection.csv`; 42 dòng; mọi cột `DROP` có lý do. Bỏ **cột**, không bỏ **dòng**. |
| P1.16 Bảng trước/sau | — | So raw và standardized: số dòng, số cột, số ô trống từng cột (raw: chuỗi rỗng; sau: NULL), số giá trị khác nhau trước/sau trim của cột phân tích, `SUM` 4 measure | `reports/preprocessing/before_after.csv`; số dòng 388.338 → 388.338; tổng tiền không đổi. |
| P1.17 Notebook minh họa | — | `notebooks/01_preprocessing.ipynb` gọi lại các hàm trong `src/etl/preprocess.py` theo từng bước "Bước 1…n" (markdown tiếng Việt), in `shape`, `info()`, `isnull().sum()`, `head()`, số dòng theo DQ flag, bảng P1.15 và P1.16. **Không chép lại logic**; file `.py` vẫn là nguồn chuẩn. Lưu sẵn output để chụp hình báo cáo | Chạy notebook từ đầu không lỗi; TSV tạo ra có cùng SHA-256 với lệnh `python -m src.etl.preprocess`. |

**Cột xuất ra `sba7a_standardized.tsv` (dự kiến ~27 cột):** `SourceFileID, SourceRecordOrdinal, AsOfDate, ApprovalDate, ApprovalFY, FiscalYearDerived, ProjectState, ProjectCounty, NaicsCode, NaicsDescription, NaicsSectorCode, SectorMappingStatus, LocationID, BankName, ProcessingMethod, RawStatus, CanonicalStatus, TermInMonths, TermBandCode, BusinessTypeRaw, BusinessAgeRaw, BusinessTypeValueStatus, BusinessAgeValueStatus, GrossApproval, SBAGuaranteedApproval, GrossChargeOffAmount, JobsSupported, IsExactDuplicate, DQFlagCount`. Ngày sự kiện (`FirstDisbursementDate`, `PaidInFullDate`, `ChargeOffDate`) để trong file DQ/staging, chưa là date role (theo candidate schema).

**Test (`tests/test_preprocess.py`):** 388.338 dòng; ordinal duy nhất liên tục; tổng 4 measure = raw; FY count = 42.298 / 51.856 / 47.678 / 57.362 / 70.242 / 78.078 / 40.824; `LocationID` giữ số 0 đầu; `P I F` → `PIF`; TermBand đủ 388.338; 687 dòng có `IsExactDuplicate`; `column_selection.csv` đủ 42 cột nguồn và mọi cột `DROP` có lý do; mọi cột `KEEP` có trong TSV; `before_after.csv` có số dòng và tổng tiền không đổi.

**Acceptance Phase 1:** chạy 2 lần ra cùng checksum output; mọi test pass; không dòng nào bị loại.

## 4. Phase 2 — DDL kho dữ liệu (SQL Server)

**File dự kiến** (không sửa `sql/01_warehouse.sql` của prototype cũ):

| File | Nội dung | Dùng trong SSIS |
|---|---|---|
| `sql/dwh/00_drop_all.sql` | Drop fact trước, rồi 8 dim, rồi staging | Execute SQL Task "Drop All Tables" |
| `sql/dwh/01_create_all.sql` | Schema `stg`, `dwh`; 1 bảng staging, 8 dim, 1 fact; PK, FK, UNIQUE | Execute SQL Task "Create All Tables" |
| `sql/dwh/02_seed_static.sql` | Unknown member key 0 cho mọi dim; `DimDate` sinh liên tục + 2 special member; `DimTermBand` 8 dòng tĩnh; `DimLoanStatus` 5 dòng + mô tả | Execute SQL Task "Seed Static Dimensions" |
| `sql/dwh/04_validate.sql` | Truy vấn đối soát (Phase 4) | Execute SQL Task cuối / chạy tay trong SSMS |

**Bảng và khóa:**

| Bảng | PK | Business key (UNIQUE) | Thuộc tính chính | Số member dự kiến |
|---|---|---|---|---|
| `stg.LoanStandardized` | — | `(SourceFileID, SourceRecordOrdinal)` | Toàn bộ cột TSV | 388.338 |
| `dwh.DimDate` | `DateKey` INT = YYYYMMDD (0 = Missing, −1 = Invalid) | `FullDate` | `CalendarYear/Quarter/Month`, `MonthName`, `FiscalYear`, `FiscalQuarter`, `FiscalMonth`, `DateMemberType` | Mọi ngày 2019-10-01 → 2026-09-30 + 2 special |
| `dwh.DimProjectGeography` | `GeographyKey` IDENTITY | `(ProjectState, ProjectCounty)` | 2 cột text | Đếm khi chạy |
| `dwh.DimIndustry` | `IndustryKey` IDENTITY | `(NaicsCode, NaicsDescription)` | + `NaicsSectorCode`, `NaicsSectorName`, `NaicsVersion`, `SectorMappingStatus` | ≈1.795 cặp raw (trước trim) |
| `dwh.DimLender` | `LenderKey` IDENTITY | `LocationID` | `BankName` | 2.338 |
| `dwh.DimLoanProfile` | `LoanProfileKey` IDENTITY | `ProcessingMethod` | raw label | 19 |
| `dwh.DimLoanStatus` | `LoanStatusKey` IDENTITY | `RawStatus` | `CanonicalStatus`, `StatusMappingStatus`, `StatusDescription` | 5 |
| `dwh.DimTermBand` | `TermBandKey` IDENTITY | `BandCode` | `BandLabel`, `LowerBound`, `UpperBound`, `SortOrder`, `IsAnalytical`, `RuleVersion` | 8 |
| `dwh.DimBusiness` | `BusinessKey` IDENTITY | `(BusinessTypeRaw, BusinessAgeRaw)` | `*ValueStatus` | 22 |
| `dwh.FactLoanSnapshot` | `LoanSnapshotKey` IDENTITY | `(SourceFileID, SourceRecordOrdinal)` | 8 FK `NOT NULL`; `GrossApproval`, `SBAGuaranteedApproval`, `GrossChargeOffAmount` DECIMAL(18,3) (D4); `JobsSupported` INT; `RecordCount` TINYINT = 1; `TermInMonths` INT; `ETLBatchID` | 388.338 |

Kiểu text dùng `NVARCHAR` đủ rộng (vd. `BankName`, `NaicsDescription` NVARCHAR(255)); các cột business key của Dim (cột trong `UNIQUE`) khai báo `COLLATE Latin1_General_100_BIN2` để SQL Server so sánh hoa/thường giống Sort và Lookup của SSIS (R7); `DateKey` tính: `FiscalYear = YEAR(d) + (MONTH(d) >= 10)`, `FiscalMonth = ((MONTH(d) + 2) % 12) + 1`, `FiscalQuarter = (FiscalMonth − 1) / 3 + 1`.

**Acceptance Phase 2:** chạy `00 → 01 → 02` hai lần liên tiếp trên DB trống không lỗi; mọi dim có đúng một member key 0.

## 5. Phase 3 — SSIS package (theo cấu trúc đồ án tham khảo)

**Project:** `Source/SSIS/SBA7A_ETL/` (`SBA7A_ETL.dtproj`, `Package.dtsx`). Connection managers: `SBA7A_STANDARDIZED_SOURCE` (Flat File, TSV, code page 65001, header row), `SBA7A_DWH` (OLE DB → SQL Server).

**Control Flow (nối tuần tự bằng precedence constraint, như mục 2.5 của tài liệu tham khảo):**

| # | Task | Loại | Nội dung |
|---|---|---|---|
| 1 | Drop All Tables | Execute SQL Task | `00_drop_all.sql` |
| 2 | Create All Tables | Execute SQL Task | `01_create_all.sql` |
| 3 | Seed Static Dimensions | Execute SQL Task | `02_seed_static.sql` (Unknown, DimDate, DimTermBand, DimLoanStatus) |
| 4 | STG_LOAN | Data Flow Task | Flat File Source → Data Conversion (kiểu DT_WSTR/DT_NUMERIC(18,3) cho tiền/DT_DBDATE/DT_I4) → OLE DB Destination `stg.LoanStandardized` (fast load) |
| 5 | DIM_PROJECT_GEOGRAPHY | Data Flow Task | OLE DB Source (stg, 2 cột) → Sort theo `(ProjectState, ProjectCounty)` + **Remove rows with duplicate sort values** → OLE DB Destination (bỏ qua cột IDENTITY) |
| 6 | DIM_INDUSTRY | Data Flow Task | Tương tự, key `(NaicsCode, NaicsDescription)`, mang theo `NaicsSectorCode`, `SectorMappingStatus` |
| 7 | DIM_LENDER | Data Flow Task | Sort-dedupe theo `LocationID`, mang `BankName` |
| 8 | DIM_LOAN_PROFILE | Data Flow Task | Sort-dedupe theo `ProcessingMethod` |
| 9 | DIM_BUSINESS | Data Flow Task | Sort-dedupe theo `(BusinessTypeRaw, BusinessAgeRaw)`, mang 2 cột ValueStatus |
| 10 | FACT_LOAN_SNAPSHOT | Data Flow Task | Xem dưới |
| 11 | Validate | Execute SQL Task | `04_validate.sql`; lỗi đối soát → task fail |

**D3 = Sort (đã chốt).** Mỗi Dim ở task 5–9 dùng component **Sort** với ô **Remove rows with duplicate sort values**, chỉ chọn các cột business key làm cột sort (cột mang theo như `BankName`, `NaicsSectorCode` để *Pass Through*). Đây là cách cả 5 đồ án tham khảo dùng. Không dùng `SELECT DISTINCT`.

Task 5–9 không phụ thuộc nhau nên có thể chạy song song sau task 4; nhưng để giống tài liệu tham khảo và dễ chụp màn hình, nối tuần tự cũng được. Biến thể tùy chọn (đồ án IS217_O21_21521779 và [15]): gộp task 5–9 thành một Data Flow, đọc staging một lần → **Multicast** → 5 nhánh Sort → 5 Destination.

**Data Flow FACT_LOAN_SNAPSHOT:**

```text
OLE DB Source (stg.LoanStandardized)
 → Lookup DimDate           (ApprovalDate = FullDate)                    → ApprovalDateKey
 → Lookup DimProjectGeography (ProjectState, ProjectCounty)              → GeographyKey
 → Lookup DimIndustry       (NaicsCode, NaicsDescription)                → IndustryKey
 → Lookup DimLender         (LocationID)                                 → LenderKey
 → Lookup DimLoanProfile    (ProcessingMethod)                           → LoanProfileKey
 → Lookup DimLoanStatus     (RawStatus)                                  → LoanStatusKey
 → Lookup DimTermBand       (TermBandCode = BandCode)                    → TermBandKey
 → Lookup DimBusiness       (BusinessTypeRaw, BusinessAgeRaw)            → BusinessKey
 → Derived Column: RecordCount = 1; mọi *Key NULL → 0 (Unknown); ETLBatchID
 → OLE DB Destination dwh.FactLoanSnapshot (bỏ qua LoanSnapshotKey vì IDENTITY)
```

- Mỗi Lookup: **Full cache**, "Specify how to handle rows with no matching entries" = **Ignore failure** (rồi Derived Column đổi NULL → 0). **Không** chọn "Redirect to no match output" rồi bỏ nhánh đó, vì sẽ mất dòng. (Đồ án tham khảo chỉ nối *Lookup Match Output* — với SBA làm vậy có thể rớt dòng mà không báo.)
- **Không có Sort/Remove duplicates** trong Data Flow này.
- Dùng **Lookup** (như đồ án [6] và [27]), **không** dùng chuỗi Sort + Merge Join (như đồ án IS217_O21_21520429, IS217_O21_21521779, [15]): Merge Join phải sort lại 388.338 dòng fact ở mỗi Dim, sinh nhiều bảng trung gian, và kiểu inner join mặc định làm mất dòng không khớp mà không báo.
- Thêm Row Count transformation đầu/cuối để ghi log số dòng vào biến.

**Acceptance Phase 3:** Package chạy xanh toàn bộ từ DB trống; chạy lại lần 2 cho kết quả giống hệt (idempotent nhờ drop/create).

## 6. Phase 4 — Đối soát sau khi nạp

`sql/dwh/04_validate.sql` kiểm tra, so với `reports/preprocessing/reconciliation.csv`:

| # | Kiểm tra | Kỳ vọng |
|---|---|---|
| V1 | `COUNT(*)` fact = `SUM(RecordCount)` | 388.338 |
| V2 | `COUNT(DISTINCT SourceRecordOrdinal)` | 388.338 |
| V3 | `SUM` 4 measure fact = staging = file Python | Bằng nhau tuyệt đối |
| V4 | Count theo `DimDate.FiscalYear` | 42.298 / 51.856 / 47.678 / 57.362 / 70.242 / 78.078 / 40.824 (FY2020→FY2026) |
| V5 | Count theo `DimLoanStatus.RawStatus` | Khớp profiling (vd. `P I F` = 68.201) |
| V6 | Số dòng fact có FK = 0 (Unknown) theo từng Dim | 0, hoặc giải thích được từng dòng |
| V7 | FK mồ côi (LEFT JOIN dim IS NULL) | 0 |
| V8 | Số member mỗi Dim | Khớp bảng §4 |
| V9 | Dòng exact duplicate vẫn còn | 687 |
| V10 | Mỗi `LocationID` đúng 1 `LenderKey`; mỗi cặp NAICS đúng 1 `IndustryKey` | Không fan-out |
| V11 | Count và `SUM(GrossApproval)` theo `DimIndustry.SectorMappingStatus` | Tổng các status = 388.338; số `UNMAPPED` được báo rõ |

Lưu kết quả (ảnh chụp SSMS + file CSV kết quả) vào `reports/etl/` làm bằng chứng cho báo cáo.

## 7. Rủi ro và cách xử lý

| ID | Rủi ro | Xử lý |
|---|---|---|
| R1 | Vô tình dedupe fact theo thói quen từ đồ án mẫu | Không có Sort trong DFT fact; V1/V9 bắt lỗi. |
| R2 | Ô nhiều dòng / dấu ngoặc kép làm SSIS đọc lệch cột | Python xuất TSV đã loại `\r\n\t` khỏi text (P1.4). |
| R3 | Lookup SSIS với cột NULL | t **không chắc** hành vi Full cache khi so NULL = NULL trong mọi phiên bản SSIS, nên plan tránh hẳn: cột lookup dùng token `(Missing)` (P1.13) và Ignore failure → key 0. Nên thử nhanh trên máy m trước. |
| R4 | Mất số 0 đầu của `LocationID`, `NaicsCode` | Giữ text ở Python, Flat File column kiểu DT_WSTR, cột SQL NVARCHAR. |
| R5 | Sai FY do dùng năm dương lịch | `FiscalYear` sinh trong `DimDate` theo công thức §4; V4 so với `ApprovalFY` nguồn. |
| R6 | NAICS sector công bố như đã xác minh | `SectorMappingStatus` luôn đi kèm; Q13/Q15 ghi rõ còn `PENDING_VERIFICATION` cho tới khi §9 bước 5 xong. |
| R7 | So sánh chữ hoa/thường không nhất quán: collation mặc định của SQL Server thường không phân biệt hoa/thường, còn Sort và Lookup của SSIS thì có phân biệt. Hai biến thể kiểu `Abc`/`ABC` có thể làm lỗi `UNIQUE` hoặc rơi vào Unknown | Cột business key của Dim dùng collation phân biệt hoa/thường (vd. `Latin1_General_100_BIN2`); V6/V8 bắt lỗi còn sót. |

## 8. Quyết định đã chốt (2026-10-01)

| ID | Câu hỏi | Quyết định | Lý do |
|---|---|---|---|
| D1 | NAICS Sector: nạp mã sector ứng viên ngay, hay để NULL cho tới khi xác minh reference NAICS 2017/2022? | **A — nạp ngay**: `NaicsSectorCode` từ 2 số đầu (gộp 31–33 / 44–45 / 48–49), `SectorMappingStatus = 'CANDIDATE_UNVERIFIED'`, chưa nạp `NaicsSectorName`. Xác minh ở §9 bước 5 rồi mới đổi sang `VERIFIED` và điền tên. | Q13/Q15 và hierarchy Sector → NAICS trong cube làm và test được ngay; vẫn giữ BR-NAICS-01 (không gọi là đã xác minh). |
| D2 | Phiên bản công cụ | Visual Studio 2022 (+ SQL Server Integration Services Projects 2022, Microsoft Analysis Services Projects 2022) + SSMS 22 (workload Business Intelligence) + SQL Server 2022 Developer (Database Engine, Analysis Services chế độ Multidimensional). | Theo môi trường nhóm. |
| D3 | Lọc trùng khi dựng Dim: Sort hay `SELECT DISTINCT`? | **Sort + Remove rows with duplicate sort values**, kèm collation `Latin1_General_100_BIN2` cho cột business key (R7). | Cả 5 đồ án tham khảo cùng môn đều dùng Sort; với 388.338 dòng hiệu năng không thành vấn đề. |
| D4 | Kiểu cột tiền: DECIMAL(18,2) hay giữ đủ độ chính xác nguồn? | **DECIMAL(18,3)** cho `GrossApproval`, `SBAGuaranteedApproval`, `GrossChargeOffAmount` ở cả `stg.LoanStandardized` và `dwh.FactLoanSnapshot`; SSIS Data Conversion dùng `DT_NUMERIC` precision 18, scale 3. Python giữ nguyên giá trị gốc, không làm tròn. | 2 dòng `SBAGuaranteedApproval` có 3 chữ số lẻ (ordinal 81174 = 3749992.425, 84754 = 3749975.124; cờ `AMOUNT_SCALE_GT_2`). Làm tròn 2 chữ số làm `SUM` lệch 0,009 so với raw, vi phạm V3. |

## 9. Thứ tự làm và đầu ra

| Bước | Việc | Đầu ra | Phụ thuộc |
|---:|---|---|---|
| 1 | Viết + test `src/etl/preprocess.py` | TSV standardized, manifest, DQ, reconciliation | — |
| 2 | Viết `sql/dwh/00–02` và chạy thử trong SSMS | DB `SBA7A_DWH` với bảng rỗng + seed | 1 (để biết độ rộng cột) |
| 3 | Dựng SSIS package theo §5 | `.dtproj`, `.dtsx`, ảnh chạy xanh | 1, 2 |
| 4 | Viết + chạy `04_validate.sql` | Kết quả V1–V11 trong `reports/etl/` | 3 |
| 5 | Xác minh NAICS (D1): tải danh sách mã NAICS 2017 và 2022 của U.S. Census Bureau vào `data/reference/`; kiểm từng `NaicsCode` trong CSV có trong ít nhất một bản không; kiểm 2 số đầu khớp sector chính thức. Mã khớp → `VERIFIED` + điền `NaicsSectorName`, `NaicsVersion`; mã không khớp → `UNMAPPED`. Chạy lại package | `reports/etl/naics_verification.csv` (số mã/số dòng theo status); BR-NAICS-01 mapping chuyển khỏi `PENDING_VERIFICATION` nếu không còn mã không khớp | 1, 4 |
| 6 | Viết Chương 1 (dữ liệu + tiền xử lý: bảng DQ, rule, before/after) và Chương 2 (SSIS: từng task + ảnh + kết quả đối soát) theo bố cục tài liệu tham khảo | Nội dung báo cáo | 1–5 |
| 7 | Cập nhật `docs/00_current_status.md`, `PROJECT_STATUS.md`, `preprocessing_plan.md`, `business_rule_register.md` từ `NOT IMPLEMENTED`/`PENDING_VERIFICATION` sang trạng thái thật | Tài liệu đồng bộ | 1–5 |
