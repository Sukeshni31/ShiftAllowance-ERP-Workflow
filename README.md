# Shift Allowance Validation – ERP Exceptions + Leave Reconciliation  

This project documents and automates the **Shift Allowance Validation** workflow with **ERP Exceptions** and **Leave Reconciliation** to ensure only validated allowances reach payroll.

---

## 🎯 Objectives
- Centralize **Planned Shifts** (ERP roster/SOW) and **Exceptions** in ERP  
- Reconcile with **Leave data** (PTO/WO/Holidays)  
- Detect **variances** weekly before payroll processing  
- Maintain **audit trail** and approver timestamps  

---

## 🔄 End-to-End Workflow  

## 🔄 End-to-End Workflow

```mermaid
flowchart LR
  A["Stage 1: Planned Shifts<br/>(ERP Roster / SOW)"] --> B["Stage 2: Exception Requests<br/>(ERP + Approvals)"]
  B --> C["Stage 3: Ops Validation<br/>(Business check)"]
  C --> D["Stage 4: Finance Pre-Check<br/>(ERP export + Variance checks)"]
  D --> E["Stage 5: Ops Monitoring<br/>(Weekly flags resolved)"]
  E --> F["Stage 6: Payroll Processing<br/>(Finance sign-off)"]
