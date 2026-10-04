"""Phase 1 preprocessing: raw SBA 7(a) FOIA CSV -> standardized TSV + audit reports.

Run: ``python -m src.etl.preprocess``

Implements P1.1-P1.16 of ``docs/etl/etl_implementation_plan.md``. No record is ever
dropped (BR-POP-01): output row count == source record count == 388,338.

Each plan step is a function (``record_ordinal``, ``clean_columns``, ``parse_types``,
``check_dates``, ``flag_duplicates``, ``map_status``, ... ``column_selection``,
``before_after``) so ``notebooks/01_preprocessing.ipynb`` (P1.17) can call them one by
one; ``standardize`` + ``export_outputs`` chain them for ``run``.

Outputs
-------
``data/staging/<source stem>_clean.csv``
    Cleaned copy of the source file: same 42 columns, same column and record order
    (CSV line i+1 = SourceRecordOrdinal i), UTF-8, CRLF, RFC 4180 quoting. Text is
    trimmed with CR/LF/tab -> space; dates ISO; amounts per the rule below;
    ``TermInMonths``/``JobsSupported``/``ApprovalFY`` as integers. ``LoanStatus`` keeps
    the source label (``P I F``); exact duplicates are kept. Contains ``Borr*`` (PII),
    so it stays under the git-ignored ``data/staging``.
``data/staging/sba7a_standardized.tsv``
    UTF-8 (no BOM), header row, tab-delimited, CRLF row delimiter, no text qualifier,
    NULL written as an empty field. Contains no timestamp, so two runs on the same
    source produce a byte-identical file.
``reports/preprocessing/manifest.json``
    Source checksum/schema, run metadata, rule version, output checksums, counts.
``reports/preprocessing/dq_issues.csv``
    One row per (record, issue[, column]). Flags only; values are never corrected.
``reports/preprocessing/reconciliation.csv``
    Raw CSV vs. each output re-read from disk: rows, measure sums, counts by FY/status.
``reports/preprocessing/column_selection.csv``
    P1.15: 42 source columns with missing/distinct counts, KEEP/DROP, TSV targets, reason.
``reports/preprocessing/before_after.csv``
    P1.16: raw vs. TSV rows, columns, blank cells, distinct values, measure sums.

Lookup columns (P1.13)
----------------------
Columns used as Dim business keys get a separate ``*Lookup`` column where NULL is
replaced by ``(Missing)`` so SSIS Lookup never has to match NULL = NULL (plan §7 R3).
The plain column keeps NULL.

=========================  ==================  ===================
Lookup column              Source column       Dim
=========================  ==================  ===================
ProjectStateLookup         ProjectState        DimProjectGeography
ProjectCountyLookup        ProjectCounty       DimProjectGeography
NaicsCodeLookup            NaicsCode           DimIndustry
NaicsDescriptionLookup     NaicsDescription    DimIndustry
LocationIDLookup           LocationID          DimLender
ProcessingMethodLookup     ProcessingMethod    DimLoanProfile
RawStatusLookup            RawStatus           DimLoanStatus
BusinessTypeLookup         BusinessTypeRaw     DimBusiness
BusinessAgeLookup          BusinessAgeRaw      DimBusiness
=========================  ==================  ===================

``TermBandCode`` is never NULL (``MISSING`` band) and ``ApprovalDate`` maps to the
DimDate special members, so neither needs a lookup column.

Amounts are written with at least 2 decimals but never rounded: a source value with
more decimals (2 rows of ``SBAGuaranteedApproval``) keeps its precision and is flagged
``AMOUNT_SCALE_GT_2``, so measure sums reconcile exactly with the raw file.

``DQFlagCount`` = number of rows in ``dq_issues.csv`` for that record (includes the
``EXACT_DUPLICATE`` issue).
"""
import argparse
import csv
import hashlib
import json
import operator
import platform
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv'
EXPECTED_SHA256 = '6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe'
STAGING_DIR = ROOT / 'data/staging'
REPORT_DIR = ROOT / 'reports/preprocessing'
TSV_NAME = 'sba7a_standardized.tsv'
RULE_VERSION = 'P1-2026-10-01'
MISSING_TOKEN = '(Missing)'

SOURCE_COLUMNS = [
    'AsOfDate', 'Program', 'LocationID', 'BorrName', 'BorrStreet', 'BorrCity', 'BorrState',
    'BorrZip', 'BankName', 'BankFDICNumber', 'BankNCUANumber', 'BankStreet', 'BankCity',
    'BankState', 'BankZip', 'GrossApproval', 'SBAGuaranteedApproval', 'ApprovalDate',
    'ApprovalFY', 'FirstDisbursementDate', 'ProcessingMethod', 'InitialInterestRate',
    'FixedorVariableInterestInd', 'TermInMonths', 'NaicsCode', 'NaicsDescription',
    'FranchiseCode', 'FranchiseName', 'ProjectCounty', 'ProjectState', 'SBADistrictOffice',
    'CongressionalDistrict', 'BusinessType', 'BusinessAge', 'LoanStatus', 'PaidInFullDate',
    'ChargeOffDate', 'GrossChargeOffAmount', 'RevolverStatus', 'JobsSupported',
    'CollateralInd', 'SoldSecMrktInd',
]
DATE_COLUMNS = ['AsOfDate', 'ApprovalDate', 'FirstDisbursementDate', 'PaidInFullDate', 'ChargeOffDate']
AMOUNT_COLUMNS = ['GrossApproval', 'SBAGuaranteedApproval', 'GrossChargeOffAmount']
INTEGER_COLUMNS = ['TermInMonths', 'JobsSupported']
MEASURES = AMOUNT_COLUMNS + ['JobsSupported']

