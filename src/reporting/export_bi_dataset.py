"""Export the flat record-level dataset used by Looker Studio (and Power BI Import fallback).

Mirrors sql/07_export_bi_dataset.sql (Fact_Loan joined to the 8 dimensions), but reads the
Chapter 2 SSIS input `data/staging/sba7a_standardized.tsv` so it can run without SQL Server.
Keeps every published record (BR-POP-01, exact duplicates included) and only the columns the
Chapter 4 reports use, so the file stays under Looker Studio's 100 MB CSV upload limit.

Usage: python -m src.reporting.export_bi_dataset [input.tsv] [output.csv]
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN = ROOT / "data/staging/sba7a_standardized.tsv"
DEFAULT_OUT = ROOT / "data/processed/bi/sba7a_bi_dataset.csv"

# Same labels as sql/03_backfill_ssas_dimension_attributes.sql (approved 2026-10-28).
TERM_BANDS = {
    "ZERO": "1. 0 months",
    "SHORT": "2. 1-60 months",
    "MEDIUM": "3. 61-119 months",
    "TERM_120": "4. 120 months",
    "LONG": "5. 121-240 months",
    "VERY_LONG": "6. 241+ months",
}

# NAICS 2-digit sector titles (candidate mapping, BR-NAICS-01 still PENDING_VERIFICATION).
NAICS_SECTORS = {
    "11": "Agriculture, Forestry, Fishing and Hunting",
    "21": "Mining, Quarrying, and Oil and Gas Extraction",
    "22": "Utilities",
    "23": "Construction",
    "31-33": "Manufacturing",
    "42": "Wholesale Trade",
    "44-45": "Retail Trade",
    "48-49": "Transportation and Warehousing",
    "51": "Information",
    "52": "Finance and Insurance",
    "53": "Real Estate and Rental and Leasing",
    "54": "Professional, Scientific, and Technical Services",
    "55": "Management of Companies and Enterprises",
    "56": "Administrative and Support and Waste Management",
    "61": "Educational Services",
    "62": "Health Care and Social Assistance",
    "71": "Arts, Entertainment, and Recreation",
    "72": "Accommodation and Food Services",
    "81": "Other Services (except Public Administration)",
    "92": "Public Administration",
}

# Derived labels such as "State - County" or "FY-Quarter" are built as Looker calculated
# fields instead of stored columns, to keep the file well below 100 MB.
OUT_COLUMNS = [
    "ApprovalDate", "FiscalYear", "FiscalQuarter",
    "ProjectState", "ProjectCounty", "NaicsSector", "BankName", "ProcessingMethod",
    "RawStatus", "LoanStatus", "TermBand",
    "GrossApproval", "SBAGuaranteedApproval", "GrossChargeOffAmount", "JobsSupported",
    "ChargeOffRecord",
]


def fiscal_quarter(d: date) -> int:
    # Federal FY starts 1 October: Oct-Dec = Q1, Jan-Mar = Q2, Apr-Jun = Q3, Jul-Sep = Q4.
    return ((d.month - 10) % 12) // 3 + 1


def blank(v: str, label: str = "(Missing)") -> str:
    v = (v or "").strip()
    return v if v else label


def money(v: str) -> str:
    v = (v or "").strip()
    if not v:
        return "0"
    return v[:-3] if v.endswith(".00") else v


def convert(src: Path, dst: Path) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with src.open(newline="", encoding="utf-8") as fin, dst.open("w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin, delimiter="\t")
        writer = csv.writer(fout)
        writer.writerow(OUT_COLUMNS)
        for r in reader:
            d = date.fromisoformat(r["ApprovalDate"][:10])
            fy = int(r["FiscalYearDerived"])
            fq = fiscal_quarter(d)
            sector_code = (r["NaicsSectorCode"] or "").strip()
            sector = (f"{sector_code} - {NAICS_SECTORS.get(sector_code, 'Unmapped')}"
                      if sector_code else "(Missing)")
            raw_status = blank(r["RawStatus"])
            writer.writerow([
                d.isoformat(), fy, f"Q{fq}",
                blank(r["ProjectState"]), blank(r["ProjectCounty"]),
                sector, blank(r["BankName"]), blank(r["ProcessingMethod"]),
                raw_status, blank(r["CanonicalStatus"]),
                TERM_BANDS.get(r["TermBandCode"].strip(), "(Missing)"),
                money(r["GrossApproval"]), money(r["SBAGuaranteedApproval"]),
                money(r["GrossChargeOffAmount"]), (r["JobsSupported"] or "0").strip() or "0",
                1 if raw_status == "CHGOFF" else 0,
            ])
            n += 1
    return n


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    rows = convert(src, dst)
    print(f"{rows} rows -> {dst} ({dst.stat().st_size / 1e6:.1f} MB)")
