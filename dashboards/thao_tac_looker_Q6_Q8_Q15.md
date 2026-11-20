# Thao tác chi tiết – Looker Studio Q6, Q8 & Q15

Từng bước bấm, đã chạy thử trên giao diện Looker Studio hiện tại (11/2026). Không có lời thoại.

Số đúng để đối chiếu:
- **Q6, YoY:** FY2021 62.03% · FY2022 −29.68% · FY2023 7.09% · FY2024 13.11% · FY2025 19.8%
- **Q8, FY2025:** CA 12.9% · TX 10.91% · FL 8.65% · NY 4.92% · GA 4.1%
- **Top 3 county năm FY2025:**
  - CA: LOS ANGELES 30.3% · ORANGE 11.36% · SAN DIEGO 10.18%
  - TX: HARRIS 16.64% · DALLAS 12.45% · TARRANT 8.99%
- **Pivot Grouping and Totals (Q8, FY2025):** CA Total (57) 4,808,747,400 · TX Total (172) 4,067,228,500 · Grand total 37,287,816,200
- **Q15, FY2025:** baseline 0.11% (85 CHGOFF / 78,078 bản ghi); 3 ngành Eligible: Retail Trade 1,913,418 USD · Construction 1,374,156 · Manufacturing 659,111

---

## Làm quen giao diện (đọc trước, không cần quay)

Trong màn hình sửa report:

- **Thanh công cụ trên cùng:** `Add data` · `Blend` · `Add a chart ▾` · `Add a control ▾` · `Theme and layout`. Menu chữ: `File  Edit  View  Insert  Page  Arrange  Resource  Help`.
- **Cột phải thứ nhất (Properties):** thuộc tính của chart đang chọn, có 2 tab `Setup` và `Style`.
- **Cột phải ngoài cùng (Data):** danh sách field của data source. Cách nhanh nhất để đưa field vào chart là **kéo field từ đây thả vào ô `Add dimension` / `Add metric`**.
- **Mỗi field trong chart hiện thành một ô màu** (xanh lá là dimension, xanh dương là metric). Có 2 vùng bấm khác nhau:
  - Bấm **vào chữ tên field**: mở danh sách để **đổi sang field khác**.
  - Bấm **vào icon nhỏ bên trái** (`ABC`, `123`, `SUM`, hoặc hình bút chì khi rê chuột): mở **bảng cài đặt** gồm Display name, Data type, Aggregation, Comparison calculation.
  - Rê chuột vào ô sẽ hiện dấu **✕** bên phải để xóa field.
- **Lưu ý:**
  - Kéo field thả lên một ô đã có sẵn thì Looker **chèn thêm** field mới chứ không thay thế. Muốn thay thì bấm vào tên field, hoặc xóa ô cũ bằng ✕.
  - Ngay trong chế độ sửa, **bấm vào một dòng của bảng là bảng lọc chéo** (cross-filter): trên thanh trên cùng hiện thêm thẻ kiểu `ProjectCounty: ORANGE`. Bấm nút **`Reset`** ở góc trên phải vùng vẽ để bỏ lọc.

---

## Phần 0 – Xuất dữ liệu

Chạy trong terminal ở thư mục repo:

```bash
python3 -m src.reporting.export_bi_dataset
```

Kết quả là file `data/processed/bi/sba7a_bi_dataset.csv` (≈ 64 MB, 388,338 dòng).

---

## Phần 1 – Tạo data source

1. Mở https://lookerstudio.google.com → bấm **`+ Create`** (góc trên trái) → **`Data source`**.
2. Ô tìm connector: gõ `File` → chọn **`File Upload`** (Google Connector).
3. Kéo file `sba7a_bi_dataset.csv` vào khung upload (hoặc bấm **`Click to upload files`** rồi chọn file). Đợi dòng file hiện dấu ✓ xanh.
4. Bấm vào tên `Untitled Data Source` ở góc trên trái → gõ **`SBA7A_BI_DATASET`** → Enter.
5. Bấm **`CONNECT`** (góc trên phải). Màn hình chuyển sang danh sách 16 field.

### 1.1. Tạo 3 trường tính toán ngay tại màn hình data source

Phải tạo ở đây, không tạo trong report. Khi tạo trong report, công thức gõ `ProjectState` bị báo *Unknown dimension or metric id* vì ID nội bộ của field khác tên hiển thị.

Lặp lại 3 lần, mỗi lần cho một field trong bảng bên dưới:

1. Bấm **`Add a field`** (thanh trên danh sách field) → **`Add calculated field`**.
2. Ô **Field Name**: gõ tên field.
3. Click vào khung **Formula** → gõ công thức.
   - Khi gõ `(`, Looker tự thêm `)`. Gõ tiếp nội dung bên trong, không cần gõ dấu `)` cuối.
   - Khi gõ đúng tên field, chữ đó được tô nền xanh.
   - Nếu có popup gợi ý che mất ô, nhấn `Esc`.
