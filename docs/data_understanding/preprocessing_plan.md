# Preprocessing Plan — SBA 7(a)

> **Trạng thái 2026-10-01: IMPLEMENTED — Phase 1.** Kế hoạch dưới đây đã được triển khai bằng `src/etl/preprocess.py` (PRE-01–PRE-10 ứng với P1.1–P1.14 của [ETL Implementation Plan §3](../etl/etl_implementation_plan.md)). Xem [Giải thích Phase 1](../etl/phase1_preprocessing_explained.md) để biết code thật làm gì, số liệu và chỗ khác plan. Nội dung bên dưới giữ nguyên là kế hoạch gốc; NAICS mapping vẫn `PENDING_VERIFICATION`.

> **PLANNED / NOT IMPLEMENTED**, cập nhật 2026-09-30. Đây là kế hoạch logic để triển khai và viết phần tiền xử lý trong Chương 1; chưa chạy cleaning, chưa xuất standardized dataset, chưa thiết kế SSIS package, nạp Fact/Dimension hoặc build Cube. Phạm vi Q1–Q15 và rule: [current questions](../business_requirements/business_questions_current.md), [register](../business_requirements/business_rule_register.md).

## Input, nguyên tắc và output dự kiến

Input là CSV SBA 7(a) FOIA bất biến, 388.338 published records × 42 thuộc tính, một snapshot `2026-06-30`, cùng workbook sheet `7(a) Data Dictionary`. Baseline có ở [Overview](data_overview.md), [Profiling](data_profiling_report.md), [Data Quality](data_quality_report.md). Output **dự kiến**, chưa tồn tại: standardized dataset, DQ report theo bản ghi, reconciliation report và manifest gồm source checksum + rule version. Giữ raw values hoặc liên kết truy vết đầy đủ; không `drop_duplicates`, `dropna()` toàn bảng hay fill mean/mode chỉ vì bài mẫu làm vậy.

```text
Raw SBA CSV bất biến + dictionary
  → Validate checksum/schema/record ordinal
  → Parse datatype trong bản làm việc; mã giữ text
  → Chuẩn hóa blank/whitespace có kiểm soát, giữ raw
  → Kiểm numeric/date/FY/status và tạo DQ issues
  → Áp dụng chỉ các mapping/derived attributes đã approved
  → Reconcile row count, sums, FY/status, raw ↔ standardized
  → Xuất standardized dataset + DQ report + manifest
```

## Quy tắc theo nhóm dữ liệu

| Nhóm | Baseline verified | Cách xử lý đề xuất | Dependency |
|---|---|---|---|
| Kiểu dữ liệu | CSV lưu text; 5 trường ngày không có parse error; các amount/rate/term/jobs không thấy parse error hoặc số âm ở snapshot này. | Parse date ISO; amount/rate dạng decimal; kiểm `JobsSupported` và `TermInMonths` là số nguyên về nghĩa. Giữ `LocationID`, ZIP, NAICS, FDIC/NCUA, district dạng text để không mất số 0 đầu. Parse lỗi trong bản nạp khác → DQ, không sửa raw. | Schema nguồn. |
| Missing | `FirstDisbursementDate` thiếu 71.186; FDIC 41.322; NCUA 377.191; rate/FV 8; nhiều ngày outcome thiếu theo status. | Blank→NULL trong bản chuẩn hóa; phân biệt thiếu có điều kiện với lỗi; không loại dòng hoặc điền số trung bình. Unknown member chỉ khi thiết kế dimension cần và có nhãn riêng. | BR09/meaning của blank. |
| Exact duplicate | 687 dòng thuộc 296 nhóm raw exact duplicate, 391 bản sao dư; không có public LoanID. | Giữ toàn bộ; gắn group/issue flag và file identity + source record ordinal. Không dùng row hash làm LoanID. | BR01–BR02. |
| Text/category | `Program` có khoảng trắng ở toàn bộ dòng; 19 nhãn `ProcessingMethod` trong CSV. | Trim cosmetic trên cột phân tích, giữ chuỗi gốc; so cardinality trước/sau. Không tự gộp method, county, lender names hay khác biệt chữ hoa/thường có ý nghĩa. | BR15; method mapping `OPEN`. |
| Status | CSV có `P I F`; workbook ghi `PIF`. | Giữ `RawStatus` đúng nguồn; mapping project-approved `P I F→PIF` ở `CanonicalStatus` và audit mapping version/status khi triển khai. Không sửa raw. | BR-STATUS-01 `PROJECT_APPROVED`; NOT IMPLEMENTED. |
| Date/FY | FY2026 chỉ đến 30/06; 5 CHGOFF thiếu ngày, 22 `ChargeOffDate` sau snapshot, 2 `PaidInFullDate` trước approval. | Parse/flag, không tự đổi/xóa. Đối chiếu `ApprovalFY` với FY suy từ `ApprovalDate`. FiscalYear/Quarter nên ở `Dim_Date` hoặc semantic layer sau khi schema được duyệt, tránh hai định nghĩa khác nhau. | BR04, BR10 và candidate schema. |
| Numeric/zero | 11 term=0, 87 rate=0, 45.739 jobs=0. | Giữ 0 khác NULL; flag và công bố mẫu số. Kiểm amount âm, `SBAGuaranteedApproval>GrossApproval`, impossible dates; không coi giá trị hiếm mặc nhiên sai. | BR09, BR14. |
| NAICS | Raw `NaicsCode` 6 ký tự; source không ghi vintage. | Giữ raw code/description. Cấp Sector cho Q13/Q15 đã duyệt; chỉ gán `NaicsSectorCode/NaicsSectorName` bằng reference/version được xác minh, gồm dải gộp 31–33, 44–45, 48–49; unmapped ghi audit. | BR-NAICS-01: analytical level `PROJECT_APPROVED`; mapping `PENDING_VERIFICATION`. |
| TermBand | 11 term=0; 236.672 dòng đúng 120 tháng. | Bản standardized cơ sở chỉ parse/flag raw `TermInMonths`. Khi materialize dùng `ZERO`, `SHORT=1–60`, `MEDIUM=61–119`, `TERM_120=120`, `LONG=121–240`, `VERY_LONG=>240`; `MISSING`/`INVALID` riêng và ngoài mẫu số share; ghi rule version. | BR-TERM-01 `PROJECT_APPROVED`; NOT IMPLEMENTED. |
| Q15 eligibility | Ngưỡng 30/5 đã được duyệt cho sector×cohort. | Chỉ áp ở query-time; không loại dòng khỏi dataset. FY2025 có 7 sector qua gate/3 sau baseline trong phép thử candidate; FY2026 có 0 qua gate. | BR-CHGOFF-01 `PROJECT_APPROVED`; NOT IMPLEMENTED. |

