"""Reproducible single-snapshot preparation. Run: python -m src.main."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ['GrossApproval', 'SBAGuaranteedApproval', 'GrossChargeOffAmount',
           'JobsSupported', 'InitialInterestRate', 'TermInMonths']
DATES = ['AsOfDate', 'ApprovalDate', 'FirstDisbursementDate', 'PaidInFullDate', 'ChargeOffDate']


def sector(code):
    prefix = code[:2]
    return {'31': '31-33', '32': '31-33', '33': '31-33', '44': '44-45',
            '45': '44-45', '48': '48-49', '49': '48-49'}.get(prefix, prefix or 'Unknown')


def dimension(frame, columns, key):
    """Attribute-tuple keys are scoped to this rebuild, never durable loan IDs."""
    values = frame[columns].fillna('Unknown').replace('', 'Unknown')
    dim = values.drop_duplicates().sort_values(columns).reset_index(drop=True)
    dim.insert(0, key, range(1, len(dim) + 1))
    mapped = values.merge(dim, on=columns, how='left', validate='many_to_one', sort=False)
    assert len(mapped) == len(frame) and mapped[key].notna().all()
    return dim, mapped[key].to_numpy()


def prepare(source, output):
    output.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    d = pd.read_csv(source, dtype=str, keep_default_na=False).apply(lambda s: s.str.strip())
    required = set(NUMERIC + DATES + ['LocationID', 'LoanStatus', 'ApprovalFY'])
    if not required.issubset(d.columns):
        raise ValueError(f'Missing fields: {required - set(d.columns)}')
    raw = d.copy()
    profile = {'source': source.name, 'sha256': digest, 'rows': len(d), 'columns': len(d.columns),
               'normalized_duplicate_rows': int(d.duplicated().sum()),
               'missing': d.eq('').sum().to_dict(), 'location_ids': d.LocationID.nunique(),
               'approval_fy': d.ApprovalFY.value_counts().sort_index().to_dict()}
    issues = []
    def flag(mask, rule):
        for index in d.index[mask]:
            issues.append({'SourceRowNumber': int(index + 2), 'Rule': rule})
    flag(d.duplicated(keep=False), 'identical_attributes_not_proven_duplicate_loan')
    for c in NUMERIC:
        value = pd.to_numeric(d[c], errors='coerce')
        flag(d[c].ne('') & value.isna(), f'invalid_numeric_{c}')
        flag(value.lt(0), f'negative_{c}')
        d[c] = value
    for c in DATES:
        value = pd.to_datetime(d[c], format='%Y-%m-%d', errors='coerce')
        flag(d[c].ne('') & value.isna(), f'invalid_date_{c}')
        d[c] = value
    # Required measures/dates must not silently disappear from aggregates.
    mandatory = ['GrossApproval', 'SBAGuaranteedApproval', 'GrossChargeOffAmount',
                 'JobsSupported', 'TermInMonths', 'ApprovalDate', 'AsOfDate']
    if d[mandatory].isna().any().any():
        raise ValueError('Invalid/missing required numeric or date field; inspect source before loading.')
    if d.AsOfDate.nunique() != 1:
        raise ValueError('Only a single AsOfDate snapshot is supported.')
    d['LoanStatus'] = d.LoanStatus.str.replace(' ', '', regex=False)
    flag(~d.LoanStatus.isin(['PIF', 'CHGOFF', 'EXEMPT', 'CANCLD', 'COMMIT']), 'unknown_status')
    flag(d.SBAGuaranteedApproval.gt(d.GrossApproval), 'guarantee_above_approval')
    flag(d.TermInMonths.eq(0), 'zero_term_review')
    flag(d.InitialInterestRate.eq(0), 'zero_interest_review')
    flag(d.ApprovalDate.gt(d.AsOfDate), 'approval_after_snapshot')
    flag(pd.to_numeric(d.ApprovalFY, errors='coerce').ne(d.ApprovalDate.dt.year + d.ApprovalDate.dt.month.ge(10)), 'fiscal_year_mismatch')
    for c in DATES[2:]:
        flag(d[c].lt(d.ApprovalDate) | d[c].gt(d.AsOfDate), f'event_date_out_of_range_{c}')
    flag(d.LoanStatus.eq('CHGOFF') & d.ChargeOffDate.isna(), 'chargeoff_missing_date')
    flag(d.LoanStatus.eq('PIF') & d.PaidInFullDate.isna(), 'pif_missing_date')
    profile['status'] = d.LoanStatus.value_counts().to_dict()
    profile['approval_date_range'] = [str(d.ApprovalDate.min().date()), str(d.ApprovalDate.max().date())]
    profile['as_of_date'] = str(d.AsOfDate.iloc[0].date())
    profile['numeric'] = {c: {'sum': float(d[c].sum()), 'min': float(d[c].min()),
                              'max': float(d[c].max()), 'missing': int(d[c].isna().sum())} for c in NUMERIC}
    tables = {}
    fact = pd.DataFrame({'LoanRowKey': range(1, len(d) + 1), 'SourceRowNumber': range(2, len(d) + 2)})
    # Normalize state/county and industry/sector into real snowflake branches.
    d['StateCode'] = d.ProjectState
    tables['DimState'], d['StateKey'] = dimension(d, ['StateCode'], 'StateKey')
    tables['DimCounty'], fact['CountyKey'] = dimension(d, ['StateKey', 'ProjectCounty'], 'CountyKey')
    d['SectorCode'] = d.NaicsCode.map(sector)
    tables['DimSector'], d['SectorKey'] = dimension(d, ['SectorCode'], 'SectorKey')
    tables['DimIndustry'], fact['IndustryKey'] = dimension(d, ['SectorKey', 'NaicsCode', 'NaicsDescription'], 'IndustryKey')
    for name, cols, key in [
        ('DimLender', ['LocationID', 'BankName', 'BankFDICNumber', 'BankNCUANumber', 'BankCity', 'BankState', 'BankZip'], 'LenderKey'),
        ('DimBusiness', ['BusinessType', 'BusinessAge', 'FranchiseCode', 'FranchiseName'], 'BusinessKey'),
        ('DimLoanProfile', ['Program', 'ProcessingMethod', 'FixedorVariableInterestInd', 'RevolverStatus', 'CollateralInd', 'SoldSecMrktInd', 'LoanStatus'], 'LoanProfileKey')]:
        tables[name], fact[key] = dimension(d, cols, key)
    all_dates = pd.concat([d[c] for c in DATES]).dropna()
    calendar = pd.Series(pd.date_range(all_dates.min(), all_dates.max()))
    tables['DimDate'] = pd.DataFrame({'DateKey': calendar.dt.strftime('%Y%m%d').astype(int),
        'FullDate': calendar.dt.strftime('%Y-%m-%d'), 'CalendarYear': calendar.dt.year,
        'CalendarQuarter': calendar.dt.quarter, 'MonthNumber': calendar.dt.month,
        'YearMonth': calendar.dt.strftime('%Y-%m'),
        'FiscalYear': calendar.dt.year + calendar.dt.month.ge(10).astype(int),
        'FiscalQuarter': ((calendar.dt.month - 10) % 12 // 3 + 1)})
    fact_dates = ['ApprovalDate', 'FirstDisbursementDate', 'PaidInFullDate', 'ChargeOffDate']
    for c in fact_dates:
        fact[c + 'Key'] = d[c].dt.strftime('%Y%m%d').astype('Int64')
    for c in NUMERIC:
        fact[c] = d[c]
    fact['LoanCount'] = 1
    fact['ChargeOffCount'] = d.LoanStatus.eq('CHGOFF').astype(int)
    fact['ResolvedCount'] = d.LoanStatus.isin(['CHGOFF', 'PIF']).astype(int)
    fact['NonCancelledCount'] = (~d.LoanStatus.eq('CANCLD')).astype(int)
    fact['NonCancelledApproval'] = d.GrossApproval.where(d.LoanStatus.ne('CANCLD'), 0)
    fact['UnguaranteedApproval'] = d.GrossApproval - d.SBAGuaranteedApproval
    fact['InterestWeightedAmount'] = (d.InitialInterestRate / 100 * d.GrossApproval).fillna(0)
    fact['InterestKnownApproval'] = d.GrossApproval.where(d.InitialInterestRate.notna(), 0)
    fact['TermTotal'] = d.TermInMonths
    elapsed = (d.FirstDisbursementDate - d.ApprovalDate).dt.days
    valid_elapsed = elapsed.ge(0) & d.FirstDisbursementDate.le(d.AsOfDate)
    fact['DisbursementDaysTotal'] = elapsed.where(valid_elapsed, 0).astype(int)
    fact['DisbursementObservedCount'] = valid_elapsed.astype(int)
    tables['FactLoanSnapshot'] = fact
    # Missing date keys remain NULL; SQL/SSAS handle the unknown member explicitly.
    for name, frame in tables.items():
        frame.to_csv(output / f'{name}.csv', index=False, encoding='utf-8')
    errors = pd.DataFrame(issues, columns=['SourceRowNumber', 'Rule'])
    errors.to_csv(output / 'quality_issues.csv', index=False)
    profile['quality_issues'] = errors.Rule.value_counts().to_dict()
    profile['table_rows'] = {name: len(frame) for name, frame in tables.items()}
    profile['policy'] = 'Preserve all source rows, including identical attributes; no published loan ID.'
    (output / 'profile.json').write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding='utf-8')
    # Compact marts: only additive components. Compute ratios after aggregation in BI.
    mart = fact.join(d[['ApprovalFY', 'StateCode', 'SectorCode', 'LoanStatus']])
    measures = ['LoanCount', 'GrossApproval', 'SBAGuaranteedApproval', 'GrossChargeOffAmount', 'JobsSupported',
                'ChargeOffCount', 'ResolvedCount', 'NonCancelledApproval', 'NonCancelledCount',
                'InterestWeightedAmount', 'InterestKnownApproval', 'DisbursementDaysTotal', 'DisbursementObservedCount']
    mart.groupby(['ApprovalFY', 'StateCode', 'SectorCode', 'LoanStatus'], dropna=False)[measures].sum().reset_index().to_csv(output / 'mart_portfolio.csv', index=False)
    # Raw text retained only in source; downstream ML is an explicit feature allowlist.
    cohort = d.LoanStatus.isin(['PIF', 'CHGOFF'])
    ml = d.loc[cohort, ['ApprovalDate', 'GrossApproval', 'SBAGuaranteedApproval', 'InitialInterestRate',
                        'TermInMonths', 'ProcessingMethod', 'FixedorVariableInterestInd', 'SectorCode',
                        'StateCode', 'BusinessType', 'BusinessAge']].copy()
    ml['ClassChargeOff'] = d.loc[cohort, 'LoanStatus'].eq('CHGOFF').astype(int)
    # A stable grouping hash prevents repeated borrower names/addresses across train/test.
    identity = raw.BorrName.str.upper() + '|' + raw.BorrStreet.str.upper() + '|' + raw.BorrZip
    ml['BorrowerGroup'] = identity.loc[cohort].map(lambda x: hashlib.sha256(x.encode()).hexdigest())
    ml.to_csv(output / 'mining_resolved.csv', index=False)
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/processed')
    args = parser.parse_args()
    result = prepare(args.input, args.output)
    print(json.dumps({'rows': result['rows'], 'tables': result['table_rows'], 'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
