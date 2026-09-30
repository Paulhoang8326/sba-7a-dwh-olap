# PROJECT_CONTEXT — Bối cảnh dự án SBA 7(a)

> **CURRENT SOURCE OF TRUTH:** [docs/00_current_status.md](docs/00_current_status.md) xác định phạm vi hiện hành. [Q1–Q15](docs/business_requirements/business_questions_current.md), gồm Q10 mới, đã duyệt ở cấp nội dung; [star 1 `FactLoanSnapshot` + 8 Dim](docs/dimensional_model/candidate_schema.md) là **PROPOSED TARGET SCHEMA**, chưa là Final/physical schema. [Measure Contract](docs/business_requirements/measure_contract_q1_q15.md) đã viết, chưa triển khai. [Rule register](docs/business_requirements/business_rule_register.md) ghi `PROJECT_APPROVED` cho population, cấp NAICS Sector, TermBand, canonical PIF và Q15 gates; NAICS reference/version/mapping còn `PENDING_VERIFICATION`. [Preprocessing](docs/data_understanding/preprocessing_plan.md) là `PLANNED / NOT IMPLEMENTED`. Các mô tả snowflake/Python/SQL ở phần lịch sử bên dưới là **previous prototype**, dù có một số tên bảng trùng candidate.

> Tài liệu bối cảnh tương đối ổn định, lập ngày 2026-09-24. Đọc cùng [PROJECT_STATUS.md](PROJECT_STATUS.md) để biết tiến độ mới nhất. Khi tài liệu và dữ liệu/code khác nhau, kiểm tra nguồn thực tế trước khi kết luận. **Đã có trong repository** không đồng nghĩa **đã triển khai trên SQL Server/SSAS** hoặc **đã được người dùng chốt**.

## 1. Project Overview

| Nội dung | Bối cảnh và mức xác nhận |
|---|---|
| Tên đề tài | **Xây dựng hệ thống Kho dữ liệu và OLAP hỗ trợ phân tích danh mục tín dụng, bảo lãnh và kết quả khoản vay SBA 7(a) tại Hoa Kỳ giai đoạn FY2020–FY2026** — tên được người dùng cung cấp, cũng ghi trong [README.md](README.md). |
| Môn học | Kho dữ liệu và OLAP — người dùng cung cấp. |
| Bối cảnh | Đồ án sinh viên dùng dữ liệu công khai SBA FOIA để thực hành khảo sát nguồn, thiết kế kho dữ liệu, ETL, truy vấn đa chiều và báo cáo. Không phải hệ thống vận hành để quyết định cấp tín dụng. |
| Lý do chọn | Snapshot cục bộ có 388.338 dòng, 42 trường, các chiều FY, địa lý, lender, NAICS và trạng thái; có số tiền phê duyệt, bảo lãnh và charge-off. Đây là cơ sở phù hợp để thực hành OLAP, theo [docs/01_feasibility.md](docs/01_feasibility.md). |
| Mục tiêu | Khảo sát dữ liệu; xác định câu hỏi/KPI hợp lệ; xây mô hình kho dữ liệu, quy trình nạp, cube và dashboard. Đây là **mục tiêu**, không phải danh sách chức năng đã hoàn thành. |
| Phạm vi hiện hành | CSV SBA 7(a) FY2020–FY2026, snapshot 2026-06-30. File FY2010–FY2019 chỉ là **khả năng mở rộng được thảo luận**, chưa có trong repository/chưa chốt nhập vào phạm vi. |
| Đối tượng phân tích | Dòng hồ sơ vay công bố, vốn phê duyệt và bảo lãnh, địa lý dự án, ngành, lender đang được gán khoản vay, trạng thái tại snapshot và số việc làm được báo cáo. |
| Kết quả mong đợi | Mô hình có đối soát dữ liệu, truy vấn OLAP, dashboard và báo cáo đồ án; [docs/07_delivery.md](docs/07_delivery.md) nêu bộ bàn giao dự kiến. Chưa coi checklist này là sản phẩm đã hoàn thành. |

## 2. Business Problems

