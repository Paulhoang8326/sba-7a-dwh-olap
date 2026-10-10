> **HISTORICAL REFERENCE — NOT CURRENT CONTRACT.** Giữ nguyên nội dung đóng góp từ `main` để tham khảo lịch sử. Các tên bảng, số Dimensions và trạng thái implementation bên dưới không thay thế [trạng thái hiện hành](../00_current_status.md), [schema hiện hành](../dimensional_model/candidate_schema.md) hoặc [kế hoạch SSIS Chương 2](../etl/chapter2_ssis_plan.md). Chương 1 hiện là `CHAPTER 1 READY TO FREEZE`; preprocessing đã tích hợp và TSV đã tái lập, warehouse/SSIS chưa triển khai.

# Coverage, derived attributes, DQ và mapping sơ bộ

PROPOSED, 2026-09-28. Căn cứ [19 BQ](../business_requirements/business_questions_selection.md), [KPI catalog](../business_requirements/kpi_catalog.md), [derived requirements](../business_requirements/derived_attribute_requirements.md), [DQ report](../data_understanding/data_quality_report.md). Schema/mapping dưới đây chưa chạy transformation.

## 1. Coverage 19 Business Questions

F=FactLoanSnapshot; D=DimDate (Approval role + AsOf role), G=DimProjectGeography, I=DimIndustry, L=DimLender, B=DimBusiness, C=DimLoanCharacteristics, S=DimLoanStatus. RC=RecordCount. YES là có đường triển khai logic, **không phải đã deploy hoặc đã được duyệt công bố**. CONDITIONAL là schema đủ cột nhưng thiếu rule/reference cho phần yêu cầu đó. Mọi BQ chịu policy population/đơn vị chung chưa chốt.

| BQ | Fact | Required Dimensions | Required Measures | Supported? | Notes |
|---|---|---|---|---|---|
| BQ01 vốn FY/quý/state | F | D,G | GrossApproval | YES | Fiscal quarter/month, FY2026 partial |
| BQ02 count/average theo FY/method | F | D,C; G slicer | RC,GrossApproval | YES | K01,K03; count dòng; method raw |
| BQ03 growth/state | F | D,G | GrossApproval hai windows | CONDITIONAL | K04; duyệt BR04 FYTD; FY2020 không kỳ trước trong file |
| BQ04 size×age×FY | F | D,C,B | RC,GrossApproval | CONDITIONAL | K01,K02,K05; duyệt LoanSizeBand, Missing age riêng |
| BQ06 guarantee/method | F | D,C | SBAGuaranteedApproval | YES | K06, raw method |
| BQ07 guarantee ratio | F | D,G,I | GrossApproval,SBAGuaranteedApproval | YES theo code | K08; sector chỉ khi reference VERIFIED |
| BQ08 ngoài guarantee/lender/method | F | D,L,C | GrossApproval,SBAGuaranteedApproval | YES | K07; lender currently assigned |
| BQ10 state/county | F | D,G | RC,GrossApproval | YES | K01,K02; county key gồm state |
| BQ11 state share | F | D,G | GrossApproval | YES | K05 parent mọi state trong FY |
| BQ12 roll-up NAICS→sector | F | D,G,I | RC,GrossApproval | CONDITIONAL | K01,K02,K05; code có thể tính, sector thiếu version/reference, không tuyên bố hoàn thành BQ12 chỉ bằng raw code |
| BQ14 jobs/vốn mỗi job | F | D,G,I | JobsSupported,GrossApproval | YES theo code | K09,K10, jobs>0 ở mẫu; diễn giải lender-reported |
| BQ15 lender concentration | F | D,L; G slicer | RC,GrossApproval | YES | K01,K02,K05; Top N rank K02, denominator toàn lender |
| BQ16 term×method×FY | F | D,C | RC,GrossApproval; TermInMonths tạo band | CONDITIONAL | K01,K02,K05; duyệt band, 11 zero riêng |
| BQ17 business type/age | F | D,G,B | RC,GrossApproval | YES raw labels | K01,K02; Missing khác Unanswered |
| BQ18 initial rate | F | C; D slicer | InitialInterestRate,RC | CONDITIONAL | K11; unit/FV/87 zeros/8 NULLs/band OPEN; average không trọng số theo catalog |
| BQ20 status composition | F | D,C,S | RC | YES raw labels | K01,K12; approval cohort tại một as-of |
| BQ21 observed CHGOFF share | F | D,G,I,S | RC | YES theo code | K12(s=CHGOFF); denominator mọi status, không default rate |
| BQ22 gross charge-off | F | D,G,I,S | GrossChargeOffAmount,RC | CONDITIONAL policy | K13/K01 CHGOFF; BR10 chưa duyệt, không event-date filter cho cohort total |
| BQ23 observed PIF share×size | F | D,C,S | RC | CONDITIONAL | K12 literal P I F; size OPEN; diễn giải canonical PIF chờ BR06 |

