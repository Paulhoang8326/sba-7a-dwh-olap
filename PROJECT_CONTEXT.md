# PROJECT_CONTEXT — SBA 7(a) theo Chương 1 hiện hành

Cập nhật **2026-10-02**. Đọc file này trước task tiếp theo. [Chương 1 mới nhất](project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx) là nguồn chính cho nội dung nhóm trình bày; [trạng thái và Open Issues](docs/00_current_status.md) phân biệt nội dung báo cáo với implementation. Không dùng tên FactLoanSnapshot/DimDate của prototype làm tên schema hiện hành.

## 1. Project Overview

Đề tài: **Xây dựng hệ thống kho dữ liệu và OLAP hỗ trợ phân tích danh mục tín dụng, bảo lãnh và kết quả khoản vay SBA 7(a) tại Hoa Kỳ giai đoạn FY2020–FY2026**. IS217, nhóm 19: Hoàng Khôi Nguyên (24521176), Phan Thế Hiển (24520479). Mục tiêu: tổ chức dữ liệu đa chiều thống nhất grain, measures và population để phân tích vốn, bảo lãnh, địa lý, lender, phương thức, doanh nghiệp, kỳ hạn, ngành và trạng thái quan sát.

## 2. Dataset

SBA FOIA, bản CSV cục bộ `data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv`; dictionary `data/raw/foia/7a_504_foia_data_dictionary.xlsx`, sheet 7(a). **388.338 published records × 42 thuộc tính**; snapshot **2026-06-30**. SHA-256 `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`.

## 3. Data Scope

FY2020–FY2026; ApprovalDate 2019-10-01..2026-06-30. Một snapshot chứa nhiều approval cohorts, không nhiều snapshot theo FY. FY2026 partial qua Q3; Q6 dùng FYTD cùng kỳ FY2025, FY2020 không YoY. Không mở rộng FY2010–2019.

## 4. Important Data Limitations

Không public unique LoanID. LocationID là lender ID. Giữ 687 records thuộc 296 nhóm exact raw duplicate (391 copies dư), không suy là cùng khoản vay. LoanStatus tại snapshot không là outcome cuối FY/default probability; cohort mới có thời gian quan sát ngắn. GrossApproval/guarantee là amount lúc approval, không dư nợ/giải ngân; charge-off là gross, không net loss. JobsSupported do lender báo, không số người duy nhất hoặc tác động nhân quả. Missing không tự điền; BusinessAge là nhãn, không tuổi số. Một snapshot không tự cung cấp SCD history.

## 5. Preprocessing Status

**REPORT_DOCUMENTED_COMPLETED / CHECKOUT_UNVERIFIED**: report §1.2.2 mô tả pandas, đọc text, checksum, lineage, trim/blank→NULL/newline→space, duplicate/DQ flags, ISO dates, integer jobs/term, money DECIMAL(18,3), raw/canonical status, TermBand, NAICS candidate, export/reconcile. Output được report ghi **388.338×38** gồm 18 retained source attributes và standardized/derived/lookup/DQ. Notebook 01_preprocessing.ipynb, module preprocess, TSV/clean CSV và manifest chưa có trong checkout. Không chạy lại src/main.py để thay preprocessing mới; file đó sinh prototype snowflake.

## 6. Dimensional Model

Logical star **1 Fact_Loan + 8 Dim_***, theo report §1.3.3–1.3.5. [Field contract](docs/dimensional_model/candidate_schema.md) trích đủ các bảng report. Report gọi mô hình đề xuất; chưa là physical database đã nạp. DBML còn precision tiền và TermBandKey khác report.

## 7. Fact Grain

Một published record tại snapshot. LoanKey là surrogate PK, không SBA LoanID. Lineage SourceFileID + SourceRecordOrdinal; SourceRowNumber vật lý riêng, ETLBatchID cho lần nạp. Có 16 source records multiline. RecordCount=1. Snapshot metadata phải còn truy vết được dù AsOfDate không nằm bảng Fact report.

## 8. Dimensions

Dim_Date (ApprovalDateKey); Dim_ProjectGeography; Dim_Industry; Dim_Lender; Dim_LoanProfile; Dim_LoanStatus; Dim_TermBand; Dim_Business. Mỗi dimension có FK trực tiếp từ Fact. Chỉ approval date role; FirstDisbursementDate/PaidInFullDate/ChargeOffDate giữ DATE trong Fact. County đi với state; raw NAICS code+description; LocationID nhóm lender; Dim_Business chỉ classification type/age, không borrower identity. Business key đầy đủ/Unknown/SCD còn cần physical spec.

## 9. Measures/KPIs

Base: GrossApproval, SBAGuaranteedApproval, GrossChargeOffAmount, JobsSupported, RecordCount. Derived query: average per record, guarantee ratio, FY/state/status/band shares, YoY, rank, structural shift, method contribution, observed CHGOFF share. Ratio-of-sums, tử/mẫu cùng population; mẫu số 0→NULL. Không cộng ratios/TermInMonths hoặc amounts xuyên snapshots.

## 10. Business Questions

