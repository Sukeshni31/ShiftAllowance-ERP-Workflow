# Requirements & Data Inputs

## Data Inputs Required
- **ERP Roster**: Planned Shifts (EmployeeID, Date, ShiftType)
- **Exception Requests**: ERP Approved (EmployeeID, Date, ExceptionType, Approver)
- **Leave Data**: PTO/Holiday/WOs (EmployeeID, Date, LeaveType)
- **Allowance Data**: Allowance claims (EmployeeID, Date, AllowanceType, ApprovedBy)

## Output Data
- **Variance Report**: EmployeeID, Date, Shift, Exception Status, Leave Status, Allowance Status, Variance Flag

## Tools Used
- Python for automation (pandas library)
- GitHub Actions for scheduling & reporting
- ERP API (optional future integration)

## Automation Goals
- Auto-flag allowance during PTO/Holiday
- Auto-flag allowance without approved exception
- Weekly variance check report for Ops & Finance review
