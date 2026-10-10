# Chương 2 — Kế hoạch triển khai SBA 7(a) bằng SSIS

Cập nhật 2026-10-10. Phạm vi đồ án IS217: một snapshot, full load, `Fact_Loan` + tám dimensions. Đây là kế hoạch thực hiện; chưa có database target hoặc package SSIS chạy thật.

## Đầu vào đã chuẩn bị

- Chương 1 giữ nguyên pipeline/notebook và TSV **38 cột**. Không đổi nội dung §1.2.2.
- Chương 2 dùng một TSV **52 cột**: 38 cột đầu cùng thứ tự/cách biểu diễn, cộng đúng 14 source fields. Không có `Borr*`.
- Script [prepare_ssis_input.py](../../src/etl/prepare_ssis_input.py) gọi `preprocess.standardize()` trong bộ nhớ, lấy 14 trường từ cleaned frame cùng parser index. Không ghi clean CSV, không gọi exporter Chương 1.
- DBML thống nhất ba money measures `DECIMAL(18,3)` và `TermBandKey BIGINT` ở PK/FK theo report. SQL prototype cũ không phải DDL target.
- Hình schema cũ trong Word/SVG còn annotations `(19,2)`/`INT`; bảng mô tả report và DBML đã thống nhất là căn cứ viết DDL. Ghi datatype đã chốt trong Chương 2; không thay Word/logic Chương 1 ở bước chuẩn bị này.

Chạy từ repository root, dùng Python đã có pandas:

```powershell
python -m src.etl.prepare_ssis_input
python -m unittest discover -s tests -p test_prepare_ssis_input.py -v
```

Output local: `data/staging/chapter2/sba7a_ssis_input.tsv` và `sba7a_ssis_input.manifest.json`. Cả hai được `.gitignore` hiện có loại khỏi commit. Script từ chối ghi đè; để tái tạo một lần khác dùng `--output tmp/chapter2_repeat/input.tsv` với đường dẫn chưa tồn tại.

| Cột thêm sau 38 cột gốc | Đích |
|---|---|
| FirstDisbursementDate, PaidInFullDate, ChargeOffDate | Fact_Loan; DATE nullable |
| CongressionalDistrict, SBADistrictOffice | Dim_ProjectGeography; giữ text/NULL |
| BankFDICNumber, BankNCUANumber, BankStreet, BankCity, BankState, BankZip | Dim_Lender; giữ text/leading zeros/NULL |
| FixedorVariableInterestInd, RevolverStatus, CollateralInd | Dim_LoanProfile; rename trường đầu thành FixedOrVariableInterestInd khi load |

Manifest local ghi source/output SHA-256, 52-column header, số records, totals, kiểm tra từng ô và checksum projection 38 cột. Source checksum phải khớp manifest Chương 1 trước khi xử lý. Mỗi record 52 cột được đọc lại đối chiếu với record trong bộ nhớ; projection 38 cột phải có SHA-256 `837723fb7b6b8358ce4aaf4855ea396b197104660babbe6d6d9f6a6be3a78bc5`.

## Các bước thực hiện

| Bước | Thực hiện | Minh chứng cần chụp/lưu khi chạy thật |
|---:|---|---|
| 1 | Xác nhận SQL Server instance, SSMS, Visual Studio và extension Integration Services Projects tương thích; chọn TargetServerVersion phù hợp máy. | Phiên bản công cụ, kết nối thành công |
| 2 | Tạo database riêng cho đồ án, ví dụ SBA7A_DWH; tạo 9 bảng từ [DBML hiện hành](../../diagram/candidate_schema.dbml). Chốt Unicode, nullable attrs và seed TermBand/status ngay khi viết DDL. | DDL và database diagram 1 Fact + 8 Dim |
| 3 | Tạo project trong `Source/SSIS/`; Flat File Connection tới TSV 52 cột, OLE DB Connection tới database đồ án. | Connection managers và Preview/header |
| 4 | Control Flow: chuẩn bị/reset dữ liệu demo → load Dimensions → load Fact → đối soát, nối Success constraints. Full reload chỉ tác động 9 bảng target trong database đồ án; xóa Fact trước Dimensions, không dùng script drop tất cả database objects. | Control Flow hoàn chỉnh |
| 5 | Tám Data Flow Tasks load Dimensions theo bảng dưới. Dùng Derived Column/Data Conversion, Sort bỏ trùng theo đúng key dimension, OLE DB Destination. | Một ảnh Data Flow và mapping cho từng Dim |
| 6 | Fact Data Flow đọc đủ 388.338 records, chuyển kiểu, tám Lookups lấy surrogate FK, thêm RecordCount=1 và ETLBatchID, OLE DB Destination vào Fact_Loan. | Lookups, mappings và row counts |
| 7 | Chạy toàn package; kiểm count, exact totals, duplicate lineage, FK/orphans, lookup errors. Thử full reload lần hai và đối soát lại. | Success execution, query results |
| 8 | Viết Chương 2 theo các bước đã chạy; lưu ảnh và mô tả ngắn vì sao chọn keys/conversions. | Report Chương 2, `.dtproj`/`.dtsx`, DDL/query checks |

Flat File: UTF-8 code page 65001, tab delimiter, CRLF row delimiter, header, **không text qualifier**, empty field là NULL. Khai báo widths/types rõ ràng, không dựa vào sample inference. Mã/ZIP giữ text; kiểm Unicode cho NaicsDescription/BankStreet; tiền dùng exact numeric `(18,3)` trong Data Conversion tới SQL, không qua float. Test Preview trước full load.

## Load tám Dimensions và Fact

