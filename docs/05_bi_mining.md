# Power BI, Looker Studio và mining

## Sáu báo cáo

Tạo 3 báo cáo riêng ở mỗi công cụ để đáp ứng cách hiểu chặt của “3 reports”; có thể tái sử dụng mô hình dữ liệu. Cùng tên KPI, đơn vị USD và phạm vi status ở cả hai nền tảng. Mọi trang ghi `Snapshot 2026-06-30` và FY2026 partial.

| Công cụ / báo cáo | Câu hỏi | Visuals và tương tác |
|---|---|---|
| Power BI 1 – Portfolio | Vốn phân bổ và xu hướng như thế nào? | Cards Count, NonCancelledApproval, Guaranteed; line tháng; stacked FY/status; slicers FY, State, Sector |
| Power BI 2 – Industry & Jobs | Ngành/địa phương nào nhận vốn và báo cáo hỗ trợ việc làm nhiều? | Bar sector, map state, matrix county, scatter Gross vs Jobs; drill ngành và địa lý; tooltip Approval Per Job |
| Power BI 3 – Outcomes & Lenders | Cohort nào có tỷ lệ CHGOFF trong nhóm resolved cao? | Counts theo status; rate theo cohort kèm denominator, scatter lender, charge-off amount; filter minimum Resolved Count=100 |
| Looker 1 – Portfolio overview | So sánh quy mô FY/state | Scorecards, time/FY bar, table state, status filter |
| Looker 2 – Sector and employment | Phân bổ ngành và JobsSupported | Sector bars, state heat table, scatter, share of gross; FY filter |
| Looker 3 – Cohort outcomes | Resolved outcome khác nhau theo FY/ngành/bang? | Resolved Count, Charge Off Count, ratio, status distribution, amount; minimum denominator filter |

Looker dùng `mart_portfolio.csv` đã tổng hợp theo FY/State/Sector/Status, không phải một sample tùy ý. Mart này **không có lender/county/month**, nên không đặt các bộ lọc hoặc biểu đồ đó trong 3 báo cáo Looker hiện tại. Nếu cần drill sâu phải xuất mart khác và đối soát lại; không blend các bảng grain khác nhau gây fan-out. Không tải raw borrower name/address lên dashboard công khai.

Power BI dùng SQL view `marts.vLoan` cho prototype hoặc mô hình snowflake từ SQL Server; quan hệ 1:N, hướng filter single. Nếu dùng live SSAS, calculated measures lấy từ cube. CSV mart là phương án chuyển dữ liệu Looker; tạo data source upload hoặc Google Sheets/BigQuery tùy môi trường, không giả định dịch vụ Looker truy cập được SQL Server localhost.

### Công thức mẫu Power BI Import

```dax
Gross Approval = SUM(FactLoanSnapshot[GrossApproval])
Loan Count = SUM(FactLoanSnapshot[LoanCount])
Resolved Charge Off Rate = DIVIDE(SUM(FactLoanSnapshot[ChargeOffCount]), SUM(FactLoanSnapshot[ResolvedCount]))
Guarantee Ratio = DIVIDE(SUM(FactLoanSnapshot[SBAGuaranteedApproval]), [Gross Approval])
Weighted Initial Rate = DIVIDE(SUM(FactLoanSnapshot[InterestWeightedAmount]), SUM(FactLoanSnapshot[InterestKnownApproval]))
```

Looker calculated field: `SUM(ChargeOffCount) / SUM(ResolvedCount)` với CASE trả NULL nếu SUM(ResolvedCount)=0; tương tự weighted rate và Average Disbursement Days. Không dùng AVG của tỷ lệ đã tính theo dòng mart. Các khoản hủy vẫn xuất hiện ở status overview; báo cáo vốn hoạt động dùng NonCancelledApproval/Count để phân biệt.

Tiêu chí nghiệm thu: chọn FY2024, CA, Sector72 giống Q04; đối chiếu SQL/cube/Power BI/Looker. Đổi filter không làm tổng tiền tăng do nhân dòng. Tỷ lệ recompute đúng khi roll-up, không sum tỷ lệ. Lưu PBIX và link Looker, ảnh chụp filter + thời điểm xuất dữ liệu; chưa tạo trong đợt chuyển repo này.

## Mining: hướng chính khả thi