Nếu không loại bản ghi, mục tiêu kiểm đối soát row count là **388.338**; đây chưa phải số dòng *sau cleaning* đã chạy. Số cột đầu ra chưa chốt vì mapping/derived fields còn phụ thuộc rule.

## Checklist triển khai

Tất cả task sau đều **NOT IMPLEMENTED**; profiling sẵn có là baseline kiểm tra, không phải preprocessing đã hoàn thành.

| ID | Task | Input | Xử lý | Output dự kiến | Dependency | Status |
|---|---|---|---|---|---|---|
| PRE-01 | Raw manifest | CSV/workbook | Checksum, schema, count, ordinal | Manifest | — | NOT IMPLEMENTED |
| PRE-02 | Parse types | Raw fields | Date/decimal; code giữ text | Typed fields + errors | PRE-01 | NOT IMPLEMENTED |
| PRE-03 | Blank/text | Raw/typed | NULL, trim có kiểm soát | Standardized fields | PRE-02 | NOT IMPLEMENTED |
| PRE-04 | Date/FY validation | Typed dates | Order/cutoff/FY checks | DQ issues | PRE-02, BR04/BR10 | NOT IMPLEMENTED |
| PRE-05 | Numeric validation | Typed numeric | Null/zero/âm/quan hệ amount | DQ issues | PRE-02 | NOT IMPLEMENTED |
| PRE-06 | Duplicate audit | Raw row + ordinal | Group và flag, giữ dòng | DQ issues | PRE-01 | NOT IMPLEMENTED |
| PRE-07 | Status mapping | Raw status | Raw→canonical | Mapped status + audit | BR-STATUS-01 `PROJECT_APPROVED`; mapping version | PLANNED / NOT IMPLEMENTED |
| PRE-08 | NAICS mapping | Raw code | Reference sector, unmapped audit | Sector attributes | Reference/version/crosswalk `PENDING_VERIFICATION` | CONDITIONAL / NOT IMPLEMENTED |
| PRE-09 | TermBand nếu materialize | Term months | Bands gồm `TERM_120`, `MISSING`/`INVALID` | Band/rule version | BR-TERM-01 `PROJECT_APPROVED` | PLANNED / NOT IMPLEMENTED |
| PRE-10 | Reconcile/export | Các bước trên | Count, sums, distributions, lineage | Standardized dataset + report | PRE-01–06; PRE-07–09 chỉ khi rule tương ứng approved | NOT IMPLEMENTED |

## Viết trong Chương 1

Trình bày nguồn và quy mô → bảng DQ hiện có → quy tắc chuẩn hóa và status → pipeline → bảng before/after **chỉ khi thực thi**. Một hình pipeline và một đoạn code minh họa ngắn là đủ; bảng rule, số bản ghi ảnh hưởng, lý do và kết quả đối soát là bằng chứng chính. Không gọi kế hoạch này là kết quả cleaning.
