# Ghi chú tham khảo 5 đồ án năm trước

Đã trích đọc nội dung PDF cục bộ để tham khảo cấu trúc và cách triển khai; số trang dưới đây là tổng trang vật lý của file. Số trang in trên mục lục có thể lệch. Không sao chép số liệu/kết quả mẫu vào đề tài SBA.

| File trong references | Chủ đề / số trang | Điều áp dụng cho repo này |
|---|---|---|
| IS217_O21_21520429_21521505.pdf | Thiệt mạng do khủng bố/xung đột Israel–Palestine; 291 trang | Tách giới thiệu nguồn, schema, SSIS, phần phân tích; mô tả thao tác và kết quả bằng ảnh |
| IS217_O21_21521779_21522178.pdf | Phim điện ảnh; 414 trang | SSIS đi từng bảng và ràng buộc thực thi; phần mining có Decision Tree và điều chỉnh mô hình |
| [15]_IS217P11_22520542_22520464.pdf | Bài hát top trending; 258 trang | Có các báo cáo Looker riêng và so sánh nhiều thuật toán classification (gồm Naive Bayes) |
| [27]_IS217Q13_23520698_23521417.pdf | Bank Transaction Fraud Detection; 341 trang | Gần đề tài tài chính nhất; tham khảo bố cục phân tích, Looker và mô hình phân loại, không đồng nhất fraud với charge-off |
| [6]_IS217Q11_23520009_23520753.pdf | Phim điện ảnh; 389 trang | Mục 1.2.1 sơ đồ bông tuyết, dimension/bridge, từng data flow và quan hệ ưu tiên |

Các mẫu cho thấy cần chứng minh **quá trình xây dựng và kết quả chạy**, không chỉ có source hoặc slide lý thuyết. Áp dụng: mỗi truy vấn có câu hỏi → cấu hình/filter → kết quả → diễn giải; screenshot SSIS có row counts; mining có đối chiếu mô hình.

Không đưa bridge many-to-many từ đề tài phim vào SBA nếu không có quan hệ nhiều-nhiều thật. Không kế thừa giới hạn upload/tool version trong báo cáo cũ thành thông tin hiện tại. Với Looker, repo xuất mart nhỏ giữ đủ số liệu tổng hợp thay vì bỏ bớt bản ghi vì file lớn.
