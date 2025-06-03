import boto3
import traceback
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime, timezone
from helpers.categories import CATEGORIES
from botocore.exceptions import ClientError

# AWS secrets
AWS_ACCESS_KEY_ID = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]

S3_BUCKET = "aws-budget-buddy"
STATEMENTS_FOLDER = "statements"
MASTER_KEY = "categorized_expenses.parquet"

CATEGORY_COLUMN = "category"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# generate list of existing issuer folders in S3
response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{STATEMENTS_FOLDER}/", Delimiter="/")
existing_issuers = [prefix["Prefix"].split("/")[1] for prefix in response.get("CommonPrefixes", [])]

# ─── Header ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Budget Buddy", layout="wide")
st.title("👋 Hi! I'm your Budget Buddy")
st.text("Get started below!\nUse the sidebar to access the analytics page.")

# ─── Upload Section ────────────────────────────────────────────────────

st.header("Upload Statements")

issuer = st.selectbox("Select Issuer", existing_issuers)
file = st.file_uploader("Upload CSV File", type=["csv"])

if file and issuer:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    s3_key = f"{STATEMENTS_FOLDER}/{issuer}/{issuer}_statement_{now}.csv"

    try:
        s3.upload_fileobj(file, S3_BUCKET, s3_key)
        st.success(f"✅ Uploaded to S3: `{s3_key}`")

    except Exception as e:
        st.error(f"Failed to load or process data: {e}")
        st.text("Detailed traceback:")
        st.code(traceback.format_exc())

# ─── Categorize Section ────────────────────────────────────────────────────

st.header("Categorize Expenses")

try:
    response = s3.get_object(Bucket=S3_BUCKET, Key=MASTER_KEY)
    raw = response["Body"].read()
    buffer = BytesIO(raw)

    data = pd.read_parquet(buffer)
    data = data.sort_values(by="transaction_date", ascending=True)

    show_all = st.checkbox("Show all expenses", value=False)
    if not show_all:
        data = data[data[CATEGORY_COLUMN].isnull() | (data[CATEGORY_COLUMN] == "")]

    edited = st.data_editor(
        data,
        use_container_width=True,
        num_rows="dynamic",

        # configure CATEGORY_COLUMN as a dropdown selector
        column_config={CATEGORY_COLUMN: st.column_config.SelectboxColumn(options=CATEGORIES)}
    )

    if st.button("💾 Save Changes"):
        # Save to Parquet in memory
        out_buffer = BytesIO()
        edited.to_parquet(out_buffer, index=False, compression='snappy')

        # Upload updated master file
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=MASTER_KEY,
            Body=out_buffer.getvalue()
        )
        
        st.success("Categorized data synced to cloud.")

except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchKey':
        st.text("No categorized expenses found. Start with uploading some statements.")
    else:
        st.error(f"Failed to load or process data: {e}")
        st.text("Detailed traceback:")
        st.code(traceback.format_exc())