# Data Profiling – SBA 7(a)

Chạy toàn bộ 388,338 dòng; dữ liệu gốc không bị sửa. CSV chi tiết trong `reports/data_profiling/`. `Null` là ô rỗng hoặc chỉ khoảng trắng; số khác 0 và ngày được parse để thống kê nhưng không ghi ngược vào nguồn.

## Hồ sơ cột

| Attribute | Data Type | Non-null | Null | Null % | Unique | Unique % |
|---|---|---|---|---|---|---|
| AsOfDate | date (CSV: text) | 388338 | 0 | 0.0 | 1 | 0.0003 |
| Program | text | 388338 | 0 | 0.0 | 1 | 0.0003 |
| LocationID | code (CSV: text) | 388338 | 0 | 0.0 | 2338 | 0.6021 |
| BorrName | text | 388338 | 0 | 0.0 | 323752 | 83.3686 |
| BorrStreet | text | 388338 | 0 | 0.0 | 333651 | 85.9177 |
| BorrCity | text | 388338 | 0 | 0.0 | 21599 | 5.5619 |
| BorrState | text | 388338 | 0 | 0.0 | 54 | 0.0139 |
| BorrZip | code (CSV: text) | 388338 | 0 | 0.0 | 21250 | 5.472 |
| BankName | text | 388338 | 0 | 0.0 | 2183 | 0.5621 |
| BankFDICNumber | code (CSV: text) | 347016 | 41322 | 10.6407 | 1873 | 0.5397 |
| BankNCUANumber | code (CSV: text) | 11147 | 377191 | 97.1296 | 322 | 2.8887 |
| BankStreet | text | 388338 | 0 | 0.0 | 2282 | 0.5876 |
| BankCity | text | 388338 | 0 | 0.0 | 1666 | 0.429 |
| BankState | text | 388338 | 0 | 0.0 | 54 | 0.0139 |
| BankZip | code (CSV: text) | 388338 | 0 | 0.0 | 1998 | 0.5145 |
| GrossApproval | numeric (CSV: text) | 388338 | 0 | 0.0 | 21175 | 5.4527 |
| SBAGuaranteedApproval | numeric (CSV: text) | 388338 | 0 | 0.0 | 29363 | 7.5612 |
| ApprovalDate | date (CSV: text) | 388338 | 0 | 0.0 | 2285 | 0.5884 |
| ApprovalFY | code (CSV: text) | 388338 | 0 | 0.0 | 7 | 0.0018 |
| FirstDisbursementDate | date (CSV: text) | 317152 | 71186 | 18.3309 | 2345 | 0.7394 |
| ProcessingMethod | text | 388338 | 0 | 0.0 | 19 | 0.0049 |
| InitialInterestRate | numeric (CSV: text) | 388330 | 8 | 0.0021 | 1681 | 0.4329 |
| FixedorVariableInterestInd | text | 388330 | 8 | 0.0021 | 2 | 0.0005 |
| TermInMonths | numeric (CSV: text) | 388338 | 0 | 0.0 | 347 | 0.0894 |
| NaicsCode | code (CSV: text) | 388338 | 0 | 0.0 | 1157 | 0.2979 |
| NaicsDescription | text | 388338 | 0 | 0.0 | 1783 | 0.4591 |
| FranchiseCode | code (CSV: text) | 46582 | 341756 | 88.0048 | 3690 | 7.9215 |
| FranchiseName | text | 46418 | 341920 | 88.047 | 3543 | 7.6328 |
| ProjectCounty | text | 388338 | 0 | 0.0 | 1855 | 0.4777 |
| ProjectState | text | 388338 | 0 | 0.0 | 54 | 0.0139 |
| SBADistrictOffice | text | 388338 | 0 | 0.0 | 67 | 0.0173 |
| CongressionalDistrict | code (CSV: text) | 388314 | 24 | 0.0062 | 54 | 0.0139 |
| BusinessType | text | 388304 | 34 | 0.0088 | 3 | 0.0008 |
| BusinessAge | text | 388152 | 186 | 0.0479 | 5 | 0.0013 |
| LoanStatus | text | 388338 | 0 | 0.0 | 5 | 0.0013 |
| PaidInFullDate | date (CSV: text) | 68202 | 320136 | 82.4375 | 78 | 0.1144 |
| ChargeOffDate | date (CSV: text) | 6888 | 381450 | 98.2263 | 1002 | 14.547 |
| GrossChargeOffAmount | numeric (CSV: text) | 388338 | 0 | 0.0 | 6472 | 1.6666 |
| RevolverStatus | text | 388338 | 0 | 0.0 | 2 | 0.0005 |
| JobsSupported | numeric (CSV: text) | 388338 | 0 | 0.0 | 281 | 0.0724 |
| CollateralInd | text | 388338 | 0 | 0.0 | 2 | 0.0005 |
| SoldSecMrktInd | text | 116764 | 271574 | 69.9324 | 1 | 0.0009 |

