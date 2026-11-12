# Q11 – Phân tích trạng thái khoản vay theo phương thức xử lý

Thống kê số bản ghi theo từng trạng thái khoản vay và phương thức xử lý hồ sơ đối với các khoản vay được phê duyệt trong năm tài chính FY2025, nhằm xác định sự phân bố trạng thái giữa các phương thức xử lý.

## Cấu hình thực hiện

| Thành phần | Trường |
|---|---|
| Measure | `Record Count` |
| Rows | `Processing Method` |
| Rows | `Loan Status Raw` |
| Filter | `Fiscal Year = 2025` |
| Phép OLAP | Slice, Dice |

`Loan Status Raw` tương ứng với thuộc tính **Raw Status** của dimension **Dim Loan Status** trong project Cube hiện tại, lấy từ `Dim_LoanStatus.RawStatus`. `Processing Method` thuộc `Dim_LoanProfile.ProcessingMethod`; bộ lọc năm thuộc `Dim_Date.FiscalYear`.

Số bản ghi được tính bằng `SUM(RecordCount)`, với `RecordCount = 1` trên mỗi bản ghi công bố. Giữ nguyên nhãn trạng thái raw, gồm `P I F`. FY2025 là năm tài chính phê duyệt; trạng thái là trạng thái quan sát tại snapshot 30/06/2026.

## Cube Browser và Excel PivotTable

Trong Cube Browser, chọn Cube `SBA7A DWH_DSV`, lọc **Fiscal Year = 2025**, đưa **Processing Method** rồi **Raw Status** vào hàng và đưa **Record Count** vào vùng dữ liệu.

Trong Excel PivotTable kết nối cùng Cube, đặt **Fiscal Year = 2025** ở Filters, **Processing Method** rồi **Raw Status** ở Rows và **Record Count** ở Values. Giữ cách hiển thị giá trị là **No Calculation**, định dạng số nguyên và mở các nhóm phương thức để thấy từng trạng thái. Đối chiếu số đếm ở cùng cặp phương thức × trạng thái giữa các công cụ.

## MDX tham khảo

```mdx
SELECT
    {[Measures].[Record Count]} ON COLUMNS,

    NON EMPTY (
        [Dim Loan Profile].[Processing Method].[Processing Method].Members
        *
        [Dim Loan Status].[Raw Status].[Raw Status].Members
    ) ON ROWS

FROM [SBA7A DWH_DSV]

WHERE (
    [Dim Date].[Fiscal Year].&[2025]
);
```

## Trình bày kết quả

Bảng kết quả gồm **Processing Method**, **Loan Status Raw** và **Record Count**, với nhãn phạm vi **FY2025**. `NON EMPTY` chỉ ẩn các tổ hợp không có dữ liệu trong kết quả MDX. Chỉ ghi số đếm và nhận xét về sự phân bố trạng thái từ kết quả đã thực thi và đối soát.
