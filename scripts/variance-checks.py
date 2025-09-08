import pandas as pd
from pathlib import Path

# ------------------------
# CONFIG
# ------------------------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SHIFT_FILE = DATA_DIR / "sample_shift_data.csv"
LEAVE_FILE = DATA_DIR / "sample_leave_data.csv"
OUTPUT_FILE = DATA_DIR / "variance_report.csv"
EXCESS_EXCEPTIONS_PER_MONTH = 8  # policy threshold

def load_data():
    shift_df = pd.read_csv(SHIFT_FILE, parse_dates=["Date"])
    leave_df = pd.read_csv(LEAVE_FILE, parse_dates=["Date"])
    return shift_df, leave_df

def join_data(shift_df, leave_df):
    df = shift_df.merge(leave_df, on=["EmployeeID", "Date"], how="left")
    df["LeaveStatus"] = df["LeaveStatus"].fillna("Present")
    # normalize text
    for col in ["ExceptionApproved", "AllowanceApproved", "PlannedShift", "AllowanceType"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
    return df

def flag_variances(df):
    df["VarianceFlag"] = "OK"
    df["Notes"] = ""

    # 1) Allowance during PTO/Holiday/WO
    mask1 = df["AllowanceApproved"].eq("Yes") & df["LeaveStatus"].isin(["Pto", "Holiday", "Wo"])
    df.loc[mask1, "VarianceFlag"] = "Flagged"
    df.loc[mask1, "Notes"] += "Allowance claimed on PTO/Holiday/WO; "

    # 2) Allowance without approved exception (e.g., Night allowance but no exception)
    mask2 = df["AllowanceApproved"].eq("Yes") & df["ExceptionApproved"].ne("Yes")
    df.loc[mask2, "VarianceFlag"] = "Flagged"
    df.loc[mask2, "Notes"] += "Allowance without approved exception; "

    # 3) Excessive exceptions per employee per month
    df["YearMonth"] = df["Date"].dt.to_period("M")
    exc_counts = df[df["ExceptionApproved"].eq("Yes")].groupby(
        ["EmployeeID", "YearMonth"]
    ).size()
    for (emp, ym), count in exc_counts.items():
        if count > EXCESS_EXCEPTIONS_PER_MONTH:
            mask3 = (df["EmployeeID"] == emp) & (df["YearMonth"] == ym)
            df.loc[mask3, "VarianceFlag"] = "Flagged"
            df.loc[mask3, "Notes"] += f"Excessive exceptions (> {EXCESS_EXCEPTIONS_PER_MONTH}/month); "

    return df

def save_output(df):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Wrote {OUTPUT_FILE}")

if __name__ == "__main__":
    shift_df, leave_df = load_data()
    combined = join_data(shift_df, leave_df)
    flagged = flag_variances(combined)
    save_output(flagged)