KNOWN_STATUSES = {'CANCLD', 'CHGOFF', 'COMMIT', 'EXEMPT', 'P I F'}
STATUS_CANONICAL = {'P I F': 'PIF'}
SECTOR_RANGES = {'31': '31-33', '32': '31-33', '33': '31-33', '44': '44-45', '45': '44-45',
                 '48': '48-49', '49': '48-49'}

# Source column -> (staging column, lookup column)
LOOKUP_COLUMNS = {
    'ProjectState': 'ProjectStateLookup',
    'ProjectCounty': 'ProjectCountyLookup',
    'NaicsCode': 'NaicsCodeLookup',
    'NaicsDescription': 'NaicsDescriptionLookup',
    'LocationID': 'LocationIDLookup',
    'ProcessingMethod': 'ProcessingMethodLookup',
    'RawStatus': 'RawStatusLookup',
    'BusinessTypeRaw': 'BusinessTypeLookup',
    'BusinessAgeRaw': 'BusinessAgeLookup',
}
OUTPUT_COLUMNS = [
    'SourceFileID', 'SourceRecordOrdinal', 'AsOfDate', 'ApprovalDate', 'ApprovalFY',
    'FiscalYearDerived', 'ProjectState', 'ProjectCounty', 'NaicsCode', 'NaicsDescription',
    'NaicsSectorCode', 'SectorMappingStatus', 'LocationID', 'BankName', 'ProcessingMethod',
    'RawStatus', 'CanonicalStatus', 'TermInMonths', 'TermBandCode', 'BusinessTypeRaw',
    'BusinessAgeRaw', 'BusinessTypeValueStatus', 'BusinessAgeValueStatus', 'GrossApproval',
    'SBAGuaranteedApproval', 'GrossChargeOffAmount', 'JobsSupported', 'IsExactDuplicate',
    'DQFlagCount', *LOOKUP_COLUMNS.values(),
]
# Dim business keys checked for case-only variants (plan §7 R7); tuples are composite keys.
CASE_KEYS = [('ProjectState',), ('ProjectCounty',), ('NaicsCode', 'NaicsDescription'),
             ('LocationID',), ('BankName',), ('ProcessingMethod',), ('BusinessTypeRaw',),
             ('BusinessAgeRaw',)]

# P1.15 lineage: source column -> TSV columns it feeds (first = direct copy). Audit columns
# built from all columns (IsExactDuplicate, DQFlagCount) are not lineage and are left out.
SOURCE_TO_TARGET = {
    'AsOfDate': ['AsOfDate'],
    'LocationID': ['LocationID', 'LocationIDLookup'],
    'BankName': ['BankName'],
    'GrossApproval': ['GrossApproval'],
    'SBAGuaranteedApproval': ['SBAGuaranteedApproval'],
    'ApprovalDate': ['ApprovalDate', 'FiscalYearDerived'],
    'ApprovalFY': ['ApprovalFY'],
    'ProcessingMethod': ['ProcessingMethod', 'ProcessingMethodLookup'],
    'TermInMonths': ['TermInMonths', 'TermBandCode'],
    'NaicsCode': ['NaicsCode', 'NaicsSectorCode', 'SectorMappingStatus', 'NaicsCodeLookup'],
    'NaicsDescription': ['NaicsDescription', 'NaicsDescriptionLookup'],
    'ProjectCounty': ['ProjectCounty', 'ProjectCountyLookup'],
    'ProjectState': ['ProjectState', 'ProjectStateLookup'],
    'BusinessType': ['BusinessTypeRaw', 'BusinessTypeValueStatus', 'BusinessTypeLookup'],
    'BusinessAge': ['BusinessAgeRaw', 'BusinessAgeValueStatus', 'BusinessAgeLookup'],
    'LoanStatus': ['RawStatus', 'CanonicalStatus', 'RawStatusLookup'],
    'GrossChargeOffAmount': ['GrossChargeOffAmount'],
    'JobsSupported': ['JobsSupported'],
}
# Declared reasons for columns that are not in the TSV. THIEU_TREN_50PCT and HANG_SO are
# added from the data in column_selection(); Program relies on HANG_SO alone.
DROP_REASONS = {
    **{c: ('PII',) for c in ['BorrName', 'BorrStreet', 'BorrCity', 'BorrState', 'BorrZip']},
    **{c: ('CHI_DUNG_DQ',) for c in ['FirstDisbursementDate', 'PaidInFullDate',
                                     'ChargeOffDate', 'InitialInterestRate']},
    **{c: ('NGOAI_PHAM_VI_Q1_Q15',) for c in [
        'BankFDICNumber', 'BankNCUANumber', 'BankStreet', 'BankCity', 'BankState', 'BankZip',
        'FixedorVariableInterestInd', 'FranchiseCode', 'FranchiseName', 'SBADistrictOffice',
        'CongressionalDistrict', 'RevolverStatus', 'CollateralInd', 'SoldSecMrktInd']},
}
REASON_CODES = {'PII', 'NGOAI_PHAM_VI_Q1_Q15', 'THIEU_TREN_50PCT', 'HANG_SO', 'CHI_DUNG_DQ',
                'CO_TRONG_KHO'}