4. Đợi dòng dưới khung công thức hết vòng xoay và không báo lỗi → bấm **`Save`** → đợi thông báo *Calculated field saved* ở góc dưới trái → bấm **`Close`**.

| Field Name | Formula |
|---|---|
| `FY` | `CONCAT("FY", CAST(FiscalYear AS TEXT))` |
| `FY_Next` | `CONCAT("FY", CAST(FiscalYear + 1 AS TEXT))` |
| `StateGeo` | `CONCAT("US-", ProjectState)` |

### 1.2. Đổi kiểu cho StateGeo

1. Trong danh sách field, tìm dòng **`StateGeo`** → bấm mũi tên ▾ ở cột **Type** (đang ghi `Text`).
2. Rê chuột vào **`Geo`** → chọn **`Country subdivision (1st level)`**.
3. Hộp thoại *"You are changing StateGeo from Text to Country subdivision (1st level)"* hiện ra → bấm **`CONTINUE`**.
4. Cột Type của StateGeo giờ có icon quả địa cầu.

### 1.3. Tạo report

1. Bấm **`Create Report`** (góc trên phải) → nếu hỏi *Add data to report*, bấm **`Add to report`**.
2. Bấm vào tên `Untitled Report` (góc trên trái) → gõ `SBA 7(a) - Chương 4 - Báo biểu Q6, Q8 & Q15`.
3. Trên trang 1, Looker có thể tự thêm sẵn một bảng: click chọn nó → nhấn `Delete`.

---

## Phần 2 – Trang Q6 (YoY)

### 2.1. Tạo blend

1. Bấm **`Blend`** trên thanh công cụ. Cách khác: **Resource → Manage blends → ADD A BLEND**.
2. **Bảng bên trái**, data source `SBA7A_BI_DATASET`:
   - Ô Dimensions: thêm **`FY`**.
   - Ô Metrics: thêm **`GrossApproval`**.
   - Bấm vào tên bảng ở đầu cột → đặt tên `Năm hiện tại`.
3. Bấm ô **`Merge another table`** (bên phải bảng 1) → chọn lại **`SBA7A_BI_DATASET`**. Looker tự chép các dimension của bảng 1 sang bảng 2 – xóa hết bằng ✕ rồi thêm lại đúng field bên dưới:
   - Dimensions: **`FY_Next`**.
   - Metrics: **`GrossApproval`** → bấm vào ô metric này → ô tên, đổi thành **`PriorFYGross`** → đóng popup.
   - Đặt tên bảng: `Năm trước`.
4. Bấm vào ô nối giữa 2 bảng (ghi *Configure merge*), hộp *Merge configuration* hiện ra:
   - Merge operator: **`Left outer`**.
   - Merge conditions: bên trái chọn **`FY`**, bên phải chọn **`FY_Next`** → **`Apply`**.
   - Bấm **`Save`**.
5. Ô **Blend name** ở dưới cùng: gõ `Blend_YoY_FY` → bấm **`Save`** (góc dưới phải) → **`Close`**.
6. Panel Data bên phải giờ có thêm nguồn `Blend_YoY_FY` với các field FY, GrossApproval, PriorFYGross.

### 2.2. Tiêu đề

1. **Insert → Text** (hoặc icon **`T`** trên thanh công cụ) → kéo một khung ở đầu trang.
2. Gõ `Báo biểu Q6 – Tăng trưởng vốn phê duyệt SBA 7(a) theo năm tài chính (YoY)`.
3. Panel bên phải: Font size 22, bấm **B** (đậm).

### 2.3. Biểu đồ combo

1. **`Add a chart ▾`** → kéo danh sách xuống nhóm **Line** (ngay dưới nhóm Pie / Google Maps / Geo chart) → chọn icon có **cột + đường** (rê chuột vào hiện tên *Combo chart*; đừng chọn *Stacked combo chart*) → click vào vùng trống dưới tiêu đề để đặt.
   - Không thấy thì dùng cách thay thế: chọn **Column chart** ở nhóm **Bar**, rồi ở bước Style bên dưới đổi **Series #2** từ Bars sang **Line** – kết quả y hệt.
