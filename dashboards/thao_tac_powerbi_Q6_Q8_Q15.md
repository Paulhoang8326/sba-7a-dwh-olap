# Thao tác Power BI – Q6, Q8 & Q15 (làm trên máy Nguyên)

File này dành cho máy đang chạy SSAS và có cube `SBA7A_SSAS` (máy `KHOINGUYEN`). Mọi thứ cần dùng đều nằm trong file này, kể cả đoạn MDX phải dán vào cube.

Cách làm giống các nhóm tham khảo: Power BI **Connect live** vào cube `SBA7A DWH_DSV`. Mọi chỉ số nằm sẵn trong cube, Power BI chỉ kéo thả, không viết DAX. Live connection vào cube Multidimensional cũng không cho tạo measure.

**Cần có trên máy**
- SQL Server đang chạy database `SBA7A_DWH`, và SSAS (Multidimensional) đang có database `SBA7A_SSAS` đã deploy và process.
- Visual Studio có extension *Analysis Services Projects*, mở được `SBA7A_SSAS/SBA7A_SSAS.sln`.
- SQL Server Management Studio (SSMS).
- Power BI Desktop: cài từ Microsoft Store, hoặc tải ở trang Power BI của Microsoft.

**Thứ tự làm**

| Phần | Việc | Thời gian ước tính |
|---|---|---|
| 0 | Thêm 8 measure vào cube, deploy, chạy kiểm tra | 15–20 phút |
| 1 | Nối Power BI vào cube | 5 phút |
| 2 | Trang Q6 | 15–20 phút |
| 3 | Trang Q8, gồm Matrix Grouping and Totals | 30–40 phút |
| 4 | Trang Q15 | 20–30 phút |
| 5 | Lưu, xuất PDF | 10 phút |

Nên làm thử một lượt trước, rồi mới bật quay video cho lượt chính. Lỗi ở bước nào thì chụp màn hình gửi lại nhóm.

**Số để đối chiếu**

| | Kết quả đúng |
|---|---|
| Q6 – YoY | FY2021 +62.03% · FY2022 −29.68% · FY2023 +7.09% · FY2024 +13.11% · FY2025 +19.80% |
| Q6 – Tổng vốn | FY2020 = 22,549,825,700 (năm gốc) · FY2025 = 37,287,816,200 |
| Q8 – FY2025 | CA 12.90% · TX 10.91% · FL 8.65% · NY 4.92% · GA 4.10% |
| Q8 – Top 3 county của CA, FY2025 | LOS ANGELES 1,457,139,100 (30.30%) · ORANGE 546,312,500 (11.36%) · SAN DIEGO 489,766,900 (10.18%) |
| Q8 – Matrix Grouping and Totals, FY2025 | Tổng CA 4,808,747,400 · Tổng TX 4,067,228,500 · Total 37,287,816,200 |
| Q15 – FY2025 | Baseline 0.11% (85 CHGOFF / 78,078 bản ghi) |
| Q15 – ngành Eligible | Retail Trade 1,913,417.62 · Construction 1,374,155.58 · Manufacturing 659,110.94 |
| Q15 – Top 3 bang của Retail Trade | CA 47.00% · AL 27.40% · TN 10.38% |

---

## Phần 0 – Bổ sung measure vào cube (làm trên máy có SSAS, 1 lần)

Cube đã có `Gross Approval`, `Prior FY Gross Approval`, `YoY Gross Approval Growth` và `State Approval Share`. Phần này thêm 8 measure:
- 1 measure lọc phạm vi cho Q6.
- 1 measure % county trong bang cho Q8.
- 6 measure cho Q15.

1. Mở **Visual Studio** → `SBA7A_SSAS/SBA7A_SSAS.sln`.
2. Trong *Solution Explorer*, mở **Cubes → `SBA7A DWH_DSV.cube`**, nhấp đúp để mở → chọn tab **Calculations**.
3. Trên thanh công cụ của tab, bấm nút **Script View** (biểu tượng tờ giấy có chữ, cạnh nút *Form View*).
4. Kéo xuống **cuối script**, xuống thêm 1 dòng trống.
   - Dán **toàn bộ khối MDX dưới đây** vào. Nếu có repo mới nhất thì khối này cũng nằm ở file `OLAP_Queries/MDX_Queries/calc_powerbi_q6_q8_q15.mdx`.
   - Không xóa dòng `CALCULATE;` hay các `CREATE MEMBER` cũ (`Average Approval per Record`, `State Approval Share`, `Prior FY Gross Approval`, `YoY Gross Approval Growth`, `SBA Guarantee Ratio`).

