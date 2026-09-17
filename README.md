# 🧠 Global Mental Health DWH & OLAP System

Hệ thống Kho dữ liệu (Data Warehouse) và Phân tích trực tuyến (OLAP) phục vụ nghiên cứu **Gánh nặng rối loạn tâm lý toàn cầu và mối liên hệ với các yếu tố kinh tế - xã hội**.

* **Môn học:** IS217 - Kho dữ liệu và OLAP
* **Trường:** Trường Đại học Công nghệ Thông tin - ĐHQG-HCM (UIT)
* **Dữ liệu nguồn:** IHME Global Burden of Disease (GBD 2013-2023) & World Bank Socioeconomic Indicators.

---

## 🏛️ Kiến trúc Mô hình Dữ liệu (Fact Constellation Schema)

Hệ thống sử dụng mô hình **Fact Constellation (Galaxy Schema)** với 2 bảng Fact chia sẻ các Conformed Dimensions dạng Star:

* **Fact 1: `Fact_Mental_Health`** (Grain: Quốc gia, Năm, Rối loạn tâm thần, Giới tính, Độ tuổi) -> Chỉ số: DALYs, Prevalence (Number & Percent).
* **Fact 2: `Fact_SocioEconomic`** (Grain: Quốc gia, Năm) -> Chỉ số: Dân số, GDP bình quân, Tổng GDP (giải quyết triệt để lỗi Fan-out duplication khi gộp chỉ số kinh tế vào dữ liệu dịch tễ).
* **Conformed Dimensions:** `Dim_Location`, `Dim_Time`, `Dim_Cause`, `Dim_Demographic`.

---

## 📂 Cấu trúc Thư mục Dự án

```text
mental-health-dwh-olap/
├── .gitignore                      # Ignore venv, cache, intermediate data
├── README.md                       # Giới thiệu & Hướng dẫn sử dụng
├── requirements.txt                # Thư viện Python
├── docker-compose.yml              # Dịch vụ PostgreSQL 16 + pgAdmin
├── .env.example                    # Template biến môi trường
│
├── data/
│   ├── 01_raw/                     # Dữ liệu thô (GBD, kinh tế, quốc gia)
│   ├── 02_staging/                 # Dữ liệu làm sạch sơ bộ
│   └── 03_processed/               # Dữ liệu chuẩn hóa xuất khẩu (Star Schema)
│
├── sql/
│   ├── 00_init_db.sql              # Khởi tạo schemas (staging, dwh, marts)
│   ├── 01_staging/                 # DDL bảng staging
│   ├── 02_dimensions/              # DDL & nạp các bảng Dimension
│   ├── 03_facts/                   # DDL & nạp các bảng Fact
│   └── 04_olap_queries/            # Truy vấn OLAP (Rollup, Drilldown, Slice, Dice, Pivot)
│
├── src/                            # Pipeline ETL (Python)
│   ├── config.py                   # Cấu hình đường dẫn và môi trường
│   ├── etl/                        # Module Extract - Transform - Load
│   ├── utils/                      # Helper logger & database connection
│   └── main.py                     # Entrypoint chạy toàn bộ pipeline
│
├── notebooks/                      # Phân tích EDA & Khai phá tương quan
├── dashboards/                     # Báo cáo Power BI & Streamlit app
└── docs/                           # Từ điển dữ liệu & Sơ đồ kiến trúc
```

---

## 🚀 Hướng dẫn Khởi chạy Nhanh

### 1. Chạy Pipeline ETL làm sạch & chuyển đổi dữ liệu
Chạy script ETL Python để trích xuất dữ liệu từ `data/01_raw/`, làm sạch và xuất các bảng Dimension/Fact vào `data/03_processed/`:
```bash
python -m src.main
```

### 2. Khởi động Cơ sở dữ liệu PostgreSQL (Tùy chọn)
Nếu bạn có cài đặt Docker:
```bash
docker-compose up -d
```
* **PostgreSQL:** `localhost:5432` (User: `postgres`, Pass: `postgres`, DB: `mental_health_dwh`)
* **pgAdmin:** `http://localhost:5050` (Email: `admin@admin.com`, Pass: `admin`)

### 3. Chạy Thử nghiệm Web Dashboard (Streamlit)
```bash
pip install -r requirements.txt
streamlit run dashboards/app/app.py
```
