# Thiết kế FactLoanSnapshot

PROPOSED, 2026-09-28. Căn cứ [KPI Catalog](../business_requirements/kpi_catalog.md), [Business Rules](../business_requirements/business_rules.md), [proposal](dimensional_model_proposal.md).

## 1. Hợp đồng Fact

| Thành phần | Nội dung |
|---|---|
| Fact Table Name | FactLoanSnapshot |
| Grain | Một dòng trong FactLoanSnapshot đại diện cho một bản ghi CSV SBA 7(a) được công bố trong snapshot ngày 30/06/2026, được định danh nguồn bằng file bất biến và thứ tự bản ghi trong file. |
| Fact Type | Record-level point-in-time snapshot; gần Periodic Snapshot nhưng chỉ một kỳ, không periodic aggregate chuẩn. Lý do/giới hạn tại proposal §4 |
| Primary Key | LoanSnapshotKey, surrogate nội bộ, không SBA LoanID |
| Unique source identity | (SourceFileID, SourceRecordOrdinal), độc lập ETLBatchID; replay cùng file không thêm fact |
| Foreign Keys | ApprovalDateKey, FirstDisbursementDateKey, PaidInFullDateKey, ChargeOffDateKey, AsOfDateKey → DimDate; GeographyKey, IndustryKey, LenderKey, BusinessKey, LoanCharacteristicsKey, LoanStatusKey → sáu dim còn lại |
| Stored Measures | GrossApproval, SBAGuaranteedApproval, GrossChargeOffAmount, JobsSupported, RecordCount |
| Numeric observations | TermInMonths, InitialInterestRate; không expose SUM làm KPI |
| Degenerate Dimensions | Không business transaction number đáng tin; không phát minh DD LoanID. File/ordinal là lineage, không DD nghiệp vụ |
| Technical Attributes | SourceFileID, SourceRecordOrdinal, SourceRowNumber, ETLBatchID; PK/FK; audit chi tiết ngoài star |
| Source | FOIA_7a_FY2020_Present_asof_260630.csv; 388.338 records; AsOfDate=2026-06-30 |

LoanSnapshotKey dự kiến bigint, dim keys integer; đây là kiểu logic, không DDL. Amount dùng decimal exact, không float; precision/scale chốt ở mapping đầy đủ. Term/jobs dùng số nguyên sau kiểm tính nguyên, giữ text nguồn staging; rate decimal nullable, giữ đơn vị nguồn đến khi xác minh.

## 2. Measures và additivity

Phân loại chính trong **một snapshot**. Theo [Kimball](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/additive-semi-additive-non-additive-fact/), tỷ lệ phải tổng hợp thành phần rồi chia. Nếu tương lai lưu nhiều snapshot, amount/count/jobs là **SEMI_ADDITIVE qua AsOfDate**, dù cộng được theo ApprovalDate/cohort và lát cắt rời nhau. Hiện cấm SUM qua snapshots.

| Measure | Additivity | Stored / Calculated | Reason |
|---|---|---|---|
| GrossApproval | ADDITIVE trong snapshot; SEMI_ADDITIVE qua snapshot | Stored | Tổng phê duyệt, không số dư/giải ngân |
| SBAGuaranteedApproval | ADDITIVE trong snapshot; SEMI_ADDITIVE qua snapshot | Stored | Bảo lãnh phê duyệt cùng population |
| GrossChargeOffAmount | ADDITIVE trong snapshot; SEMI_ADDITIVE qua snapshot | Stored | K13 chỉ SUM CHGOFF; không net loss hoặc flow giữa snapshots |
| JobsSupported | ADDITIVE trong snapshot; SEMI_ADDITIVE qua snapshot | Stored | Tổng tự khai theo dòng, không người/việc làm duy nhất |
| RecordCount | ADDITIVE trong snapshot; SEMI_ADDITIVE qua snapshot cho KPI danh mục | Stored 1 | SUM khớp COUNT(*) kể cả duplicates |
| TermInMonths | NON_ADDITIVE | Stored observation | Để band/drill-through; tổng tháng hồ sơ không có nghĩa BQ16 |
| InitialInterestRate | NON_ADDITIVE | Stored observation nullable | K11 tính SUM/COUNT(rate), không SUM rate làm KPI |
| NonSBAGuaranteedApproval | ADDITIVE trong snapshot; SEMI_ADDITIVE qua snapshot | Calculated, không cột fact chính | Hiệu hai amount/SUM đủ K07, tránh dư thừa |

