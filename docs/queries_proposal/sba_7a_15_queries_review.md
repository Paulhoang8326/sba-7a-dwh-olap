# Đề xuất chốt 15 bài toán phân tích, schema và các quyết định trước ETL
## Đồ án Kho dữ liệu & OLAP – SBA 7(a)

> **Phạm vi đề xuất:** 15 bài toán phân tích chính  
> **Schema đề xuất:** 1 Fact + 7 Dimension  
> **Nguồn:** SBA 7(a) FOIA, FY2020–FY2026  
> **Snapshot:** 30/06/2026  
> **Grain:** Một dòng trong `FactLoanSnapshot` đại diện cho một bản ghi CSV SBA 7(a) được công bố tại snapshot 30/06/2026.

---

# 1. Mục tiêu của tài liệu

Tài liệu này được dùng để nhóm cùng rà soát và chốt ba nội dung chính trước khi chuyển sang Source-to-Target Mapping, Data Cleaning và ETL:

1. **Bộ 15 bài toán phân tích chính thức** của đồ án.
2. **Schema 1 Fact + 7 Dimension** tương ứng với phạm vi 15 câu.
3. **Các business rule và quyết định còn phải chốt** trước khi triển khai ETL.

Bộ câu hỏi được xây dựng theo hướng mỗi câu phải giúp nhìn ra ít nhất một trong các yếu tố sau:

- xu hướng theo thời gian;
- mức độ tập trung;
- sự thay đổi cơ cấu;
- sự khác biệt giữa các nhóm;
- một nhóm bất thường hoặc đáng đào sâu;
- mối quan hệ giữa nhiều chỉ số;
- Top-N và mức đóng góp của từng nhóm.

Mục tiêu là tránh việc 15 câu chỉ là các truy vấn `SUM + GROUP BY` thay đổi cột.

---

# 2. Quy ước công thức

| Ký hiệu | Ý nghĩa |
|---|---|
| `A` | `SUM(GrossApproval)` – Tổng vốn phê duyệt |
| `G` | `SUM(SBAGuaranteedApproval)` – Tổng vốn SBA bảo lãnh khi phê duyệt |
| `N` | `SUM(RecordCount)` – Số bản ghi công bố |
| `J` | `SUM(JobsSupported)` – Tổng số việc làm được lender báo cáo |
| `CO` | `SUM(GrossChargeOffAmount)` trên các dòng `CHGOFF` |

> `N` là số **bản ghi được công bố**, không phải số khoản vay duy nhất.

---

# 3. Bộ 15 bài toán phân tích đề xuất

