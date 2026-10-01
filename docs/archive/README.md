# Historical documentation archive

> [!WARNING]
> Bắt đầu từ [docs/00_current_status.md](../00_current_status.md) cho trạng thái hiện hành. Tài liệu tại đây chỉ phục vụ lịch sử; không làm nguồn quyết định cho Q1–Q15, business rules hoặc target model hiện hành.

Các tài liệu dưới đây đã có bằng chứng historical/deprecated/previous requirements trong repository trước khi di chuyển. Nội dung gốc được bảo tồn; chỉ thêm banner và điều chỉnh Markdown link destinations để giữ liên kết hợp lệ.

## Tài liệu đã archive

| Đường dẫn trước đây | Tài liệu lưu trữ |
|---|---|
| `docs/01_feasibility.md` | [01_feasibility.md](other/01_feasibility.md) |
| `docs/02_warehouse_design.md` | [02_warehouse_design.md](dimensional_model/02_warehouse_design.md) |
| `docs/03_implementation.md` | [03_implementation.md](olap/03_implementation.md) |
| `docs/04_analysis_catalog.md` | [04_analysis_catalog.md](olap/04_analysis_catalog.md) |
| `docs/05_bi_mining.md` | [05_bi_mining.md](other/05_bi_mining.md) |
| `docs/07_delivery.md` | [07_delivery.md](other/07_delivery.md) |
| `docs/business_requirements/business_objectives.md` | [business_objectives.md](business_requirements/business_objectives.md) |
| `docs/business_requirements/business_questions_catalog.md` | [business_questions_catalog.md](business_requirements/business_questions_catalog.md) |
| `docs/business_requirements/business_questions_selection.md` | [business_questions_selection.md](business_requirements/business_questions_selection.md) |
| `docs/business_requirements/business_rules.md` | [business_rules.md](business_requirements/business_rules.md) |
| `docs/business_requirements/derived_attribute_requirements.md` | [derived_attribute_requirements.md](business_requirements/derived_attribute_requirements.md) |
| `docs/business_requirements/kpi_business_question_mapping.md` | [kpi_business_question_mapping.md](business_requirements/kpi_business_question_mapping.md) |
| `docs/business_requirements/kpi_catalog.md` | [kpi_catalog.md](business_requirements/kpi_catalog.md) |
| `docs/business_requirements/olap_analysis_requirements.md` | [olap_analysis_requirements.md](business_requirements/olap_analysis_requirements.md) |
| `docs/validation.md` | [validation.md](other/validation.md) |

## Các điểm giữ lại để review

- README tại `Source/`, `Database/` và `dashboards/` vẫn là index thư mục/trạng thái, có hướng dẫn prototype. Giữ tại chỗ; các link tới archive chỉ là historical references.
- [Document/README.md](../../Document/README.md) và [Database/README.md](../../Database/README.md) còn dẫn checklist cũ cho báo cáo/bàn giao. Checklist đó cần được review trước khi dùng cho target mới; chưa có checklist current thay thế trong lần dọn này.
- [PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md) còn dẫn feasibility/checklist cũ ở các phần bối cảnh và sản phẩm dự kiến. Đây là dependency cần review; không copy logic cũ sang canonical.
- [docs/data_dictionary.md](../data_dictionary.md) chưa được đánh dấu deprecated và còn hữu ích cho định nghĩa nguồn; có một số ghi chú vị trí lưu theo prototype cần review.
- [PROJECT_STATUS.md](../../PROJECT_STATUS.md) chứa cả trạng thái hiện hành và lịch sử kiểm chứng; giữ tại chỗ.
- Các JSON profiling/mining, SQL/Python/MDX, dataset và DBML giữ nguyên vị trí/nội dung.
- Các đường dẫn viết dưới dạng literal trong nội dung lịch sử được giữ nguyên; Markdown links đã được điều chỉnh theo vị trí mới.