| Dimension | Nguồn/khóa lookup đề xuất cho snapshot này | Lưu ý |
|---|---|---|
| Dim_Date | ApprovalDate → FullDate; DateKey đề xuất YYYYMMDD | Distinct ngày, derive year/month/quarter, FY bắt đầu tháng 10; kiểm ApprovalFY với FiscalYearDerived |
| Dim_ProjectGeography | ProjectState + ProjectCounty + CongressionalDistrict + SBADistrictOffice | Cần cả bốn thuộc tính; state/county chỉ là cấp aggregate Q9 |
| Dim_Industry | NaicsCode + NaicsDescription | Không code-only; giữ CANDIDATE_UNVERIFIED, tên/version NULL khi chưa có verified reference |
| Dim_Lender | LocationID | BankName và sáu trường bổ sung là attributes; LocationID hiện xác định duy nhất lender tuple |
| Dim_LoanProfile | ProcessingMethod + FixedorVariableInterestInd + RevolverStatus + CollateralInd | Không method-only; không impute fixed/variable missing |
| Dim_LoanStatus | RawStatus | CanonicalStatus có sẵn; StatusMappingStatus theo rule dự án, không gắn verified SBA mapping |
| Dim_TermBand | TermBandCode | Seed sáu analytical bands và hai DQ bands; PK/FK bigint; labels/order/status chốt khi viết DDL |
| Dim_Business | BusinessTypeRaw + BusinessAgeRaw | Missing khác Unanswered; không borrower/business identity |

Sort loại trùng chỉ dùng ở nhánh **dimension members**. Nhánh Fact không dedup, không lọc bỏ 687 published records thuộc duplicate groups. Lookup mỗi record phải trả đúng một member. Với composite có NULL, tạo helper token/NULL handling giống nhau ở input và reference; giữ source attributes nullable. Helper không thay nghĩa source missing thành technical Unknown.

Ở snapshot này có thể dừng batch khi lookup lỗi và sửa mapping trước khi chạy lại, thay vì tự tạo cơ chế Unknown/SCD phức tạp. Ghi số lỗi, không âm thầm bỏ records. `SourceFileID + SourceRecordOrdinal` là unique lineage của Fact; manifest giữ checksum/snapshot. Full reload có kiểm soát là đủ cho bài học một snapshot, không cần CDC hay SCD2.

`SourceRowNumber` để NULL trong lần load đầu vì TSV 52 cột không xuất physical line; lineage vẫn có ordinal + checksum. Không gán ordinal+1 do raw có multiline records. `ETLBatchID` tạo một lần cho cả package run. `AsOfDate` và DQ details giữ trong input/manifest và reports Chương 1; chưa cần thêm bảng audit hoặc sửa grain Fact.

## Đối soát đơn giản bắt buộc

| Kiểm tra | Kỳ vọng |
|---|---:|
| Input / COUNT(Fact_Loan) / SUM(RecordCount) | 388338 |
| SUM(GrossApproval) | 202550139718.000 |
| SUM(SBAGuaranteedApproval) | 152596337956.289 |
| SUM(GrossChargeOffAmount) | 898807495.320 |
| SUM(JobsSupported) | 4072432 |
| Trùng (SourceFileID, SourceRecordOrdinal) | 0 |
| FK orphan / lookup errors / conversion errors | 0 trước nghiệm thu |

Đối chiếu thêm FY/raw-status counts với `reports/preprocessing/reconciliation.csv`. Expected observed dimension tuples đã audit: Geography 4848, Industry 1171, Lender 2338, LoanProfile 93, Business 22, LoanStatus 5; Date/TermBand counts phụ thuộc seed/calendar design. Nếu thêm special members, báo tách số seed và observed members.

Q1–Q12/Q14 có source fields cần thiết; Q13/Q15 có candidate sector để phát triển nhưng kết quả sector chính thức chờ reference/version verification. Các gates Q12/Q15 là query rules, không lọc input ETL.

## Cách tổ chức báo cáo theo mẫu

Đã đọc text và kiểm một số trang minh họa; số trang dưới đây là **PDF page, tính từ 1**:

- [Spotify — mẫu 15](../../references/%5B15%5D_IS217P11_22520542_22520464.pdf): trang 23–32 chuẩn bị công cụ, database, project, Flat File/Multicast/Sort; trang 96–100 nạp Fact qua các luồng kết nối. SBA không cần sao chép các bridge/merge nhiều tầng của Spotify.
- [Bank Transaction Fraud — mẫu 27](../../references/%5B27%5D_IS217Q13_23520698_23521417.pdf): trang 39–47 công cụ/database/project/Execute SQL Task; trang 167–177 Fact và Lookup; trang 203–208 thứ tự chạy, dữ liệu và lược đồ kết quả.
- [TMDB — mẫu 6](../../references/%5B6%5D_IS217Q11_23520009_23520753.pdf): trang 31–39 Execute SQL Tasks; trang 164–167 Derived Column/Fact Lookup; trang 172–175 thứ tự Control Flow và kết quả. Dùng cách trình bày từng bước/ảnh thật, không cần copy thao tác drop toàn bộ tables.

Một số mẫu hướng dẫn Configure Management Data Warehouse (Data Collection). Database ứng dụng SBA chỉ cần database đồ án và các target tables, không cần cấu hình kho giám sát hệ thống đó.

Chương 2 đề xuất: 2.1 Công cụ; 2.2 Database/schema; 2.3 Project và connections; 2.4 Load Dimensions; 2.5 Load Fact; 2.6 Chạy/đối soát. Không bắt buộc production monitoring, CDC hoặc hạ tầng audit riêng.