Các nhóm dưới đây là **định hướng phân tích của previous prototype**, không thay [Q1–Q15 hiện hành](docs/business_requirements/business_questions_current.md). `Loan Count` trong prototype là **số dòng công bố**, chưa chứng minh là số khoản vay duy nhất.

| Business Problem | Business Questions | KPIs phù hợp nguồn | Dimensions | Expected Insights và giới hạn |
|---|---|---|---|---|
| Loan Portfolio Analysis | Quy mô vốn phê duyệt thay đổi theo FY; tập trung ở đâu, ngành nào, lender nào? | Số dòng, `SUM(GrossApproval)`, vốn không thuộc `CANCLD`, giá trị bình quân/dòng | Ngày phê duyệt, project state/county, NAICS/sector, lender hiện tại, status | Cơ cấu và xu hướng danh mục; FY2026 chỉ tới 30/06/2026, cần so cùng kỳ. |
| Credit Risk Analysis | Cơ cấu `PIF`, `CHGOFF`, `EXEMPT`, `COMMIT`, `CANCLD` của từng cohort ra sao? | Count theo status; `CHGOFF / (PIF + CHGOFF)` **chỉ trong tập resolved**; `SUM(GrossChargeOffAmount)` | Approval FY, status, ngành, địa lý, business profile | Mô tả kết quả đã quan sát tại snapshot; không phải xác suất vỡ nợ của toàn danh mục hay prospective risk. |
| Guarantee Analysis | SBA bảo lãnh bao nhiêu so với vốn phê duyệt; phân bố theo method/quy mô? | `SUM(SBAGuaranteedApproval)`, `SUM(GrossApproval - SBAGuaranteedApproval)`, tỷ lệ hai **tổng** | FY, processing method, ngành, địa lý, lender | Cơ cấu bảo lãnh tại lúc phê duyệt; phần không bảo lãnh không phải dư nợ hiện tại của lender. |
| Economic Contribution Analysis | Ngành/địa phương nào có `JobsSupported` được báo cáo nhiều? | `SUM(JobsSupported)`, USD phê duyệt/việc làm báo cáo khi mẫu số > 0 | FY, project geography, ngành, business age/type | Phân bố số việc làm lender tự khai; không phải số người duy nhất hoặc ước lượng tác động nhân quả. |

Không có dữ liệu đủ để tính dư nợ hiện tại, dòng tiền giải ngân/trả nợ, recovery, lợi nhuận hoặc tổn thất ròng của SBA ở cấp khoản vay. [docs/data_dictionary.md](docs/data_dictionary.md) ghi nghĩa gốc của trường.

## 3. Dataset Overview