**Kết quả:** 19/19 có đường triển khai trong cùng Fact; không cần thêm Fact. Có 7 hàng CONDITIONAL (BQ03,04,12,16,18,22,23); 12 hàng còn lại có đường tính bằng thuộc tính/nhãn nguồn nhưng vẫn chịu rules chung. BQ07/14/21/22 roll-up sector cũng conditional nếu người dùng chọn sector. Không đánh đồng logical coverage với dữ liệu/reference sẵn sàng hoặc kết quả kiểm thử OLAP.

Median lãi suất là lựa chọn gợi ý trong BQ catalog, không KPI chốt trong K01–K13; rate row-level được giữ nên có thể tính median ở query hỗ trợ, không cộng median từ nhóm. Không tự thêm median KPI chính.

## 2. Coverage KPI K01–K13

| KPI | Stored Measures | Dimensions | Derived Attributes | Supported? |
|---|---|---|---|---|
| K01 ApprovalRecordCount | RecordCount | D,G,I,L,B,C,S | Hằng 1 | YES; rows, không unique loans |
| K02 TotalGrossApproval | GrossApproval | D,G,I,L,B,C; S filter | FiscalQuarter/Month, bands tùy BQ | YES; population BR03 PROPOSED |
| K03 AverageGrossApproval | GrossApproval,RecordCount | D,C; G slicer | Không | YES, ratio of sums |
| K04 YoYApprovalGrowth | GrossApproval | D,G | FiscalYear/Month; FYTD động | CONDITIONAL BR04; FY2020 trả NULL |
| K05 GrossApprovalShare | GrossApproval | D,G,I,L,B,C | Size/term/sector tùy phân nhóm | CONDITIONAL từng band/sector; state/lender trực tiếp |
| K06 TotalSBAGuaranteedApproval | SBAGuaranteedApproval | D,C | Không | YES |
| K07 NonSBAGuaranteedApproval | GrossApproval,SBAGuaranteedApproval | D,L,C | Hiệu hai tổng | YES, không cần stored derived amount |
| K08 WeightedGuaranteeRatio | GrossApproval,SBAGuaranteedApproval | D,G,I | Sector nếu roll-up | YES theo code, không AVG tỷ lệ |
| K09 TotalReportedJobsSupported | JobsSupported | D,G,I | Sector nếu roll-up | YES, tổng reported |
| K10 ApprovalPerReportedJob | GrossApproval,JobsSupported | D,G,I | Không ngoài sector tùy chọn | YES, mẫu >0 |
| K11 AverageInitialInterestRate | InitialInterestRate; RC báo mẫu | C | LoanSizeBand | CONDITIONAL, unit/rate policy/FV OPEN |
| K12 StatusRecordShare | RecordCount | D,S,C,G,I | Size BQ23, sector tùy chọn | YES raw status; CONDITIONAL BQ23 band/canonical meaning |
| K13 TotalGrossChargeOffAmount | GrossChargeOffAmount | D,G,I,S | DQ event-date audit | CONDITIONAL BR10 trước công bố; schema có đủ amount/status |

