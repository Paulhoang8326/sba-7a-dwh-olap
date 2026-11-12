# Q9 – Top 3 County tại California

Liệt kê Top 3 county có tổng vốn phê duyệt cao nhất tại bang California (CA) trong giai đoạn FY2020–FY2026, nhằm xác định những khu vực tập trung nhiều vốn SBA 7(a) nhất trong bang.

## Phạm vi và cách tổng hợp

- Địa lý: `Dim_ProjectGeography`, lọc `ProjectState = CA`, nhóm theo `ProjectCounty`.
- Thời gian: FY2020–FY2026, cộng toàn bộ giai đoạn cho từng county. FY2026 sử dụng dữ liệu hiện có tại snapshot 30/06/2026.
- Measure: `SUM(GrossApproval)`, hiển thị trong Cube là `Gross Approval`.
- Phép OLAP: Slice, Top-N. Xếp giảm dần theo tổng vốn và lấy Top 3 county tại California cho toàn giai đoạn.

## Cube Browser

1. Chọn Cube `SBA7A DWH_DSV`.
2. Filter: **Dim Project Geography → Project State = CA**; **Dim Date → Fiscal Year = FY2020–FY2026**.
3. Rows: **Project County**; Measures: **Gross Approval**. Giữ năm trong bộ lọc để tổng hợp chung cả giai đoạn; không đưa năm vào hàng/cột và không đặt thêm bộ lọc quý/tháng.
4. Sắp xếp giảm dần theo Gross Approval và trình bày ba county đầu tiên. Có thể dùng [truy vấn MDX Q9](MDX_Queries/09_MDX.mdx) để lấy đúng tập Top 3.

## Excel PivotTable

1. Kết nối tới cùng Cube.
2. Filters: **Project State = CA**, **Fiscal Year = FY2020–FY2026**.
3. Rows: **Project County**; Values: **Gross Approval**.
4. Tại trường Project County, chọn **Value Filters → Top 10…**, đặt **Top**, **3**, **Items**, **by Gross Approval**.
5. Sắp xếp Gross Approval từ lớn đến nhỏ. Giữ FY trong Filters để tổng hợp cả giai đoạn; tắt Grand Totals khi trình bày kết quả Top 3.

## MDX

[09_MDX.mdx](MDX_Queries/09_MDX.mdx) sử dụng cùng logic dưới đây:

```mdx
SELECT
    [Measures].[Gross Approval] ON COLUMNS,

    TOPCOUNT(
        NONEMPTY(
            [Dim Project Geography].[Project County].[Project County].Members,
            [Measures].[Gross Approval]
        ),
        3,
        [Measures].[Gross Approval]
    ) ON ROWS

FROM (
    SELECT
        {
            [Dim Date].[Fiscal Year].&[2020]
            : [Dim Date].[Fiscal Year].&[2026]
        } ON COLUMNS
    FROM [SBA7A DWH_DSV]
)

WHERE (
    [Dim Project Geography].[Project State].&[CA]
);
```

Subselect giới hạn dữ liệu ở FY2020–FY2026. `WHERE` giữ ngữ cảnh California khi `NONEMPTY` lấy các county có vốn và `TOPCOUNT` xếp giảm dần để lấy ba county theo tổng vốn của cả giai đoạn. Thuộc tính Project County trong project Cube có khóa ghép `ProjectState` + `ProjectCounty`.

## Trình bày kết quả

Bảng kết quả gồm **Thứ hạng**, **County**, **Project State (CA)** và **Tổng Gross Approval (USD), FY2020–FY2026**, sắp xếp giảm dần theo tổng vốn. Đối chiếu ba county và số tiền giữa Cube Browser, PivotTable và MDX trước khi nhận xét về nơi tập trung vốn trong California. Chỉ điền tên county, số tiền và nhận xét từ kết quả thực thi đã kiểm chứng.
