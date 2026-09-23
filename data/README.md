# Data layers

```text
data/
├── raw/foia/    Dữ liệu SBA gốc, không chỉnh sửa
├── staging/     Dữ liệu trung gian của ETL
└── processed/   Dimension, fact, mart, quality log và mining input
```

`data/raw/foia/*.csv`, `data/staging/*` và `data/processed/*` không được commit. Sau khi clone, đặt CSV nguồn đúng tên trong `data/raw/foia/`, rồi chạy `python -m src.main`.

Workbook từ điển dữ liệu và các file README nhỏ được giữ trong Git. Không đặt file kết quả thủ công vào `processed/` vì pipeline có thể ghi đè các file cùng tên.
