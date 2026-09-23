# Checklist bàn giao và trạng thái

Đợt chuyển repo này hoàn thành phần định hướng và nền tảng. Đánh dấu `[x]` chỉ cho công việc đã thực hiện; không đồng nghĩa đã nộp môn học.

- [x] Profile toàn bộ CSV và đọc từ điển SBA.
- [x] Chuyển đề tài, lưu nguyên phần cũ trong archive.
- [x] Pipeline xuất 8 dimension + 1 fact, marts và tập mining.
- [x] DDL SQL Server và câu đối soát.
- [x] Thiết kế SSIS/SSAS, 15 manual, 15 MDX, 5 Pivot, 6 báo cáo BI.
- [ ] Chạy SSIS từ raw trên SQL Server và lưu project thật.
- [ ] Deploy/process SSAS, kiểm chứng 15 MDX và chụp 15 manual.
- [ ] Excel Pivot thật kết nối cube, Refresh All thành công.
- [ ] 3 Power BI PBIX và 3 Looker report/link.
- [x] Chạy baseline mining, đối chiếu Dummy/Logistic/Tree và ghi kết quả test.
- [ ] Hoàn thiện phân tích lỗi, minh họa mô hình và phần mining trong báo cáo cuối.
- [ ] Báo cáo Word, video, thông tin nhóm, database bàn giao.

## Bộ nộp cuối

```text
Submission/
  Data/        CSV + dictionary copy nguyên từ data/raw/foia/; kèm checksum
  Source/      SSIS project; SSAS project; Excel Pivot; mining source
  Database/    SBA7aDWH.mdf, SBA7aDWH_log.ldf; nên kèm .bak và restore notes
  Video/       Video demo chạy ETL, cube, queries, Pivot, BI, mining
  group_info.txt
  Document/    BaoCao_SBA7a.docx
```

Chỉ copy MDF/LDF khi database đã được detach/offline đúng quy trình; không copy file đang được engine ghi. Ghi version SQL Server, tên instance, cách attach/restore, connection settings cần đổi. Nên giữ backup .bak; không detach database đang dùng chung để lấy file. Không commit credentials hoặc file database lớn vào Git.

## Đề cương báo cáo Word

1. Bài toán, nguồn dữ liệu, lý do phù hợp tiêu chí, kết quả profiling và giới hạn.
2. SSIS: chọn dữ liệu, staging, cleansing, quality/rejects, dimension/fact load, audit.
3. SSAS: grain, sơ đồ bông tuyết, measures, hierarchies, role dates, build/process cube; 15 manual + 15 MDX + 5 Pivot kèm kết quả và nhận xét.
4. Power BI: 3 báo cáo; Looker Studio: 3 báo cáo; thông điệp nghiệp vụ và đối soát.
5. Data mining: class/cohort, leakage/censoring, split, baseline và metrics, diễn giải.
6. Kết luận, giới hạn, phân công, tài liệu tham khảo; phụ lục query và setup.

Repo hiện chỉ có đề cương, **không có bản Word giả hoàn chỉnh hay ảnh kết quả chưa chạy**. Báo cáo cuối viết sau khi có minh chứng SSIS/SSAS/BI thật.