Các giá trị ví dụ nằm trong `column_profile.csv`; phân phối top 10 của mọi cột phân loại/mã nằm trong `categorical_distribution.csv`.

## Cột số

| Attribute | Min | Max | Mean | Median | Std | Q1 | Q3 | Zero | Negative | Parse fail |
|---|---|---|---|---|---|---|---|---|---|---|
| GrossApproval | 1000.0 | 5000000.0 | 521582.07468236436 | 195000.0 | 864066.3018846636 | 52000.0 | 500000.0 | 0 | 0 | 0 |
| SBAGuaranteedApproval | 500.0 | 4500000.0 | 392947.2211225505 | 127500.0 | 667510.2682456305 | 37500.0 | 384750.0 | 0 | 0 | 0 |
| InitialInterestRate | 0.0 | 16.5 | 8.815177274251282 | 9.25 | 2.7028744670583285 | 6.25 | 10.75 | 87 | 0 | 0 |
| TermInMonths | 0.0 | 420.0 | 138.23786495269584 | 120.0 | 69.67245542308513 | 120.0 | 120.0 | 11 | 0 | 0 |
| GrossChargeOffAmount | 0.0 | 4632999.92 | 2314.497925312485 | 0.0 | 42221.61950753864 | 0.0 | 0.0 | 381450 | 0 | 0 |
| JobsSupported | 0.0 | 550.0 | 10.486823334311863 | 5.0 | 18.739413386764355 | 2.0 | 12.0 | 45739 | 0 | 0 |

## Ngày

| Attribute | Min | Max | Missing | Parse fail | Formats |
|---|---|---|---|---|---|
| AsOfDate | 2026-06-30 | 2026-06-30 | 0 | 0 | {"YYYY-MM-DD": 388338} |
| ApprovalDate | 2019-10-01 | 2026-06-30 | 0 | 0 | {"YYYY-MM-DD": 388338} |
| FirstDisbursementDate | 2019-10-01 | 2026-06-30 | 71186 | 0 | {"YYYY-MM-DD": 317152} |
| PaidInFullDate | 2019-12-31 | 2026-05-31 | 320136 | 0 | {"YYYY-MM-DD": 68202} |
| ChargeOffDate | 2020-07-06 | 2026-07-01 | 381450 | 0 | {"YYYY-MM-DD": 6888} |

## Thiếu dữ liệu

| Attribute | Missing | % |
|---|---|---|
| ChargeOffDate | 381450 | 98.2263 |
| BankNCUANumber | 377191 | 97.1296 |
| FranchiseName | 341920 | 88.047 |
| FranchiseCode | 341756 | 88.0048 |
| PaidInFullDate | 320136 | 82.4375 |
| SoldSecMrktInd | 271574 | 69.9324 |
| FirstDisbursementDate | 71186 | 18.3309 |
| BankFDICNumber | 41322 | 10.6407 |
| BusinessAge | 186 | 0.0479 |
| BusinessType | 34 | 0.0088 |
| CongressionalDistrict | 24 | 0.0062 |
| InitialInterestRate | 8 | 0.0021 |
| FixedorVariableInterestInd | 8 | 0.0021 |

`missing_values.csv` chứa số thiếu chia theo FY và LoanStatus (mẫu số là số dòng của từng nhóm). Nhóm có tỷ lệ thiếu cao nhất trong từng lát cắt:

| Attribute | Theo | Nhóm | Thiếu | Dòng nhóm | % thiếu nhóm |
|---|---|---|---|---|---|
| FirstDisbursementDate | ApprovalFY | 2026 | 17581 | 40824 | 43.0654 |
| FirstDisbursementDate | LoanStatus | CANCLD | 50104 | 50104 | 100.0 |
| BankFDICNumber | ApprovalFY | 2025 | 9562 | 78078 | 12.2467 |
| BankFDICNumber | LoanStatus | EXEMPT | 27616 | 242061 | 11.4087 |
| BankNCUANumber | ApprovalFY | 2025 | 76078 | 78078 | 97.4385 |
| BankNCUANumber | LoanStatus | CHGOFF | 6783 | 6893 | 98.4042 |
| FranchiseName | ApprovalFY | 2024 | 64336 | 70242 | 91.5919 |
| FranchiseName | LoanStatus | CANCLD | 45615 | 50104 | 91.0406 |
| SoldSecMrktInd | ApprovalFY | 2026 | 32245 | 40824 | 78.9854 |
| SoldSecMrktInd | LoanStatus | CANCLD | 50098 | 50104 | 99.988 |
| ChargeOffDate | ApprovalFY | 2026 | 40824 | 40824 | 100.0 |
| ChargeOffDate | LoanStatus | EXEMPT | 242061 | 242061 | 100.0 |
| PaidInFullDate | ApprovalFY | 2026 | 40741 | 40824 | 99.7967 |
| PaidInFullDate | LoanStatus | CANCLD | 50104 | 50104 | 100.0 |

