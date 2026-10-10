> **HISTORICAL REFERENCE — NOT CURRENT CONTRACT.** Giữ nguyên nội dung đóng góp từ `main` để tham khảo lịch sử. Các tên bảng, số Dimensions và trạng thái implementation bên dưới không thay thế [trạng thái hiện hành](../00_current_status.md), [schema hiện hành](../dimensional_model/candidate_schema.md) hoặc [kế hoạch SSIS Chương 2](../etl/chapter2_ssis_plan.md). Chương 1 hiện là `CHAPTER 1 READY TO FREEZE`; preprocessing đã tích hợp và TSV đã tái lập, warehouse/SSIS chưa triển khai.

# Bus Matrix

PROPOSED, 2026-09-28. Một process quan sát **danh mục hồ sơ công bố tại snapshot** dùng một FactLoanSnapshot. Các hàng G01–G05 là analysis groups trên cùng grain, không năm fact/business processes độc lập. Căn cứ [objectives](../business_requirements/business_objectives.md), [OLAP](../business_requirements/olap_analysis_requirements.md), [schema](star_schema.md).

## 1. Analysis Group × Dimension

X=trục chính của ít nhất một BQ trong nhóm; S=slicer dùng chung có thể dùng, không bắt buộc; C=sector roll-up cần reference; —=không cần trực tiếp. Date luôn approval cohort + as-of, các event roles chỉ khi mở phân tích sự kiện và kiểm DQ.

| Analysis Group | DimDate | DimProjectGeography | DimIndustry | DimLender | DimBusiness | DimLoanCharacteristics | DimLoanStatus |
|---|---|---|---|---|---|---|---|
| G01 Loan Approval — BQ01–04 | X | X | S | S | X | X | S (population) |
| G02 SBA Guarantee — BQ06–08 | X | X | X/C | X | S | X | S (population) |
| G03 Geography & Industry — BQ10–12,14 | X | X | X/C | S | S | S | S (population) |
| G04 Portfolio Composition — BQ15–18 | X | X | S | X | X | X | S (population) |
| G05 Status & Outcomes — BQ20–23 | X | X | X/C | S | S | X | X |

Mọi nhóm chia sẻ date, geography, industry/lender/business/characteristics/status khi có nhu cầu slice; một fact không yêu cầu tất cả chiều xuất hiện trong mọi BQ. Không dùng loan status làm một thời gian thứ hai.

## 2. KPI × Dimension trong các BQ được chọn

X là chiều yêu cầu bởi ít nhất một BQ sử dụng KPI; S là filter chung, C là sector conditional. Bảng này không cấm slice trên chiều khác vì Fact còn liên kết đầy đủ.

| KPI | Date | Geography | Industry | Lender | Business | Characteristics | Status |
|---|---|---|---|---|---|---|---|
| K01 Count | X | X | X/C | X | X | X | X |
| K02 Approval | X | X | X/C | X | X | X | S |
| K03 Avg approval | X | S | — | — | — | X | S |
| K04 Growth | X | X | — | — | — | — | S |
| K05 Approval share | X | X | X/C | X | X | X | S |
| K06 SBA approval | X | S | — | — | — | X | S |
| K07 Non-SBA approval | X | — | — | X | — | X | S |
| K08 Guarantee ratio | X | X | X/C | — | — | — | S |
| K09 Jobs | X | X | X/C | — | — | — | S |
| K10 Approval/job | X | X | X/C | — | — | — | S |
| K11 Initial rate | S | S | — | — | — | X | S |
| K12 Status share | X | X | X/C | S | S | X | X |
| K13 Gross charge-off | X | X | X/C | — | — | S | X |

K04 so hai approval windows trong cùng snapshot. K12 giữ tất cả status ở mẫu số. K13 lọc CHGOFF theo approval cohort; event date không tự loại dòng. Không SUM rate/share/average/growth giữa các ô. [Fact contract](fact_table_design.md) là nơi định nghĩa công thức, [coverage](schema_coverage.md) chỉ rõ các decision gates.
