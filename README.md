# SBA 7(a) Loan Portfolio — Data Warehouse & OLAP

Đồ án IS217: **Xây dựng hệ thống Kho dữ liệu và OLAP hỗ trợ phân tích danh mục tín dụng, bảo lãnh và kết quả khoản vay SBA 7(a) tại Hoa Kỳ giai đoạn FY2020–FY2026**.

> **Source of Truth:** [Trạng thái hiện hành](docs/00_current_status.md) chỉ rõ tài liệu canonical cho [Q1–Q15](docs/business_requirements/business_questions_current.md), [Target Schema Proposal](docs/dimensional_model/candidate_schema.md), [Measure Contract](docs/business_requirements/measure_contract_q1_q15.md), [business rules](docs/business_requirements/business_rule_register.md) và [Preprocessing Plan](docs/data_understanding/preprocessing_plan.md). Q1–Q15 gồm Q10 mới đã duyệt ở cấp nội dung; star 1F+8D là **PROPOSED TARGET SCHEMA**, chưa là Final/physical schema. Population, cấp NAICS Sector, TermBand tách `TERM_120`, `P I F→PIF` canonical và Q15 gates 30/5 đã `PROJECT_APPROVED`; NAICS reference/version/mapping còn `PENDING_VERIFICATION`. Script/tài liệu snowflake và 15 truy vấn cũ là **previous prototype**.

Dữ liệu thực tế: **388.338 dòng × 42 cột**, CSV 181.130.871 byte (~172,74 MiB), snapshot **30/06/2026**. FY2026 chưa đầy đủ. Nguồn gốc: [SBA FOIA](https://data.sba.gov/dataset/7a-504-foia); bản phân tích luôn dùng file cục bộ trong `data/raw/foia/`, không tự cập nhật bản online.

## Đọc trước: tài liệu hiện hành

- [Trạng thái và Source of Truth](docs/00_current_status.md)
- [Business Questions Q1–Q15](docs/business_requirements/business_questions_current.md)
- [Measure Contract Q1–Q15 — tài liệu, chưa triển khai](docs/business_requirements/measure_contract_q1_q15.md)
- [Measure–Dimension Matrix](docs/dimensional_model/measure_dimension_matrix.md)
- [Target Schema Proposal: star 1 Fact + 8 Dim](docs/dimensional_model/candidate_schema.md)
- [Business Rule Register](docs/business_requirements/business_rule_register.md)
- [Preprocessing Plan — chưa triển khai](docs/data_understanding/preprocessing_plan.md)

## Tài liệu và mã previous prototype

- [Đánh giá dataset trước đây](docs/01_feasibility.md)
- [Thiết kế snowflake previous prototype](docs/02_warehouse_design.md)
- [Hướng dẫn SSIS/SSAS previous prototype](docs/03_implementation.md)
- [15 manual và 5 Excel Pivot previous prototype](docs/04_analysis_catalog.md)
- [15 MDX previous prototype](Source/SSAS/15_queries.mdx)
- [Đặc tả BI và mining previous prototype](docs/05_bi_mining.md)
- [Tham khảo đồ án mẫu](docs/06_references.md)
- [Checklist bàn giao](docs/07_delivery.md)
- [Kết quả profiling toàn bộ nguồn](docs/data_profile.json)
- [Kiểm chứng đã thực hiện](docs/validation.md)
- [Từ điển 42 cột từ workbook nguồn](docs/data_dictionary.md)

## Chạy lại previous Python prototype

Python 3.10+:

```powershell
python -m pip install -r requirements.txt
python -m src.main
python -m unittest discover -s tests -v
python -m src.mining
```

Pipeline **prototype cũ** xuất 8 dimension, 1 fact, quality issues, mart BI và dữ liệu mining vào `data/processed/`. Nó chưa thực hiện [Preprocessing Plan hiện hành](docs/data_understanding/preprocessing_plan.md) hoặc Target Schema Proposal star 1 Fact + 8 Dim. Hai mô hình đều có 8 dimension nhưng khác cấu trúc và business rules. Không tự kết nối database. Giữ nguyên mọi dòng nguồn; khóa dòng chỉ có ý nghĩa trong đúng file và SHA-256 của lần chạy. Chạy lại sẽ ghi đè các file đầu ra cùng tên; đây là **full rebuild một snapshot**, không phải incremental ETL.

`sql/01_warehouse.sql`, [hướng dẫn SSIS](docs/03_implementation.md) và `sql/02_validation.sql` phục vụ **previous prototype**; không dùng chúng để tạo database của candidate hiện hành trước khi có physical mapping mới. Script DDL không dùng để chạy lại trên database đã có các bảng này.

## Trạng thái repo

Đã có pipeline Python, SQL Server DDL, thiết kế SSIS/SSAS, MDX theo hợp đồng cube, truy vấn manual/Pivot, kế hoạch BI và baseline mining cho **previous prototype**. Q1–Q15 mới và Target Schema Proposal star 1 Fact + 8 Dim hiện mới ở mức tài liệu. Chưa có `.dtproj`, `.dtsx`, `.dwproj`, cube đã deploy, Excel Pivot kết nối cube, `.pbix`, link Looker, `.mdf/.ldf`, video hay báo cáo `.docx`. Các truy vấn MDX cũ cần thiết kế/kiểm chứng lại sau khi business rules và physical mapping được duyệt.

Stack mục tiêu: SQL Server Database Engine + SSIS + SSAS **Multidimensional** trên Windows; Power BI Desktop, Excel, Looker Studio. Python hỗ trợ kiểm tra/chuẩn bị dữ liệu và mining, không thay thế phần SSIS bắt buộc.

## Cấu trúc

```text
data/
├── raw/foia/            Nguồn gốc nguyên vẹn: CSV + dictionary XLSX
├── staging/             Dữ liệu trung gian do ETL tạo
└── processed/           Dimension, fact, mart và quality outputs
references/              5 báo cáo PDF năm trước
src/                     Pipeline chuẩn bị dữ liệu + baseline mining
sql/                     DDL và đối soát SQL Server
Source/SSIS/             Hướng dẫn, nơi lưu project thật sau khi dựng
Source/SSAS/             MDX + nơi lưu project cube
Source/Excel/            Hướng dẫn 5 Pivot truy vấn cube
Source/DataMining/       Hướng dẫn chạy baseline
dashboards/              Đặc tả Power BI/Looker
docs/                    Phân tích, thiết kế, kiểm tra, kế hoạch
Database/ Video/ Document/  Nơi hoàn thiện sản phẩm nộp
group_info.txt           Mẫu thông tin/phân công, chưa điền thành viên
```

Tên thư mục checkout hiện tại giữ nguyên để không phá đường dẫn của công cụ. Khi hoàn tất, nên đổi tên repository GitHub thành `sba-7a-dwh-olap`. `data/raw/foia/` sẽ được copy vào `Data/` của bộ nộp cuối; không nhân đôi CSV lớn trong repo. File CSV vượt 100 MB: quản lý dữ liệu ngoài Git hoặc cấu hình Git LFS trước khi push.