# P1.16 analysis columns compared before/after trim.
ANALYSIS_COLUMNS = ['ProjectState', 'ProjectCounty', 'NaicsCode', 'NaicsDescription', 'LocationID',
                    'BankName', 'ProcessingMethod', 'LoanStatus', 'BusinessType', 'BusinessAge']

CONTROL_CHARS = re.compile(r'\r\n|[\r\n\t]')
DATE_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}')
CENT = Decimal('0.01')


# ---------------------------------------------------------------- value rules
def clean_text(values):
    """P1.3/P1.4 on a str Series: CR/LF/CRLF/tab -> one space, trim, '' -> None.

    Letter case is never changed.
    """
    values = values.str.replace(CONTROL_CHARS, ' ', regex=True).str.strip()
    return values.astype(object).where(values.ne(''), None)


def parse_decimal(value):
    """Return a finite Decimal, None for NULL, or raise ValueError."""
    if value is None:
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValueError(value) from None
    if not number.is_finite():
        raise ValueError(value)
    return number


def parse_date(value):
    """Return an ISO date string, None for NULL, or raise ValueError."""
    if value is None:
        return None
    if not DATE_PATTERN.fullmatch(value):
        raise ValueError(value)
    return datetime.strptime(value, '%Y-%m-%d').date().isoformat()


def fiscal_year(iso_date):
    """US federal FY: October-December belong to the next year."""
    if iso_date is None:
        return None
    year, month = int(iso_date[:4]), int(iso_date[5:7])
    return year + 1 if month >= 10 else year


def canonical_status(raw):
    """BR-STATUS-01: 'P I F' -> 'PIF'; known values unchanged; unknown -> UNMAPPED."""
    if raw is None:
        return 'MISSING'
    if raw not in KNOWN_STATUSES:
        return 'UNMAPPED'
    return STATUS_CANONICAL.get(raw, raw)


def term_band(raw):
    """BR-TERM-01 band code for a cleaned TermInMonths string."""
    if raw is None:
        return 'MISSING'
    try:
        months = parse_decimal(raw)
    except ValueError:
        return 'INVALID'
    if months < 0 or months != months.to_integral_value():
        return 'INVALID'
    months = int(months)
    if months == 0:
        return 'ZERO'
    if months <= 60:
        return 'SHORT'
    if months <= 119:
        return 'MEDIUM'
    if months == 120:
        return 'TERM_120'
    if months <= 240:
        return 'LONG'
    return 'VERY_LONG'


def naics_sector(code):
    """BR-NAICS-01 / D1=A: candidate sector from the 2-digit prefix (not verified)."""
    if code is None or not re.fullmatch(r'\d{6}', code):
        return None, 'UNMAPPED'
    prefix = code[:2]
    return SECTOR_RANGES.get(prefix, prefix), 'CANDIDATE_UNVERIFIED'


def value_status(value):
    """BR-BUSINESS-01: any non-NULL label (including 'Unanswered') is PRESENT."""
    return 'MISSING' if value is None else 'PRESENT'


def format_amount(value):
    """At least 2 decimals; never round away source precision (e.g. 3749992.425 stays)."""
    if value is None:
        return None
    return format(value if value.as_tuple().exponent < -2 else value.quantize(CENT), 'f')


def compare(left, right, op):
    """Element-wise op(left, right) as a bool Series; False when either side is NULL."""
    return pd.Series([a is not None and b is not None and op(a, b) for a, b in zip(left, right)],
                     index=left.index, dtype=bool)


def row_hash(values):
    """SHA-256 over the 42 raw (untouched) source values of one record."""
    return hashlib.sha256('\x1f'.join(values).encode('utf-8')).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------- pipeline steps
def check_source(source, expected_sha256):
    """P1.1: refuse Git LFS pointers, checksum mismatches and schema drift."""
    with source.open('rb') as handle:
        if handle.read(64).startswith(b'version https://git-lfs'):
            raise RuntimeError(f'{source.name} is a Git LFS pointer; run `git lfs pull` first.')
    digest = sha256_file(source)
    if expected_sha256 and digest != expected_sha256:
        raise RuntimeError(f'SHA-256 mismatch for {source.name}: {digest} != {expected_sha256}')
    with source.open(encoding='utf-8', newline='') as handle:
        header = next(csv.reader(handle))
    if header != SOURCE_COLUMNS:
        raise RuntimeError(f'Unexpected header in {source.name}: {header}')
    return digest, header


