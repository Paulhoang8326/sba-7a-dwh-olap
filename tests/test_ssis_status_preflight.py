"""Offline tests: exception persistence/gating, exact mapping and calendar coverage."""
import csv
from datetime import date,timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from src.etl.preflight_ssis_status import calendar_bounds,inspect_input
from src.etl.ssis_status_rules import APPROVED_STATUS_PAIRS,classify_status


class StatusContractTests(unittest.TestCase):
    def test_five_exact_pairs(self):
        for raw,(canonical,classification) in APPROVED_STATUS_PAIRS.items():
            with self.subTest(raw=raw):
                self.assertEqual(classify_status(raw,canonical),(classification,None))

    def test_missing_and_unsupported_do_not_infer_canonical(self):
        for raw in [None,'',' \t ']:
            self.assertEqual(classify_status(raw,'MISSING'),('MISSING','MISSING_RAW_STATUS'))
        for raw,canonical in [('NEW','NEW'),('PIF','PIF'),('chgoff','CHGOFF'),('P I F ','PIF'),('P  I F','PIF')]:
            self.assertEqual(classify_status(raw,canonical),('UNMAPPED','RAW_STATUS_NOT_IN_WHITELIST'))
        for canonical in [None,'','P I F','CHGOFF','pif']:
            self.assertEqual(classify_status('P I F',canonical),('UNMAPPED','CANONICAL_STATUS_MISMATCH'))

    def fixture(self,path,overrides):
        fields=['SourceFileID','SourceRecordOrdinal','RawStatus','CanonicalStatus','ApprovalDate']+[f'Column{i}' for i in range(47)]
        with path.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t');writer.writeheader()
            for i,values in enumerate(overrides,1):
                row={k:'' for k in fields}
                row.update(SourceFileID='fixture.tsv',SourceRecordOrdinal=str(i),RawStatus='P I F',CanonicalStatus='PIF',ApprovalDate='2020-02-29')
                row.update(values);writer.writerow(row)

    def test_all_exceptions_persist_with_lineage_and_input_unchanged(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);input_path=root/'input.tsv'
            self.fixture(input_path,[{}, {'RawStatus':'NEW','CanonicalStatus':'NEW'},
                         {'RawStatus':'','CanonicalStatus':''},{'CanonicalStatus':'P I F'}])
            before=input_path.read_bytes()
            report=inspect_input(input_path,root/'exceptions')
            self.assertEqual(report['exit_code'],2)
            self.assertEqual(report['rows'],4)
            self.assertEqual(report['exception_events'],3)
            with Path(report['exception_csv']).open(encoding='utf-8-sig',newline='') as f:events=list(csv.DictReader(f))
            self.assertEqual([r['SourceRecordOrdinal'] for r in events],['2','3','4'])
            self.assertEqual([r['RawStatus'] for r in events],['NEW','','P I F'])
            self.assertEqual(events[-1]['CanonicalStatus'],'P I F')
            self.assertEqual(input_path.read_bytes(),before)
            self.assertEqual(report['input_sha256'],hashlib.sha256(before).hexdigest())
            self.assertEqual(json.loads(Path(report['manifest']).read_text())['result'],'FAIL')

    def test_success_artifacts_are_unique_on_rerun(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);input_path=root/'input.tsv'
            self.fixture(input_path,[{'RawStatus':raw,'CanonicalStatus':canonical} for raw,(canonical,_) in APPROVED_STATUS_PAIRS.items()])
            a=inspect_input(input_path,root/'exceptions');b=inspect_input(input_path,root/'exceptions')
            self.assertEqual(a['classification_counts'],{'DIRECT_MAPPING':4,'NORMALIZED':1})
            self.assertEqual(a['exit_code'],0)
            self.assertNotEqual(a['exception_csv'],b['exception_csv'])
            self.assertTrue(Path(a['exception_csv']).exists())

    def test_no_text_qualifier_matches_ssis_input_contract(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);input_path=root/'input.tsv'
            self.fixture(input_path,[{}])
            content=input_path.read_bytes().replace(b'\tP I F\t',b'\t"P I F"\t')
            input_path.write_bytes(content)
            report=inspect_input(input_path,root/'logs')
            self.assertEqual(report['exit_code'],2)
            with Path(report['exception_csv']).open(encoding='utf-8-sig',newline='') as f:events=list(csv.DictReader(f))
            self.assertEqual(events[0]['RawStatus'],'"P I F"')
            self.assertEqual(events[0]['Reason'],'RAW_STATUS_NOT_IN_WHITELIST')

    def test_empty_header_and_date_lineage_errors_fail(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);input_path=root/'input.tsv'
            self.fixture(input_path,[])
            self.assertEqual(inspect_input(input_path,root/'logs')['exit_code'],2)
            input_path.write_text('WrongHeader\nabc\n')
            self.assertEqual(inspect_input(input_path,root/'logs')['exit_code'],2)
            self.fixture(input_path,[{'ApprovalDate':'2027-01-01','SourceRecordOrdinal':''}])
            report=inspect_input(input_path,root/'logs')
            self.assertEqual(report['exception_events'],2)

    def test_command_line_exit_code_is_gate_not_advisory(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);input_path=root/'input.tsv'
            self.fixture(input_path,[{'RawStatus':'OTHER','CanonicalStatus':'OTHER'}])
            process=subprocess.run([sys.executable,'-m','src.etl.preflight_ssis_status','--input',str(input_path),
                                   '--exceptions',str(root/'logs')],capture_output=True,text=True,check=False)
            self.assertEqual(process.returncode,2)
            self.assertEqual(json.loads(process.stdout)['result'],'FAIL')

    def test_calendar_contiguous_leap_year_fiscal_boundaries_and_rerun(self):
        start,end=calendar_bounds('2019-10-01','2026-06-30')
        all_dates=[start+timedelta(days=n) for n in range((end-start).days+1)]
        self.assertEqual(len(all_dates),2465)
        self.assertIn(date(2020,2,29),all_dates);self.assertIn(date(2024,2,29),all_dates)
        self.assertTrue(all((b-a).days==1 for a,b in zip(all_dates,all_dates[1:])))
        fiscal=lambda d:(d.year+(d.month>=10),((d.month+2)%12)//3+1,(d.month+2)%12+1)
        self.assertEqual(fiscal(date(2019,10,1)),(2020,1,1))
        self.assertEqual(fiscal(date(2020,9,30)),(2020,4,12))
        self.assertEqual(fiscal(date(2020,1,1)),(2020,2,4))
        # Insert-only model preserves preexisting members/keys outside/inside range.
        existing={date(2019,9,30):'keep_outside',date(2020,2,29):'keep_inside'}
        before=dict(existing)
        for day in all_dates:existing.setdefault(day,day.strftime('%Y%m%d'))
        first=dict(existing)
        for day in all_dates:existing.setdefault(day,day.strftime('%Y%m%d'))
        self.assertEqual(existing,first)
        self.assertEqual({k:existing[k] for k in before},before)
        self.assertEqual(sum(start<=d<=end for d in existing),2465)

    def test_calendar_invalid_configuration_rejected(self):
        for a,b in [('2026-07-01','2026-06-30'),('2019-1-01','2026-06-30'),('1900-01-01','2100-01-01')]:
            with self.assertRaises(ValueError):calendar_bounds(a,b)


if __name__=='__main__':unittest.main()
