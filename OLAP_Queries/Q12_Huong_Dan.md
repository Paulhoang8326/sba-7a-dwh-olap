# Q12 – Thống kê vốn phê duyệt theo nhóm kỳ hạn vay

Thống kê số bản ghi, tổng vốn phê duyệt và giá trị vốn phê duyệt trung bình theo từng nhóm kỳ hạn vay (Term Band) trong năm tài chính FY2025, nhằm so sánh quy mô vốn giữa các nhóm kỳ hạn.

Phép OLAP: **Slice, Roll-up**.

## SSAS Cube Browser – Visual Studio

Mở `SBA7A DWH_DSV.cube` → tab **Browser**, dùng cấu hình:

| Vị trí | Bảng | Trường |
|---|---|---|
| Rows | `Dim Term Band` | `Term Band Name` |
| Measures | `Fact Loan` | `Record Count` |
| Measures | `Fact Loan` | `Gross Approval` |
| Measures | `Fact Loan` | `Average Approval per Record` |
| Filter | `Dim Date` | `Fiscal Year = 2025` |

`Term Band Name` là tên thuộc tính hiện có trong project Cube để hiển thị từng nhóm kỳ hạn. Slice chọn năm phê duyệt FY2025; Roll-up tổng hợp các bản ghi thành từng nhóm Term Band.

Sử dụng ba độ đo hiện có: `Record Count = SUM(RecordCount)`, `Gross Approval = SUM(GrossApproval)` và `Average Approval per Record = Gross Approval / Record Count`. Vốn bình quân trả NULL khi số bản ghi rỗng hoặc bằng 0. Không lấy trung bình các giá trị bình quân đã tổng hợp. Giữ nguyên quy tắc phân nhóm kỳ hạn, gồm ZERO và TERM_120; các nhãn DQ giữ riêng khi có phát sinh.

## MDX và Excel PivotTable

[12_MDX.mdx](MDX_Queries/12_MDX.mdx) sử dụng đúng ba độ đo, hàng `Dim Term Band.Term Band Name` và `WHERE Fiscal Year = 2025` theo cấu hình trên.

Với Excel PivotTable kết nối cùng Cube: đặt **Term Band Name** ở Rows, ba độ đo ở Values và **Fiscal Year = 2025** ở Filters. Sử dụng trực tiếp độ đo bình quân của Cube, hiển thị giá trị theo **No Calculation**. Định dạng số bản ghi là số nguyên, vốn và vốn bình quân là USD.

## Trình bày kết quả

Bảng gồm **Term Band**, **Record Count**, **Gross Approval (USD)** và **Average Approval per Record (USD)**, ghi rõ phạm vi **FY2025**. Đối chiếu từng nhóm giữa Browser, PivotTable và MDX trước khi nhận xét về số bản ghi, quy mô vốn và vốn bình quân. Chỉ ghi số liệu và nhận xét từ kết quả thực thi đã kiểm chứng.
