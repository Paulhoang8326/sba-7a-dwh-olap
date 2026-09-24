# Việc cần làm sau review (bản 3, 2026-09-24)

Bản này thay hai bản trước. Thay đổi lớn: nhóm đã thống nhất dùng tên đề tài đang có trong repo, nên **Task 0 và Task 2 của bản trước bị huỷ**, và Task 1 quay về đúng vị trí cũ của nó là hướng nâng cao tuỳ chọn.

Những gì còn lại là các lỗi thật, phần lớn nhỏ.

Các con số trong file này được tính trực tiếp trên `FOIA_7a_FY2020_Present_asof_260630.csv` (388.338 dòng × 42 cột, snapshot 30/06/2026).

---

## Bối cảnh: tên đề tài đã thống nhất

Trước đây nhóm có hai tên song song. Nay chốt dùng tên đang có trong `README.md`, `group_info.txt` và `docs/01_feasibility.md`:

> Xây dựng hệ thống Kho dữ liệu và OLAP hỗ trợ phân tích danh mục tín dụng, bảo lãnh và kết quả khoản vay SBA 7(a) tại Hoa Kỳ giai đoạn FY2020–FY2026

**Repo không phải sửa gì cho việc này.** Các tài liệu bên ngoài repo đã được cập nhật theo.

Hệ quả cho những gì từng đề nghị ở bản trước:

- Câu khai báo trong `01_feasibility.md` và `05_bi_mining.md` — *"đây là phân tích học thuật dữ liệu danh mục, không phải mô hình ra quyết định cấp tín dụng thực tế"* và *"tên bài toán phải là phân loại hồi cứu trong nhóm đã có kết quả"* — **giữ nguyên, không sửa chữ nào.** Chúng đúng và khớp với tên đề tài.
- `Resolved Charge Off Rate` giữ nguyên, kèm câu khai báo censoring bias đang có trong `02_warehouse_design.md`. Nó đo đúng thứ đề tài hỏi.
- Bộ 15 câu truy vấn giữ nguyên. Nó khớp ba trục của đề tài, và cột mô tả cách tự kiểm ở `04_analysis_catalog.md` là điểm mạnh, đừng làm mất.

---

## Task 1 — Dọn `AsOfDateKey` khỏi bảng fact

`AsOfDate` có đúng một giá trị trên cả 388.338 dòng, và `src/main.py` dòng 62–63 còn chủ động raise nếu có nhiều hơn một. Chiều một thành viên không phân biệt được gì, mà `sql/02_validation.sql` lại phải có hẳn một câu `COUNT(DISTINCT AsOfDateKey)` để tự trấn an.

Bỏ `AsOfDateKey` khỏi `dwh.FactLoanSnapshot`, bỏ role `As Of Date` trong hợp đồng cube ở `docs/03_implementation.md`, và ghi giá trị snapshot vào `docs/data_profile.json` cùng phần mô tả dữ liệu.

Nếu muốn giữ để sau này nạp nhiều snapshot thì giữ, nhưng phải ghi lý do trong `docs/02_warehouse_design.md` — mục "Grain và phạm vi" hiện đang nói ngược lại là không append snapshot thứ hai.

---

## Task 2 — Sửa câu sai trong `data/README.md`

Ba nguồn đang mâu thuẫn, và đã xác định được nguồn nào sai:

- `.gitattributes` track `data/raw/foia/*.csv` bằng Git LFS
- `.gitignore` **không** ignore đường dẫn đó (chỉ ignore `data/staging/*` và `data/processed/*`)
- `data/README.md` viết `data/raw/foia/*.csv` "không được commit" — **câu này sai**

Sửa `data/README.md` cho khớp với LFS, và thêm dòng hướng dẫn chạy `git lfs install` trước khi clone.

---

## Task 3 — Sửa link nguồn ở hai chỗ

`README.md` và `data/raw/foia/README.md` đều trỏ `https://web.data.sba.gov/en/dataset/7-a-504-foia`. Đó là bản CKAN cũ. Trang hiện hành: `https://data.sba.gov/dataset/7a-504-foia`.

---

## Task 4 — Làm test chạy được trên máy mới clone

Trên một máy chưa cài `git lfs`:

- `tests/test_pipeline.py` dòng 18 đọc thẳng CSV gốc; gặp pointer LFS 134 byte thì lỗi như thể code sai
- `test_full_snapshot_integrity` **tự skip** vì `data/processed/profile.json` chưa tồn tại (dòng 40–41), mà thư mục đó bị gitignore

Người mới clone sẽ thấy một test lỗi khó hiểu và một test skip im lặng. Thêm kiểm tra đầu file: nếu CSV nhỏ bất thường hoặc bắt đầu bằng `version https://git-lfs`, báo lỗi rõ ràng kiểu "chạy `git lfs pull` trước". Đổi thông điệp skip cho nói rõ phải chạy `python -m src.main` trước.

---

