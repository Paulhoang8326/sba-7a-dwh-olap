# Measure–Dimension Matrix — Q1–Q15

> Nội dung nghiệp vụ đồng bộ theo Chương 1 §1.3.4–1.3.6, không đổi Q1–Q15/rules. Trạng thái cập nhật 2026-10-10: preprocessing 38 cột đã tích hợp/kiểm; input Chương 2 riêng 52 cột đã chạy và đối soát. `Fact_Loan` + 8 `Dim_*` và query warehouse chưa triển khai. Xem [trạng thái](../00_current_status.md) và [kế hoạch SSIS](../etl/chapter2_ssis_plan.md).

> Matrix kiểm tra coverage cho [Business Questions hiện hành](../business_requirements/business_questions_current.md), không phải danh sách bảng SQL đã triển khai. Candidate logic ở [candidate_schema.md](candidate_schema.md); công thức/population ở [Measure Contract](../business_requirements/measure_contract_q1_q15.md), rule ở [register](../business_requirements/business_rule_register.md).

Ký hiệu: `A=SUM(GrossApproval)`, `G=SUM(SBAGuaranteedApproval)`, `N=SUM(RecordCount)`, `C=SUM(GrossChargeOffAmount)`. Mẫu số 0 → NULL/không xác định. Ratio/share/average/rank tính tại cùng lát cắt, không SUM/AVG giá trị đã tổng hợp. Tất cả count là published records trong một snapshot.

| Q | Fact base measures hoặc thuộc tính gốc | Measure tính lúc truy vấn | Dimension/cấp phân tích | Dependency/coverage |
|---:|---|---|---|---|
| Q1 | `GrossApproval` | `A` | `Dim_Date`: Approval FY → FiscalQuarter | Có; FY2026 partial. |
| Q2 | `RecordCount`, `GrossApproval` | `N`, `A/N` | `Dim_LoanProfile.ProcessingMethod`; `Dim_Date.FiscalYear` | Có ở raw method. |
| Q3 | `GrossApproval` | `A`, rank trong FY | `Dim_ProjectGeography.ProjectState`; `Dim_Date.FiscalYear` | Có. |
| Q4 | `JobsSupported` | `SUM(JobsSupported)` | `Dim_Date.FiscalYear`; `Dim_LoanProfile.ProcessingMethod` | Có; lender-reported. |
| Q5 | `GrossApproval` | `A`, Top 10 | `Dim_Lender.LocationID`, `BankName` | Có; lender hiện được gán. |
| Q6 | `GrossApproval` | `(A_t−A_t-1)/A_t-1` | `Dim_Date.FiscalYear` | Có; kết quả FY2021–FY2025, so toàn năm tài chính. FY2020 chỉ là năm cơ sở để tính YoY FY2021, không hiển thị trong các hàng kết quả tăng trưởng. Không đưa FY2026 vào kết quả Q6. |
| Q7 | `SBAGuaranteedApproval`, `GrossApproval` | `G`, `G/A` | `Dim_LoanProfile.ProcessingMethod`; `Dim_Date.FiscalYear` | Có; ratio-of-sums. |
| Q8 | `GrossApproval` | `A_state/A_all_states_same_FY` | `Dim_ProjectGeography.ProjectState`; `Dim_Date.FiscalYear` | Có; giữ slicer khác ở mẫu số. |
| Q9 | `GrossApproval` (SUM) | `A` toàn giai đoạn FY2020–FY2026; Top 3 giảm dần theo `A` | `Dim_ProjectGeography`: `ProjectState = CA`, `ProjectCounty`; `Dim_Date.FiscalYear` FY2020–FY2026 | Có; Slice, Top-N tại California; county key gồm state. |
| Q10 | `RecordCount`, `GrossApproval` | `N`, `A`, `A/N` khi `N>0` | `Dim_Business.BusinessTypeRaw`, `BusinessAgeRaw`; `Dim_Date.FiscalYear` | Raw labels và population `PROJECT_APPROVED`; giữ `Unanswered` khác missing. |
| Q11 | `RecordCount` | `SUM(RecordCount)` / `Record Count` | `Dim_LoanProfile.ProcessingMethod`; `Dim_LoanStatus.RawStatus`; `Dim_Date.FiscalYear = 2025` | Rows: `Processing Method`, `Loan Status Raw` (`Raw Status` trong Cube); Slice, Dice; giữ raw `P I F`. |
| Q12 | `RecordCount`, `GrossApproval`; `TermInMonths` để đối soát | `N=SUM(RecordCount)`, `A=SUM(GrossApproval)`, `AvgA=A/N` khi `N>0` | `Dim_TermBand.TermBandName`; `Dim_Date.FiscalYear = 2025` | Slice, Roll-up; giữ phân nhóm BR-TERM-01, gồm `TERM_120` tách riêng và ZERO; nhãn DQ giữ riêng khi có phát sinh. |
| Q13 | `GrossApproval` | `Share_i=A_i/A_state`; `½Σ|Share_i,25−Share_i,24|`; `ShareChangePP=100×ΔShare_i` | `Dim_Industry.NaicsSectorCode`; `Dim_ProjectGeography.ProjectState`; `Dim_Date` | Cấp Sector `PROJECT_APPROVED`, reference/mapping `PENDING_VERIFICATION`; state có `A>0` cả hai FY, union sector, vắng một FY → share 0. |
| Q14 | `GrossApproval`, `RecordCount` | lender `A`, `A/N`; `ΔA_method>0`; positive contribution share | `Dim_Lender`; `Dim_LoanProfile.ProcessingMethod`; `Dim_Date` | Có; rank tối đa 3 method dương. |
| Q15 | `RecordCount`, `GrossChargeOffAmount` | observed CHGOFF share, baseline cohort, `C_CHGOFF`, Top 3 state | `Dim_LoanStatus`; `Dim_Industry.NaicsSectorCode`; `Dim_ProjectGeography.ProjectState`; `Dim_Date` | Sector và gates 30/5 `PROJECT_APPROVED`; mapping `PENDING_VERIFICATION`. State chỉ xét sau gate/rank; không phải default probability. |

## Kết luận coverage

- Một fact ở grain bản ghi công bố và **8 dimensions** bao phủ Q1–Q15 ở cấp logic. `Dim_Business` phục vụ Q10; `Dim_TermBand` phục vụ Q12. `Dim_Date` chỉ cần FK vai trò phê duyệt cho bộ câu hỏi này.
- `Dim_TermBand` và quy tắc `TERM_120` đã `PROJECT_APPROVED`, nhưng chưa materialize warehouse dimension/FK; `TermInMonths` nguồn phải còn truy vết được.
- Raw `P I F→PIF` canonical đã `PROJECT_APPROVED`; source vẫn giữ nguyên. Cấp Sector cho Q13/Q15 đã duyệt, nhưng reference/version/mapping và giá trị `NaicsSectorName` chưa VERIFIED.
- Q15 áp ngưỡng và so baseline **khi truy vấn**, không xóa dòng trong preprocessing. Trong phép thử sector candidate, FY2025 có 7 sector qua gate/3 sau baseline, FY2026 có 0 qua gate; không dùng FY2025 làm ví dụ kết quả rỗng.
