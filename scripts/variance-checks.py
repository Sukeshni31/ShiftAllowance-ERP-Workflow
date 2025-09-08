import pandas as pd
from pathlib import Path

# ------------------------
# CONFIGURATION
# ------------------------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SHIFT_FILE = DATA_DIR / "sample_shift_data.csv"
LEAVE_FILE = DATA_DIR / "sample_leave_data.csv"
OUTPUT_FILE = DATA_DIR / "variance_report.csv"

EXCESS_EXCEPTIONS_PER_MONTH = 8  # policy threshold

# ------------------------
# LOAD DATA
# ------------------------
def load_data():
    try:
        shift_df = pd.read_csv(SHIFT_FILE, parse_dates=["Date"])
        leave_df = pd.read_csv(LEAVE_FILE, parse_dates=["Date"])
        return shift_df, leave_df
    except FileNotFoundError:
        print("Error: Sample data files not found. Please check the data folder.")
        return None, None

# ------------------------
# JOIN DATA
# ------------------------
def join_data(shift_df, leave_df):
    df = shift_df.merge(leave_df, on=["EmployeeID", "Date"], how="left")
    df["LeaveStatus"] = df["LeaveStatus"].fillna("Present")
    return df

# ------------------------
# FLAG VARIANCES
# ------------------------
def flag_variances(df):
    df["VarianceFlag"] = "OK"
    df["Notes"] = ""

    # 1. Allowance claimed while on PTO/Holiday
    mask1 = df["AllowanceApproved"].eq("Yes") & df["LeaveStatus"].isin(["PTO", "Holiday"])
    df.loc[mask1, "VarianceFlag"] = "Flagged"
    df.loc[mask1, "Notes"] += "Allowance claimed on PTO/Holiday; "

    # 2. Allowance claimed without approved exception
    mask2 = df["AllowanceApproved"].eq("Yes") & df["ExceptionApproved"].ne("Yes")
    df.loc[mask2, "VarianceFlag"] = "Flagged"
    df.loc[mask2, "Notes"] += "Allowance without approved exception; "

    # 3. Excessive exceptions per employee per month
    df["YearMonth"] = df["Date"].dt.to_period("M")
    counts = df[df["ExceptionApproved"] == "Yes"].groupby(["EmployeeID", "YearMonth"]).size()
    for (emp, ym), count in counts.items():
        if count > EXCESS_EXCEPTIONS_PER_MONTH:
            mask3 = (df["EmployeeID"] == emp) & (df["YearMonth"] == ym)
            df.loc[mask3, "VarianceFlag"] = "Flagged"
            df.loc[mask3, "Notes"] += f"Excessive exceptions (> {EXCESS_EXCEPTIONS_PER_MONTH}); "

    return df

# ------------------------
# SAVE OUTPUT
# ------------------------
def save_output(df):
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Variance report generated: {OUTPUT_FILE}")

# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":
    shift_df, leave_df = load_data()
    if shift_df is not None and leave_df is not None:
        combined_df = join_data(shift_df, leave_df)
        result_df = flag_variances(combined_df)
        save_output(result_df)