```mdx
/*
  Calculated members bổ sung cho báo biểu Power BI (Chương 4) – Q6, Q8, Q15.
  Dán NGUYÊN khối này vào CUỐI script ở tab Calculations (Script View) của cube
  [SBA7A DWH_DSV], sau các CREATE MEMBER đã có. Không xóa lệnh CALCULATE; ở đầu script.
  Power BI nối live vào cube Multidimensional không cho viết DAX, nên mọi chỉ số phải nằm trong cube.
*/

/* ---------- Q6: cờ phạm vi FY2021–FY2025 ----------
   Dùng làm filter trên visual (measure = 1) thay cho filter năm, để FY2020 vẫn còn
   trong ngữ cảnh và Prior FY Gross Approval của FY2021 không bị trống. */
CREATE MEMBER CURRENTCUBE.[Measures].[Q6 In Scope]
 AS IIF(
    [Dim Date].[Fiscal Date].CurrentMember.Level.Name <> "Fiscal Year",
    NULL,
    IIF(
        CInt(Right([Dim Date].[Fiscal Date].CurrentMember.Name, 4)) >= 2021
        AND CInt(Right([Dim Date].[Fiscal Date].CurrentMember.Name, 4)) <= 2025,
        1,
        NULL
    )
),
FORMAT_STRING = "0",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;

/* ---------- Q8: tỷ trọng county trong bang của nó ---------- */
CREATE MEMBER CURRENTCUBE.[Measures].[County Share in State]
 AS IIF(
    [Dim Project Geography].[Project County].CurrentMember.Level.Ordinal = 0,
    NULL,
    IIF(
        IsEmpty(
            (
                [Measures].[Gross Approval],
                [Dim Project Geography].[Project County].DefaultMember,
                Exists(
                    [Dim Project Geography].[Project State].[Project State].Members,
                    [Dim Project Geography].[Project County].CurrentMember
                ).Item(0)
            )
        ),
        NULL,
        [Measures].[Gross Approval]
        /
        (
            [Measures].[Gross Approval],
            [Dim Project Geography].[Project County].DefaultMember,
            Exists(
                [Dim Project Geography].[Project State].[Project State].Members,
                [Dim Project Geography].[Project County].CurrentMember
            ).Item(0)
        )
    )
),
FORMAT_STRING = "#,##0.00%;-#,##0.00%",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;

/* ---------- Q15: CHGOFF theo ngành so với baseline cohort FY ---------- */
CREATE MEMBER CURRENTCUBE.[Measures].[CHGOFF Record Count]
 AS (
    [Measures].[Record Count],
    [Dim Loan Status].[Raw Status].&[CHGOFF]
),
FORMAT_STRING = "#,##0;-#,##0",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;

CREATE MEMBER CURRENTCUBE.[Measures].[CHGOFF Gross Charge Off]
 AS (
    [Measures].[Gross Charge Off Amount],
    [Dim Loan Status].[Raw Status].&[CHGOFF]
),
FORMAT_STRING = "#,##0.00;-#,##0.00",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;

/* Tỷ lệ CHGOFF quan sát = số bản ghi CHGOFF / tổng bản ghi (mọi trạng thái) */
CREATE MEMBER CURRENTCUBE.[Measures].[CHGOFF Share]
 AS IIF(
    IsEmpty([Measures].[Record Count])
    OR [Measures].[Record Count] = 0,
    NULL,
    [Measures].[CHGOFF Record Count]
    / [Measures].[Record Count]
),
FORMAT_STRING = "#,##0.00%;-#,##0.00%",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;

/* Baseline = tỷ lệ CHGOFF của cả cohort (bỏ mọi lọc ngành, giữ FY) */
CREATE MEMBER CURRENTCUBE.[Measures].[CHGOFF Baseline]
 AS (
    [Measures].[CHGOFF Share],
    Root([Dim Industry])
),
FORMAT_STRING = "#,##0.00%;-#,##0.00%",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;

/* Eligible = 1 khi ngành có >= 30 bản ghi, >= 5 CHGOFF và tỷ lệ > baseline (gates 30/5) */
CREATE MEMBER CURRENTCUBE.[Measures].[Q15 Eligible]
 AS IIF(
    IsEmpty([Measures].[Record Count]),
    NULL,
    IIF(
        [Measures].[Record Count] >= 30
        AND [Measures].[CHGOFF Record Count] >= 5
        AND [Measures].[CHGOFF Share] > [Measures].[CHGOFF Baseline],
        1,
        0
    )
),
FORMAT_STRING = "0",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;

/* % tiền xóa nợ của bang trong ngành đang xét */
CREATE MEMBER CURRENTCUBE.[Measures].[CHGOFF Amount Share in Sector]
 AS IIF(
    IsEmpty(
        (
            [Measures].[CHGOFF Gross Charge Off],
            [Dim Project Geography].[Project Geography].DefaultMember
        )
    )
    OR
    (
        [Measures].[CHGOFF Gross Charge Off],
        [Dim Project Geography].[Project Geography].DefaultMember
    ) = 0,
    NULL,
    [Measures].[CHGOFF Gross Charge Off]
    /
    (
        [Measures].[CHGOFF Gross Charge Off],
        [Dim Project Geography].[Project Geography].DefaultMember
    )
),
FORMAT_STRING = "#,##0.00%;-#,##0.00%",
VISIBLE = 1 ,  ASSOCIATED_MEASURE_GROUP = 'Fact Loan'  ;
```

