# PROJECT_STATUS — Tiến độ dự án SBA 7(a)

> **Trạng thái hiện hành (2026-10-01):** [docs/00_current_status.md](docs/00_current_status.md) là Source of Truth. **Phase 1 tiền xử lý Python: IMPLEMENTED** — P1.1–P1.17 có đủ, 57/57 test pass, 388.338 → 388.338 dòng, đối soát tổng tiền/FY/status khớp; xem [Giải thích Phase 1](docs/etl/phase1_preprocessing_explained.md) và [`reports/preprocessing/`](reports/preprocessing/). Phase 2 (DDL), Phase 3 (SSIS), Phase 4 (đối soát kho), SSAS: chưa bắt đầu. [Q1–Q15](docs/business_requirements/business_questions_current.md), gồm Q10 mới, đã duyệt ở cấp business-question scope; [star 1 `FactLoanSnapshot` + 8 dimensions](docs/dimensional_model/candidate_schema.md) là **PROPOSED TARGET SCHEMA**, chưa là Final/physical schema. [Measure Contract](docs/business_requirements/measure_contract_q1_q15.md) đã viết nhưng **NOT IMPLEMENTED**. [Rule register](docs/business_requirements/business_rule_register.md) ghi `PROJECT_APPROVED` cho population, cấp NAICS Sector, TermBand, canonical PIF và Q15 gates; NAICS reference/version/mapping còn `PENDING_VERIFICATION`, business grouping mở rộng còn `OPEN`. [Preprocessing](docs/data_understanding/preprocessing_plan.md) theo [ETL Implementation Plan §3](docs/etl/etl_implementation_plan.md) **IMPLEMENTED — Phase 1** (2026-10-01); prototype snowflake/MDX cũ giữ cho lịch sử.

## Việc tiếp theo theo trạng thái hiện hành

0. ~~Thực hiện preprocessing theo plan đã duyệt, đối soát raw → standardized~~ — **xong Phase 1 (2026-10-01)**. NAICS Sector trong output vẫn `CANDIDATE_UNVERIFIED` (D1 = A).
1. Xác minh NAICS reference/version/crosswalk và unmapped (plan §9 bước 5); không tự chuyển mapping/sector name sang `VERIFIED` chỉ vì đã duyệt cấp Sector. **Chưa bắt đầu.**
2. Phase 2 — DDL SQL Server (`sql/dwh/00_drop_all.sql`, `01_create_all.sql`, `02_seed_static.sql`) theo plan §4: tạo staging theo header TSV thật (38 cột), cột tiền `DECIMAL(18,3)` (D4). **Chưa bắt đầu.**
3. Sau Phase 2: Phase 3 SSIS và Phase 4 đối soát standardized → warehouse (plan §5–§6), rồi mới tới cube/BI.

## Lưu trữ: status snapshot ngày 2026-09-24

Toàn bộ các mục đánh số bên dưới là **ghi chép lịch sử của previous prototype** tại ngày nêu trên. Các nhãn “Current”, “Pending”, “Recommended” trong snapshot cũ không thay thế trạng thái hiện hành ở đầu file hoặc [Source of Truth](docs/00_current_status.md). Số duplicate 392 ở snapshot cũ dùng phương pháp chuẩn hóa khác; [profiling raw hiện hành](docs/data_understanding/data_profiling_report.md) ghi 687 dòng thuộc nhóm exact duplicate và 391 bản sao dư.

> **Cập nhật:** 2026-09-24. Đọc [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) để biết định nghĩa dữ liệu, grain và kiến trúc. Trạng thái ở đây dựa trên file và chứng cứ hiện có; không tự coi script/đặc tả là hệ thống đã chạy.

## 1. Historical Project Status (2026-09-24)

| Mục | Trạng thái |
|---|---|
| Giai đoạn hiện tại | **Khảo sát dữ liệu và prototype chuẩn bị kho dữ liệu đã có; chuẩn bị chốt thiết kế/triển khai SQL Server–SSIS–SSAS.** |
| Mục tiêu đang thực hiện | Đồng bộ bối cảnh và tiến độ qua hai file Markdown này; chưa có bằng chứng một tác vụ triển khai khác đang chạy. |
| Tóm tắt | Một CSV 388.338 dòng/42 cột; pipeline Python đã tạo CSV dimension/fact, mart, quality log và mining input cục bộ. Có DDL, SQL đối soát, MDX và đặc tả BI. **Chưa có bằng chứng** database/cube/SSIS/Pivot/dashboard thật đã được deploy/chạy. |
| Phạm vi | FY2020–FY2026 snapshot 2026-06-30; FY2010–FY2019 chưa được thêm vào repo/chưa chốt mở rộng. |

## 2. Completed Work

