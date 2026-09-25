# KPI Catalog ứng viên — SBA 7(a)

**Căn cứ:** [Business Rules](business_rules.md), [19 BQ được chọn](business_questions_selection.md), [Business Questions Catalog](business_questions_catalog.md), [Data Dictionary](../data_understanding/data_dictionary.md), [Data Quality Report](../data_understanding/data_quality_report.md) và workbook SBA sheet `7(a) Data Dictionary`. Đây là định nghĩa để rà soát, chưa phải KPI được nhóm phê duyệt. Một KPI dùng lại ở nhiều chiều; tên KPI không gắn state/industry/lender.

## Quy ước chung

- `P` = mọi dòng CSV của **một** `AsOfDate`, trong FY và các slicer đang chọn; mặc định cả `EXEMPT`, `P I F`, `CANCLD`, `COMMIT`, `CHGOFF` (**BR03 PROPOSED**). Dòng trùng hoàn toàn vẫn là các dòng riêng. `P_g` là lát cắt nhóm `g`. `Σ` và `N` lần lượt là SUM và số dòng, chỉ trên tập được ghi rõ. Không dùng `DISTINCT`.
- `USD` là đơn vị tiền **dự kiến** theo cách trình bày nguồn; xác nhận đơn vị phát hành trước báo cáo chính thức. Các trường amount là mức phê duyệt/charge-off, không phải tiền đã giải ngân/dư nợ/net loss.
- Mẫu số 0 → NULL và hiển thị “không xác định”; NULL ở đầu vào số không tự đổi thành 0. `ApprovalFY` là FY nguồn; `FiscalQuarter/Month` từ `ApprovalDate` phải đối chiếu (BR04). Tỷ lệ/bình quân/tăng trưởng luôn tính lại từ thành phần, không cộng hoặc trung bình các KPI tỷ lệ.
- `Share` cần xác định **parent** trước khi chạy truy vấn. Mặc định: state trong FY → toàn bộ state cùng FY; sector trong state×FY → toàn bộ sector cùng state×FY; band trong FY×BusinessAge/method → toàn bộ band cùng FY×BusinessAge/method. Các slicer khác được giữ nguyên ở tử và mẫu; bỏ **chỉ** bộ lọc của chiều phân chia. Phần “unknown” nếu có vẫn thuộc mẫu số và được hiển thị.
- Loại `Implementation Type` là loại **KPI cuối**. `GrossApproval`, `SBAGuaranteedApproval`, `JobsSupported`, `GrossChargeOffAmount` là source measures có thể lưu; count dùng 1/dòng; các tỷ lệ và average là phép tính ở semantic/query layer. Nơi lưu cụ thể chưa quyết định.

## Danh mục công thức

