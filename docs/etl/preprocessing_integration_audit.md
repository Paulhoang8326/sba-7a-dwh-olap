# Audit tích hợp preprocessing trước thiết kế SSIS

> **Snapshot audit 2026-10-08.** Các gap input/datatype bên dưới đã được xử lý ngày 2026-10-10 bằng input Chương 2 riêng 52 cột và DBML (18,3)/BIGINT. Xem [trạng thái hiện hành](../00_current_status.md) và [kế hoạch SSIS](chapter2_ssis_plan.md); giữ nội dung audit cũ để truy vết.

> Kiểm tra 2026-10-08 trên branch `feat/chapter2-preprocessing-integration`. Đây là bằng chứng Phase 1 và phân tích gap, **không** là Source-to-Target Mapping cuối cùng, package SSIS, physical schema hoặc xác minh NAICS. Báo cáo [Chương 1](../../project_report/Chuong1/IS217.R11_24521176_24520479_BTA11.docx) là nguồn nội dung; [candidate schema](../dimensional_model/candidate_schema.md) và [business rules](../business_requirements/business_rule_register.md) vẫn giữ trạng thái/ranh giới hiện hành.

## Nguồn và mức xác minh

Chọn lọc từ `origin/main`: implementation `36baa4e` (2026-10-01), LFS outputs `6846424`, rồi merge `160ed5c`. Đã đưa `src/etl/preprocess.py`, notebook, test và năm báo cáo trong `reports/preprocessing/` vào branch hiện tại; không nhập `docs/etl/etl_implementation_plan.md` cũ vì nó mô tả `FactLoanSnapshot` và TSV dự kiến khoảng 27 cột. Raw và hai LFS objects được đọc để kiểm tra, **không** checkout hai output vào `data/staging/` hay đưa clean CSV chứa `Borr*` vào commit này.

| Bằng chứng | Kết quả kiểm tra |
|---|---|
| Raw CSV | SHA-256 `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`, trùng manifest và hằng số code. |
| TSV LFS object | 181.074.115 bytes; SHA-256 `837723fb7b6b8358ce4aaf4855ea396b197104660babbe6d6d9f6a6be3a78bc5`; header đúng 38 cột, 388.338 dòng, mọi dòng đủ 38 trường. |
| Clean CSV LFS object | 153.193.050 bytes; SHA-256 `508f7b0ee658f9c3d63e92118dc9f54565b826456fe30161691615d824528ce1`; header đúng 42 cột, 388.338 dòng, mọi dòng đủ 42 trường. Chứa `Borr*`; không in giá trị. |
| Đối soát nội dung LFS | Cả hai output cùng totals: `GrossApproval=202550139718.00`, `SBAGuaranteedApproval=152596337956.289`, `GrossChargeOffAmount=898807495.32`, `JobsSupported=4072432`; FY và raw LoanStatus khớp `reconciliation.csv`. |
| Tái lập TSV, không ghi clean CSV | `check_source` → `read_raw` → `standardize` → `write_tsv` trong `tmp/` Git-ignored; SHA-256 TSV mới trùng manifest/LFS; 18/18 dòng reconciliation TSV khớp; 687 duplicate rows/296 groups, 816 DQ issues. Temp output được dọn sau khi kiểm. Đây không phải lần chạy toàn bộ `run()`/`export_outputs()`. |
| Tests | 31 direct assertions cho text, TermBand, NAICS, status/business/FY pass. Full `pytest` không chạy: môi trường thiếu `pytest`, pip không kết nối package index; integration fixture còn ghi clean CSV chứa `Borr*` nên không tạo thêm bản sao khi chưa xác định phạm vi cho phép. Không xác nhận lại tuyên bố `57/57 pass` trong remote status. |

## Contract 38 cột và hướng đến Fact + 8 Dimensions