| Nội dung | Thông tin đã đối chiếu |
|---|---|
| Dataset name | SBA 7(a) FOIA, file `FOIA_7a_FY2020_Present_asof_260630.csv` |
| Data source | [SBA 7(a) & 504 FOIA](https://data.sba.gov/dataset/7a-504-foia); bản sao cục bộ trong [data/raw/foia](data/raw/foia/README.md) là nguồn cho project. |
| Data format | 1 CSV UTF-8 có header; 1 workbook XLSX gồm sheet từ điển 7(a) và 504. Chỉ sheet `7(a) Data Dictionary` áp dụng cho CSV. |
| Time coverage | `ApprovalDate` 2019-10-01 đến 2026-06-30; `ApprovalFY` FY2020–FY2026; mọi dòng `AsOfDate = 2026-06-30`. |
| Number of files | **1 file CSV dữ liệu nguồn** và **1 workbook từ điển** trong `data/raw/foia/`; không có CSV riêng cho từng năm. |
| Total records | **388.338 dòng × 42 cột**; FY2020–FY2026 lần lượt 42.298, 51.856, 47.678, 57.362, 70.242, 78.078, 40.824. |
| Size/checksum | CSV 181.130.871 byte; SHA-256 `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`, theo [docs/data_profile.json](docs/data_profile.json). |
| Important attributes | `ApprovalDate`, `ApprovalFY`, `AsOfDate`, `GrossApproval`, `SBAGuaranteedApproval`, `GrossChargeOffAmount`, `LoanStatus`, `LocationID`, `ProjectState`, `ProjectCounty`, `NaicsCode`, `JobsSupported`. |
| Data limitations | Không có public LoanID, lịch sử giao dịch/số dư/recovery; nhiều trường thiếu; outcome của cohort mới chưa quan sát đủ. Xem §9. |

### Thuộc tính gốc trọng yếu

| Original attribute | Kiểu logic sau parse | Ý nghĩa và lưu ý |
|---|---|---|
| `AsOfDate`, `ApprovalDate`, `FirstDisbursementDate`, `PaidInFullDate`, `ChargeOffDate` | Date nullable tùy trường | Ngày snapshot và các ngày sự kiện; ngày sự kiện thiếu không gán ngày giả. |
| `ApprovalFY` | Integer | FY do nguồn ghi; đối chiếu với `ApprovalDate` (FY Mỹ bắt đầu tháng 10). |
| `LocationID` | String | Mã **lender** của SBA, không phải LoanID; giữ số 0 đầu. |
| `GrossApproval` | Decimal | Giá trị khoản vay được phê duyệt, gồm cả dòng sau đó `CANCLD`; không phải tiền đã giải ngân/dư nợ. |
| `SBAGuaranteedApproval` | Decimal | Giá trị bảo lãnh SBA lúc phê duyệt. |
| `GrossChargeOffAmount` | Decimal | Số dư ghi giảm gộp gồm phần có và không có bảo lãnh; không phải tổn thất ròng SBA. |
| `InitialInterestRate`, `TermInMonths` | Decimal nullable/decimal | Lãi suất ban đầu và kỳ hạn; không cộng trực tiếp để diễn giải. |
| `LoanStatus` | String | `EXEMPT`, `P I F`, `CANCLD`, `COMMIT`, `CHGOFF` trong CSV; prototype chuẩn hóa `P I F` → `PIF`. |
| `ProjectState`, `ProjectCounty`, `NaicsCode`, `NaicsDescription` | String | Địa lý **dự án** và ngành; county cần ghép bang, NAICS giữ dạng text. |
| `BankName`, `BankFDICNumber`, `BankNCUANumber` | String nullable | Thông tin lender **hiện được gán khoản vay**. |
| `JobsSupported` | Decimal | Việc làm tạo mới + duy trì do lender tự khai; không được SBA kiểm toán/xác minh theo từ điển nguồn. |
| `SoldSecMrktInd` | String nullable | CSV có `Y` hoặc blank; blank không được tự suy ra `N`. |

Danh mục **đủ 42 trường** và định nghĩa workbook ở [docs/data_dictionary.md](docs/data_dictionary.md); thống kê thiếu, phân bố và vấn đề chất lượng ở [docs/data_profile.json](docs/data_profile.json). Không dùng bảng tóm tắt này thay từ điển đầy đủ.

### Derived và proposed attributes

| Mức | Thuộc tính/chỉ tiêu | Quy tắc hoặc trạng thái |
|---|---|---|
| **Đã triển khai trong prototype Python** | `SectorCode`, fiscal year/quarter trong `DimDate`, `LoanCount`, `ChargeOffCount`, `ResolvedCount`, `NonCancelledApproval`, `UnguaranteedApproval`, các tử/mẫu số lãi suất và thời gian giải ngân | Quy tắc trong [src/main.py](src/main.py), giải thích tại [docs/02_warehouse_design.md](docs/02_warehouse_design.md). `InterestWeightedAmount` hiện lưu `InitialInterestRate / 100 × GrossApproval`, nên kết quả bình quân là tỷ lệ dạng 0–1. |
| **Calculated measure tại thời điểm truy vấn** | Guarantee ratio, average loan, resolved charge-off rate, weighted initial rate | Chia **tổng tử số cho tổng mẫu số**, xử lý mẫu số 0; không cộng/trung bình các tỷ lệ theo nhóm. |
| **Target Schema Proposal hiện hành, chưa có trong code/DDL** | `DimTermBand` có `TERM_120`, `DimLoanStatus`, `DimBusiness` tối thiểu, `NaicsSectorCode/NaicsSectorName` ứng viên trong `DimIndustry`, fiscal attributes của `DimDate`, star `FactLoanSnapshot` + 8 Dim | Xem [schema](docs/dimensional_model/candidate_schema.md), [Measure Contract](docs/business_requirements/measure_contract_q1_q15.md) và [rule register](docs/business_requirements/business_rule_register.md); rule phân tích đã `PROJECT_APPROVED`, NAICS mapping còn `PENDING_VERIFICATION`. `LoanSizeBand`/`GuaranteeBand` là ý tưởng cũ ngoài Q1–Q15 hiện hành. |

## 4. Data Warehouse Design

**Previous prototype trong repository** là snowflake, một fact và tám dimension. Nó có trong Python và [sql/01_warehouse.sql](sql/01_warehouse.sql); DDL chưa được chạy/kiểm chứng trên SQL Server. **Target Schema Proposal hiện hành** là [star logic `FactLoanSnapshot` + 8 dimensions](docs/dimensional_model/candidate_schema.md), chưa duyệt thành physical schema và chưa thay code/DDL prototype. `DimBusiness` prototype chứa franchise, không phải `DimBusiness` tối thiểu của candidate.

**Grain:** mỗi dòng của `FactLoanSnapshot` tương ứng **một dòng CSV tại snapshot 2026-06-30**. `LoanRowKey` là surrogate PK của lần build; `SourceRowNumber` truy vết vị trí trong file. Không khẳng định mỗi dòng là một khoản vay duy nhất. Fact có FK tới năm dimension nghiệp vụ và năm vai trò `DimDate`; `DimCounty → DimState`, `DimIndustry → DimSector` tạo hai nhánh snowflake.

| Table | Type | Grain | Key | Important Attributes | Status |
|---|---|---|---|---|---|
| `FactLoanSnapshot` | Fact | Một dòng CSV trong một snapshot | PK `LoanRowKey`; unique `SourceRowNumber` trong file; FK `CountyKey`, `IndustryKey`, `LenderKey`, `BusinessKey`, `LoanProfileKey`, 5 `*DateKey` | Amounts, jobs, rate/term gốc; count flags và numerator/denominator dẫn xuất | CSV prototype đã sinh; DDL có; **chưa nạp SQL Server** |
| `DimDate` | Dimension dùng nhiều vai trò | Một ngày lịch | PK `DateKey` | Calendar/Fiscal year, quarter, month; 5 date roles | CSV prototype đã sinh; DDL có |
| `DimState` | Dimension | Một project state/territory code | PK `StateKey` | `StateCode` | CSV prototype đã sinh; DDL có |
| `DimCounty` | Dimension | Tổ hợp state + project county | PK `CountyKey`; FK `StateKey` | `ProjectCounty` | CSV prototype đã sinh; DDL có |
| `DimSector` | Dimension | Một sector code | PK `SectorKey` | `SectorCode`, gồm dải gộp NAICS | CSV prototype đã sinh; DDL có |
| `DimIndustry` | Dimension | Tổ hợp sector + NAICS code/description | PK `IndustryKey`; FK `SectorKey` | `NaicsCode`, `NaicsDescription` | CSV prototype đã sinh; DDL có |
| `DimLender` | Dimension | Tổ hợp thuộc tính lender công bố | PK `LenderKey` | `LocationID`, bank name, FDIC/NCUA, bank city/state/ZIP | CSV prototype đã sinh; DDL có |
| `DimBusiness` | Dimension profile | Tổ hợp thuộc tính business | PK `BusinessKey` | Type, age, franchise code/name; **không là borrower ID** | CSV prototype đã sinh; DDL có |
| `DimLoanProfile` | Dimension profile | Tổ hợp các đặc tính/trạng thái | PK `LoanProfileKey` | Program, method, rate type, revolving, collateral, secondary market, status | CSV prototype đã sinh; DDL có |

`GrossApproval`, `SBAGuaranteedApproval`, `UnguaranteedApproval`, `GrossChargeOffAmount`, `JobsSupported`, count flags là additive **trong một snapshot**. Rate, term và tỷ lệ là non-additive; nhiều snapshot sẽ không được cộng số tiền/count xuyên `AsOfDate`. Xem [docs/02_warehouse_design.md](docs/02_warehouse_design.md). Một snapshot không cung cấp lịch sử để mặc định áp dụng SCD Type 2.

## 5. Data Processing Architecture

Các dòng Python/SQL/SSAS bên dưới ghi **tình trạng previous prototype**. [Preprocessing Plan hiện hành](docs/data_understanding/preprocessing_plan.md) vẫn `PLANNED / NOT IMPLEMENTED`; không gọi bước trim/parse của prototype là cleaned dataset theo rule Q1–Q15.

`Raw Data → Data Profiling → Data Cleaning → Data Transformation → ETL/ELT → Data Warehouse → OLAP → BI/Dashboard`

| Giai đoạn | Mục đích; input → output | Công nghệ / file | Trạng thái thực tế |
|---|---|---|---|
| Raw Data | Giữ CSV và XLSX gốc bất biến | [data/raw/foia](data/raw/foia/README.md) | **Có** file cục bộ |
| Data Profiling | Schema, count, null, status, FY, quality | [docs/data_profile.json](docs/data_profile.json), [src/main.py](src/main.py) | **Đã chạy** theo [docs/validation.md](docs/validation.md); kết quả có thể tái kiểm tra |
| Cleaning trong previous prototype | Trim, chuẩn hóa status, parse date/numeric, gắn cờ sai theo logic cũ | [src/main.py](src/main.py); `data/processed/quality_issues.csv` | **Có prototype Python**; không sửa raw; preprocessing hiện hành chưa triển khai |
| Transformation | Sinh dimensions, fact, mart, mining input | [src/main.py](src/main.py), `data/processed/` | **Đã sinh CSV cục bộ**; thư mục processed bị Git ignore |
| ETL/ELT chính thức | Nạp raw qua staging, dimension/fact và audit | [docs/03_implementation.md](docs/03_implementation.md), `Source/SSIS/` | **Mới là hướng dẫn**; chưa có `.dtproj`/`.dtsx` |
| Data Warehouse | Lưu bảng có PK/FK, đối soát | [sql/01_warehouse.sql](sql/01_warehouse.sql), [sql/02_validation.sql](sql/02_validation.sql) | **Có script**; chưa có bằng chứng DDL đã chạy/nạp database |
| OLAP | Cube, measures, hierarchies, MDX | `Source/SSAS/`, [docs/04_analysis_catalog.md](docs/04_analysis_catalog.md) | **Có MDX và thiết kế**; chưa có `.dwproj`, cube đã process hoặc kết quả chạy MDX |
| BI/Dashboard | Trực quan hóa và Pivot | [docs/05_bi_mining.md](docs/05_bi_mining.md), `dashboards/`, `Source/Excel/` | **Có đặc tả**; chưa có PBIX, link Looker, workbook Pivot thật |

## 6. Technology Stack

| Công nghệ | Mức xác nhận | Bằng chứng / vai trò |
|---|---|---|
| Python, pandas | **Confirmed trong prototype** | [src/main.py](src/main.py), [requirements.txt](requirements.txt); đọc CSV, profile, sinh bảng CSV. |
| scikit-learn | **Confirmed trong baseline** | [src/mining.py](src/mining.py), [docs/mining_baseline.json](docs/mining_baseline.json). |
| Git | **Confirmed** | Repository có lịch sử commit; dùng theo dõi mã/tài liệu. |
| SQL Server / T-SQL | **Proposed target, script đã viết** | [sql/01_warehouse.sql](sql/01_warehouse.sql); chưa có bằng chứng database vận hành. |
| SSIS, SSAS Multidimensional, MDX | **Proposed target / MDX đã viết** | [docs/03_implementation.md](docs/03_implementation.md), `Source/SSAS/`; chưa có project/deploy. |
| Power BI, Looker Studio, Excel Pivot | **Proposed** | [docs/05_bi_mining.md](docs/05_bi_mining.md), [docs/04_analysis_catalog.md](docs/04_analysis_catalog.md); chưa có artifact chạy thật. |
| Hệ quản trị/công cụ cuối cùng và phiên bản | **Chưa được người dùng xác nhận rõ** | Repo chọn hướng SQL Server + SSIS/SSAS; cần đối chiếu yêu cầu môn học/môi trường trước khi triển khai. |

## 7. Repository Structure

```text
README.md                 Tổng quan và trạng thái
PROJECT_CONTEXT.md        Bối cảnh, kiến trúc, quy ước tương đối ổn định
PROJECT_STATUS.md         Tiến độ, blockers, quyết định chờ xác nhận
data/raw/foia/            CSV SBA 7(a) + workbook dictionary gốc
data/staging/             Vị trí dữ liệu trung gian dự kiến
data/processed/           CSV prototype fact/dimension/mart/mining cục bộ, Git ignore
docs/                    Feasibility, warehouse, implementation, catalog, BI, profile, validation
src/                     Python chuẩn bị snapshot và baseline mining
sql/                     DDL SQL Server và câu đối soát
tests/                   Kiểm tra pipeline Python
Source/SSIS/              Hướng dẫn; project thật chưa có
Source/SSAS/              MDX mẫu; project cube chưa có
Source/Excel/             Hướng dẫn Pivot; workbook thật chưa có
Source/DataMining/        Hướng dẫn baseline
dashboards/               Đặc tả báo cáo, chưa có dashboard artifact
Database/ Document/ Video/  Vị trí dự kiến cho bộ nộp
references/               PDF đồ án cũ để tham khảo cấu trúc
```

Không có notebook `.ipynb` hiện hành trong working tree. `references/` là tài liệu tham khảo, không phải bằng chứng hệ thống SBA đã hoạt động.

## 8. Important Project Decisions

| Decision | Reason | Evidence | Status |
|---|---|---|---|
| Dùng SBA 7(a) FOIA FY2020–FY2026 snapshot 2026-06-30 cho phạm vi hiện tại | File thực có, phù hợp câu hỏi đa chiều | [README.md](README.md), [data/raw/foia/README.md](data/raw/foia/README.md) | **Phạm vi được người dùng nêu và repo thể hiện** |
| Giữ raw nguyên vẹn; không loại dòng giống nhau thiếu bằng chứng | Nguồn không có LoanID; profiling raw exact ghi 687 dòng trong nhóm trùng, 391 bản sao dư. Số 392 của prototype dùng cách chuẩn hóa khác. | [src/main.py](src/main.py), [profiling hiện hành](docs/data_understanding/data_profiling_report.md) | **Quy tắc prototype đã triển khai; số liệu cần phân biệt phương pháp** |
| Candidate `FactLoanSnapshot` ở grain một published record trong một snapshot | Tránh gán sai LoanID hoặc cộng trùng nhiều snapshot | [candidate schema](docs/dimensional_model/candidate_schema.md), [current Q1–Q15](docs/business_requirements/business_questions_current.md) | **Grain giữ nguyên trong Target Schema Proposal**; prototype cũ cũng ở grain dòng nguồn |
| Một fact, tám dimension, hai nhánh snowflake | Có phụ thuộc State→County và Sector→Industry | [sql/01_warehouse.sql](sql/01_warehouse.sql) | **Thiết kế repo đã viết, chưa triển khai DB** |
| Tỷ lệ tính từ tổng tử/mẫu số; status theo snapshot | Tránh sai lệch roll-up và nhầm cohort với lịch sử status | [docs/02_warehouse_design.md](docs/02_warehouse_design.md) | **Quy tắc phân tích trong repo** |
| Target Schema Proposal star `FactLoanSnapshot` + 8 Dim, gồm `DimTermBand`, `DimLoanStatus`, `DimBusiness` riêng | Bao phủ Q1–Q15, trong đó Q10 dùng business profile, theo [matrix](docs/dimensional_model/measure_dimension_matrix.md) | [candidate schema](docs/dimensional_model/candidate_schema.md) | **Lựa chọn logic đã duyệt, PROPOSED**, chưa có trong DDL/code |
| Population, cấp NAICS Sector, TermBand tách 120, canonical PIF, Q15 gates 30/5 | Giữ population nhất quán và filter context Q11–Q15; sector reference vẫn chưa xác minh | [rule register](docs/business_requirements/business_rule_register.md), [Measure Contract](docs/business_requirements/measure_contract_q1_q15.md) | **PROJECT_APPROVED** ở cấp phân tích; **PENDING_VERIFICATION** NAICS reference/version/mapping; chưa triển khai |
| Bổ sung FY2010–FY2019 | Tăng thời gian quan sát cohort cũ | Được thảo luận; chưa có file trong repo | **Tùy chọn, chưa chốt** |

## 9. Data Limitations & Analytical Considerations

| Giới hạn có cơ sở | Hệ quả khi phân tích |
|---|---|
| FY2026 mới đến 2026-06-30 | So FYTD cùng 9 tháng hoặc tách khỏi so sánh năm đủ. |
| Không có public LoanID; `LocationID` là lender ID | `LoanCount` là số dòng; không xác định chắc số khoản vay/doanh nghiệp duy nhất hay nối xuyên snapshot. |
| 687 dòng trong 296 nhóm exact duplicate trên chuỗi raw, 391 bản sao dư; số 689/392 ở profile prototype dùng phương pháp chuẩn hóa khác | Không tự xóa/khẳng định là cùng khoản vay; dùng số raw exact khi mô tả snapshot hiện hành. |
| Snapshot đơn lẻ | `LoanStatus` là trạng thái tại 2026-06-30, không có chuỗi chuyển trạng thái hay dư nợ theo thời gian. |
| `GrossApproval` và `SBAGuaranteedApproval` khác bản chất | Phê duyệt ≠ giải ngân/dư nợ; bảo lãnh ≠ số tiền SBA đã trả. |
| `GrossChargeOffAmount` là gộp | Không phải tổn thất ròng sau thu hồi, không phải lợi nhuận/LGD. |
| `JobsSupported` lender tự khai | Không phải số người duy nhất/tác động nhân quả. |
| Cần thời gian theo dõi tương đồng cho outcome | Cohort mới dễ có `EXEMPT`/`COMMIT` và ít sự kiện kết thúc; resolved rate có selection/censoring bias. |
| Thiếu `FirstDisbursementDate` 71.186 dòng | Trung bình thời gian giải ngân chỉ tính trên ngày hợp lệ và kèm mẫu số. |
| `SoldSecMrktInd` có 116.764 `Y`, 271.574 blank, không có `N` trong CSV đã khảo sát | Chỉ xác nhận số dòng có `Y`; blank không đồng nghĩa không bán; không tính tỷ lệ bán thực. |
| Ngày/lãi suất/kỳ hạn bất thường | Quality log có 22 charge-off dates và 2 paid-in-full dates ngoài khoảng, 5 CHGOFF thiếu ngày, 87 rate bằng 0, 11 kỳ hạn bằng 0; không âm thầm sửa. |

## 10. Project Conventions

| Chủ đề | Quy ước hiện có / chưa xác định |
|---|---|
| Naming | Target Schema Proposal dùng `FactLoanSnapshot`, `DimDate`, `DimProjectGeography`, `DimIndustry`, `DimLender`, `DimLoanProfile`, `DimLoanStatus`, `DimTermBand`, `DimBusiness` theo [schema hiện hành](docs/dimensional_model/candidate_schema.md). Một số tên trùng CSV/DDL của [previous prototype](sql/01_warehouse.sql), nhưng cấu trúc và khóa khác; chưa có physical naming contract được triển khai. |
| Folders | `data/raw/foia/` giữ nguồn; `data/staging/` trung gian; `data/processed/` output prototype, bị Git ignore; `docs/` mô tả và chứng cứ. |
| Processing | Previous prototype dùng full rebuild **một snapshot**. [Preprocessing Plan hiện hành](docs/data_understanding/preprocessing_plan.md) mới `PLANNED / NOT IMPLEMENTED`; raw vẫn bất biến, giữ mã số 0 đầu, dòng giống nhau và quality audit. |
| SQL | Script hiện viết cho SQL Server trong schema `dwh`, `staging`, `marts`; PK/FK theo [sql/01_warehouse.sql](sql/01_warehouse.sql). Quy ước transaction, incremental load và deployment chính thức: **chưa xác định**. |
| Documentation | Phân biệt thiết kế/script/prototype đã chạy với hệ thống đã deploy; ghi snapshot, grain, mẫu số và nguồn kiểm chứng cho KPI. Cập nhật bối cảnh ở file này khi có quyết định được chốt; cập nhật tiến độ ở [PROJECT_STATUS.md](PROJECT_STATUS.md). |
