"""Build the Chapter 2 input without changing Chapter 1 exports or reports.

Run from the repository root: python -m src.etl.prepare_ssis_input
Only the allowlisted 52-column TSV and its small local manifest are written.
Existing output files are refused; use --output with a new path for another run.
"""
import argparse
import csv
import hashlib
import json
from decimal import Decimal
from itertools import zip_longest
from pathlib import Path

from src.etl import preprocess as pp


EXTRA_COLUMNS = [
    'FirstDisbursementDate', 'PaidInFullDate', 'ChargeOffDate',
    'CongressionalDistrict', 'SBADistrictOffice',
    'BankFDICNumber', 'BankNCUANumber', 'BankStreet', 'BankCity', 'BankState', 'BankZip',
    'FixedorVariableInterestInd', 'RevolverStatus', 'CollateralInd',
]
OUTPUT_COLUMNS = [*pp.OUTPUT_COLUMNS, *EXTRA_COLUMNS]
OUTPUT = pp.STAGING_DIR / 'chapter2' / 'sba7a_ssis_input.tsv'
BASELINE = json.loads((pp.REPORT_DIR / 'manifest.json').read_text(encoding='utf-8'))
BASELINE_SHA256 = BASELINE['outputs']['standardized_tsv']['sha256']


def serialized_row(values):
    """Use the exact Chapter 1 text/NULL/CRLF representation."""
    return ('\t'.join(v if isinstance(v, str) else '' for v in values) + '\r\n').encode('utf-8')


def frame_sha256(frame):
    digest = hashlib.sha256(serialized_row(frame.columns))
    for row in frame.itertuples(index=False, name=None):
        digest.update(serialized_row(row))
    return digest.hexdigest()


def assemble_input(standardized, cleaned):
    """Append attributes by the shared parser index, never by business attributes."""
    if list(standardized.columns) != pp.OUTPUT_COLUMNS:
        raise ValueError('Unexpected Chapter 1 column contract.')
    if not standardized.index.equals(cleaned.index):
        raise ValueError('Source record indexes differ; enrichment would misalign rows.')
    expected = [str(i) for i in range(1, len(standardized) + 1)]
    if standardized['SourceRecordOrdinal'].tolist() != expected:
        raise ValueError('SourceRecordOrdinal must preserve parser order 1..N.')
    result = standardized.copy()
    for column in EXTRA_COLUMNS:
        result[column] = cleaned[column]
    if list(result.columns) != OUTPUT_COLUMNS or len(result.columns) != 52:
        raise ValueError('Unexpected SSIS column contract.')
    return result


def money_summary(raw):
    """Check exact representability, not a rounded approximation of the source."""
    result = {}
    for column in pp.AMOUNT_COLUMNS:
        values = [pp.parse_decimal(v.strip() or None) for v in raw[column]]
        values = [v for v in values if v is not None]
        if any(abs(v) >= Decimal('1e15') or v != v.quantize(Decimal('.001')) for v in values):
            raise ValueError(f'{column} does not fit DECIMAL(18,3) exactly.')
        result[column] = {
            'min': str(min(values)), 'max': str(max(values)),
            'sum': str(sum(values, Decimal(0))),
            'scale_gt_2_records': sum(v.as_tuple().exponent < -2 for v in values),
        }
    return result


def validate_output(path, expected, raw, baseline_sha256):
    """Re-read every exported cell, projection checksum and exact measure totals."""
    sums = {column: Decimal(0) for column in pp.MEASURES}
    positions = {c: OUTPUT_COLUMNS.index(c) for c in pp.MEASURES}
    projection = hashlib.sha256(serialized_row(pp.OUTPUT_COLUMNS))
    count = 0
    sentinel = object()
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.reader(handle, delimiter='\t', quoting=csv.QUOTE_NONE)
        if next(reader) != OUTPUT_COLUMNS:
            raise ValueError('Export header differs from the 52-column contract.')
        for actual, original in zip_longest(
                reader, expected.itertuples(index=False, name=None), fillvalue=sentinel):
            if actual is sentinel or original is sentinel:
                raise ValueError('Export row count differs from source.')
            count += 1
            wanted = [v if isinstance(v, str) else '' for v in original]
            if actual != wanted:
                raise ValueError(f'Export differs at source record {count}.')
            projection.update(serialized_row(actual[:len(pp.OUTPUT_COLUMNS)]))
            for column, position in positions.items():
                if actual[position]:
                    sums[column] += Decimal(actual[position])
    if count != len(raw) or projection.hexdigest() != baseline_sha256:
        raise ValueError('Chapter 1 row count or projected TSV checksum changed.')
    for column, total in sums.items():
        if total != pp.decimal_sum(raw[column]):
            raise ValueError(f'Measure reconciliation failed: {column}.')
    return {column: str(total) for column, total in sums.items()}


def run(source=pp.SOURCE, output=OUTPUT, *, expected_source_sha256=pp.EXPECTED_SHA256,
        expected_baseline_sha256=BASELINE_SHA256):
    source, output = Path(source).resolve(), Path(output).resolve()
    manifest_path = output.with_suffix('.manifest.json')
    if output.name == pp.TSV_NAME or output == source or output.suffix.lower() != '.tsv':
        raise ValueError('Use a separate Chapter 2 .tsv path, not the Chapter 1 export/source.')
    for path in (output, manifest_path):
        if path.exists():
            raise FileExistsError(f'Refusing to overwrite {path}; choose a new --output path.')

    digest, _ = pp.check_source(source, expected_source_sha256)
    raw = pp.read_raw(source)
    money = money_summary(raw)
    # standardize is in-memory only. Never call run/export_outputs, which writes clean CSV.
    standardized, cleaned, _, _ = pp.standardize(raw, source.stem)
    if frame_sha256(standardized) != expected_baseline_sha256:
        raise ValueError('Reproduced Chapter 1 TSV differs from its committed manifest.')
    frame = assemble_input(standardized, cleaned)
    pp.write_tsv(frame, output)
    totals = validate_output(output, frame, raw, expected_baseline_sha256)
    manifest = {
        'schema_version': 'chapter2-ssis-input-v1',
        'preprocessing_rule_version': pp.RULE_VERSION,
        'source': {'file': source.name, 'source_file_id': source.stem, 'sha256': digest},
        'output': {'file': output.name, 'rows': len(frame), 'columns': OUTPUT_COLUMNS,
                   'bytes': output.stat().st_size, 'sha256': pp.sha256_file(output)},
        'format': 'UTF-8 without BOM; tab; CRLF; header; no text qualifier; NULL=empty',
        'chapter1_projection_sha256': expected_baseline_sha256,
        'additional_source_columns': EXTRA_COLUMNS,
        'money_decimal_18_3': money,
        'measure_totals': totals,
        'checks': {'all_52_cells_per_record_match': True, 'parser_order_preserved': True,
                   'chapter1_38_column_projection_matches': True, 'measure_totals_match': True},
    }
    with manifest_path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=pp.SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    manifest = run(args.source, args.output)
    print(json.dumps({'output': str(args.output), **manifest['output'],
                      'checks': manifest['checks']}, indent=2))


if __name__ == '__main__':
    main()
