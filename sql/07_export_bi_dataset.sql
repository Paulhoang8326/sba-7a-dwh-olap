-- Chapter 4: flat dataset for Looker Studio (CSV upload) and the Power BI Import fallback.
-- Run in SSMS on SBA7A_DWH, then right-click the result grid -> Save Results As... -> .csv.
-- Keeps every published record (BR-POP-01). Only report columns are selected so the CSV
-- stays under the 100 MB Looker upload limit (about 64 MB for 388,338 rows).
-- Same output as: python -m src.reporting.export_bi_dataset
USE SBA7A_DWH;
SET NOCOUNT ON;

SELECT
    d.FullDate                                   AS ApprovalDate,
    d.FiscalYear                                 AS FiscalYear,
    CONCAT('Q', d.FiscalQuarter)                 AS FiscalQuarter,
    COALESCE(NULLIF(g.ProjectState, ''), '(Missing)')  AS ProjectState,
    COALESCE(NULLIF(g.ProjectCounty, ''), '(Missing)') AS ProjectCounty,
    COALESCE(i.NaicsSectorCode + ' - ' + i.NaicsSectorName, '(Missing)') AS NaicsSector,
    COALESCE(NULLIF(l.BankName, ''), '(Missing)')      AS BankName,
    COALESCE(NULLIF(p.ProcessingMethod, ''), '(Missing)') AS ProcessingMethod,
    s.RawStatus                                  AS RawStatus,
    s.CanonicalStatus                            AS LoanStatus,
    CONCAT(t.SortOrder, '. ', t.TermBandName)    AS TermBand,
    f.GrossApproval,
    f.SBAGuaranteedApproval,
    f.GrossChargeOffAmount,
    f.JobsSupported,
    CASE WHEN s.RawStatus = 'CHGOFF' THEN 1 ELSE 0 END AS ChargeOffRecord
FROM dbo.Fact_Loan f
JOIN dbo.Dim_Date             d ON d.DateKey        = f.ApprovalDateKey
JOIN dbo.Dim_ProjectGeography g ON g.GeographyKey   = f.GeographyKey
JOIN dbo.Dim_Industry         i ON i.IndustryKey    = f.IndustryKey
JOIN dbo.Dim_Lender           l ON l.LenderKey      = f.LenderKey
JOIN dbo.Dim_LoanProfile      p ON p.LoanProfileKey = f.LoanProfileKey
JOIN dbo.Dim_LoanStatus       s ON s.LoanStatusKey  = f.LoanStatusKey
JOIN dbo.Dim_TermBand         t ON t.TermBandKey    = f.TermBandKey
ORDER BY f.LoanKey;
