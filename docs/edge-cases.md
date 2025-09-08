# Edge Case Register  

This file documents all possible edge cases in the Shift Allowance Workflow and how they should be handled.  

| #  | Category                       | Description                        | Example                                 | Handling Approach           |
|----|-------------------------------|------------------------------------|-----------------------------------------|------------------------------|
| 1  | SOW Ambiguity                  | SOW defines hours loosely           | SOW says 9–6 IST but team works 6 PM–3 AM | Use ERP roster as source     |
| 2  | PTO Overlap                    | PTO + Allowance claimed             | Night shift claimed on PTO day           | Auto-flag + Approver review   |
| 3  | Holiday Overlap                | Holiday + Allowance claimed         | Independence Day claim                   | Auto-flag + Ops/Finance review|
| 4  | Emergency Shifts               | Sudden shift change for escalation  | Weekend P1 issue handling                | Exception + Approval required |
| 5  | Cross-Project Allocation       | Worked for different project        | Project A employees for Project B         | Manager approval mandatory    |
| 6  | RM Overrides Without ERP Logs  | Manual approvals via email          | RM emails payroll directly                | Must log in ERP               |
| 7  | System Gaps / Sync Errors       | ERP data missing in exports         | Approved exception missing               | Weekly reconciliation review  |

---

## Principles for Handling Edge Cases

- **No miscommunication penalty**: Employees following instructions must be paid.  
- **Exceptions must be ERP logged**: No allowance should flow to payroll unless captured in ERP.  
- **Real-time detection**: Variances must be flagged before payroll, not after.  
- **Audit trail**: Approvals with timestamps required for compliance.  
