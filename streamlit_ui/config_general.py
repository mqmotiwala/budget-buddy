'''
contains all config settings that are general across all users
'''

import boto3
import streamlit as st

# AWS General
S3_BUCKET = "aws-budget-buddy"
AWS_ACCESS_KEY_ID = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]

# boto3 clients
logs = boto3.client(
    "logs",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
    
# Google OAuth2Component instance
CLIENT_ID = st.secrets["oauth"]["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["oauth"]["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = st.secrets.get("oauth", {}).get("REDIRECT_URI", "http://localhost:8501")
AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"

# misc. settings
EXPENSES_PARENT_CATEGORY_KEY = "Expenses"
NON_EXPENSES_PARENT_CATEGORY_KEY = "Non-Expenses"
PREFERRED_UI_DATE_FORMAT_MOMENTJS = "dddd, MMMM DD, YYYY"
PREFERRED_UI_DATE_FORMAT_STRFTIME = "%A, %B %d, %Y"
FILTER_PLACEHOLDER_TEXT = "No filter is applied when there is no input."
FILE_UPLOADER_HELP_TEXT = "Your privacy is important to us. Statements uploaded remain encrypted at all times."
STREAMLIT_PAGE_CONFIG = {
    "page_title": "Budget Buddy",
    "page_icon": "🤓",
    "layout": "wide",
    "initial_sidebar_state": "auto",
    "menu_items": {
        "Report a Bug": "mailto:mqmotiwala@gmail.com"
    }
}

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

# note: CATEGORY_COLUMN config is added right before st.data_editor() is invoked
# this is because it relies on user specific data
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