**Phân loại CHGOFF/PIF trong các khoản vay đã có kết quả tại snapshot.** ClassChargeOff=1 nếu CHGOFF, =0 nếu PIF. Loại EXEMPT, COMMIT, CANCLD khỏi tập supervised; không gán EXEMPT=0. Giữ đầy đủ trong kho và dashboard.

Baseline `python -m src.mining`:

- Allowlist: GrossApproval, SBAGuaranteedApproval, InitialInterestRate, TermInMonths, ProcessingMethod, FixedorVariableInterestInd, sector, project state, business type/age. Các thuộc tính cần được mô tả là dữ liệu công bố tại snapshot; chưa chứng minh toàn bộ bất biến từ ngày cấp vay.
- Không dùng LoanStatus làm feature, ChargeOffDate/Amount, PaidInFullDate, ngày giải ngân, status flags, SoldSecMrktInd, current lender, tên borrower hay ngày kết thúc. Chúng biết outcome hoặc thông tin sau approval.
- Train FY2020–2021, validation FY2022, test FY2023; loại borrower group xuất hiện ở split trước khỏi split sau. Hash tên+địa chỉ+ZIP chỉ giúp tránh trùng dễ nhận diện, không bảo đảm nhận diện pháp nhân hoàn hảo.
- Preprocessor fit trên train; numeric median + scaling, categorical impute + one-hot unknown ignored. Dummy prior, Logistic Regression cân bằng class, Decision Tree depth=6/min leaf=100. Chọn bằng validation average precision; test một lần, threshold cố định 0,5.
- Báo average precision (tóm tắt PR curve), ROC-AUC, precision/recall/F1, confusion matrix và prevalence từng split. Accuracy đơn lẻ dễ gây hiểu nhầm với ~9,18% positive toàn tập resolved. Không tuyên bố threshold 0,5 là tối ưu về chi phí.

**Giới hạn cần trình bày rõ:** chia cohort theo approval không biến snapshot thành historical backtest. Nhãn train có thể chỉ xảy ra sau mốc validation/test. PIF sớm được quan sát nhiều hơn khoản dài hạn còn mở; nhóm CHGOFF/PIF có selection bias và thời gian theo dõi khác nhau. Vì thế tên bài toán phải là phân loại hồi cứu trong nhóm đã có kết quả, không tuyên bố dự báo rủi ro toàn danh mục tại ngày phê duyệt.

Hướng nâng cao nếu còn thời gian: dự báo CHGOFF trong 24/36 tháng trên cohort đủ thời gian quan sát, thiết kế competing event PIF và xử lý censoring; hoặc survival analysis với time-to-event, censor ở snapshot. Cần loại ngày sự kiện sai, tránh dùng nhãn ngoài cửa sổ và đánh giá tại cutoff lịch sử. Phân cụm hồ sơ khoản vay là phần phụ, không thay thế yêu cầu classification của cô.

Hướng trình bày kết quả: baseline → mô hình dễ giải thích → so sánh metric → phân tích false positive/negative theo ngành/cohort → giới hạn. Không kết luận quan hệ nhân quả hoặc đưa ra quyết định cho vay chỉ dựa vào mô hình đồ án.

## Kết quả baseline đã chạy trên dữ liệu cục bộ

Chạy ngày 2026-09-23; Python 3.12, scikit-learn 1.9.1; seed=42. Train 43.830 dòng, validation 12.411, test 9.687 sau loại borrower group giao nhau. Positive rate lần lượt 6,25%, 13,50%, 17,61%: chênh lệch cohort rõ rệt, cần diễn giải cùng thời gian theo dõi và selection bias.

Validation average precision: Dummy **0,1350**, Logistic **0,4900**, Decision Tree **0,6763**. Chọn Decision Tree bằng validation, không chọn bằng test.

Test một lần ở threshold 0,5: average precision **0,6650**, ROC-AUC **0,8669**, precision **0,4817**, recall **0,7263**, F1 **0,5792**. Confusion matrix (hàng actual 0/1, cột predicted 0/1): `[[6648,1333],[467,1239]]`. Kết quả tốt hơn baseline trên bài toán hồi cứu này nhưng không chứng minh dự báo prospective hoặc khả năng áp dụng lên EXEMPT. Chi tiết máy đọc: `docs/mining_baseline.json`.