13/13 có measures và đường join. Công thức/parent/aggregation xem [Fact design §3](fact_table_design.md#3-stored-và-calculated-kpi-contract). Không KPI nào đòi LoanID, số dư hoặc recovery chưa có.

## 3. Derived attribute coverage

CORE=phục vụ BQ chính hoặc logic bắt buộc, không đồng nghĩa đã VERIFIED hay phải stored. OPTIONAL=hữu ích; DEFERRED=cần scope/reference bổ sung.

| Attribute | Source | Logic | Related BQ/KPI | Target Dimension/Fact | Necessity | Explanation |
|---|---|---|---|---|---|---|
| FiscalYear | Ngày của từng role; ApprovalFY đối soát approval | year+1 nếu month≥10, khác year | Mọi BQ theo FY; K04 | DimDate, stored | CORE | FY nguồn chỉ cho approval, không đủ vai trò ngày; kiểm khớp ApprovalFY, không Fact.FiscalYear dư |
| FiscalQuarter | FullDate | floor((FiscalMonth−1)/3)+1 | BQ01/K02; BQ03/K04 | DimDate, stored | CORE | CSV không có quý tài chính, cần drill FY→quarter |
| FiscalMonth | FullDate | ((month+2) mod 12)+1 | BQ01,03/K02,K04 | DimDate, stored | CORE | Thứ tự tháng FY/FYTD không có trong nguồn |
| CalendarYear | FullDate | year | Calendar drill tùy chọn; K01/K02 khi dùng | DimDate, stored | OPTIONAL | Ngày nguồn cần thuộc tính nhóm, không lồng calendar quarter dưới FY |
| CalendarQuarter | FullDate | ceil(month/3) | Calendar drill tùy chọn | DimDate, stored | OPTIONAL | Không bắt buộc 19 BQ, dễ sinh trong Date |
| CalendarMonth, MonthName | FullDate | month, tên tháng và sort | Calendar labels; K01/K02 tùy view | DimDate, stored | OPTIONAL | Nhãn hiển thị và sort; không dùng name làm key xuyên năm |
| FiscalYTDFlag | ApprovalDate, cutoff, FY | Thuộc cửa sổ 01/10 đến cùng ngày cắt theo FY được chọn | BQ03/K04 | Semantic/query, không Fact/Dim boolean cố định | CORE logic | Thay cutoff thì predicate đổi; FY2026 so 2025-10-01..2026-06-30 với 2024-10-01..2025-06-30; tương lai cutoff 29/02 phải có policy |
| LoanSizeBand | GrossApproval | Năm khoảng 50k/150k/500k/1m; zero/missing/invalid riêng | BQ04,18,23/K01,K02,K05,K11,K12 | DimLoanCharacteristics, stored sau duyệt | CORE, OPEN | Cột tiền liên tục không có phân loại nhất quán; [ngưỡng và phân bố](dimension_design.md) là project-defined |
| TermBand | TermInMonths | (0,60],(60,120],>120; zero/missing/invalid riêng | BQ16/K01,K02,K05 | DimLoanCharacteristics, stored sau duyệt | CORE, OPEN | Cần nhóm so cơ cấu; 11 dòng 0 không short-term |
| LoanSizeBandSort, TermBandSort | Bảng band được duyệt | 1..n; exceptional 90..92 | Các BQ dùng band | DimLoanCharacteristics, stored | CORE hỗ trợ band | Sắp theo ý nghĩa số, không alphabet; không KPI độc lập |
| BandRuleVersion | Rule registry | Nhãn phiên bản PROPOSED-v1, chuyển approved khi duyệt | BQ04,16,18,23 | DimLoanCharacteristics, stored; provenance audit | CORE kiểm soát band | Tái lập ngưỡng và tránh mix definitions; không SCD loan |
| NaicsSectorCode | NaicsCode + reference | Mapping đúng version, xử lý sector gộp; không prefix mù | BQ12/K01,K02,K05; roll-up BQ07,14,21,22 | DimIndustry, stored sau xác minh | CORE, OPEN | Code nguồn cấp chi tiết không đủ roll-up sector tin cậy |
| NaicsSectorName | Sector reference | Lookup tên theo sector/version đã xác minh | BQ12 nhãn; các KPI sector | DimIndustry, nullable | DEFERRED | Không suy từ NaicsDescription; hiện thiếu reference |
| NaicsVersion, SectorMappingStatus | Reference và kết quả đối chiếu | NULL/UNVERIFIED trước evidence; VERIFIED sau duyệt | BQ12 và sector roll-ups | DimIndustry, stored | CORE kiểm soát sector | Không đoán version theo FY; thiếu mapping phải nhìn thấy |
| NonSBAGuaranteedApproval | GrossApproval,SBAGuaranteedApproval | G−S từng dòng nếu cần, K07=SUM G−SUM S cùng P | BQ08/K07 | Semantic/query; không cột Fact chính | CORE logic | Nguồn chưa có amount phần ngoài bảo lãnh; tính tránh cột dư, storage OPTIONAL nếu cần sau này |
| LoanAgeAtSnapshot | ApprovalDate,AsOfDate | Số ngày as-of trừ approval khi hợp lệ | BQ20–23 diễn giải K12,K13 | Query | OPTIONAL | Ngày nguồn không trực tiếp cho tuổi quan sát; chọn ngày tránh làm tròn tháng; không khử censoring |
| ApprovalToFirstDisbursementDays | Hai ngày nguồn | Difference khi 0≤difference và date≤as-of | Không BQ chính/KPI catalog | Query nếu mở rộng | DEFERRED | DQ06/missing, không phục vụ 19 BQ; không column Fact mới |
| LoanStatusCanonicalCode,StatusMappingStatus | LoanStatus+mapping registry | Raw khớp workbook giữ code; P I F canonical NULL/OPEN tới khi duyệt | BQ20,23/K12 | DimLoanStatus, stored | OPTIONAL canonical; CORE kiểm soát mapping nếu có | Raw đủ đếm; thêm canonical để chuyển đổi có kiểm soát, không ghi đè raw |

FYTD/loan age/duration là logic query không xuất hiện như stored column trong sơ đồ. Những metadata như version/status/sort có giá trị quản trị gắn band/sector/status, không được quảng bá là KPI mới.

## 4. Data Quality impact DQ01–DQ15

Số dòng từ [DQ report](../data_understanding/data_quality_report.md), riêng duplicate được kiểm lại trực tiếp. Một record có thể nhiều issue; không cộng các counts để ra số record lỗi duy nhất.

| DQ | Records | Ảnh hưởng schema và policy đề xuất | KPI/BQ và decision gate |
|---|---:|---|---|
| DQ01 rate missing | 8 | Fact.InitialInterestRate nullable, không impute 0; COUNT(rate) riêng N(all) | BQ18/K11; báo coverage |
| DQ02 rate type missing | 8 | Characteristics giữ Missing F/V, giữ method/bands đã biết; không loại whole record | BQ18/K11; không suy F/V |
| DQ03 BusinessType missing | 34 | Business tuple có NULL type; Missing member label | BQ17/K01,K02; không gán loại phổ biến |
| DQ04 BusinessAge missing | 186 | NULL age riêng literal Unanswered | BQ04/17; K01,K02,K05 |
| DQ05 district missing | 24 | Geography giữ state/county, district Missing; composite BK null-safe | Nhánh district tùy chọn, không mất state/county BQ10 |
| DQ06 P I F thiếu disbursement date | 3 | FirstDisbursementDateKey Missing; issue audit; không impute từ Approval/PIF | Không loại khỏi 19 BQ; duration DEFERRED |
| DQ07 term=0 | 11 | Fact giữ 0, TermBand=ZeroUnverified | BQ16; BR09/13, không short-term |
| DQ08 rate=0 | 87 | Fact giữ 0; audit count zeros; K11 tạm gồm 0 theo catalog | BQ18; BR09/14 OPEN, không công bố % chính thức |
| DQ09 CHGOFF thiếu date | 5 | ChargeOffDateKey Missing; giữ status/amount nguồn; event analysis thiếu date | BQ21/22; không tự loại count/amount cohort |
| DQ10 có PIF date nhưng status khác | 1 | Giữ PaidInFullDateKey và LoanStatusKey độc lập, issue audit; không đổi status | BQ20/23 status-based không suy outcome từ date |
| DQ11 P I F khác PIF | 68.201 | DimLoanStatus raw P I F, canonical NULL và OPEN | BR06; BQ23 lọc literal cho tới mapping được duyệt |
| DQ12 PIF date trước approval | 2 | Giữ actual date key, audit invalid sequence; event/duration query loại theo policy | Không đổi ngày hoặc loại Fact/K12 |
| DQ13 charge-off date sau as-of | 22 | DimDate có actual 2026-07-01; audit future event, không clamp | BQ22 cohort vẫn tính status CHGOFF; event view chỉ ngày≤as-of, BR10 |
| DQ14 Program whitespace | 388.338 | Program ngoài star core, giữ raw metadata/staging; trim đề xuất cần audit | Không tạo Program dim giả có nhiều nhãn; không sửa nguồn |
| DQ15 exact duplicate rows | 687 trong 296 nhóm; 391 dư | PK khác mỗi source ordinal, hash không UNIQUE; giữ 388.338 dòng | Mọi KPI count/amount, không claim unique loans |

Missing conditional: ChargeOffDate ngoài CHGOFF/PIF date ngoài P I F không mặc định lỗi; FDIC/NCUA có thể không áp dụng theo lender; franchise/SoldSecMrktInd blank không suy phủ định. Day-key existence không thay xác thực event. DataQualityFlag là tập issue/audit, không filter loại hàng mặc định.

## 5. Source-to-Target Mapping sơ bộ

Mapping bao phủ **tất cả thuộc tính trong Mermaid schema**, cộng calculated logic và technical audit được yêu cầu. Các dòng gộp nêu từng tên đích rõ ràng; chưa phải mapping thực thi đầy đủ 42 cột. Parse/lookup/generate là thiết kế cho bước sau, không đã transformation. Giữ text raw staging, code có leading zeros không parse numeric. Whitespace/missing normalization phải có policy; hiện Industry tuple bảo toàn description raw.

### 5.1 Fact: keys, observations và technical fields

| Source Attribute | Transformation | Target Table | Target Attribute | Role |
|---|---|---|---|---|
| File+record occurrence | Sinh surrogate khác nhau cho mỗi occurrence | FactLoanSnapshot | LoanSnapshotKey | PK kỹ thuật, không LoanID |
| ApprovalDate | Parse, lookup FullDate/special member | FactLoanSnapshot | ApprovalDateKey | Date FK |
| FirstDisbursementDate | Parse/lookup; missing key 0 | FactLoanSnapshot | FirstDisbursementDateKey | Date FK |
| PaidInFullDate | Parse/lookup actual date; audit sequence/status | FactLoanSnapshot | PaidInFullDateKey | Date FK |
| ChargeOffDate | Parse/lookup actual date; audit future/missing | FactLoanSnapshot | ChargeOffDateKey | Date FK |
| AsOfDate | Parse/lookup, kiểm snapshot thống nhất | FactLoanSnapshot | AsOfDateKey | Date FK |
| ProjectState,ProjectCounty,CongressionalDistrict,SBADistrictOffice | Lookup full null-safe tuple | FactLoanSnapshot | GeographyKey | FK |
| NaicsCode,NaicsDescription | Lookup cặp nguồn, không code-only | FactLoanSnapshot | IndustryKey | FK |
| LocationID | Lookup BK đã kiểm FD | FactLoanSnapshot | LenderKey | FK |
| BusinessType,BusinessAge | Lookup tuple gồm Missing nếu cần | FactLoanSnapshot | BusinessKey | FK |
| ProcessingMethod,FixedorVariableInterestInd,RevolverStatus,CollateralInd,GrossApproval,TermInMonths + band rule | Derive bands sau duyệt, lookup tuple+version | FactLoanSnapshot | LoanCharacteristicsKey | FK |
| LoanStatus | Lookup raw label | FactLoanSnapshot | LoanStatusKey | FK |
| GrossApproval | Parse decimal, giữ giá trị nguồn | FactLoanSnapshot | GrossApproval | Stored measure |
| SBAGuaranteedApproval | Parse decimal | FactLoanSnapshot | SBAGuaranteedApproval | Stored measure |
| GrossChargeOffAmount | Parse decimal, không tự đặt 0 theo status | FactLoanSnapshot | GrossChargeOffAmount | Stored measure, K13 filter ở semantic |
| JobsSupported | Parse numeric, kiểm nguyên trước integer | FactLoanSnapshot | JobsSupported | Stored reported measure |
| Record occurrence | Hằng 1 | FactLoanSnapshot | RecordCount | Stored count component |
| TermInMonths | Parse/kiểm nguyên, giữ 0 | FactLoanSnapshot | TermInMonths | Non-additive observation |
| InitialInterestRate | Parse decimal nullable, chưa scale /100 | FactLoanSnapshot | InitialInterestRate | Non-additive observation |
| Ingestion file registry/checksum | Lookup file identity bất biến | FactLoanSnapshot | SourceFileID | Lineage |
| Parser ordinal | Đếm record dữ liệu 1..N, không đếm newline | FactLoanSnapshot | SourceRecordOrdinal | Lineage/unique source identity |
| Parser physical position | Dòng bắt đầu sau header, ghi actual line | FactLoanSnapshot | SourceRowNumber | Lineage |
| Ingestion batch registry | Gán batch hiện tại | FactLoanSnapshot | ETLBatchID | Audit reference |

### 5.2 Dimension attributes và keys

| Source Attribute | Transformation | Target Table | Target Attribute | Role |
|---|---|---|---|---|
| Calendar date domain | YYYYMMDD cho ngày thực; reserved 0/-1 | DimDate | DateKey | PK |
| Date domain + missing/parse state | Một ngày hoặc NULL với special member | DimDate | FullDate, DateMemberType | BK thật/special label |
| FullDate | year, ceil(month/3), month, month name; NULL special | DimDate | CalendarYear, CalendarQuarter, CalendarMonth, MonthName | Calendar attributes |
| FullDate | FY bắt đầu 10; công thức dimension design | DimDate | FiscalYear, FiscalQuarter, FiscalMonth | Derived hierarchy |
| Geography tuple | Sinh surrogate theo tuple duy nhất | DimProjectGeography | GeographyKey | PK |
| ProjectState | Giữ mã text, chỉ normalize khi policy duyệt | DimProjectGeography | ProjectState | Business attribute |
| ProjectCounty | Giữ label, key luôn ghép state | DimProjectGeography | ProjectCounty | Business attribute |
| CongressionalDistrict | Giữ text/leading zero, missing riêng | DimProjectGeography | CongressionalDistrict | Business attribute |
| SBADistrictOffice | Giữ source label | DimProjectGeography | SBADistrictOffice | Independent attribute |
| NAICS code+description tuple | Sinh surrogate theo cặp raw | DimIndustry | IndustryKey | PK |
| NaicsCode | Giữ text 6 chữ số; kiểm không chứng minh version | DimIndustry | NaicsCode | Grouping identifier, một phần BK |
| NaicsDescription | Giữ raw variants, không chọn first canonical | DimIndustry | NaicsDescription | Description, một phần BK |
| NaicsCode + verified reference | Lookup sector, xử lý ranges; chưa reference → NULL | DimIndustry | NaicsSectorCode | Derived, CORE conditional |
| Sector reference | Tên theo đúng version; chưa reference → NULL | DimIndustry | NaicsSectorName | Reference label, DEFERRED |
| Reference/evidence registry | Ghi version khi chứng minh, status UNVERIFIED/VERIFIED/Ambiguous | DimIndustry | NaicsVersion, SectorMappingStatus | Mapping control |
| LocationID | Sinh surrogate, kiểm một BK→một bank tuple | DimLender | LenderKey | PK |
| LocationID | Giữ text/leading zeros | DimLender | LocationID | BK |
| BankName | Giữ lender hiện được gán, không unique name | DimLender | BankName | Display attribute |
| BankFDICNumber, BankNCUANumber | Giữ text, NULL không tự lỗi | DimLender | BankFDICNumber, BankNCUANumber | Secondary identifiers |
| BankStreet, BankCity, BankState, BankZip | Giữ source fields tương ứng, ZIP text | DimLender | BankStreet, BankCity, BankState, BankZip | Address attributes |
| BusinessType+BusinessAge | Sinh surrogate tuple null-safe | DimBusiness | BusinessKey | PK |
| BusinessType | Giữ raw label hoặc missing | DimBusiness | BusinessType | Business attribute |
| BusinessAge | Giữ raw label; Unanswered khác NULL | DimBusiness | BusinessAge | Business attribute |
| Characteristics tuple+bands/version | Sinh surrogate theo tổ hợp xuất hiện | DimLoanCharacteristics | LoanCharacteristicsKey | PK |
| ProcessingMethod | Giữ 19 raw labels; không ép 18 mã workbook | DimLoanCharacteristics | ProcessingMethod | Business attribute |
| FixedorVariableInterestInd | Giữ F/V raw/Missing, chưa diễn giải mã | DimLoanCharacteristics | FixedorVariableInterestInd | Business attribute |
| RevolverStatus, CollateralInd | Giữ raw Y/N; không tự mapping 0/1 | DimLoanCharacteristics | RevolverStatus, CollateralInd | Supporting attributes |
| GrossApproval + band reference | Ngưỡng §7 dimension design sau BR13 approved | DimLoanCharacteristics | LoanSizeBand, LoanSizeBandSort | Derived classification/order |
| TermInMonths + band reference | Ngưỡng §7; 0/Missing/Invalid riêng | DimLoanCharacteristics | TermBand, TermBandSort | Derived classification/order |
| Band rule registry | Ghi đúng phiên bản đã dùng, hiện draft PROPOSED-v1 | DimLoanCharacteristics | BandRuleVersion | Reproducibility |
| LoanStatus raw | Sinh surrogate theo raw label | DimLoanStatus | LoanStatusKey | PK |
| LoanStatus | Giữ raw, gồm P I F | DimLoanStatus | LoanStatusRaw | BK |
| Raw status + approved mapping | Literal khớp workbook giữ code; P I F chưa duyệt → NULL/OPEN | DimLoanStatus | LoanStatusCanonicalCode, StatusMappingStatus | Controlled mapping |

### 5.3 Calculated và audit ngoài star

| Source Attribute | Transformation | Target Table/layer | Target Attribute | Role |
|---|---|---|---|---|
| GrossApproval,SBAGuaranteedApproval | Hiệu hai SUM cùng tập | Semantic layer | NonSBAGuaranteedApproval / K07 | Calculated measure |
| ApprovalDate,cutoff,FY | Fiscal window động | Semantic layer | FiscalYTDFlag (predicate) | K04 logic, không stored boolean |
| ApprovalDate,AsOfDate | Chênh ngày hợp lệ | Query | LoanAgeAtSnapshot | OPTIONAL |
| ApprovalDate,FirstDisbursementDate | Difference hợp lệ | Query mở rộng | ApprovalToFirstDisbursementDays | DEFERRED |
| File registry | ID nội bộ gắn checksum | Audit file | SourceFileID | Lineage registry |
| Tên/path và byte file | Lưu tên/path, SHA-256 byte | Audit file | SourceFileName, SourceFileSHA256 | Required lineage |
| Parser record position | Ordinal, start/end physical line | Audit record | SourceRecordOrdinal, SourceRowNumber, SourceRowEndNumber | Trace multiline |
| 42 raw strings theo header order | SHA-256 canonical JSON array UTF-8 không trim, policy draft | Audit record | SourceRowHash | OPTIONAL, không unique |
| Batch registry/clock | Batch ID, timestamp UTC | Audit batch | ETLBatchID, ETLLoadTimestamp | Load audit |
| DQ rules kết quả từng record | Nhiều issue codes+details; không loại tự động | Audit issues | DataQualityFlag (tập issue) | CORE audit requirement |
| Program,ApprovalFY | Giữ raw và đối soát program/FY, không ép mapping | Staging/audit file hoặc record | ProgramRaw, ApprovalFYRaw | Ngoài core star |
| Borr*,FranchiseCode/Name,SoldSecMrktInd | Giữ nguyên, truy qua file+ordinal | Raw/staging | Tên nguồn tương ứng | Retained, không core Dimension |

Địa chỉ/path audit nếu triển khai cần tên cột/kiểu chi tiết trong mapping đầy đủ; không thêm vào Mermaid như dimension phân tích. Mapping logic phải bảo toàn số dòng, nullable và độ chính xác, không chạy source cleaning trong task này.

## 6. Rules còn mở và điều kiện nghiệm thu thiết kế

| Rule/decision | Hiện trạng | Cần giải quyết trước thực thi |
|---|---|---|
| BR03 | PROPOSED | Duyệt population mọi status cho vốn, nhãn riêng khi loại CANCLD |
| BR04 | PROPOSED | Duyệt fiscal derivation/FYTD cùng cutoff, FY2020 không năm trước |
| BR06 | OPEN | Evidence mapping P I F→PIF, giữ raw và canonical riêng |
| BR07 | OPEN | Reference/version NAICS cho source codes; xử lý mã đa nghĩa/description variants; xác minh sector ranges/names |
| BR09 | OPEN | Zero/missing/Unanswered, rate 0, term 0 riêng |
| BR10 | PROPOSED | CHGOFF filter và giữ amount trong cohort dù ngày lỗi; event-date validity riêng |
| BR11 | PROPOSED | Ratio-of-sums, parent filters, NULL/0 denominator, một snapshot |
| BR13 | OPEN | Duyệt ngưỡng/project grouping và phiên bản; xác nhận đơn vị amount |
| BR14 | OPEN | Đơn vị rate, F/V, 0/NULL; K11 không trọng số, chưa ký hiệu % |
| BR15 | PROPOSED | Raw labels cho method/age, geography branch keys, chưa canonicalize tự động |
| Technical bổ sung | Đề xuất trong task | CSV multiline parser, file checksum/ordinal idempotency, lookup one-to-one, audit issues không nhân fact |
| Nguồn tài chính | Catalog còn thận trọng về đơn vị | Xác nhận đơn vị amount trước nhãn báo cáo chính thức |

Không còn thiếu analytical table để viết **bản mapping đầy đủ và cleaning rules dự thảo**. Nhưng còn thiếu phê duyệt/evidence để đóng các rules trên; không gọi đây là ETL-ready. Trước nạp cần kiểm reconciliations mô tả ở Fact design, kiểm boundary bands và group totals, triển khai role-playing date/parent filters đúng engine. Những checks này là kế hoạch nghiệm thu, không kết quả chạy database.
