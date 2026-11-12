-- READ ONLY. Prepared 2026-10-28; NOT EXECUTED by Codex.
-- Save results before/after backfill and after each approved test ETL run.
SET NOCOUNT ON;
IF DB_NAME()<>N'SBA7A_DWH' THROW 51100,'Connect to SBA7A_DWH.',1;

SELECT 'Dim_Date' AS TableName,COUNT_BIG(*) AS Rows FROM dbo.Dim_Date
UNION ALL SELECT 'Dim_TermBand',COUNT_BIG(*) FROM dbo.Dim_TermBand
UNION ALL SELECT 'Dim_LoanStatus',COUNT_BIG(*) FROM dbo.Dim_LoanStatus
UNION ALL SELECT 'Dim_Business',COUNT_BIG(*) FROM dbo.Dim_Business
UNION ALL SELECT 'Dim_ProjectGeography',COUNT_BIG(*) FROM dbo.Dim_ProjectGeography
UNION ALL SELECT 'Dim_Industry',COUNT_BIG(*) FROM dbo.Dim_Industry
UNION ALL SELECT 'Dim_Lender',COUNT_BIG(*) FROM dbo.Dim_Lender
UNION ALL SELECT 'Dim_LoanProfile',COUNT_BIG(*) FROM dbo.Dim_LoanProfile
UNION ALL SELECT 'Fact_Loan',COUNT_BIG(*) FROM dbo.Fact_Loan;
SELECT COUNT_BIG(*) AS FactRows,SUM(CONVERT(bigint,RecordCount)) AS PublishedRecordCount,
 SUM(GrossApproval) AS GrossApproval,SUM(SBAGuaranteedApproval) AS SBAGuaranteedApproval,
 SUM(GrossChargeOffAmount) AS GrossChargeOffAmount,SUM(CONVERT(bigint,JobsSupported)) AS JobsSupported,
 MIN(LoanKey) AS MinLoanKey,MAX(LoanKey) AS MaxLoanKey FROM dbo.Fact_Loan;

SELECT 'MonthName' AS Attribute,COUNT_BIG(*) AS MissingValues FROM dbo.Dim_Date WHERE NULLIF(LTRIM(RTRIM(MonthName)),'') IS NULL
UNION ALL SELECT 'TermBandName',COUNT_BIG(*) FROM dbo.Dim_TermBand WHERE NULLIF(LTRIM(RTRIM(TermBandName)),'') IS NULL
UNION ALL SELECT 'SortOrder',COUNT_BIG(*) FROM dbo.Dim_TermBand WHERE SortOrder IS NULL
UNION ALL SELECT 'BandStatus',COUNT_BIG(*) FROM dbo.Dim_TermBand WHERE NULLIF(LTRIM(RTRIM(BandStatus)),'') IS NULL
UNION ALL SELECT 'StatusMappingStatus',COUNT_BIG(*) FROM dbo.Dim_LoanStatus WHERE NULLIF(LTRIM(RTRIM(StatusMappingStatus)),'') IS NULL;
SELECT TermBandKey,TermBandCode,TermBandName,MinMonths,MaxMonths,SortOrder,BandStatus
FROM dbo.Dim_TermBand ORDER BY SortOrder;
SELECT LoanStatusKey,RawStatus,CanonicalStatus,StatusMappingStatus FROM dbo.Dim_LoanStatus;
-- All rows should be approved exact pairs after script 05; exceptions require review.
SELECT LoanStatusKey,RawStatus,CanonicalStatus,StatusMappingStatus FROM dbo.Dim_LoanStatus
WHERE NOT (
 (CONVERT(varbinary(100),RawStatus)=CONVERT(varbinary(100),'CANCLD') AND CONVERT(varbinary(100),CanonicalStatus)=CONVERT(varbinary(100),'CANCLD') AND StatusMappingStatus='DIRECT_MAPPING') OR
 (CONVERT(varbinary(100),RawStatus)=CONVERT(varbinary(100),'CHGOFF') AND CONVERT(varbinary(100),CanonicalStatus)=CONVERT(varbinary(100),'CHGOFF') AND StatusMappingStatus='DIRECT_MAPPING') OR
 (CONVERT(varbinary(100),RawStatus)=CONVERT(varbinary(100),'COMMIT') AND CONVERT(varbinary(100),CanonicalStatus)=CONVERT(varbinary(100),'COMMIT') AND StatusMappingStatus='DIRECT_MAPPING') OR
 (CONVERT(varbinary(100),RawStatus)=CONVERT(varbinary(100),'EXEMPT') AND CONVERT(varbinary(100),CanonicalStatus)=CONVERT(varbinary(100),'EXEMPT') AND StatusMappingStatus='DIRECT_MAPPING') OR
 (CONVERT(varbinary(100),RawStatus)=CONVERT(varbinary(100),'P I F') AND CONVERT(varbinary(100),CanonicalStatus)=CONVERT(varbinary(100),'PIF') AND StatusMappingStatus='NORMALIZED'))
 OR RawStatus IS NULL OR CanonicalStatus IS NULL OR StatusMappingStatus IS NULL;