`Dùng` = có input/rule phù hợp ở mức logic; `Mapping` = cần biến đổi hoặc lookup khi thiết kế SSIS; `OPEN` = thiếu field hay quyết định thiết kế. Bảng này không tự quyết định business key, Unknown member, kiểu vật lý hoặc việc lưu audit vào Fact.

| # | Cột TSV | Đích/việc dùng theo Chương 1 | Phân loại |
|---:|---|---|---|
| 1 | `SourceFileID` | `Fact_Loan.SourceFileID`, cùng ordinal giữ lineage | Dùng |
| 2 | `SourceRecordOrdinal` | `Fact_Loan.SourceRecordOrdinal`; không thay `SourceRowNumber` vật lý | Dùng |
| 3 | `AsOfDate` | Metadata snapshot/source; bảng Fact 1.12 không liệt kê cột này | OPEN: vị trí lưu |
| 4 | `ApprovalDate` | `Dim_Date.FullDate` → `Fact_Loan.ApprovalDateKey` | Mapping |
| 5 | `ApprovalFY` | Kiểm FY nguồn và hỗ trợ đối soát `Dim_Date.FiscalYear` | Mapping |
| 6 | `FiscalYearDerived` | Kiểm FY từ ApprovalDate; không là measure/Fact field | Mapping |
| 7 | `ProjectState` | `Dim_ProjectGeography.ProjectState` | Dùng |
| 8 | `ProjectCounty` | `Dim_ProjectGeography.ProjectCounty`, ghép với state | Mapping |
| 9 | `NaicsCode` | `Dim_Industry.NaicsCode`; business key ứng viên gồm cả description | Mapping |
| 10 | `NaicsDescription` | `Dim_Industry.NaicsDescription` | Mapping |
| 11 | `NaicsSectorCode` | `Dim_Industry.NaicsSectorCode`, chỉ candidate | OPEN: verified reference/crosswalk |
| 12 | `SectorMappingStatus` | `Dim_Industry.SectorMappingStatus`; giữ `CANDIDATE_UNVERIFIED` | Dùng |
| 13 | `LocationID` | `Dim_Lender.LocationID`, dạng text; không là LoanID | Dùng |
| 14 | `BankName` | `Dim_Lender.BankName` | Dùng |
| 15 | `ProcessingMethod` | `Dim_LoanProfile.ProcessingMethod`; các profile fields khác vắng TSV | OPEN: nguồn bổ sung |
| 16 | `RawStatus` | `Dim_LoanStatus.RawStatus` | Dùng |
| 17 | `CanonicalStatus` | `Dim_LoanStatus.CanonicalStatus`; `P I F→PIF` | Dùng |
| 18 | `TermInMonths` | `Fact_Loan.TermInMonths`, đồng thời tạo band | Dùng |
| 19 | `TermBandCode` | `Dim_TermBand.TermBandCode` → `Fact_Loan.TermBandKey` | Mapping |
| 20 | `BusinessTypeRaw` | `Dim_Business.BusinessTypeRaw` | Dùng |
| 21 | `BusinessAgeRaw` | `Dim_Business.BusinessAgeRaw`, không là tuổi tính theo năm | Dùng |
| 22 | `BusinessTypeValueStatus` | `Dim_Business.BusinessTypeValueStatus` | Dùng |
| 23 | `BusinessAgeValueStatus` | `Dim_Business.BusinessAgeValueStatus` | Dùng |
| 24 | `GrossApproval` | `Fact_Loan.GrossApproval` | Dùng; scale vật lý OPEN |
| 25 | `SBAGuaranteedApproval` | `Fact_Loan.SBAGuaranteedApproval` | Dùng; cần bảo toàn 3dp |
| 26 | `GrossChargeOffAmount` | `Fact_Loan.GrossChargeOffAmount` | Dùng; scale vật lý OPEN |
| 27 | `JobsSupported` | `Fact_Loan.JobsSupported` | Dùng |
| 28 | `IsExactDuplicate` | Audit/DQ theo published record; không phải tiêu chí xóa dòng | OPEN: nơi lưu audit |
| 29 | `DQFlagCount` | Audit/DQ; mã issue chi tiết nằm ở `dq_issues.csv` | OPEN: nơi lưu audit |
| 30 | `ProjectStateLookup` | Helper NULL token cho `Dim_ProjectGeography` | Mapping |
| 31 | `ProjectCountyLookup` | Helper NULL token cho `Dim_ProjectGeography`; cần ghép state | Mapping |
| 32 | `NaicsCodeLookup` | Helper cho `Dim_Industry` | Mapping |
| 33 | `NaicsDescriptionLookup` | Helper cho `Dim_Industry` | Mapping |
| 34 | `LocationIDLookup` | Helper cho `Dim_Lender` | Mapping |
| 35 | `ProcessingMethodLookup` | Helper cho `Dim_LoanProfile` | Mapping |
| 36 | `RawStatusLookup` | Helper cho `Dim_LoanStatus` | Mapping |
| 37 | `BusinessTypeLookup` | Helper cho `Dim_Business` | Mapping |
| 38 | `BusinessAgeLookup` | Helper cho `Dim_Business`; missing khác `Unanswered` | Mapping |