5. Bấm **Check Syntax**: nút có dấu tick (✓) trên thanh công cụ của tab.
   - Phải báo *"The syntax is correct"*.
6. `Ctrl + S` để lưu.
7. Chuột phải project **SBA7A_SSAS** trong Solution Explorer → **Deploy**.
   - Chờ báo *Deploy Succeeded*.
   - Chỉ đổi calculation thì không cần process lại dữ liệu.
8. **Kiểm tra trong SSMS:**
   - Kết nối *Analysis Services* → chuột phải database `SBA7A_SSAS` → **New Query → MDX**.
   - Dán câu dưới đây → **Execute**:

```mdx
SELECT
  { [Measures].[Record Count], [Measures].[CHGOFF Record Count], [Measures].[CHGOFF Share],
    [Measures].[CHGOFF Baseline], [Measures].[Q15 Eligible], [Measures].[CHGOFF Gross Charge Off] } ON COLUMNS,
  NON EMPTY [Dim Industry].[Naics Sector Name].[Naics Sector Name].Members ON ROWS
FROM [SBA7A DWH_DSV]
WHERE ( [Dim Date].[Fiscal Year].&[2025] );
```

   - Mọi dòng phải có Baseline 0.11%, và 3 ngành Retail Trade, Construction, Manufacturing có Eligible = 1.

> Nếu Check Syntax báo lỗi ở `.&[CHGOFF]`: mở **Browser** của cube, kéo `Dim Loan Status → Raw Status` ra xem đúng tên thành viên, rồi sửa key trong file cho khớp.

---

## Phần 1 – Kết nối Power BI vào cube

1. Mở **Power BI Desktop** → **Blank report** (Báo cáo trống).
2. Tab **Home → Get data → More…**.
   - Gõ `Analysis Services` vào ô tìm kiếm → chọn **SQL Server Analysis Services database** → **Connect**.
3. Điền:
   - **Server**: `localhost`. Nếu SSAS cài dạng named instance thì ghi `localhost\TÊN_INSTANCE`; tên này giống tên server dùng khi deploy cube và khi kết nối SSMS.
   - **Database**: `SBA7A_SSAS`.
   - Tích **Connect live** → **OK**.
   - Nếu hỏi đăng nhập: chọn **Windows → Use my current credentials** → **Connect**.
4. Cửa sổ **Navigator**: tích cube **`SBA7A DWH_DSV`** → **OK**.
5. Panel **Data** bên phải hiện các bảng:
   - `Fact Loan` chứa các measure, có cả 8 measure mới.
   - Các dimension `Dim Date`, `Dim Project Geography`, `Dim Industry`, `Dim Loan Status`, …
   - Bấm mũi tên ▸ để mở xem cho người xem thấy.
