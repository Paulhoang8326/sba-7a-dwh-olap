import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.main import ROOT, prepare, sector


class PipelineTests(unittest.TestCase):
    def test_sector_groups(self):
        self.assertEqual(sector('311111'), '31-33')
        self.assertEqual(sector('451110'), '44-45')
        self.assertEqual(sector('492110'), '48-49')

    def test_missing_rate_and_date_duplicates_and_county_keys(self):
        row = pd.read_csv(ROOT / 'data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv',
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
            self.assertEqual(len(pd.read_csv(output/'mining_resolved.csv')),1)

    def test_full_snapshot_integrity(self):
        out=ROOT/'data/processed'
        if not (out/'profile.json').exists():
            self.skipTest('Run python -m src.main for full-source checks')
        p=json.loads((out/'profile.json').read_text(encoding='utf-8'))
        fact=pd.read_csv(out/'FactLoanSnapshot.csv')
        raw=pd.read_csv(ROOT/'data/raw/foia/FOIA_7a_FY2020_Present_asof_260630.csv',
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
        dates=pd.read_csv(out/'DimDate.csv').DateKey
        for key in ['AsOfDateKey','ApprovalDateKey','FirstDisbursementDateKey','PaidInFullDateKey','ChargeOffDateKey']:
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
