import pandas as pd

def parse(df, issuer_config):
    DATE_COLUMN = issuer_config["DATE_COLUMN"]
    DESCRIPTION_COLUMN = issuer_config["DESCRIPTION_COLUMN"]
    AMOUNT_COLUMN = issuer_config["AMOUNT_COLUMN"]
    EXPENSES_SIGN = issuer_config["EXPENSES_SIGN"]

    parsed_dates = pd.to_datetime(df[DATE_COLUMN], errors='coerce', infer_datetime_format=True)
    num_invalid = parsed_dates.isna().sum()

    if num_invalid > 0:
        print(f"{num_invalid} rows had invalid dates and were set to NaT.")

    return pd.DataFrame({
        "transaction_date": parsed_dates,
        "description": df[DESCRIPTION_COLUMN].astype(str).str.strip(),
        
        # statement amounts are positive for expenses, 
        # multiply by -1 to match preferred convention, if required
        "amount": df[AMOUNT_COLUMN].astype(float) * EXPENSES_SIGN
    })