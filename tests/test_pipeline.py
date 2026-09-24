import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.main import ROOT, prepare, sector

RAW_CSV = ROOT / 'data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv'

# Check Git LFS pointer on import to provide clear diagnostic on fresh clones
if not RAW_CSV.exists():
    raise FileNotFoundError(
        f"Missing raw data CSV file: {RAW_CSV}. "
        "Please ensure the repository was cloned with Git LFS enabled."
    )

with RAW_CSV.open('rb') as _f:
    _header = _f.read(50)
if RAW_CSV.stat().st_size < 1024 or _header.startswith(b'version https://git-lfs'):
    raise RuntimeError(
        f"File '{RAW_CSV.name}' is a Git LFS pointer ({RAW_CSV.stat().st_size} bytes), not the actual dataset. "
        "Please install Git LFS ('git lfs install') and run 'git lfs pull' before running tests or pipeline."
    )


class PipelineTests(unittest.TestCase):
    def test_sector_groups(self):
        self.assertEqual(sector('311111'), '31-33')
        self.assertEqual(sector('451110'), '44-45')
        self.assertEqual(sector('492110'), '48-49')

    def test_missing_rate_and_date_duplicates_and_county_keys(self):
        row = pd.read_csv(RAW_CSV,
                          dtype=str, keep_default_na=False, nrows=1).iloc[0].to_dict()
        row.update(InitialInterestRate='', FirstDisbursementDate='', ProjectCounty='SAME',
                   LoanStatus='EXEMPT', PaidInFullDate='')
        other = dict(row, ProjectState='TX', InitialInterestRate='10', LoanStatus='P I F')
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'source.csv'
            pd.DataFrame([row,row,other]).to_csv(source,index=False)
            output=Path(temp)/'out'
            p=prepare(source,output)
            fact=pd.read_csv(output/'FactLoanSnapshot.csv')
            self.assertEqual(p['rows'],3)
            self.assertEqual(p['normalized_duplicate_rows'],1)
            self.assertEqual(p['table_rows']['DimCounty'],2)
            self.assertEqual(fact.InterestKnownApproval.sum(),float(other['GrossApproval']))
            self.assertEqual(fact.DisbursementObservedCount.sum(),0)
            self.assertEqual(fact.ResolvedCount.sum(),1)
            self.assertTrue(fact.FirstDisbursementDateKey.isna().all())
            self.assertNotIn('AsOfDateKey', fact.columns)
            self.assertEqual(len(pd.read_csv(output/'mining_resolved.csv')),1)

    def test_full_snapshot_integrity(self):
        out=ROOT/'data/processed'
        if not (out/'profile.json').exists():
            self.skipTest(
                "Missing data/processed/profile.json (gitignored directory). "
                "Run 'python -m src.main' first to generate warehouse tables and enable full-source integrity tests."
            )
        p=json.loads((out/'profile.json').read_text(encoding='utf-8'))
        fact=pd.read_csv(out/'FactLoanSnapshot.csv')
        raw=pd.read_csv(RAW_CSV,
                        usecols=['GrossApproval','SBAGuaranteedApproval','GrossChargeOffAmount','JobsSupported'])
        self.assertEqual(len(fact),len(raw))
        self.assertEqual(len(fact),p['rows'])
        self.assertTrue(fact.LoanRowKey.is_unique)
        for c in raw:
            self.assertAlmostEqual(raw[c].sum(),fact[c].sum(),places=3)
        for dim,key in [('DimCounty','CountyKey'),('DimIndustry','IndustryKey'),('DimLender','LenderKey'),
                        ('DimBusiness','BusinessKey'),('DimLoanProfile','LoanProfileKey')]:
            values=pd.read_csv(out/f'{dim}.csv')[key]
            self.assertTrue(values.is_unique)
            self.assertTrue(fact[key].isin(values).all())
        self.assertNotIn('AsOfDateKey', fact.columns)
        dates=pd.read_csv(out/'DimDate.csv').DateKey
        for key in ['ApprovalDateKey','FirstDisbursementDateKey','PaidInFullDateKey','ChargeOffDateKey']:
            self.assertTrue(fact[key].dropna().isin(dates).all())
        for child,parent,key in [('DimCounty','DimState','StateKey'),('DimIndustry','DimSector','SectorKey')]:
            self.assertTrue(pd.read_csv(out/f'{child}.csv')[key].isin(pd.read_csv(out/f'{parent}.csv')[key]).all())
        mart=pd.read_csv(out/'mart_portfolio.csv')
        for c in ['GrossApproval','SBAGuaranteedApproval','GrossChargeOffAmount','JobsSupported','LoanCount']:
            self.assertAlmostEqual(mart[c].sum(),fact[c].sum(),places=3)
        self.assertEqual(int(fact.ResolvedCount.sum()),75094)
        self.assertEqual(int(fact.ChargeOffCount.sum()),6893)


if __name__ == '__main__':
    unittest.main()
