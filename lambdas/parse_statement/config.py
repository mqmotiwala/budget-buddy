"""
Configuration for parsing statements from various issuers.
Required keys for each issuer include:
    - DATE_COLUMN: this is the column containing transaction dates.
    - DESCRIPTION_COLUMN
    - AMOUNT_COLUMN
    - EXPENSES_SIGN: a multiplier to apply to amounts to convert expenses to negative values (if needed).
"""

ISSUER_CONFIG = {
    "amex": {
        "DATE_COLUMN": "Transaction Date",
        "DESCRIPTION_COLUMN": "Description",
        "AMOUNT_COLUMN": "Amount",
        "EXPENSES_SIGN": -1  # Amex statements have expenses as positive amounts
    }
}