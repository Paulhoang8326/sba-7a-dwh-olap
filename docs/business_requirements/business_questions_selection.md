# Đề xuất phạm vi Business Questions cho đồ án

Đề xuất **19/24 câu hỏi** trong [catalog](business_questions_catalog.md) vào phạm vi chính. Đây là lựa chọn phạm vi để phát triển đề cương; `CONDITIONAL` nghĩa là phải hoàn tất điều kiện nêu dưới đây trước khi đưa ra số chính thức. Chọn theo mức phù hợp đề tài, khả năng trả lời từ CSV, phân tích đa chiều, giá trị dashboard và tránh lặp câu hỏi. Không có câu nào chứng minh yêu cầu vận hành thực tế của SBA.

| BQ ID | Nhóm | Lý do chọn và điều kiện thực hiện |
|---|---|---|
| BQ01 | G01 | Trục quy mô vốn phê duyệt theo thời gian và địa lý; giữ nhãn vốn **phê duyệt** và nêu FY2026 chưa đủ. |
| BQ02 | G01 | Tách count dòng và quy mô bình quân để không đọc sai biến động tổng; mọi count ghi là dòng công bố. |
| BQ03 | G01 | Bổ sung phân tích động giữa các kỳ; FY2026 chỉ so cùng kỳ tới 30/06, FY đầy đủ so cùng phạm vi năm. |
| BQ04 | G01 | Cho phép xem mix quy mô theo FY/tuổi đời; công bố ngưỡng nhóm dẫn xuất và giữ `BusinessAge` thiếu/`Unanswered`. |
| BQ06 | G02 | Measure bảo lãnh tại phê duyệt sẵn có, kết hợp FY và method. |
| BQ07 | G02 | So tỷ trọng bảo lãnh qua địa lý/ngành; tính tỷ số hai tổng với cùng điều kiện lọc. |
| BQ08 | G02 | Làm rõ phần vốn phê duyệt ngoài bảo lãnh theo lender hiện tại; không gọi đó là dư nợ/rủi ro thực tế. |
| BQ10 | G03 | Địa lý dự án state→county tạo drill-down tự nhiên; county luôn ghép với state. |
| BQ11 | G03 | Tỷ trọng state theo FY hỗ trợ đánh giá tập trung và pivot, mẫu số là tổng cùng FY. |
| BQ12 | G03 | Cơ cấu ngành × địa lý là phân tích đa chiều trọng tâm; cần xác nhận quy tắc/phiên bản NAICS trước khi đặt tên sector. |
| BQ14 | G03 | Bổ sung mặt việc làm được báo cáo; trình bày rõ lender tự khai, mẫu số khác 0 nếu tính USD/việc làm. |
| BQ15 | G04 | Phân bố theo lender phù hợp chủ đề danh mục; dùng `LocationID` và gọi lender **hiện được gán**. |
| BQ16 | G04 | Mix kỳ hạn theo sản phẩm/FY có giá trị OLAP; quy tắc nhóm và 11 dòng kỳ hạn 0 cần công bố. |
| BQ17 | G04 | Cơ cấu doanh nghiệp theo FY/state có sẵn; giữ riêng giá trị thiếu và nhãn `Unanswered`. |
| BQ18 | G04 | So lãi suất ban đầu theo rate type/method là góc nhìn khoản vay có ích; cần xác minh đơn vị, 87 số 0, 8 ô thiếu và mã F/V. |
| BQ20 | G05 | Cơ cấu trạng thái tại snapshot là nền cho mọi phân tích outcome; giữ nhãn thô `P I F` đến khi chốt mapping. |
| BQ21 | G05 | Tỷ trọng CHGOFF đã quan sát theo cohort/state/ngành cung cấp insight thận trọng; luôn ghi count mẫu số và tuổi cohort. |
| BQ22 | G05 | Gross charge-off theo cohort/ngành/địa lý liên quan trực tiếp chủ đề kết quả; kiểm tra DQ09/DQ13 khi phân tích ngày sự kiện. |
| BQ23 | G05 | Tỷ trọng PIF đã quan sát là góc nhìn bổ sung CHGOFF; cần xác nhận mapping `P I F`/`PIF` và không gọi là hoàn trả cuối cùng. |

