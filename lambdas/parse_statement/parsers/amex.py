import pandas as pd

def parse(df):
    return pd.DataFrame({
        "transaction_date": pd.to_datetime(df["transaction_date"]),
        "description": df["description"],
        "amount": df["amount"].astype(float) * -1
    })