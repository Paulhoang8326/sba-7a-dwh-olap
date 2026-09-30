# Trạng thái hiện hành — SBA 7(a)

> Cập nhật: 2026-09-30. Trang này phân biệt phạm vi câu hỏi, Target Schema Proposal, Measure Contract, business rules, prototype cũ và hệ thống đã triển khai. Người dùng đã duyệt **star 1F+8D, Q10 mới và năm nhóm business rule ở cấp dự án**. Physical/Final Schema chưa chốt; NAICS reference/version/mapping còn `PENDING_VERIFICATION`.

## Source of Truth

| Chủ đề | Tài liệu canonical hiện hành | Cách dùng |
|---|---|---|
| Business Questions | [Q1–Q15 hiện hành](business_requirements/business_questions_current.md) | Phạm vi câu hỏi `DECIDED` ở cấp nội dung. Bộ BQ01–BQ24 cũ là lịch sử. |
| Measure–Dimension Matrix | [Matrix Q1–Q15](dimensional_model/measure_dimension_matrix.md) | Kiểm tra coverage từ câu hỏi đến measure, dimension và điều kiện. |
| Measure Contract | [Measure Contract Q1–Q15](business_requirements/measure_contract_q1_q15.md) | Tách Formula Status với Rule/Population Status; **DOCUMENTED / NOT IMPLEMENTED**. |
| Target Schema Proposal | [Candidate logical schema](dimensional_model/candidate_schema.md) | Đã chọn star 1 `FactLoanSnapshot` + 8 dimensions ở cấp logic; **PROPOSED**, chưa là Final/physical schema hoặc database đã nạp. |
| Business Rules | [Business Rule Register](business_requirements/business_rule_register.md) | Population, cấp NAICS Sector, TermBand tách `TERM_120`, `P I F→PIF` canonical và Q15 gates 30/5 `PROJECT_APPROVED`; NAICS mapping còn chờ xác minh. |
| Preprocessing | [Preprocessing Plan](data_understanding/preprocessing_plan.md) | `PLANNED / NOT IMPLEMENTED`; không phải cleaned dataset đã tạo. |
| Dữ liệu và quality | [Data Overview](data_understanding/data_overview.md), [Profiling](data_understanding/data_profiling_report.md), [Data Quality](data_understanding/data_quality_report.md) | Bằng chứng `VERIFIED` của snapshot nguồn. |
| Prototype đã có | [Thiết kế snowflake trước đây](02_warehouse_design.md), [kiểm chứng prototype](validation.md) | Giữ để truy vết; `DEPRECATED AS CURRENT`, không dùng làm candidate schema. |

## Dataset — VERIFIED

- Nguồn là một CSV SBA 7(a) FOIA với **388.338 published records**, **42 thuộc tính**, `AsOfDate = 2026-06-30`, `ApprovalFY` FY2020–FY2026. FY2026 mới đến 30/06/2026.
- `Program` trong file là chương trình **7(a)** (chuỗi nguồn có khoảng trắng); mọi kết luận ở đây chỉ áp dụng cho snapshot 7(a) này.
- Một dòng nguồn là một **published record trong một snapshot**. Không có public unique `LoanID`; `LocationID` là mã lender. `Published Record Count` không phải unique loan count.
- Profiling trên chuỗi nguồn xác định **687 dòng thuộc 296 nhóm exact duplicate**, gồm 391 bản sao dư theo phương pháp đó. Giữ mọi dòng; không suy ra chúng là cùng một khoản vay. Con số 689/392 ở tài liệu feasibility cũ là kết quả theo cách chuẩn hóa khác, không phải số exact-raw hiện hành.
- `LoanStatus` là trạng thái **tại snapshot**, không phải trạng thái lịch sử cuối mỗi FY. `GrossApproval` và `SBAGuaranteedApproval` là giá trị tại phê duyệt; `GrossChargeOffAmount` là gross, không phải net loss; `JobsSupported` do lender báo cáo.

## Phạm vi và thiết kế

