"""BR-STATUS-01 technical mapping approved 2026-10-28; no raw/canonical mutation."""
RULE_VERSION = 'BR-STATUS-01-2026-10-28'
APPROVED_STATUS_PAIRS = {
    'CANCLD': ('CANCLD', 'DIRECT_MAPPING'),
    'CHGOFF': ('CHGOFF', 'DIRECT_MAPPING'),
    'COMMIT': ('COMMIT', 'DIRECT_MAPPING'),
    'EXEMPT': ('EXEMPT', 'DIRECT_MAPPING'),
    'P I F': ('PIF', 'NORMALIZED'),
}


def classify_status(raw, canonical):
    """Return technical classification/reason. Never infer a business status.

    Only missingness trims whitespace. Nonempty labels/pairs must match exactly;
    unsupported raw PIF, casing changes and extra whitespace are exceptions.
    """
    if raw is None or not raw.strip():
        return 'MISSING', 'MISSING_RAW_STATUS'
    expected = APPROVED_STATUS_PAIRS.get(raw)
    if expected is None:
        return 'UNMAPPED', 'RAW_STATUS_NOT_IN_WHITELIST'
    if canonical != expected[0]:
        return 'UNMAPPED', 'CANONICAL_STATUS_MISMATCH'
    return expected[1], None
