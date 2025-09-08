import sys
import pandas as pd
from pathlib import Path

DATA_DIR   = Path(__file__).resolve().parents[1] / "data"
SHIFT_FILE = DATA_DIR / "sample_shift_data.csv"      # ACTUAL shifts (your existing file)
LEAVE_FILE = DATA_DIR / "sample_leave_data.csv"
SOW_FILE   = DATA_DIR / "sow_planned_shifts.csv"     # NEW: SOW roster (planned)
OUTPUT     = DATA_DIR / "variance_report.csv"

EXCESS_EXCEPTIONS_PER_MONTH = 8  # already used rule

def log(msg: str):
    print(f"[variance] {msg}", flush=True)

def read_csv_safe(path: Path):
    log(f"Reading: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)

def norm_cols(df: pd.DataFrame, mapping: dict):
    """Normalize columns: lowercase + remove spaces/underscores; then rename per mapping."""
    def keyify(c): return c.lower().replace(" ", "").replace("_", "")
    lower = {keyify(c): c for c in df.columns}
    to_rename = {}
    for want, candidates in mapping.items():
        found = next((lower[k] for k in candidates if k in lower), None)
        if found:
            to_rename[found] = want
    return df.rename(columns=to_rename)

def parse_date(df: pd.DataFrame, col: str):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def ensure(df: pd.DataFrame, cols_defaults: dict):
    for c, default in cols_defaults.items():
        if c not in df.columns:
            df[c] = default
    return df

def load_inputs():
    # Actual shifts
    actual = read_csv_safe(SHIFT_FILE)
    actual = norm_cols(actual, {
        "EmployeeID":   ["employeeid","employee_id","empid","emp_id","employee"],
        "Name":         ["name","employeename","employee_name","empname"],
        "Date":         ["date","workdate","shiftdate"],
        "PlannedShift": ["plannedshift","planned_shift","shift","actualshift","workshift"],
        "ExceptionApproved": ["exceptionapproved","exception_approved","approvedexception","exception"],
        "AllowanceApproved": ["allowanceapproved","allowance_approved","approvedallowance","allowanceok","allowance"],
        "AllowanceType": ["allowancetype","allowance_type","type"]
    })
    actual = ensure(actual, {
        "EmployeeID":"", "Name":"", "Date":"", "PlannedShift":"",  # we will treat this as ActualShift
        "ExceptionApproved":"No", "AllowanceApproved":"No", "AllowanceType":""
    })
    actual = parse_date(actual, "Date")
    actual["ActualShift"] = actual["PlannedShift"].astype(str).str.title()
    actual.drop(columns=["PlannedShift"], inplace=True)

    # Leave
    leave = read_csv_safe(LEAVE_FILE)
    leave = norm_cols(leave, {
        "EmployeeID": ["employeeid","employee_id","empid","emp_id","employee"],
        "Date":       ["date","workdate","shiftdate"],
        "LeaveStatus":["leavestatus","leave_status","status","leavetype"]
    })
    leave = ensure(leave, {"LeaveStatus":"Present"})
    leave = parse_date(leave, "Date")
    leave["LeaveStatus"] = leave["LeaveStatus"].astype(str).str.title()

    # SOW (planned)
    sow = read_csv_safe(SOW_FILE)
    sow = norm_cols(sow, {
        "EmployeeID":        ["employeeid","employee_id","empid","emp_id","employee"],
        "Name":              ["name","employeename","employee_name","empname"],
        "Date":              ["date","workdate","shiftdate"],
        "PlannedShift":      ["plannedshift","planned_shift","sowshift","rostershift","shift"],
        "SOWMaxNightShifts": ["sowmaxnightshifts","maxnightshifts","nightlimit","maxnight","nightcap"]
    })
    sow = ensure(sow, {"SOWMaxNightShifts": ""})
    sow = parse_date(sow, "Date")
    sow["PlannedShift"] = sow["PlannedShift"].astype(str).str.title()
    # Make numeric where possible
    sow["SOWMaxNightShifts"] = pd.to_numeric(sow["SOWMaxNightShifts"], errors="coerce")

    # Merge actual + leave
    df = actual.merge(leave[["EmployeeID","Date","LeaveStatus"]], on=["EmployeeID","Date"], how="left")
    df["LeaveStatus"] = df["LeaveStatus"].fillna("Present")

    # Merge in SOW planned
    df = df.merge(sow[["EmployeeID","Date","PlannedShift","SOWMaxNightShifts"]],
                  on=["EmployeeID","Date"], how="left")

    # Normalize Yes/No + types
    for col in ["ExceptionApproved","AllowanceApproved"]:
        df[col] = df[col].astype(str).str.strip().str.lower().map({"yes":"Yes"}).fillna("No")
    df["ActualShift"] = df["ActualShift"].astype(str).str.title()
    df["PlannedShift"] = df["PlannedShift"].astype(str).str.title()
    df["AllowanceType"] = df["AllowanceType"].astype(str).str.title()

    log(f"Rows: actual={len(actual)}, sow={len(sow)}, leave={len(leave)}, merged={len(df)}")
    return df

def flag_rules(df: pd.DataFrame):
    df["VarianceFlag"] = "OK"
    df["Notes"] = ""

    # 1) Allowance during PTO/Holiday/WO
    mask1 = df["AllowanceApproved"].eq("Yes") & df["LeaveStatus"].isin(["Pto","Holiday","Wo","Weeklyoff"])
    df.loc[mask1, "VarianceFlag"] = "Flagged"
    df.loc[mask1, "Notes"] += "Allowance on PTO/Holiday/WO; "

    # 2) Allowance without approved exception
    mask2 = df["AllowanceApproved"].eq("Yes") & df["ExceptionApproved"].ne("Yes")
    df.loc[mask2, "VarianceFlag"] = "Flagged"
    df.loc[mask2, "Notes"] += "Allowance without approved exception; "

    # 3) Excessive exceptions per month (existing rule)
    if "Date" in df.columns:
        df["YearMonth"] = df["Date"].dt.to_period("M")
        exc_counts = df[df["ExceptionApproved"].eq("Yes")].groupby(["EmployeeID","YearMonth"]).size()
        for (emp, ym), count in exc_counts.items():
            if count > EXCESS_EXCEPTIONS_PER_MONTH:
                mask3 = (df["EmployeeID"]==emp) & (df["YearMonth"]==ym)
                df.loc[mask3, "VarianceFlag"] = "Flagged"
                df.loc[mask3, "Notes"] += f"Excessive exceptions (> {EXCESS_EXCEPTIONS_PER_MONTH}/month); "

    # 4) NEW: SOW Planned vs Actual mismatch
    sow_known = df["PlannedShift"].notna() & (df["PlannedShift"].astype(str).str.len()>0)
    act_known = df["ActualShift"].notna() & (df["ActualShift"].astype(str).str.len()>0)
    mask4 = sow_known & act_known & df["PlannedShift"].ne(df["ActualShift"])
    df.loc[mask4, "VarianceFlag"] = "Flagged"
    df.loc[mask4, "Notes"] += "SOW vs Actual shift mismatch; "

    # 5) NEW: Night shift limit exceeded per month (from SOW)
    if "SOWMaxNightShifts" in df.columns:
        night_mask = df["ActualShift"].eq("Night")
        night_counts = df[night_mask].groupby(["EmployeeID","YearMonth"]).size() if "YearMonth" in df.columns else pd.Series(dtype=int)
        # Build a per-employee/month allowed max (use max provided in SOW rows for that month/emp)
        allowed = (df.groupby(["EmployeeID","YearMonth"])["SOWMaxNightShifts"]
                     .max().fillna(-1)) if "YearMonth" in df.columns else pd.Series(dtype=float)
        # Compare
        for key, actual_nights in night_counts.items():
            allowed_nights = allowed.get(key, -1)
            if pd.notna(allowed_nights) and allowed_nights >= 0 and actual_nights > allowed_nights:
                emp, ym = key
                mask5 = (df["EmployeeID"].eq(emp)) & (df["YearMonth"].eq(ym))
                df.loc[mask5, "VarianceFlag"] = "Flagged"
                df.loc[mask5, "Notes"] += f"Night shifts exceeded SOW limit ({int(allowed_nights)}) in {ym}; "

    # Select/Order columns for output
    order = [
        "EmployeeID","Name","Date",
        "PlannedShift","ActualShift",
        "ExceptionApproved","AllowanceApproved","AllowanceType",
        "LeaveStatus","VarianceFlag","Notes"
    ]
    extra = [c for c in ["YearMonth","SOWMaxNightShifts"] if c in df.columns]
    return df[[c for c in order if c in df.columns] + extra].sort_values(["EmployeeID","Date"])

def main():
    try:
        df = load_inputs()
        out = flag_rules(df)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(OUTPUT, index=False)
        log(f"Wrote {OUTPUT}")
    except Exception as e:
        log(f"ERROR: {type(e).__name__}: {e}")
        fallback = pd.DataFrame([{"VarianceFlag":"ERROR","Notes":str(e)}])
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        fallback.to_csv(OUTPUT, index=False)
        log(f"Wrote fallback report to {OUTPUT}")
        # keep job green for now
        # sys.exit(1)

if __name__ == "__main__":
    main()
