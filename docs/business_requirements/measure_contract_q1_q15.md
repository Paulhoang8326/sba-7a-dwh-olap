# Measure Contract — Q1–Q15 hiện hành

> **DOCUMENTED / NOT IMPLEMENTED**, cập nhật 2026-09-30 cho [Q1–Q15](business_questions_current.md) và [Target Schema Proposal 1F+8D](../dimensional_model/candidate_schema.md). Các quyết định trong [Business Rule Register](business_rule_register.md) có status `PROJECT_APPROVED` ở cấp đồ án; tài liệu này chưa chứng minh physical schema, ETL, SQL, MDX hay cube đã chạy. NAICS reference/version/mapping còn `PENDING_VERIFICATION`.

## 1. Population, grain và thành phần cộng được

- Một dòng fact = **một published record** của một snapshot `AsOfDate=2026-06-30`, không phải unique loan hay unique business. Giữ mọi dòng nguồn, kể cả exact duplicates; không cộng cùng record qua nhiều snapshots.
- **BR-POP-01:** mặc định dùng mọi published record trong FY và các slicer được chọn, kể cả `CANCLD`, `COMMIT`, `EXEMPT`, `P I F`, `CHGOFF`. Chỉ lọc `RawStatus` khi BQ/measure quy định rõ. Một KPI dùng tử/mẫu trên cùng population và cùng snapshot; các ngoại lệ status của Q11/Q15 được mô tả dưới đây.
- `N=SUM(RecordCount)` với `RecordCount=1`; `A=SUM(GrossApproval)`; `G=SUM(SBAGuaranteedApproval)`; `J=SUM(JobsSupported)`; `C=SUM(GrossChargeOffAmount)`. `J` là **việc làm lender báo cáo**; giữ giá trị 0 của nguồn, không gọi là việc làm SBA trực tiếp tạo ra. `A`/`G` là amount tại phê duyệt, không phải giải ngân/dư nợ; `C` là gross, không phải net loss.
- `AvgA=A/N` khi `N>0`; `GR=G/A` khi `A>0`. Mọi mẫu số 0 → NULL/“không xác định”. Average, ratio, share, YoY, rank và structural shift là logic query/semantic layer, không SUM/AVG các kết quả đã tổng hợp. `TermInMonths` giữ để validation/derive band, không SUM thành KPI.
- `Share=Measure_group/Measure_parent` chỉ có nghĩa khi **parent, slicer, FY và status population** được ghi rõ ở từng Q. Trước khi rank Top-N, tính metric trên toàn bộ tập eligible; tie/order phụ cần được ghi ở query spec.

## 2. Hợp đồng theo Business Question

