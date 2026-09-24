# Từ điển dữ liệu nguồn SBA 7(a)

Trích định nghĩa từ sheet `7(a) Data Dictionary` của workbook cục bộ. Không dùng sheet 504 cho CSV này. Định nghĩa nguồn giữ tiếng Anh để đối chiếu chính xác; quy tắc chuẩn hóa và measures xem `02_warehouse_design.md`.

| Field | Source definition |
|---|---|
| AsOfDate | Date when the data was recorded (toàn bộ file nguồn có giá trị duy nhất là ngày snapshot 2026-06-30; lưu ở metadata `profile.json`, không làm khóa dimension `AsOfDateKey` trong bảng fact) |
| Program | Indicator of whether loan was approved under SBA's 7(a) or 504 loan program |
| LocationID | SBA's unique lender ID code |
| BorrName | Borrower name |
| BorrStreet | Borrower street address |
| BorrCity | Borrower city |
| BorrState | Borrower state |
| BorrZip | Borrower zip code |
| BankName | Name of the bank that the loan is currently assigned to |
| BankFDICNumber | The Federal Depository Insurance Corporation certificate ID of the lender |
| BankNCUANumber | The National Credit Union Association charter number of the lender |
| BankStreet | Bank street address |
| BankCity | Bank city |
| BankState | Bank state |
| BankZip | Bank zip code |
| GrossApproval | Total loan amount |
| SBAGuaranteedApproval | Amount of SBA's loan guaranty |
| ApprovalDate | Date the loan was approved |
| ApprovalFY | Fiscal year the loan was approved |
| FirstDisbursementDate | Date of first loan disbursement (if available) |
| ProcessingMethod | Specific processing method loan was approved under.  See SOP 50 10 5 for definitions and rules for each processing method.  <br>7(a) Processing Methods:<br>	• 7a General = 7AG<br>	• 7a with EWCP = 7EW<br>	• 7(a) WCP = WCP<br>	• Builders Line of Credit (CAPLine) = SGC<br>	• Community Advantage Initiative = CAI<br>	• Community Advantage International Trade = CAT<br>	• Community Advantage RLOC = CAR<br>	• Community Advantage Recovery Loan = CRL<br>	• Contract Loan Line of Credit (CAPLine) = CTR<br>	• Export Express = EXP<br>	• International Trade Loans = ITR<br>	• MARC 7a General = MAC<br>	• Preferred Lenders Program = PLP<br>	• Preferred Lenders with EWCP = PLW<br>	• Preferred Lenders with WCP = PWC<br>	• SBA Express Program = SBX<br>	• Seasonal Line of Credit (CAPLine) = SLC<br>	• Standard Asset Base Working Capital Line of Credit (CAPLine) = STC |
| InitialInterestRate | Initial interest rate - total interest rate (base rate plus spread) at time loan was approved |
| FixedorVariableInterestInd | Fixed/variable interest rate indicator |
| TermInMonths | Length of loan term |
| NaicsCode | North American Industry Classification System (NAICS) code |
| NaicsDescription | North American Industry Classification System (NAICS) description |
| FranchiseCode | Franchise Code |
| FranchiseName | Franchise Name (if applicable) |
| ProjectCounty | County where project occurs |
| ProjectState | State where project occurs |
| SBADistrictOffice | SBA district office |
| CongressionalDistrict | Congressional district where project occurs |
| BusinessType | Borrower Business Type - Individual, Partnership, or Corporation |
| BusinessAge | Categorical description of the age of the business |
| LoanStatus | Current status of loan:  <br>• CANCLD = Cancelled<br>• CHGOFF = Charged Off<br>• COMMIT = Undisbursed<br>• EXEMPT = The status of loans that have been disbursed but have not been cancelled, paid in full, or charged off are exempt from disclosure under FOIA Exemption 4<br>• PIF = Paid In Full |
| PaidInFullDate | Date loan was paid in full (if applicable) |
| ChargeOffDate | Date SBA charged off loan (if applicable) |
| GrossChargeOffAmount | Total loan balance charged off (includes guaranteed and non-guaranteed portion of loan) |
| RevolverStatus | Indicator of whether a loan is a term loan or revolving line of credit (0=Term, 1=Revolver) |
| JobsSupported | Total Jobs Created + Jobs Retained as reported by lender on SBA Loan Application.  SBA does not review, audit, or validate these numbers - they are simply self-reported, good faith estimates by the lender. |
| CollateralInd | An indicator whether the SBA lender reported that the loan was backed by collateral |
| SoldSecMrktInd | An indicator if the loan was sold on the secondary market. This is a static field once it is sold on the secondary market. Equals 'Y', if sold on the secondary market. Once it is 'Y' it will stay 'Y' for it's entirety.  |