| # | Nội dung câu hỏi phân tích | Công thức / logic chính | Thuộc tính / bảng liên quan | Điều kiện tính và lưu ý |
|---:|---|---|---|---|
| **1** | **Phân tích tổng vốn phê duyệt theo từng năm tài chính, quý tài chính và bang của dự án, nhằm xác định giai đoạn nào có quy mô vốn lớn nhất và các bang nào đóng góp chính vào biến động đó.** | `A = SUM(GrossApproval)`; so sánh theo FY → Quarter → State | **FactLoanSnapshot:** `GrossApproval`; **DimDate:** `FiscalYear`, `FiscalQuarter`; **DimProjectGeography:** `ProjectState` | FY bắt đầu 01/10. FY2026 chỉ đến 30/06 nên không so trực tiếp tổng FY2026 với full FY trước. |
| **2** | **So sánh số bản ghi khoản vay được công bố và quy mô vốn phê duyệt trung bình giữa các phương thức xử lý qua từng năm tài chính, nhằm phân biệt trường hợp tăng tổng vốn do có nhiều hồ sơ hơn với trường hợp tăng do quy mô mỗi hồ sơ lớn hơn.** | `N`; `AverageApproval = A/N` | **Fact:** `GrossApproval`, `RecordCount`; **DimDate:** `FiscalYear`; **DimLoanProfile:** `ProcessingMethod` | `N` là số bản ghi công bố, không phải số khoản vay duy nhất. `N > 0`. |
| **3** | **Phân tích tốc độ tăng trưởng vốn phê duyệt qua từng năm tài chính (YoY – Year-over-Year, tức tăng trưởng so với năm trước), nhằm xác định những giai đoạn danh mục tăng nhanh, chững lại hoặc suy giảm; riêng FY2026 được so sánh với cùng kỳ FY2025.** | `YoY = (A_t - A_t-1)/A_t-1 ×100%` | **Fact:** `GrossApproval`; **DimDate:** `FiscalYear`, `FiscalMonth` | FY2020–FY2025 so full-year khi có năm trước. FY2026 chỉ so 01/10–30/06 với FY2025 cùng kỳ. `A_t-1 > 0`. |
| **4** | **Phân tích tổng vốn SBA bảo lãnh và tỷ trọng bảo lãnh theo từng phương thức xử lý qua các năm tài chính, nhằm phát hiện phương thức nào vừa chiếm quy mô bảo lãnh lớn vừa có mức độ phụ thuộc tương đối vào bảo lãnh SBA cao.** | `G`; `GuaranteeRatio = G/A ×100%` | **Fact:** `GrossApproval`, `SBAGuaranteedApproval`; **DimDate**; **DimLoanProfile:** `ProcessingMethod` | Tử và mẫu dùng cùng lát cắt. `A > 0`. Đây là bảo lãnh **khi phê duyệt**, không phải số tiền SBA đã thực trả. |
| **5** | **Phân tích phần vốn phê duyệt không nằm trong phần SBA bảo lãnh theo lender hiện tại và phương thức xử lý, nhằm xác định những lender/phương thức đang gắn với quy mô vốn ngoài phần bảo lãnh lớn nhất.** | `NonSBAGuaranteed = A - G` | **Fact:** hai amount; **DimLender:** `LocationID`, `BankName`; **DimLoanProfile:** `ProcessingMethod`; **DimDate** | Không diễn giải đây là dư nợ hiện tại hoặc phần tổn thất lender sẽ phải chịu. |
| **6** | **Tìm các ngành NAICS có tổng vốn phê duyệt tăng từ FY2024 sang FY2025 nhưng tỷ trọng SBA bảo lãnh không tăng hoặc giảm, nhằm phát hiện những ngành đang mở rộng quy mô vốn mà không tăng mức phụ thuộc tương đối vào bảo lãnh SBA. Với mỗi ngành thỏa điều kiện, tìm Top 3 bang đóng góp dương nhiều nhất vào mức tăng vốn và tính tỷ trọng đóng góp của từng bang.** | `ΔA = A_2025-A_2024`; điều kiện `ΔA>0` và `GuaranteeRatio_2025 <= GuaranteeRatio_2024`. Bang: `ΔA_state`; `PositiveContribution = max(ΔA_state,0)/Σmax(ΔA_state,0)` | **Fact:** approval + guarantee; **DimIndustry**; **DimProjectGeography**; **DimDate** | So cùng population. Nếu dùng sector phải xác minh NAICS mapping. “Đóng góp” ở đây là đóng góp **dương** để tỷ trọng dễ diễn giải. |
| **7** | **Tìm các bang có mức độ tập trung vốn cao nhất vào một số county bằng cách xếp hạng Top 3 county theo vốn phê duyệt trong từng bang và tính tỷ trọng của Top 3 trong tổng vốn của bang, nhằm xác định nơi dòng vốn tập trung vào vài khu vực nhỏ thay vì phân bổ rộng.** | `CountyShare = A_county/A_state`; `Top3CountyShare = ΣA_top3county/A_state ×100%` | **Fact:** `GrossApproval`; **DimProjectGeography:** State, County; **DimDate** | County luôn phải đi cùng State. Có thể tính theo từng FY để xem concentration thay đổi theo thời gian. |
| **8** | **Tìm những bang có sự chuyển dịch cơ cấu ngành mạnh giữa FY2024 và FY2025 bằng cách so sánh tỷ trọng vốn của từng ngành trong tổng vốn của bang; với mỗi bang, liệt kê Top 3 ngành tăng thị phần mạnh nhất và Top 3 ngành giảm mạnh nhất, nhằm nhìn ra hướng dịch chuyển của dòng vốn giữa các ngành.** | `IndustryShare = A_industry,state/A_state`; `ShareChangePP = Share_2025 - Share_2024` | **Fact:** `GrossApproval`; **DimIndustry**; **DimProjectGeography**; **DimDate** | `ShareChangePP` tính theo **điểm phần trăm** (percentage point – mức chênh giữa hai tỷ lệ %), không phải % tăng trưởng của tỷ lệ. |
| **9** | **Tìm các lender có tổng vốn phê duyệt tăng đồng thời quy mô vốn trung bình trên mỗi bản ghi cũng tăng từ FY2024 sang FY2025, nhằm phát hiện những lender đang mở rộng theo hướng các hồ sơ có giá trị lớn hơn. Với mỗi lender thỏa điều kiện, liệt kê Top 3 phương thức xử lý đóng góp nhiều nhất vào phần vốn tăng thêm.** | Điều kiện `A25>A24` và `(A25/N25)>(A24/N24)`; `MethodGrowth=A_method25-A_method24`; xếp Top 3 | **Fact:** Gross, RecordCount; **DimLender**; **DimLoanProfile**; **DimDate** | `LocationID` dùng nhận diện lender. Có thể tính % đóng góp dương của từng method vào tổng phần tăng dương của lender. |
| **10** | **Theo dõi tỷ trọng vốn của Top 5 lender lớn nhất qua từng năm tài chính, nhằm đánh giá danh mục đang ngày càng tập trung vào một số lender lớn hay phân tán hơn theo thời gian.** | Xếp lender theo `A`; `Top5Share = ΣA_top5 / A_all_lenders ×100%` | **Fact:** `GrossApproval`; **DimLender**; **DimDate** | Top 5 phải được xác định lại trong từng FY. Không dùng một danh sách Top 5 cố định cho tất cả năm. |
| **11** | **So sánh tổng số việc làm được lender báo cáo và mức vốn phê duyệt trên mỗi việc làm theo ngành và bang, nhằm phát hiện các ngành/khu vực có cùng quy mô vốn nhưng khác biệt lớn về số việc làm được báo cáo.** | `ReportedJobs=J`; `ApprovalPerJob=A/J` | **Fact:** `GrossApproval`, `JobsSupported`; **DimIndustry**; **DimProjectGeography**; **DimDate** | Chỉ tính khi `J>0`. Đây là việc làm **do lender báo cáo**, không phải số việc làm được chứng minh là SBA tạo ra. |
| **12** | **Tìm các nhóm kỳ hạn (Term Band – nhóm khoản vay theo số tháng kỳ hạn) có tỷ trọng vốn tăng nhưng tỷ trọng số bản ghi giảm từ FY2024 sang FY2025, nhằm phát hiện các nhóm đang chuyển dịch về phía những khoản phê duyệt có quy mô lớn hơn. Với mỗi nhóm thỏa điều kiện, tìm Top 3 phương thức xử lý đóng góp nhiều nhất vào phần vốn tăng thêm.** | `ApprovalShare=A_band/A_allbands`; `RecordShare=N_band/N_allbands`; lọc `ApprovalShare25>24` và `RecordShare25<24`; Top 3 MethodGrowth | **Fact:** Gross, RecordCount, TermInMonths; **DimTermBand**; **DimLoanProfile**; **DimDate** | Band là phân loại do đồ án định nghĩa. `TermInMonths=0`, Missing, Invalid phải tách riêng. |
| **13** | **Phân tích cơ cấu trạng thái khoản vay tại snapshot 30/06/2026 theo năm tài chính phê duyệt và phương thức xử lý, nhằm quan sát cohort (nhóm hồ sơ cùng kỳ phê duyệt) nào đang có tỷ trọng PIF, CHGOFF, COMMIT hoặc các trạng thái khác cao hơn.** | `StatusShare_s = N(status=s)/N(all statuses same cohort/method) ×100%` | **Fact:** `RecordCount`; **DimLoanStatus**; **DimDate**; **DimLoanProfile** | Đây là status **tại snapshot hiện tại**, không phải status của khoản vay tại cuối FY trong quá khứ. Khi PIF mapping chưa chốt có thể hiển thị raw `P I F`. |
| **14** | **Tìm các ngành có tỷ trọng CHGOFF (charge-off – khoản được ghi nhận xóa nợ/gross charge-off trong dữ liệu) cao hơn mức chung của cùng cohort, đồng thời có tổng Gross Charge-off lớn; với mỗi ngành đó, liệt kê Top 3 bang đóng góp nhiều nhất vào giá trị Gross Charge-off và % đóng góp của từng bang.** | `IndustryCHGOFFShare=N_CHGOFF,industry/N_all,industry`; `CohortBaseline=N_CHGOFF,cohort/N_all,cohort`; lọc `IndustryShare > Baseline`; rank theo `CO`; `StateCOShare=CO_state/CO_industry` | **Fact:** RecordCount, GrossChargeOffAmount; **DimLoanStatus**; **DimIndustry**; **DimProjectGeography**; **DimDate** | So với baseline **cùng cohort** để giảm phần nào ảnh hưởng khác biệt tuổi cohort. Vẫn không được gọi là xác suất/default rate cuối cùng. |
| **15** | **Tìm các ngành có mức “gánh nặng charge-off tương đối” cao bằng cách so sánh tỷ trọng của ngành trong tổng Gross Charge-off với tỷ trọng của chính ngành đó trong tổng vốn phê duyệt của cùng cohort; ngành nào chiếm tỷ trọng charge-off lớn hơn đáng kể tỷ trọng vốn sẽ được ưu tiên đào sâu, sau đó xác định Top 3 bang đóng góp lớn nhất vào phần charge-off của ngành.** | `ChargeOffAmountShare=CO_industry/CO_all`; `ApprovalShare=A_industry/A_all`; `Gap = ChargeOffAmountShare - ApprovalShare`; rank `Gap DESC`; Top 3 state theo CO | **Fact:** GrossApproval, GrossChargeOffAmount; **DimIndustry**; **DimProjectGeography**; **DimLoanStatus**; **DimDate** | Hai share phải cùng cohort/filter. `Gap>0` chỉ cho thấy charge-off amount chiếm tỷ trọng lớn tương đối so với footprint approval; **không tự chứng minh ngành rủi ro hơn hoặc nguyên nhân gây charge-off**. |

