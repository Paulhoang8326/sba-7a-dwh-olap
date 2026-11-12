"""Read-only SSIS input gate: write exception CSV/manifest, exit nonzero on error.

Run by the package's Execute Process Task *before* Create_All_Tables. No database
library, no input changes, no dropping/skipping records. Python standard library.
"""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid

from .ssis_status_rules import RULE_VERSION, classify_status

EXCEPTION_FIELDS = ['InputRecordNumber', 'SourceFileID', 'SourceRecordOrdinal',
                    'RawStatus', 'CanonicalStatus', 'StatusMappingStatus', 'Reason']


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def calendar_bounds(start, end):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    if a.isoformat() != start or b.isoformat() != end or not 0 <= (b-a).days <= 36600:
        raise ValueError('Calendar bounds require ISO YYYY-MM-DD, start<=end and <=36601 days')
    return a, b


def inspect_input(input_path, output_dir, start='2019-10-01', end='2026-06-30'):
    """Inspect all rows, persist all exceptions, and return a machine-readable report.

    A failure writing artifacts raises an error (the caller returns failure).
    Manifests and CSV use unique names + exclusive create, never overwrite logs.
    """
    input_path, output_dir = Path(input_path).resolve(), Path(output_dir).resolve()
    a, b = calendar_bounds(start, end)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    csv_path = output_dir / ('status_exceptions_'+run_id+'.csv')
    json_path = output_dir / ('status_preflight_'+run_id+'.json')
    counts, reasons, rows, errors = Counter(), Counter(), 0, 0
    first_stat = input_path.stat()
    fingerprint = sha256(input_path)
    minimum, maximum = None, None
    with csv_path.open('x', encoding='utf-8-sig', newline='') as destination:
        writer = csv.DictWriter(destination, fieldnames=EXCEPTION_FIELDS)
        writer.writeheader()

        def exception(number, row, classification, reason):
            nonlocal errors
            errors += 1
            reasons[reason] += 1
            writer.writerow({'InputRecordNumber': number,
                             **{k: row.get(k) for k in EXCEPTION_FIELDS[1:5]},
                             'StatusMappingStatus': classification, 'Reason': reason})

        with input_path.open(encoding='utf-8-sig', newline='') as source:
            # SSIS input has no text qualifier: quoted labels must stay literal
            # and be rejected rather than accepted by Python's CSV unquoting.
            reader = csv.DictReader(source, delimiter='\t', quoting=csv.QUOTE_NONE)
            required = {'SourceFileID', 'SourceRecordOrdinal', 'RawStatus', 'CanonicalStatus', 'ApprovalDate'}
            if reader.fieldnames is None or not required <= set(reader.fieldnames):
                exception(0, {}, 'UNMAPPED', 'INPUT_HEADER_MISSING_REQUIRED_COLUMNS')
            elif len(reader.fieldnames) != len(set(reader.fieldnames)) or len(reader.fieldnames) != 52:
                exception(0, {}, 'UNMAPPED', 'INPUT_HEADER_NOT_52_UNIQUE_COLUMNS')
            else:
                for number, row in enumerate(reader, 1):
                    rows += 1
                    classification, reason = classify_status(row.get('RawStatus'), row.get('CanonicalStatus'))
                    counts[classification] += 1
                    if reason:
                        exception(number, row, classification, reason)
                    if None in row or any(v is None for v in row.values()):
                        exception(number, row, classification, 'MALFORMED_INPUT_ROW')
                    ordinal = row.get('SourceRecordOrdinal') or ''
                    if not row.get('SourceFileID') or not ordinal.isascii() or not ordinal.isdecimal() or int(ordinal) <= 0:
                        exception(number, row, classification, 'MISSING_OR_INVALID_LINEAGE')
                    try:
                        raw_date = row.get('ApprovalDate') or ''
                        value = date.fromisoformat(raw_date)
                        if value.isoformat() != raw_date or not a <= value <= b:
                            raise ValueError('ApprovalDate outside calendar bounds')
                        minimum = value if minimum is None else min(minimum, value)
                        maximum = value if maximum is None else max(maximum, value)
                    except ValueError:
                        exception(number, row, classification, 'INVALID_OR_OUT_OF_RANGE_APPROVAL_DATE')
        if rows == 0:
            exception(0, {}, 'UNMAPPED', 'EMPTY_INPUT')
        last_stat = input_path.stat()
        if (first_stat.st_size, first_stat.st_mtime_ns) != (last_stat.st_size, last_stat.st_mtime_ns) or sha256(input_path) != fingerprint:
            exception(0, {}, 'UNMAPPED', 'INPUT_CHANGED_DURING_PREFLIGHT')
    report = {'rule_version': RULE_VERSION, 'run_id': run_id, 'input_path': str(input_path),
              'input_sha256': fingerprint, 'rows': rows, 'classification_counts': dict(counts),
              'exception_events': errors, 'exception_reasons': dict(reasons),
              'exception_csv': str(csv_path), 'manifest': str(json_path),
              'calendar_start': start, 'calendar_end': end, 'calendar_days': (b-a).days+1,
              'min_approval_date': minimum.isoformat() if minimum else None,
              'max_approval_date': maximum.isoformat() if maximum else None,
              'result': 'FAIL' if errors else 'PASS', 'exit_code': 2 if errors else 0}
    with json_path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--exceptions', type=Path, required=True)
    parser.add_argument('--calendar-start', default='2019-10-01')
    parser.add_argument('--calendar-end', default='2026-06-30')
    args = parser.parse_args(argv)
    try:
        report = inspect_input(args.input, args.exceptions, args.calendar_start, args.calendar_end)
    except (OSError, ValueError, csv.Error) as exc:
        print('PREFLIGHT_ERROR: '+str(exc), file=sys.stderr)
        return 3
    print(json.dumps(report, ensure_ascii=True))
    return report['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
