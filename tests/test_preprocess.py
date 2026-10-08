"""Tests for Phase 1 preprocessing. Run: python -m pytest tests/test_preprocess.py"""
import hashlib
from decimal import Decimal

import pandas as pd
import pytest

from src.etl import preprocess as pp

N_RECORDS = 388_338
# TSV checksum recorded before P1.15-P1.17 were added; refactoring must not change it.
TSV_SHA256_BASELINE = '837723fb7b6b8358ce4aaf4855ea396b197104660babbe6d6d9f6a6be3a78bc5'
AUDIT_COLUMNS = {'SourceFileID', 'SourceRecordOrdinal', 'IsExactDuplicate', 'DQFlagCount'}
FY_COUNTS = {'2020': 42_298, '2021': 51_856, '2022': 47_678, '2023': 57_362,
             '2024': 70_242, '2025': 78_078, '2026': 40_824}


# ---------------------------------------------------------------- unit rules
def test_clean_text_trims_replaces_controls_and_keeps_case():
    values = pd.Series([' 7A', 'a\r\nb', 'x\ty\nz', '   ', '', 'MixedCase '])
    assert pp.clean_text(values).tolist() == ['7A', 'a b', 'x y z', None, None, 'MixedCase']


@pytest.mark.parametrize('raw, band', [
    (None, 'MISSING'), ('abc', 'INVALID'), ('-1', 'INVALID'), ('12.5', 'INVALID'),
    ('0', 'ZERO'), ('0.0', 'ZERO'), ('1', 'SHORT'), ('60.0', 'SHORT'), ('61', 'MEDIUM'),
    ('119', 'MEDIUM'), ('120.0', 'TERM_120'), ('121', 'LONG'), ('240', 'LONG'),
    ('241', 'VERY_LONG'), ('300.0', 'VERY_LONG'),
])
def test_term_band(raw, band):
    assert pp.term_band(raw) == band


@pytest.mark.parametrize('code, expected', [
    ('311811', ('31-33', 'CANDIDATE_UNVERIFIED')), ('332710', ('31-33', 'CANDIDATE_UNVERIFIED')),
    ('445110', ('44-45', 'CANDIDATE_UNVERIFIED')), ('492110', ('48-49', 'CANDIDATE_UNVERIFIED')),
    ('722511', ('72', 'CANDIDATE_UNVERIFIED')), ('11111', (None, 'UNMAPPED')),
    ('12345A', (None, 'UNMAPPED')), (None, (None, 'UNMAPPED')),
])
def test_naics_sector(code, expected):
    assert pp.naics_sector(code) == expected


def test_status_business_and_fiscal_year_rules():
    assert pp.canonical_status('P I F') == 'PIF'
    assert pp.canonical_status('CHGOFF') == 'CHGOFF'
    assert pp.canonical_status('PAID') == 'UNMAPPED'
    assert pp.value_status('Unanswered') == 'PRESENT'
    assert pp.value_status(None) == 'MISSING'
    assert pp.fiscal_year('2019-10-01') == 2020
    assert pp.fiscal_year('2020-09-30') == 2020


# ---------------------------------------------------------------- full-file runs
def _source_available():
    if not pp.SOURCE.exists():
        return False
    with pp.SOURCE.open('rb') as handle:
        return not handle.read(64).startswith(b'version https://git-lfs')


needs_source = pytest.mark.skipif(not _source_available(),
                                  reason='raw CSV missing or Git LFS pointer (run `git lfs pull`)')


@pytest.fixture(scope='module')
def runs(tmp_path_factory):
    """Run the pipeline twice into separate temp dirs (for the determinism check)."""
    results = []
    for name in ('run1', 'run2'):
        base = tmp_path_factory.mktemp(name)
        manifest = pp.run(staging_dir=base / 'staging', report_dir=base / 'reports')
        results.append((base, manifest))
    return results


@pytest.fixture(scope='module')
def out(runs):
    return pp.read_tsv(runs[0][0] / 'staging' / pp.TSV_NAME)


@pytest.fixture(scope='module')
def clean(runs):
    return pp.read_clean_csv(runs[0][0] / 'staging' / f'{pp.SOURCE.stem}_clean.csv')


@pytest.fixture(scope='module')
def raw():
    return pp.read_raw(pp.SOURCE)


