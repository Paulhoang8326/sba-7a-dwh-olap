# Preprocessing — kết quả theo report và tình trạng checkout

> Đồng bộ 2026-10-02 theo [Chương 1 §1.2.2](../../project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx). **REPORT_DOCUMENTED_COMPLETED / CHECKOUT_UNVERIFIED** thay trạng thái cũ PLANNED / NOT IMPLEMENTED. Report mô tả đã chạy Python, nhưng `01_preprocessing.ipynb`, module `preprocess`, `sba7a_standardized.tsv`, `_clean.csv` và manifest/reconciliation tương ứng **chưa tìm thấy trong checkout**, kể cả file Git-ignored. Không coi `src/main.py` hoặc CSV snowflake cũ là implementation thay thế.

## Input và output

Input bất biến: `data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv`, 388.338 dòng × 42 cột, SHA-256 `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`; dictionary cùng thư mục, sheet `7(a) Data Dictionary`. Raw không sửa.

Report §1.2.2.5 nêu giữ trực tiếp **18 thuộc tính nguồn**, bổ sung standardized/derived/lookup/DQ để có **388.338 dòng × 38 cột**. Không diễn giải thành chỉ 18 nguồn được dùng toàn project: bảng 1.3 tham chiếu **32 thuộc tính nguồn** cho Fact/Dimensions. Hình 1.23 xác nhận 18 cột KEEP: `AsOfDate`, `LocationID`, `BankName`, `GrossApproval`, `SBAGuaranteedApproval`, `ApprovalDate`, `ApprovalFY`, `ProcessingMethod`, `TermInMonths`, `NaicsCode`, `NaicsDescription`, `ProjectCounty`, `ProjectState`, `BusinessType`, `BusinessAge`, `LoanStatus`, `GrossChargeOffAmount`, `JobsSupported`. Danh sách này được đọc từ hình report, không thay contract máy đọc. **Danh sách đủ 38 output columns chưa có header/contract trong repo**; các TargetColumns bị rút gọn trong screenshot không được tự bổ sung. Cần bổ sung output header, lookup artifacts và manifest trước mapping SSIS.

## Các bước Python đã được mô tả trong report

| Bước | Quy tắc / kết quả theo report | Bằng chứng trong checkout |
|---|---|---|
| Đọc nguồn | pandas/hashlib, checksum, 42 cột; đọc text giữ số 0 đầu; che Borr* khi hiển thị | Raw + profile có; notebook mới chưa có |
| Lineage | SourceRecordOrdinal tách SourceRowNumber vật lý | Report §1.2.2.1 và bảng Fact; prototype chỉ index+2 |
| Missing/text | Trim, blank→NULL; newline trong ô→space; không impute | Report §1.2.2.2; chưa kiểm đầu ra |
| Duplicate | 687 records thuộc 296 nhóm exact raw duplicate; flag và giữ mọi dòng | Khớp profiling; không drop_duplicates bản ghi nguồn |
| Date/FY/numeric DQ | Parse YYYY-MM-DD; đối chiếu FY, date order, zero/âm; flag, không xóa/sửa suy diễn | Report có hình kết quả; DQ flags mới chưa có file |
| Datatype | Money DECIMAL(18,3), JobsSupported/TermInMonths integer; giữ 2 records money 3dp | Precision đã kiểm trên raw; DBML/DDL còn khác |
| Status | Giữ nguồn; P I F→PIF canonical | Report §1.2.2.4; warehouse chưa có Dim_LoanStatus |
| TermBand | ZERO, SHORT, MEDIUM, TERM_120, LONG, VERY_LONG, MISSING, INVALID | Report mô tả đã tạo nhãn; warehouse dimension chưa có |
| NAICS | Sector candidate kèm mapping status CANDIDATE_UNVERIFIED | Không nâng thành verified reference/version/crosswalk |
| Business | Raw type/age, Unanswered và missing riêng; không tuổi số | Report mô tả giữ nhãn |
| Export/reconcile | sba7a_standardized.tsv cho SSIS; _clean.csv đối soát; count, 4 totals, FY/status; notebook/script TSV SHA-256 match | Report mô tả PASS; output, hash manifest và script tương ứng chưa có để tái kiểm |

## Python và SSIS

Python preprocessing được báo cáo mô tả là đã làm; SSIS sẽ tiếp nhận standardized input **sau khi** xác minh file/header/precision/encoding/null delimiter và lookup đủ cho 8 dimensions. Chưa tạo package hoặc chạy ETL trong task đồng bộ tài liệu.

ETL còn lại: source manifest và snapshot metadata; staging contract; dimension business keys/Unknown members/surrogate keys; FK lookup; nạp Fact_Loan giữ lineage; ETLBatchID/audit; đối soát raw→standardized→warehouse (count, totals, FY/status, FK/orphans, idempotency). Đây là việc task sau, không coi đã hoàn tất do report có screenshots.

Các gate Q12/Q15 là query population, không là điều kiện xóa records trong preprocessing. NAICS reference/version, physical precision, bộ 38 columns và lookup artifacts là [Open Issues](../00_current_status.md#open-issues-report-va-implementation).
