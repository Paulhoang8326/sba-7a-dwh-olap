# Trạng thái hiện hành — SBA 7(a)

Cập nhật **2026-10-10**: **CHAPTER 1 READY TO FREEZE** trong phạm vi đồ án IS217. [Report Chương 1](../project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx) giữ nguyên; DBML đã thống nhất money/TermBandKey. Input SSIS 52 cột đã tạo và kiểm trên đủ 388.338 records. Tiếp theo là [triển khai Chương 2](etl/chapter2_ssis_plan.md); chưa có database/package target chạy thật.

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
| Input và kế hoạch Chương 2 | [chapter2_ssis_plan.md](etl/chapter2_ssis_plan.md), [prepare_ssis_input.py](../src/etl/prepare_ssis_input.py) | Một TSV local 52 cột; kiểm count, từng record, totals và projection checksum |
| Diagram DBML | [candidate_schema.dbml](../diagram/candidate_schema.dbml) | Khớp bảng report; money (18,3), TermBandKey BIGINT; chưa là deployed DDL |
| SQL schema hiện có | [01_warehouse.sql](../sql/01_warehouse.sql), [02_validation.sql](../sql/02_validation.sql) | Canonical implementation **prototype cũ**, không schema đích hiện hành |
| Python hiện có | [preprocess.py](../src/etl/preprocess.py), [notebook](../notebooks/01_preprocessing.ipynb); [src/main.py](../src/main.py) | Hai file đầu là Phase 1 mới; `src/main.py` là prototype snowflake cũ |

## Dataset và scope

388.338 published records × 42 source fields; một snapshot 2026-06-30, ApprovalDate 2019-10-01..2026-06-30, FY2020–FY2026. FY2026 partial; Q6 so cùng kỳ Oct–Jun. Không có public unique LoanID; LocationID là lender. Giữ 687 records/296 nhóm exact raw duplicates (391 copies dư); số 689/392 trong lịch sử dùng normalization khác. Raw bất biến, không suy 1 record=1 unique loan.

## Trạng thái theo tầng bằng chứng

| Nội dung | Trạng thái sau đồng bộ | Giới hạn |
|---|---|---|
| Chương 1 | CHAPTER 1 READY TO FREEZE | Không có lỗi nghiêm trọng buộc sửa DOCX; hình schema cũ còn type annotations đã được đính chính ở DBML/ghi chú Chương 2 |
| Logical model | REPORT_ALIGNED — 1 Fact_Loan + 8 Dim_* | Proposal trong report; không physical/deployed |
| Q1–Q15 / measures | DOCUMENTED / WAREHOUSE_NOT_IMPLEMENTED | Nội dung khớp §1.3.6; chi tiết công thức kế thừa Measure Contract |
| Preprocessing | CODE_INTEGRATED / TSV_REPRODUCED | Code/notebook/reports có trong branch; raw và hai output LFS kiểm hash/header/shape/totals; TSV tái lập đúng SHA-256. Full `run()`/pytest chưa chạy vì giới hạn dependency và clean CSV chứa `Borr*`. |
| TermBand / canonical PIF | Code và direct rule assertions khớp report | Warehouse Dim/FK chưa materialize; không suy Phase 1 là SSIS đã chạy |
| Input Chương 2 | GENERATED / VALIDATED — 388.338 × 52 | 6 unittest pass; full-data exporter pass; 38-column projection cùng checksum baseline; không xuất Borr* hoặc clean CSV mới |
| NAICS | CANDIDATE_UNVERIFIED / PENDING_VERIFICATION | Cấp sector đã chọn; reference/version/crosswalk chưa verified |
| Python/SQL/CSV cũ | PREVIOUS PROTOTYPE — DEPRECATED AS CURRENT | Snowflake FactLoanSnapshot, giữ code và artifact lịch sử |
| SSIS / SQL target / SSAS / BI | Chưa có artifact/bằng chứng triển khai target trong checkout | Task này chưa thực hiện Chương 2 hoặc package |

## Open Issues report và implementation