`RecordCount=1`, các surrogate PK/FK và `ETLBatchID` không nằm trong TSV; chúng thuộc bước mapping/load về sau. Q1–Q15 và Measure Contract là logic phân tích, không được áp dụng làm bộ lọc loại dòng trong Phase 1.

## OPEN trước khi thiết kế/nạp SSIS

1. `Fact_Loan` cần `FirstDisbursementDate`, `PaidInFullDate`, `ChargeOffDate` và `SourceRowNumber`; TSV không có. Clean CSV có ba ngày sự kiện nhưng không có physical `SourceRowNumber`. Cần quyết định cách lấy thêm từ raw theo `(SourceFileID, SourceRecordOrdinal)` và cách tính dòng vật lý khi có 16 record multiline; không suy ordinal+1 là số dòng vật lý.
2. `Dim_ProjectGeography` còn `CongressionalDistrict`, `SBADistrictOffice`; `Dim_Lender` còn FDIC/NCUA và địa chỉ; `Dim_LoanProfile` còn fixed/variable, revolver, collateral. Các nguồn này bị DROP khỏi TSV nhưng còn trong raw/clean CSV. Cần Source-to-Target Mapping được duyệt, không tự thêm vào 38 cột hay bỏ khỏi mô hình.
3. `Dim_Industry.NaicsSectorName/NaicsVersion`, `Dim_LoanStatus.StatusMappingStatus`, `Dim_TermBand` labels/ranges/status và các `*ValueStatus` khác cần mapping/nguồn hoặc quyết định trước khi load. Prefix NAICS hiện chỉ `CANDIDATE_UNVERIFIED`.
4. Report §1.2.2.4 nêu `DECIMAL(18,3)` để giữ hai giá trị 3dp; DBML còn `decimal(19,2)`. Chốt physical precision/scale trước khi SSIS chuyển kiểu; không sửa schema trong task này.
5. Chốt composite business keys, case/collation, NULL token/Unknown member, xử lý unmatched lookup, uniqueness/idempotency và vị trí DQ audit. Không nhầm 38 cột staging với 22 cột của bảng Fact trong report.
6. Clean CSV có `Borr*` và đã được commit LFS ở remote; kiểm phạm vi được phép lưu/chia sẻ trước khi đưa file đó vào branch khác, chạy full test/pipeline hay xuất bản thêm. Bước tích hợp này không tạo bản sao clean CSV.

**Readiness:** đủ bằng chứng để bắt đầu *thiết kế* SSIS/Source-to-Target Mapping; chưa đủ contract để dựng package/nạp `Fact_Loan` hoặc công bố NAICS verified. Không có `.dtproj`/`.dtsx` mới trong task này.