6. **File → Save as** → đặt tên `SBA7A_Chuong4_PowerBI.pbix`.

**Thao tác chung dùng nhiều lần**

| Việc | Cách làm |
|---|---|
| Đổi tên cột/trục trên visual | Ở panel *Visualizations*, ô field → bấm mũi tên ▾ bên phải tên field → **Rename for this visual** → gõ tên → Enter. |
| Đổi tên trang | Nhấp đúp vào tab trang ở dưới cùng → gõ tên → Enter. |
| Thêm tiêu đề | **Insert → Text box** → gõ nội dung → bôi đen → chỉnh cỡ chữ 18, **B** đậm. |
| Mở phần định dạng visual | Chọn visual → *Visualizations* → icon **cọ vẽ** (*Format your visual*). |
| Filter trên 1 visual | Chọn visual → panel **Filters** → mục **Filters on this visual** → kéo field vào ô *Add data fields here*. |

---

## Phần 2 – Trang Q6 (YoY)

### 2.1. Trang và tiêu đề
1. Đổi tên `Page 1` thành `Q6 – Tăng trưởng YoY`.
2. **Insert → Text box**: `Báo biểu Q6 – Tăng trưởng vốn phê duyệt SBA 7(a) theo năm tài chính (YoY), FY2021–FY2025`.

### 2.2. Biểu đồ cột + đường
1. Bấm vào vùng trống của trang → panel *Visualizations* → icon **Line and clustered column chart**: cột kèm đường gấp khúc, hàng đầu.
   - Kéo khung chart to ra khoảng 2/3 chiều ngang trang.
2. Panel **Data** → `Dim Date` → mở hierarchy **`Fiscal Date`** → kéo **chỉ level `Fiscal Year`** vào ô **X-axis**.
   - **Bắt buộc** dùng level trong hierarchy `Fiscal Date`, không dùng attribute `Fiscal Year` rời. YoY trong cube tính bằng `Fiscal Date.CurrentMember.PrevMember`, nên với field rời nó sẽ trống.
   - Nếu lỡ kéo cả hierarchy, ô X-axis sẽ có 4 dòng (Fiscal Year, Fiscal Quarter, Fiscal Month, Date). Bấm ✕ xóa 3 dòng dưới, chỉ giữ Fiscal Year.
3. `Fact Loan` → kéo **`Gross Approval`** vào **Column y-axis**.
4. Kéo **`YoY Gross Approval Growth`** vào **Line y-axis**.
5. **Lọc FY2021–FY2025**:
   - Panel **Filters → Filters on this visual** → kéo measure **`Q6 In Scope`** vào *Add data fields here*.
   - **Show items when the value**: `is` → gõ `1` → **Apply filter**.
   - Chart còn đúng 5 năm, 2021–2025.
   - **Không** lọc bằng Fiscal Year. Lọc năm sẽ cắt mất FY2020 nên YoY của FY2021 bị trống. `Q6 In Scope` chỉ ẩn dòng, FY2020 vẫn còn để tính.
6. **Sắp xếp**: bấm **…** (More options, góc trên phải chart) → **Sort axis → Fiscal Year** → lại **…** → **Sort axis → Sort ascending**.
7. **Đổi tên** bằng ▾ → *Rename for this visual*:
   - `Fiscal Year` → `Năm tài chính`
   - `Gross Approval` → `Tổng vốn phê duyệt (USD)`
   - `YoY Gross Approval Growth` → `YoY (%)`
8. **Định dạng** (icon cọ vẽ → tab **Visual**):
   - **Data labels** → On.
     - Trong *Apply settings to → Series*, chọn `Tổng vốn phê duyệt (USD)` và tắt *Show for this series*, để số tiền không đè lên cột. Chỉ giữ nhãn cho `YoY (%)`.
   - **Y-axis** → *Range → Minimum* `0`.
   - Tab **General → Title** → Text: `Tổng vốn phê duyệt và YoY theo năm tài chính`.
9. **Kiểm tra**: rê chuột vào cột FY2021, tooltip phải ra YoY 62.03%. FY2022 phải là −29.68%.

