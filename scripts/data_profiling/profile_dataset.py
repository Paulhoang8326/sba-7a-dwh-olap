"""Read-only profiling of the local SBA 7(a) FOIA snapshot.

Run from the repository root: python scripts/data_profiling/profile_dataset.py
Only writes docs/data_understanding and reports/data_profiling.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv"
WORKBOOK = ROOT / "data/raw/foia/7a_504_foia_data_dictionary.xlsx"
DOCS = ROOT / "docs/data_understanding"
REPORTS = ROOT / "reports/data_profiling"
NUMERIC = {"GrossApproval", "SBAGuaranteedApproval", "InitialInterestRate", "TermInMonths", "GrossChargeOffAmount", "JobsSupported"}
DATES = {"AsOfDate", "ApprovalDate", "FirstDisbursementDate", "PaidInFullDate", "ChargeOffDate"}
CODE = {"LocationID", "BorrZip", "BankFDICNumber", "BankNCUANumber", "BankZip", "ApprovalFY", "NaicsCode", "FranchiseCode", "CongressionalDistrict"}
STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC AS GU MP PR VI".split())

MEANINGS = {
"AsOfDate": ("Ngày ghi nhận snapshot", "Mốc quan sát trạng thái và số liệu công bố.", "Một snapshot, không phải lịch sử trạng thái."),
"Program": ("Chương trình SBA", "Chỉ báo chương trình 7(a) hoặc 504 của hồ sơ.", "CSV này thuộc 7(a); xác minh biểu diễn giá trị thực tế."),
"LocationID": ("Mã định danh lender SBA", "Mã lender duy nhất theo SBA.", "Không phải mã khoản vay; giữ số 0 đầu."),
"BorrName": ("Tên người vay/doanh nghiệp vay", "Tên chủ thể đi vay.", "Không chứng minh tính duy nhất của khoản vay."),
"BorrStreet": ("Đường/địa chỉ người vay", "Địa chỉ đường của người vay.", "Có thể là thông tin nhận dạng cá nhân."),
"BorrCity": ("Thành phố người vay", "Thành phố trong địa chỉ người vay.", "Không đồng nhất với địa điểm dự án."),
"BorrState": ("Bang người vay", "Bang trong địa chỉ người vay.", "Khác ProjectState."),
"BorrZip": ("ZIP người vay", "Mã bưu chính trong địa chỉ người vay.", "Mã định danh dạng chuỗi; giữ số 0 đầu."),
"BankName": ("Tên lender hiện được gán khoản vay", "Tổ chức cho vay hiện được gán khoản vay.", "Nguồn nói currently assigned; không mặc định lender ban đầu."),
"BankFDICNumber": ("Mã chứng nhận FDIC", "Mã chứng nhận FDIC của lender.", "Có thể không áp dụng với mọi loại lender."),
"BankNCUANumber": ("Mã charter NCUA", "Mã charter NCUA của lender.", "Có thể không áp dụng với mọi loại lender."),
"BankStreet": ("Đường/địa chỉ lender", "Địa chỉ đường của lender.", ""),
"BankCity": ("Thành phố lender", "Thành phố trong địa chỉ lender.", ""),
"BankState": ("Bang lender", "Bang trong địa chỉ lender.", "Khác ProjectState và BorrState."),
"BankZip": ("ZIP lender", "Mã bưu chính lender.", "Giữ số 0 đầu."),
"GrossApproval": ("Tổng số tiền vay được phê duyệt", "Quy mô khoản vay tại phê duyệt.", "Không phải dư nợ hiện tại; đơn vị USD cần xác minh theo nguồn phát hành."),
"SBAGuaranteedApproval": ("Số tiền SBA bảo lãnh khi phê duyệt", "Phần khoản vay được SBA bảo lãnh.", "Không phải khoản SBA đã chi trả."),
"ApprovalDate": ("Ngày phê duyệt", "Ngày khoản vay được phê duyệt.", "FY bắt đầu tháng 10; đối chiếu ApprovalFY."),
"ApprovalFY": ("Năm tài chính phê duyệt", "FY của phê duyệt khoản vay.", "Trong CSV là chuỗi; ngữ nghĩa là năm tài chính số nguyên."),
"FirstDisbursementDate": ("Ngày giải ngân đầu tiên", "Lần giải ngân đầu tiên nếu có.", "Thiếu có thể phản ánh chưa giải ngân hoặc nguồn không cung cấp."),
"ProcessingMethod": ("Phương thức xử lý/phê duyệt", "Hình thức xử lý khoản vay theo chương trình 7(a).", "Workbook liệt kê các mã phương thức; CSV có thể dùng nhãn thay mã."),
"InitialInterestRate": ("Lãi suất ban đầu", "Lãi suất tổng (base rate + spread) tại lúc phê duyệt.", "Đơn vị biểu diễn cần đối chiếu; không phải lãi suất hiện tại."),
"FixedorVariableInterestInd": ("Chỉ báo lãi suất cố định/biến đổi", "Kiểu lãi suất tại phê duyệt.", "Ý nghĩa mã cụ thể cần xác minh nếu workbook không nêu."),
"TermInMonths": ("Thời hạn vay (tháng)", "Độ dài kỳ hạn khoản vay.", "CSV là số thập phân; ngữ nghĩa số tháng."),
"NaicsCode": ("Mã NAICS", "Mã ngành kinh tế Bắc Mỹ.", "Dạng chuỗi; không coi là đại lượng số."),
"NaicsDescription": ("Mô tả NAICS", "Tên/mô tả ngành theo NAICS.", "Có thể chứa khoảng trắng cuối."),
"FranchiseCode": ("Mã franchise", "Mã franchise nếu áp dụng.", "Thiếu có thể là không áp dụng; cần xác minh."),
"FranchiseName": ("Tên franchise", "Tên franchise nếu áp dụng.", "Thiếu có thể là không áp dụng; cần xác minh."),
"ProjectCounty": ("Quận/hạt dự án", "County nơi dự án diễn ra.", ""),
"ProjectState": ("Bang dự án", "Bang nơi dự án diễn ra.", ""),
"SBADistrictOffice": ("Văn phòng khu vực SBA", "SBA district office liên quan hồ sơ.", "Vai trò chính xác trong quy trình cần xác minh."),
"CongressionalDistrict": ("Địa hạt quốc hội dự án", "Congressional district nơi dự án diễn ra.", "Giữ số 0 đầu; phụ thuộc ProjectState."),
"BusinessType": ("Loại hình người vay", "Individual, Partnership hoặc Corporation theo workbook.", "Các nhãn khác trong CSV cần xác minh."),
"BusinessAge": ("Nhóm tuổi đời doanh nghiệp", "Phân loại tuổi đời doanh nghiệp.", "Workbook không giải thích từng nhãn; cần xác minh."),
"LoanStatus": ("Trạng thái khoản vay tại snapshot", "Trạng thái hiện tại của hồ sơ vay.", "CANCLD=Cancelled; CHGOFF=Charged Off; COMMIT=Undisbursed; EXEMPT=đã giải ngân và chưa hủy/PIF/charge-off; workbook ghi PIF=Paid In Full nhưng CSV dùng nhãn P I F."),
"PaidInFullDate": ("Ngày trả hết nợ", "Ngày khoản vay đã được thanh toán đủ nếu áp dụng.", "Thiếu hợp lệ khi chưa PIF."),
"ChargeOffDate": ("Ngày SBA charge-off", "Ngày SBA ghi nhận charge-off nếu áp dụng.", "Thiếu hợp lệ khi chưa charge-off."),
"GrossChargeOffAmount": ("Tổng số dư đã charge-off", "Bao gồm phần được và không được bảo lãnh.", "Không phải tổn thất ròng sau thu hồi."),
"RevolverStatus": ("Chỉ báo khoản vay quay vòng", "0=term loan, 1=revolving line of credit theo workbook.", "CSV có thể dùng Y/N; cần xác minh mapping Y/N với 0/1."),
"JobsSupported": ("Số việc làm được hỗ trợ", "Jobs Created + Jobs Retained do lender báo trong đơn vay.", "SBA không audit/xác minh; không phải số việc làm thực tế độc lập."),
"CollateralInd": ("Chỉ báo tài sản bảo đảm", "Lender báo khoản vay có tài sản bảo đảm hay không.", "Ý nghĩa nhãn mã cần xác minh nếu workbook không nêu."),
"SoldSecMrktInd": ("Chỉ báo bán thị trường thứ cấp", "Y nếu khoản vay đã được bán trên thị trường thứ cấp.", "Nguồn nêu Y là trạng thái tĩnh sau khi bán; blank không tự suy ra N."),
}

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

def md_table(rows: list[list[str]], headers: list[str]) -> str:
    def clean(x: object) -> str:
        return str(x).replace("|", "\\|").replace("\n", "<br>")
    return "| " + " | ".join(headers) + " |\n|" + "|".join(["---"] * len(headers)) + "|\n" + "\n".join("| " + " | ".join(clean(v) for v in r) + " |" for r in rows) + "\n"

def main() -> None:
    if not SOURCE.exists() or SOURCE.stat().st_size < 100_000_000:
        raise SystemExit("CSV chưa tải đầy đủ (có thể chỉ là Git LFS pointer).")
    with SOURCE.open("rb") as f:
        if f.read(100).startswith(b"version https://git-lfs"):
            raise SystemExit("CSV là Git LFS pointer, chưa tải nội dung.")
    DOCS.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SOURCE, dtype=str, keep_default_na=False, encoding="utf-8", low_memory=False)
    n = len(df); cols = list(df.columns)
    if len(cols) != 42 or set(cols) != set(MEANINGS):
        raise SystemExit("Schema không khớp 42 thuộc tính đã đối chiếu; cần cập nhật script trước khi chạy.")
    book = load_workbook(WORKBOOK, read_only=True, data_only=True)
    sheet = book["7(a) Data Dictionary"]
    official = {str(row[0]).strip(): str(row[1]).strip() for row in sheet.values if row[0] and row[1]}
    missing_def = sorted(set(cols) - set(official))
    if missing_def:
        raise SystemExit(f"Workbook thiếu định nghĩa: {missing_def}")
    # Exact duplicates preserve every byte-level field value as decoded by CSV; no whitespace normalization.
    exact = int(df.duplicated(keep=False).sum())
    extra = int(df.duplicated().sum())
    group_sizes = df.groupby(cols, dropna=False, sort=False).size()
    exact_groups = int((group_sizes > 1).sum())
    max_group = int(group_sizes.max())
    # A weak composite only shows matching descriptions, never establishes a unique loan.
    weak_cols = ["BorrName", "BankName", "ApprovalDate", "GrossApproval", "ProjectState"]
    weak = df.groupby(weak_cols, dropna=False, sort=False).size()
    potential = int(weak[weak > 1].sum())
    sample_groups = weak[weak > 1].sort_values(ascending=False).head(5)
    profile = []; numeric_rows = []; date_rows = []; categorical = []; missing_rows = []
    fy = df["ApprovalFY"].str.strip(); status = df["LoanStatus"].str.strip()
    status_for_rules = status.replace({"P I F":"PIF"})  # comparison only; source/output retain P I F
    for col in cols:
        s = df[col]; blank = s.str.strip().eq(""); non = s[~blank]
        uniq = int(non.nunique(dropna=True)); samples = non.drop_duplicates().head(3).tolist()
        kind = "date (CSV: text)" if col in DATES else "numeric (CSV: text)" if col in NUMERIC else "code (CSV: text)" if col in CODE else "text"
        profile.append({"Attribute": col, "Data Type": kind, "Non-null Count": n-int(blank.sum()), "Null Count": int(blank.sum()), "Null %": round(100*blank.mean(), 4), "Unique Count": uniq, "Unique %": round(100*uniq/max(1,n-int(blank.sum())),4), "Sample Values": " | ".join(samples)})
        if blank.any():
            for key, group in (("ApprovalFY", fy), ("LoanStatus", status)):
                for value, count in group[blank].value_counts().items():
                    missing_rows.append({"Attribute": col, "Missing Count": int(blank.sum()), "Missing %": round(100*blank.mean(),4), "Group By": key, "Group": value, "Group Missing": int(count), "Group Rows": int((group==value).sum()), "Group Missing %": round(100*count/(group==value).sum(),4)})
        if col in NUMERIC:
            nums = pd.to_numeric(s.mask(blank), errors="coerce")
            d = nums.describe(percentiles=[.25,.5,.75])
            numeric_rows.append({"Attribute":col,"Parse Fail":int((~blank & nums.isna()).sum()),"Min":d.get("min"),"Max":d.get("max"),"Mean":d.get("mean"),"Median":d.get("50%"),"Std":d.get("std"),"Q1":d.get("25%"),"Q3":d.get("75%"),"Zero Count":int((nums==0).sum()),"Negative Count":int((nums<0).sum())})
        elif col in DATES:
            dates = pd.to_datetime(s.mask(blank), format="%Y-%m-%d", errors="coerce")
            formats = Counter("YYYY-MM-DD" if re.fullmatch(r"\d{4}-\d{2}-\d{2}",v) else "other" for v in non)
            date_rows.append({"Attribute":col,"Min Date":str(dates.min().date()) if dates.notna().any() else "", "Max Date":str(dates.max().date()) if dates.notna().any() else "", "Parse Fail":int((~blank & dates.isna()).sum()),"Missing":int(blank.sum()),"Formats":json.dumps(formats,ensure_ascii=False)})
        else:
            counts = non.value_counts().head(10)
            for rank,(value,count) in enumerate(counts.items(),1):
                categorical.append({"Attribute":col,"Unique Count":uniq,"Rank":rank,"Value":value,"Count":int(count),"Percent of Non-null":round(100*count/len(non),4)})
    write_csv(REPORTS/"column_profile.csv",profile,list(profile[0]))
    write_csv(REPORTS/"numeric_profile.csv",numeric_rows,list(numeric_rows[0]))
    write_csv(REPORTS/"date_profile.csv",date_rows,list(date_rows[0]))
    write_csv(REPORTS/"categorical_distribution.csv",categorical,list(categorical[0]))
    write_csv(REPORTS/"missing_values.csv",missing_rows,list(missing_rows[0]))
    dup_rows = [{"Metric":"exact duplicate rows (including first occurrence)","Count":exact,"Percentage":round(100*exact/n,4)}, {"Metric":"exact surplus copies","Count":extra,"Percentage":round(100*extra/n,4)}, {"Metric":"exact duplicate groups","Count":exact_groups,"Percentage":""}, {"Metric":"max exact group size","Count":max_group,"Percentage":""}, {"Metric":"weak composite matching rows","Count":potential,"Percentage":round(100*potential/n,4)}]
    write_csv(REPORTS/"duplicate_summary.csv",dup_rows,list(dup_rows[0]))
    nums = {c:pd.to_numeric(df[c].str.strip().replace("",pd.NA),errors="coerce") for c in NUMERIC}
    dt = {c:pd.to_datetime(df[c].str.strip().replace("",pd.NA),format="%Y-%m-%d",errors="coerce") for c in DATES}
    checks = []
    def issue(attribute, issue_text, mask, impact, treatment, level="Dấu hiệu cần xác minh"):
        count = int(mask.sum());
        if count: checks.append({"ID":f"DQ{len(checks)+1:02d}","Attribute":attribute,"Issue":issue_text,"Affected Records":count,"Percentage":round(100*count/n,4),"Potential Impact":impact,"Suggested Treatment":treatment,"Classification":level})
    for c in NUMERIC:
        issue(c,"Giá trị âm",nums[c]<0,"Tổng hợp và phân bố sai","Đối chiếu hồ sơ nguồn và quy tắc nghiệp vụ")
        issue(c,"Không parse được số",df[c].str.strip().ne("") & nums[c].isna(),"Không tính được chỉ tiêu","Xác minh kiểu/format nguồn")
    issue("SBAGuaranteedApproval","Vượt GrossApproval",nums["SBAGuaranteedApproval"]>nums["GrossApproval"],"Tỷ lệ bảo lãnh bất hợp lý","Đối chiếu SBA")
    for c in ("InitialInterestRate","FixedorVariableInterestInd","BusinessType","BusinessAge","CongressionalDistrict"):
        issue(c,"Giá trị thiếu, chưa rõ lý do",df[c].str.strip().eq(""),"Giảm mức phủ khi phân tích theo thuộc tính","Xác minh với nguồn và giữ riêng nhóm thiếu")
    issue("FirstDisbursementDate","P I F nhưng thiếu ngày giải ngân đầu tiên",status_for_rules.eq("PIF")&df["FirstDisbursementDate"].str.strip().eq(""),"Không xác định được mốc giải ngân","Xác minh khả năng ngày không được cung cấp")
    issue("TermInMonths","Kỳ hạn bằng 0",nums["TermInMonths"]==0,"Phân tích kỳ hạn bị méo","Kiểm tra quy tắc nghiệp vụ của sản phẩm")
    issue("InitialInterestRate","Lãi suất ban đầu bằng 0",nums["InitialInterestRate"]==0,"Phân tích lãi suất bị méo","Xác minh lãi suất thật hay mã thiếu")
    issue("GrossChargeOffAmount","Số tiền charge-off dương nhưng status khác CHGOFF",(nums["GrossChargeOffAmount"]>0)&status_for_rules.ne("CHGOFF"),"Mâu thuẫn diễn giải kết quả","Đối chiếu định nghĩa trạng thái/snapshot")
    issue("ChargeOffDate","CHGOFF nhưng thiếu ngày",status_for_rules.eq("CHGOFF")&df["ChargeOffDate"].str.strip().eq(""),"Thiếu mốc thời gian kết quả","Kiểm tra độ trễ cập nhật nguồn")
    issue("PaidInFullDate","PIF nhưng thiếu ngày",status_for_rules.eq("PIF")&df["PaidInFullDate"].str.strip().eq(""),"Thiếu mốc trả hết","Kiểm tra độ trễ cập nhật nguồn")
    issue("PaidInFullDate","Có ngày PIF nhưng trạng thái không phải P I F",status_for_rules.ne("PIF")&df["PaidInFullDate"].str.strip().ne(""),"Mâu thuẫn trạng thái/ngày","Đối chiếu độ trễ và quy tắc trạng thái")
    issue("LoanStatus","Nhãn P I F khác mã PIF trong workbook",status.eq("P I F"),"Đối chiếu mã và tổng hợp trạng thái cần mapping có tài liệu","Xác nhận P I F tương ứng PIF theo SBA")
    for c in DATES:
        issue(c,"Ngày không parse được",df[c].str.strip().ne("")&dt[c].isna(),"Không thể sắp xếp thời gian","Đối chiếu format nguồn")
        if c != "AsOfDate":
            issue(c,"Ngày sau AsOfDate",dt[c]>dt["AsOfDate"],"Sự kiện xảy ra sau snapshot","Xác minh cập nhật hoặc ngày nguồn")
        if c in ("FirstDisbursementDate","PaidInFullDate","ChargeOffDate"):
            issue(c,"Ngày trước ApprovalDate",dt[c]<dt["ApprovalDate"],"Trình tự thời gian bất thường","Đối chiếu hồ sơ và quy tắc thời gian")
    fy_expected = dt["ApprovalDate"].dt.year + (dt["ApprovalDate"].dt.month>=10).astype(int)
    issue("ApprovalFY","Không khớp FY tính từ ApprovalDate",pd.to_numeric(fy,errors="coerce").ne(fy_expected),"Phân tích theo cohort sai","Xác minh quy ước FY của nguồn")
    issue("NaicsCode","Không đúng 6 chữ số",~df["NaicsCode"].str.strip().str.fullmatch(r"\d{6}"),"Nhóm ngành sai hoặc thiếu độ chi tiết","Đối chiếu NAICS gốc và phiên bản mã")
    for c in ("BorrState","BankState","ProjectState"):
        issue(c,"Mã bang/lãnh thổ không thuộc danh sách USPS",~df[c].str.strip().isin(STATES),"Phân tích địa lý sai","Đối chiếu mã địa lý nguồn")
    for c in ("LoanStatus","Program","FixedorVariableInterestInd","CollateralInd","RevolverStatus"):
        issue(c,"Có khoảng trắng đầu/cuối",df[c].str.strip().ne(df[c]),"Tạo nhãn phân loại trùng nghĩa","Đối chiếu dạng gốc trước khi chuẩn hóa")
    issue("All attributes","Bản ghi trùng hoàn toàn (tính cả bản gốc)",df.duplicated(keep=False),"Đếm dòng có thể cao hơn đếm khoản vay nếu trùng thực","Cần mã khoản vay hoặc đối soát SBA trước khi kết luận")
    write_csv(REPORTS/"quality_issues.csv",checks,list(checks[0]) if checks else ["ID","Attribute","Issue","Affected Records","Percentage","Potential Impact","Suggested Treatment","Classification"])
    digest = hashlib.sha256()
    with SOURCE.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            digest.update(chunk)
    sha = digest.hexdigest()
    fy_counts = fy.value_counts().sort_index()
    sizes = {"CSV":SOURCE.stat().st_size,"XLSX dictionary":WORKBOOK.stat().st_size}
    overview = ["# Tổng quan dữ liệu SBA 7(a)","",f"Nguồn: `{SOURCE.relative_to(ROOT)}`; SHA-256 `{sha}`. Workbook: `{WORKBOOK.relative_to(ROOT)}`, sheet `7(a) Data Dictionary`. Chỉ đọc file gốc, không biến đổi dữ liệu.","",f"- **1 CSV dữ liệu** ({sizes['CSV']:,} byte; {sizes['CSV']/2**20:.2f} MiB); 1 workbook mô tả ({sizes['XLSX dictionary']:,} byte). Tổng hai file: {sum(sizes.values()):,} byte.",f"- **{n:,} bản ghi, {len(cols)} thuộc tính**. CSV là một file, nên kiểm tra khác biệt schema/kiểu hoặc trùng giữa nhiều file không áp dụng.",f"- Bộ nhớ DataFrame chuỗi (deep): **{df.memory_usage(deep=True).sum()/2**20:.2f} MiB**. Cần thêm bộ nhớ cho thống kê, nhóm trùng và cột số/ngày; số này không phải RAM đỉnh.","- Trên đĩa CSV lưu mọi giá trị dưới dạng text; kiểu ngữ nghĩa và các thống kê parse trình bày trong báo cáo kèm theo.","- FY2026 chỉ tới 30/06/2026; không xem là cả FY.","","## Tên thuộc tính", "", ", ".join(f"`{c}`" for c in cols),"","## Số dòng theo ApprovalFY","",md_table([[k,f"{v:,}"] for k,v in fy_counts.items()],["ApprovalFY","Số dòng"]),"## Khoảng ngày","",md_table([[r["Attribute"],r["Min Date"],r["Max Date"],r["Missing"],r["Parse Fail"]] for r in date_rows],["Attribute","Min","Max","Thiếu","Không parse"]),"## Giới hạn diễn giải","","Một dòng là một bản ghi công bố; không có mã khoản vay công khai để chứng minh mỗi dòng là một khoản vay duy nhất. `AsOfDate` là ngày snapshot, các ngày sự kiện có thể thuộc ngoài khoảng năm phê duyệt. Kiểu chuỗi của mã và ngày là kiểu đọc từ CSV, không nên suy ra số thực chỉ vì toàn chữ số."]
    (DOCS/"data_overview.md").write_text("\n".join(overview),encoding="utf-8")
    method_codes = []
    for line in official["ProcessingMethod"].splitlines():
        match = re.search(r"([^\t•�]+?)\s*=\s*([A-Z0-9]+)\s*$",line)
        if match:
            method_codes.append([match.group(2),match.group(1).strip()])
    def semantic_type(c: str) -> str:
        if c in DATES: return "date"
        if c in ("TermInMonths","JobsSupported"): return "integer count"
        if c in NUMERIC: return "decimal"
        if c == "ApprovalFY": return "integer FY"
        if c in CODE: return "code"
        return "category/text"
    dictionary = ["# Data Dictionary – SBA 7(a)","", "Nguồn định nghĩa: workbook SBA `7a_504_foia_data_dictionary.xlsx`, sheet `7(a) Data Dictionary`. Diễn giải tiếng Việt dưới đây dựa trên định nghĩa gốc; các nhãn chưa được workbook giải mã đều ghi cần xác minh. CSV lưu mọi ô dưới dạng text; `Data Type` ghi kiểu hiện tại / kiểu ngữ nghĩa.","",md_table([[i,c,MEANINGS[c][0],"text / "+semantic_type(c),next((v for v in df[c] if v.strip()),""),MEANINGS[c][1],MEANINGS[c][2]] for i,c in enumerate(cols,1)],["STT","Attribute","Description","Data Type","Example Value","Business Meaning","Notes"]),"## Mã ProcessingMethod trong workbook","","Workbook cung cấp các cặp nhãn/mã 7(a) sau. CSV hiện lưu nhãn; bảng mã chỉ hỗ trợ đối chiếu, không thay giá trị CSV.","",md_table(method_codes,["Mã","Nhãn tiếng Anh theo SBA"]),"## Đối chiếu nguồn","","Mọi thuộc tính trên đều có định nghĩa trong sheet 7(a). CSV ghi `P I F` trong khi workbook ghi `PIF`; quy tắc kiểm tra so theo mapping tạm thời, chưa thay dữ liệu. Các mã giá trị khác chưa được workbook giải thích đầy đủ: `BusinessAge`, `FixedorVariableInterestInd`, `CollateralInd`, `RevolverStatus` (workbook ghi 0/1, CSV dùng Y/N), `SoldSecMrktInd` khi blank. Cần xác minh trước khi quy chuẩn ý nghĩa."]
    (DOCS/"data_dictionary.md").write_text("\n".join(dictionary),encoding="utf-8")
    missing_sorted = sorted((p for p in profile if p["Null Count"]),key=lambda x:-x["Null Count"])
    status_counts = status.value_counts()
    concentration = []
    for c in ["FirstDisbursementDate","BankFDICNumber","BankNCUANumber","FranchiseName","SoldSecMrktInd","ChargeOffDate","PaidInFullDate"]:
        for dimension in ["ApprovalFY","LoanStatus"]:
            rr = [r for r in missing_rows if r["Attribute"]==c and r["Group By"]==dimension]
            if rr:
                high = max(rr,key=lambda r:r["Group Missing %"])
                concentration.append([c,dimension,high["Group"],high["Group Missing"],high["Group Rows"],high["Group Missing %"]])
    report = ["# Data Profiling – SBA 7(a)","",f"Chạy toàn bộ {n:,} dòng; dữ liệu gốc không bị sửa. CSV chi tiết trong `reports/data_profiling/`. `Null` là ô rỗng hoặc chỉ khoảng trắng; số khác 0 và ngày được parse để thống kê nhưng không ghi ngược vào nguồn.","","## Hồ sơ cột","",md_table([[p["Attribute"],p["Data Type"],p["Non-null Count"],p["Null Count"],p["Null %"],p["Unique Count"],p["Unique %"]] for p in profile],["Attribute","Data Type","Non-null","Null","Null %","Unique","Unique %"]),"Các giá trị ví dụ nằm trong `column_profile.csv`; phân phối top 10 của mọi cột phân loại/mã nằm trong `categorical_distribution.csv`.","","## Cột số","",md_table([[r[k] for k in ("Attribute","Min","Max","Mean","Median","Std","Q1","Q3","Zero Count","Negative Count","Parse Fail")] for r in numeric_rows],["Attribute","Min","Max","Mean","Median","Std","Q1","Q3","Zero","Negative","Parse fail"]),"## Ngày","",md_table([[r[k] for k in ("Attribute","Min Date","Max Date","Missing","Parse Fail","Formats")] for r in date_rows],["Attribute","Min","Max","Missing","Parse fail","Formats"]),"## Thiếu dữ liệu","",md_table([[p["Attribute"],p["Null Count"],p["Null %"]] for p in missing_sorted],["Attribute","Missing","%"]),"`missing_values.csv` chứa số thiếu chia theo FY và LoanStatus (mẫu số là số dòng của từng nhóm). Nhóm có tỷ lệ thiếu cao nhất trong từng lát cắt:","",md_table(concentration,["Attribute","Theo","Nhóm","Thiếu","Dòng nhóm","% thiếu nhóm"]),"Thiếu `ChargeOffDate` ngoài CHGOFF và `PaidInFullDate` ngoài `P I F` thường phù hợp điều kiện áp dụng của trường. `FirstDisbursementDate` thiếu toàn bộ ở CANCLD và COMMIT, tương ứng trạng thái hủy/chưa giải ngân; còn 3 dòng `P I F` thiếu ngày giải ngân cần xác minh. `BankFDICNumber`/`BankNCUANumber` có thể không áp dụng theo loại lender; `FranchiseCode/Name`, `SoldSecMrktInd` còn cần kiểm tra nghiệp vụ. Không coi tất cả ô trống là lỗi.","","## Trùng lặp","",md_table([[x["Metric"],x["Count"],x["Percentage"]] for x in dup_rows],["Metric","Count","% trên toàn bộ dòng"]),f"Composite yếu dùng `{', '.join(weak_cols)}` chỉ để sàng lọc; {potential:,} dòng cùng composite trong nhóm từ 2 dòng; nhóm lớn nhất có {int(sample_groups.iloc[0]) if len(sample_groups) else 0} dòng. Không đủ cơ sở gọi chúng là cùng khoản vay. Exact duplicate cũng chưa chứng minh lỗi do không có LoanID công khai. Không xóa dòng nào.","","## Trạng thái","",md_table([[k,int(v),round(100*v/n,2)] for k,v in status_counts.items()],["LoanStatus","Số dòng","%"]),"CSV dùng nhãn `P I F`; workbook mô tả mã `PIF`. Script chỉ dùng mapping tạm trong phép kiểm tra, không sửa giá trị nguồn.","","## Kiểm tra nhất quán","",md_table([[q["Attribute"],q["Issue"],q["Affected Records"],q["Percentage"]] for q in checks],["Attribute","Dấu hiệu","Số dòng","%"]),"Các kiểm tra là dấu hiệu cần điều tra, trừ khi có quy tắc nguồn xác minh. Mã bang so với danh sách USPS gồm 50 bang, DC và lãnh thổ; NAICS so dạng 6 chữ số, không chứng minh mã đang hiệu lực trong một phiên bản NAICS cụ thể. Kiểm tra ngày dùng thứ tự sự kiện và ngày snapshot, không tự sửa bản ghi."]
    (DOCS/"data_profiling_report.md").write_text("\n".join(report),encoding="utf-8")
    quality = ["# Báo cáo chất lượng dữ liệu", "", "Các hàng là dấu hiệu hoặc điểm cần xác minh trên snapshot 30/06/2026. Không có thao tác làm sạch. Tỷ lệ lấy trên toàn bộ bản ghi; một dòng có thể nằm trong nhiều vấn đề.","",md_table([[q[k] for k in ("ID","Attribute","Issue","Affected Records","Percentage","Potential Impact","Suggested Treatment")] for q in checks],["ID","Attribute","Issue","Affected Records","Percentage","Potential Impact","Suggested Treatment"]),"## Các giới hạn trước giai đoạn kế tiếp","","- Chưa có public LoanID đáng tin cậy; không được đồng nhất số dòng với số khoản vay duy nhất.","- Các giá trị trống mang tính điều kiện nghiệp vụ cần phân biệt theo LoanStatus và loại lender; xem `missing_values.csv`.","- FY2026 mới tới 30/06/2026; kết quả của cohort mới chịu thời gian quan sát ngắn.","- Snapshot hiện tại không cho phép suy ra lịch sử thay đổi trạng thái, dư nợ hiện tại, thu hồi hoặc tổn thất ròng.","- Xác minh mapping mã chưa được workbook giải thích trước khi định nghĩa KPI/chuyển đổi."]
    (DOCS/"data_quality_report.md").write_text("\n".join(quality),encoding="utf-8")
    print(json.dumps({"rows":n,"columns":len(cols),"sha256":sha,"exact_rows":exact,"exact_surplus":extra,"issues":checks,"memory_mib":round(df.memory_usage(deep=True).sum()/2**20,2)},ensure_ascii=True))

if __name__ == "__main__":
    main()
