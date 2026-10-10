# Data mining

> **Previous prototype / DEPRECATED AS CURRENT.** Module và baseline dưới đây thuộc pipeline cũ; chưa được kiểm chứng cho Q1–Q15 hiện hành và Target Schema Proposal star 1 Fact + 8 Dim. Xem [Source of Truth](../../docs/00_current_status.md).

Source thực thi nằm ở `src/mining.py`, dữ liệu trong `data/processed/` được sinh bởi `python -m src.main`.
Chạy từ repo root: `python -m src.mining`. Kết quả ghi `docs/mining_baseline.json` khi thành công.
[Cohort, features, leakage và giới hạn](../../docs/archive/other/05_bi_mining.md).
Khi đóng gói bài nộp, copy module src và requirements.txt vào Source để giữ khả năng chạy lại.