### 2.3. Bảng chi tiết
1. Bấm vùng trống → icon **Table**. Đặt bên phải hoặc bên dưới chart.
2. Ô **Columns**, kéo lần lượt:
   - `Fiscal Date` → level `Fiscal Year`, cũng chỉ level này.
   - `Gross Approval`
   - `Prior FY Gross Approval`
   - `YoY Gross Approval Growth`
3. Lọc giống chart: Filters on this visual → `Q6 In Scope` is `1` → Apply filter.
4. Đổi tên:
   - `Năm tài chính`
   - `Tổng vốn phê duyệt (USD)`
   - `Vốn năm trước (USD)`
   - `YoY (%)`
5. Bấm vào tiêu đề cột `Năm tài chính` để sắp xếp tăng dần.
6. Cọ vẽ → **Totals** → Off: không có dòng tổng, vì cộng YoY là vô nghĩa.
7. **Kiểm tra**: dòng FY2021 có `Vốn năm trước` = 22,549,825,700, tức tổng của FY2020.

### 2.4. Ghi chú
**Insert → Text box**, chữ cỡ 10:
`YoY = (Vốn năm t − Vốn năm t−1) / Vốn năm t−1, tính bằng calculated member trong cube SSAS (PrevMember trên hierarchy Fiscal Date). FY2020 chỉ là năm gốc; FY2026 chưa đủ năm (dữ liệu đến 30/06/2026) nên không đưa vào. Nguồn: cube SBA7A DWH_DSV, giữ cả bản ghi trùng (BR-POP-01).`

---

## Phần 3 – Trang Q8 (tỷ trọng theo bang + Top 3 county + Matrix Grouping and Totals)

### 3.1. Trang mới
1. Bấm **+** cạnh tab trang ở dưới cùng → đổi tên `Q8 – Tỷ trọng theo bang`.
2. Text box: `Báo biểu Q8 – Tỷ trọng vốn phê duyệt của từng bang theo năm tài chính và Top 3 county của bang được chọn`.

### 3.2. Slicer năm
1. Bấm vùng trống → icon **Slicer** (hình phễu có vạch).
2. Kéo `Dim Date` → attribute **`Fiscal Year`** (field rời là được, Q8 không dùng PrevMember) vào ô **Field**.
3. Cọ vẽ → **Visual → Slicer settings**:
   - **Options → Style**: `Dropdown`.
   - **Selection → Single select**: On.
4. Mở dropdown → chọn **2025**.
5. Đổi tên field thành `Năm tài chính`. Tiêu đề slicer sẽ đổi theo.

### 3.3. Bảng Top 10 bang
1. Icon **Table**.
2. Ô **Columns**: kéo `Dim Project Geography` → **`Project State`**, rồi `Gross Approval`, `State Approval Share`.
3. Filters on this visual → bấm thẻ **Project State** đã có sẵn ở đó:
   - **Filter type**: `Top N`
   - **Show items**: `Top` · `10`
   - **By value**: kéo `Gross Approval` vào ô này
   - **Apply filter**
4. Bấm tiêu đề cột `Gross Approval` cho mũi tên chỉ xuống, tức sắp xếp giảm dần.
5. Đổi tên:
   - `Bang`
   - `Tổng vốn (USD)`
   - `Tỷ trọng (%)`
6. **Kiểm tra** FY2025: dòng đầu CA 12.90%, rồi TX 10.91%, FL 8.65%.
   - `State Approval Share` chia vốn của bang cho vốn **toàn quốc cùng năm**, nên đổi năm thì tỷ trọng tự tính lại.

### 3.4. Biểu đồ (tùy chọn: bản đồ hoặc cột)
- **Cách đơn giản, chắc chắn chạy**:
  1. Icon **Clustered bar chart**.
  2. Y-axis `Project State`, X-axis `State Approval Share`.
  3. Filter Top N 10 như 3.3.
  4. Đổi tên trục giống bảng.
- **Bản đồ**:
  1. Icon **Filled map**.
     - Nếu icon bị mờ hoặc báo lỗi: **File → Options and settings → Options → Security → tích "Use Map and Filled Map visuals"** → OK.
  2. Location: `Project State`. Tooltips: `Gross Approval`, `State Approval Share`.
  3. Nếu bản đồ đặt sai chỗ (ví dụ "CA" thành Canada, "GA" thành nước khác) thì xóa map và dùng bar chart ở trên. Live connection không cho đặt *Data category = State*.

