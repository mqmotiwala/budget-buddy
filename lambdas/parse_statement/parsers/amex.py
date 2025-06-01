import pandas as pd

def parse(df):
    return pd.DataFrame({
        "date": pd.to_datetime(df["Date"]),
        "description": df["Details"],
        "amount": df["Amount"].astype(float),
        "raw_vendor_name": df["Details"]
    })