---

# 4. Vì sao bộ 15 câu này có chiều sâu hơn?

| Dạng phân tích | Query tiêu biểu |
|---|---|
| Trend theo thời gian | Q1, Q3, Q4 |
| So volume với average | Q2 |
| Ratio / intensity | Q4, Q5 |
| Geographic concentration | Q7 |
| Structural shift (chuyển dịch cơ cấu) | Q8, Q12 |
| Top-N + contribution analysis | Q6, Q7, Q9, Q10, Q14, Q15 |
| Conditional pattern detection | Q6, Q9, Q12, Q14, Q15 |
| Cohort analysis | Q13–Q15 |
| Benchmark against baseline | Q14 |
| Compare two different shares | Q15 |

Các thao tác OLAP có thể thể hiện gồm:

- **Roll-up:** gộp từ mức chi tiết lên cấp cao hơn.
- **Drill-down:** đi từ cấp tổng hợp xuống chi tiết hơn.
- **Slice:** lọc theo một giá trị cụ thể.
- **Dice:** lọc đồng thời theo nhiều chiều.
- **Pivot:** thay đổi cách bố trí chiều.
- **Top-N / Ranking:** xếp hạng nhóm.
- **Contribution analysis:** tính mức đóng góp của từng nhóm.

---

# 5. Schema đề xuất tương ứng

