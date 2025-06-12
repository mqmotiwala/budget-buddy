import streamlit as st
import boto3
import json

# AWS
S3_BUCKET = "aws-budget-buddy"
AWS_ACCESS_KEY_ID = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]
STATEMENTS_FOLDER = "statements"
MASTER_KEY = "categorized_expenses.parquet"
CATEGORIES_KEY = "categories.json"

# general settings
PREFERRED_UI_DATE_FORMAT_MOMENTJS = "dddd, MMMM DD, YYYY"
PREFERRED_UI_DATE_FORMAT_STRFTIME = "%A, %B %d, %Y"
FILTER_PLACEHOLDER_TEXT = "No filter is applied when there is no input."
FILE_UPLOADER_HELP_TEXT = "Your privacy is important to us. Statements uploaded remain encyrpted at all times."

# categories
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def extract_categories(obj):
    """
    Recursively extract all terminal string values from a nested structure (dicts/lists).

    Args:
        obj (dict, list, or str): A nested combination of dictionaries, lists, and string values.

    Returns:
        list of str: All string values found anywhere in the structure, in depth-first order.
    """

    res = []
    if isinstance(obj, dict):
        for value in obj.values():
            res.extend(extract_categories(value))

    elif isinstance(obj, list):
        for item in obj:
            res.extend(extract_categories(item))

    elif isinstance(obj, str):
        res.append(obj)

    return res

response = s3.get_object(Bucket=S3_BUCKET, Key=CATEGORIES_KEY)
CATEGORIES_BODY = json.loads(response['Body'].read().decode("utf-8"))
CATEGORIES = extract_categories(CATEGORIES_BODY)

EXPENSES_PARENT_CATEGORY_KEY = "Expenses"
NON_EXPENSES_PARENT_CATEGORY_KEY = "Non-Expenses"
EXPENSES_CATEGORIES = extract_categories(CATEGORIES_BODY.get(EXPENSES_PARENT_CATEGORY_KEY, {}))
NON_EXPENSES_CATEGORIES = extract_categories(CATEGORIES_BODY.get(NON_EXPENSES_PARENT_CATEGORY_KEY, {}))

# existing issuers
response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{STATEMENTS_FOLDER}/", Delimiter="/")
EXISTING_ISSUERS = [prefix["Prefix"].split("/")[1] for prefix in response.get("CommonPrefixes", [])]

# column names
TRANSACTION_ID_COLUMN = "transaction_id"
DATE_COLUMN = "transaction_date"
DESCRIPTION_COLUMN = "description"
AMOUNT_COLUMN = "amount"
ISSUER_COLUMN = "statement_issuer"
CATEGORY_COLUMN = "category"
NOTES_COLUMN = "notes"
GROUP_BY_COLUMN = "group_by"

# st.data_editor settings
EDITING_NOT_ALLOWED_TEXT = "Editing is not allowed here! It breaks deduplication logic. 🤭"
SELECTION_PROMPT = "To get started, make a selection."

column_configs = {
    TRANSACTION_ID_COLUMN: None,

    DATE_COLUMN: st.column_config.DateColumn(
        label="Transaction Date",
        disabled=True,
        help=EDITING_NOT_ALLOWED_TEXT,
        format=PREFERRED_UI_DATE_FORMAT_MOMENTJS,
        width="medium"
    ),

    DESCRIPTION_COLUMN: st.column_config.TextColumn(
        label="Description",
        disabled=True,
        help=EDITING_NOT_ALLOWED_TEXT,
        width=None
    ),

    AMOUNT_COLUMN: st.column_config.NumberColumn(
        label="Amount",
        format="dollar",
        width="medium"
    ),

    ISSUER_COLUMN: st.column_config.TextColumn(
        label="Statement Issuer",
        disabled=True, 
        width="medium"
    ),

    CATEGORY_COLUMN: st.column_config.SelectboxColumn(
        label="Category",
        options=CATEGORIES,
        width="medium"
    ),

    NOTES_COLUMN: st.column_config.TextColumn(
        label="Notes",
        width="large"
    )
}

# analytics time ranges options
TIME_RANGES = [
    "Current Month",
    "Current Year",
    "Last Month",
    "Trailing 3 Months",
    "Trailing 6 Months",
    "Trailing Year",
    "Last Year",
    "All Time",
    "Custom"
]