| Nội dung | Trạng thái | Diễn giải |
|---|---|---|
| Q1–Q15 | **DECIDED — business-question scope only** | Nội dung câu hỏi chính đã được người dùng xác nhận. Công thức phụ thuộc rule vẫn có thể `CONDITIONAL`. |
| `FactLoanSnapshot` + 8 dimensions | **PROPOSED TARGET SCHEMA; lựa chọn logic đã duyệt** | Star schema bổ sung `DimBusiness`/`BusinessKey`; grain vẫn là published record trong snapshot. Chưa duyệt Final/physical schema/DDL. |
| Base measures và Measure Contract | **FORMULA READY / DOCUMENTED; NOT IMPLEMENTED** | `GrossApproval`, `SBAGuaranteedApproval`, `GrossChargeOffAmount`, `JobsSupported`, `RecordCount`. Average, ratio, share, YoY, ranking và shift tính ở lớp truy vấn. |
| BR-POP-01, BR-TERM-01, BR-STATUS-01, BR-CHGOFF-01 | **PROJECT_APPROVED** | Default population mọi published record; `TERM_120` riêng; raw `P I F` giữ nguyên và canonical `PIF`; Q15 gates 30/5. Chưa nạp vào kho. |
| BR-NAICS-01 | **PROJECT_APPROVED — analytical level; PENDING_VERIFICATION — reference/mapping** | Q13/Q15 dùng NAICS Sector; không suy ra vintage hoặc gắn sector name chưa xác minh. |
| BR-BUSINESS-01 / BR-BUSINESS-02 | **DECIDED cho raw Q10/proposal / OPEN cho canonical và grouping** | Giữ `BusinessTypeRaw`, `BusinessAgeRaw`, `Unanswered` và missing; chưa tạo `BusinessAgeGroup` hoặc borrower identity. |
| Preprocessing | **PLANNED / NOT IMPLEMENTED** | Mới có kế hoạch. Raw CSV không được sửa; chưa xuất standardized dataset theo plan. |
| Python snowflake prototype và 15 manual/MDX cũ | **DEPRECATED AS CURRENT; retained for history** | Code, DDL, MDX và kiểm chứng prototype vẫn có giá trị lịch sử; không tương ứng bộ Q1–Q15 hiện hành. |
| SQL Server, SSIS, SSAS cube, Pivot, BI theo candidate mới | **NOT IMPLEMENTED** | Có script/đặc tả prototype cũ, chưa có bằng chứng triển khai candidate mới. |

## Quy ước trạng thái

`VERIFIED` = nguồn/dữ liệu đã kiểm chứng; `PROJECT_APPROVED` = quyết định phân tích của đồ án được người dùng duyệt, không mặc nhiên là quy tắc SBA; `PENDING_VERIFICATION` = còn cần kiểm nguồn/mapping; `DECIDED` = nội dung BQ hoặc quyết định được duyệt theo phạm vi nêu; `READY` = công thức đủ rõ cho bước được chỉ rõ; `PROPOSED` = đề xuất chưa duyệt; `OPEN` = còn thiếu quyết định/căn cứ; `DEPRECATED` = lịch sử; `NOT IMPLEMENTED` = chưa triển khai. Formula Status, Rule/Population Status và Implementation Status là ba trục khác nhau.

## Open Decisions và bước tiếp theo

1. Xác minh NAICS reference/version/crosswalk, đối soát sector code/name và unmapped trước khi công bố Q13/Q15 theo sector. Các rule khác đã `PROJECT_APPROVED`, nhưng chưa triển khai.
2. Viết Source-to-Target Mapping theo [star 1F+8D](dimensional_model/candidate_schema.md), [Measure Contract](business_requirements/measure_contract_q1_q15.md), unknown members, khóa/lineage và rule version. Phần NAICS có thể để `PENDING_VERIFICATION`; chưa gọi là Final Schema.
3. Triển khai [Preprocessing Plan](data_understanding/preprocessing_plan.md) và đối soát raw → standardized → warehouse trước khi thay hoặc chạy Python/DDL/MDX/cube prototype.

Không coi việc đồng bộ tài liệu lần này là đã làm preprocessing, ETL, database hay cube.
