-- PREPARED ONLY. NOT EXECUTED. Approved BR-STATUS-01 classification, 2026-10-28.
-- Default preview. Only UPDATEs NULL/blank StatusMappingStatus for five exact pairs.
-- No raw/canonical/key changes, no Fact DML, no seed for missing/unsupported statuses.
-- Execute as one batch, outside any existing transaction; allow tempdb/maintenance time.
SET NOCOUNT ON;
SET XACT_ABORT ON;
DECLARE @Apply bit=0, @ExpectedStatusRows bigint=5;
IF DB_NAME()<>N'SBA7A_DWH' THROW 51200,'Connect to SBA7A_DWH.',1;
IF @@TRANCOUNT<>0 THROW 51201,'Run outside an existing transaction.',1;
DECLARE @Mapping TABLE (RawStatus varchar(50) PRIMARY KEY,CanonicalStatus varchar(50),MappingStatus varchar(30));
INSERT @Mapping VALUES ('CANCLD','CANCLD','DIRECT_MAPPING'),('CHGOFF','CHGOFF','DIRECT_MAPPING'),
 ('COMMIT','COMMIT','DIRECT_MAPPING'),('EXEMPT','EXEMPT','DIRECT_MAPPING'),('P I F','PIF','NORMALIZED');
BEGIN TRY
 BEGIN TRANSACTION;
 IF EXISTS (SELECT 1 FROM sys.triggers WHERE parent_id=OBJECT_ID('dbo.Dim_LoanStatus') AND is_disabled=0)
  THROW 51202,'Review enabled LoanStatus triggers before any update.',1;
 IF (SELECT COUNT(*) FROM sys.columns WHERE object_id=OBJECT_ID('dbo.Fact_Loan'))<>22
  THROW 51203,'Fact contract differs from the audited 22 columns.',1;
 SELECT * INTO #StatusBefore FROM dbo.Dim_LoanStatus WITH (TABLOCK,HOLDLOCK);
 SELECT * INTO #FactBefore FROM dbo.Fact_Loan WITH (TABLOCK,HOLDLOCK);
 SELECT s.LoanStatusKey,s.RawStatus,s.CanonicalStatus,s.StatusMappingStatus AS OldMappingStatus,
  CASE WHEN NULLIF(LTRIM(RTRIM(s.RawStatus)),'') IS NULL THEN 'MISSING'
       WHEN m.RawStatus IS NOT NULL THEN m.MappingStatus ELSE 'UNMAPPED' END AS ProposedMappingStatus,
  CASE WHEN NULLIF(LTRIM(RTRIM(s.RawStatus)),'') IS NULL THEN 'MISSING_RAW_STATUS'
       WHEN NOT EXISTS (SELECT 1 FROM @Mapping rawmap WHERE CONVERT(varbinary(100),rawmap.RawStatus)=CONVERT(varbinary(100),s.RawStatus))
         THEN 'RAW_STATUS_NOT_IN_WHITELIST'
       WHEN m.RawStatus IS NULL THEN 'CANONICAL_STATUS_MISMATCH' END AS ExceptionReason
 INTO #Proposal FROM #StatusBefore s
 LEFT JOIN @Mapping m ON CONVERT(varbinary(100),m.RawStatus)=CONVERT(varbinary(100),s.RawStatus)
                    AND CONVERT(varbinary(100),m.CanonicalStatus)=CONVERT(varbinary(100),s.CanonicalStatus);
 SELECT 'BEFORE' AS Phase,* FROM #Proposal ORDER BY LoanStatusKey;
 SELECT ProposedMappingStatus,COUNT_BIG(*) AS Members FROM #Proposal GROUP BY ProposedMappingStatus;
 SELECT COUNT_BIG(*) AS FactRows,SUM(CONVERT(bigint,RecordCount)) AS PublishedRecordCount,
  SUM(GrossApproval) AS GrossApproval,SUM(SBAGuaranteedApproval) AS SBAGuaranteedApproval,
  SUM(GrossChargeOffAmount) AS GrossChargeOffAmount,SUM(CONVERT(bigint,JobsSupported)) AS JobsSupported FROM #FactBefore;
 IF @Apply=0
 BEGIN
  ROLLBACK TRANSACTION;
  PRINT 'PREVIEW ONLY. Save exception result rows; no persistent UPDATE performed.';
  RETURN;
 END;
 IF (SELECT COUNT_BIG(*) FROM #StatusBefore)<>@ExpectedStatusRows
 OR EXISTS (SELECT 1 FROM #Proposal WHERE ExceptionReason IS NOT NULL)
 OR EXISTS (SELECT RawStatus FROM #StatusBefore GROUP BY RawStatus HAVING COUNT_BIG(*)>1)
 OR EXISTS (SELECT 1 FROM @Mapping m WHERE NOT EXISTS (SELECT 1 FROM #StatusBefore s
       WHERE CONVERT(varbinary(100),s.RawStatus)=CONVERT(varbinary(100),m.RawStatus)
         AND CONVERT(varbinary(100),s.CanonicalStatus)=CONVERT(varbinary(100),m.CanonicalStatus)))
  THROW 51204,'Expected exactly five approved pairs, without exceptions or duplicate raw keys. No automatic mapping.',1;
 IF EXISTS (SELECT 1 FROM #Proposal WHERE NULLIF(LTRIM(RTRIM(OldMappingStatus)),'') IS NOT NULL
             AND CONVERT(varbinary(100),OldMappingStatus)<>CONVERT(varbinary(100),ProposedMappingStatus))
  THROW 51205,'Existing nonblank mapping classification conflicts; review instead of overwriting.',1;
 UPDATE s SET StatusMappingStatus=p.ProposedMappingStatus
 FROM dbo.Dim_LoanStatus s JOIN #Proposal p ON p.LoanStatusKey=s.LoanStatusKey
 WHERE NULLIF(LTRIM(RTRIM(s.StatusMappingStatus)),'') IS NULL;
 DECLARE @Updated int=@@ROWCOUNT;
 IF EXISTS (SELECT 1 FROM dbo.Dim_LoanStatus s JOIN #Proposal p ON p.LoanStatusKey=s.LoanStatusKey
   WHERE s.StatusMappingStatus IS NULL
      OR CONVERT(varbinary(100),s.StatusMappingStatus)<>CONVERT(varbinary(100),p.ProposedMappingStatus))
  THROW 51206,'Classification postcheck failed.',1;
 IF (SELECT COUNT_BIG(*) FROM dbo.Dim_LoanStatus)<>@ExpectedStatusRows
 OR EXISTS (SELECT LoanStatusKey,CONVERT(varbinary(100),RawStatus),CONVERT(varbinary(100),CanonicalStatus)
   FROM #StatusBefore EXCEPT SELECT LoanStatusKey,CONVERT(varbinary(100),RawStatus),CONVERT(varbinary(100),CanonicalStatus) FROM dbo.Dim_LoanStatus)
 OR EXISTS (SELECT LoanStatusKey,CONVERT(varbinary(100),RawStatus),CONVERT(varbinary(100),CanonicalStatus)
   FROM dbo.Dim_LoanStatus EXCEPT SELECT LoanStatusKey,CONVERT(varbinary(100),RawStatus),CONVERT(varbinary(100),CanonicalStatus) FROM #StatusBefore)
  THROW 51207,'Raw/canonical/key/count changed unexpectedly.',1;
 IF (SELECT COUNT_BIG(*) FROM dbo.Fact_Loan)<>(SELECT COUNT_BIG(*) FROM #FactBefore)
 OR EXISTS (
  SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,LoanStatusKey,TermBandKey,BusinessKey,
   GrossApproval,SBAGuaranteedApproval,GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,
   FirstDisbursementDate,PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
   SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM #FactBefore
  EXCEPT
  SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,LoanStatusKey,TermBandKey,BusinessKey,
   GrossApproval,SBAGuaranteedApproval,GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,
   FirstDisbursementDate,PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
   SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM dbo.Fact_Loan)
 OR EXISTS (
  SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,LoanStatusKey,TermBandKey,BusinessKey,
   GrossApproval,SBAGuaranteedApproval,GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,
   FirstDisbursementDate,PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
   SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM dbo.Fact_Loan
  EXCEPT
  SELECT LoanKey,ApprovalDateKey,GeographyKey,IndustryKey,LenderKey,LoanProfileKey,LoanStatusKey,TermBandKey,BusinessKey,
   GrossApproval,SBAGuaranteedApproval,GrossChargeOffAmount,JobsSupported,RecordCount,TermInMonths,
   FirstDisbursementDate,PaidInFullDate,ChargeOffDate,CONVERT(varbinary(8000),SourceFileID),SourceRecordOrdinal,
   SourceRowNumber,CONVERT(varbinary(8000),ETLBatchID) FROM #FactBefore)
  THROW 51208,'Fact exact comparison failed; rolling back.',1;
 SELECT 'AFTER' AS Phase,LoanStatusKey,RawStatus,CanonicalStatus,StatusMappingStatus FROM dbo.Dim_LoanStatus ORDER BY LoanStatusKey;
 SELECT @Updated AS RowsUpdated,COUNT_BIG(*) AS FactRows,SUM(CONVERT(bigint,RecordCount)) AS PublishedRecordCount,
  SUM(GrossApproval) AS GrossApproval,SUM(SBAGuaranteedApproval) AS SBAGuaranteedApproval,
  SUM(GrossChargeOffAmount) AS GrossChargeOffAmount,SUM(CONVERT(bigint,JobsSupported)) AS JobsSupported FROM dbo.Fact_Loan;
 COMMIT TRANSACTION;
 DROP TABLE #StatusBefore,#FactBefore,#Proposal; -- local working snapshots only
 PRINT 'COMMITTED approved technical classifications only; RawStatus/CanonicalStatus/keys/Fact comparison passed.';
END TRY
BEGIN CATCH
 IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