| Q | KPI/nguồn fact | Population và cấp phân tích | Công thức/query contract | Formula Status | Rule/Population Status |
|---:|---|---|---|---|---|
| Q1 | `A` / `GrossApproval` | Mặc định BR-POP-01; `DimDate.FiscalYear → FiscalQuarter` | `A=SUM(GrossApproval)`; FY2026 là partial. | **READY** | **PROJECT_APPROVED** population; FY2026 phải gắn nhãn partial. |
| Q2 | `N`, `AvgA` / `RecordCount`, `GrossApproval` | Mặc định; FY × `DimLoanProfile.ProcessingMethod` raw | `AvgA=A/N` khi `N>0`; đếm published records. | **READY** | **PROJECT_APPROVED** population; method mapping khác raw chưa duyệt. |
| Q3 | `A`, state rank | Mặc định; FY × `DimProjectGeography.ProjectState` | Rank `A` giảm dần **riêng từng FY** rồi lấy Top 10. | **READY** | **PROJECT_APPROVED** population; tie rule ở query spec. |
| Q4 | `J` / `JobsSupported` | Mọi published record trong FY × raw `ProcessingMethod`, trừ slicer được nêu rõ | `SUM(JobsSupported)`; giữ nguồn 0. | **READY** | **SOURCE-SUPPORTED** về nghĩa lender-reported; không suy ra tác động nhân quả. |
| Q5 | `A`, lender rank | Mặc định; **GROUP BY `LocationID`**; `BankName` chỉ để hiển thị lender hiện được gán | Rank `A` giảm dần, Top 10; tên không phải khóa nhóm. | **READY** | **PROJECT_APPROVED** population; tie rule ở query spec. |
| Q6 | YoY của `A` | Mặc định; `DimDate.FiscalYear` và cùng kỳ FYTD | `(A_t−A_t-1)/A_t-1` khi mẫu >0. FY2020=NULL; FY2021–FY2025 so full FY; FY2026 `2025-10-01..2026-06-30` so FY2025 `2024-10-01..2025-06-30`. | **READY** | **PROJECT_APPROVED** population; cửa sổ FY2026 đã thuộc Q6, FY derivation cần đối soát khi mapping. |
| Q7 | `G`, `GR` / `SBAGuaranteedApproval`, `GrossApproval` | Cùng population FY × raw `ProcessingMethod` | `GR=G/A` khi `A>0`, không AVG tỷ lệ dòng. | **READY** | **PROJECT_APPROVED** population; đây là bảo lãnh tại approval, không phải payout. |
| Q8 | State approval share | Mặc định; FY × `ProjectState` | `A_state/A_all_states_same_FY`; mẫu số bỏ filter **state/county** đang tạo nhóm, giữ FY và các slicer khác theo cùng population. | **READY** | **PROJECT_APPROVED** population; parent context phải được giữ đúng. |
| Q9 | County `A`, rank | Mặc định; `ProjectState → ProjectCounty` | Rank `A` trong **mỗi state**, Top 3; county key gồm state. | **READY** | **PROJECT_APPROVED** population; tie rule ở query spec. |
| Q10 | `N`, `A`, `AvgA` | Mặc định; FY × `DimBusiness.BusinessTypeRaw × BusinessAgeRaw` | `AvgA=A/N` khi `N>0`; `Unanswered`, source missing và Unknown lookup là ba tình huống riêng. | **READY** | **PROJECT_APPROVED** BR-POP-01/BR-BUSINESS-01; không dùng `BusinessAgeGroup`. |
| Q11 | Status count/share | **Mọi status** trong cùng cohort FY × raw `ProcessingMethod` | `N_status/N_all_status_same_cohort_method`; chỉ filter status ở tử, không ở mẫu. | **READY** | **PROJECT_APPROVED** `P I F→PIF` canonical; raw vẫn giữ. |
| Q12 | Band approval share, `AvgA` | Mặc định; FY2024/25 × `DimTermBand`; share denominator chỉ gồm 6 band analytical của BR-TERM-01 | `Share_band,FY=A_band,FY/A_six_bands,FY`; tìm `Share25>Share24` và `AvgA25>AvgA24` khi `N24,N25>0`. `MISSING`/`INVALID` chỉ hiển thị DQ, không vào mẫu số. | **READY** | **PROJECT_APPROVED — project-defined** `TERM_120` tách riêng; chưa materialize dimension. |
| Q13 | Industry share, `StructuralShiftScore`, `ShareChangePP` | Mặc định; FY2024/25 × state × **NAICS Sector** | `Share_i,s,t=A_i,s,t/A_s,t` khi `A_s,24>0` và `A_s,25>0`; union sector hai FY, vắng một FY → share 0. `ShiftScore_s=0.5×Σ_i abs(Share_i,s,25−Share_i,s,24)`; `ShareChangePP=100×(Share25−Share24)`. Rank state, Top 3 sector tăng/giảm share trong từng state. | **READY** | **PROJECT_APPROVED** cấp Sector; **PENDING_VERIFICATION** reference/version/mapping và unmapped coverage. |
| Q14 | Lender `A`, `AvgA`, positive method contribution | Mặc định; lender `LocationID` × FY2024/25 × raw `ProcessingMethod` | Chỉ lender có `N24,N25>0`, `A25>A24`, `AvgA25>AvgA24`. `ΔA_method=A_method,25−A_method,24`; chỉ `ΔA_method>0`. `Contribution=ΔA_method/Σ_all_positive_methods ΔA_method`; tính mẫu số **trước** khi lấy Top 3 method để hiển thị. | **READY** | **PROJECT_APPROVED** population; tie rule ở query spec. |
| Q15 | Observed CHGOFF share, cohort baseline, `C` | Cohort FY × **NAICS Sector**; gate/baseline tính trên mọi state; mọi status ở mẫu số | `Share=N_CHGOFF_sector/N_all_status_sector`; `Baseline=N_CHGOFF_cohort/N_all_status_cohort`. Chỉ rank sector có `N_total≥30`, `N_CHGOFF≥5`, `Share>Baseline` theo `C_CHGOFF=SUM(GrossChargeOffAmount)` trên raw `CHGOFF`. **Sau đó** Top 3 state theo `C_CHGOFF` trong từng sector. | **READY** | **PROJECT_APPROVED** 30/5 và cấp Sector; **PENDING_VERIFICATION** NAICS mapping. Exploratory only. |

