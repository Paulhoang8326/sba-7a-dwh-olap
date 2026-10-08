# Trạng thái hiện hành — SBA 7(a)

Cập nhật **2026-10-08**, sau khi tích hợp chọn lọc và kiểm chứng Phase 1 theo [Chương 1 mới nhất](../project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx). Report là nguồn chính cho nội dung nhóm trình bày; code/DDL/output là bằng chứng implementation. Khi khác nhau, giữ hai mức xác nhận và Open Issues, không ép code/schema khớp report.

## Canonical project files

| Vai trò | File thực tế | Trạng thái |
|---|---|---|
| Báo cáo nhóm | [Chương 1 mới nhất](../project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx) | Nguồn chính cho nội dung báo cáo; không sửa DOCX |
| Context ngắn | [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) | Context đọc trước cho task sau |
| Trạng thái / Open Issues | [docs/00_current_status.md](../docs/00_current_status.md) | Phân biệt report, checkout và triển khai |
| Mô hình logic / field contract | [candidate_schema.md](../docs/dimensional_model/candidate_schema.md) | Fact_Loan + 8 Dim_* theo bảng report |
| Q1–Q15 | [business_questions_current.md](../docs/business_requirements/business_questions_current.md) | Canonical nội dung; bảng 1.14 report là nguồn đối chiếu |
| Measures / KPI | [measure_contract_q1_q15.md](../docs/business_requirements/measure_contract_q1_q15.md) | Công thức logic, chưa chạy warehouse |
| Coverage | [measure_dimension_matrix.md](../docs/dimensional_model/measure_dimension_matrix.md) | 8 dimensions bao phủ Q1–Q15 |
| Business rules | [business_rule_register.md](../docs/business_requirements/business_rule_register.md) | Rule dự án; NAICS mapping chưa verified |
| Dataset / profiling / DQ | [overview](../docs/data_understanding/data_overview.md), [profiling](../docs/data_understanding/data_profiling_report.md), [quality](../docs/data_understanding/data_quality_report.md) | Baseline nguồn, không là standardized output |
| Dictionary | [định nghĩa nguồn](../docs/data_dictionary.md), [diễn giải Việt](../docs/data_understanding/data_dictionary.md) | Hai vai trò bổ sung, không phải hai schema đích |
| Preprocessing | [preprocessing_plan.md](../docs/data_understanding/preprocessing_plan.md), [integration audit](etl/preprocessing_integration_audit.md) | Code/notebook/reports đã tích hợp; LFS output đã kiểm trong Git cache, chưa checkout vào staging |
| Diagram DBML | [candidate_schema.dbml](../diagram/candidate_schema.dbml) | Proposal, còn lệch datatype; không là physical authority |
| SQL schema hiện có | [01_warehouse.sql](../sql/01_warehouse.sql), [02_validation.sql](../sql/02_validation.sql) | Canonical implementation **prototype cũ**, không schema đích hiện hành |
| Python hiện có | [preprocess.py](../src/etl/preprocess.py), [notebook](../notebooks/01_preprocessing.ipynb); [src/main.py](../src/main.py) | Hai file đầu là Phase 1 mới; `src/main.py` là prototype snowflake cũ |

## Dataset và scope

388.338 published records × 42 source fields; một snapshot 2026-06-30, ApprovalDate 2019-10-01..2026-06-30, FY2020–FY2026. FY2026 partial; Q6 so cùng kỳ Oct–Jun. Không có public unique LoanID; LocationID là lender. Giữ 687 records/296 nhóm exact raw duplicates (391 copies dư); số 689/392 trong lịch sử dùng normalization khác. Raw bất biến, không suy 1 record=1 unique loan.

## Trạng thái theo tầng bằng chứng

| Nội dung | Trạng thái sau đồng bộ | Giới hạn |
|---|---|---|
| Chương 1 | REPORT_PRESENT | Đã đọc toàn bộ text/tables; không sửa DOCX |
| Logical model | REPORT_ALIGNED — 1 Fact_Loan + 8 Dim_* | Proposal trong report; không physical/deployed |
| Q1–Q15 / measures | DOCUMENTED / WAREHOUSE_NOT_IMPLEMENTED | Nội dung khớp §1.3.6; chi tiết công thức kế thừa Measure Contract |
| Preprocessing | CODE_INTEGRATED / TSV_REPRODUCED | Code/notebook/reports có trong branch; raw và hai output LFS kiểm hash/header/shape/totals; TSV tái lập đúng SHA-256. Full `run()`/pytest chưa chạy vì giới hạn dependency và clean CSV chứa `Borr*`. |
| TermBand / canonical PIF | Code và direct rule assertions khớp report | Warehouse Dim/FK chưa materialize; không suy Phase 1 là SSIS đã chạy |
| NAICS | CANDIDATE_UNVERIFIED / PENDING_VERIFICATION | Cấp sector đã chọn; reference/version/crosswalk chưa verified |
| Python/SQL/CSV cũ | PREVIOUS PROTOTYPE — DEPRECATED AS CURRENT | Snowflake FactLoanSnapshot, giữ code và artifact lịch sử |
| SSIS / SQL target / SSAS / BI | Chưa có artifact/bằng chứng triển khai target trong checkout | Task này chưa thực hiện Chương 2 hoặc package |

