# Preprocessing — kết quả theo report và bằng chứng tích hợp

> Cập nhật 2026-10-08 theo [Chương 1 §1.2.2](../../project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx) và [integration audit](../etl/preprocessing_integration_audit.md). **CODE_INTEGRATED / TSV_REPRODUCED**: notebook, module, test, manifest/reconciliation đã vào branch; LFS outputs kiểm trong Git cache, chưa checkout vào staging. Full `run()`/pytest chưa tái kiểm; không coi `src/main.py` hoặc CSV snowflake cũ là implementation thay thế.

## Input và output

Input bất biến: `data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv`, 388.338 dòng × 42 cột, SHA-256 `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`; dictionary cùng thư mục, sheet `7(a) Data Dictionary`. Raw không sửa.

Report §1.2.2.5 nêu giữ trực tiếp **18 thuộc tính nguồn**, bổ sung standardized/derived/lookup/DQ để có **388.338 dòng × 38 cột**. Không diễn giải thành chỉ 18 nguồn được dùng toàn project: bảng 1.3 tham chiếu **32 thuộc tính nguồn** cho Fact/Dimensions. Hình 1.23 xác nhận 18 cột KEEP: `AsOfDate`, `LocationID`, `BankName`, `GrossApproval`, `SBAGuaranteedApproval`, `ApprovalDate`, `ApprovalFY`, `ProcessingMethod`, `TermInMonths`, `NaicsCode`, `NaicsDescription`, `ProjectCounty`, `ProjectState`, `BusinessType`, `BusinessAge`, `LoanStatus`, `GrossChargeOffAmount`, `JobsSupported`. `column_selection.csv` và header LFS xác nhận 18 KEEP/38 output; danh sách từng cột và gap so với target có trong [integration audit](../etl/preprocessing_integration_audit.md). Header không tự giải quyết các lookup/field bị loại khỏi TSV.

## Các bước Python đã được mô tả trong report

| Bước | Quy tắc / kết quả theo report | Bằng chứng trong checkout |
|---|---|---|
| Đọc nguồn | pandas/hashlib, checksum, 42 cột; đọc text giữ số 0 đầu; che Borr* khi hiển thị | Module/notebook có; raw SHA-256 khớp manifest; che Borr* chỉ là hiển thị notebook, clean CSV vẫn chứa cột này |
| Lineage | SourceRecordOrdinal tách SourceRowNumber vật lý | Code tạo ordinal 1..N; TSV không có SourceRowNumber vật lý, vẫn OPEN cho Fact |
| Missing/text | Trim, blank→NULL; newline trong ô→space; không impute | Code và 31 direct rule assertions có kiểm; header/count/hash TSV tái lập |
| Duplicate | 687 records thuộc 296 nhóm exact raw duplicate; flag và giữ mọi dòng | Khớp profiling; không drop_duplicates bản ghi nguồn |
| Date/FY/numeric DQ | Parse YYYY-MM-DD; đối chiếu FY, date order, zero/âm; flag, không xóa/sửa suy diễn | Code và `reports/preprocessing/dq_issues.csv` có trong branch; tái lập 816 issues |
| Datatype | Money DECIMAL(18,3), JobsSupported/TermInMonths integer; giữ 2 records money 3dp | Precision đã kiểm trên raw; DBML/DDL còn khác |
| Status | Giữ nguồn; P I F→PIF canonical | Report §1.2.2.4; warehouse chưa có Dim_LoanStatus |
| TermBand | ZERO, SHORT, MEDIUM, TERM_120, LONG, VERY_LONG, MISSING, INVALID | Report mô tả đã tạo nhãn; warehouse dimension chưa có |
| NAICS | Sector candidate kèm mapping status CANDIDATE_UNVERIFIED | Không nâng thành verified reference/version/crosswalk |
| Business | Raw type/age, Unanswered và missing riêng; không tuổi số | Report mô tả giữ nhãn |
| Export/reconcile | sba7a_standardized.tsv cho SSIS; _clean.csv đối soát; count, 4 totals, FY/status; notebook/script TSV SHA-256 match | Hai LFS objects kiểm hash/header/shape/totals; TSV tái lập cùng hash và 18/18 đối soát pass. Không chạy lại đường ghi clean CSV |

## Python và SSIS

Python preprocessing đã được tích hợp và kiểm TSV; SSIS có thể dùng contract 38 cột làm **đầu vào thiết kế**, nhưng phải chốt precision, null delimiter, field bổ sung và lookup đủ cho 8 dimensions trước khi dựng package. Chưa tạo package hoặc chạy ETL trong task tích hợp này.

ETL còn lại: source manifest và snapshot metadata; staging contract; dimension business keys/Unknown members/surrogate keys; FK lookup; nạp Fact_Loan giữ lineage; ETLBatchID/audit; đối soát raw→standardized→warehouse (count, totals, FY/status, FK/orphans, idempotency). Đây là việc task sau, không coi đã hoàn tất do report có screenshots.

Các gate Q12/Q15 là query population, không là điều kiện xóa records trong preprocessing. NAICS reference/version, physical precision, field/lookup và quyền xử lý clean CSV vẫn là [Open Issues](../00_current_status.md#open-issues-report-va-implementation).