`Completed Date = Unknown` nếu bằng chứng chỉ cho biết công việc đã có, không xác định chắc ngày hoàn thành. Ngày trong [docs/validation.md](docs/validation.md) là ngày **kiểm chứng được ghi lại**, không tự đồng nhất với ngày tạo toàn bộ tính năng.

| ID | Task | Result | Evidence | Completed Date |
|---|---|---|---|---|
| C01 | Khảo sát CSV và từ điển | Profile 388.338 dòng, 42 cột; checksum, null, FY/status, quality issues | [docs/data_profile.json](docs/data_profile.json), [docs/data_dictionary.md](docs/data_dictionary.md), `data/raw/foia/` | 2026-09-23 (ngày kiểm chứng ghi trong docs) |
| C02 | Xây pipeline prototype một snapshot | Sinh 8 dimension, 1 fact, quality log, mart, mining input dưới `data/processed/` | [src/main.py](src/main.py), [docs/validation.md](docs/validation.md), các CSV output cục bộ bị Git ignore | 2026-09-23 (ngày kiểm chứng ghi trong docs) |
| C03 | Kiểm tra pipeline | Tài liệu ghi 3 tests PASS, đối soát dòng/khóa/FK/tổng tiền; output hiện tồn tại | [tests/test_pipeline.py](tests/test_pipeline.py), [docs/validation.md](docs/validation.md) | 2026-09-23 (ngày kiểm chứng ghi trong docs) |
| C04 | Viết thiết kế kho dữ liệu và DDL | Thiết kế snowflake 1 fact + 8 dimensions; DDL SQL Server và câu đối soát | [docs/02_warehouse_design.md](docs/02_warehouse_design.md), [sql/01_warehouse.sql](sql/01_warehouse.sql), [sql/02_validation.sql](sql/02_validation.sql) | Unknown |
| C05 | Viết hướng dẫn SSIS/SSAS và truy vấn mẫu | Có hợp đồng cube, 15 MDX mẫu, 15 câu manual và 5 Pivot theo tài liệu; **chưa chứng minh đã chạy** | [docs/03_implementation.md](docs/03_implementation.md), [docs/04_analysis_catalog.md](docs/04_analysis_catalog.md), `Source/SSAS/` | Unknown |
| C06 | Viết đặc tả BI | Kế hoạch Power BI và Looker Studio, KPI và bộ lọc | [docs/05_bi_mining.md](docs/05_bi_mining.md), `dashboards/README.md` | Unknown |
| C07 | Chạy baseline mining hồi cứu | Dummy, Logistic Regression, Decision Tree; có validation/test metrics, giới hạn được ghi rõ | [src/mining.py](src/mining.py), [docs/mining_baseline.json](docs/mining_baseline.json), [docs/validation.md](docs/validation.md) | 2026-09-23 (ngày kiểm chứng ghi trong docs) |
| C08 | Tạo tài liệu đồng bộ bối cảnh/tiến độ | Hai file Markdown tại root, đối chiếu trạng thái repo | [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md), file này | 2026-09-24 |
| C09 | Phase 1 — tiền xử lý Python (P1.1–P1.17) theo candidate 1F+8D | TSV chuẩn hóa 388.338 × 38 (SHA-256 `837723fb…a78bc5`), bản sạch 42 cột, manifest, 816 cờ DQ, đối soát 35/35 khớp, bảng chọn cột (18 KEEP/24 DROP), bảng trước/sau, notebook; 57/57 test pass | [src/etl/preprocess.py](src/etl/preprocess.py), [tests/test_preprocess.py](tests/test_preprocess.py), [notebooks/01_preprocessing.ipynb](notebooks/01_preprocessing.ipynb), [reports/preprocessing/](reports/preprocessing/), [docs/etl/phase1_preprocessing_explained.md](docs/etl/phase1_preprocessing_explained.md) | 2026-10-01 |

## 3. In Progress — historical snapshot

| ID | Task | Current Progress | Related Files | Next Action |
|---|---|---|---|---|
| — | Chưa xác định được tác vụ triển khai đang thực hiện | Repository chỉ cho thấy sản phẩm đã có và kế hoạch, không có bằng chứng một build/deploy hiện đang chạy | [README.md](README.md), [docs/07_delivery.md](docs/07_delivery.md) | Chốt các pending decisions ở §6 trước khi thay đổi mô hình hoặc triển khai stack đích. |

## 4. Planned / Not Started — historical snapshot

Priority dưới đây chỉ là **đề xuất thứ tự**, chưa phải kế hoạch đã được người dùng duyệt.

