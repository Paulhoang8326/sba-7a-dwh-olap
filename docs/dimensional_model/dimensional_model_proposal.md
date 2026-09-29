# Đề xuất mô hình đa chiều SBA 7(a)

Ngày lập: 2026-09-28. **PROPOSED — thiết kế logic để rà soát**, chưa duyệt các rules còn mở, chưa thay prototype, ETL hoặc database.

## 1. Căn cứ và nguyên tắc

Đã đọc bốn tài liệu data understanding: [overview](../data_understanding/data_overview.md), [dictionary](../data_understanding/data_dictionary.md), [profiling](../data_understanding/data_profiling_report.md), [quality](../data_understanding/data_quality_report.md); tám tài liệu business requirements: [objectives](../business_requirements/business_objectives.md), [BQ catalog](../business_requirements/business_questions_catalog.md), [selection](../business_requirements/business_questions_selection.md), [OLAP](../business_requirements/olap_analysis_requirements.md), [rules](../business_requirements/business_rules.md), [KPI catalog](../business_requirements/kpi_catalog.md), [KPI–BQ mapping](../business_requirements/kpi_business_question_mapping.md), [derived attributes](../business_requirements/derived_attribute_requirements.md). Đọc trực tiếp sheet `7(a) Data Dictionary` trong [workbook SBA](../../data/raw/foia/7a_504_foia_data_dictionary.xlsx).

Ưu tiên 19 BQ và K01–K13 của requirements hiện tại. README/PROJECT_CONTEXT/prototype mô tả hiện trạng khác; không quyết định schema mới. KPI catalog vẫn là ứng viên, K11 OPEN. Không mang resolved-only rate, weighted interest hoặc KPI 36 tháng từ prototype vào phạm vi mới.

Thiết kế đi theo **BQ → KPI → measures → dimensions → kiểm tra grain**; grain phải được xác định trước bảng Fact. Không chia cơ học 42 cột thành bảng. Một cột có trong CSV không tự tạo nhu cầu Dimension. Mọi ngưỡng/phương án mới dưới đây là đề xuất, không tự đổi PROPOSED/OPEN thành VERIFIED.

| Nhóm BQ | KPI | Thành phần đo | Chiều cần thiết | Hệ quả đối với grain |
|---|---|---|---|---|
| BQ01–04 | K01–K05 | Count dòng, GrossApproval | Approval date, geography, method, size, business age | Giữ dòng để đếm và phân nhóm lại |
| BQ06–08 | K06–K08 | GrossApproval, SBAGuaranteedApproval | Date, geography, industry, lender, method | Hai amount trên cùng bản ghi |
| BQ10–12,14 | K01,K02,K05,K09,K10 | Count, approval, jobs | Date, geography, industry | Không gộp sớm mất giao cắt |
| BQ15–18 | K01–K03,K05,K11 | Count, approval, rate; term để band | Date, lender, characteristics, business, geography | Giữ rate/term gốc để đổi policy |
| BQ20–23 | K01,K12,K13 | Count, gross charge-off | Approval cohort, as-of, status, industry, geography, size | Cùng bản ghi tại snapshot, không là event history |

## 2. Kiểm tra trực tiếp phục vụ thiết kế

Đọc CSV bằng parser CSV, không ghi lại nguồn, ngày 2026-09-28. SHA-256 xác nhận `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe`. Xác nhận 388.338 bản ghi, 687 dòng trong 296 nhóm exact duplicate, 391 bản sao dư. Các thống kê DQ khác dẫn từ profiling hiện hành; **không tuyên bố chạy lại toàn bộ profiling**.

| Kiểm tra trực tiếp | Kết quả | Hệ quả |
|---|---|---|
| LocationID → 7 thuộc tính bank | 2.338 IDs; 0 ID có nhiều tổ hợp bank | LocationID làm BK trong snapshot, kiểm FD mỗi lần nạp |
| NAICS code → description raw | 1.157 mã; 1.795 cặp; 638 mã có nhiều mô tả | Giữ cặp code + description; nhóm BQ theo mã |
| NAICS sau trim chỉ để chẩn đoán | 14 mã vẫn có nhiều mô tả | Không chọn một canonical name tùy ý |
| Bốn thuộc tính geography | 4.848 tổ hợp | Một fact lookup đúng một tổ hợp |
| BusinessType × BusinessAge raw | 22 tổ hợp gồm biểu diễn thiếu | Dimension profile nhỏ |
| Characteristics + bands đề xuất | 521 tổ hợp method/rate type/revolver/collateral/size/term | Một dimension kết hợp vẫn phù hợp đồ án |
| CSV multiline | 16 bản ghi có newline trong ô | Record ordinal khác số dòng vật lý |

Ví dụ multiline: ordinal 13.092 bắt đầu dòng vật lý 13.093, kết thúc 13.094; ordinal 52.821 bắt đầu 52.823, kết thúc 52.824. Đây là tọa độ truy vết, không LoanID. Cardinality trên là raw và các band đề xuất, chưa phải số member sau cleaning.