SELECT MIN(FullDate) AS MinFullDate,MAX(FullDate) AS MaxFullDate,COUNT_BIG(*) AS DateRows,
 DATEDIFF(day,MIN(FullDate),MAX(FullDate))+1 AS CalendarDays FROM dbo.Dim_Date;
SELECT FullDate,COUNT_BIG(*) AS DuplicateCount FROM dbo.Dim_Date GROUP BY FullDate HAVING COUNT_BIG(*)>1;
SELECT DateKey,FullDate,CalendarMonth FROM dbo.Dim_Date WHERE
 DateKey<>CONVERT(int,CONVERT(char(8),FullDate,112)) OR CalendarMonth<>MONTH(FullDate);

-- Every result below should be empty before allowing a rerun. Do not delete duplicates automatically.
SELECT SourceFileID,SourceRecordOrdinal,COUNT_BIG(*) AS DuplicateCount FROM dbo.Fact_Loan
GROUP BY SourceFileID,SourceRecordOrdinal HAVING COUNT_BIG(*)>1;
SELECT COALESCE(NULLIF(LTRIM(RTRIM(BusinessTypeRaw)),''),'(Missing)') AS BusinessType,
 COALESCE(NULLIF(LTRIM(RTRIM(BusinessAgeRaw)),''),'(Missing)') AS BusinessAge,COUNT_BIG(*) AS DuplicateCount
FROM dbo.Dim_Business GROUP BY COALESCE(NULLIF(LTRIM(RTRIM(BusinessTypeRaw)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(BusinessAgeRaw)),''),'(Missing)') HAVING COUNT_BIG(*)>1;
SELECT RawStatus,COUNT_BIG(*) AS DuplicateCount FROM dbo.Dim_LoanStatus GROUP BY RawStatus HAVING COUNT_BIG(*)>1;
SELECT TermBandCode,COUNT_BIG(*) AS DuplicateCount FROM dbo.Dim_TermBand GROUP BY TermBandCode HAVING COUNT_BIG(*)>1;
SELECT LocationID,COUNT_BIG(*) AS DuplicateCount FROM dbo.Dim_Lender GROUP BY LocationID HAVING COUNT_BIG(*)>1;
SELECT COALESCE(NULLIF(LTRIM(RTRIM(NaicsCode)),''),'(Missing)') AS Code,
 COALESCE(NULLIF(LTRIM(RTRIM(NaicsDescription)),''),'(Missing)') AS Description,COUNT_BIG(*) AS DuplicateCount
FROM dbo.Dim_Industry GROUP BY COALESCE(NULLIF(LTRIM(RTRIM(NaicsCode)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(NaicsDescription)),''),'(Missing)') HAVING COUNT_BIG(*)>1;
SELECT COALESCE(NULLIF(LTRIM(RTRIM(ProcessingMethod)),''),'(Missing)') AS Method,
 COALESCE(NULLIF(LTRIM(RTRIM(FixedOrVariableInterestInd)),''),'(Missing)') AS Interest,
 COALESCE(NULLIF(LTRIM(RTRIM(RevolverStatus)),''),'(Missing)') AS Revolver,
 COALESCE(NULLIF(LTRIM(RTRIM(CollateralInd)),''),'(Missing)') AS Collateral,COUNT_BIG(*) AS DuplicateCount