2. Panel **Setup**:
   1. **Data source**: bấm vào ô data source → chọn **`Blend_YoY_FY`**.
   2. **Dimension**: bấm vào tên field đang có → chọn **`FY`**.
   3. **Metric**: giữ một ô **`GrossApproval`**, xóa các metric thừa bằng ✕.
   4. Bấm vào icon trái của ô GrossApproval → **Display name**: `Tổng vốn phê duyệt (USD)` → nhấn `Esc`.
   5. Tạo metric YoY:
      - Bấm **`Add metric`** → cuối danh sách bấm **`Add calculated field`**.
      - Name: `YoY (%)`.
      - Formula: `(SUM(GrossApproval) - SUM(PriorFYGross)) / SUM(PriorFYGross)` → **`Apply`**.
   6. Bấm icon trái của ô `YoY (%)` → **Data type**: chọn **`Numeric` → `Percent`** → `Esc`.
      - Phải đổi ở *Data type*. Chỉ đổi *Display format* thì số hiện 0.62% thay vì 62%.
   7. **Sort**: chọn `FY`, **Ascending**.
   8. Lọc 5 năm:
      - **Filter → `Add filter` → `Create a filter`**.
      - Tên filter: `FY 2021-2025`.
      - Chọn **Include** → field **`FY`** → điều kiện **`RegExp Match`** → giá trị `FY202[1-5]`.
      - Bấm **`Save`**.
3. Panel **Style**:
   - Mục **Series #1** (Tổng vốn): ô chọn kiểu phải là **Bars**.
   - Mục **Series #2** (YoY): ô chọn kiểu là **Line**; tick **Show points** và **Show data labels**.
   - **Trục phải cho YoY** (bắt buộc, nếu không đường YoY nằm sát đáy vì % nhỏ hơn hàng tỷ USD rất nhiều): trong mục Series #2 tìm chữ **Axis** với 2 lựa chọn **Left / Right** → chọn **Right**. Nếu mục Series đang thu gọn thì bấm vào tiêu đề *Series #2* để mở. Ở combo chart Looker thường đã để sẵn đường trên trục phải – nhìn chart thấy có 2 trục số (trái: tiền, phải: %) là được, không cần chỉnh.
   - Mục **Left Y-Axis** (nếu có): Axis min = `0`. Không có thì bỏ qua.
   - **Chart title**: bật **Show title** → gõ `Tổng vốn phê duyệt và tăng trưởng YoY theo năm tài chính (FY2021–FY2025)`.
4. Kéo các góc chart cho rộng. Rê chuột vào điểm FY2021 để kiểm tra: 62.03%.

### 2.4. Bảng chi tiết

1. **`Add a chart ▾` → `Table`** (ô đầu tiên) → click vùng trống dưới combo chart.
2. Setup:
   - Data source: **`Blend_YoY_FY`**.
   - Dimension: **`FY`**, icon trái → Display name `Năm tài chính`.
   - Metric:
     - **`GrossApproval`** → Display name `Tổng vốn phê duyệt (USD)`.
     - **`PriorFYGross`** → Display name `Vốn năm trước (USD)`.
     - `YoY (%)`: tạo lại bằng Add metric → Add calculated field, cùng công thức, rồi đổi **Data type → Percent**. Field tạo trong chart chỉ dùng được ở chart đó.
   - Filter: **`Add filter`** → chọn filter có sẵn **`FY 2021-2025`**.
   - Sort: `FY` Ascending.

### 2.5. Ghi chú và đổi tên trang

1. **Insert → Text** ở cuối trang, gõ:
   `Nguồn: SBA7A_DWH (388,338 bản ghi, giữ cả bản trùng – BR-POP-01). YoY = (Tổng vốn FY − Tổng vốn FY trước) / Tổng vốn FY trước. FY2020 chỉ dùng làm năm gốc; FY2026 bị loại vì chưa đủ năm (dữ liệu đến 30/06/2026).`
2. **Page → Manage pages** → rê chuột vào dòng trang 1 → bấm **⋮** → **Rename** → `Q6 – YoY` → Enter → đóng.

---

## Phần 3 – Trang Q8 (tỷ trọng theo bang + Top 3 county + bảng Grouping and Totals)

Thứ tự làm đúng như dưới đây: bản đồ và bảng Top 10 trước, nhóm "drop-down bang + bảng county" sau cùng, rồi group và tải lại trang.

### 3.1. Trang mới và tiêu đề

1. **Page → New page**. Thanh trang bên trái hiện số **2**.
2. **Page → Manage pages** → đổi tên trang 2 thành `Q8 – Tỷ trọng theo bang`.
3. **Insert → Text**: `Báo biểu Q8 – Tỷ trọng vốn phê duyệt SBA 7(a) theo bang trong từng năm tài chính`.

### 3.2. Drop-down chọn năm (áp cho cả trang)

1. **`Add a control ▾` → `Drop-down list`** → click vào góc trên trái trang để đặt.
2. Panel **Setup**:
   - **Control field**: bấm vào tên field (mặc định là `ApprovalDate`) → gõ `FY` vào ô tìm → chọn **`FY`**.
   - **Default selection**: ô chữ `value1, value2, value3` → gõ `FY2025` → nhấn `Tab`. Control hiện `FY: FY2025`, thanh trên cùng hiện thẻ `FY FY2025`.
3. Panel **Style** → bật **`Single-select`**.