## Câu hỏi để mở rộng

| BQ ID | Lý do chưa đưa vào phạm vi chính | Điều kiện để xem xét lại |
|---|---|---|
| BQ05 | Mùa vụ theo tháng có phần trùng với BQ01/BQ03, dữ liệu FY2026 thiếu quý cuối. | Có thời gian làm drill-down theo tháng và quy tắc so cùng kỳ rõ ràng. |
| BQ09 | Tỷ lệ bảo lãnh theo nhóm quy mô/method bổ sung chiều sâu nhưng chồng phần BQ04 và BQ07. | Sau khi chốt ngưỡng quy mô và kiểm tra độ phủ từng nhóm. |
| BQ13 | Chênh giữa bang người vay và dự án hữu ích nhưng nằm ngoài trọng tâm địa điểm dự án. | Có nhu cầu riêng phân tích địa chỉ người vay so địa điểm dự án. |
| BQ19 | Có thể phân tích collateral, nhưng workbook chưa giải mã Y/N rõ và không có giá trị tài sản. | Xác minh mã `CollateralInd`, chỉ mô tả cờ lender báo. |
| BQ24 | Tỷ trọng CHGOFF trong tập resolved dễ bị hiểu nhầm là rủi ro toàn danh mục; phụ thuộc mạnh tuổi cohort/cỡ mẫu. | Chốt tập resolved, ngưỡng cỡ mẫu và cách công bố giới hạn chọn mẫu. |

Các câu hỏi mở rộng không bị đánh giá là vô giá trị; đây là quyết định giữ phạm vi đồ án tập trung và tránh diễn giải quá mức.

## Câu hỏi không được dataset hỗ trợ

| Câu hỏi | Thiếu thông tin |
|---|---|
| Dư nợ hiện tại theo lender/state là bao nhiêu? | Không có lịch sử giải ngân, trả nợ hoặc số dư. |
| SBA đã thực trả bảo lãnh và chịu tổn thất ròng bao nhiêu? | Không có claim payment, recovery hay dòng tiền; `GrossChargeOffAmount` là gross toàn khoản vay. |
| Tỷ lệ vỡ nợ cuối cùng của từng cohort? | Chỉ có một snapshot, nhiều hồ sơ chưa có outcome và thời gian theo dõi khác nhau. |
| Trạng thái từng khoản tại cuối mỗi FY trước đây? | Không có chuỗi snapshot/trạng thái lịch sử. |
| Chương trình SBA tạo thêm bao nhiêu việc làm so với khi không tham gia? | Không có nhóm đối chứng; `JobsSupported` do lender tự khai. |

## Điểm phải chốt trước KPI Catalog

1. Đơn vị đếm chính thức: dòng công bố; nếu muốn số khoản vay duy nhất cần LoanID/đối soát ngoài CSV. Không loại 687 dòng trong nhóm exact duplicate dựa trên suy đoán (DQ15).
2. Phạm vi trạng thái của từng tổng vốn và mẫu số; xử lý `CANCLD`, `COMMIT`, `EXEMPT` có chủ đích. BQ20–BQ23 là snapshot, không phải lịch sử.
3. Quy tắc FY/quý/tháng, cửa sổ cùng kỳ FY2026, cách trình bày cohort chưa trưởng thành.
4. Mapping `P I F` ↔ `PIF`; mã F/V, Y/N của collateral/revolver; phiên bản và mapping NAICS sector.
5. Đơn vị và cách tổng hợp lãi suất; chính sách với 0/thiếu/kỳ hạn 0 và ngày sự kiện bất thường DQ01–DQ13. Không thực hiện làm sạch trong giai đoạn này.
6. Quy tắc xác định lender bằng `LocationID` và cách ghi nhãn `BankName` là tổ chức **hiện được gán**.

Sau khi những điều kiện trên được ghi thành quyết định có nguồn, bộ 19 câu hỏi đủ làm đầu vào cho **KPI Catalog ứng viên và xác định chiều phân tích chính thức**. Bản hiện tại chưa phải KPI Catalog đã chốt.
