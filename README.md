# Shift Allowance Validation — ERP Exceptions + Leave Reconciliation

Automates shift allowance validation against SAP ERP data and leave records, ensuring only validated allowances reach payroll — with a full audit trail and approver timestamps.

---

## The problem

Shift allowances are prone to errors when planned rosters, actual exceptions, and leave data sit in separate systems. Manual reconciliation before payroll is slow, error-prone, and hard to audit.

---

## What this workflow does

- Centralises planned shifts (SAP ERP roster / SOW) and actuals in one view
- Reconciles against leave data — PTO, week-off, public holidays
- Detects variances weekly before payroll processing runs
- Maintains a timestamped audit trail with approver sign-off at each stage
- Flags exceptions for HR / payroll team review before any allowance is processed

---

## Workflow stages

1. **Roster input** — planned shifts loaded from SAP ERP
2. **Exception capture** — actual attendance / shift changes recorded
3. **Leave reconciliation** — cross-checked against approved leave (PTO, WO, holidays)
4. **Variance detection** — mismatches flagged for review
5. **Approver sign-off** — timestamped approval before payroll release
6. **Audit log** — complete record retained per pay cycle

---

## Use case

Generic template adaptable to any organisation running shift-based operations on SAP — manufacturing, healthcare, aviation, GCCs with 24/7 delivery models.

---

## Tech

`Python` `SAP ERP` `Leave Management Integration`
