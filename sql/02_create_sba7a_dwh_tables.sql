-- SBA 7(a): create the current 1 Fact + 8 Dimensions schema.
-- Source: diagram/candidate_schema.dbml; connect to SBA7A_DWH via OLE DB.
-- Execute SQL Task: Direct input, ResultSet=None, BypassPrepare=True.
-- Existing tables are skipped, not validated or modified.
-- No seed data or ETL is performed. DateKey is supplied by ETL.
SET NOCOUNT ON;

IF DB_NAME() <> N'SBA7A_DWH'
BEGIN
    THROW 50001, 'Connect to SBA7A_DWH before creating warehouse tables.', 1;
END;

-- Dimension: Dim_Date
IF OBJECT_ID(N'dbo.Dim_Date', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_Date]
    (
        [DateKey] INT NOT NULL,
        [FullDate] DATE NOT NULL,
        [CalendarYear] SMALLINT NULL,
        [CalendarQuarter] TINYINT NULL,
        [CalendarMonth] TINYINT NULL,
        [MonthName] VARCHAR(20) NULL,
        [FiscalYear] SMALLINT NOT NULL,
        [FiscalQuarter] TINYINT NOT NULL,
        [FiscalMonth] TINYINT NULL,
        CONSTRAINT [PK_Dim_Date] PRIMARY KEY ([DateKey])
    );
END;

-- Dimension: Dim_ProjectGeography
IF OBJECT_ID(N'dbo.Dim_ProjectGeography', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_ProjectGeography]
    (
        [GeographyKey] BIGINT IDENTITY(1,1) NOT NULL,
        [ProjectState] VARCHAR(10) NULL,
        [ProjectCounty] VARCHAR(150) NULL,
        [CongressionalDistrict] VARCHAR(50) NULL,
        [SBADistrictOffice] VARCHAR(200) NULL,
        [GeographyValueStatus] VARCHAR(30) NULL,
        CONSTRAINT [PK_Dim_ProjectGeography] PRIMARY KEY ([GeographyKey])
    );
END;

-- Dimension: Dim_Industry
IF OBJECT_ID(N'dbo.Dim_Industry', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_Industry]
    (
        [IndustryKey] BIGINT IDENTITY(1,1) NOT NULL,
        [NaicsCode] VARCHAR(20) NULL,
        [NaicsDescription] VARCHAR(300) NULL,
        [NaicsSectorCode] VARCHAR(20) NULL,
        [NaicsSectorName] VARCHAR(200) NULL,
        [NaicsVersion] VARCHAR(30) NULL,
        [SectorMappingStatus] VARCHAR(30) NULL,
        CONSTRAINT [PK_Dim_Industry] PRIMARY KEY ([IndustryKey])
    );
END;

-- Dimension: Dim_Lender
IF OBJECT_ID(N'dbo.Dim_Lender', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_Lender]
    (
        [LenderKey] BIGINT IDENTITY(1,1) NOT NULL,
        [LocationID] VARCHAR(50) NOT NULL,
        [BankName] VARCHAR(300) NULL,
        [BankFDICNumber] VARCHAR(50) NULL,
        [BankNCUANumber] VARCHAR(50) NULL,
        [BankStreet] VARCHAR(300) NULL,
        [BankCity] VARCHAR(150) NULL,
        [BankState] VARCHAR(20) NULL,
        [BankZip] VARCHAR(20) NULL,
        [LenderValueStatus] VARCHAR(30) NULL,
        CONSTRAINT [PK_Dim_Lender] PRIMARY KEY ([LenderKey])
    );
END;

-- Dimension: Dim_LoanProfile
IF OBJECT_ID(N'dbo.Dim_LoanProfile', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_LoanProfile]
    (
        [LoanProfileKey] BIGINT IDENTITY(1,1) NOT NULL,
        [ProcessingMethod] VARCHAR(150) NULL,
        [FixedOrVariableInterestInd] VARCHAR(50) NULL,
        [RevolverStatus] VARCHAR(50) NULL,
        [CollateralInd] VARCHAR(50) NULL,
        [LoanProfileValueStatus] VARCHAR(30) NULL,
        CONSTRAINT [PK_Dim_LoanProfile] PRIMARY KEY ([LoanProfileKey])
    );
END;

-- Dimension: Dim_LoanStatus
IF OBJECT_ID(N'dbo.Dim_LoanStatus', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_LoanStatus]
    (
        [LoanStatusKey] BIGINT IDENTITY(1,1) NOT NULL,
        [RawStatus] VARCHAR(50) NOT NULL,
        [CanonicalStatus] VARCHAR(50) NULL,
        [StatusMappingStatus] VARCHAR(30) NULL,
        CONSTRAINT [PK_Dim_LoanStatus] PRIMARY KEY ([LoanStatusKey])
    );
