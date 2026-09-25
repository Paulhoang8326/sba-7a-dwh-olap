# Tổng quan dữ liệu SBA 7(a)

Nguồn: `data\raw\foia\FOIA_7a_FY2020_Present_asof_260630.csv`; SHA-256 `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`. Workbook: `data\raw\foia\7a_504_foia_data_dictionary.xlsx`, sheet `7(a) Data Dictionary`. Chỉ đọc file gốc, không biến đổi dữ liệu.

- **1 CSV dữ liệu** (181,130,871 byte; 172.74 MiB); 1 workbook mô tả (24,529 byte). Tổng hai file: 181,155,400 byte.
- **388,338 bản ghi, 42 thuộc tính**. CSV là một file, nên kiểm tra khác biệt schema/kiểu hoặc trùng giữa nhiều file không áp dụng.
- Bộ nhớ DataFrame chuỗi (deep): **892.44 MiB**. Cần thêm bộ nhớ cho thống kê, nhóm trùng và cột số/ngày; số này không phải RAM đỉnh.
- Trên đĩa CSV lưu mọi giá trị dưới dạng text; kiểu ngữ nghĩa và các thống kê parse trình bày trong báo cáo kèm theo.
- FY2026 chỉ tới 30/06/2026; không xem là cả FY.

## Tên thuộc tính

`AsOfDate`, `Program`, `LocationID`, `BorrName`, `BorrStreet`, `BorrCity`, `BorrState`, `BorrZip`, `BankName`, `BankFDICNumber`, `BankNCUANumber`, `BankStreet`, `BankCity`, `BankState`, `BankZip`, `GrossApproval`, `SBAGuaranteedApproval`, `ApprovalDate`, `ApprovalFY`, `FirstDisbursementDate`, `ProcessingMethod`, `InitialInterestRate`, `FixedorVariableInterestInd`, `TermInMonths`, `NaicsCode`, `NaicsDescription`, `FranchiseCode`, `FranchiseName`, `ProjectCounty`, `ProjectState`, `SBADistrictOffice`, `CongressionalDistrict`, `BusinessType`, `BusinessAge`, `LoanStatus`, `PaidInFullDate`, `ChargeOffDate`, `GrossChargeOffAmount`, `RevolverStatus`, `JobsSupported`, `CollateralInd`, `SoldSecMrktInd`

## Số dòng theo ApprovalFY

| ApprovalFY | Số dòng |
|---|---|
| 2020 | 42,298 |
| 2021 | 51,856 |
| 2022 | 47,678 |
| 2023 | 57,362 |
| 2024 | 70,242 |
| 2025 | 78,078 |
| 2026 | 40,824 |

## Khoảng ngày

| Attribute | Min | Max | Thiếu | Không parse |
|---|---|---|---|---|
| AsOfDate | 2026-06-30 | 2026-06-30 | 0 | 0 |
| ApprovalDate | 2019-10-01 | 2026-06-30 | 0 | 0 |
| FirstDisbursementDate | 2019-10-01 | 2026-06-30 | 71186 | 0 |
| PaidInFullDate | 2019-12-31 | 2026-05-31 | 320136 | 0 |
| ChargeOffDate | 2020-07-06 | 2026-07-01 | 381450 | 0 |

## Giới hạn diễn giải

Một dòng là một bản ghi công bố; không có mã khoản vay công khai để chứng minh mỗi dòng là một khoản vay duy nhất. `AsOfDate` là ngày snapshot, các ngày sự kiện có thể thuộc ngoài khoảng năm phê duyệt. Kiểu chuỗi của mã và ngày là kiểu đọc từ CSV, không nên suy ra số thực chỉ vì toàn chữ số.