@pytest.fixture(scope='module')
def issues(runs):
    return pd.read_csv(runs[0][0] / 'reports' / 'dq_issues.csv', dtype=str, keep_default_na=False)


@needs_source
def test_no_record_dropped_and_ordinal_contiguous(out):
    assert len(out) == N_RECORDS
    ordinal = out['SourceRecordOrdinal'].astype(int)
    assert ordinal.is_unique
    assert ordinal.tolist() == list(range(1, N_RECORDS + 1))


@needs_source
def test_output_columns_exclude_pii_and_bank_address(out):
    assert list(out.columns) == pp.OUTPUT_COLUMNS
    banned = [c for c in out.columns if c.startswith('Borr') or c.startswith('Franchise')
              or c in {'BankStreet', 'BankCity', 'BankState', 'BankZip'}]
    assert banned == []


@needs_source
@pytest.mark.parametrize('column', pp.MEASURES)
def test_measure_sums_match_raw(raw, out, column):
    assert pp.decimal_sum(raw[column]) == pp.decimal_sum(out[column])
    assert out[column].ne('').all()


@needs_source
def test_counts_by_approval_fy(out):
    assert out['ApprovalFY'].value_counts().to_dict() == FY_COUNTS


@needs_source
def test_pif_status_mapping(out):
    pif = out[out['RawStatus'] == 'P I F']
    assert len(pif) == 68_201
    assert pif['CanonicalStatus'].eq('PIF').all()
    assert not out['CanonicalStatus'].eq('UNMAPPED').any()


@needs_source
def test_term_bands(out):
    bands = out['TermBandCode'].value_counts()
    assert bands['TERM_120'] == 236_672
    assert bands['ZERO'] == 11
    assert bands.sum() == N_RECORDS
    assert set(bands.index) <= {'ZERO', 'SHORT', 'MEDIUM', 'TERM_120', 'LONG', 'VERY_LONG',
                                'MISSING', 'INVALID'}


@needs_source
def test_exact_duplicates_flagged_not_removed(out, issues):
    assert out['IsExactDuplicate'].eq('1').sum() == 687
    dup = issues[issues['IssueCode'] == 'EXACT_DUPLICATE']
    assert len(dup) == 687
    groups = dup['Detail'].str.extract(r'DuplicateGroupID=(\d+)')[0]
    assert groups.nunique() == 296


@needs_source
def test_location_id_keeps_leading_zero(out):
    assert out['LocationID'].str.startswith('0').any()
    assert out['NaicsCode'].str.fullmatch(r'\d{6}|').all()


@needs_source
def test_business_type_age_combinations(out):
    pairs = out[['BusinessTypeRaw', 'BusinessAgeRaw']].drop_duplicates()
    assert len(pairs) == 22
    assert set(out['BusinessTypeValueStatus']) <= {'PRESENT', 'MISSING'}
    assert out.loc[out['BusinessAgeRaw'] == 'Unanswered', 'BusinessAgeValueStatus'].eq('PRESENT').all()


@needs_source
def test_lookup_columns_replace_null_only(out):
    for column, lookup in pp.LOOKUP_COLUMNS.items():
        missing = out[column].eq('')
        assert out[lookup].ne('').all(), lookup
        assert (out.loc[missing, lookup] == pp.MISSING_TOKEN).all(), lookup
        assert (out.loc[~missing, lookup] == out.loc[~missing, column]).all(), lookup


@needs_source
def test_dq_flag_count_matches_issue_file(out, issues):
    per_record = issues['SourceRecordOrdinal'].value_counts()
    counts = out.set_index('SourceRecordOrdinal')['DQFlagCount'].astype(int)
    assert counts.sum() == len(issues)
    assert (counts[per_record.index] == per_record).all()


@needs_source
def test_reconciliation_all_match(runs):
    recon = pd.read_csv(runs[0][0] / 'reports' / 'reconciliation.csv')
    assert recon['Match'].all()
    assert runs[0][1]['outputs']['reconciliation_all_match']


@needs_source
def test_two_runs_same_tsv_checksum(runs):
    digests = [hashlib.sha256((base / 'staging' / pp.TSV_NAME).read_bytes()).hexdigest()
               for base, _ in runs]
    assert digests[0] == digests[1]
    assert digests[0] == runs[0][1]['outputs']['standardized_tsv']['sha256']