## 3. Filter context và điều kiện không được bỏ qua

**Q12.** `ZERO` là một trong 6 band trong mẫu số share dù `TermInMonths=0` cần hiển thị DQ riêng. `MISSING`/`INVALID` vẫn giữ trong dữ liệu và báo số lượng riêng. Không tạo `AvgA` giả khi band không có published record ở một trong hai FY. Các band là **project-defined analytical classification**, không phải phân loại SBA.

**Q13.** Share lưu dạng 0–1; `ShareChangePP` mới nhân 100 để thành điểm phần trăm. Chỉ gán share=0 cho **sector vắng** khi tổng state của FY đó >0; state có mẫu số không xác định không được gán score 0. Không âm thầm bỏ sector unmapped: đối soát số bản ghi/amount và ghi nhãn unmapped cho đến khi reference được xác minh.

**Q14.** Contribution denominator gồm **mọi** method tăng dương của cùng lender, kể cả method ngoài Top 3 hiển thị. Nếu một method không có record ở một FY, amount của method trong FY đó là 0 cho phép so sánh; lender vẫn phải có `N>0` ở cả hai FY.

**Q15.** Thứ tự: cohort → sector population (`N_total`, `N_CHGOFF`, observed share) → gate 30/5 → so baseline toàn cohort → rank sector theo `C_CHGOFF` → Top 3 state đóng góp trong mỗi sector. State filter không tham gia gate/baseline. Ngưỡng là **ranking eligibility**, không phải significance test hay xác suất default. Theo phép thử sector candidate từ CSV, **FY2025 có 7 sector qua gate và 3 sau baseline; FY2026 có 0 qua gate**. Đây chưa là output chính thức vì NAICS mapping/reference chưa VERIFIED. Cohort không có sector eligible trả thông báo không có nhóm đủ điều kiện; không hạ ngưỡng để tạo kết quả.

## 4. Trạng thái measure và gate tiếp theo

| Measure/logic | Formula Status | Rule/Population Status |
|---|---|---|
| `PublishedRecordCount`, `TotalGrossApproval`, `TotalSBAGuaranteedApproval`, `AverageGrossApprovalPerRecord`, `WeightedGuaranteeRatio` | **READY** | **PROJECT_APPROVED** BR-POP-01; same-slice denominator. |
| `ReportedJobsSupported` | **READY** | **SOURCE-SUPPORTED** về nghĩa lender-reported; không là số việc làm duy nhất/tác động SBA. |
| `StateApprovalShare`, `StatusRecordShare`, `YoYGrossApprovalGrowth`, `PositiveMethodContributionShare` | **READY** | **PROJECT_APPROVED** population/logic Q; tie/FY physical mapping chưa triển khai. |
| `TermBandApprovalShare` | **READY** | **PROJECT_APPROVED — project-defined** BR-TERM-01; chưa materialize. |
| `StructuralShiftScore`, `ShareChangePP`, Q15 `ObservedCHGOFFShare` và `C_CHGOFF` theo sector | **READY** | **PROJECT_APPROVED** cấp Sector và gate 30/5; **PENDING_VERIFICATION** NAICS reference/version/mapping. |

`READY` trong cột Formula chỉ nói biểu thức đã đủ rõ để đặc tả, **không** có nghĩa SQL/MDX/cube đã chạy. Chỉ khi xác minh NAICS mapping, kiểm coverage/unmapped, hoàn tất physical mapping và đối soát dữ liệu mới có thể công bố kết quả sector của Q13/Q15 từ warehouse. Q10 raw không phụ thuộc NAICS; business canonical/grouping là extension còn `OPEN`.
