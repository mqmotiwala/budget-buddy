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
UPLOAD_STATE_MACHINE = "arn:aws:states:us-west-2:676206945006:stateMachine:handle_new_statement"

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

sf = boto3.client(
    "stepfunctions",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# free/premiun tier settings
MAX_FREE_STATEMENT_UPLOADS = 3

# Google OAuth2Component instance
CLIENT_ID = st.secrets["oauth"]["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["oauth"]["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = st.secrets.get("oauth", {}).get("REDIRECT_URI", "http://localhost:8501")
AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"

# categorization settings
INCOME_PARENT_CATEGORY_KEY = "Income"
SAVINGS_PARENT_CATEGORY_KEY = "Savings"
EXPENSES_PARENT_CATEGORY_KEY = "Expenses"
NON_EXPENSES_PARENT_CATEGORY_KEY = "Non-Expenses"
NON_EXPENSES_CATEGORIES = ["Void", "TBD"]

# misc. settings
PREFERRED_UI_DATE_FORMAT_MOMENTJS = "dddd, MMMM DD, YYYY"
PREFERRED_UI_DATE_FORMAT_STRFTIME = "%A, %B %d, %Y"
FILTER_PLACEHOLDER_TEXT = "No filter is applied when there is no input."
FILE_UPLOADER_HELP_TEXT = "Statements uploaded remain encrypted at all times."
ASSETS_PATH = "streamlit_ui/assets"
LOGOUT_BUTTON_KEY_NAME = "logout_button"

# tab settings
GET_PREMIUM_TAB_NAME = "Get Premium"
BUDGET_BUDDY_TAB_NAME = "Budget Buddy"
PRIVACY_POLICY_TAB_NAME = "Privacy Policy"
SELECT_ISSUERS_TAB_NAME = "Statement Issuers"
COMMUNICATIONS_HUB_TAB_NAME = "Communications Hub"
CUSTOMIZE_CATEGORIES_TAB_NAME = "Customize Categories"

# this is passed to st.tabs() which displays tabs in order of elements in the list
TAB_NAMES = [
    BUDGET_BUDDY_TAB_NAME,
    CUSTOMIZE_CATEGORIES_TAB_NAME,
    SELECT_ISSUERS_TAB_NAME,
    COMMUNICATIONS_HUB_TAB_NAME,
    PRIVACY_POLICY_TAB_NAME,
    GET_PREMIUM_TAB_NAME,
]

# page configs
BUDGET_BUDDY_ICON = "🤓"
BUDGET_BUDDY_COLOR = "#EFB60C" # same as primaryColor in config.toml
STREAMLIT_GENERAL_PAGE_CONFIG = {
    "page_title": "Budget Buddy",
    "page_icon": BUDGET_BUDDY_ICON,
    "layout": "wide",
    "initial_sidebar_state": "auto"
}

STREAMLIT_LANDING_PAGE_CONFIG = STREAMLIT_GENERAL_PAGE_CONFIG.copy()
STREAMLIT_LANDING_PAGE_CONFIG["layout"] = "centered"

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
OUTDATED_CATEGORY_LABEL_PREFIX = "OUTDATED CATEGORY:"

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

# Lambda functions
LAMBDAS = {
    "parse_statement": {
        "progress": [
            "🟠 Giving the CSV a good look...",
            "🟠 Decoding your transactions, line by line...",
            "🟠 Matching CSV format to our secret sauce...",
            "🟠 Parsing with care — no charge left behind!",
            "🟠 Sorting the signal from the noise...",
            "🟠 Zipping everything into place — almost there!"
        ],
        "success": "🟢 I parsed your statement 😋",
        "error": "🔴 Something went wrong while processing this statement. 😔",
    },
    "update_master": {
        "progress": [
            "🟠 Dusting off the old master file...",
            "🟠 Merging the new with the old — carefully...",
            "🟠 Crunching some numbers...",
            "🟠 Shuffling through your transactions...",
            "🟠 Checking for duplicates...",
            "🟠 Giving your expenses a quick polish...",
            "🟠 Preparing your financial history scroll...",
            "🟠 Compressing data, gotta stay lean...",
            "🟠 Backing up the old master file...",
            "🟠 Uploading the updated ledger to the cloud gods...",
            "🟠 Giving your master file a well-deserved upgrade..."
        ],
        "success": "🟢 Updated master file! Let's get categorizin' 🤩",
        "error": "🔴 Something went wrong while updating your master file. 😔"
    }
}

UPLOAD_STATE_MACHINE_TERMINAL_STATES = [
    "SUCCEEDED",
    "FAILED",
    "TIMED OUT",
    "ABORTED"
]