### 3.3. Bản đồ

1. **`Add a chart ▾`** → kéo danh sách xuống cuối, nhóm **Geo chart** → chọn ô đầu tiên → click vào vùng trống bên trái, dưới drop-down.
2. Looker tự điền sẵn **Geo dimension = `StateGeo`** và **Zoom area = `United States`**. Không phải chỉnh 2 mục này.
3. **Metric** đang là `Record Count` (số bản ghi): kéo **`GrossApproval`** từ panel Data thả lên ô `Record Count`, rồi rê vào `Record Count` bấm ✕ nếu nó còn.
4. Kéo góc dưới phải của chart cho bản đồ to ra. Chú thích màu phải ghi khoảng `2,656,000 – 4,808,747,400` (max là CA).

### 3.4. Bảng Top 10 bang

1. **`Add a chart ▾` → `Table`** → click vùng trống bên phải bản đồ.
2. Bảng mới tự lấy `StateGeo` + `GrossApproval`. Sửa lại:
   - Kéo **`ProjectState`** từ panel Data thả vào ô **`Add dimension`**.
   - Rê vào ô **`StateGeo`** → bấm ✕ để xóa.
3. Kéo **`GrossApproval`** thả vào **`Add metric`**. Giờ có 2 ô GrossApproval.
4. Bấm **icon trái** (chữ `SUM`) của ô GrossApproval **thứ hai**:
   - **Display name**: `Tỷ trọng (%)`.
   - **Comparison calculation**: chọn **`Percent of total`**.
   - Nhấn `Esc`. Cột cuối hiện 12.9%, 10.91%, …
5. Ô GrossApproval thứ nhất → icon trái → Display name `Tổng vốn (USD)`. Ô ProjectState → icon trái → Display name `Bang`.
6. Kéo panel Setup xuống mục **Number of rows** → chọn **`Top N`** → ô **Top rows**: xóa `100`, gõ `10` → `Tab`.
7. Mục **Sort** đã mặc định là `GrossApproval` **Descending**, giữ nguyên.
8. Kéo cạnh dưới của bảng cho vừa đủ 10 dòng, **đừng để khung bảng thừa dài xuống dưới**. Khung thừa sẽ bị dính vào vùng chọn ở bước group.

### 3.5. Bảng Top 3 county

1. **`Add a chart ▾` → `Table`** → click vùng trống ở **góc dưới bên trái**, cách xa bản đồ và bảng Top 10.
2. Dimension: kéo **`ProjectCounty`** vào `Add dimension`, xóa `StateGeo` bằng ✕. Icon trái của ô ProjectCounty → Display name `Quận (County)`.
3. Metric: thêm `GrossApproval` lần 2 → icon trái → **Percent of total**, Display name `% trong bang`. Ô thứ nhất đặt Display name `Tổng vốn (USD)`.
4. Number of rows → **Top N** → Top rows = `3`.
5. Style → bật **Show title**: `Top 3 county của bang được chọn`.
6. Lúc này chưa có lọc bang, nên bảng ra top 3 toàn quốc: LOS ANGELES, ORANGE, HARRIS. Bình thường.

### 3.6. Drop-down chọn bang

1. **`Add a control ▾` → `Drop-down list`** → click ngay **phía trên bảng county**, sát nhau.
2. Setup:
   - **Control field**: bấm vào tên field → tìm `ProjectState` → chọn.
   - **Default selection**: gõ `CA` → `Tab`.
3. Style → bật **`Single-select`**.
4. Lúc này **cả trang** bị lọc theo CA: bản đồ chỉ tô CA, bảng Top 10 chỉ còn CA 100%. Bước group tiếp theo sẽ sửa.

### 3.7. Group drop-down bang với bảng county

1. Click vào một chỗ trống trên trang để bỏ chọn mọi thứ.
2. **Kéo chuột vẽ một khung chọn**: bắt đầu từ chỗ trống bên phải drop-down bang, kéo chéo xuống dưới-trái sao cho khung **chỉ chạm** drop-down bang và bảng county.
   - Panel phải phải ghi **`Multiple Properties`**.
   - Nếu khung chạm thêm bản đồ hoặc bảng Top 10 thì làm lại, hoặc dời 2 thành phần này ra xa hơn trước.
   - Shift + click để chọn nhiều cũng được, nhưng khi mình thử thì kéo khung chắc ăn hơn.
3. Menu **Arrange → Group** (phím tắt `Cmd + G` trên Mac, `Ctrl + G` trên Windows). Panel phải đổi thành **`Group properties`**.
4. **Tải lại trang** (`Cmd + R` / `F5`). Trước khi tải lại, bản đồ và bảng Top 10 vẫn còn dính lọc CA, đây là lỗi hiển thị. Sau khi tải lại:
   - Bản đồ và Top 10 hiện toàn quốc (CA 12.9%, TX 10.91% …).
   - Bảng county hiện LOS ANGELES 30.3%, ORANGE 11.36%, SAN DIEGO 10.18%.