| ID | Task | Objective | Dependencies | Priority đề xuất |
|---|---|---|---|---|
| P01 | Chốt thiết kế kho dữ liệu và phạm vi | Xác nhận snowflake đang có hay chuyển star phẳng, KPI, có/không FY2010–FY2019 | Khảo sát nguồn, trao đổi với người dùng/giảng viên | Cao |
| P02 | Dựng database SQL Server và đối soát | Tạo bảng, nạp dữ liệu, kiểm tra count/FK/tổng tiền | P01; SQL Server instance và quyền triển khai | Cao |
| P03 | Dựng SSIS project thật từ raw | Có package `.dtproj`/`.dtsx`, staging, cleansing, audit, đối soát | P01, P02; môi trường SSIS | Cao nếu môn học yêu cầu SSIS |
| P04 | Dựng/process SSAS cube | Có `.dwproj`, DSV, dimensions, measures, 5 date roles | P02/P03; SSAS và phiên bản tương thích | Cao nếu môn học yêu cầu SSAS |
| P05 | Chạy và kiểm chứng 15 MDX/manual + 5 Excel Pivot | Kết quả thật, ảnh/bằng chứng, workbook kết nối cube | P04 | Trung bình |
| P06 | Tạo dashboard Power BI và Looker Studio | 3 báo cáo mỗi công cụ theo đặc tả, đối soát KPI/filter | P02/P04 hoặc mart đã kiểm chứng; quyền công cụ | Trung bình |
| P07 | Hoàn thiện phần mining và diễn giải | Phân tích lỗi, leakage/censoring, kết luận đúng phạm vi hồi cứu | Baseline đã có; yêu cầu đánh giá môn học | Trung bình |
| P08 | Viết báo cáo Word, video và đóng gói | Bộ nộp có chứng cứ hệ thống chạy, hướng dẫn tái lập | P02–P07 và thông tin nhóm | Sau cùng |

## 5. Issues & Blockers — historical snapshot

| ID | Issue đã phát hiện | Impact | Related Files | Suggested Solution | Status |
|---|---|---|---|---|---|
| I01 | Nguồn không có public LoanID; 392 dòng dư khi `drop_duplicates` thuộc tính chuẩn hóa | Không khẳng định count là số khoản vay duy nhất hoặc ghép chính xác nhiều snapshot | [docs/data_profile.json](docs/data_profile.json), [docs/01_feasibility.md](docs/01_feasibility.md) | Giữ mọi dòng và `SourceRowNumber`; chỉ mở rộng snapshot khi có khóa/quy tắc ghép được xác minh | Đang giới hạn phân tích |
| I02 | FY2026 chỉ đến 2026-06-30 | So tổng năm với FY đầy đủ sẽ sai | [docs/data_profile.json](docs/data_profile.json) | So FYTD cùng kỳ hoặc tách FY2026 | Có quy tắc phân tích, cần áp dụng trong dashboard |
| I03 | Kết quả theo status chịu thời gian theo dõi khác nhau; `EXEMPT` không phải nhãn good | Dễ diễn giải sai tỷ lệ charge-off/risk | [docs/05_bi_mining.md](docs/05_bi_mining.md), [docs/02_warehouse_design.md](docs/02_warehouse_design.md) | Báo cohort, tử/mẫu số, chỉ gọi resolved rate trên PIF+CHGOFF; không tuyên bố prospective risk | Đang giới hạn phân tích |
| I04 | `SoldSecMrktInd`: 116.764 `Y`, 271.574 blank, không có `N` | Không tính được tỷ lệ đã/không bán thật | CSV nguồn, [docs/data_profile.json](docs/data_profile.json) | Chỉ báo số dòng xác nhận `Y`; blank là unknown | Đang giới hạn phân tích |
| I05 | Chưa có artifact SQL Server/SSIS/SSAS/BI chạy thật | Không thể coi DDL/MDX/đặc tả là chức năng đã triển khai hoặc nghiệm thu | [docs/validation.md](docs/validation.md), [docs/07_delivery.md](docs/07_delivery.md) | Triển khai tuần tự sau khi chốt thiết kế; lưu kết quả đối soát và ảnh chạy | Chưa thực hiện |
| I06 | Thiết kế trong repo là snowflake, trong trao đổi đã có đề xuất star phẳng | Nếu dùng lẫn tên bảng/khóa, SQL/MDX/tài liệu không nhất quán | [sql/01_warehouse.sql](sql/01_warehouse.sql), [docs/02_warehouse_design.md](docs/02_warehouse_design.md) | Chốt một mô hình đích trước khi sửa DDL, ETL và query | Chờ quyết định |
| I07 | `FirstDisbursementDate` thiếu 71.186 dòng; có một số ngày sự kiện bất thường, zero rate/term | Một số KPI duration và chất lượng đầu vào bị ảnh hưởng | [docs/data_profile.json](docs/data_profile.json), `data/processed/quality_issues.csv` | Giữ quality log, chỉ tính duration trên ngày hợp lệ, hiển thị mẫu số | Có quy tắc prototype; cần đối soát trên stack đích |

