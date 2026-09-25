# Data Dictionary – SBA 7(a)

Nguồn định nghĩa: workbook SBA `7a_504_foia_data_dictionary.xlsx`, sheet `7(a) Data Dictionary`. Diễn giải tiếng Việt dưới đây dựa trên định nghĩa gốc; các nhãn chưa được workbook giải mã đều ghi cần xác minh. CSV lưu mọi ô dưới dạng text; `Data Type` ghi kiểu hiện tại / kiểu ngữ nghĩa.

| STT | Attribute | Description | Data Type | Example Value | Business Meaning | Notes |
|---|---|---|---|---|---|---|
| 1 | AsOfDate | Ngày ghi nhận snapshot | text / date | 2026-06-30 | Mốc quan sát trạng thái và số liệu công bố. | Một snapshot, không phải lịch sử trạng thái. |
| 2 | Program | Chương trình SBA | text / category/text |  7A | Chỉ báo chương trình 7(a) hoặc 504 của hồ sơ. | CSV này thuộc 7(a); xác minh biểu diễn giá trị thực tế. |
| 3 | LocationID | Mã định danh lender SBA | text / code | 0029805 | Mã lender duy nhất theo SBA. | Không phải mã khoản vay; giữ số 0 đầu. |
| 4 | BorrName | Tên người vay/doanh nghiệp vay | text / category/text | AMERIPRO CONSTRUCTION SERVICES, INC. | Tên chủ thể đi vay. | Không chứng minh tính duy nhất của khoản vay. |
| 5 | BorrStreet | Đường/địa chỉ người vay | text / category/text | 1403 SENTRY LANE | Địa chỉ đường của người vay. | Có thể là thông tin nhận dạng cá nhân. |
| 6 | BorrCity | Thành phố người vay | text / category/text | Norristown | Thành phố trong địa chỉ người vay. | Không đồng nhất với địa điểm dự án. |
| 7 | BorrState | Bang người vay | text / category/text | PA | Bang trong địa chỉ người vay. | Khác ProjectState. |
| 8 | BorrZip | ZIP người vay | text / code | 19403 | Mã bưu chính trong địa chỉ người vay. | Mã định danh dạng chuỗi; giữ số 0 đầu. |
| 9 | BankName | Tên lender hiện được gán khoản vay | text / category/text | TD Bank, National Association | Tổ chức cho vay hiện được gán khoản vay. | Nguồn nói currently assigned; không mặc định lender ban đầu. |
| 10 | BankFDICNumber | Mã chứng nhận FDIC | text / code | 18409 | Mã chứng nhận FDIC của lender. | Có thể không áp dụng với mọi loại lender. |
| 11 | BankNCUANumber | Mã charter NCUA | text / code | 67390 | Mã charter NCUA của lender. | Có thể không áp dụng với mọi loại lender. |
| 12 | BankStreet | Đường/địa chỉ lender | text / category/text | 2035 Limestone Rd | Địa chỉ đường của lender. |  |
| 13 | BankCity | Thành phố lender | text / category/text | WILMINGTON | Thành phố trong địa chỉ lender. |  |
| 14 | BankState | Bang lender | text / category/text | DE | Bang trong địa chỉ lender. | Khác ProjectState và BorrState. |
| 15 | BankZip | ZIP lender | text / code | 19808 | Mã bưu chính lender. | Giữ số 0 đầu. |
| 16 | GrossApproval | Tổng số tiền vay được phê duyệt | text / decimal | 25000.0 | Quy mô khoản vay tại phê duyệt. | Không phải dư nợ hiện tại; đơn vị USD cần xác minh theo nguồn phát hành. |
| 17 | SBAGuaranteedApproval | Số tiền SBA bảo lãnh khi phê duyệt | text / decimal | 12500.0 | Phần khoản vay được SBA bảo lãnh. | Không phải khoản SBA đã chi trả. |
| 18 | ApprovalDate | Ngày phê duyệt | text / date | 2019-10-01 | Ngày khoản vay được phê duyệt. | FY bắt đầu tháng 10; đối chiếu ApprovalFY. |
| 19 | ApprovalFY | Năm tài chính phê duyệt | text / integer FY | 2020 | FY của phê duyệt khoản vay. | Trong CSV là chuỗi; ngữ nghĩa là năm tài chính số nguyên. |
| 20 | FirstDisbursementDate | Ngày giải ngân đầu tiên | text / date | 2019-10-31 | Lần giải ngân đầu tiên nếu có. | Thiếu có thể phản ánh chưa giải ngân hoặc nguồn không cung cấp. |
| 21 | ProcessingMethod | Phương thức xử lý/phê duyệt | text / category/text | SBA Express Program | Hình thức xử lý khoản vay theo chương trình 7(a). | Workbook liệt kê các mã phương thức; CSV có thể dùng nhãn thay mã. |
| 22 | InitialInterestRate | Lãi suất ban đầu | text / decimal | 11.04 | Lãi suất tổng (base rate + spread) tại lúc phê duyệt. | Đơn vị biểu diễn cần đối chiếu; không phải lãi suất hiện tại. |
| 23 | FixedorVariableInterestInd | Chỉ báo lãi suất cố định/biến đổi | text / category/text | V | Kiểu lãi suất tại phê duyệt. | Ý nghĩa mã cụ thể cần xác minh nếu workbook không nêu. |
| 24 | TermInMonths | Thời hạn vay (tháng) | text / integer count | 120.0 | Độ dài kỳ hạn khoản vay. | CSV là số thập phân; ngữ nghĩa số tháng. |
| 25 | NaicsCode | Mã NAICS | text / code | 236220 | Mã ngành kinh tế Bắc Mỹ. | Dạng chuỗi; không coi là đại lượng số. |
| 26 | NaicsDescription | Mô tả NAICS | text / category/text | Commercial and Institutional Building Construction  | Tên/mô tả ngành theo NAICS. | Có thể chứa khoảng trắng cuối. |
| 27 | FranchiseCode | Mã franchise | text / code | S2561 | Mã franchise nếu áp dụng. | Thiếu có thể là không áp dụng; cần xác minh. |
| 28 | FranchiseName | Tên franchise | text / category/text | Poke Burri | Tên franchise nếu áp dụng. | Thiếu có thể là không áp dụng; cần xác minh. |
| 29 | ProjectCounty | Quận/hạt dự án | text / category/text | MONTGOMERY | County nơi dự án diễn ra. |  |
| 30 | ProjectState | Bang dự án | text / category/text | PA | Bang nơi dự án diễn ra. |  |
| 31 | SBADistrictOffice | Văn phòng khu vực SBA | text / category/text | PHILADELPHIA DISTRICT OFFICE | SBA district office liên quan hồ sơ. | Vai trò chính xác trong quy trình cần xác minh. |
| 32 | CongressionalDistrict | Địa hạt quốc hội dự án | text / code | 04 | Congressional district nơi dự án diễn ra. | Giữ số 0 đầu; phụ thuộc ProjectState. |
| 33 | BusinessType | Loại hình người vay | text / category/text | PARTNERSHIP | Individual, Partnership hoặc Corporation theo workbook. | Các nhãn khác trong CSV cần xác minh. |
| 34 | BusinessAge | Nhóm tuổi đời doanh nghiệp | text / category/text | Unanswered | Phân loại tuổi đời doanh nghiệp. | Workbook không giải thích từng nhãn; cần xác minh. |
| 35 | LoanStatus | Trạng thái khoản vay tại snapshot | text / category/text | P I F | Trạng thái hiện tại của hồ sơ vay. | CANCLD=Cancelled; CHGOFF=Charged Off; COMMIT=Undisbursed; EXEMPT=đã giải ngân và chưa hủy/PIF/charge-off; workbook ghi PIF=Paid In Full nhưng CSV dùng nhãn P I F. |
| 36 | PaidInFullDate | Ngày trả hết nợ | text / date | 2024-11-30 | Ngày khoản vay đã được thanh toán đủ nếu áp dụng. | Thiếu hợp lệ khi chưa PIF. |
| 37 | ChargeOffDate | Ngày SBA charge-off | text / date | 2021-06-25 | Ngày SBA ghi nhận charge-off nếu áp dụng. | Thiếu hợp lệ khi chưa charge-off. |
| 38 | GrossChargeOffAmount | Tổng số dư đã charge-off | text / decimal | 0.0 | Bao gồm phần được và không được bảo lãnh. | Không phải tổn thất ròng sau thu hồi. |
| 39 | RevolverStatus | Chỉ báo khoản vay quay vòng | text / category/text | Y | 0=term loan, 1=revolving line of credit theo workbook. | CSV có thể dùng Y/N; cần xác minh mapping Y/N với 0/1. |
| 40 | JobsSupported | Số việc làm được hỗ trợ | text / integer count | 5.0 | Jobs Created + Jobs Retained do lender báo trong đơn vay. | SBA không audit/xác minh; không phải số việc làm thực tế độc lập. |
| 41 | CollateralInd | Chỉ báo tài sản bảo đảm | text / category/text | N | Lender báo khoản vay có tài sản bảo đảm hay không. | Ý nghĩa nhãn mã cần xác minh nếu workbook không nêu. |
| 42 | SoldSecMrktInd | Chỉ báo bán thị trường thứ cấp | text / category/text | Y | Y nếu khoản vay đã được bán trên thị trường thứ cấp. | Nguồn nêu Y là trạng thái tĩnh sau khi bán; blank không tự suy ra N. |