def read_raw(source):
    """Read every cell as text; '' stays '' (no NA inference) so leading zeros survive."""
    raw = pd.read_csv(source, dtype=str, keep_default_na=False, encoding='utf-8')
    if list(raw.columns) != SOURCE_COLUMNS:
        raise RuntimeError('Parsed columns differ from header.')
    return raw


class IssueLog:
    """Collects DQ issues (flag only, values are never corrected).

    Rows are sorted when written, so the order in which steps flag does not matter.
    """

    def __init__(self):
        self.rows = []

    def flag(self, ordinals, code, column=None, raw_values=None, detail=None):
        for i, ordinal in enumerate(ordinals):
            self.rows.append({'SourceRecordOrdinal': int(ordinal), 'IssueCode': code,
                              'ColumnName': column,
                              'RawValue': None if raw_values is None else raw_values[i],
                              'Detail': detail if not callable(detail) else detail(i)})

    def counts_by_record(self):
        return Counter(row['SourceRecordOrdinal'] for row in self.rows)


def record_ordinal(raw):
    """P1.2: record ordinal 1..N in parser order (records, not physical lines)."""
    return pd.Series(range(1, len(raw) + 1), index=raw.index)


def clean_columns(raw):
    """P1.3/P1.4: apply ``clean_text`` to all 42 source columns (case untouched)."""
    return pd.DataFrame({c: clean_text(raw[c]) for c in SOURCE_COLUMNS}, index=raw.index)


def multiline_records(raw):
    """P1.4: number of records with a CR/LF inside a cell."""
    return int(raw.apply(lambda s: s.str.contains('[\r\n]', regex=True)).any(axis=1).sum())


def trim_cardinality(raw, clean):
    """P1.3: distinct values per column before (raw) and after cleaning (NULL counted once)."""
    return {c: {'raw': int(raw[c].nunique()), 'standardized': int(clean[c].nunique(dropna=False))}
            for c in SOURCE_COLUMNS}


def parse_types(clean, ordinal, log):
    """P1.5: dates -> ISO strings, numeric columns -> Decimal; failures -> PARSE_ERROR + None.

    Codes (LocationID, NaicsCode, ZIP, FDIC/NCUA, district) are not parsed and stay text.
    """
    def typed(column, parser):
        values, bad = [], []
        for i, v in enumerate(clean[column]):
            try:
                values.append(parser(v))
            except ValueError:
                values.append(None)
                bad.append(i)
        if bad:
            log.flag(ordinal.iloc[bad], 'PARSE_ERROR', column, clean[column].iloc[bad].tolist())
        return pd.Series(values, index=clean.index, dtype=object)

    result = {c: typed(c, parse_date) for c in DATE_COLUMNS}
    result.update({c: typed(c, parse_decimal)
                   for c in AMOUNT_COLUMNS + INTEGER_COLUMNS + ['InitialInterestRate', 'ApprovalFY']})
    return result


def format_typed(clean, typed, ordinal, log):
    """P1.5: output strings for ApprovalFY, integer columns and amounts.

    Non-integral ApprovalFY -> PARSE_ERROR, non-integral term/jobs -> NON_INTEGER (both
    written as NULL); amounts keep source precision, > 2 decimals -> AMOUNT_SCALE_GT_2.
    """
    out = pd.DataFrame(index=clean.index)
    fy = typed['ApprovalFY']
    fy_bad = fy.map(lambda v: v is not None and v != v.to_integral_value()).astype(bool)
    log.flag(ordinal[fy_bad], 'PARSE_ERROR', 'ApprovalFY', clean['ApprovalFY'][fy_bad].tolist())
    out['ApprovalFY'] = [None if v is None or bad else str(int(v)) for v, bad in zip(fy, fy_bad)]

    for column in INTEGER_COLUMNS:
        values = typed[column]
        fractional = values.map(lambda v: v is not None and v != v.to_integral_value()).astype(bool)
        log.flag(ordinal[fractional], 'NON_INTEGER', column, clean[column][fractional].tolist())
        out[column] = [None if v is None or frac else str(int(v))
                       for v, frac in zip(values, fractional)]

    for column in AMOUNT_COLUMNS:
        values = typed[column]
        out[column] = values.map(format_amount)
        m = values.map(lambda v: v is not None and v.as_tuple().exponent < -2).astype(bool)
        log.flag(ordinal[m], 'AMOUNT_SCALE_GT_2', column, clean[column][m].tolist(),
                 'kept at source precision; DECIMAL(x,2) would round it')
    return out


