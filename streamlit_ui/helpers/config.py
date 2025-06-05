import streamlit as st
import boto3
import json

# AWS
S3_BUCKET = "aws-budget-buddy"
AWS_ACCESS_KEY_ID = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]
CATEGORIES_KEY = "categories.json"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

response = s3.get_object(Bucket=S3_BUCKET, Key=CATEGORIES_KEY)
CATEGORIES = sorted(json.loads(response['Body'].read().decode("utf-8")))

# column names
TRANSACTION_ID_COLUMN = "transaction_id"
DATE_COLUMN = "transaction_date"
DESCRIPTION_COLUMN = "description"
AMOUNT_COLUMN = "amount"
ISSUER_COLUMN = "statement_issuer"
CATEGORY_COLUMN = "category"
NOTES_COLUMN = "notes"

# st.data_editor settings
EDITING_NOT_ALLOWED_TEXT = "Editing is not allowed here! It breaks deduplication logic. 🤭"

column_configs = {
    TRANSACTION_ID_COLUMN: None,

    DATE_COLUMN: st.column_config.DateColumn(
        label="Transaction Date",
        disabled=True,
        help=EDITING_NOT_ALLOWED_TEXT,
        format="dddd, MMMM DD, YYYY",
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
        help=EDITING_NOT_ALLOWED_TEXT,
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