## 3. Grain

**Một dòng trong `FactLoanSnapshot` đại diện cho một bản ghi CSV SBA 7(a) được công bố trong snapshot ngày 30/06/2026, được định danh nguồn bằng file bất biến và thứ tự bản ghi trong file.**

| Phương án | Khả thi | COUNT và duplicate | Quyết định |
|---|---|---|---|
| A — một bản ghi công bố/snapshot | Có: file checksum + record ordinal | COUNT(*)=388.338 toàn file, giữ 687 dòng trùng | Chọn; bảo toàn K01–K13 và đối soát |
| B — một khoản vay duy nhất | Chưa có public LoanID đáng tin cậy | Borrower+date+amount không chứng minh cùng loan | Không chọn; cần ID/đối soát SBA |

687 là số dòng trong các nhóm trùng, không phải số cần xóa. DISTINCT 42 cột làm mất 391 dòng (còn 387.947), thay đổi count, tiền và jobs. Không thực hiện. Hash giống nhau vẫn có nhiều ordinal và nhiều fact rows. Distinct lender/code chỉ đếm thành viên phân loại, không thay K01.

Grain hỗ trợ tổng/cơ cấu/bình quân/count dòng tại snapshot, không hỗ trợ unique-loan count, lịch sử chuyển trạng thái, dư nợ, cash flow hay causal impact. Cohort mới ít thời gian quan sát hơn. Multi-snapshot cần hợp đồng identity/lineage mới; không nối loan bằng surrogate key hoặc hash.

## 4. Fact và Dimension

**Một Fact, bảy Dimension logic:** `FactLoanSnapshot`; `DimDate`, `DimProjectGeography`, `DimIndustry`, `DimLender`, `DimBusiness`, `DimLoanCharacteristics`, `DimLoanStatus`. Năm date roles dùng một DimDate. Audit/reference không tính vào số chiều phân tích.

Tên FactLoanSnapshot phù hợp quan sát hồ sơ tại ngày chụp; chữ Loan không biến row thành unique loan. Loại **record-level point-in-time snapshot**, gần nhóm **Periodic Snapshot** trong bốn loại yêu cầu, nhưng mới có một kỳ quan sát, chưa có lịch nạp định kỳ và không phải periodic aggregate chuẩn theo tháng. Đây là giới hạn phân loại quan trọng. Không gọi transaction vì một dòng chứa nhiều mốc và trạng thái quan sát; không accumulating snapshot vì không có identity/process để cập nhật cùng loan; không factless vì có measures. Tham khảo khái niệm [Periodic Snapshot của Kimball](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/periodic-snapshot-fact-table/); áp dụng cho nguồn này là lựa chọn thiết kế có giới hạn.

Một Fact đủ vì 19 BQ là các lát cắt trên cùng grain. Không có payment/charge-off transaction grain để biện minh thêm Fact. Các mốc ngày là thuộc tính cùng bản ghi. Chi tiết tại [Fact](fact_table_design.md), [Dimension](dimension_design.md), [Star schema](star_schema.md), [Bus matrix](bus_matrix.md), [Coverage/mapping](schema_coverage.md).

## 5. Alternative designs

| Quyết định | So sánh | Recommendation |
|---|---|---|
| Một dimension lớn loan/business | Ít FK nhưng tổ hợp type/age/franchise/method/bands tăng mạnh, trộn hai khái niệm và tái tạo khi đổi band | Không gộp toàn bộ |
| Program + Business + Characteristics | Tách Business rõ, nhưng Program chỉ một giá trị; dim riêng cho method thêm bảng nhỏ | Chọn biến thể hai bảng Business + Characteristics, method trong Characteristics; Program ở metadata |
| BusinessType/BusinessAge | Gộp Characteristics tiết kiệm một FK nhưng nhân tổ hợp; riêng Business chỉ 22 tổ hợp raw, BQ04/17 rõ, mở rộng độc lập | DimBusiness chỉ type/age, không borrower entity; chưa thêm franchise |
| LoanStatus riêng/gộp | Gộp ít FK nhưng nhân tổ hợp 5 status; riêng giúp quản lý mapping và K12 bỏ filter status giữ method/band | DimLoanStatus riêng |
| Borrower có/không | 323.752 tên, 333.651 street raw; cardinality lớn, không BK tin cậy, 19 BQ không phân tích borrower | Không DimBorrower; giữ raw/staging để truy vết; mở rộng khi có BQ/identity policy |
| Franchise | 3.690 mã, thiếu phần lớn; thêm vào Business tăng cardinality, không BQ chính | Giữ raw/staging, không suy blank là non-franchise |
| Mỗi flag/band một dim | Tái sử dụng tốt nhưng nhiều FK/bảng nhỏ, tăng chi phí vận hành | Một Characteristics; chỉ sinh tổ hợp xuất hiện, không Cartesian product |
| AsOfDate FK/metadata | Metadata đủ mô tả file; FK làm mốc quan sát rõ ở Fact và cube | AsOfDateKey trong Fact, metadata file để đối soát; cấm SUM qua snapshots |
| Star/snowflake | Snowflake giảm lặp nhưng thêm join; không cần cho scope này | Geography gộp state/county, Industry gộp sector; không dim-to-dim FK |
| NonSBAGuaranteedApproval | Stored dễ đọc nhưng dư thừa và phải đối soát; hiệu hai SUM đủ K07 | Calculated, không cột Fact chính |