| KPI ID; KPI Name | Business Definition; Related BQs | Formula | Numerator | Denominator | Source Attributes | Required Derived Attributes | Implementation Type; Decision Status |
|---|---|---|---|---|---|---|---|
| K01 Approval Record Count | Số dòng công bố trong lát cắt; BQ02, BQ04, BQ10, BQ12, BQ15–BQ17, BQ20–BQ23 | `N(P)` | `RecordCount=1` mỗi dòng | — | Dòng CSV, `AsOfDate` | `RecordCount` kỹ thuật | COUNT_MEASURE; PROPOSED |
| K02 Total Gross Approval | Tổng vốn phê duyệt trong file; BQ01, BQ04, BQ10, BQ12, BQ15–BQ17 | `Σ_P GrossApproval` | — | — | `GrossApproval` | — | STORED_MEASURE; PROPOSED |
| K03 Average Gross Approval per Record | Quy mô phê duyệt bình quân trên dòng; BQ02 | `K02/K01` cùng lát cắt | `Σ_P GrossApproval` | `N(P)` | `GrossApproval`, dòng CSV | `RecordCount` | CALCULATED_MEASURE; PROPOSED |
| K04 YoY Gross Approval Growth | Tăng trưởng tổng vốn giữa hai cửa sổ FY tương ứng; BQ03 | `(A_t − A_{t−1})/A_{t−1} ×100` | Chênh hai tổng `GrossApproval` cùng cửa sổ | Tổng kỳ trước cùng cửa sổ | `GrossApproval`, `ApprovalDate`, `ApprovalFY`, `AsOfDate` | Fiscal year/quarter/month kiểm tra; FYTD là logic truy vấn | TEMPORAL_CALCULATION; PROPOSED |
| K05 Gross Approval Share | Phần vốn của nhóm so với parent; BQ04, BQ11, BQ12, BQ15–BQ16 | `Σ_{P_g} GrossApproval / Σ_{P_parent} GrossApproval ×100` | Tổng nhóm | Tổng parent | `GrossApproval`; cột chia nhóm tùy BQ | `LoanSizeBand` BQ04; `TermBand` BQ16; `NaicsSectorCode` BQ12 khi xác minh | CALCULATED_MEASURE; PROPOSED |
| K06 Total SBA Guaranteed Approval | Tổng vốn SBA bảo lãnh ở phê duyệt; BQ06 | `Σ_P SBAGuaranteedApproval` | — | — | `SBAGuaranteedApproval` | — | STORED_MEASURE; PROPOSED |
| K07 Total Non-SBA Guaranteed Approval | Phần phê duyệt ngoài bảo lãnh SBA; BQ08 | `Σ_P GrossApproval − Σ_P SBAGuaranteedApproval` | — | — | `GrossApproval`, `SBAGuaranteedApproval` | `NonSBAGuaranteedApproval` tùy chọn lưu ở fact | DERIVED_MEASURE; PROPOSED |
| K08 Weighted Guarantee Ratio | Tỷ phần bảo lãnh trên vốn phê duyệt trong cùng lát cắt; BQ07 | `K06/K02 ×100` | `Σ_P SBAGuaranteedApproval` | `Σ_P GrossApproval` | Hai amount | — | CALCULATED_MEASURE; PROPOSED |
| K09 Total Reported Jobs Supported | Tổng việc làm do lender báo trên đơn; BQ14 | `Σ_P JobsSupported` | — | — | `JobsSupported` | — | STORED_MEASURE; PROPOSED |
| K10 Approval per Reported Job | Vốn phê duyệt trên một đơn vị job báo cáo; BQ14 | `K02/K09` | `Σ_P GrossApproval` | `Σ_P JobsSupported` | `GrossApproval`, `JobsSupported` | — | CALCULATED_MEASURE; PROPOSED |
| K11 Average Initial Interest Rate | Trung bình số lãi suất ban đầu **trên dòng có rate không NULL**; BQ18 | `Σ_{P_r} InitialInterestRate / N(P_r)`, `P_r={r∈P: rate không NULL}`; **chưa công bố chính thức** | Tổng rate nguồn trên dòng hợp lệ | Số dòng rate không NULL | `InitialInterestRate`, `FixedorVariableInterestInd`, `ProcessingMethod`, `GrossApproval` cho band | `LoanSizeBand` | CALCULATED_MEASURE; OPEN |
| K12 Status Record Share | Tỷ trọng số dòng có một trạng thái trong cùng cohort/lát cắt; BQ20, BQ21, BQ23 | `N(P ∩ status=s)/N(P_parent) ×100`; `s` là nhãn nguồn. BQ21: `CHGOFF`; BQ23: `P I F` | Count của status chọn | Count mọi status cùng cohort, state/industry/band và slicer khác | `LoanStatus`, `ApprovalFY`, `AsOfDate`; chiều BQ tương ứng | `LoanSizeBand` BQ23; `NaicsSectorCode` khi roll-up BQ21 | CALCULATED_MEASURE; PROPOSED |
| K13 Total Gross Charge-off Amount | Tổng gross charge-off của dòng CHGOFF đã quan sát; BQ22 | `Σ_{r∈P, LoanStatus=CHGOFF} GrossChargeOffAmount` | — | — | `GrossChargeOffAmount`, `LoanStatus`, `ChargeOffDate` để kiểm DQ | Cờ chất lượng event date (audit) | STORED_MEASURE với điều kiện lọc semantic; PROPOSED |

## Phạm vi, chiều và giới hạn của từng KPI

Trong bảng, “P” luôn là **Default Population** ở trên; cột Filter Conditions ghi phần thêm hoặc điều kiện cửa sổ. `—` nghĩa là không thêm bộ lọc ngoài lát cắt BQ. Nguồn DQ chi tiết tại [Data Quality Report](../data_understanding/data_quality_report.md).

