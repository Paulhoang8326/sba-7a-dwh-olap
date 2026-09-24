# Data layers

```text
data/
├── raw/foia/    Dữ liệu SBA gốc, không chỉnh sửa
├── staging/     Dữ liệu trung gian của ETL
└── processed/   Dimension, fact, mart, quality log và mining input
```

File CSV dữ liệu nguồn trong `data/raw/foia/*.csv` được theo dõi và commit qua **Git LFS** (theo cấu hình `.gitattributes`). Trước khi clone repository, cần đảm bảo máy đã cài đặt Git LFS:

```bash
git lfs install
```

Sau khi clone, nếu file CSV trong `data/raw/foia/` chỉ là con trỏ LFS (~134 byte), hãy tải nội dung thật bằng lệnh:

```bash
git lfs pull
```

Chỉ có dữ liệu trung gian `data/staging/*` và kết quả chuẩn hóa `data/processed/*` là **không được commit** (đã được cấu hình trong `.gitignore`). Sau khi đã có file CSV nguồn, chạy pipeline để sinh toàn bộ warehouse tables:

```bash
python -m src.main
```

Workbook từ điển dữ liệu và các file README được giữ trực tiếp trong Git. Không đặt file kết quả thủ công vào `processed/` vì pipeline có thể ghi đè các file cùng tên.
