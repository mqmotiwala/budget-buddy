import pandas as pd
import hashlib
import re
import logging 

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def parse(df, issuer_config):
    DATE_COLUMN = issuer_config["DATE_COLUMN"]
    DESCRIPTION_COLUMN = issuer_config["DESCRIPTION_COLUMN"]
    AMOUNT_COLUMN = issuer_config["AMOUNT_COLUMN"]
    EXPENSES_SIGN = issuer_config["EXPENSES_SIGN"]

    parsed_dates = pd.to_datetime(df[DATE_COLUMN], errors='coerce')
    num_invalid = parsed_dates.isna().sum()

    if num_invalid > 0:
        print(f"{num_invalid} rows had invalid dates and were set to NaT.")

    descriptions = df[DESCRIPTION_COLUMN].astype(str).str.strip()

    # generate transaction_ids, intended to be a unique deduplication key for transactions, via SHA-256 hashes over transaction_date and description columns
    # we intentionally exclude amount column, because the amount may be user-adjusted for valid reasons (splitting costs)
    # note that, its possible to have repeated transactions on the same day, producing duplicate SHA-256 hashes for valid repeated transactions
    # to handle this, we identify the valid repeated transactions, and re-hash them using the base hash to produce truly unique transaction_ids
    hashes = [
        hashlib.sha256(str([date, desc]).encode("utf-8")).hexdigest()
        for date, desc in zip(parsed_dates, descriptions)
    ]

    hash_counts = {}
    transaction_ids = []
    for h in hashes:
        hash_counts[h] = hash_counts.get(h, 0) + 1

        count = hash_counts.get(h)
        if count == 1:
            # this captures the first instance of all transactions, including transactions in valid repeated transactions
            transaction_ids.append(h)
        else:
            # subsequent transactions in valid repeat transactions are rehashed to produce final unique transaction_id
            new_hash = hashlib.sha256(f"{count} occurrence of {h}".encode("utf-8")).hexdigest()
            transaction_ids.append(new_hash)

            logger.info(f"count {count} for hash {h} detected. rehashed to {new_hash}")

    return pd.DataFrame({
        "transaction_id": transaction_ids,
        "transaction_date": parsed_dates,
        "description": descriptions,
        
        # statement amounts are positive for expenses, 
        # multiply by -1 to match preferred convention, if required
        "amount": df[AMOUNT_COLUMN].astype(float) * EXPENSES_SIGN
    })