| KPI | Analysis Dimensions | Default Population; Filter Conditions | Aggregation Rule | Unit | Data Quality Concerns | Interpretation Limitations |
|---|---|---|---|---|---|---|
| K01 | FY, method, band, state/county, sector, lender, business type/age, status | P; —. Khi hiển thị count status, slice `LoanStatus` trên K01 | Count dòng, additive trong một snapshot | dòng | DQ15 | Không phải khoản vay duy nhất. |
| K02 | FY/quý, state/county, NAICS, lender, band, term, business age/type | P; — | SUM trong một snapshot | USD phê duyệt | DQ15 | Bao gồm CANCLD/COMMIT theo đề xuất; không phải giải ngân hay dư nợ. |
| K03 | FY, method, state | P; mẫu K01>0 | Tỷ số hai tổng | USD/dòng | DQ15 | Phụ thuộc cơ cấu trạng thái và dòng trùng; không phải average/loan duy nhất. |
| K04 | FY, state; cửa sổ FYTD | P; FY2020–FY2025 so năm đầy đủ liền trước có trong nguồn; FY2026 so cùng 01/10–30/06 với FY2025; mẫu >0 | Tính lại từ hai SUM, không cộng % | % | DQ15; đối chiếu ngày/FY | FY2020 không có FY2019 trong file; FY2026 không là full-year YoY. |
| K05 | `LoanSizeBand`, `ProjectState`, NAICS/sector, lender, `TermBand`, FY | P; `parent` theo quy ước trên; mẫu >0 | Tỷ số SUM nhóm/SUM parent | % | DQ07, DQ15; band/sector OPEN | Tỷ trọng thay đổi khi đổi parent; không là chỉ số rủi ro. |
| K06 | FY, method, state | P; — | SUM trong snapshot | USD bảo lãnh phê duyệt | DQ15; method mapping | Không phải claim SBA đã chi trả. |
| K07 | Lender `LocationID`, method, FY | P; — | Hiệu hai SUM cùng tập | USD phê duyệt | DQ15; kiểm tra `GrossApproval ≥ SBAGuaranteedApproval` khi mapping | Không phải dư nợ/phần tổn thất lender. |
| K08 | FY, state, NAICS/sector | P; K02>0 | Tỷ số hai SUM, không AVG tỷ lệ dòng | % | DQ15; sector OPEN | Không đo rủi ro; phải giữ cùng tập lọc. |
| K09 | NAICS/sector, state, FY | P; — | SUM trong snapshot | job được báo cáo | 45.739 dòng 0; DQ15 | Không là số người duy nhất, số tạo mới hay tác động nhân quả. |
| K10 | NAICS/sector, state, FY | P; K09>0 | Tỷ số hai SUM | USD/job được báo cáo | Jobs 0, DQ15 | Không là chi phí tạo việc làm/hiệu quả chương trình. |
| K11 | F/V nguồn, method, `LoanSizeBand` | P_r; loại **chỉ NULL về mặt công thức tạm**, giữ 0 để kiểm; chưa chốt đơn vị/mã F/V | Tổng rate / count rate, không SUM/AVG các average | đơn vị rate nguồn (OPEN) | DQ01–DQ02, DQ08; band OPEN | Không là lãi hiện hành; không công bố % cho tới khi xác minh. |
| K12 | Status, cohort FY, method, state, NAICS/sector, band | P; status literal; mẫu mọi status cùng lát cắt >0 | Count tử / count mẫu, tính lại mỗi cell | % dòng | DQ11, DQ15; DQ09–DQ13 nếu xét event date | CHGOFF/PIF là tỷ trọng **đã quan sát**, không phải default/repayment rate cuối cùng; cohort khác tuổi. |
| K13 | Cohort FY, state, NAICS/sector | P; `LoanStatus=CHGOFF`; không lọc theo `ChargeOffDate` cho cohort approval | SUM amount CHGOFF trong snapshot | USD gross charge-off | DQ09, DQ13, DQ15; kiểm CSV gốc: amount khác 0 chỉ ở CHGOFF trong snapshot này | Không là net SBA loss; 5 dòng thiếu ngày vẫn thuộc tổng theo status. |

**Loại các KPI trùng:** “Total Approval by Lender/State/Industry” = K02 theo dimension; “State/Industry Approval Share” = K05 theo parent; “Status Record Count” = K01 theo `LoanStatus`; “Observed CHGOFF/PIF Share” = K12 với `s` tương ứng. Average term không bắt buộc BQ16; collateral share thuộc BQ19 ngoài 19 câu chọn; resolved-only rate thuộc BQ24 ngoài phạm vi chính. Không thêm KPI 36 tháng vì 19 BQ hiện tại không yêu cầu fixed-window outcome.

**Xung đột với prototype:** [warehouse design](../02_warehouse_design.md) và [src/main.py](../../src/main.py) có `NonCancelledApproval`, `ResolvedCount`/resolved charge-off rate, weighted interest và duration. Chúng là hiện trạng prototype, không tự động vào catalog 19 BQ. K11 ở đây là bình quân không trọng số ứng viên cho BQ18; không dùng nhầm weighted-rate của prototype. Nếu nhóm chọn một định nghĩa khác, phải đổi công thức và rà lại mapping trước triển khai.