5. Thử: bấm drop-down bang → chọn **TX**.
   - Chỉ bảng county đổi: HARRIS 16.64%, DALLAS 12.45%, TARRANT 8.99%.
   - Bản đồ và Top 10 giữ nguyên.

### 3.8. Bảng Grouping and Totals (pivot Bang → County, có tổng phụ và tổng cộng)

Bảng này đáp ứng yêu cầu "1 report dạng Grouping and Totals". Nó chỉ chịu lọc FY của trang. **Không** đưa vào group ở 3.7, để drop-down bang không lọc nó.

1. Nới trang cho đủ chỗ: **Theme and layout** (thanh công cụ) → tab **Layout** → mục **Canvas size** → ô **Height (px)**: tăng thêm khoảng `700`, ví dụ `768` → `1500` → `Enter`.
   - Có thể kéo cạnh dưới trang xuống cũng được.
   - Click ra chỗ trống để đóng panel.
2. **`Add a chart ▾`** → kéo danh sách xuống nhóm **Pivot table** → chọn **ô đầu tiên** → click vào vùng trống **phía dưới cùng** trang, tách xa các thành phần khác.
3. Panel **Setup**. Pivot mới có sẵn Row dimension `FY`, Column dimension `ApprovalDate`, Metric `Record Count`. Sửa lại như sau:
   - **Row dimension**: bấm vào chữ `FY` → gõ `ProjectState` → chọn. Bấm **`Add dimension`** ngay dưới → gõ `ProjectCounty` → chọn.
     - Bây giờ Row dimension có 2 ô theo thứ tự `ProjectState`, `ProjectCounty`. Đây chính là phần **grouping**: county nằm trong nhóm bang.
   - **Column dimension**: rê chuột vào ô `ApprovalDate` → bấm ✕ ở cuối ô để xóa. Mục này để trống.
   - **Metric**: bấm vào chữ `Record Count` → gõ `GrossApproval` → chọn.
4. Kéo panel Setup xuống mục **Totals → Rows**:
   - Bật **`Show subtotals`**: tổng phụ cho mỗi bang.
   - Bật **`Show grand total`**: tổng cộng cả nước.
5. Kéo xuống mục **Sorting**:
   - **Row #1** (bang): `GrossApproval`, **Descending**. Đây là mặc định, giữ nguyên.
   - **Row #2** (county): `GrossApproval`, **Descending**. Ô **Number of rows**: xóa `Auto` → gõ `3` → `Tab`.
     - Mỗi bang chỉ hiện 3 county lớn nhất, tiêu đề cột đổi thành `Top 3 - ProjectCounty`.
     - Dòng `Total` của bang vẫn là **tổng của cả bang**, không chỉ của 3 county.
6. Đổi tên cột: bấm **icon trái** của từng ô (`ABC` / `SUM`) → Display name → `Esc`.
   - `ProjectState` → `Bang`
   - `ProjectCounty` → `Quận (County)`
   - `GrossApproval` → `Tổng vốn (USD)`
7. Kéo góc dưới phải cho bảng rộng khoảng nửa trang, cao gần hết phần trang vừa nới.
   - Panel **Style** → bật **Show title** → `Tổng vốn theo bang → Top 3 county (có tổng phụ từng bang và tổng cộng)`.
8. **Kiểm tra** với FY2025:
   - Dòng đầu là **CA**: LOS ANGELES 1,457,139,100 · ORANGE 546,312,500 · SAN DIEGO 489,766,900.
     - Tiếp theo là dòng **`Total (57)` = 4,808,747,400**. 57 là số county của CA.
   - TX: HARRIS, DALLAS, TARRANT, rồi `Total (172)` = 4,067,228,500.
   - Dòng cuối cùng: **`Grand total (2439)` = 37,287,816,200**, bằng tổng vốn FY2025 ở trang Q6.
   - Đổi drop-down bang sang TX thì bảng này **không đổi**. Đúng, vì nó nằm ngoài group.
9. (Tùy chọn) Setup → bật **`Expand-collapse`** → *Default expand level* = `ProjectState`.
   - Bảng sẽ thu gọn, mỗi bang một dòng tổng. Người xem bấm **⊞** cạnh bang để mở county.
   - Khi quay video thì nên để **tắt** cho thấy rõ tổng phụ.

### 3.9. Ghi chú

**Insert → Text**:
`Tỷ trọng (%) = Tổng vốn của bang / Tổng vốn toàn quốc trong cùng FY. % trong bang = Tổng vốn của county / Tổng vốn của bang trong cùng FY. Nguồn: SBA7A_DWH, giữ cả bản trùng (BR-POP-01).`

