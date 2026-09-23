# Nguồn SBA FOIA

Giữ nguyên `FOIA_7a_FY2020_Present_asof_260630.csv` và `7a_504_foia_data_dictionary.xlsx` trong `data/raw/foia/`.
CSV này chỉ chứa 7(a); workbook có cả dictionary 7(a) và 504. Không áp dụng định nghĩa amount của 504 cho file 7(a).

Nguồn công bố: [SBA 7(a) & 504 FOIA](https://web.data.sba.gov/en/dataset/7-a-504-foia).
Khi tải lại, trang có thể đã đổi snapshot; dùng tên file và checksum trong `docs/data_profile.json` để đối chiếu.
CSV lớn được Git ignore; cần chia sẻ riêng hoặc cấu hình Git LFS. Khi nộp bài, copy cả CSV và XLSX vào thư mục `Data/`.
