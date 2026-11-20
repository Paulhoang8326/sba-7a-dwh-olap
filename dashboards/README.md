# Báo cáo – Chương 4

Mỗi công cụ có 3 report (Q6, Q8, Q15). Trang Q8 có report dạng **Grouping and Totals**: Looker dùng pivot table, Power BI dùng Matrix, cả hai có tổng phụ theo bang và tổng cộng.

| File | Nội dung |
|---|---|
| [thao_tac_looker_Q6_Q8_Q15.md](thao_tac_looker_Q6_Q8_Q15.md) | Thao tác từng bước trên Looker Studio, nguồn là CSV xuất từ DWH. Đã chạy thử trên giao diện thật. |
| [thao_tac_powerbi_Q6_Q8_Q15.md](thao_tac_powerbi_Q6_Q8_Q15.md) | Thao tác từng bước trên Power BI, Connect live vào cube SSAS. Gồm cả đoạn MDX bổ sung measure cho cube. Chưa chạy thử trên SSAS thật. |

Nguồn dữ liệu:
- Looker: `data/processed/bi/sba7a_bi_dataset.csv`, tạo bằng [sql/07_export_bi_dataset.sql](../sql/07_export_bi_dataset.sql) trong SSMS hoặc `python -m src.reporting.export_bi_dataset`. File này không commit (gitignore).
- Power BI: cube `SBA7A DWH_DSV`, cộng thêm các measure trong [calc_powerbi_q6_q8_q15.mdx](../OLAP_Queries/MDX_Queries/calc_powerbi_q6_q8_q15.mdx).

Đặc tả BI cũ (prototype, không còn dùng): [05_bi_mining.md](../docs/archive/other/05_bi_mining.md).