@needs_source
def test_clean_csv_same_shape_and_order_as_source(clean, out):
    assert len(clean) == N_RECORDS
    assert list(clean.columns) == pp.SOURCE_COLUMNS
    # Row i of the clean file is SourceRecordOrdinal i of the standardized TSV.
    assert (clean['LocationID'] == out['LocationID']).all()
    assert (clean['ApprovalDate'] == out['ApprovalDate']).all()


@needs_source
@pytest.mark.parametrize('column', pp.MEASURES)
def test_clean_csv_measure_sums_match_raw(raw, clean, column):
    assert pp.decimal_sum(raw[column]) == pp.decimal_sum(clean[column])


@needs_source
def test_clean_csv_values_cleaned(clean):
    for column in clean.columns:
        values = clean[column]
        assert not values.str.contains('[\r\n\t]', regex=True).any(), column
        assert (values == values.str.strip()).all(), column
    assert clean['Program'].eq('7A').all()
    assert clean['LoanStatus'].eq('P I F').sum() == 68_201
    assert clean['LocationID'].str.startswith('0').any()
    assert clean['TermInMonths'].str.fullmatch(r'\d+').all()


@needs_source
def test_two_runs_same_clean_csv_checksum(runs):
    name = f'{pp.SOURCE.stem}_clean.csv'
    digests = [hashlib.sha256((base / 'staging' / name).read_bytes()).hexdigest()
               for base, _ in runs]
    assert digests[0] == digests[1] == runs[0][1]['outputs']['clean_csv']['sha256']


@needs_source
def test_tsv_checksum_unchanged_from_baseline(runs):
    assert runs[0][1]['outputs']['standardized_tsv']['sha256'] == TSV_SHA256_BASELINE


@pytest.fixture(scope='module')
def selection(runs):
    return pd.read_csv(runs[0][0] / 'reports' / 'column_selection.csv', dtype=str,
                       keep_default_na=False)


@needs_source
def test_column_selection_covers_42_source_columns(selection):
    assert len(selection) == 42
    assert selection['SourceColumn'].tolist() == pp.SOURCE_COLUMNS
    assert set(selection['Decision']) == {'KEEP', 'DROP'}


@needs_source
def test_column_selection_reasons(selection):
    drop = selection[selection['Decision'] == 'DROP']
    assert drop['Reason'].ne('').all()
    for reasons in selection['Reason']:
        assert set(reasons.split('|')) <= pp.REASON_CODES
    reason = selection.set_index('SourceColumn')['Reason']
    for column in ['BorrName', 'BorrStreet', 'BorrCity', 'BorrState', 'BorrZip']:
        assert 'PII' in reason[column].split('|')
    assert 'HANG_SO' in reason['Program'].split('|')
    assert reason['BankNCUANumber'] == 'THIEU_TREN_50PCT|NGOAI_PHAM_VI_Q1_Q15'


@needs_source
def test_column_selection_keep_targets_exist_in_tsv(selection, out):
    keep = selection[selection['Decision'] == 'KEEP']
    targets = set()
    for value in keep['TargetColumns']:
        assert value != ''
        targets |= set(value.split('|'))
    assert targets <= set(out.columns)
    # Every non-audit TSV column traces back to a kept source column.
    assert set(out.columns) - AUDIT_COLUMNS == targets
    assert selection.loc[selection['Decision'] == 'DROP', 'TargetColumns'].eq('').all()


@needs_source
def test_before_after_rows_and_sums_unchanged(runs):
    frame = pd.read_csv(runs[0][0] / 'reports' / 'before_after.csv', dtype=str,
                        keep_default_na=False)
    rows = frame[frame['Metric'] == 'row_count'].iloc[0]
    assert int(rows['Before']) == int(rows['After']) == N_RECORDS
    sums = frame[frame['Metric'] == 'sum'].set_index('Column')
    assert set(sums.index) == set(pp.MEASURES)
    for column in pp.MEASURES:
        assert Decimal(sums.loc[column, 'Before']) == Decimal(sums.loc[column, 'After'])


@needs_source
def test_source_checksum_recorded(runs):
    assert runs[0][1]['source']['sha256'] == pp.EXPECTED_SHA256
    assert runs[0][1]['source']['records'] == N_RECORDS
    assert runs[0][1]['source']['columns'] == 42