| ID | Report / quyết định hiện tại | Checkout / khác biệt | Khả năng nguyên nhân và bước cần làm | Status |
|---|---|---|---|---|
| OI-01 | Fact_Loan / LoanKey + 8 Dim_* (bảng 1.4–1.12) | Python/DDL FactLoanSnapshot / LoanRowKey, snowflake DimState/County và DimSector/Industry; status nằm LoanProfile, business có franchise, nhiều date roles | Prototype trước khi report đổi model; đặc tả mapping/physical schema mới trong task sau | OPEN |
| OI-02 | Python preprocessing hoàn tất, 388.338×38, TSV/clean CSV, notebook/script SHA-256 match (§1.2.2) | Code/notebook/reports đã có; LFS objects kiểm trực tiếp; TSV tái lập cùng SHA-256 và 18/18 đối soát pass. Full `run()`/pytest chưa tái kiểm do clean CSV chứa `Borr*` và thiếu pytest. | Xem [integration audit](etl/preprocessing_integration_audit.md); không gọi full test suite pass. | PARTIALLY_VERIFIED |
| OI-03 | TSV Chương 1 giữ 38 cột; target dùng 32 source attrs | Input riêng Chương 2 nối đúng 14 trường, giữ record order và toàn bộ 38 cột đầu | Dùng file 52 cột cho SSIS; không cần enrichment JOIN | RESOLVED — INPUT |
| OI-04 | §1.2.2.4 DECIMAL(18,3), hai values 3dp | DBML đã đổi ba money measures thành (18,3); full source fits chính xác | Hình schema cũ trong DOCX/SVG còn annotation (19,2); dùng DBML và chú thích datatype ở Chương 2. Không đổi model/business content | RESOLVED — TECHNICAL; image note retained |
| OI-05 | Bảng 1.10 và 1.12 TermBandKey BIGINT | DBML PK/FK đã BIGINT | Hình cũ còn INT; triển khai theo bảng report và DBML đã thống nhất | RESOLVED — TECHNICAL; image note retained |
| OI-06 | SourceFileID + SourceRecordOrdinal; SourceRowNumber vật lý riêng | Input 52 cột giữ source/ordinal, không xuất physical line | Kế hoạch load đầu để SourceRowNumber NULL; không gán ordinal+1. Có thể bổ sung raw parser start-line sau nếu cần | CHAPTER 2 IMPLEMENTATION |
| OI-07 | Sector candidate CANDIDATE_UNVERIFIED (§1.2.2.4); reference/version còn cần xác minh (§1.3.5) | Preprocessing mới lấy prefix có dải gộp và gắn `CANDIDATE_UNVERIFIED`; chưa có verified reference/crosswalk | Candidate prefix không chứng minh vintage; xác minh trước kết quả chính thức Q13/Q15 | PENDING_VERIFICATION |
| OI-08 | PK/FK/type logic trong report | Full composite keys đã có trong kế hoạch; lengths/NULL/seed cần cụ thể khi viết DDL | Full reload một snapshot và kiểm lookup errors là đủ đồ án; không cần SCD2/CDC/production audit | CHAPTER 2 IMPLEMENTATION |
| OI-09 | Notebook che `Borr*` khi hiển thị | Clean CSV remote vẫn có Borr*; input 52 cột không có | SSIS dùng TSV allowlist local, không cần clean CSV. Quyền chia sẻ raw/clean tiếp tục tách riêng | NOT BLOCKING SSIS INPUT |

## Điều kiện tiếp tục Chương 2

Có thể chuyển sang dựng database và package theo [kế hoạch Chương 2](etl/chapter2_ssis_plan.md). Chốt widths/Unicode, helper NULL và seed labels khi viết DDL/Data Flow, không cần kéo dài audit Chương 1. NAICS vẫn candidate; xác minh reference trước khi công bố kết quả sector chính thức Q13/Q15. Q1–Q15 và business rules không đổi.

Kết quả 2026-10-10: TSV 52 cột **217.379.346 bytes**, SHA-256 `8d082d3ef52cc81d023726b58b93d6408a6f2c17226a168da27d1dcb9d0ca56d`; projection 38 cột SHA-256 `837723fb7b6b8358ce4aaf4855ea396b197104660babbe6d6d9f6a6be3a78bc5`. Tổng measures và từng record khớp, script kiểm DECIMAL(18,3) chứa chính xác mọi money value. Manifest/output lớn chỉ lưu local và ignore.

## Quy ước bằng chứng

CODE_INTEGRATED = source/report artifact đã vào branch; TSV_REPRODUCED = đã tái tạo TSV cùng SHA-256 từ raw mà không ghi clean CSV; PARTIALLY_VERIFIED = còn giới hạn full run/test. PROJECT_APPROVED = quyết định dự án, không quy tắc SBA. PENDING_VERIFICATION = thiếu nguồn xác minh. OPEN = thiếu contract/quyết định. WAREHOUSE_NOT_IMPLEMENTED = chưa thấy target artifacts/bằng chứng thực thi. Các snapshot archived không thay trạng thái này.
