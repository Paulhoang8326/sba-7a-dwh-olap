"""Synthetic, PII-free tests; no pytest or full clean-CSV export needed.

python -m unittest discover -s tests -p test_prepare_ssis_input.py -v
"""
import csv
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.etl import preprocess as pp
from src.etl import prepare_ssis_input as ssis


def fixture():
    # Borr fields stay empty. Identical first two records must both survive.
    row = dict.fromkeys(pp.SOURCE_COLUMNS, '')
    row.update(AsOfDate='2026-06-30', Program='7A', LocationID='00123',
               ApprovalDate='2024-10-01', ApprovalFY='2025', LoanStatus='P I F',
               GrossApproval='5000000', SBAGuaranteedApproval='3749992.425',
               GrossChargeOffAmount='0', JobsSupported='0', TermInMonths='120',
               NaicsCode='311811', NaicsDescription='Bakery', ProcessingMethod='7A',
               ProjectState='CA', ProjectCounty='Example', BusinessType='CORPORATION',
               BusinessAge='Unanswered', BankName='Test bank',
               FirstDisbursementDate='2024-10-02', PaidInFullDate='2025-01-01',
               CongressionalDistrict='01', SBADistrictOffice=' Office\r\nName ',
               BankFDICNumber='00012', BankStreet=' Rue École\t1 ', BankCity='Test city',
               BankState='CA', BankZip='00101', FixedorVariableInterestInd='F',
               RevolverStatus='N', CollateralInd='Y')
    other = {**row, 'BusinessAge': '', 'PaidInFullDate': '',
             'SBAGuaranteedApproval': '3749975.124', 'TermInMonths': '0',
             'FixedorVariableInterestInd': '', 'CongressionalDistrict': ''}
    return pd.DataFrame([row, row.copy(), other], columns=pp.SOURCE_COLUMNS)


class SSISInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = pp.ROOT / 'tmp' / 'ssis_input_tests'
        cls.temp_root.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.raw = fixture()
        self.base, self.clean, _, _ = pp.standardize(self.raw, 'fixture')

    def test_contract_and_record_alignment(self):
        result = ssis.assemble_input(self.base, self.clean)
        self.assertEqual(result.shape, (3, 52))
        self.assertEqual(len(set(result.columns)), 52)
        self.assertFalse(any(c.startswith('Borr') for c in result.columns))
        pd.testing.assert_frame_equal(result[pp.OUTPUT_COLUMNS], self.base)
        pd.testing.assert_frame_equal(result[ssis.EXTRA_COLUMNS], self.clean[ssis.EXTRA_COLUMNS])
        self.assertEqual(result.SourceRecordOrdinal.tolist(), ['1', '2', '3'])
        self.assertEqual(result.IsExactDuplicate.tolist(), ['1', '1', '0'])
        self.assertEqual(result.BankZip.tolist(), ['00101'] * 3)
        self.assertEqual(result.BankStreet.tolist(), ['Rue École 1'] * 3)
        self.assertEqual(result.SBADistrictOffice.tolist(), ['Office Name'] * 3)
        self.assertIsNone(result.PaidInFullDate.iloc[2])
        self.assertEqual(result.SBAGuaranteedApproval.iloc[0], '3749992.425')
        self.assertEqual(result.BusinessAgeValueStatus.tolist(), ['PRESENT', 'PRESENT', 'MISSING'])

    def test_reject_reordered_enrichment(self):
        with self.assertRaises(ValueError):
            ssis.assemble_input(self.base, self.clean.iloc[::-1])

    def test_reject_noncontiguous_ordinal(self):
        self.base.loc[1, 'SourceRecordOrdinal'] = '1'
        with self.assertRaises(ValueError):
            ssis.assemble_input(self.base, self.clean)

    def test_decimal_limits_without_rounding(self):
        summary = ssis.money_summary(self.raw)
        self.assertEqual(summary['SBAGuaranteedApproval']['sum'], '11249959.974')
        for value in ['1.0001', '1000000000000000']:
            with self.subTest(value=value):
                raw = self.raw.copy()
                raw.loc[0, 'GrossApproval'] = value
                with self.assertRaises(ValueError):
                    ssis.money_summary(raw)

    def test_run_reproducible_and_existing_files_protected(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as directory:
            directory = Path(directory)
            source = directory / 'fixture.csv'
            self.raw.to_csv(source, index=False, encoding='utf-8', lineterminator='\r\n')
            baseline = ssis.frame_sha256(self.base)
            kwargs = {'expected_source_sha256': pp.sha256_file(source),
                      'expected_baseline_sha256': baseline}
            first = ssis.run(source, directory / 'first.tsv', **kwargs)
            second = ssis.run(source, directory / 'second.tsv', **kwargs)
            self.assertEqual(first['output']['sha256'], second['output']['sha256'])
            self.assertTrue(all(first['checks'].values()))
            self.assertFalse(any(directory.glob('*clean.csv')))
            with (directory / 'first.tsv').open(encoding='utf-8', newline='') as handle:
                rows = list(csv.reader(handle, delimiter='\t', quoting=csv.QUOTE_NONE))
            self.assertEqual(len(rows), 4)
            self.assertTrue(all(len(row) == 52 for row in rows))
            with self.assertRaises(FileExistsError):
                ssis.run(source, directory / 'first.tsv', **kwargs)
            with self.assertRaises(ValueError):
                ssis.run(source, directory / pp.TSV_NAME, **kwargs)
            with self.assertRaises(ValueError):
                ssis.run(source, directory / 'bad.tsv',
                         expected_source_sha256=kwargs['expected_source_sha256'],
                         expected_baseline_sha256='0' * 64)
            self.assertFalse((directory / 'bad.tsv').exists())
            self.assertEqual(pp.sha256_file(source), kwargs['expected_source_sha256'])

    def test_export_validation_detects_missing_record(self):
        frame = ssis.assemble_input(self.base, self.clean)
        with tempfile.TemporaryDirectory(dir=self.temp_root) as directory:
            path = Path(directory) / 'truncated.tsv'
            pp.write_tsv(frame.iloc[:2], path)
            with self.assertRaises(ValueError):
                ssis.validate_output(path, frame, self.raw, ssis.frame_sha256(self.base))


if __name__ == '__main__':
    unittest.main()