### 3.5. Slicer bang
1. Thêm **Slicer** thứ hai → field `Project State`.
   - Style `Dropdown`, **Single select** On.
   - Chọn **CA**.
   - Đổi tên `Bang`.
2. **Slicer bang không được lọc bảng Top 10, bar chart và map:**
   - Chọn slicer `Bang` → trên ribbon bấm tab **Format** → **Edit interactions**.
   - Trên bảng Top 10, bar chart và map, mỗi visual hiện 2 icon nhỏ ở góc trên. Bấm icon **None** (vòng tròn gạch chéo) trên từng visual.
   - Bấm lại **Edit interactions** để tắt chế độ này.

### 3.6. Bảng Top 3 county
1. Icon **Table**.
   - Columns: `Project County`, `Gross Approval`, `County Share in State`.
2. Filters on this visual → thẻ **Project County**:
   - Filter type `Top N`
   - Top `3`
   - By value `Gross Approval`
   - Apply filter
3. Sắp xếp `Gross Approval` giảm dần.
4. Đổi tên:
   - `Quận (County)`
   - `Tổng vốn (USD)`
   - `% trong bang`
5. Cọ vẽ → **General → Title** → On → Text: `Top 3 county của bang được chọn`.
6. **Kiểm tra** với 2025 và CA:
   - LOS ANGELES 30.30%
   - ORANGE 11.36%
   - SAN DIEGO 10.18%
   - Đổi slicer bang sang TX thì bảng phải đổi theo.

### 3.7. Matrix Grouping and Totals (Bang → County, có tổng phụ và tổng cộng)

Đây là report dạng **Grouping and Totals**: nhóm theo bang, mỗi bang có dòng tổng phụ, cuối bảng có tổng cộng. Matrix chỉ chịu lọc của slicer năm.

1. Nới trang nếu chật: bấm vùng trống → cọ vẽ (*Format your report page*) → **Canvas settings** → **Type**: `Custom` → **Height**: `1300`.
2. Bấm vùng trống → panel *Visualizations* → icon **Matrix**: lưới có ô tô đậm, nằm cạnh icon Table. Đặt ở phần dưới trang.
3. Ô **Rows**: kéo `Dim Project Geography` → **`Project State`**, rồi kéo **`Project County`** vào ngay dưới.
   - Đây là phần **grouping**: county nằm trong nhóm bang.
   - Kéo cả hierarchy `Project Geography` vào cũng được, Power BI tự thêm 2 level.
4. Ô **Values**: kéo `Gross Approval`, rồi `Record Count`.
5. Đổi tên (▾ → Rename for this visual):
   - `Bang`
   - `Quận (County)`
   - `Tổng vốn (USD)`
   - `Số bản ghi`
6. **Mở county ra**: trên header của matrix (rê chuột vào visual), bấm icon **mũi tên rẽ nhánh xuống** (*Expand all down one level in the hierarchy*). Mỗi bang hiện danh sách county bên dưới.
7. **Bật tổng** (cọ vẽ → tab **Visual**):
   - **Row subtotals** → On.
     - Trong thẻ này, mục *Rows* → **Show subtotal for**: `All` (hoặc chọn level `Bang`).
     - **Subtotal label**: `Tổng`.
   - **Layout and style presets → Layout**: `Outline` hoặc `Tabular` để tên bang và county nằm ở 2 cột riêng. Dòng tổng của mỗi bang hiện ngay dưới các county của bang đó.
   - Dòng **Total** ở cuối là tổng cộng cả nước, tức grand total.
8. Sắp xếp: bấm tiêu đề cột `Tổng vốn (USD)` cho mũi tên chỉ xuống. Bang và county trong từng bang đều xếp giảm dần.
9. **Slicer bang không được lọc matrix**:
   - Chọn slicer `Bang` → **Format → Edit interactions** → trên matrix bấm **None**.
   - Slicer năm giữ **Filter** (mặc định).
