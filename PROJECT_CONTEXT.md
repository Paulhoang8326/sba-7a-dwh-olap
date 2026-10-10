# PROJECT_CONTEXT — SBA 7(a) theo Chương 1 hiện hành

Cập nhật **2026-10-10**: **CHAPTER 1 READY TO FREEZE**. [Chương 1](project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx) giữ nguyên; [trạng thái](docs/00_current_status.md) và [kế hoạch SSIS](docs/etl/chapter2_ssis_plan.md) là điểm bắt đầu Chương 2. Không dùng tên FactLoanSnapshot/DimDate của prototype làm tên schema hiện hành.

## 1. Project Overview

Đề tài: **Xây dựng hệ thống kho dữ liệu và OLAP hỗ trợ phân tích danh mục tín dụng, bảo lãnh và kết quả khoản vay SBA 7(a) tại Hoa Kỳ giai đoạn FY2020–FY2026**. IS217, nhóm 19: Hoàng Khôi Nguyên (24521176), Phan Thế Hiển (24520479). Mục tiêu: tổ chức dữ liệu đa chiều thống nhất grain, measures và population để phân tích vốn, bảo lãnh, địa lý, lender, phương thức, doanh nghiệp, kỳ hạn, ngành và trạng thái quan sát.

## 2. Dataset

SBA FOIA, bản CSV cục bộ `data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv`; dictionary `data/raw/foia/7a_504_foia_data_dictionary.xlsx`, sheet 7(a). **388.338 published records × 42 thuộc tính**; snapshot **2026-06-30**. SHA-256 `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`.

## 3. Data Scope

FY2020–FY2026; ApprovalDate 2019-10-01..2026-06-30. Một snapshot chứa nhiều approval cohorts, không nhiều snapshot theo FY. FY2026 partial qua Q3; Q6 dùng FYTD cùng kỳ FY2025, FY2020 không YoY. Không mở rộng FY2010–2019.

## 4. Important Data Limitations

Không public unique LoanID. LocationID là lender ID. Giữ 687 records thuộc 296 nhóm exact raw duplicate (391 copies dư), không suy là cùng khoản vay. LoanStatus tại snapshot không là outcome cuối FY/default probability; cohort mới có thời gian quan sát ngắn. GrossApproval/guarantee là amount lúc approval, không dư nợ/giải ngân; charge-off là gross, không net loss. JobsSupported do lender báo, không số người duy nhất hoặc tác động nhân quả. Missing không tự điền; BusinessAge là nhãn, không tuổi số. Một snapshot không tự cung cấp SCD history.

## 5. Preprocessing Status

**CODE_INTEGRATED / TSV_REPRODUCED**: report §1.2.2 mô tả pandas, đọc text, checksum, lineage, trim/blank→NULL/newline→space, duplicate/DQ flags, ISO dates, integer jobs/term, money DECIMAL(18,3), raw/canonical status, TermBand, NAICS candidate, export/reconcile. `src/etl/preprocess.py`, notebook, tests và reports đã tích hợp; 18 nguồn KEEP, **388.338×38** và checksum TSV được kiểm trực tiếp, TSV tái lập đúng SHA-256. Hai output LFS đã kiểm trong Git cache nhưng chưa checkout vào staging; full `run()`/pytest chưa tái kiểm vì clean CSV có `Borr*` và môi trường thiếu pytest. Xem [integration audit](docs/etl/preprocessing_integration_audit.md). `src/main.py` vẫn là prototype snowflake cũ.

## 6. Dimensional Model

Logical star **1 Fact_Loan + 8 Dim_***, theo report §1.3.3–1.3.5. [Field contract](docs/dimensional_model/candidate_schema.md) trích đủ 76 columns. DBML đã thống nhất money DECIMAL(18,3), TermBandKey BIGINT; chưa là physical database đã nạp. Hình schema cũ trong report còn type annotations, được ghi chú ở kế hoạch Chương 2; không thay đổi logic mô hình.

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
| Preprocessing | [preprocessing_plan.md](docs/data_understanding/preprocessing_plan.md), [integration audit](docs/etl/preprocessing_integration_audit.md) | Code/notebook/reports có trong branch; TSV tái lập, full test còn giới hạn |
| Input/kế hoạch Chương 2 | [chapter2_ssis_plan.md](docs/etl/chapter2_ssis_plan.md) | TSV 52 cột local đã kiểm; kế hoạch dựng package |
| Diagram DBML | [candidate_schema.dbml](diagram/candidate_schema.dbml) | Đã thống nhất datatype với bảng report; chưa là deployed DDL |
| SQL schema hiện có | [01_warehouse.sql](sql/01_warehouse.sql), [02_validation.sql](sql/02_validation.sql) | Canonical implementation **prototype cũ**, không schema đích hiện hành |
| Python hiện có | [preprocess.py](src/etl/preprocess.py), [notebook](notebooks/01_preprocessing.ipynb); [src/main.py](src/main.py) | Hai file đầu là Phase 1 mới; `src/main.py` là prototype cũ |

## 13. Current Project Status

Chương 1 đủ để freeze trong phạm vi đồ án. `prepare_ssis_input.py` tái sử dụng rules cũ, tạo input riêng **388.338×52**, giữ toàn bộ 38 cột đầu và thêm đúng 14 source fields; không xuất Borr*. 6 unittest pass và full-data export/đối soát pass. Output/manifest lưu local, ignore. Raw/DDL/DOCX và preprocessing Chương 1 giữ nguyên; target Fact_Loan/SSIS chưa triển khai.

## 14. Next Phase — Chapter 2 / SSIS

Bắt đầu triển khai theo [kế hoạch tám bước](docs/etl/chapter2_ssis_plan.md), tham khảo ba báo cáo mẫu. Dùng input 52 cột, full composite keys, Fact Lookups và các kiểm count/totals/FK. Chốt seed/NULL/Unicode trong bước viết DDL/Data Flow; NAICS candidate không phải verified reference. Không cần production monitoring, CDC hay SCD2 cho một snapshot.