K11 tạm loại NULL, **không tự loại 87 số 0**, chưa hiển thị % khi chưa xác minh đơn vị. Hidden SUM(rate)/COUNT(rate) có thể cấu hình cube, không cần cột row-level dư. Term=0 giữ 0, band ZeroUnverified, không đổi NULL/short-term. Rate/term chi tiết ở Fact tránh dimension numeric quá lớn; bands ở Dimension phục vụ slice.

## 3. Stored và calculated KPI contract

G=GrossApproval, S=SBAGuaranteedApproval, C=GrossChargeOffAmount, J=JobsSupported, R=InitialInterestRate, N=SUM(RecordCount). P là một snapshot cùng slicer; mặc định cả 5 status theo BR03 PROPOSED, giữ duplicates. Chia với mẫu >0, mẫu 0/không có dữ liệu → NULL. NULL số không tự thành 0. Đơn vị tiền dự kiến USD theo catalog, cần xác nhận phát hành.

| KPI | Formula | Required Stored Measures | Dimensions | Aggregation Behavior |
|---|---|---|---|---|
| K01 ApprovalRecordCount | N(P) | RecordCount | Mọi dim | SUM/COUNT dòng |
| K02 TotalGrossApproval | SUM_P G | G | Mọi dim | SUM một snapshot |
| K03 AverageGrossApproval | SUM_P G / N(P) | G, RecordCount | Date, Characteristics; Geography slicer | Ratio of sums, không AVG average |
| K04 YoYApprovalGrowth | (A_t − A_prev)/A_prev ×100 | G | Approval Date, Geography | Hai SUM cùng cửa sổ; FY2020 thiếu FY2019 → NULL; FY2026 dùng 01/10–30/06 cả hai FY |
| K05 GrossApprovalShare (StateApprovalShare là một ứng dụng) | SUM_group G / SUM_parent G ×100 | G | Date + chiều chia nhóm | Chỉ gỡ filter trục chia nhóm |
| K06 TotalSBAGuaranteedApproval | SUM_P S | S | Date, Characteristics | SUM |
| K07 NonSBAGuaranteedApproval | SUM_P G − SUM_P S | G, S | Lender, Characteristics, Date | Hiệu hai SUM cùng tập |
| K08 WeightedGuaranteeRatio | SUM_P S / SUM_P G ×100 | S, G | Date, Geography, Industry | Không AVG tỷ lệ từng dòng |
| K09 TotalReportedJobsSupported | SUM_P J | J | Date, Geography, Industry | SUM tự khai |
| K10 ApprovalPerReportedJob | SUM_P G / SUM_P J | G, J | Date, Geography, Industry | Tính lại roll-up; mẫu jobs=0 → NULL |
| K11 AverageInitialInterestRate | SUM_P R / COUNT_P(R), R không NULL | R; RecordCount báo tổng mẫu | Characteristics, Date nếu lọc | Unweighted mean số nguồn; báo n(rate),n(all),n(zero); OPEN |
| K12 StatusRecordShare | N(status=s,P)/N(all status,cùng P) ×100 | RecordCount | Status + Date/Geography/Industry/Characteristics | Bỏ status filter ở mẫu, giữ các chiều khác |
| ObservedChargeOffRecordShare = K12(s=CHGOFF) | Count CHGOFF/count mọi status ×100 | RecordCount | Status, Date, Geography, Industry | Tỷ trọng quan sát, không default probability |
| ObservedPIFRecordShare = K12(s=`P I F`) | Count literal `P I F`/count mọi status ×100 | RecordCount | Status, Date, Characteristics | Raw-label share; BR06 còn OPEN |
| K13 TotalGrossChargeOffAmount | SUM_{P,status=CHGOFF} C | C; RecordCount báo mẫu | Status, Approval Date, Geography, Industry | SUM có điều kiện, không loại event date thiếu/sau snapshot trong KPI cohort |

K03/04/05/07/08/10/11/12 tính ở semantic/query layer. Không lưu %/mean cố định mỗi fact row: filter, parent, time window thay đổi theo cell; SUM/AVG các tỷ lệ tạo sai số. K07 chỉ materialize sau nếu có nhu cầu hiệu năng và đối soát hiệu tổng. K13 là source measure với filter, không Fact mới.