10. Cọ vẽ → **General → Title** → `Tổng vốn theo bang và county (tổng phụ từng bang, tổng cộng cả nước)`.
11. **Kiểm tra** FY2025:
    - Dòng tổng của CA = **4,808,747,400**, TX = 4,067,228,500.
    - Dòng **Total** cuối = **37,287,816,200**, bằng tổng vốn FY2025 ở trang Q6.
    - Mở CA: LOS ANGELES 1,457,139,100, ORANGE 546,312,500, SAN DIEGO 489,766,900 đứng đầu.
12. Ghi chú: Top N trên Matrix tính trên toàn bảng, không tính theo từng bang. Vì vậy matrix hiện đủ county; còn Top 3 county theo bang xem ở bảng 3.6.

### 3.8. Ghi chú
Text box: `Tỷ trọng = vốn phê duyệt của bang / tổng vốn toàn quốc trong cùng năm tài chính (calculated member State Approval Share trong cube). % trong bang = vốn county / vốn của bang chứa county đó. Nguồn: cube SBA7A DWH_DSV, BR-POP-01.`

---

## Phần 4 – Trang Q15 (ngành CHGOFF cao hơn baseline + Top 3 bang)

### 4.0. Hiểu trước (không cần quay)
Trong từng năm tài chính (cohort FY):
1. **Tỷ lệ CHGOFF của ngành** = số bản ghi CHGOFF của ngành / tổng bản ghi của ngành.
2. **Baseline** = tỷ lệ CHGOFF của cả năm, tính trên mọi ngành.
3. Ngành **Eligible** khi đồng thời thỏa:
   - có ≥ 30 bản ghi
   - có ≥ 5 CHGOFF
   - tỷ lệ > baseline
4. Xếp hạng các ngành Eligible theo **tiền xóa nợ** (Gross Charge Off trên bản ghi CHGOFF). Với ngành được chọn, tìm **Top 3 bang** đóng góp tiền xóa nợ.

Cả 4 bước đã nằm trong cube:
- `CHGOFF Record Count`
- `CHGOFF Share`
- `CHGOFF Baseline`
- `Q15 Eligible`
- `CHGOFF Gross Charge Off`
- `CHGOFF Amount Share in Sector`

Khác Looker: Power BI lọc được trên measure, nên bảng ngành chỉ cần filter `Q15 Eligible = 1`.

### 4.1. Trang mới
1. **+** → đổi tên `Q15 – CHGOFF theo ngành`.
2. Text box: `Báo biểu Q15 – Ngành có tỷ lệ CHGOFF cao hơn baseline và Top 3 bang đóng góp tiền xóa nợ`.

### 4.2. Slicer năm
1. **Slicer** → field `Dim Date` → `Fiscal Year`.
   - Style `Dropdown`, **Single select** On.
   - Chọn **2025**.
   - Đổi tên `Năm tài chính`.
2. Bắt buộc single select vì Q15 tính riêng từng cohort FY.

### 4.3. Bảng ngành
1. Icon **Table**. Columns, theo thứ tự:
   - `Dim Industry` → **`Naics Sector Name`**
   - `Record Count`
   - `CHGOFF Record Count`
   - `CHGOFF Share`
   - `CHGOFF Baseline`
   - `Q15 Eligible`
   - `CHGOFF Gross Charge Off`
2. **Kiểm tra trước khi lọc**: cột `CHGOFF Baseline` phải là **0.11% ở mọi dòng**.
3. Filters on this visual → kéo **`Q15 Eligible`** vào → *Show items when the value* `is` `1` → **Apply filter**.
4. Bấm tiêu đề cột `CHGOFF Gross Charge Off` cho mũi tên chỉ xuống, tức sắp xếp giảm dần.
5. Đổi tên:

   | Field | Tên hiển thị |
   |---|---|
   | Naics Sector Name | `Ngành (NAICS)` |
   | Record Count | `Số bản ghi` |
   | CHGOFF Record Count | `Số CHGOFF` |
   | CHGOFF Share | `Tỷ lệ CHGOFF (%)` |
   | CHGOFF Baseline | `Baseline (%)` |
   | Q15 Eligible | `Eligible` |
   | CHGOFF Gross Charge Off | `Tiền xóa nợ (USD)` |