Thiếu `ChargeOffDate` ngoài CHGOFF và `PaidInFullDate` ngoài `P I F` thường phù hợp điều kiện áp dụng của trường. `FirstDisbursementDate` thiếu toàn bộ ở CANCLD và COMMIT, tương ứng trạng thái hủy/chưa giải ngân; còn 3 dòng `P I F` thiếu ngày giải ngân cần xác minh. `BankFDICNumber`/`BankNCUANumber` có thể không áp dụng theo loại lender; `FranchiseCode/Name`, `SoldSecMrktInd` còn cần kiểm tra nghiệp vụ. Không coi tất cả ô trống là lỗi.

## Trùng lặp

| Metric | Count | % trên toàn bộ dòng |
|---|---|---|
| exact duplicate rows (including first occurrence) | 687 | 0.1769 |
| exact surplus copies | 391 | 0.1007 |
| exact duplicate groups | 296 |  |
| max exact group size | 8 |  |
| weak composite matching rows | 3316 | 0.8539 |

Composite yếu dùng `BorrName, BankName, ApprovalDate, GrossApproval, ProjectState` chỉ để sàng lọc; 3,316 dòng cùng composite trong nhóm từ 2 dòng; nhóm lớn nhất có 11 dòng. Không đủ cơ sở gọi chúng là cùng khoản vay. Exact duplicate cũng chưa chứng minh lỗi do không có LoanID công khai. Không xóa dòng nào.

## Trạng thái

| LoanStatus | Số dòng | % |
|---|---|---|
| EXEMPT | 242061 | 62.33 |
| P I F | 68201 | 17.56 |
| CANCLD | 50104 | 12.9 |
| COMMIT | 21079 | 5.43 |
| CHGOFF | 6893 | 1.78 |

CSV dùng nhãn `P I F`; workbook mô tả mã `PIF`. Script chỉ dùng mapping tạm trong phép kiểm tra, không sửa giá trị nguồn.

## Kiểm tra nhất quán

| Attribute | Dấu hiệu | Số dòng | % |
|---|---|---|---|
| InitialInterestRate | Giá trị thiếu, chưa rõ lý do | 8 | 0.0021 |
| FixedorVariableInterestInd | Giá trị thiếu, chưa rõ lý do | 8 | 0.0021 |
| BusinessType | Giá trị thiếu, chưa rõ lý do | 34 | 0.0088 |
| BusinessAge | Giá trị thiếu, chưa rõ lý do | 186 | 0.0479 |
| CongressionalDistrict | Giá trị thiếu, chưa rõ lý do | 24 | 0.0062 |
| FirstDisbursementDate | P I F nhưng thiếu ngày giải ngân đầu tiên | 3 | 0.0008 |
| TermInMonths | Kỳ hạn bằng 0 | 11 | 0.0028 |
| InitialInterestRate | Lãi suất ban đầu bằng 0 | 87 | 0.0224 |
| ChargeOffDate | CHGOFF nhưng thiếu ngày | 5 | 0.0013 |
| PaidInFullDate | Có ngày PIF nhưng trạng thái không phải P I F | 1 | 0.0003 |
| LoanStatus | Nhãn P I F khác mã PIF trong workbook | 68201 | 17.5623 |
| PaidInFullDate | Ngày trước ApprovalDate | 2 | 0.0005 |
| ChargeOffDate | Ngày sau AsOfDate | 22 | 0.0057 |
| Program | Có khoảng trắng đầu/cuối | 388338 | 100.0 |
| All attributes | Bản ghi trùng hoàn toàn (tính cả bản gốc) | 687 | 0.1769 |

Các kiểm tra là dấu hiệu cần điều tra, trừ khi có quy tắc nguồn xác minh. Mã bang so với danh sách USPS gồm 50 bang, DC và lãnh thổ; NAICS so dạng 6 chữ số, không chứng minh mã đang hiệu lực trong một phiên bản NAICS cụ thể. Kiểm tra ngày dùng thứ tự sự kiện và ngày snapshot, không tự sửa bản ghi.