Q1 vốn FY/quý; Q2 count/average theo method; Q3 Top 10 state/FY; Q4 reported jobs/FY/method; Q5 Top 10 lender; Q6 YoY/FYTD; Q7 guarantee/method; Q8 state share/FY; Q9 Top 3 county/state; Q10 FY×raw business type/age (missing/Unanswered riêng); Q11 snapshot status/cohort/method; Q12 band cùng tăng share và average FY2024→25; Q13 structural shift ngành/state và Top 3 sector tăng/giảm; Q14 lender cùng tăng total/average và tối đa 3 method tăng dương; Q15 sector CHGOFF share cao hơn cohort baseline, gates 30/5, rank gross charge-off rồi Top 3 state. [Q1–Q15](docs/business_requirements/business_questions_current.md).

## 11. Important Business Rules

Default mọi published record, giữ CANCLD và duplicates trừ query lọc rõ. FY bắt đầu tháng 10, Q1=Oct–Dec/Q2=Jan–Mar/Q3=Apr–Jun/Q4=Jul–Sep. Raw P I F giữ, canonical PIF. TermBand: ZERO=0, SHORT=1–60, MEDIUM=61–119, TERM_120=120, LONG=121–240, VERY_LONG>240; MISSING/INVALID giữ DQ, ngoài share denominator Q12. Q13/Q15 sector mapping CANDIDATE_UNVERIFIED, không đoán NAICS vintage. Q15 mẫu số mọi status, N≥30/CHGOFF≥5, baseline toàn cohort trước state filter; exploratory only. Công thức chi tiết trong Measure Contract kế thừa rule dự án khi report không mâu thuẫn, không coi toàn bộ chi tiết là do report định nghĩa.

## 12. Canonical Files

| Vai trò | File thực tế | Trạng thái |
|---|---|---|
| Báo cáo nhóm | [Chương 1 mới nhất](project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx) | Nguồn chính cho nội dung báo cáo; không sửa DOCX |
| Context ngắn | [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Context đọc trước cho task sau |
| Trạng thái / Open Issues | [docs/00_current_status.md](docs/00_current_status.md) | Phân biệt report, checkout và triển khai |
| Mô hình logic / field contract | [candidate_schema.md](docs/dimensional_model/candidate_schema.md) | Fact_Loan + 8 Dim_* theo bảng report |
| Q1–Q15 | [business_questions_current.md](docs/business_requirements/business_questions_current.md) | Canonical nội dung; bảng 1.14 report là nguồn đối chiếu |
| Measures / KPI | [measure_contract_q1_q15.md](docs/business_requirements/measure_contract_q1_q15.md) | Công thức logic, chưa chạy warehouse |
| Coverage | [measure_dimension_matrix.md](docs/dimensional_model/measure_dimension_matrix.md) | 8 dimensions bao phủ Q1–Q15 |
| Business rules | [business_rule_register.md](docs/business_requirements/business_rule_register.md) | Rule dự án; NAICS mapping chưa verified |
| Dataset / profiling / DQ | [overview](docs/data_understanding/data_overview.md), [profiling](docs/data_understanding/data_profiling_report.md), [quality](docs/data_understanding/data_quality_report.md) | Baseline nguồn, không là standardized output |
| Dictionary | [định nghĩa nguồn](docs/data_dictionary.md), [diễn giải Việt](docs/data_understanding/data_dictionary.md) | Hai vai trò bổ sung, không phải hai schema đích |
| Preprocessing | [preprocessing_plan.md](docs/data_understanding/preprocessing_plan.md) | Report mô tả hoàn tất; artifact checkout chưa có |
| Diagram DBML | [candidate_schema.dbml](diagram/candidate_schema.dbml) | Proposal, còn lệch datatype; không là physical authority |
| SQL schema hiện có | [01_warehouse.sql](sql/01_warehouse.sql), [02_validation.sql](sql/02_validation.sql) | Canonical implementation **prototype cũ**, không schema đích hiện hành |
| Python hiện có | [src/main.py](src/main.py) | Prototype snowflake; không notebook preprocessing của report |

## 13. Current Project Status

Documentation đã đồng bộ model/naming, dataset, Q1–Q15, preprocessing report và Open Issues. Raw/code/DDL/DOCX giữ nguyên. Prototype CSV tồn tại trong data/processed; target Fact_Loan chưa triển khai. Chưa tìm thấy .dtproj/.dtsx/.dwproj hoặc bằng chứng deployment database/cube/BI. Báo cáo Chương 1 có trong checkout; các bản report khác là lịch sử/reference.

## 14. Next Phase — Chapter 2 / SSIS

Context đủ để bắt đầu đặc tả Chương 2; **chưa đủ để nạp SSIS trực tiếp** khi thiếu preprocessing artifacts/38-column contract và physical mapping. Bước kế tiếp: bổ sung/xác minh notebook, module, TSV, manifest và lookup artifacts; giải quyết precision/TermBandKey, keys/Unknown và NAICS; sau đó trình đặc tả Source-to-Target Mapping + reconciliation trước implementation. Task này không tạo/chạy SSIS.