def check_dates(clean, typed, formatted, ordinal, log):
    """P1.6: derive FiscalYearDerived and flag FY/date anomalies. Returns FiscalYearDerived."""
    fiscal = pd.Series([None if (y := fiscal_year(d)) is None else str(y)
                        for d in typed['ApprovalDate']], index=clean.index, dtype=object)
    m = compare(formatted['ApprovalFY'], fiscal, operator.ne)
    log.flag(ordinal[m], 'FY_MISMATCH', 'ApprovalFY', formatted['ApprovalFY'][m].tolist(),
             lambda i, d=fiscal[m].tolist(): f'FiscalYearDerived={d[i]}')

    co, asof, pif, appr = (typed['ChargeOffDate'], typed['AsOfDate'],
                           typed['PaidInFullDate'], typed['ApprovalDate'])
    m = compare(co, asof, operator.gt)                           # ISO strings sort as dates
    log.flag(ordinal[m], 'CHARGEOFF_AFTER_ASOF', 'ChargeOffDate', co[m].tolist(),
             lambda i, a=asof[m].tolist(): f'AsOfDate={a[i]}')
    m = compare(pif, appr, operator.lt)
    log.flag(ordinal[m], 'PIF_BEFORE_APPROVAL', 'PaidInFullDate', pif[m].tolist(),
             lambda i, a=appr[m].tolist(): f'ApprovalDate={a[i]}')
    m = clean['LoanStatus'].eq('CHGOFF') & clean['ChargeOffDate'].isna()
    log.flag(ordinal[m], 'CHGOFF_MISSING_DATE', 'ChargeOffDate', None)
    return fiscal


def check_numbers(clean, typed, ordinal, log):
    """P1.7: flag negative amounts, guarantee > gross, term = 0, rate = 0 (0 != NULL)."""
    for column in AMOUNT_COLUMNS:
        values = typed[column]
        m = values.map(lambda v: v is not None and v < 0).astype(bool)
        log.flag(ordinal[m], 'NEGATIVE_AMOUNT', column, clean[column][m].tolist())
    m = compare(typed['SBAGuaranteedApproval'], typed['GrossApproval'], operator.gt)
    log.flag(ordinal[m], 'GUARANTEE_GT_GROSS', 'SBAGuaranteedApproval',
             clean['SBAGuaranteedApproval'][m].tolist(),
             lambda i, a=clean['GrossApproval'][m].tolist(): f'GrossApproval={a[i]}')
    for code, column in [('TERM_ZERO', 'TermInMonths'), ('RATE_ZERO', 'InitialInterestRate')]:
        m = typed[column].map(lambda v: v is not None and v == 0).astype(bool)
        log.flag(ordinal[m], code, column, clean[column][m].tolist())


def flag_duplicates(raw, ordinal, log):
    """P1.8: RowHash on the 42 untouched raw values; flag groups, never delete.

    Returns a frame with RowHash, GroupSize, DuplicateGroupID (NULL if unique),
    IsExactDuplicate. Group ids are numbered by the group's first ordinal.
    """
    hashes = pd.Series([row_hash(r) for r in raw.itertuples(index=False, name=None)],
                       index=raw.index)
    group_size = hashes.map(hashes.value_counts())
    is_dup = group_size.gt(1)
    first_ordinal = ordinal[is_dup].groupby(hashes[is_dup]).min().sort_values()
    group_id = pd.Series(range(1, len(first_ordinal) + 1), index=first_ordinal.index)
    dup_group = hashes[is_dup].map(group_id)
    log.flag(ordinal[is_dup], 'EXACT_DUPLICATE', None, hashes[is_dup].tolist(),
             lambda i, g=dup_group.tolist(), s=group_size[is_dup].tolist():
             f'DuplicateGroupID={g[i]}; GroupSize={s[i]}')
    return pd.DataFrame({'RowHash': hashes, 'GroupSize': group_size,
                         'DuplicateGroupID': dup_group.reindex(raw.index).astype('Int64'),
                         'IsExactDuplicate': is_dup})


def map_status(clean):
    """P1.9 (BR-STATUS-01): RawStatus as published, CanonicalStatus for display."""
    raw_status = clean['LoanStatus']
    return pd.DataFrame({'RawStatus': raw_status,
                         'CanonicalStatus': raw_status.map(canonical_status)})


def map_term_band(clean):
    """P1.10 (BR-TERM-01): TermBandCode from the cleaned TermInMonths string."""
    return clean['TermInMonths'].map(term_band)


def map_naics(clean):
    """P1.11 (BR-NAICS-01, D1=A): candidate sector code + SectorMappingStatus."""
    sectors = [naics_sector(code) for code in clean['NaicsCode']]
    return pd.DataFrame({'NaicsSectorCode': [s[0] for s in sectors],
                         'SectorMappingStatus': [s[1] for s in sectors]}, index=clean.index)


def map_business(clean):
    """P1.12 (BR-BUSINESS-01): raw labels + PRESENT/MISSING value status."""
    return pd.DataFrame({'BusinessTypeRaw': clean['BusinessType'],
                         'BusinessAgeRaw': clean['BusinessAge'],
                         'BusinessTypeValueStatus': clean['BusinessType'].map(value_status),
                         'BusinessAgeValueStatus': clean['BusinessAge'].map(value_status)})


def add_lookup_columns(frame):
    """P1.13: ``*Lookup`` copies of Dim business keys with NULL -> ``(Missing)``."""
    collisions = {c: int(frame[c].eq(MISSING_TOKEN).sum()) for c in LOOKUP_COLUMNS}
    if any(collisions.values()):
        raise RuntimeError(f'Source already contains the token {MISSING_TOKEN!r}: {collisions}')
    for column, lookup in LOOKUP_COLUMNS.items():
        frame[lookup] = frame[column].fillna(MISSING_TOKEN)
    return frame


