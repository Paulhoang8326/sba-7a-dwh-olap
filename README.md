# SBA 7(a) Loan Portfolio — Data Warehouse & OLAP

Đồ án IS217: **Xây dựng hệ thống Kho dữ liệu và OLAP hỗ trợ phân tích danh mục tín dụng, bảo lãnh và kết quả khoản vay SBA 7(a) tại Hoa Kỳ giai đoạn FY2020–FY2026**.

Dữ liệu thực tế: **388.338 dòng × 42 cột**, CSV 181.130.871 byte (~172,74 MiB), snapshot **30/06/2026**. FY2026 chưa đầy đủ. Nguồn gốc: [SBA FOIA](https://web.data.sba.gov/en/dataset/7-a-504-foia); bản phân tích luôn dùng file cục bộ trong `data/raw/foia/`, không tự cập nhật bản online.

## Đọc trước

- [Đánh giá dataset và hướng triển khai](docs/01_feasibility.md)
- [Mô hình bông tuyết, grain và measures](docs/02_warehouse_design.md)
- [SSIS, SSAS và quy ước cube](docs/03_implementation.md)
- [15 manual queries và 5 Excel Pivot](docs/04_analysis_catalog.md)
- [15 MDX queries](Source/SSAS/15_queries.mdx)
- [6 báo cáo BI và data mining](docs/05_bi_mining.md)
- [Tham khảo đồ án mẫu](docs/06_references.md)
- [Checklist bàn giao](docs/07_delivery.md)
- [Kết quả profiling toàn bộ nguồn](docs/data_profile.json)
- [Kiểm chứng đã thực hiện](docs/validation.md)
- [Từ điển 42 cột từ workbook nguồn](docs/data_dictionary.md)

## Chạy nền tảng chuẩn bị dữ liệu

Python 3.10+:

```powershell
python -m pip install -r requirements.txt
python -m src.main
python -m unittest discover -s tests -v
python -m src.mining
```

Pipeline xuất 8 dimension, 1 fact, quality issues, mart BI và dữ liệu mining vào `data/processed/`. Không tự kết nối database. Giữ nguyên mọi dòng nguồn; khóa dòng chỉ có ý nghĩa trong đúng file và SHA-256 của lần chạy. Chạy lại sẽ ghi đè các file đầu ra cùng tên; đây là **full rebuild một snapshot**, không phải incremental ETL.

Tạo database mới bằng `sql/01_warehouse.sql`, nạp CSV theo [hướng dẫn SSIS](docs/03_implementation.md), đối soát bằng `sql/02_validation.sql`. Script DDL không dùng để chạy lại trên database đã có các bảng này.

## Trạng thái repo

Đã có pipeline Python, SQL Server DDL, thiết kế SSIS/SSAS, MDX theo hợp đồng cube, truy vấn manual/Pivot, kế hoạch BI và baseline mining. Đây là nền tảng và lộ trình thực hiện, **chưa phải bộ bài nộp hoàn chỉnh**: chưa có `.dtproj`, `.dtsx`, `.dwproj`, cube đã deploy, Excel Pivot kết nối cube, `.pbix`, link Looker, `.mdf/.ldf`, video hay báo cáo `.docx`. Các truy vấn MDX cần kiểm chứng sau khi dựng cube đúng quy ước.

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