### 3.10. Kiểm tra ở chế độ xem

1. Bấm **`View`** (nút xanh góc trên phải).
2. Trang Q8:
   - Đổi FY → `FY2021`: bản đồ, Top 10 và bảng county cùng đổi.
   - Đổi bang → `FL`: chỉ bảng county đổi, bảng pivot giữ nguyên.
   - Đổi FY → `FY2021`: dòng `Grand total` của pivot phải bằng 36,536,756,800.
3. Bấm số **1** ở thanh trang bên trái để quay về trang Q6.
4. Bấm **`Edit`** để quay lại chế độ sửa nếu cần.

---

---

## Phần 4 – Trang Q15 (ngành có tỷ lệ CHGOFF cao hơn baseline + Top 3 bang)

### 4.0. Hiểu trước khi làm (không cần quay)

Q15 đi qua 4 bước, trong **từng FY**:
1. Mỗi ngành (NaicsSector): số bản ghi, số bản ghi CHGOFF, **tỷ lệ CHGOFF** = CHGOFF / số bản ghi.
2. **Gate 30/5**: ngành phải có ≥ 30 bản ghi và ≥ 5 CHGOFF.
3. **Baseline** = tỷ lệ CHGOFF của cả năm (mọi ngành). Ngành phải có tỷ lệ > baseline.
4. Ngành qua cả 2 điều kiện (Eligible = 1) được xếp hạng theo **tổng tiền xóa nợ** (GrossChargeOffAmount), rồi xem **Top 3 bang** đóng góp trong ngành đó.

Looker tính được cột Eligible nhưng **không lọc được** theo nó (đã thử: filter trên blend báo *System Error*). Vì vậy bảng hiển thị **tất cả ngành**, sắp xếp cho Eligible = 1 lên đầu, rồi theo tiền xóa nợ giảm dần.

Số đúng để đối chiếu:

| FY | Baseline | Qua gate | Eligible | Ngành Eligible (xếp theo tiền xóa nợ) |
|---|---|---|---|---|
| FY2025 | 0.11% | 7 | 3 | 44-45 Retail Trade · 23 Construction · 31-33 Manufacturing |
| FY2024 | 0.9% | 15 | 7 | 54 Professional… · 44-45 Retail · 48-49 Transportation · … |
| FY2026 | 0.00% | 0 | 0 | không có ngành đủ điều kiện (dữ liệu đến 30/06/2026) |

Top 3 bang FY2025 (theo tiền xóa nợ, % trong ngành):
- Retail Trade: CA 47.00% · AL 27.40% · TN 10.38%
- Construction: VA 31.21% · CA 14.68% · IL 12.74%
- Manufacturing: VA 29.81% · AZ 22.36% · FL 21.69%

### 4.1. Trang mới và tiêu đề

1. **Page → New page** → **Page → Manage pages** → đổi tên trang 3 thành `Q15 – CHGOFF theo ngành`.
2. **Insert → Text**: `Báo biểu Q15 – Ngành có tỷ lệ CHGOFF cao hơn baseline và Top 3 bang đóng góp`.

### 4.2. Tạo blend "ngành + cả năm"

1. Bấm **`Blend`** trên thanh công cụ (hoặc **Resource → Manage blends**) → **`ADD A BLEND`**.
2. **Bảng 1** (bên trái) – data source `SBA7A_BI_DATASET`:
   - Ô **Table name**: `Ngành`.
   - **Dimensions**: bấm `Add dimension` → gõ `FY` → chọn **`FY`**; bấm `Add dimension` lần nữa → gõ `Naics` → chọn **`NaicsSector`**.
   - **Metrics**: bấm `Add metric` → chọn **`ChargeOffRecord`**; `Add metric` → **`GrossChargeOffAmount`**; `Add metric` → **`Record Count`**.
   - (Kéo field từ cột *Available Fields* thả vào đôi khi không ăn – dùng `Add dimension` / `Add metric` rồi gõ tên là chắc nhất.)
3. Bấm ô **`Merge another table`** → chọn **`SBA7A_BI_DATASET`**.
4. **Bảng 2**:
   - Looker tự chép sẵn vài field vào ô Dimensions → rê chuột từng ô, bấm ✕ cho đến khi **chỉ còn `FY`**.
   - Ô **Table name**: `Cohort`.
   - **Metrics**: `Add metric` → **`ChargeOffRecord`**, rồi bấm icon `SUM` bên trái ô → **Display name** `CHG_cohort` → `Esc`.
   - `Add metric` → **`Record Count`** → icon bên trái → Display name `N_cohort` → `Esc`.