def assemble_standardized(source_file_id, ordinal, clean, typed, formatted, fiscal, dups, log):
    """P1.14: build the TSV frame (columns in OUTPUT_COLUMNS order). Call after all flags."""
    out = pd.DataFrame(index=clean.index)
    out['SourceFileID'] = source_file_id
    out['SourceRecordOrdinal'] = ordinal.astype(str)
    out['AsOfDate'] = typed['AsOfDate']
    out['ApprovalDate'] = typed['ApprovalDate']
    out['ApprovalFY'] = formatted['ApprovalFY']
    out['FiscalYearDerived'] = fiscal
    for column in ['ProjectState', 'ProjectCounty', 'NaicsCode', 'NaicsDescription',
                   'LocationID', 'BankName', 'ProcessingMethod']:
        out[column] = clean[column]
    out = out.join(map_naics(clean)).join(map_status(clean))
    for column in INTEGER_COLUMNS:
        out[column] = formatted[column]
    out['TermBandCode'] = map_term_band(clean)
    out = out.join(map_business(clean))
    for column in AMOUNT_COLUMNS:
        out[column] = formatted[column]
    out['IsExactDuplicate'] = dups['IsExactDuplicate'].astype(int).astype(str)
    counts = log.counts_by_record()
    out['DQFlagCount'] = ordinal.map(lambda o: str(counts.get(o, 0)))
    out = add_lookup_columns(out)[OUTPUT_COLUMNS]
    if len(out) != len(clean):
        raise AssertionError('Row count changed during standardization.')
    return out


def assemble_clean_copy(clean, typed, formatted):
    """P1.14: cleaned copy of the source (42 columns, typed values where a type applies)."""
    cleaned = clean.copy()
    for column in DATE_COLUMNS:
        cleaned[column] = typed[column]
    for column in AMOUNT_COLUMNS + INTEGER_COLUMNS + ['ApprovalFY']:
        cleaned[column] = formatted[column]
    if len(cleaned) != len(clean):
        raise AssertionError('Row count changed in the clean copy.')
    return cleaned


def standardize(raw, source_file_id):
    """Run P1.2-P1.13 in order. Returns (standardized, clean copy, IssueLog, audit dict)."""
    log = IssueLog()
    ordinal = record_ordinal(raw)
    clean = clean_columns(raw)
    typed = parse_types(clean, ordinal, log)
    formatted = format_typed(clean, typed, ordinal, log)
    fiscal = check_dates(clean, typed, formatted, ordinal, log)
    check_numbers(clean, typed, ordinal, log)
    dups = flag_duplicates(raw, ordinal, log)
    out = assemble_standardized(source_file_id, ordinal, clean, typed, formatted, fiscal, dups, log)
    cleaned = assemble_clean_copy(clean, typed, formatted)
    return out, cleaned, log, audit_summary(raw, clean, out, dups)


def audit_summary(raw, clean, standardized, dups):
    """Counts reported in manifest.json (multiline, duplicates, trim cardinality, R7)."""
    return {
        'multiline_records': multiline_records(raw),
        'exact_duplicate_rows': int(dups['IsExactDuplicate'].sum()),
        'exact_duplicate_groups': int(dups['DuplicateGroupID'].nunique()),
        'cardinality_before_after_trim': trim_cardinality(raw, clean),
        'case_variant_groups': case_variants(standardized),
    }


def case_variants(frame):
    """R7: groups of business-key values that differ only by letter case (report only)."""
    report = {}
    for key in CASE_KEYS:
        values = frame[list(key)].dropna(how='all').drop_duplicates()
        folded = values.apply(lambda s: s.str.casefold())
        sizes = values.groupby([folded[c].fillna('\x00') for c in key]).size()
        groups = sizes[sizes > 1]
        examples = []
        for folded_key in groups.index[:5]:
            folded_key = folded_key if isinstance(folded_key, tuple) else (folded_key,)
            mask = pd.Series(True, index=folded.index)
            for c, v in zip(key, folded_key):
                mask &= folded[c].fillna('\x00').eq(v)
            examples.append(sorted(' | '.join(str(x) for x in row)
                                   for row in values[mask].itertuples(index=False, name=None)))
        report['+'.join(key)] = {'groups': int(len(groups)),
                                 'distinct_values_involved': int(groups.sum()),
                                 'examples': examples}
    return report


def write_tsv(frame, path):
    """Deterministic UTF-8 TSV: CRLF rows, NULL -> empty field, no quoting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(frame.columns)
    bad = [c for c in columns if frame[c].dropna().str.contains('[\t\r\n]', regex=True).any()]
    if bad:
        raise RuntimeError(f'Control characters left in TSV columns: {bad}')
    with path.open('w', encoding='utf-8', newline='') as handle:
        handle.write('\t'.join(columns) + '\r\n')
        for row in frame.itertuples(index=False, name=None):
            handle.write('\t'.join(v if isinstance(v, str) else '' for v in row) + '\r\n')


def read_tsv(path):
    return pd.read_csv(path, sep='\t', dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE,
                       encoding='utf-8')


def decimal_sum(values):
    return sum((Decimal(v) for v in values if v != ''), Decimal(0))


def read_clean_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8')


def write_clean_csv(frame, path):
    """Deterministic UTF-8 CSV: CRLF rows, minimal quoting, NULL -> empty field."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding='utf-8', lineterminator='\r\n', na_rep='')


