# Từ điển Dữ liệu (Data Dictionary)
**Dự án:** Kho dữ liệu & Hệ thống OLAP Phân tích Gánh nặng Rối loạn Tâm lý Toàn cầu (IS217)

---

## 1. Bảng Chiều (Dimension Tables)

### 1.1 `dwh.dim_location` (Chiều Địa lý & Phân loại kinh tế)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Mô tả ý nghĩa |
| :--- | :--- | :---: | :---: | :--- |
| `location_key` | INT / SERIAL | **PK** | NOT NULL | Khóa thay thế (Surrogate Key) đại diện cho quốc gia/vùng lãnh thổ |
| `location_id` | INT | | | Mã định danh quốc gia theo chuẩn IHME GBD |
| `location_name` | VARCHAR(255) | **AK** | NOT NULL | Tên chuẩn hóa của quốc gia hoặc vùng lãnh thổ (204 quốc gia) |
| `iso3` | VARCHAR(10) | | | Mã chuẩn hóa ISO 3 ký tự (e.g. VNM, USA, FRA) |
| `region` | VARCHAR(150) | | | 7 Phân vùng khu vực địa lý theo chuẩn World Bank |
| `income_group` | VARCHAR(100) | | | Phân loại 4 nhóm thu nhập của World Bank (Low, Lower middle, Upper middle, High) |

### 1.2 `dwh.dim_time` (Chiều Thời gian)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Mô tả ý nghĩa |
| :--- | :--- | :---: | :---: | :--- |
| `time_key` | INT | **PK** | NOT NULL | Khóa thời gian dạng số (YYYY, ví dụ: 2013, 2023) |
| `year` | INT | **AK** | NOT NULL | Năm quan sát (2013 đến 2023) |
| `period_phase` | VARCHAR(50) | | | Phân kỳ: Pre-COVID (2013-2019), COVID-19 Peak (2020-2021), Post-COVID (2022-2023) |

### 1.3 `dwh.dim_cause` (Chiều Rối loạn tâm lý)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Mô tả ý nghĩa |
| :--- | :--- | :---: | :---: | :--- |
| `cause_key` | INT / SERIAL | **PK** | NOT NULL | Khóa thay thế cho loại bệnh/rối loạn tâm thần |
| `cause_id` | INT | **AK** | NOT NULL | Mã ID rối loạn theo chuẩn IHME GBD |
| `cause_name` | VARCHAR(255) | | NOT NULL | Tên rối loạn tâm thần (Depressive disorders, Anxiety, Schizophrenia,...) |
| `cause_category` | VARCHAR(150) | | | Phân loại nhóm y khoa (Mood & Affective, Neurotic & Anxiety, Neurodevelopmental,...) |
| `is_overall_total` | BOOLEAN | | NOT NULL | Cờ đánh dấu dòng tổng hợp `Mental disorders` (TRUE) để tránh cộng dồn trùng lặp |

### 1.4 `dwh.dim_demographic` (Chiều Nhân khẩu học)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Mô tả ý nghĩa |
| :--- | :--- | :---: | :---: | :--- |
| `demographic_key` | INT / SERIAL | **PK** | NOT NULL | Khóa thay thế tổ hợp giới tính và độ tuổi |
| `sex_id` | INT | | NOT NULL | Mã giới tính (1: Male, 2: Female) |
| `sex_name` | VARCHAR(50) | | NOT NULL | Tên giới tính (Male, Female) |
| `age_id` | INT | | NOT NULL | Mã nhóm tuổi (284) |
| `age_name` | VARCHAR(100) | | NOT NULL | Tên nhóm tuổi lao động (`20-54 years`) |

---

## 2. Bảng Fact (Fact Tables)

### 2.1 `dwh.fact_mental_health` (Gánh nặng sức khỏe tâm thần)
* **Độ hạt (Grain):** 1 dòng tương ứng với 1 bệnh lý, 1 nhóm nhân khẩu học tại 1 quốc gia trong 1 năm cụ thể.
* **Số dòng sau Pivot:** 40,392 dòng.

| Tên cột | Kiểu dữ liệu | Phân loại chỉ số | Mô tả ý nghĩa |
| :--- | :--- | :--- | :--- |
| `fact_id` | BIGSERIAL (PK) | - | Khóa chính bảng fact |
| `location_key` | INT (FK) | - | Tham chiếu đến `dwh.dim_location` |
| `time_key` | INT (FK) | - | Tham chiếu đến `dwh.dim_time` |
| `cause_key` | INT (FK) | - | Tham chiếu đến `dwh.dim_cause` |
| `demographic_key` | INT (FK) | - | Tham chiếu đến `dwh.dim_demographic` |
| `dalys_number` | NUMERIC(18,4) | **Additive** | Tổng số năm sống bị mất do tàn tật/tử vong sớm (DALYs) |
| `dalys_percent` | NUMERIC(18,8) | **Non-additive** | Tỷ trọng DALYs tâm thần trên tổng gánh nặng mọi bệnh tật |
| `dalys_lower` | NUMERIC(18,4) | Informational | Giới hạn dưới khoảng tin cậy 95% của DALYs |
| `dalys_upper` | NUMERIC(18,4) | Informational | Giới hạn trên khoảng tin cậy 95% của DALYs |
| `prevalence_number` | NUMERIC(18,4) | **Additive** | Số ca mắc bệnh ước tính trong độ tuổi 20-54 |
| `prevalence_percent`| NUMERIC(18,8) | **Non-additive** | Tỷ lệ dân số mắc bệnh (%) |
| `prevalence_lower` | NUMERIC(18,4) | Informational | Giới hạn dưới khoảng tin cậy 95% của hiện mắc |
| `prevalence_upper` | NUMERIC(18,4) | Informational | Giới hạn trên khoảng tin cậy 95% của hiện mắc |

### 2.2 `dwh.fact_socioeconomic` (Chỉ số Kinh tế - Xã hội)
* **Độ hạt (Grain):** 1 dòng tương ứng với 1 quốc gia trong 1 năm.
* **Số dòng:** 2,200 dòng.

| Tên cột | Kiểu dữ liệu | Phân loại chỉ số | Mô tả ý nghĩa |
| :--- | :--- | :--- | :--- |
| `fact_se_id` | SERIAL (PK) | - | Khóa chính bảng fact kinh tế |
| `location_key` | INT (FK) | - | Tham chiếu đến `dwh.dim_location` |
| `time_key` | INT (FK) | - | Tham chiếu đến `dwh.dim_time` |
| `population` | NUMERIC(18,2) | **Semi-additive** | Tổng dân số quốc gia (chỉ cộng dồn theo không gian, không cộng theo năm) |
| `gdp_per_capita_usd` | NUMERIC(18,2) | **Non-additive** | GDP bình quân đầu người tính bằng USD |
| `gdp_total_usd` | NUMERIC(24,2) | **Semi-additive** | Tổng quy mô GDP quốc gia tính bằng USD |