END;

-- Dimension: Dim_TermBand
IF OBJECT_ID(N'dbo.Dim_TermBand', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_TermBand]
    (
        [TermBandKey] BIGINT IDENTITY(1,1) NOT NULL,
        [TermBandCode] VARCHAR(30) NOT NULL,
        [TermBandName] VARCHAR(100) NULL,
        [MinMonths] INT NULL,
        [MaxMonths] INT NULL,
        [SortOrder] INT NULL,
        [BandStatus] VARCHAR(30) NULL,
        CONSTRAINT [PK_Dim_TermBand] PRIMARY KEY ([TermBandKey])
    );
END;

-- Dimension: Dim_Business
IF OBJECT_ID(N'dbo.Dim_Business', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Dim_Business]
    (
        [BusinessKey] BIGINT IDENTITY(1,1) NOT NULL,
        [BusinessTypeRaw] VARCHAR(150) NULL,
        [BusinessAgeRaw] VARCHAR(150) NULL,
        [BusinessTypeValueStatus] VARCHAR(30) NULL,
        [BusinessAgeValueStatus] VARCHAR(30) NULL,
        CONSTRAINT [PK_Dim_Business] PRIMARY KEY ([BusinessKey])
    );
END;

-- Fact: Fact_Loan
IF OBJECT_ID(N'dbo.Fact_Loan', N'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Fact_Loan]
    (
        [LoanKey] BIGINT IDENTITY(1,1) NOT NULL,
        [ApprovalDateKey] INT NOT NULL,
        [GeographyKey] BIGINT NOT NULL,
        [IndustryKey] BIGINT NOT NULL,
        [LenderKey] BIGINT NOT NULL,
        [LoanProfileKey] BIGINT NOT NULL,
        [LoanStatusKey] BIGINT NOT NULL,
        [TermBandKey] BIGINT NOT NULL,
        [BusinessKey] BIGINT NOT NULL,
        [GrossApproval] DECIMAL(18,3) NULL,
        [SBAGuaranteedApproval] DECIMAL(18,3) NULL,
        [GrossChargeOffAmount] DECIMAL(18,3) NULL,
        [JobsSupported] INT NULL,
        [RecordCount] INT NOT NULL CONSTRAINT [DF_Fact_Loan_RecordCount] DEFAULT (1),
        [TermInMonths] INT NULL,
        [FirstDisbursementDate] DATE NULL,
        [PaidInFullDate] DATE NULL,
        [ChargeOffDate] DATE NULL,
        [SourceFileID] VARCHAR(100) NOT NULL,
        [SourceRecordOrdinal] BIGINT NOT NULL,
        [SourceRowNumber] BIGINT NULL,
        [ETLBatchID] VARCHAR(100) NULL,
        CONSTRAINT [PK_Fact_Loan] PRIMARY KEY ([LoanKey]),
        CONSTRAINT [UQ_Fact_Loan_SourceRecord] UNIQUE ([SourceFileID], [SourceRecordOrdinal]),
        CONSTRAINT [FK_Fact_Loan_ApprovalDateKey] FOREIGN KEY ([ApprovalDateKey])
            REFERENCES [dbo].[Dim_Date] ([DateKey]),
        CONSTRAINT [FK_Fact_Loan_GeographyKey] FOREIGN KEY ([GeographyKey])
            REFERENCES [dbo].[Dim_ProjectGeography] ([GeographyKey]),
        CONSTRAINT [FK_Fact_Loan_IndustryKey] FOREIGN KEY ([IndustryKey])
            REFERENCES [dbo].[Dim_Industry] ([IndustryKey]),
        CONSTRAINT [FK_Fact_Loan_LenderKey] FOREIGN KEY ([LenderKey])
            REFERENCES [dbo].[Dim_Lender] ([LenderKey]),
        CONSTRAINT [FK_Fact_Loan_LoanProfileKey] FOREIGN KEY ([LoanProfileKey])
            REFERENCES [dbo].[Dim_LoanProfile] ([LoanProfileKey]),
        CONSTRAINT [FK_Fact_Loan_LoanStatusKey] FOREIGN KEY ([LoanStatusKey])
            REFERENCES [dbo].[Dim_LoanStatus] ([LoanStatusKey]),
        CONSTRAINT [FK_Fact_Loan_TermBandKey] FOREIGN KEY ([TermBandKey])
            REFERENCES [dbo].[Dim_TermBand] ([TermBandKey]),
        CONSTRAINT [FK_Fact_Loan_BusinessKey] FOREIGN KEY ([BusinessKey])
            REFERENCES [dbo].[Dim_Business] ([BusinessKey])
    );
END;