def reconcile(raw, outputs):
    """P1.14: compare the raw CSV with each output as re-read from disk.

    ``outputs`` is a list of (output name, frame, status column).
    """
    raw_fy = raw['ApprovalFY'].str.strip().value_counts()
    raw_st = raw['LoanStatus'].str.strip().value_counts()
    rows = []
    for name, frame, status in outputs:
        rows.append((name, 'row_count', '', len(raw), len(frame)))
        for column in MEASURES:
            rows.append((name, f'sum_{column}', '', decimal_sum(raw[column]),
                         decimal_sum(frame[column])))
        for metric, raw_counts, out_counts in [
                ('count_by_ApprovalFY', raw_fy, frame['ApprovalFY'].value_counts()),
                ('count_by_LoanStatus', raw_st, frame[status].value_counts())]:
            for key in sorted(set(raw_counts.index) | set(out_counts.index)):
                rows.append((name, metric, key, int(raw_counts.get(key, 0)),
                             int(out_counts.get(key, 0))))
        if 'TermBandCode' in frame:
            rows.append((name, 'sum_TermBand_counts', '', len(raw),
                         int(frame['TermBandCode'].value_counts().sum())))
    result = pd.DataFrame(rows, columns=['Output', 'Metric', 'Key', 'RawValue', 'OutputValue'])
    result['Match'] = [a == b for a, b in zip(result.RawValue, result.OutputValue)]
    return result


def issues_frame(log, source_file_id):
    """dq_issues rows sorted by (ordinal, IssueCode, ColumnName) — independent of step order."""
    columns = ['SourceFileID', 'SourceRecordOrdinal', 'IssueCode', 'ColumnName', 'RawValue', 'Detail']
    frame = pd.DataFrame(log.rows, columns=columns[1:])
    frame.insert(0, 'SourceFileID', source_file_id)
    frame = frame.sort_values(['SourceRecordOrdinal', 'IssueCode', 'ColumnName'],
                              kind='mergesort', na_position='first')
    return frame.reset_index(drop=True)


def write_report(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding='utf-8', lineterminator='\n')


def column_selection(raw, tsv):
    """P1.15: one row per source column with KEEP/DROP derived from the actual TSV columns.

    Missing/distinct counts come from the raw values after ``clean_text`` (blank after
    trim = missing; distinct excludes missing). KEEP lists the TSV columns the source
    column feeds; DROP gets the declared reasons plus data-driven ones
    (``THIEU_TREN_50PCT`` when > 50 % missing, ``HANG_SO`` when <= 1 distinct value).
    Dropping a column never drops a record.
    """
    present = set(tsv.columns)
    n = len(raw)
    rows = []
    for column in SOURCE_COLUMNS:
        values = clean_text(raw[column])
        missing = int(values.isna().sum())
        distinct = int(values.nunique())
        targets = [t for t in SOURCE_TO_TARGET.get(column, []) if t in present]
        if targets:
            decision, reasons = 'KEEP', ['CO_TRONG_KHO']
        else:
            decision = 'DROP'
            reasons = (['THIEU_TREN_50PCT'] if missing * 2 > n else []) \
                + (['HANG_SO'] if distinct <= 1 else []) + list(DROP_REASONS.get(column, ()))
        rows.append({'SourceColumn': column, 'MissingCount': missing,
                     'MissingPct': round(100 * missing / n, 2), 'DistinctCount': distinct,
                     'Decision': decision, 'TargetColumns': '|'.join(targets),
                     'Reason': '|'.join(reasons)})
    return pd.DataFrame(rows)


def before_after(raw, tsv):
    """P1.16: raw vs standardized TSV (as re-read from disk, NULL = '').

    Rows: row/column counts; blank cells of every kept column (raw '' vs TSV empty);
    distinct non-blank values of the analysis columns before/after trim; measure sums.
    """
    rows = [('row_count', '', len(raw), len(tsv)),
            ('column_count', '', raw.shape[1], tsv.shape[1])]

    def label(source, target):
        return source if source == target else f'{source} -> {target}'

    for source, targets in SOURCE_TO_TARGET.items():
        if targets[0] in tsv.columns:
            rows.append(('blank_cells', label(source, targets[0]),
                         int(raw[source].eq('').sum()), int(tsv[targets[0]].eq('').sum())))
    for source in ANALYSIS_COLUMNS:
        target = SOURCE_TO_TARGET[source][0]
        before, after = raw[source], tsv[target]
        rows.append(('distinct_values', label(source, target),
                     int(before[before.ne('')].nunique()), int(after[after.ne('')].nunique())))
    for column in MEASURES:
        rows.append(('sum', column, decimal_sum(raw[column]), decimal_sum(tsv[column])))
    return pd.DataFrame(rows, columns=['Metric', 'Column', 'Before', 'After'])