```text
FactLoanSnapshot

DimDate
DimProjectGeography
DimIndustry
DimLender
DimLoanProfile
DimLoanStatus
DimTermBand
```

> **1 Fact + 7 Dimension**

| Bảng | Vai trò |
|---|---|
| `FactLoanSnapshot` | Lưu measures và grain source record tại snapshot |
| `DimDate` | FY, quý, tháng phê duyệt |
| `DimProjectGeography` | State, county và địa lý dự án |
| `DimIndustry` | NAICS và sector |
| `DimLender` | Lender hiện được gán |
| `DimLoanProfile` | ProcessingMethod và profile mở rộng |
| `DimLoanStatus` | Status tại snapshot |
| `DimTermBand` | Nhóm kỳ hạn |

---

# 6. Các thuộc tính dẫn xuất mới không có trực tiếp trong dataset gốc

## 6.1. Thuộc tính thời gian

| Thuộc tính | Nguồn | Logic | Dùng cho |
|---|---|---|---|
| `FiscalYear` | `ApprovalDate`, đối chiếu `ApprovalFY` | Tháng 10–12 → `YEAR+1`, còn lại → `YEAR` | Query theo FY |
| `FiscalQuarter` | `ApprovalDate` | Q1=10–12, Q2=1–3, Q3=4–6, Q4=7–9 | Q1 |
| `FiscalMonth` | `ApprovalDate` | Oct=1,…,Sep=12 | Q3 |
| `CalendarYear` | `ApprovalDate` | `YEAR(date)` | Optional |
| `CalendarQuarter` | `ApprovalDate` | Quý dương lịch | Optional |
| `CalendarMonth` | `ApprovalDate` | `MONTH(date)` | Optional |
| `MonthName` | `ApprovalDate` | Tên tháng | Display |

