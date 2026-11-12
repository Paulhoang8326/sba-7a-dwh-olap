-- PREPARED ONLY / NOT EXECUTED. Review in SSMS before any execution.
-- 2026-10-28: user approved MonthName, six labels/orders and BandStatus.
-- StatusMappingStatus remains untouched: DIRECT_MAPPING/NORMALIZED proposal pending.
-- No INSERT/UPDATE/DELETE against Fact_Loan; no schema/key changes.
-- Default is PREVIEW ONLY: no persistent UPDATE unless @Apply = 1.
-- Run the whole file as one batch. Requires tempdb space for an exact Fact snapshot.
SET NOCOUNT ON;
SET XACT_ABORT ON;
DECLARE @Apply bit = 0;
DECLARE @ExpectedDateRows bigint = 2465, @ExpectedTermRows bigint = 6,
        @ExpectedStatusRows bigint = 5;
IF DB_NAME() <> N'SBA7A_DWH'
    THROW 51000, 'Connect to SBA7A_DWH. No changes made.', 1;
IF @@TRANCOUNT <> 0
    THROW 51001, 'Run outside an existing transaction.', 1;

DECLARE @Months TABLE (MonthNumber int PRIMARY KEY, MonthName varchar(20) NOT NULL);
INSERT @Months VALUES (1,'January'),(2,'February'),(3,'March'),(4,'April'),
 (5,'May'),(6,'June'),(7,'July'),(8,'August'),(9,'September'),(10,'October'),
 (11,'November'),(12,'December');
DECLARE @Bands TABLE (TermBandCode varchar(30) PRIMARY KEY,
 TermBandName varchar(100), SortOrder int, BandStatus varchar(30));
INSERT @Bands VALUES ('ZERO','0 months',1,'VALID'),('SHORT','1-60 months',2,'VALID'),
 ('MEDIUM','61-119 months',3,'VALID'),('TERM_120','120 months',4,'VALID'),
 ('LONG','121-240 months',5,'VALID'),('VERY_LONG','241+ months',6,'VALID');
-- No MISSING/INVALID seeds: current six rows have actual, approved ranges.