def export_outputs(raw, standardized, cleaned, log, audit, *, source, digest, header,
                   expected_sha256=EXPECTED_SHA256, staging_dir=STAGING_DIR,
                   report_dir=REPORT_DIR, started=None):
    """P1.14-P1.16: write TSV, clean CSV and all reports; return the manifest dict."""
    started = time.time() if started is None else started
    source, staging_dir, report_dir = Path(source), Path(staging_dir), Path(report_dir)
    source_file_id = source.stem

    tsv_path = staging_dir / TSV_NAME
    write_tsv(standardized, tsv_path)
    clean_path = staging_dir / f'{source_file_id}_clean.csv'
    write_clean_csv(cleaned, clean_path)
    issue_frame = issues_frame(log, source_file_id)
    write_report(issue_frame, report_dir / 'dq_issues.csv')
    tsv = read_tsv(tsv_path)
    recon = reconcile(raw, [('standardized_tsv', tsv, 'RawStatus'),
                            ('clean_csv', read_clean_csv(clean_path), 'LoanStatus')])
    write_report(recon, report_dir / 'reconciliation.csv')
    selection = column_selection(raw, tsv)
    write_report(selection, report_dir / 'column_selection.csv')
    write_report(before_after(raw, tsv), report_dir / 'before_after.csv')

    def display_path(path):
        return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)

    manifest = {
        'rule_version': RULE_VERSION,
        'run': {'started_at_utc': datetime.fromtimestamp(started, timezone.utc)
                                          .isoformat(timespec='seconds'),
                'finished_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'duration_seconds': round(time.time() - started, 1),
                'python': platform.python_version(), 'pandas': pd.__version__},
        'source': {'file': source.name, 'source_file_id': source_file_id, 'sha256': digest,
                   'expected_sha256': expected_sha256, 'bytes': source.stat().st_size,
                   'records': len(raw), 'columns': len(header), 'header': header,
                   'multiline_records': audit['multiline_records']},
        'outputs': {
            'clean_csv': {'path': display_path(clean_path), 'sha256': sha256_file(clean_path),
                          'rows': len(cleaned), 'columns': list(cleaned.columns),
                          'format': 'UTF-8, comma-delimited, RFC 4180 quoting, CRLF, header'},
            'standardized_tsv': {'path': display_path(tsv_path),
                                 'sha256': sha256_file(tsv_path), 'rows': len(standardized),
                                 'columns': list(standardized.columns),
                                 'format': 'UTF-8, tab-delimited, CRLF, header, NULL = empty'},
            'dq_issues_rows': len(issue_frame),
            'reconciliation_all_match': bool(recon['Match'].all()),
            'dropped_source_columns': selection.loc[selection['Decision'] == 'DROP',
                                                    'SourceColumn'].tolist(),
        },
        'counts': {
            'dq_issue_rows_by_code': issue_frame['IssueCode'].value_counts().sort_index().to_dict(),
            'dq_issue_records_by_code': issue_frame.groupby('IssueCode')['SourceRecordOrdinal']
                                        .nunique().to_dict(),
            'exact_duplicate_rows': audit['exact_duplicate_rows'],
            'exact_duplicate_groups': audit['exact_duplicate_groups'],
            'sector_mapping_status': standardized['SectorMappingStatus'].value_counts().to_dict(),
            'term_band': standardized['TermBandCode'].value_counts().sort_index().to_dict(),
            'canonical_status': standardized['CanonicalStatus'].value_counts().sort_index().to_dict(),
            'business_type_x_age_combinations': int(
                standardized[['BusinessTypeRaw', 'BusinessAgeRaw']].drop_duplicates().shape[0]),
            'lookup_missing_tokens': {lk: int(standardized[lk].eq(MISSING_TOKEN).sum())
                                      for lk in LOOKUP_COLUMNS.values()},
        },
        'cardinality_before_after_trim': audit['cardinality_before_after_trim'],
        'case_variant_groups': audit['case_variant_groups'],
    }
    (report_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                              encoding='utf-8')
    if not recon['Match'].all():
        raise RuntimeError('Reconciliation mismatch:\n'
                           + recon[~recon['Match']].to_string(index=False))
    return manifest


def run(source=SOURCE, staging_dir=STAGING_DIR, report_dir=REPORT_DIR,
        expected_sha256=EXPECTED_SHA256):
    """P1.1-P1.16 end to end."""
    started = time.time()
    source = Path(source)
    digest, header = check_source(source, expected_sha256)
    raw = read_raw(source)
    standardized, cleaned, log, audit = standardize(raw, source.stem)
    return export_outputs(raw, standardized, cleaned, log, audit, source=source, digest=digest,
                          header=header, expected_sha256=expected_sha256,
                          staging_dir=staging_dir, report_dir=report_dir, started=started)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--staging-dir', type=Path, default=STAGING_DIR)
    parser.add_argument('--report-dir', type=Path, default=REPORT_DIR)
    args = parser.parse_args(argv)
    manifest = run(args.source, args.staging_dir, args.report_dir)
    for name in ('clean_csv', 'standardized_tsv'):
        output = manifest['outputs'][name]
        print(f"{output['rows']} rows -> {output['path']} (sha256 {output['sha256']})")
    print(json.dumps(manifest['counts'], indent=2))


if __name__ == '__main__':
    sys.exit(main())