---

# 7. DimTermBand – classification dẫn xuất

| `TermBandCode` | `TermBandName` | Điều kiện |
|---|---|---|
| `ZERO` | Zero Unverified | `TermInMonths = 0` |
| `SHORT` | Short Term | `1 <= TermInMonths <= 60` |
| `MEDIUM` | Medium Term | `61 <= TermInMonths <= 120` |
| `LONG` | Long Term | `TermInMonths > 120` |
| `MISSING` | Missing | NULL |
| `INVALID` | Invalid | Giá trị được xác định là không hợp lệ |

Các thuộc tính:

```text
TermBandKey
TermBandCode
TermBandName
MinMonths
MaxMonths
SortOrder
BandStatus
```

> Các ngưỡng trên là **proposal của đồ án**, chưa phải phân loại chính thức của SBA.

---

# 8. Thuộc tính ngành dẫn xuất

| Thuộc tính | Có sẵn trong CSV? | Nguồn / logic |
|---|:---:|---|
| `NaicsSectorCode` | Không | Mapping từ `NaicsCode` sang sector |
| `NaicsSectorName` | Không | Lookup từ NAICS reference |
| `NaicsVersion` | Không | Metadata của reference |
| `SectorMappingStatus` | Không | Trạng thái xác minh mapping |

Nếu chưa chốt NAICS version/reference, có thể phân tích ở cấp:

```text
NaicsCode
NaicsDescription
```

---

# 9. Thuộc tính status dẫn xuất

| Thuộc tính | Nguồn | Vai trò |
|---|---|---|
| `LoanStatusRaw` | `LoanStatus` nguồn | Giữ nguyên giá trị gốc |
| `LoanStatusCanonicalCode` | Mapping | Mã chuẩn nếu đã xác minh |
| `StatusMappingStatus` | Metadata | Trạng thái mapping |

Ví dụ mapping ứng viên:

```text
P I F -> PIF
```

Không ghi đè raw trước khi mapping được chốt.

---

# 10. Calculated Measures / KPI mới

| Calculated Measure | Công thức | Dùng trong |
|---|---|---|
| `ApprovalRecordCount` | `SUM(RecordCount)` | Q2, Q7, Q12–Q14 |
| `AverageGrossApproval` | `A/N` | Q2, Q9 |
| `YoYGrossApprovalGrowth` | `(A_t-A_t-1)/A_t-1` | Q3 |
| `WeightedGuaranteeRatio` | `G/A` | Q4, Q6 |
| `NonSBAGuaranteedApproval` | `A-G` | Q5 |
| `GroupApprovalShare` | `A_group/A_parent` | Q7–Q12 |
| `ShareChangePP` | `Share_t - Share_t-1` | Q8 |
| `PositiveGrowthContributionShare` | `max(ΔA_group,0)/Σmax(ΔA,0)` | Q6, Q9 |
| `Top5LenderShare` | `ΣA_top5/A_all` | Q10 |
| `ApprovalPerReportedJob` | `A/J` | Q11 |
| `StatusRecordShare` | `N_status/N_parent` | Q13 |
| `ObservedCHGOFFShare` | `N_CHGOFF/N_allstatus` | Q14 |
| `ChargeOffAmountShare` | `CO_group/CO_parent` | Q15 |
| `ChargeOffVsApprovalShareGap` | `ChargeOffAmountShare - ApprovalShare` | Q15 |