## 6. Cột nguồn ngoài schema chính

| Cột | Nơi giữ và lý do |
|---|---|
| BorrName, BorrStreet, BorrCity, BorrState, BorrZip | Raw/staging, truy qua file+ordinal; không BQ borrower chính. BQ13 thuộc mở rộng; borrower geography khác borrower identity |
| FranchiseCode, FranchiseName | Raw/staging, chưa BQ chính và chưa có missing policy |
| SoldSecMrktInd | Raw/staging, ngoài 19 BQ; blank không tự đổi N |
| Program | Raw/staging và metadata file, giá trị raw có whitespace; một chương trình không cần dimension riêng; trim chờ DQ14 policy |
| ApprovalFY | Raw/staging đối soát DimDate.FiscalYear; không cột FY dư trong Fact |

RevolverStatus/CollateralInd giữ raw trong Characteristics vì ít giá trị, hỗ trợ drill-through và mở rộng nhẹ, chưa thêm KPI hoặc giải mã Y/N. CongressionalDistrict/SBADistrictOffice và ba event dates giữ theo yêu cầu địa lý/ngày và audit, không dùng chúng làm điều kiện loại population chính.

## 7. Final Summary và readiness

1. Grain: một bản ghi nguồn tại snapshot 30/06/2026; không unique loan.
2. Một Fact và bảy Dimension, tên tại §4.
3. Stored measures: GrossApproval, SBAGuaranteedApproval, GrossChargeOffAmount, JobsSupported, RecordCount. TermInMonths/InitialInterestRate lưu observation non-additive.
4. Calculated KPIs: K03,K04,K05,K07,K08,K10,K11,K12; K01,K02,K06,K09,K13 là count/tổng (K13 lọc CHGOFF). Observed CHGOFF/PIF share là K12.
5. CORE derived: FiscalYear đối soát, FiscalQuarter, FiscalMonth, LoanSizeBand, TermBand, NaicsSectorCode conditional; FYTD predicate động và NonSBAGuaranteedApproval logic. Sector name DEFERRED; loan age OPTIONAL.
6. Technical: PK/FK, SourceFileID, SourceRecordOrdinal, SourceRowNumber, ETLBatchID; audit checksum/file name/line end/row hash/load time/DQ issues. PK không là SBA LoanID.
7. Cột ngoài core và lý do: §6.
8. Rules catalog **OPEN**: BR06, BR07, BR09, BR13, BR14. **PROPOSED chưa duyệt**: BR03, BR04, BR10, BR11, BR15. BR01/02/05/08/12 VERIFIED giữ nguyên nghĩa.
9. **19/19 BQ và 13/13 KPI có đường triển khai logic, chưa 100% sẵn sàng công bố.** BQ12 sector cần reference/version; BQ04/16/18/23 cần band policy; BQ18/K11 cần đơn vị, mã F/V, rate=0.
10. Trước cleaning/ETL cần duyệt population, FYTD, bands, status mapping, NAICS/mô tả, rate/đơn vị tiền, ngày bất thường; đặc tả null/unknown/lookup không nhân dòng, parser multiline/idempotency và đối soát.

**Đã đủ cơ sở xây dựng Source-to-Target Mapping đầy đủ và Data Cleaning Rules dạng dự thảo có decision gates. Chưa đủ để chốt mapping/rules thực thi hoặc chạy cleaning/ETL.** Có thể viết bản dự thảo với placeholder và người duyệt; không tự biến PROPOSED thành VERIFIED. Task này chỉ tạo sáu tài liệu, không triển khai bước tiếp theo.

## 8. Kiểm tra bàn giao tài liệu

Đã kiểm tra sáu file Markdown, links nội bộ tới file đích, số cột bảng và cặp code fences; coverage đủ 19 BQ, 13 KPI, 15 DQ. Đối chiếu 71 trường khai báo theo bảng trong Mermaid đều xuất hiện trong mapping sơ bộ; 11 Fact FK có đủ 11 quan hệ tới Dimension, tổng cộng 8 entities gồm 1 Fact và 7 Dimension. Đây là kiểm tra cấu trúc văn bản, chưa render/parse Mermaid bằng engine chuyên dụng vì runtime hiện không có Mermaid parser.

Kiểm tra đọc CSV bổ sung: 0 dòng ApprovalFY khác FY dẫn xuất từ ApprovalDate; 0 TermInMonths âm hoặc không nguyên. Chưa chạy ETL, database, cube hoặc tính lại toàn bộ 13 KPI. Git chỉ có thư mục tài liệu mới của task; nguồn CSV, code, SQL và requirements không thay đổi.