FROM dbo.Dim_LoanProfile GROUP BY COALESCE(NULLIF(LTRIM(RTRIM(ProcessingMethod)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(FixedOrVariableInterestInd)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(RevolverStatus)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(CollateralInd)),''),'(Missing)') HAVING COUNT_BIG(*)>1;
SELECT COALESCE(NULLIF(LTRIM(RTRIM(ProjectState)),''),'(Missing)') AS State,
 COALESCE(NULLIF(LTRIM(RTRIM(ProjectCounty)),''),'(Missing)') AS County,
 COALESCE(NULLIF(LTRIM(RTRIM(CongressionalDistrict)),''),'(Missing)') AS District,
 COALESCE(NULLIF(LTRIM(RTRIM(SBADistrictOffice)),''),'(Missing)') AS Office,COUNT_BIG(*) AS DuplicateCount
FROM dbo.Dim_ProjectGeography GROUP BY COALESCE(NULLIF(LTRIM(RTRIM(ProjectState)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(ProjectCounty)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(CongressionalDistrict)),''),'(Missing)'),
 COALESCE(NULLIF(LTRIM(RTRIM(SBADistrictOffice)),''),'(Missing)') HAVING COUNT_BIG(*)>1;

-- Eight orphan checks: every OrphanRows value must be zero.
SELECT 'ApprovalDateKey' AS ForeignKeyName,COUNT_BIG(*) AS OrphanRows FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_Date d ON d.DateKey=f.ApprovalDateKey WHERE d.DateKey IS NULL
UNION ALL SELECT 'GeographyKey',COUNT_BIG(*) FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_ProjectGeography d ON d.GeographyKey=f.GeographyKey WHERE d.GeographyKey IS NULL
UNION ALL SELECT 'IndustryKey',COUNT_BIG(*) FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_Industry d ON d.IndustryKey=f.IndustryKey WHERE d.IndustryKey IS NULL
UNION ALL SELECT 'LenderKey',COUNT_BIG(*) FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_Lender d ON d.LenderKey=f.LenderKey WHERE d.LenderKey IS NULL
UNION ALL SELECT 'LoanProfileKey',COUNT_BIG(*) FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_LoanProfile d ON d.LoanProfileKey=f.LoanProfileKey WHERE d.LoanProfileKey IS NULL
UNION ALL SELECT 'LoanStatusKey',COUNT_BIG(*) FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_LoanStatus d ON d.LoanStatusKey=f.LoanStatusKey WHERE d.LoanStatusKey IS NULL
UNION ALL SELECT 'TermBandKey',COUNT_BIG(*) FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_TermBand d ON d.TermBandKey=f.TermBandKey WHERE d.TermBandKey IS NULL
UNION ALL SELECT 'BusinessKey',COUNT_BIG(*) FROM dbo.Fact_Loan f LEFT JOIN dbo.Dim_Business d ON d.BusinessKey=f.BusinessKey WHERE d.BusinessKey IS NULL;
SELECT name,is_disabled,is_not_trusted FROM sys.foreign_keys WHERE parent_object_id=OBJECT_ID('dbo.Fact_Loan');
SELECT name,is_unique,is_disabled FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Fact_Loan');
SELECT COLUMN_NAME,DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='Fact_Loan' AND COLUMN_NAME='TermInMonths';

SELECT b.TermBandCode,b.TermBandName,b.SortOrder,b.BandStatus,COUNT_BIG(*) AS FactRows,
 MIN(f.TermInMonths) AS MinObservedMonths,MAX(f.TermInMonths) AS MaxObservedMonths
FROM dbo.Fact_Loan f JOIN dbo.Dim_TermBand b ON b.TermBandKey=f.TermBandKey
GROUP BY b.TermBandCode,b.TermBandName,b.SortOrder,b.BandStatus ORDER BY b.SortOrder;
SELECT f.LoanKey,f.TermInMonths,b.TermBandCode FROM dbo.Fact_Loan f
JOIN dbo.Dim_TermBand b ON b.TermBandKey=f.TermBandKey WHERE b.BandStatus='VALID'
AND (f.TermInMonths IS NULL OR f.TermInMonths<b.MinMonths
 OR (b.MaxMonths IS NOT NULL AND f.TermInMonths>b.MaxMonths));
