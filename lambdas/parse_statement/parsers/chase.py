import pandas as pd

def parse(df):
    return pd.DataFrame({
        "date": pd.to_datetime(df["Transaction Date"]),
        "description": df["Description"],
        "amount": df["Amount"].astype(float),
        "raw_vendor_name": df["Description"]  # can refine later
    })