## 6. Pending Decisions — historical snapshot, superseded by current status

Chỉ những lựa chọn **chưa thấy được chốt** trong yêu cầu/repository:

| ID | Cần người dùng xác nhận | Vì sao cần trước bước tiếp theo |
|---|---|---|
| D01 | Giữ **snowflake 1 fact + 8 dimensions** đang có, hay đổi sang **star schema phẳng** được đề xuất trong trao đổi? | Quyết định tên bảng, khóa, DDL, ETL, cube và toàn bộ SQL/MDX. |
| D02 | Giữ FY2020–FY2026 làm toàn bộ phạm vi hay bổ sung FY2010–FY2019 cho phân tích cohort? | Thay dữ liệu, profiling, ETL và cách đặt phạm vi đề tài; file cũ chưa có trong repo. |
| D03 | Chốt bộ KPI và thuật ngữ trong báo cáo, nhất là `Loan Count` = số dòng, resolved charge-off rate và giới hạn của `JobsSupported` | Đảm bảo dashboard/OLAP không diễn giải quá dữ liệu. |
| D04 | Xác nhận stack/phiên bản mà giảng viên yêu cầu, đặc biệt SQL Server, SSIS, SSAS Multidimensional và mining | Repo có hướng triển khai, nhưng chưa có project chạy thật hoặc xác nhận môi trường bắt buộc. |

Không đưa các câu hỏi đã có câu trả lời vào danh sách: nguồn chính là SBA 7(a) FOIA, phạm vi hiện tại FY2020–FY2026, grain prototype là dòng CSV trong một snapshot.

## 7. Recommended Next Steps — historical snapshot, superseded by current status

| Order | Task | Objective | Expected Output |
|---:|---|---|---|
| 1 | Chốt D01–D04 theo yêu cầu môn học và dữ liệu thực | Tránh triển khai DDL/ETL trên mô hình chưa nhất quán | Quyết định được ghi vào [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) và đặc tả thiết kế |
| 2 | Đồng bộ schema, measures, query catalog với mô hình được chốt | Một hợp đồng bảng/khóa/KPI duy nhất | DDL, Python/SSIS mapping, MDX/SQL được đối chiếu |
| 3 | Dựng database và chạy đối soát nguồn → fact | Chứng minh grain, khóa, tổng tiền và status | Database thực, kết quả [sql/02_validation.sql](sql/02_validation.sql) |
| 4 | Dựng SSIS project từ raw và lưu bằng chứng thực thi | Đáp ứng quy trình ETL của đồ án | `.dtproj`/`.dtsx`, audit/quality, row counts |
| 5 | Process cube, kiểm tra measures rồi mới chạy 15 MDX/manual/Pivot | Truy vấn OLAP có kết quả thật và đúng mẫu số | SSAS project, query outputs, workbook Pivot |
| 6 | Xây và đối soát BI; hoàn thiện mining/báo cáo | Trình bày kết quả có bằng chứng, diễn giải giới hạn | PBIX/Looker, báo cáo Word, video và bộ nộp |

## 8. Recent Changes

| Date | Change | Related Files | Impact |
|---|---|---|---|
| 2026-09-24 | Thêm tài liệu đồng bộ bối cảnh và tiến độ; không thay source code/dataset | [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md), file này | ChatGPT/Codex có điểm bắt đầu chung để hiểu repo và phân biệt triển khai với đề xuất. |
| 2026-09-23 | Commit `8da9357` chuyển repository sang đề tài SBA 7(a), bổ sung source/dictionary, Python, DDL, MDX, docs và baseline | [README.md](README.md), `src/`, `sql/`, `docs/`, `Source/` | Tạo nền tảng hiện tại; `git show --stat` là bằng chứng lịch sử. |
| 2026-09-23 | [docs/validation.md](docs/validation.md) ghi lần chạy pipeline, 3 tests và baseline mining | `data/processed/`, [docs/mining_baseline.json](docs/mining_baseline.json) | Chứng minh prototype Python, **không** chứng minh SQL/SSIS/SSAS/BI đã chạy. |
| 2026-09-17 | Git history ghi các commit khởi tạo repository và dữ liệu ban đầu | Git log | Là mốc lịch sử; chi tiết sản phẩm hiện tại nên đối chiếu commit 2026-09-23. |

**Quy tắc cập nhật:** cập nhật file này khi tiến độ/bằng chứng triển khai thay đổi; cập nhật [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) khi phạm vi, KPI hoặc kiến trúc được chốt/đổi. Không âm thầm giải quyết mâu thuẫn giữa hai file và repository.
