# Trạng thái hiện hành — SBA 7(a)

Cập nhật **2026-10-02**, đồng bộ [Chương 1 mới nhất](../project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx). Report là nguồn chính cho nội dung nhóm trình bày; code/DDL/output là bằng chứng implementation. Khi khác nhau, giữ hai mức xác nhận và Open Issues, không ép code/schema khớp report.

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
| Preprocessing | [preprocessing_plan.md](../docs/data_understanding/preprocessing_plan.md) | Report mô tả hoàn tất; artifact checkout chưa có |
| Diagram DBML | [candidate_schema.dbml](../diagram/candidate_schema.dbml) | Proposal, còn lệch datatype; không là physical authority |
| SQL schema hiện có | [01_warehouse.sql](../sql/01_warehouse.sql), [02_validation.sql](../sql/02_validation.sql) | Canonical implementation **prototype cũ**, không schema đích hiện hành |
| Python hiện có | [src/main.py](../src/main.py) | Prototype snowflake; không notebook preprocessing của report |

## Dataset và scope

388.338 published records × 42 source fields; một snapshot 2026-06-30, ApprovalDate 2019-10-01..2026-06-30, FY2020–FY2026. FY2026 partial; Q6 so cùng kỳ Oct–Jun. Không có public unique LoanID; LocationID là lender. Giữ 687 records/296 nhóm exact raw duplicates (391 copies dư); số 689/392 trong lịch sử dùng normalization khác. Raw bất biến, không suy 1 record=1 unique loan.

## Trạng thái theo tầng bằng chứng

| Nội dung | Trạng thái sau đồng bộ | Giới hạn |
|---|---|---|
| Chương 1 | REPORT_PRESENT | Đã đọc toàn bộ text/tables; không sửa DOCX |
| Logical model | REPORT_ALIGNED — 1 Fact_Loan + 8 Dim_* | Proposal trong report; không physical/deployed |
| Q1–Q15 / measures | DOCUMENTED / WAREHOUSE_NOT_IMPLEMENTED | Nội dung khớp §1.3.6; chi tiết công thức kế thừa Measure Contract |
| Preprocessing | REPORT_DOCUMENTED_COMPLETED / CHECKOUT_UNVERIFIED | Report có kết quả 388.338×38; notebook/module/output tương ứng chưa tìm thấy |
| TermBand / canonical PIF | Report mô tả đã làm bằng Python | Warehouse Dim/FK chưa materialize, không khẳng định toàn bộ preprocessing mới đã chạy trong repo |
| NAICS | CANDIDATE_UNVERIFIED / PENDING_VERIFICATION | Cấp sector đã chọn; reference/version/crosswalk chưa verified |
| Python/SQL/CSV cũ | PREVIOUS PROTOTYPE — DEPRECATED AS CURRENT | Snowflake FactLoanSnapshot, giữ code và artifact lịch sử |
| SSIS / SQL target / SSAS / BI | Chưa có artifact/bằng chứng triển khai target trong checkout | Task này chưa thực hiện Chương 2 hoặc package |

## Open Issues report và implementation

| ID | Report / quyết định hiện tại | Checkout / khác biệt | Khả năng nguyên nhân và bước cần làm | Status |
|---|---|---|---|---|
| OI-01 | Fact_Loan / LoanKey + 8 Dim_* (bảng 1.4–1.12) | Python/DDL FactLoanSnapshot / LoanRowKey, snowflake DimState/County và DimSector/Industry; status nằm LoanProfile, business có franchise, nhiều date roles | Prototype trước khi report đổi model; đặc tả mapping/physical schema mới trong task sau | OPEN |
| OI-02 | Python preprocessing hoàn tất, 388.338×38, TSV/clean CSV, notebook/script SHA-256 match (§1.2.2) | Không tìm thấy 01_preprocessing.ipynb, module preprocess, sba7a_standardized.tsv, _clean.csv, manifest/reconciliation tương ứng | Có thể artifact nằm ngoài repo hoặc report kế thừa tài liệu nguồn; cần đưa đúng artifact vào repo và tái kiểm, không kết luận chưa từng chạy | CHECKOUT_UNVERIFIED |
| OI-03 | 18 retained source columns + derived/lookup/DQ = 38 output; model tham chiếu 32 nguồn | Chưa có header contract 38 cột và dimension lookup artifacts; Hình 1.23 đánh DROP BankStreet/FDIC/NCUA/address, CongressionalDistrict/SBADistrictOffice, các event dates và thuộc tính profile bổ sung nhưng model vẫn tham chiếu; chưa có lookup artifacts để chứng minh mapping đầy đủ | Report phân biệt retained/output/source reference; kiểm header và lookup trước SSIS, không tự suy danh sách 18/38 | OPEN |
| OI-04 | §1.2.2.4 DECIMAL(18,3), 2 records cần 3dp; bảng Fact ghi DECIMAL | DBML và SVG decimal(19,2); hình schema report cũng mang precision cũ; SQL cũ decimal(24,6) không cùng contract nhưng giữ được 3dp | Diagram chưa cập nhật khi merge preprocessing; chốt contract precision/scale trong task physical mapping. Không sửa DDL/DBML structure ở đây | OPEN |
| OI-05 | Bảng 1.10 và 1.12 TermBandKey BIGINT | DBML và hình 1.30 int ở dimension và FK | Logical table / diagram không đồng bộ; review type thống nhất trong task schema | OPEN |
| OI-06 | SourceFileID + SourceRecordOrdinal; SourceRowNumber vật lý riêng | Prototype chỉ index+2 đặt tên SourceRowNumber, không đúng dòng vật lý khi 16 records multiline | Prototype dùng ordinal offset; đặc tả lineage đúng parser, giữ checksum và mapping source record | OPEN |
| OI-07 | Sector candidate CANDIDATE_UNVERIFIED (§1.2.2.4); reference/version còn cần xác minh (§1.3.5) | Prototype lấy prefix có dải gộp; chưa có verified reference/crosswalk | Candidate prefix không chứng minh vintage; xác minh trước kết quả chính thức Q13/Q15 | PENDING_VERIFICATION |
| OI-08 | PK/FK/type logic trong report | Length/nullability/identity/UNIQUE/Unknown/SCD, tie order và full business keys chưa đầy đủ | Report Chương 1 không phải physical spec; giữ OPEN và đặc tả trước DDL/SSIS | OPEN |

## Điều kiện tiếp tục Chương 2

Documentation đủ làm context cho **đặc tả ETL/SSIS**. Để triển khai/nạp cần giải quyết OI-02/03 (artifact/input/lookup contract), OI-04/05 (datatype), OI-06/08 (lineage/physical keys). NAICS candidate giữ nguyên trạng thái cho đến xác minh OI-07. Bước tiếp theo là review Source-to-Target Mapping và reconciliation từ input thực tế; chưa chạy SQL/SSIS/cube trong task này.

## Quy ước bằng chứng

REPORT_DOCUMENTED_COMPLETED = report mô tả đã hoàn tất, không phải đã tái kiểm trong checkout; CHECKOUT_UNVERIFIED = thiếu artifact để tái kiểm, không kết luận chưa từng thực hiện. PROJECT_APPROVED = quyết định dự án, không quy tắc SBA. PENDING_VERIFICATION = thiếu nguồn xác minh. OPEN = thiếu contract/quyết định. WAREHOUSE_NOT_IMPLEMENTED = chưa thấy target artifacts/bằng chứng thực thi. Các snapshot archived không thay trạng thái này.
