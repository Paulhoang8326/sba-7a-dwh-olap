# Q6 – Phân tích tăng trưởng vốn phê duyệt theo năm tài chính

Phân tích tốc độ tăng trưởng tổng vốn phê duyệt SBA 7(a) qua các năm tài chính FY2021–FY2025 bằng chỉ số YoY (Year-over-Year), nhằm xác định xu hướng tăng trưởng hoặc suy giảm vốn phê duyệt qua từng năm.

## Phạm vi và độ đo

Kết quả Q6 gồm đúng năm hàng FY2021–FY2025, mỗi hàng so tổng vốn của cả năm tài chính với năm liền trước. FY2020 chỉ là năm cơ sở cho YoY FY2021, không hiển thị trong các hàng kết quả tăng trưởng. Không đưa FY2026 vào kết quả.

Sử dụng các độ đo hiện có trong Cube `SBA7A DWH_DSV`:

- `Gross Approval`: tổng vốn phê duyệt của năm đang xét.
- `Prior FY Gross Approval`: tổng vốn phê duyệt của năm trước.
- `YoY Gross Approval Growth`: `(Gross Approval − Prior FY Gross Approval) / Prior FY Gross Approval`, hiển thị phần trăm. Năm trước rỗng hoặc bằng 0 thì trả về `NULL`.

Hai độ đo tính toán sử dụng `CurrentMember` của hierarchy `[Dim Date].[Fiscal Date]`. Vì vậy, phải đặt **Fiscal Date → Fiscal Year** trên hàng; không dùng riêng attribute hierarchy `[Dim Date].[Fiscal Year]`. Dùng toàn năm tài chính, không đặt bộ lọc quý/tháng/ngày.

## MDX

Chạy [06_MDX.mdx](MDX_Queries/06_MDX.mdx) trong database SSAS chứa Cube. Trục hàng chỉ chọn FY2021–FY2025; FY2020 vẫn có trong dữ liệu để `PrevMember` tính được YoY FY2021. Không dùng subselect hoặc slicer năm giới hạn dữ liệu còn FY2021–FY2025 trước khi tính độ đo.

## Cube Browser

1. Chọn Cube `SBA7A DWH_DSV`, nạp lại metadata nếu cần.
2. Đưa hierarchy **Dim Date → Fiscal Date** vào hàng và giữ ở cấp **Fiscal Year**; không mở xuống quý/tháng.
3. Đưa ba độ đo trên vào vùng dữ liệu. Giữ FY2020 trong ngữ cảnh tính toán; không áp dụng bộ lọc dữ liệu loại năm cơ sở.
4. Khi dùng bộ lọc hàng để hiển thị FY2021–FY2025, kiểm tra `Prior FY Gross Approval` của FY2021 vẫn là tổng FY2020. Nếu Browser tạo subselect làm mất năm cơ sở, dùng kết quả của [truy vấn MDX Q6](MDX_Queries/06_MDX.mdx) để xuất bảng năm hàng.
5. Bảng và hình kết quả Q6 chỉ trình bày FY2021–FY2025, không kèm hàng tổng cộng hoặc FY2026. FY2020 chỉ được nêu như cơ sở so sánh của FY2021.

## Excel PivotTable

1. Kết nối tới cùng Cube, tạo PivotTable dành cho Q6.
2. Rows: **Dim Date → Fiscal Date → Fiscal Year**; Values: ba độ đo trên. Sử dụng trực tiếp `YoY Gross Approval Growth` của Cube.
3. Giữ tất cả năm trong dữ liệu Pivot để năm cơ sở vẫn truy cập được. Không lọc FY2020 khỏi Pivot bằng slicer, report filter hoặc bộ lọc thành viên. Không đặt bộ lọc quý/tháng/ngày.
4. Tắt Subtotals và Grand Totals, thu gọn hierarchy về cấp năm. Để chỉ trình bày FY2021–FY2025, ẩn các **hàng worksheet** chứa FY2020 và FY2026; không xóa các hàng và không lọc dữ liệu Pivot. Sau mỗi lần Refresh hoặc đổi bố cục, kiểm tra lại các hàng được ẩn.
5. Định dạng hai cột vốn bằng USD và cột YoY dạng phần trăm; đối chiếu năm hàng với MDX Q6, đặc biệt mẫu số FY2021 phải là tổng FY2020.

## Bảng kết quả và nhận xét

Bảng kết quả có các cột **Năm tài chính**, **Tổng vốn phê duyệt (USD)**, **Vốn phê duyệt năm trước (USD)** và **YoY (%)**. Thứ tự và cơ sở so sánh của các hàng:

| Năm tài chính trong kết quả | Năm cơ sở so sánh |
|---|---|
| FY2021 | FY2020 |
| FY2022 | FY2021 |
| FY2023 | FY2022 |
| FY2024 | FY2023 |
| FY2025 | FY2024 |

Điền các giá trị từ cùng một lần truy vấn hoặc Refresh. Không cộng hoặc lấy trung bình các tỷ lệ YoY để tạo hàng tổng cộng. Dùng giá trị chưa làm tròn khi kiểm tra `(A_t − A_t-1) / A_t-1`.

Nhận xét theo từng năm FY2021–FY2025: YoY dương thể hiện vốn tăng so với năm trước; âm thể hiện suy giảm; bằng 0 thể hiện không đổi. Chỉ xác định năm tăng mạnh nhất, năm giảm mạnh nhất và xu hướng của giai đoạn từ kết quả đã kiểm chứng. Không đưa nhận xét tăng trưởng FY2020 hoặc FY2026 vào Q6.