Parent K05: BQ04 mọi size band trong FY×age; BQ11 mọi state cùng FY; BQ12 mọi ngành trong state×FY; BQ15 mọi lender cùng FY; BQ16 mọi term band trong method×FY. Top N xếp K02, mẫu số tất cả lender, hiển thị Other. Bỏ đồng bộ các filter của hierarchy phân chia (state/county phụ thuộc hoặc code/description/sector) theo parent được định nghĩa; giữ slicer độc lập có chủ đích. Với Characteristics chứa method và band, chỉ bỏ band, **không bỏ toàn dimension**. Unknown vẫn nằm mẫu. Kiểm auto-exist/filter context trong công cụ OLAP khi triển khai.

## 4. Technical fields

| Attribute | Phân loại | Nơi đề xuất | Lý do/quy tắc |
|---|---|---|---|
| LoanSnapshotKey | CORE | Fact PK | Định danh row; duplicate nội dung vẫn khác PK |
| Dimension surrogate keys | CORE | Dim PK, Fact FK | Lookup đúng một member; không dùng tên làm FK |
| SourceFileID | CORE | Fact và audit file | Định danh nội dung bất biến, không chỉ basename |
| SourceRecordOrdinal | CORE | Fact | Bản ghi dữ liệu từ 1, độc lập multiline |
| SourceRowNumber | CORE | Fact | Dòng vật lý bắt đầu record, header=1; không ordinal+1 sau multiline |
| SourceRowEndNumber | AUDIT | Audit record | Dòng kết thúc; truy vết multiline |
| SourceFileName | AUDIT; lineage CORE | Audit file | Tên/đường dẫn gốc, Fact chỉ giữ ID |
| SourceFileSHA256 | CORE lineage | Audit file | Xác minh byte file; file identity + ordinal |
| SourceRowHash | OPTIONAL | Audit record | Hash 42 chuỗi trước cleaning, không UNIQUE/LoanID |
| ETLBatchID | CORE | Fact và audit batch | Theo dõi load/replay; không thuộc unique source identity |
| ETLLoadTimestamp | AUDIT | Audit batch | Timestamp UTC lúc nạp khác AsOfDate; full rebuild không cần lặp |
| DataQualityFlag | AUDIT; yêu cầu DQ CORE | Audit issue nhiều dòng/record | Mã DQ, detail; không boolean duy nhất làm mất loại lỗi; Fact existence flag OPTIONAL |
| RecordCount | CORE semantic; chọn stored | Fact hằng 1 | Cube SUM và đối soát 388.338 |
| Business LoanID tự tạo | NOT NEEDED | Không có | PK/hash không chứng minh unique loan |
| SCD ValidFrom/ValidTo/IsCurrent | NOT NEEDED trong scope | Không có | Không suy lịch sử từ một snapshot |

Audit file/batch/issue là metadata, không analytical Fact/Dimension thêm. Đọc issue bằng EXISTS hoặc aggregate trước join, tránh fan-out measures. Row hash đề xuất SHA-256 trên JSON array 42 strings theo thứ tự header, UTF-8, escape chuẩn, không trim; chỉ là thiết kế chưa chạy ETL. Hash parser content không thay checksum file byte.

## 5. Date/DQ và đối soát dự kiến

Ngày parse được vẫn lookup ngày nguồn, kể cả 22 ChargeOffDate sau snapshot; không ép về AsOfDate. FK không chứng minh event hợp lệ. Event query cần predicate `ApprovalDate ≤ event date ≤ AsOfDate` và status phù hợp, kiểm qua audit. Ngày thiếu/không parse dùng special member Missing/Invalid. Hai PaidInFullDate trước ApprovalDate và một date/status mâu thuẫn giữ raw+issue. BQ20–23 dùng approval cohort và status snapshot, không phụ thuộc event date hợp lệ.

Acceptance criteria cho ETL tương lai, **chưa thực thi**: 388.338 source identities; SUM(RecordCount)=COUNT(*); mọi FK đúng một member; count/tổng không đổi sau join; giữ 687 duplicate rows; NAICS join không fan-out; 16 multiline truy lại đúng; rate denominator=COUNT(rate), không N(all); K07 khớp hiệu tổng; nhóm gồm Unknown cộng về tổng; chỉ một snapshot được chọn.
