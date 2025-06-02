# streamlit_app/pages/Upload.py

import boto3
import traceback
import streamlit as st
from datetime import datetime, timezone

# AWS secrets
AWS_ACCESS_KEY_ID = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]

S3_BUCKET = "aws-budget-buddy"
STATEMENTS_FOLDER = "statements"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# generate list of existing issuer folders inSS S3
response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{STATEMENTS_FOLDER}/", Delimiter="/")
existing_issuers = [prefix["Prefix"].split("/")[1] for prefix in response.get("CommonPrefixes", [])]

# ─── Streamlit Page UI ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Upload Statement", layout="centered")
st.title("Upload Statement")

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