## Mã ProcessingMethod trong workbook

Workbook cung cấp các cặp nhãn/mã 7(a) sau. CSV hiện lưu nhãn; bảng mã chỉ hỗ trợ đối chiếu, không thay giá trị CSV.

| Mã | Nhãn tiếng Anh theo SBA |
|---|---|
| 7AG | 7a General |
| 7EW | 7a with EWCP |
| WCP | 7(a) WCP |
| SGC | Builders Line of Credit (CAPLine) |
| CAI | Community Advantage Initiative |
| CAT | Community Advantage International Trade |
| CAR | Community Advantage RLOC |
| CRL | Community Advantage Recovery Loan |
| CTR | Contract Loan Line of Credit (CAPLine) |
| EXP | Export Express |
| ITR | International Trade Loans |
| MAC | MARC 7a General |
| PLP | Preferred Lenders Program |
| PLW | Preferred Lenders with EWCP |
| PWC | Preferred Lenders with WCP |
| SBX | SBA Express Program |
| SLC | Seasonal Line of Credit (CAPLine) |
| STC | Standard Asset Base Working Capital Line of Credit (CAPLine) |

## Đối chiếu nguồn

Mọi thuộc tính trên đều có định nghĩa trong sheet 7(a). CSV ghi `P I F` trong khi workbook ghi `PIF`; quy tắc kiểm tra so theo mapping tạm thời, chưa thay dữ liệu. Các mã giá trị khác chưa được workbook giải thích đầy đủ: `BusinessAge`, `FixedorVariableInterestInd`, `CollateralInd`, `RevolverStatus` (workbook ghi 0/1, CSV dùng Y/N), `SoldSecMrktInd` khi blank. Cần xác minh trước khi quy chuẩn ý nghĩa.