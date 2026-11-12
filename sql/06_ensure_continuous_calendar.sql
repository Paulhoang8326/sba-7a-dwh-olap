-- SSIS Execute SQL Task source, NOT EXECUTED in this change.
-- OLE DB positional parameters 0/1: User::CalendarStartDate / CalendarEndDate,
-- VARCHAR input, size 10. Creates no table and never UPDATEs existing members.
SET NOCOUNT ON;
SET XACT_ABORT ON;
IF DB_NAME()<>N'SBA7A_DWH' THROW 51300,'Connect to SBA7A_DWH.',1;
DECLARE @Start date=CONVERT(date,?,23), @End date=CONVERT(date,?,23);
IF @Start IS NULL OR @End IS NULL OR @End<@Start OR DATEDIFF(day,@Start,@End)>36600
 THROW 51301,'Invalid or excessive calendar bounds.',1;
IF @@TRANCOUNT<>0 THROW 51302,'Calendar task requires no ambient SQL transaction.',1;
BEGIN TRY
 BEGIN TRANSACTION;
 IF EXISTS (SELECT 1 FROM sys.triggers WHERE parent_id=OBJECT_ID('dbo.Dim_Date') AND is_disabled=0)
  THROW 51303,'Review enabled Dim_Date triggers before inserting calendar members.',1;
 IF EXISTS (SELECT 1 FROM dbo.Dim_Date WITH (UPDLOCK,HOLDLOCK)
            WHERE DateKey<>CONVERT(int,CONVERT(char(8),FullDate,112)))
  THROW 51304,'Existing DateKey/FullDate conflict; no existing member is repaired.',1;
 ;WITH Numbers AS (
   SELECT 0 AS n UNION ALL SELECT n+1 FROM Numbers WHERE n<DATEDIFF(day,@Start,@End)
 ), Calendar AS (SELECT DATEADD(day,n,@Start) AS FullDate FROM Numbers)
 INSERT dbo.Dim_Date
  (DateKey,FullDate,CalendarYear,CalendarQuarter,CalendarMonth,MonthName,FiscalYear,FiscalQuarter,FiscalMonth)
 SELECT CONVERT(int,CONVERT(char(8),c.FullDate,112)),c.FullDate,YEAR(c.FullDate),DATEPART(quarter,c.FullDate),MONTH(c.FullDate),
  CASE MONTH(c.FullDate) WHEN 1 THEN 'January' WHEN 2 THEN 'February' WHEN 3 THEN 'March'
   WHEN 4 THEN 'April' WHEN 5 THEN 'May' WHEN 6 THEN 'June' WHEN 7 THEN 'July'
   WHEN 8 THEN 'August' WHEN 9 THEN 'September' WHEN 10 THEN 'October'
   WHEN 11 THEN 'November' WHEN 12 THEN 'December' END,
  YEAR(c.FullDate)+CASE WHEN MONTH(c.FullDate)>=10 THEN 1 ELSE 0 END,
  ((MONTH(c.FullDate)+2)%12)/3+1, (MONTH(c.FullDate)+2)%12+1
 FROM Calendar c
 WHERE NOT EXISTS (SELECT 1 FROM dbo.Dim_Date d WITH (UPDLOCK,HOLDLOCK)
                   WHERE d.DateKey=CONVERT(int,CONVERT(char(8),c.FullDate,112)))
 OPTION (MAXRECURSION 0);
 IF (SELECT COUNT_BIG(*) FROM dbo.Dim_Date WHERE FullDate BETWEEN @Start AND @End)<>DATEDIFF(day,@Start,@End)+1
  THROW 51305,'Calendar coverage postcheck failed.',1;
 COMMIT TRANSACTION;
END TRY
BEGIN CATCH
 IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