## Open Issues report và implementation

| ID | Report / quyết định hiện tại | Checkout / khác biệt | Khả năng nguyên nhân và bước cần làm | Status |
|---|---|---|---|---|
| OI-01 | Fact_Loan / LoanKey + 8 Dim_* (bảng 1.4–1.12) | Python/DDL FactLoanSnapshot / LoanRowKey, snowflake DimState/County và DimSector/Industry; status nằm LoanProfile, business có franchise, nhiều date roles | Prototype trước khi report đổi model; đặc tả mapping/physical schema mới trong task sau | OPEN |
| OI-02 | Python preprocessing hoàn tất, 388.338×38, TSV/clean CSV, notebook/script SHA-256 match (§1.2.2) | Code/notebook/reports đã có; LFS objects kiểm trực tiếp; TSV tái lập cùng SHA-256 và 18/18 đối soát pass. Full `run()`/pytest chưa tái kiểm do clean CSV chứa `Borr*` và thiếu pytest. | Xem [integration audit](etl/preprocessing_integration_audit.md); không gọi full test suite pass. | PARTIALLY_VERIFIED |
| OI-03 | 18 retained source columns + derived/lookup/DQ = 38 output; model tham chiếu 32 nguồn | Header 38 cột và 18 KEEP đã xác minh; nhưng event dates, district/lender/profile attributes vẫn vắng TSV, chỉ có ở raw/clean CSV. | Chốt Source-to-Target Mapping và đường bổ sung nguồn/lookup cho 8 Dim trước SSIS; không tự sửa schema. | OPEN |
| OI-04 | §1.2.2.4 DECIMAL(18,3), 2 records cần 3dp; bảng Fact ghi DECIMAL | DBML và SVG decimal(19,2); hình schema report cũng mang precision cũ; SQL cũ decimal(24,6) không cùng contract nhưng giữ được 3dp | Diagram chưa cập nhật khi merge preprocessing; chốt contract precision/scale trong task physical mapping. Không sửa DDL/DBML structure ở đây | OPEN |
| OI-05 | Bảng 1.10 và 1.12 TermBandKey BIGINT | DBML và hình 1.30 int ở dimension và FK | Logical table / diagram không đồng bộ; review type thống nhất trong task schema | OPEN |
| OI-06 | SourceFileID + SourceRecordOrdinal; SourceRowNumber vật lý riêng | Prototype chỉ index+2 đặt tên SourceRowNumber, không đúng dòng vật lý khi 16 records multiline | Prototype dùng ordinal offset; đặc tả lineage đúng parser, giữ checksum và mapping source record | OPEN |
| OI-07 | Sector candidate CANDIDATE_UNVERIFIED (§1.2.2.4); reference/version còn cần xác minh (§1.3.5) | Preprocessing mới lấy prefix có dải gộp và gắn `CANDIDATE_UNVERIFIED`; chưa có verified reference/crosswalk | Candidate prefix không chứng minh vintage; xác minh trước kết quả chính thức Q13/Q15 | PENDING_VERIFICATION |
| OI-08 | PK/FK/type logic trong report | Length/nullability/identity/UNIQUE/Unknown/SCD, tie order và full business keys chưa đầy đủ | Report Chương 1 không phải physical spec; giữ OPEN và đặc tả trước DDL/SSIS | OPEN |
| OI-09 | Notebook che `Borr*` khi hiển thị | Clean CSV LFS trên remote vẫn giữ `Borr*`; branch này không checkout/commit lại file đó | Kiểm phạm vi truy cập/phát hành trước full pipeline/test hoặc tích hợp clean CSV | OPEN |

## Điều kiện tiếp tục Chương 2

Đã có code, header và đối soát TSV đủ làm context cho **thiết kế ETL/SSIS**. Để dựng package/nạp cần giải quyết OI-03 (field/lookup contract), OI-04/05 (datatype), OI-06/08 (lineage/physical keys), OI-09 (clean CSV) và phần test còn lại của OI-02. NAICS candidate giữ nguyên trạng thái đến khi xác minh OI-07. [Audit 38 cột](etl/preprocessing_integration_audit.md) là gap triage, chưa là Source-to-Target Mapping cuối cùng; chưa chạy SQL/SSIS/cube.

## Quy ước bằng chứng

CODE_INTEGRATED = source/report artifact đã vào branch; TSV_REPRODUCED = đã tái tạo TSV cùng SHA-256 từ raw mà không ghi clean CSV; PARTIALLY_VERIFIED = còn giới hạn full run/test. PROJECT_APPROVED = quyết định dự án, không quy tắc SBA. PENDING_VERIFICATION = thiếu nguồn xác minh. OPEN = thiếu contract/quyết định. WAREHOUSE_NOT_IMPLEMENTED = chưa thấy target artifacts/bằng chứng thực thi. Các snapshot archived không thay trạng thái này.
