# Ánh xạ KPI ↔ 19 Business Questions

Phạm vi lấy từ [Business Questions Selection](business_questions_selection.md), nội dung câu hỏi từ [Business Questions Catalog](business_questions_catalog.md), định nghĩa KPI từ [KPI Catalog](kpi_catalog.md). `K01` là count dòng; `K02` là tổng vốn phê duyệt; `K05` là tỷ trọng **số tiền**, `K12` là tỷ trọng **số dòng**. Các ID dưới đây là **ứng viên**, không phải hợp đồng measure đã chốt.

| BQ | Nội dung trọng tâm | KPI phục vụ | Chiều/lát cắt và điều kiện riêng | Tình trạng |
|---|---|---|---|---|
| BQ01 | Vốn theo FY/quý/state | K02 | `ApprovalFY`, fiscal quarter từ `ApprovalDate`, `ProjectState` | Fiscal derivation PROPOSED |
| BQ02 | Count và bình quân theo FY/method | K01, K03; K02 là tử số | `ApprovalFY`, `ProcessingMethod`; count là dòng | PROPOSED |
| BQ03 | Tăng trưởng vốn | K04; K02 là thành phần | FY đầy đủ, FY2026 cùng kỳ 01/10–30/06; state | PROPOSED; FYTD phải chốt |
| BQ04 | Cơ cấu nhóm quy mô × tuổi doanh nghiệp | K01, K02, K05 | `LoanSizeBand`, `BusinessAge`, FY; parent của share là mọi band trong FY×age | CONDITIONAL: ngưỡng band |
| BQ06 | SBA guarantee theo FY/method | K06 | FY, method | PROPOSED |
| BQ07 | Tỷ trọng bảo lãnh | K08; K06/K02 là thành phần | FY, state, `NaicsCode`; sector nếu mapping được xác minh | PROPOSED; sector OPEN |
| BQ08 | Phần ngoài bảo lãnh theo lender/method | K07 | `LocationID` lender hiện tại, method, FY | PROPOSED |
| BQ10 | Vốn tại project state/county | K02, K01 | `ProjectState` + `ProjectCounty`, FY | PROPOSED |
| BQ11 | Tỷ trọng state trong FY | K05; K02 là thành phần | Parent = mọi state cùng FY và slicer còn lại | PROPOSED |
| BQ12 | Ngành × state × FY | K01, K02, K05 | `NaicsCode`; sector code/name chỉ sau mapping; parent share = mọi ngành trong state×FY | CONDITIONAL: NAICS sector |
| BQ14 | Jobs báo cáo và vốn/job | K09, K10; K02 là tử số | NAICS, state, FY; K10 chỉ khi jobs tổng >0 | PROPOSED |
| BQ15 | Tập trung theo lender hiện tại | K02, K01, K05 | `LocationID`; Top N là xếp hạng K02, không phải KPI mới; parent toàn lender trong FY | PROPOSED |
| BQ16 | Cơ cấu nhóm kỳ hạn | K01, K02, K05 | `TermBand`, method, FY; parent mọi band trong method×FY; 0 riêng | CONDITIONAL: ngưỡng band |
| BQ17 | Business type/age | K01, K02 | `BusinessType`, `BusinessAge`, FY, state; unknown/Unanswered riêng | PROPOSED |
| BQ18 | Lãi suất ban đầu | K11; K01 để nêu cỡ mẫu | `FixedorVariableInterestInd`, method, `LoanSizeBand` | OPEN: đơn vị, F/V, rate=0 |
| BQ20 | Cơ cấu status tại snapshot | K01, K12 | `LoanStatus`, FY, method, `AsOfDate`; mẫu mọi status | PROPOSED; mapping PIF OPEN |
| BQ21 | Tỷ trọng CHGOFF đã quan sát | K12 với `s=CHGOFF`; K01 là count mẫu | Cohort FY, state, NAICS; giữ mọi status ở mẫu | PROPOSED; censoring |
| BQ22 | Gross charge-off | K13; K01 đếm CHGOFF | Cohort FY, state, NAICS; event date chỉ để DQ | PROPOSED; BR10 |
| BQ23 | Tỷ trọng PIF đã quan sát | K12 với literal `s=P I F`; K01 là count mẫu | Cohort FY, `LoanSizeBand`; giữ mọi status ở mẫu | CONDITIONAL: mapping PIF, band |

**Coverage:** 19/19 BQ được chọn có ít nhất một KPI. 13 KPI được dùng: K01–K13. BQ05, BQ09, BQ13, BQ19, BQ24 ở phạm vi mở rộng theo [selection](business_questions_selection.md); vì vậy không có KPI riêng cho collateral hoặc tỷ lệ trong tập resolved. `K03`, `K04`, `K05`, `K08`, `K10`, `K11`, `K12` phải được tính lại tại từng cell OLAP; không cộng các giá trị %/bình quân đã tổng hợp. Toàn bộ count và amount chỉ cộng trong **một** snapshot.

**Điều kiện trước sử dụng số chính thức:** chốt population gồm/loại CANCLD/COMMIT, ngưỡng hai band, NAICS sector reference, nhãn `P I F` và rate; xem [Business Rules](business_rules.md) và [Derived Attribute Requirements](derived_attribute_requirements.md). Với BQ18, K11 là công thức tạm có trạng thái OPEN, không phải KPI đủ điều kiện công bố.