Các average/share/ratio/growth phải được tính lại tại từng lát cắt OLAP, không cộng các tỷ lệ đã tổng hợp trước.

---

# 11. Technical attributes mới của DWH

| Thuộc tính | Bảng | Mục đích |
|---|---|---|
| `LoanSnapshotKey` | Fact | Surrogate PK |
| `DateKey` | DimDate | PK/FK |
| `GeographyKey` | DimProjectGeography | PK/FK |
| `IndustryKey` | DimIndustry | PK/FK |
| `LenderKey` | DimLender | PK/FK |
| `LoanProfileKey` | DimLoanProfile | PK/FK |
| `LoanStatusKey` | DimLoanStatus | PK/FK |
| `TermBandKey` | DimTermBand | PK/FK |
| `RecordCount` | Fact | Hằng `1` mỗi source record |
| `SourceFileID` | Fact | File lineage |
| `SourceRecordOrdinal` | Fact | Logical CSV record ordinal |
| `SourceRowNumber` | Fact | Physical source line, optional |
| `ETLBatchID` | Fact | Batch audit |

Đề xuất:

```sql
UNIQUE (SourceFileID, SourceRecordOrdinal)
```

---

# 12. Derived logic không nên lưu thành cột cố định

## Fiscal YTD

Q3 cần so FY2026 với FY2025 cùng kỳ.

Không nên lưu:

```text
IsFYTD = true/false
```

một cách cố định.

Nên triển khai như **dynamic predicate** dựa trên ngày cutoff của snapshot.

---

# 13. Những thành phần không còn thuộc core scope

| Thành phần | Quyết định |
|---|---|
| `DimBusiness` | Deferred |
| `DimLoanSizeBand` | Deferred |
| KPI `InitialInterestRate` | Deferred |
| `RateKnownCount` | Không cần core |
| BusinessAge / BusinessType analysis | Extension |
| PIF theo LoanSizeBand | Extension |
| Collateral analysis | Extension |
| Revolver analysis | Extension |

---

# 14. DimLoanProfile nên giữ gì?

## Bản cực gọn

```text
DimLoanProfile
---------------
LoanProfileKey
ProcessingMethod
```

## Bản cho phép mở rộng

```text
DimLoanProfile
---------------
LoanProfileKey
ProcessingMethod
FixedorVariableInterestInd
RevolverStatus
CollateralInd
```

Khuyến nghị:

> Giữ bản mở rộng nhưng đánh dấu ba thuộc tính cuối là **Optional / Extension attributes**.

---

# 15. Các quyết định bắt buộc phải chốt trước ETL

| Vấn đề | Cần chốt gì? | Nếu chưa chốt sẽ ảnh hưởng |
|---|---|---|
| **15 query chính thức** | Dùng bộ 15 câu này thay phạm vi 19 BQ hay chuyển phần còn lại sang Extension/Deferred | Scope/schema |
| **Fact grain** | 1 published CSV record × snapshot | Toàn DWH |
| **Duplicate policy** | Giữ exact duplicates, không `DISTINCT` | Count/KPI |
| **Default population** | Amount KPI có gồm `CANCLD`, `COMMIT`, `EXEMPT` hay không | Gần như mọi query |
| **FY rule** | FY bắt đầu 01/10; FY2026 same-period comparison | Query thời gian |
| **TermBand** | Chốt `1–60`, `61–120`, `>120` hay rule khác | Q12 |
| **NAICS mapping** | Phiên bản/reference chính thức | Q6, Q8, Q11, Q14, Q15 nếu dùng sector |
| **Status mapping** | `P I F` ↔ `PIF` | DimLoanStatus |
| **Unknown members** | Policy Unknown/Missing/Invalid cho FK NOT NULL | ETL lookup |
| **Lender identity** | `LocationID` làm business key | Q5, Q9, Q10 |
| **Charge-off semantics** | CHGOFF snapshot + GrossChargeOffAmount | Q14–Q15 |
| **Lineage uniqueness** | `(SourceFileID, SourceRecordOrdinal)` | Reload/idempotency |
| **Physical types** | Decimal precision, varchar length, SQL Server `BIT`, ... | DDL |

