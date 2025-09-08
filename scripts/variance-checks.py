import sys
import pandas as pd
from pathlib import Path

DATA_DIR   = Path(__file__).resolve().parents[1] / "data"
SHIFT_FILE = DATA_DIR / "sample_shift_data.csv"
LEAVE_FILE = DATA_DIR / "sample_leave_data.csv"
OUTPUT     = DATA_DIR / "variance_report.csv"

EXCESS_EXCEPTIONS_PER_MONTH = 8  # tweak as needed

def log(msg: str):
    print(f"[variance] {msg}", flush=True)

def read_csv_safe(path: Path):
    log(f"Reading: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)

def norm_cols(df: pd.DataFrame, mapping):
    # normalize all column names (lowercase, remove spaces/underscores)
    def k(c): return c.lower().replace(" ", "").replace("_", "")
    renamed = {}
    lower = {k(c): c for c in df.columns}
    for want, candidates in mapping.items():
        found = next((lower[cand] for cand in candidates if cand in lower), None)
        if found:
            renamed[found] = want
    df = df.rename(columns=renamed)
    return df

def parse_dates(df: pd.DataFrame, date_col: str):
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df

def ensure_cols(df: pd.DataFrame, cols_defaults: dict):
    for c, default in cols_defaults.items():
        if c not in df.columns:
            df[c] = default
    return df

def load_data():
    # Read
    shift = read_csv_safe(SHIFT_FILE)
    leave = read_csv_safe(LEAVE_FILE)

    # Standardize column names
    shift = norm_cols(shift, {
        "EmployeeID":   ["employeeid","employee_id","empid","emp_id","employee"],
        "Name":         ["name","employee_name","empname"],
        "Date":         ["date","workdate","shiftdate"],
        "PlannedShift": ["plannedshift","planned_shift","shift","rostershift"],
        "ExceptionApproved": ["exceptionapproved","exception_approved","approvedexception","exception"],
        "AllowanceApproved": ["allowanceapproved","allowance_approved","approvedallowance","allowanceok","allowance"],
        "AllowanceType": ["allowancetype","allowance_type","type"]
    })
    leave = norm_cols(leave, {
        "EmployeeID": ["employeeid","employee_id","empid","emp_id","employee"],
        "Date":       ["date","workdate","shiftdate"],
        "LeaveStatus":["leavestatus","leave_status","status","leavetype"]
    })

    # Parse dates
    shift = parse_dates(shift, "Date")
    leave = parse_dates(leave, "Date")

    # Ensure required columns exist
    shift = ensure_cols(shift, {
        "EmployeeID":"", "Name":"", "Date":pd.NaT,
        "PlannedShift":"", "ExceptionApproved":"No",
        "AllowanceApproved":"No", "AllowanceType":""
    })
    leave = ensure_cols(leave, {"LeaveStatus":"Present"})

    # Coerce case/values
    for col in ["ExceptionApproved","AllowanceApproved","PlannedShift","AllowanceType","LeaveStatus"]:
        if col in shift.columns:
            shift[col] = shift[col].astype(str).str.strip()
        if col in leave.columns:
            leave[col] = leave[col].astype(str).str.strip()

    # Merge
    df = shift.merge(leave[["EmployeeID","Date","LeaveStatus"]], on=["EmployeeID","Date"], how="left")
    df["LeaveStatus"] = df["LeaveStatus"].fillna("Present")

    # Final coercions
    df["ExceptionApproved"] = df["ExceptionApproved"].str.lower().map({"yes":"Yes"}).fillna("No")
    df["AllowanceApproved"] = df["AllowanceApproved"].str.lower().map({"yes":"Yes"}).fillna("No")
    df["PlannedShift"]      = df["PlannedShift"].str.title()
    df["AllowanceType"]     = df["AllowanceType"].str.title()
    df["LeaveStatus"]       = df["LeaveStatus"].str.title()  # PTO -> Pto, HOLIDAY -> Holiday

    # Basic sanity logs
    log(f"Rows: shift={len(shift)}, leave={len(leave)}, merged={len(df)}")
    log("Merged head:\n" + df.head(5).to_string())

    return df

def flag_variances(df: pd.DataFrame):
    df["VarianceFlag"] = "OK"
    df["Notes"] = ""

    # 1) Allowance during PTO/Holiday/WO
    mask1 = df["AllowanceApproved"].eq("Yes") & df["LeaveStatus"].isin(["Pto","Holiday","Wo"])
    df.loc[mask1, "VarianceFlag"] = "Flagged"
    df.loc[mask1, "Notes"] += "Allowance claimed on PTO/Holiday/WO; "

    # 2) Allowance without approved exception
    mask2 = df["AllowanceApproved"].eq("Yes") & df["ExceptionApproved"].ne("Yes")
    df.loc[mask2, "VarianceFlag"] = "Flagged"
    df.loc[mask2, "Notes"] += "Allowance without approved exception; "

    # 3) Excessive exceptions per employee per month
    if "Date" in df.columns:
        df["YearMonth"] = df["Date"].dt.to_period("M")
        exc_counts = df[df["ExceptionApproved"].eq("Yes")].groupby(["EmployeeID","YearMonth"]).size()
        for (emp, ym), count in exc_counts.items():
            if count > EXCESS_EXCEPTIONS_PER_MONTH:
                mask3 = (df["EmployeeID"]==emp) & (df["YearMonth"]==ym)
                df.loc[mask3, "VarianceFlag"] = "Flagged"
                df.loc[mask3, "Notes"] += f"Excessive exceptions (> {EXCESS_EXCEPTIONS_PER_MONTH}/month); "

    # Order & output columns
    keep = [
        "EmployeeID","Name","Date","PlannedShift",
        "ExceptionApproved","AllowanceApproved","AllowanceType",
        "LeaveStatus","VarianceFlag","Notes"
    ]
    cols = [c for c in keep if c in df.columns] + [c for c in df.columns if c not in keep]
    return df[cols]

def main():
    try:
        df = load_data()
        out = flag_variances(df)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(OUTPUT, index=False)
        log(f"Wrote {OUTPUT}")
    except Exception as e:
        # Always print a readable error, but also write a minimal report so the artifact step succeeds
        log(f"ERROR: {type(e).__name__}: {e}")
        fallback = pd.DataFrame([{"VarianceFlag":"ERROR","Notes":str(e)}])
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        fallback.to_csv(OUTPUT, index=False)
        log(f"Wrote fallback report to {OUTPUT}")
        # Do NOT crash the job
        # sys.exit(1)

if __name__ == "__main__":
    main()