## Task 5 — Đối chiếu với khung báo cáo `olap.docx`

Khung báo cáo của môn có mục **1.2.8 `Bảng BRIDGE_<A>_<B>`** và cả mục **3.6 "Tạo dimension cho bảng BRIDGE"** kèm named calculation cho khoá phức hợp. Thiết kế hiện tại không có bridge, và đúng là dữ liệu SBA không có quan hệ nhiều-nhiều nào để cần bridge.

Khung cũng ghi 6 bảng `DIM_<TÊN>`; repo có 8.

Việc cần làm: hỏi giảng viên xem hai mục đó có bắt buộc không. Nếu không, viết một đoạn ngắn trong báo cáo giải thích vì sao đề tài này không có bridge, thay vì để trống mục. `docs/01_feasibility.md` đã có sẵn phương án gộp Sector vào Industry để còn 8 bảng nếu cô muốn siết số lượng.

---

## Ghi chú cho báo cáo, không phải việc sửa code

**Độ lệch prevalence giữa các split của mining.** `mining_baseline.json` cho train 6,25%, validation 13,50%, test 17,61%. Average precision phụ thuộc prevalence, nên 0,676 ở validation và 0,665 ở test không so trực tiếp được với nhau. Trong báo cáo nên có một câu giải thích, kẻo bị hỏi "sao test không tụt điểm".

**Chọn phiên bản SQL Server.** `docs/03_implementation.md` nói đúng: Data Mining bị deprecated từ SQL Server 2017 và **discontinued hẳn ở SQL Server 2022** Analysis Services, chỉ còn ở 2019 trở về trước (đã kiểm trên Microsoft Learn). Nếu chương 5 định chạy trên SSAS/DMX thì cả nhóm phải cài **SQL Server 2019**. Chạy bằng Python như baseline hiện tại thì bản nào cũng được.

---

## Hướng nâng cao, chỉ làm nếu còn thời gian

Đây chính là mục `docs/05_bi_mining.md` đã xếp sẵn: *"dự báo CHGOFF trong 24/36 tháng trên cohort đủ thời gian quan sát"*. Không bắt buộc với tên đề tài hiện tại, nhưng nếu làm thì nó là phần ăn điểm rõ nhất của chương 5, và dưới đây là số liệu để biết có đáng làm không.

Thêm hai cột vào fact — `ChargeOffWithin36M` và `EligibleFor36M` (đủ 36 tháng tính tới `AsOfDate`, và trạng thái không thuộc `CANCLD`/`COMMIT`) — rồi một calculated member `Early Default Rate 36M` bằng tỷ số hai cột.

| ApprovalFY | Đủ 36 tháng | Xoá nợ ≤36 tháng | Tỷ lệ 36 tháng | Rate hiện tại để so |
| --- | --- | --- | --- | --- |
| 2020 | 36.464 | 301 | 0,83% | 6,38% |
| 2021 | 45.165 | 331 | 0,73% | 6,10% |
| 2022 | 41.764 | 796 | 1,91% | 13,24% |
| 2023 | 35.893 | 1.020 | 2,84% | 17,40% |

Tổng 159.286 khoản đủ điều kiện, 2.448 nhãn dương, 1,54%. Cột "tỷ lệ 36 tháng" đơn điệu tăng và giải thích được bằng Mục 1112 CARES Act ở FY2020–2021; cột bên phải thì không đọc được vì phản ánh thời điểm tất toán.

Nếu làm, kiểm bằng `EligibleFor36M.sum() == 159286` và `ChargeOffWithin36M.sum() == 2448`.

---

## Không cần sửa — đã kiểm, đúng rồi

Ghi lại để vòng sau khỏi "sửa nhầm":

- `CHECK(LoanCount=1)` trong DDL — chốt grain
- `Weighted Initial Rate` dùng mẫu số riêng `InterestKnownApproval`
- Mọi calculated member bọc `IIF` chống chia 0
- Câu kiểm số dòng sau join trong `02_validation.sql`
- Hai nhánh snowflake `DimState → DimCounty`, `DimSector → DimIndustry`
- Hàm `sector()` gộp NAICS `31-33`, `44-45`, `48-49` theo chuẩn Census
- Các cột khai `NOT NULL` cho trường hay rỗng: `src/main.py` dòng 23 đã có `fillna('Unknown').replace('', 'Unknown')`
- `DimLender` 2.338 dòng, đúng bằng số `LocationID`; top 10 lender FY2024 xếp theo `LocationID` hay gộp theo tên đều ra danh sách y hệt
- `BorrowerGroup` hash tên + địa chỉ + ZIP để chặn rò rỉ giữa các split
- Fact giữ đủ 388.338 dòng kể cả `CANCLD` và `COMMIT` — đúng với đề tài phân tích danh mục
- Không có bảng bridge, vì dữ liệu không có quan hệ nhiều-nhiều nào
- Toàn bộ phần khai báo giới hạn trong `01_feasibility.md` và `05_bi_mining.md`