---

# 16. Lưu ý đặc biệt với Q14 và Q15

Có thể nói:

> “Ngành X có tỷ trọng bản ghi CHGOFF quan sát cao hơn baseline của cùng cohort.”

hoặc:

> “Ngành X chiếm tỷ trọng Gross Charge-off lớn hơn tỷ trọng vốn phê duyệt trong cùng cohort.”

Không nên nói:

> “Ngành X có xác suất default cao hơn.”

hoặc:

> “Ngành X rủi ro hơn X%.”

Vì:

- dataset chỉ có một snapshot;
- cohort có thời gian theo dõi khác nhau;
- không có trạng thái lịch sử đầy đủ;
- `GrossChargeOffAmount` không phải net loss;
- không có recovery để tính tổn thất ròng.

---

# 17. Coverage của schema 1 Fact + 7 Dim

| Dimension | Query sử dụng |
|---|---|
| `DimDate` | Q1–Q15 gần như toàn bộ |
| `DimProjectGeography` | Q1, Q6–Q8, Q11, Q14–Q15 |
| `DimIndustry` | Q6, Q8, Q11, Q14–Q15 |
| `DimLender` | Q5, Q9–Q10 |
| `DimLoanProfile` | Q2, Q4–Q5, Q9, Q12–Q13 |
| `DimLoanStatus` | Q13–Q15 |
| `DimTermBand` | Q12 |

> Không có Dimension nào tồn tại chỉ để “cho đủ schema”.

---

# 18. Mức độ khó của bộ query

| Tầng | Query | Đặc điểm |
|---|---|---|
| **Cơ sở** | Q1, Q2, Q4, Q5, Q11, Q13 | SUM, average, ratio, group |
| **Trung bình** | Q3, Q7, Q10 | growth, ranking, share |
| **Nâng cao / nhiều lớp** | **Q6, Q8, Q9, Q12, Q14, Q15** | điều kiện đa KPI + change + Top-N + contribution + benchmark |

---

# 19. Trình tự triển khai sau khi chốt

```text
15 Business Questions
        ↓
KPI / Formula
        ↓
Business Rules
        ↓
Final Schema
        ↓
Source-to-Target Mapping
        ↓
Data Cleaning Rules
        ↓
ETL
        ↓
Cube / OLAP
        ↓
Queries / Dashboard
```

Không nên bắt đầu code ETL trước khi chốt:

- default population;
- TermBand;
- NAICS mapping;
- status mapping;
- lineage uniqueness.

---

# 20. Đề xuất cập nhật tài liệu trong repo

Nếu nhóm chốt bộ 15 câu này, nên chuyển phạm vi sang:

> **15 Core Business Questions + các Business Questions còn lại là Extension / Deferred**

Mục tiêu:

- tránh schema tiếp tục bị thiết kế để cover phạm vi cũ;
- tránh `DimBusiness`, `DimLoanSizeBand`, rate analysis quay lại core;
- đảm bảo Business Questions → KPI → Schema → ETL dùng cùng một scope.

---

# 21. Ba nội dung nên được duyệt cùng lúc

Để kết thúc bước requirement/modeling, nhóm nên duyệt đồng thời:

1. **Bộ 15 bài toán phân tích** trong mục 3.
2. **Schema 1 Fact + 7 Dimension**.
3. **Danh sách quyết định bắt buộc trước ETL** trong mục 15.

Nếu ba phần này thống nhất, có thể chuyển sang:

> **Source-to-Target Mapping + Data Cleaning Rules.**
