"""
Configuration for parsing statements from various issuers.
Required keys for each issuer include:
    - DATE_COLUMN: this is the column containing transaction dates.
    - DESCRIPTION_COLUMN
    - AMOUNT_COLUMN
    - EXPENSES_SIGN: a multiplier to apply to amounts to convert expenses to negative values (if needed).


NOTE: This file is deprecated as of 2025-07-11 as issuers management has moved to src/issuers.json in S3
"""

ISSUERS = {
    "amazon": {
        "DATE_COLUMN": "Transaction Date",
        "DESCRIPTION_COLUMN": "Description",
        "AMOUNT_COLUMN": "Amount",
        "EXPENSES_SIGN": 1
    },

    "amex": {
        "DATE_COLUMN": "Date",
        "DESCRIPTION_COLUMN": "Description",
        "AMOUNT_COLUMN": "Amount",
        "EXPENSES_SIGN": -1  # Amex statements have expenses as positive amounts
    },

    "chase": {
        "DATE_COLUMN": "Transaction Date",
        "DESCRIPTION_COLUMN": "Description",
        "AMOUNT_COLUMN": "Amount",
        "EXPENSES_SIGN": 1
    },

    "chase_debit": {
        "DATE_COLUMN": "Posting Date",
        "DESCRIPTION_COLUMN": "Description",
        "AMOUNT_COLUMN": "Amount",
        "EXPENSES_SIGN": 1
    },

    "rbc": {
        "DATE_COLUMN": "Transaction Date",
        "DESCRIPTION_COLUMN": "Description",
        "AMOUNT_COLUMN": "Amount",
        "EXPENSES_SIGN": 1
    }
}