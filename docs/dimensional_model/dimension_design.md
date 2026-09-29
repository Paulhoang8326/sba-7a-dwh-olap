# Thiết kế các Dimension

PROPOSED, 2026-09-28. Bảy bảng logic, không DDL/ETL. Căn cứ [OLAP requirements](../business_requirements/olap_analysis_requirements.md), [derived requirements](../business_requirements/derived_attribute_requirements.md), [profiling](../data_understanding/data_profiling_report.md), [kiểm tra trực tiếp](dimensional_model_proposal.md#2-kiểm-tra-trực-tiếp-phục-vụ-thiết-kế).

## 1. Quy ước chung

Surrogate key độc lập business key (BK), không tạo định danh loan/borrower. Một fact FK phải lookup đúng một member. Null-safe tuple comparison dùng token kỹ thuật phân biệt NULL với chuỗi thật; không ghép chuỗi có delimiter mơ hồ. Missing hiển thị riêng, không tự đổi thành giá trị nghiệp vụ. Raw luôn giữ ở staging. Dim attribute có thể NULL khi thiếu; Fact FK trỏ member hợp lệ, không mất dòng vì INNER JOIN.

Đề xuất member key 0=Unknown cho dimension khi cả tuple không xác định; tuple chỉ thiếu một thuộc tính vẫn giữ phần đã biết, không đẩy cả record vào Unknown. Không nhầm missing BusinessAge với literal Unanswered. Toàn bộ dimensions là phiên bản mô tả trong snapshot này, full rebuild có kiểm soát; không suy SCD2/lịch sử từ một file. Thay mapping/band sau phê duyệt phải reprocess dimension/FK đồng bộ và audit phiên bản. Không giả định key tự sinh giữ nguyên qua rebuild.

## 2. DimDate

| Thành phần | Thiết kế |
|---|---|
| Purpose | Trục approval cohort, fiscal drill-down/FYTD; ngày snapshot và các mốc sự kiện |
| Grain | Một ngày lịch thực; thêm special members ngoài tập ngày |
| Primary Key | DateKey: integer; có thể YYYYMMDD với ngày thực, 0 Missing/Unknown, -1 Invalid/unparseable |
| Business Key | FullDate cho ngày thực; DateMemberType phân biệt special members FullDate=NULL |
| Important Attributes | FullDate, CalendarYear, CalendarQuarter, CalendarMonth, MonthName, DateMemberType |
| Derived Attributes | FiscalYear, FiscalQuarter, FiscalMonth; calendar attributes cũng được sinh từ FullDate |
| Related BQ | Tất cả 19 BQ; BQ01/BQ03 cần fiscal drill/FYTD, BQ20–23 cần approval cohort và AsOfDate |
| Related KPI | K01–K13 theo thời gian, K04 bắt buộc fiscal window |

Một bảng dùng năm vai trò: ApprovalDate, FirstDisbursementDate, PaidInFullDate, ChargeOffDate, AsOfDate; năm FK trong Fact. Semantic layer đặt tên role rõ, Approval Date là default cohort; các event roles chỉ dùng khi chọn có chủ đích. Không nối cả năm khóa qua cùng một alias SQL làm mất dòng, không đặt nhiều active date paths nhập nhằng.

FY SBA bắt đầu **01/10**, kết thúc **30/09**. FiscalYear=year(d)+1 nếu month≥10, ngược lại year(d). FiscalMonth=((month(d)+2) mod 12)+1. FiscalQuarter=floor((FiscalMonth−1)/3)+1. Q1=10–12, Q2=01–03, Q3=04–06, Q4=07–09. MonthName là nhãn tháng dương lịch, sắp theo CalendarMonth hoặc FiscalMonth tùy hierarchy.

Hierarchy 1: FiscalYear → (FiscalYear,FiscalQuarter) → (FiscalYear,FiscalMonth) → FullDate.
Hierarchy 2: CalendarYear → (CalendarYear,CalendarQuarter) → (CalendarYear,CalendarMonth) → FullDate.
Các tuple trên là OLAP level keys, không bắt buộc cột vật lý mới. Không dùng “Q1” hoặc “January” đơn lẻ làm khóa level xuyên năm.

Date range phải bao phủ mọi ngày parse được, ít nhất 2019-10-01–2026-07-01 ở nguồn hiện tại, có thể sinh trọn các năm liên quan. 2026-07-01 tồn tại trong dim để bảo toàn ngày nguồn bất thường, **không** có nghĩa được nhận vào phân tích event hợp lệ. Special member có fiscal/calendar fields NULL, không gán năm 1900. Missing event date không tự suy “not applicable”: lý do thiếu được xét cùng status và audit, không impute ngày.

## 3. DimProjectGeography

| Thành phần | Thiết kế |
|---|---|
| Purpose | Phân tích địa điểm **dự án**, khác borrower/bank |
| Grain | Một tổ hợp quan sát (ProjectState,ProjectCounty,CongressionalDistrict,SBADistrictOffice) |
| Primary Key | GeographyKey |
| Business Key | Null-safe tuple bốn thuộc tính; đây là combination key, không mã hành chính chính thức |
| Important Attributes | ProjectState, ProjectCounty, CongressionalDistrict, SBADistrictOffice dạng text |
| Derived Attributes | Không thêm tên state/FIPS chưa có reference; composite level keys tạo trong OLAP |
| Related BQ | BQ01–03,07,10–12,14,15/17 slicer,21–22 |
| Related KPI | K01–K05,K08–K10,K12,K13 khi slice geography |

4.848 tổ hợp raw trong kiểm tra hiện tại. Nếu một county xuất hiện ở nhiều district/office thì có nhiều geography members, mỗi fact vẫn đúng một member. Group theo State+County cộng mọi members tương ứng, không join riêng theo county gây fan-out.

Hierarchy độc lập:
- ProjectState → (ProjectState,ProjectCounty).
- ProjectState → (ProjectState,CongressionalDistrict).
- SBADistrictOffice là attribute axis độc lập; chưa khẳng định office thuộc đúng một state hoặc county.

Không State → County → CongressionalDistrict; ranh giới county/district có thể giao nhau. Mã district giữ số 0 đầu. Thiếu 24 district giữ Missing thuộc state/county đã biết. Không suy ranh giới theo năm election hoặc tạo history boundary từ nguồn này.

## 4. DimIndustry

| Thành phần | Thiết kế |
|---|---|
| Purpose | Phân tích ngành theo mã nguồn và dự phòng roll-up sector có kiểm soát |
| Grain | Một cặp (NaicsCode,NaicsDescription) **nguồn** trong snapshot; chưa canonicalize description |
| Primary Key | IndustryKey |
| Business Key | Null-safe tuple (NaicsCode,NaicsDescription); NaicsCode là business grouping identifier nhưng chưa là unique row key |
| Important Attributes | NaicsCode, NaicsDescription |
| Derived/reference Attributes | NaicsSectorCode, NaicsSectorName, NaicsVersion, SectorMappingStatus |
| Related BQ | BQ07,12,14,21,22 |
| Related KPI | K01,K02,K05,K08,K09,K10,K12,K13 |

Kiểm tra raw có 1.157 mã và 1.795 cặp code/description; 14 mã vẫn nhiều descriptions sau trim chẩn đoán. Giữ các biến thể để không tự chọn tên, dùng code làm level grouping của BQ. Nếu pivot theo code không được ép description thành thuộc tính một-một; hiển thị code hoặc drill xuống biến thể mô tả. Phải lookup **cặp đầy đủ** từ Fact, không join code với nhiều dim rows.

NaicsSectorCode cần reference NAICS có nguồn/phiên bản phù hợp **cho các mã trong CSV**. Chỉ biết mã 6 chữ số không xác minh version; không tự chọn 2017/2022 hoặc dùng ApprovalFY để đoán. Mapping phải xử lý sector gộp, không dùng prefix 2 chữ số làm mã sector chính thức một cách máy móc. Một mã chỉ nhận một sector theo rule được duyệt trong snapshot; nếu ambiguous, giữ Unmapped/Ambiguous và audit, không nhân Fact.

Trước reference: NaicsSectorCode/Name/Version=NULL, SectorMappingStatus=UNVERIFIED; group Unmapped có thể hiển thị nhưng **không tuyên bố trả lời BQ12 roll-up sector hoàn chỉnh**. Sau xác minh: status VERIFIED, version/reference provenance ở audit; code → sector mapping dùng thống nhất cho mọi description variant. Hierarchy điều kiện: sector → NAICS code → source-description member. Name là nhãn của sector đã xác minh, không lấy NaicsDescription cấp 6 chữ số làm sector name. Bảng reference phục vụ mapping, không thêm snowflake Dimension.

## 5. DimLender

| Thành phần | Thiết kế |
|---|---|
| Purpose | Phân tích lender hiện được gán hồ sơ |
| Grain | Một LocationID trong snapshot đã kiểm FD với thuộc tính bank |
| Primary Key | LenderKey |
| Business Key | LocationID dạng text, giữ số 0 đầu |
| Important Attributes | LocationID, BankName, BankFDICNumber, BankNCUANumber, BankStreet, BankCity, BankState, BankZip |
| Derived Attributes | Không cần derived core |
| Related BQ | BQ08, BQ15 |
| Related KPI | K01,K02,K05,K07 |

Workbook xác nhận LocationID là SBA lender ID, BankName là currently assigned lender. 2.338 LocationID, không ID nào có nhiều tổ hợp bảy bank fields trong raw snapshot. Đây là bằng chứng BK phù hợp **trong file này**, không chứng minh định danh lender luôn bất biến trong tương lai. BankName chỉ có 2.183 giá trị và có thể dùng chung/đổi tên, không làm BK. FDIC/NCUA là mã phụ thiếu theo loại lender, không thay LocationID.

BankState → (BankState,BankCity) → LocationID chỉ là hierarchy địa chỉ nếu FD đã kiểm; không tổ chức mẹ–con. BankZip/FDIC/NCUA là text, không measure. Snapshot mới có xung đột LocationID→attributes phải giải quyết/version trước lookup, không lấy FIRST/MAX ngẫu nhiên. Không áp lịch sử lender phê duyệt từ lender hiện tại.

## 6. DimBusiness

| Thành phần | Thiết kế |
|---|---|
| Purpose | Profile phân loại doanh nghiệp cho BQ04/BQ17, không định danh borrower |
| Grain | Một tổ hợp (BusinessType,BusinessAge) null-safe |
| Primary Key | BusinessKey |
| Business Key | Tuple (BusinessType,BusinessAge); không borrower ID |
| Important Attributes | BusinessType, BusinessAge raw labels |
| Derived Attributes | Không core; Missing là cách biểu diễn thiếu, không nhóm tuổi suy diễn |
| Related BQ | BQ04, BQ17 |
| Related KPI | K01,K02,K05 |

22 tổ hợp raw cho thấy dimension nhỏ và dễ hiểu. Type và age là hai trục song song, không hierarchy type→age. Giữ BusinessAge=Unanswered khác NULL; BusinessType thiếu không mặc định CORPORATION. FranchiseCode/Name và Borr* giữ raw/staging, có thể mở rộng khi có BQ và khóa/policy phù hợp. Không cần surrogate borrower entity chỉ vì tên có cardinality cao.

## 7. DimLoanCharacteristics

| Thành phần | Thiết kế |
|---|---|
| Purpose | Slice method, rate type, quy mô và kỳ hạn; một dimension kết hợp các phân loại thấp cardinality |
| Grain | Một tổ hợp method/rate type/revolver/collateral/size band/term band/BandRuleVersion xuất hiện |
| Primary Key | LoanCharacteristicsKey |
| Business Key | Tuple (ProcessingMethod,FixedorVariableInterestInd,RevolverStatus,CollateralInd,LoanSizeBand,TermBand,BandRuleVersion) |
| Important Attributes | ProcessingMethod, FixedorVariableInterestInd, RevolverStatus, CollateralInd |
| Derived Attributes | LoanSizeBand, LoanSizeBandSort, TermBand, TermBandSort, BandRuleVersion |
| Related BQ | BQ02,04,06,08,16,18,20,23 |
| Related KPI | K01,K02,K03,K05,K06,K07,K11,K12 |

521 tổ hợp raw với bands đề xuất, chưa là final cleaned cardinality. Không tạo Cartesian product mọi giá trị. Sort là thuộc tính phụ thuộc band; không phải phần BK. Không đưa numeric rate/term chính xác vào tuple. Giữ mã F/V,Y/N,19 method labels raw đến khi mapping được duyệt; 18 method codes workbook không tự bao phủ 19 labels.

Không hierarchy method→band→rate type; đó là các trục chéo dùng pivot. Program chỉ một giá trị, không DimLoanProgram riêng. Không thêm SoldSecMrktInd vì ngoài 19 BQ. Revolver/collateral là thuộc tính bổ trợ nhỏ, chưa mở scope KPI.

### LoanSizeBand

Mục đích: BQ04 cơ cấu vốn/count (K01,K02,K05), BQ18 phân khúc rate (K11), BQ23 outcome theo size (K12). GrossApproval liên tục không cung cấp nhãn band dùng chung.

| Phương án | Ưu/nhược |
|---|---|
| Ba nhóm: (0,150k],(150k,1m],(1m,+∞) | Rất đơn giản, nhưng che khuất phân bố nhỏ/trung bình |
| Năm nhóm: (0,50k],(50k,150k],(150k,500k],(500k,1m],(1m,+∞) | Đọc được và phân tách quanh Q1=52k, median=195k, Q3=500k; ổn định giữa FY |
| Quantiles theo từng FY | Cân bằng count nhưng ngưỡng thay đổi, không so cùng size giữa FY; ties khó chia |

**Chọn đề xuất năm nhóm cố định — Project-defined analytical grouping**, không chuẩn SBA. Đơn vị số tiền nguồn, dự kiến USD còn chờ xác nhận catalog.

| LoanSizeBand | Điều kiện G | Sort | Count kiểm trực tiếp |
|---|---|---|---|
| S1: 0–50k | 0 < G ≤ 50.000 | 1 | 96.083 |
| S2: 50k–150k | 50.000 < G ≤ 150.000 | 2 | 88.206 |
| S3: 150k–500k | 150.000 < G ≤ 500.000 | 3 | 107.312 |
| S4: 500k–1m | 500.000 < G ≤ 1.000.000 | 4 | 42.315 |
| S5: trên 1m | G > 1.000.000, không cap ngầm ở 5m | 5 | 54.422 |
| ZeroUnverified | G=0 | 90 | 0 |
| Missing | G=NULL | 91 | 0 |
| Invalid | G<0 hoặc parse fail | 92 | 0 |

Tổng năm nhóm=388.338. Đây là chẩn đoán trong bộ nhớ, chưa gán/lưu band vào dữ liệu. BandRuleVersion=`PROPOSED-v1` trong thiết kế; chỉ activate sau duyệt BR13. Số quan sát phân bố đủ rộng là lý do chọn, không bằng chứng ngưỡng chính thức.

### TermBand

Mục đích BQ16/K01,K02,K05; source TermInMonths là số tháng không có phân loại ngắn/trung/dài thống nhất. Phương án ≤12/13–60/>60 quá dồn nhóm dài khi median=120; phương án ≤60/61–120/>120 phù hợp mô tả hơn; quantile bands kém ổn định vì Q1=median=Q3=120.

**Chọn đề xuất 60/120 tháng — Project-defined analytical grouping**, không chuẩn SBA và không kỳ hạn trả thực tế.

| TermBand | Điều kiện T | Sort | Count kiểm trực tiếp |
|---|---|---|---|
| Short: đến 60 tháng | 0 < T ≤ 60 | 1 | 32.801 |
| Medium: trên 60 đến 120 | 60 < T ≤ 120 | 2 | 276.222 |
| Long: trên 120 | T > 120 | 3 | 79.304 |
| ZeroUnverified | T=0 | 90 | 11 |
| Missing | T=NULL | 91 | 0 |
| Invalid | T<0/không nguyên/parse fail | 92 | 0 theo profile hiện tại |

Giữ 11 dòng 0 riêng, không short-term. Missing/Invalid/ZeroUnverified khác nhau. Nếu ngưỡng chưa duyệt, band phải được gắn trạng thái chưa áp dụng trong staging/mapping draft; không coi thiết kế này đã cleaning dữ liệu.

## 8. DimLoanStatus

| Thành phần | Thiết kế |
|---|---|
| Purpose | Slice cơ cấu trạng thái, quản lý mapping và mẫu số mọi status |
| Grain | Một nhãn LoanStatus nguồn |
| Primary Key | LoanStatusKey |
| Business Key | LoanStatusRaw |
| Important Attributes | LoanStatusRaw |
| Derived/reference Attributes | LoanStatusCanonicalCode nullable, StatusMappingStatus |
| Related BQ | BQ20,BQ21,BQ22,BQ23; các BQ vốn khi filter status |
| Related KPI | K01,K12,K13; K02/K06/K07 theo population |

Raw members: EXEMPT, `P I F`, CANCLD, COMMIT, CHGOFF. Không hierarchy trạng thái tiến triển và không suy EXEMPT là performing. Với literal đã khớp workbook có thể canonical code giống raw, status VERIFIED; `P I F` canonical=NULL, status OPEN cho tới BR06 được duyệt. Khi duyệt mapping, `P I F → PIF` chỉ thay canonical attribute có audit, giữ raw nguyên vẹn; không sửa CSV. K12 BQ23 trước đó lọc LoanStatusRaw=`P I F`, không lọc canonical=NULL.

So với status trực tiếp Fact: riêng dimension giảm lặp, dùng cùng nhãn/mapping tập trung, dễ expose member và total mọi status. Không lưu thêm status trong Characteristics; không lưu outcome count flags dư trong Fact vì RecordCount+Status đủ.

## 9. Nguồn–đích và thay đổi sau này

[Mapping sơ bộ đầy đủ các thuộc tính schema](schema_coverage.md#5-source-to-target-mapping-sơ-bộ) bao phủ keys/technical/derived. Band version/reference provenance thuộc hợp đồng mapping, không tự chứng minh schema đã triển khai. Nếu scope mở rộng nhiều snapshots/SCD/borrower entity thì review grain, BK và sự phụ thuộc thuộc tính trước, không nối bằng fact PK.
