-- SQL Server 2019+; execute in SSMS or sqlcmd. Creates objects only in a NEW database.
USE master;
GO
IF DB_ID(N'SBA7aDWH') IS NULL CREATE DATABASE SBA7aDWH;
GO
USE SBA7aDWH;
GO
CREATE SCHEMA dwh;
GO
CREATE SCHEMA staging;
GO
CREATE SCHEMA marts;
GO
CREATE TABLE dwh.DimDate (
 DateKey int PRIMARY KEY, FullDate date NOT NULL UNIQUE,
 CalendarYear int NOT NULL, CalendarQuarter int NOT NULL, MonthNumber int NOT NULL,
 YearMonth nvarchar(7) NOT NULL, FiscalYear int NOT NULL, FiscalQuarter int NOT NULL
);
CREATE TABLE dwh.DimState (StateKey int PRIMARY KEY, StateCode nvarchar(30) NOT NULL UNIQUE);
CREATE TABLE dwh.DimCounty (
 CountyKey int PRIMARY KEY, StateKey int NOT NULL REFERENCES dwh.DimState,
 ProjectCounty nvarchar(150) NOT NULL, UNIQUE(StateKey,ProjectCounty)
);
CREATE TABLE dwh.DimSector (SectorKey int PRIMARY KEY, SectorCode nvarchar(30) NOT NULL UNIQUE);
CREATE TABLE dwh.DimIndustry (
 IndustryKey int PRIMARY KEY, SectorKey int NOT NULL REFERENCES dwh.DimSector,
 NaicsCode nvarchar(30) NOT NULL, NaicsDescription nvarchar(300) NOT NULL
);
CREATE TABLE dwh.DimLender (
 LenderKey int PRIMARY KEY, LocationID nvarchar(30) NOT NULL, BankName nvarchar(300) NOT NULL,
 BankFDICNumber nvarchar(30) NOT NULL, BankNCUANumber nvarchar(30) NOT NULL,
 BankCity nvarchar(150) NOT NULL, BankState nvarchar(30) NOT NULL, BankZip nvarchar(30) NOT NULL
);
CREATE TABLE dwh.DimBusiness (
 BusinessKey int PRIMARY KEY, BusinessType nvarchar(100) NOT NULL, BusinessAge nvarchar(150) NOT NULL,
 FranchiseCode nvarchar(30) NOT NULL, FranchiseName nvarchar(300) NOT NULL
);
CREATE TABLE dwh.DimLoanProfile (
 LoanProfileKey int PRIMARY KEY, Program nvarchar(30) NOT NULL, ProcessingMethod nvarchar(150) NOT NULL,
 FixedorVariableInterestInd nvarchar(30) NOT NULL, RevolverStatus nvarchar(30) NOT NULL,
 CollateralInd nvarchar(30) NOT NULL, SoldSecMrktInd nvarchar(30) NOT NULL, LoanStatus nvarchar(30) NOT NULL
);
CREATE TABLE dwh.FactLoanSnapshot (
 LoanRowKey int PRIMARY KEY, SourceRowNumber int NOT NULL UNIQUE,
 CountyKey int NOT NULL REFERENCES dwh.DimCounty,
 IndustryKey int NOT NULL REFERENCES dwh.DimIndustry,
 LenderKey int NOT NULL REFERENCES dwh.DimLender,
 BusinessKey int NOT NULL REFERENCES dwh.DimBusiness,
 LoanProfileKey int NOT NULL REFERENCES dwh.DimLoanProfile,
 ApprovalDateKey int NOT NULL REFERENCES dwh.DimDate,
 FirstDisbursementDateKey int NULL REFERENCES dwh.DimDate,
 PaidInFullDateKey int NULL REFERENCES dwh.DimDate,
 ChargeOffDateKey int NULL REFERENCES dwh.DimDate,
 GrossApproval decimal(24,6) NOT NULL,
 SBAGuaranteedApproval decimal(24,6) NOT NULL,
 GrossChargeOffAmount decimal(24,6) NOT NULL,
 JobsSupported decimal(24,6) NOT NULL,
 InitialInterestRate decimal(12,6) NULL,
 TermInMonths decimal(10,2) NOT NULL,
 LoanCount int NOT NULL CHECK(LoanCount=1),
 ChargeOffCount int NOT NULL, ResolvedCount int NOT NULL, NonCancelledCount int NOT NULL,
 NonCancelledApproval decimal(24,6) NOT NULL,
 UnguaranteedApproval decimal(24,6) NOT NULL,
 InterestWeightedAmount decimal(24,6) NOT NULL,
 InterestKnownApproval decimal(24,6) NOT NULL,
 TermTotal decimal(24,6) NOT NULL,
 DisbursementDaysTotal int NOT NULL, DisbursementObservedCount int NOT NULL
);
GO
CREATE INDEX IX_Fact_Approval ON dwh.FactLoanSnapshot(ApprovalDateKey) INCLUDE(GrossApproval,LoanCount);
GO
CREATE VIEW marts.vLoan AS
SELECT f.*, dt.FullDate AS ApprovalDate, dt.FiscalYear, dt.CalendarYear, dt.CalendarQuarter,
 dt.YearMonth, dt.MonthNumber, s.StateCode, c.ProjectCounty, se.SectorCode,
 i.NaicsCode, i.NaicsDescription, l.BankName, l.LocationID,
 b.BusinessType,b.BusinessAge, p.ProcessingMethod,p.LoanStatus,p.FixedorVariableInterestInd,p.CollateralInd
FROM dwh.FactLoanSnapshot f
JOIN dwh.DimDate dt ON dt.DateKey=f.ApprovalDateKey
JOIN dwh.DimCounty c ON c.CountyKey=f.CountyKey
JOIN dwh.DimState s ON s.StateKey=c.StateKey
JOIN dwh.DimIndustry i ON i.IndustryKey=f.IndustryKey
JOIN dwh.DimSector se ON se.SectorKey=i.SectorKey
JOIN dwh.DimLender l ON l.LenderKey=f.LenderKey
JOIN dwh.DimBusiness b ON b.BusinessKey=f.BusinessKey
JOIN dwh.DimLoanProfile p ON p.LoanProfileKey=f.LoanProfileKey;
GO