6. Cọ vẽ → **General → Title** → `Ngành vượt baseline (≥ 30 bản ghi, ≥ 5 CHGOFF), xếp theo tiền xóa nợ`.
7. **Kiểm tra** FY2025, đúng 3 dòng theo thứ tự:
   - Retail Trade 1,913,417.62
   - Construction 1,374,155.58
   - Manufacturing 659,110.94

### 4.4. Slicer ngành
1. **Slicer** → field `Naics Sector Name`.
   - Style `Dropdown`, **Single select** On.
   - Chọn **Retail Trade**.
   - Đổi tên `Ngành`.
2. Slicer ngành **không được lọc bảng ngành**:
   - Chọn slicer → **Format → Edit interactions** → trên bảng ngành bấm **None**.
   - Tắt Edit interactions.

### 4.5. Bảng Top 3 bang
1. Icon **Table** → Columns:
   - `Project State`
   - `CHGOFF Gross Charge Off`
   - `CHGOFF Amount Share in Sector`
2. Filters on this visual → thẻ **Project State**:
   - `Top N`
   - Top `3`
   - By value `CHGOFF Gross Charge Off`
   - Apply filter
3. Sắp xếp `CHGOFF Gross Charge Off` giảm dần.
4. Đổi tên:
   - `Bang`
   - `Tiền xóa nợ (USD)`
   - `% trong ngành`
5. Title: `Top 3 bang đóng góp tiền xóa nợ của ngành được chọn`.
6. **Kiểm tra** FY2025 + Retail Trade:
   - CA 47.00%
   - AL 27.40%
   - TN 10.38%
7. Lưu ý khi demo: chỉ chọn ngành đang có trong bảng ngành, tức Eligible = 1.
   - Có thể bấm thẳng một dòng trong bảng ngành, bảng bang sẽ lọc theo ngành đó.
   - Bấm lại dòng đó để bỏ chọn.

### 4.6. Ghi chú
Text box: `Q15 (exploratory). Tỷ lệ CHGOFF = số bản ghi CHGOFF / tổng bản ghi của ngành trong FY; Baseline = tỷ lệ CHGOFF của cả FY. Eligible = 1 khi ngành có ≥ 30 bản ghi, ≥ 5 CHGOFF và tỷ lệ > baseline; ngành Eligible xếp theo tiền xóa nợ trên bản ghi CHGOFF. Đây là tỷ lệ quan sát, không phải xác suất vỡ nợ. NAICS mapping còn PENDING_VERIFICATION. Nguồn: cube SBA7A DWH_DSV, BR-POP-01.`

---

## Phần 5 – Lưu và chụp
1. `Ctrl + S`.
   - File `.pbix` live không chứa dữ liệu, chỉ chứa kết nối. Muốn mở lại phải nối được tới SSAS.
2. Chụp từng trang đưa vào báo cáo Chương 4: **File → Export → Export to PDF**, hoặc chụp màn hình.
3. Gửi file `.pbix` và file PDF cho nhóm. Nhóm sẽ để vào thư mục `dashboards/` của repo.

## Lỗi hay gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Không thấy các measure mới (`Q6 In Scope`, `CHGOFF …`) | Cube chưa deploy bản mới. Làm lại Phần 0, rồi trong Power BI bấm **Home → Refresh**. |
| YoY / Vốn năm trước trống | X-axis đang dùng attribute `Fiscal Year` rời. Phải dùng level `Fiscal Year` **trong hierarchy `Fiscal Date`**. |
| FY2021 YoY trống dù đã dùng đúng level | Đang lọc bằng năm. Bỏ filter năm, chỉ dùng filter `Q6 In Scope is 1`. |
| Top 3 county ra số cả nước hoặc trộn nhiều bang | Slicer bang chưa chọn giá trị nào. Chọn CA. |
| Bảng Top 10 chỉ còn 1 bang | Slicer bang đang lọc bảng. Edit interactions → None. |
| Baseline mỗi dòng một số | Measure `CHGOFF Baseline` sai; kiểm tra lại đoạn `Root([Dim Industry])` trong script cube. |
| Bảng ngành trống | Slicer ngành đang lọc bảng ngành (Edit interactions → None), hoặc slicer năm chưa chọn. |
| Không có "Rename" khi bấm chuột phải field ở panel Data | Live connection không cho đổi tên trong model. Đổi tên trong ô field của visual (▾ → Rename for this visual). |