5. Bấm ô **Configure merge** giữa 2 bảng → kiểm tra: **Left outer**, điều kiện **`FY` (Ngành) = `FY` (Cohort)** (thường Looker tự điền) → **`Apply`**.
6. Ô **Blend name** (bên phải trên cùng): `Blend_Q15_Sector` → **`Save`** (dưới cùng bên phải) → **`CLOSE`**.
7. **Kiểm tra**: panel *Data* bên phải, mục `Blend_Q15_Sector` phải có đủ **`CHG_cohort`** và **`N_cohort`**. Thiếu cái nào nghĩa là bước đổi tên ở bảng Cohort chưa ăn (field trùng tên với bảng Ngành nên bị ẩn) → **Resource → Manage blends → EDIT** → bảng Cohort → bấm đúng **icon `SUM`/`AUT` bên trái** ô metric (bấm vào chữ tên sẽ mở danh sách đổi field, không phải ô đổi tên) → gõ Display name → `Esc` → **Save**.

Ý nghĩa: mỗi dòng (năm × ngành) của bảng `Ngành` được gắn thêm số liệu cả năm từ bảng `Cohort` → tính được baseline ngay trên dòng ngành.

### 4.3. Drop-down chọn năm

1. **`Add a control ▾` → `Drop-down list`** → đặt góc trên phải trang.
2. Setup: **Control field** → `FY`; **Default selection** gõ `FY2025` → `Tab`.
3. Style → bật **`Single-select`**. (Bắt buộc: Q15 tính riêng từng cohort FY.)

### 4.4. Bảng xếp hạng ngành

1. **`Add a chart ▾` → `Table`** → đặt dưới tiêu đề, kéo rộng gần hết chiều ngang trang.
2. Setup → **Data source**: bấm ô data source → mục *Blended data* → **`Blend_Q15_Sector`**.
3. **Dimension**: bấm vào tên field đang có → gõ `Naics` → chọn **`NaicsSector`** → icon trái → Display name `Ngành (NAICS)`.
4. **Metric** – xóa các metric thừa bằng ✕, rồi thêm lần lượt bằng `Add metric` + gõ tên:
   - **`Record Count`** (field của bảng Ngành, chữ C hoa) → Display name `Số bản ghi`.
   - **`ChargeOffRecord`** → Display name `Số CHGOFF`.
   - **`GrossChargeOffAmount`** → Display name `Tiền xóa nợ (USD)`.
5. Thêm 3 metric tính toán: `Add metric` → **`Add calculated field`** (cuối danh sách). Trong hộp *New Field*: gõ **Display name**, gõ **Formula**, chỉnh **Data type** (ô ngay dưới tên: rê vào `Numeric` → chọn), bấm **`Apply`**, `Esc`.

| Display name | Formula | Data type |
|---|---|---|
| `Tỷ lệ CHGOFF (%)` | `SUM(ChargeOffRecord) / SUM(Record Count)` | Numeric → **Percent** |
| `Baseline (%)` | `SUM(CHG_cohort) / SUM(N_cohort)` | Numeric → **Percent** |
| `Eligible` | `CASE WHEN SUM(Record Count) >= 30 AND SUM(ChargeOffRecord) >= 5 AND SUM(ChargeOffRecord) / SUM(Record Count) > SUM(CHG_cohort) / SUM(N_cohort) THEN 1 ELSE 0 END` | Number |

   - Gõ `(` thì Looker tự thêm `)` → gõ tiếp bên trong, dùng phím `End` để nhảy ra sau dấu `)` cuối.
   - Gõ đúng tên field thì chữ được tô nền xanh; nếu báo lỗi dưới khung công thức thì kiểm tra lại chính tả (`Record Count` có dấu cách, C hoa).
6. **Sort** (kéo panel Setup xuống cuối):
   - **Sort #1**: bấm vào ô field → gõ `Elig` → chọn **`Eligible`** → **Descending**. (Looker hiện cảnh báo *Sort will apply, but the field will not be shown* – bỏ qua, cột Eligible vẫn hiện vì đã có trong Metric.)
   - Bấm **`Add sort`** → **Sort #2**: chọn **`GrossChargeOffAmount`** (nhóm *Chart fields*) → **Descending**.
7. Kiểm tra FY2025: 3 dòng đầu Eligible = 1 – Retail Trade (1,913,417.62), Construction (1,374,155.58), Manufacturing (659,110.94); Baseline mọi dòng = 0.11%; các dòng sau Eligible = 0.
8. (Tuỳ chọn, cho dễ nhìn) Style → **Conditional formatting → Add formatting** → Single color, Format based on `Eligible`, Condition *Equal to* `1` → chọn màu nền vàng nhạt → Save. Nếu không cho chọn Eligible thì bỏ qua bước này.
9. Style → bật **Show title**: `Xếp hạng ngành theo tiền xóa nợ (Eligible = 1 xếp trước)`.

### 4.5. Bảng Top 3 bang của ngành được chọn