BEGIN TRY
 BEGIN TRANSACTION;
 -- Shared table locks freeze Fact and all referenced member keys during review/apply.
 -- Reject enabled UPDATE triggers instead of assuming that their side effects are safe.
 IF EXISTS (SELECT 1 FROM sys.triggers WHERE parent_id IN
    (OBJECT_ID('dbo.Dim_Date'),OBJECT_ID('dbo.Dim_TermBand')) AND is_disabled=0)
     THROW 51002, 'Enabled Dimension trigger requires separate review.', 1;
 IF (SELECT COUNT(*) FROM sys.columns WHERE object_id=OBJECT_ID('dbo.Fact_Loan'))<>22
     THROW 51013, 'Fact column contract differs from the 22-column audited DDL; review exact comparison first.', 1;

 SELECT * INTO #FactBefore FROM dbo.Fact_Loan WITH (TABLOCK,HOLDLOCK);
 SELECT * INTO #DateBefore FROM dbo.Dim_Date WITH (TABLOCK,HOLDLOCK);
 SELECT * INTO #TermBefore FROM dbo.Dim_TermBand WITH (TABLOCK,HOLDLOCK);
 SELECT * INTO #StatusBefore FROM dbo.Dim_LoanStatus WITH (TABLOCK,HOLDLOCK);
 DECLARE @OtherDimCounts TABLE (DimName sysname PRIMARY KEY, RowCountBefore bigint);
 INSERT @OtherDimCounts
 SELECT 'Dim_Business',COUNT_BIG(*) FROM dbo.Dim_Business WITH (TABLOCK,HOLDLOCK)
 UNION ALL SELECT 'Dim_ProjectGeography',COUNT_BIG(*) FROM dbo.Dim_ProjectGeography WITH (TABLOCK,HOLDLOCK)
 UNION ALL SELECT 'Dim_Industry',COUNT_BIG(*) FROM dbo.Dim_Industry WITH (TABLOCK,HOLDLOCK)
 UNION ALL SELECT 'Dim_Lender',COUNT_BIG(*) FROM dbo.Dim_Lender WITH (TABLOCK,HOLDLOCK)
 UNION ALL SELECT 'Dim_LoanProfile',COUNT_BIG(*) FROM dbo.Dim_LoanProfile WITH (TABLOCK,HOLDLOCK);

 IF (SELECT COUNT_BIG(*) FROM #DateBefore) <> @ExpectedDateRows
 OR (SELECT COUNT_BIG(*) FROM #TermBefore) <> @ExpectedTermRows
 OR (SELECT COUNT_BIG(*) FROM #StatusBefore) <> @ExpectedStatusRows
     THROW 51003, 'Counts differ from user-confirmed snapshot. Review before changing expected counts.', 1;
 IF EXISTS (SELECT 1 FROM #DateBefore WHERE FullDate IS NULL
   OR DateKey<>CONVERT(int,CONVERT(char(8),FullDate,112))
   OR (CalendarMonth IS NOT NULL AND CalendarMonth<>MONTH(FullDate)))
     THROW 51004, 'DateKey/FullDate/CalendarMonth conflict.', 1;
 IF EXISTS (SELECT 1 FROM #TermBefore t LEFT JOIN @Bands b ON b.TermBandCode=t.TermBandCode
            WHERE b.TermBandCode IS NULL)
 OR EXISTS (SELECT TermBandCode FROM #TermBefore GROUP BY TermBandCode HAVING COUNT_BIG(*)>1)
 OR EXISTS (SELECT 1 FROM @Bands b WHERE NOT EXISTS
            (SELECT 1 FROM #TermBefore t WHERE t.TermBandCode=b.TermBandCode))
     THROW 51005, 'Expected exactly the six distinct approved TermBand codes.', 1;
 IF EXISTS (SELECT 1 FROM #TermBefore WHERE
   (TermBandCode='ZERO' AND (MinMonths IS NULL OR MinMonths<>0 OR MaxMonths IS NULL OR MaxMonths<>0)) OR
   (TermBandCode='SHORT' AND (MinMonths IS NULL OR MinMonths<>1 OR MaxMonths IS NULL OR MaxMonths<>60)) OR
   (TermBandCode='MEDIUM' AND (MinMonths IS NULL OR MinMonths<>61 OR MaxMonths IS NULL OR MaxMonths<>119)) OR
   (TermBandCode='TERM_120' AND (MinMonths IS NULL OR MinMonths<>120 OR MaxMonths IS NULL OR MaxMonths<>120)) OR
   (TermBandCode='LONG' AND (MinMonths IS NULL OR MinMonths<>121 OR MaxMonths IS NULL OR MaxMonths<>240)) OR
   (TermBandCode='VERY_LONG' AND (MinMonths IS NULL OR MinMonths<>241 OR MaxMonths IS NOT NULL)))
     THROW 51006, 'Existing range bounds conflict with BR-TERM-01; no bounds are changed by this script.', 1;
 -- Fill gaps only. Existing nonblank conflicting labels/statuses require human review.
 IF EXISTS (SELECT 1 FROM #DateBefore d JOIN @Months m ON m.MonthNumber=MONTH(d.FullDate)
   WHERE NULLIF(LTRIM(RTRIM(d.MonthName)),'') IS NOT NULL
   AND CONVERT(varbinary(100),d.MonthName)<>CONVERT(varbinary(100),m.MonthName))
 OR EXISTS (SELECT 1 FROM #TermBefore t JOIN @Bands b ON b.TermBandCode=t.TermBandCode
   WHERE (NULLIF(LTRIM(RTRIM(t.TermBandName)),'') IS NOT NULL
          AND CONVERT(varbinary(200),t.TermBandName)<>CONVERT(varbinary(200),b.TermBandName))
      OR (t.SortOrder IS NOT NULL AND t.SortOrder<>b.SortOrder)
      OR (NULLIF(LTRIM(RTRIM(t.BandStatus)),'') IS NOT NULL
          AND CONVERT(varbinary(100),t.BandStatus)<>CONVERT(varbinary(100),b.BandStatus)))
     THROW 51007, 'A nonblank attribute conflicts with the approved mapping.', 1;

 SELECT 'BEFORE' AS Phase,COUNT_BIG(*) AS FactRows,SUM(CONVERT(bigint,RecordCount)) AS PublishedRecordCount,
  SUM(GrossApproval) AS GrossApproval,SUM(SBAGuaranteedApproval) AS SBAGuaranteedApproval,
  SUM(GrossChargeOffAmount) AS GrossChargeOffAmount,SUM(CONVERT(bigint,JobsSupported)) AS JobsSupported
 FROM #FactBefore;
 SELECT d.DateKey,d.FullDate,d.MonthName AS OldMonthName,m.MonthName AS ProposedMonthName
 FROM #DateBefore d JOIN @Months m ON m.MonthNumber=MONTH(d.FullDate)
 WHERE NULLIF(LTRIM(RTRIM(d.MonthName)),'') IS NULL ORDER BY d.DateKey;
 SELECT t.TermBandKey,t.TermBandCode,t.TermBandName AS OldName,b.TermBandName AS ProposedName,
  t.SortOrder AS OldSortOrder,b.SortOrder AS ProposedSortOrder,t.BandStatus AS OldBandStatus,b.BandStatus AS ProposedBandStatus
 FROM #TermBefore t JOIN @Bands b ON b.TermBandCode=t.TermBandCode ORDER BY b.SortOrder;
 SELECT RawStatus,CanonicalStatus,StatusMappingStatus,'UNCHANGED - rule pending approval' AS Decision
 FROM #StatusBefore ORDER BY RawStatus;

 IF @Apply = 0
 BEGIN
   ROLLBACK TRANSACTION;
   PRINT 'PREVIEW ONLY. No persistent UPDATE performed. Review output before setting @Apply=1.';
   RETURN;
 END;

 UPDATE d SET MonthName=m.MonthName
 FROM dbo.Dim_Date d JOIN @Months m ON m.MonthNumber=MONTH(d.FullDate)
 WHERE NULLIF(LTRIM(RTRIM(d.MonthName)),'') IS NULL;
 DECLARE @DateUpdated int=@@ROWCOUNT;
 UPDATE t SET
  TermBandName=CASE WHEN NULLIF(LTRIM(RTRIM(t.TermBandName)),'') IS NULL THEN b.TermBandName ELSE t.TermBandName END,
  SortOrder=COALESCE(t.SortOrder,b.SortOrder),
  BandStatus=CASE WHEN NULLIF(LTRIM(RTRIM(t.BandStatus)),'') IS NULL THEN b.BandStatus ELSE t.BandStatus END
 FROM dbo.Dim_TermBand t JOIN @Bands b ON b.TermBandCode=t.TermBandCode
 WHERE NULLIF(LTRIM(RTRIM(t.TermBandName)),'') IS NULL OR t.SortOrder IS NULL
    OR NULLIF(LTRIM(RTRIM(t.BandStatus)),'') IS NULL;
 DECLARE @TermUpdated int=@@ROWCOUNT;

 IF EXISTS (SELECT 1 FROM dbo.Dim_Date d JOIN @Months m ON m.MonthNumber=MONTH(d.FullDate)
   WHERE d.MonthName IS NULL OR CONVERT(varbinary(100),d.MonthName)<>CONVERT(varbinary(100),m.MonthName))
 OR EXISTS (SELECT 1 FROM dbo.Dim_TermBand t JOIN @Bands b ON b.TermBandCode=t.TermBandCode
   WHERE t.TermBandName IS NULL OR t.SortOrder IS NULL OR t.BandStatus IS NULL
      OR CONVERT(varbinary(200),t.TermBandName)<>CONVERT(varbinary(200),b.TermBandName)
      OR t.SortOrder<>b.SortOrder OR CONVERT(varbinary(100),t.BandStatus)<>CONVERT(varbinary(100),b.BandStatus))
     THROW 51008, 'Postcheck failed: expected attributes differ.', 1;
 -- Exact Fact comparison, including LoanKey, eight FKs and binary string values.
 IF (SELECT COUNT_BIG(*) FROM dbo.Fact_Loan)<>(SELECT COUNT_BIG(*) FROM #FactBefore)
 OR EXISTS (
   SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,
    LoanStatusKey,TermBandKey,BusinessKey,GrossApproval,SBAGuaranteedApproval,
    GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,FirstDisbursementDate,
    PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
    SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM #FactBefore
   EXCEPT
   SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,
    LoanStatusKey,TermBandKey,BusinessKey,GrossApproval,SBAGuaranteedApproval,
    GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,FirstDisbursementDate,
    PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
    SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM dbo.Fact_Loan)
 OR EXISTS (
   SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,
    LoanStatusKey,TermBandKey,BusinessKey,GrossApproval,SBAGuaranteedApproval,
    GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,FirstDisbursementDate,
    PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
    SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM dbo.Fact_Loan
   EXCEPT
   SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,
    LoanStatusKey,TermBandKey,BusinessKey,GrossApproval,SBAGuaranteedApproval,
    GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,FirstDisbursementDate,
    PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
    SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM #FactBefore)
     THROW 51009, 'Fact changed: rolling back this transaction.', 1;
 IF EXISTS (SELECT * FROM #StatusBefore EXCEPT SELECT * FROM dbo.Dim_LoanStatus)
 OR EXISTS (SELECT * FROM dbo.Dim_LoanStatus EXCEPT SELECT * FROM #StatusBefore)
     THROW 51010, 'LoanStatus changed unexpectedly.', 1;
 IF (SELECT COUNT_BIG(*) FROM dbo.Dim_Date)<>@ExpectedDateRows
 OR (SELECT COUNT_BIG(*) FROM dbo.Dim_TermBand)<>@ExpectedTermRows
 OR EXISTS (SELECT DateKey,FullDate,CalendarYear,CalendarQuarter,CalendarMonth,FiscalYear,FiscalQuarter,FiscalMonth
     FROM #DateBefore EXCEPT SELECT DateKey,FullDate,CalendarYear,CalendarQuarter,CalendarMonth,FiscalYear,FiscalQuarter,FiscalMonth FROM dbo.Dim_Date)
 OR EXISTS (SELECT TermBandKey,TermBandCode,MinMonths,MaxMonths FROM #TermBefore
     EXCEPT SELECT TermBandKey,TermBandCode,MinMonths,MaxMonths FROM dbo.Dim_TermBand)
     THROW 51011, 'Dimension identity/range/count changed.', 1;
 IF EXISTS (
  SELECT 'Dim_Business' AS DimName,COUNT_BIG(*) AS RowCountAfter FROM dbo.Dim_Business
  UNION ALL SELECT 'Dim_ProjectGeography',COUNT_BIG(*) FROM dbo.Dim_ProjectGeography
  UNION ALL SELECT 'Dim_Industry',COUNT_BIG(*) FROM dbo.Dim_Industry
  UNION ALL SELECT 'Dim_Lender',COUNT_BIG(*) FROM dbo.Dim_Lender
  UNION ALL SELECT 'Dim_LoanProfile',COUNT_BIG(*) FROM dbo.Dim_LoanProfile
  EXCEPT SELECT DimName,RowCountBefore FROM @OtherDimCounts)
     THROW 51012, 'An unrelated Dimension count changed.', 1;

 SELECT 'AFTER' AS Phase,COUNT_BIG(*) AS FactRows,SUM(CONVERT(bigint,RecordCount)) AS PublishedRecordCount,
  SUM(GrossApproval) AS GrossApproval,SUM(SBAGuaranteedApproval) AS SBAGuaranteedApproval,
  SUM(GrossChargeOffAmount) AS GrossChargeOffAmount,SUM(CONVERT(bigint,JobsSupported)) AS JobsSupported
 FROM dbo.Fact_Loan;
 SELECT @DateUpdated AS DateRowsUpdated,@TermUpdated AS TermRowsUpdated;
 SELECT TermBandKey,TermBandCode,TermBandName,MinMonths,MaxMonths,SortOrder,BandStatus
 FROM dbo.Dim_TermBand ORDER BY SortOrder;
 SELECT 'AFTER' AS Phase,SUM(CASE WHEN MonthName IS NULL THEN 1 ELSE 0 END) AS MissingMonthNames FROM dbo.Dim_Date;
 COMMIT TRANSACTION;
 -- Session-local working snapshots only; no warehouse object is dropped.
 DROP TABLE #FactBefore, #DateBefore, #TermBefore, #StatusBefore;
 PRINT 'COMMITTED approved Dimension attributes. Fact exact comparison passed. StatusMappingStatus unchanged.';
END TRY
BEGIN CATCH
 IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
