USE SBA7aDWH;
-- Must equal profile.json and all 388338 input rows for the supplied snapshot.
SELECT COUNT_BIG(*) AS RowsLoaded,SUM(GrossApproval) AS GrossApproval,
 SUM(SBAGuaranteedApproval) AS Guaranteed,SUM(GrossChargeOffAmount) AS ChargeOff
FROM dwh.FactLoanSnapshot;
SELECT FiscalYear,COUNT_BIG(*) AS LoanCount,SUM(GrossApproval) AS GrossApproval
FROM marts.vLoan GROUP BY FiscalYear ORDER BY FiscalYear;
SELECT LoanStatus,COUNT_BIG(*) AS LoanCount FROM marts.vLoan GROUP BY LoanStatus;
-- Every snowflake join must preserve the fact count.
SELECT (SELECT COUNT_BIG(*) FROM marts.vLoan) AS ViewRows,
 (SELECT COUNT_BIG(*) FROM dwh.FactLoanSnapshot) AS FactRows;
-- Keys are scoped to this single snapshot; do not append another snapshot.
SELECT COUNT(DISTINCT AsOfDateKey) AS SnapshotCount FROM dwh.FactLoanSnapshot;