1. **`Add a chart ▾` → `Table`** → đặt ở **góc dưới bên trái**, cách xa bảng ngành.
2. Data source: **`SBA7A_BI_DATASET`** (không phải blend).
3. Dimension: **`ProjectState`** → Display name `Bang`.
4. Metric: **`GrossChargeOffAmount`** → Display name `Tiền xóa nợ (USD)`; thêm `GrossChargeOffAmount` lần 2 → icon trái → **Comparison calculation: Percent of total** → Display name `% trong ngành`.
5. Filter: **`Add filter` → `Create a filter`** → tên `Chỉ CHGOFF` → Include · `RawStatus` · *Equal to (=)* · `CHGOFF` → **Save**.
6. Number of rows → **Top N** → Top rows = `3`. Sort `GrossChargeOffAmount` Descending (mặc định).
7. Style → **Show title**: `Top 3 bang đóng góp tiền xóa nợ của ngành được chọn`.

### 4.6. Drop-down chọn ngành + Group

1. **`Add a control ▾` → `Drop-down list`** → đặt **ngay trên** bảng Top 3 bang.
2. Setup: **Control field** → `NaicsSector`; **Default selection**: gõ đúng `44-45 - Retail Trade` → `Tab`. Style → bật **Single-select**.
3. Group (giống mục 3.7): click chỗ trống → kéo khung chọn chỉ chạm drop-down ngành và bảng Top 3 bang → panel ghi *Multiple Properties* → **Arrange → Group** → `Cmd + R` tải lại trang.
4. Kiểm tra: bảng ngành vẫn hiện đủ 20 ngành; bảng bang hiện CA 47.00% · AL 27.40% · TN 10.38%. Đổi ngành sang `23 - Construction` → VA · CA · IL.
5. Lưu ý khi demo: chỉ nên chọn ngành có Eligible = 1 ở bảng trên (Q15 chỉ xét bang **sau** khi ngành đã qua điều kiện).

### 4.7. Ghi chú

**Insert → Text**:
`Q15 (exploratory). Tỷ lệ CHGOFF = số bản ghi CHGOFF / tổng bản ghi của ngành trong FY; Baseline = tỷ lệ CHGOFF của cả FY. Eligible = 1 khi ngành có ≥ 30 bản ghi, ≥ 5 CHGOFF và tỷ lệ > baseline; chỉ ngành Eligible = 1 được xếp hạng theo tiền xóa nợ (GrossChargeOffAmount trên CHGOFF). Đây là tỷ lệ quan sát, không phải xác suất vỡ nợ. NAICS mapping còn PENDING_VERIFICATION. Nguồn: SBA7A_DWH, giữ cả bản trùng (BR-POP-01).`

### 4.8. Kiểm tra ở chế độ xem

1. **`View`** → trang Q15.
2. Đổi FY → `FY2024`: bảng ngành có 7 dòng Eligible = 1, baseline 0.9%.
3. Đổi FY → `FY2026`: mọi dòng Eligible = 0 – đúng với quy tắc (không có ngành đủ điều kiện, không hạ ngưỡng).
4. Bấm **Reset** để về mặc định FY2025 / Retail Trade.

---

## Lỗi hay gặp

| Hiện tượng | Nguyên nhân / cách sửa |
|---|---|
| *Unknown dimension or metric id: ProjectState* khi tạo field | Đang tạo field trong report. Tạo ở trang data source (Phần 1.1), hoặc trong report bấm **Resource → Manage added data sources → Edit**. |
| YoY hiện 0.62% | Đổi **Data type → Numeric → Percent** của metric YoY, không phải Display format. |
| YoY dòng FY2021 trống | Filter 2021–2025 đang đặt ở data source hoặc blend. Phải đặt filter trên **chart**. |
| Kéo field vào ô có sẵn thì ra 2 field | Kéo thả là chèn thêm. Xóa ô cũ bằng ✕. |
| Bảng tự lọc theo một dòng, trên thanh trên cùng hiện thẻ lạ | Lỡ click vào dòng (cross-filter). Bấm **`Reset`**. Muốn tắt hẳn: Setup → Chart interactions → tắt **Cross-filtering**. |
| Group xong mà bản đồ vẫn chỉ hiện 1 bang | Tải lại trang (`Cmd + R`). |
| Filter trên bảng blend (ví dụ `Record Count >= 30`) làm chart báo *System Error* | Looker không lọc được metric của blend. Gỡ filter đó (✕) – Q15 dùng cột Eligible + sắp xếp thay cho lọc. |
| Không tìm thấy `Eligible` khi tạo filter | Bình thường: field tính trong chart không dùng làm filter được. Chỉ dùng để hiển thị và Sort. |
| Khung chọn dính cả bảng Top 10 | Khung bảng Top 10 dài thừa. Kéo cạnh dưới của bảng lên, hoặc dời drop-down bang và bảng county ra xa. |
