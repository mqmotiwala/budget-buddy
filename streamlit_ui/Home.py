import time 
import boto3
import traceback
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime, timezone
from helpers.config import CATEGORIES, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from helpers.helpers import check_lambda_completed
from botocore.exceptions import ClientError

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

issuer = st.selectbox("Select Issuer", existing_issuers, index=None, key="issuer_select")
file = st.file_uploader("Upload CSV File", type=["csv"], key="file_uploader")

if file and issuer:
    if st.button("📤 Upload Statement"):
        upload_s = time.time()
        upload_ms = int(upload_s * 1000) # used to check against Lambda logs for successful completion
        formatted_time = datetime.fromtimestamp(upload_s, tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")

        new_statement_key = f"{STATEMENTS_FOLDER}/{issuer}/{issuer}_statement_{formatted_time}.csv"

        with st.status("Uploading to S3...", expanded=True) as status:
            try:
                s3.upload_fileobj(file, S3_BUCKET, new_statement_key)
                status.write("🟢 Uploaded to S3")
            except Exception as e:
                status.update(label="Upload failed", state="error")
                st.error(f"🔴 Upload failed: {e}")
                st.code(traceback.format_exc())
                st.stop()

            # Check Lambdas completed
            for lambda_function in ["parse_statement", "update_master"]:
                status.update(label=f"🟠 Waiting for `{lambda_function}` Lambda...")
                if check_lambda_completed(f"/aws/lambda/{lambda_function}", upload_ms):
                    status.write(f"🟢 `{lambda_function}` completed")
                else:
                    status.update(label=f"{lambda_function}() timed out", state="error")
                    st.warning(f"🔴 Could not confirm {lambda_function}() executed.")
                    st.stop()
            
            status.update(label="done!", state="complete", expanded=False)

# ─── Categorize Section ────────────────────────────────────────────────────

st.header("Categorize Expenses")

try:
    response = s3.get_object(Bucket=S3_BUCKET, Key=MASTER_KEY)
    raw = response["Body"].read()
    buffer = BytesIO(raw)

    data = pd.read_parquet(buffer)
    data = data.sort_values(by="transaction_date", ascending=True)

    uncategorized = data[data[CATEGORY_COLUMN].isna() | (data[CATEGORY_COLUMN] == "")]

    if uncategorized.empty:
        st.text("Nice! all expenses are categorized.")
        st.text("You can still edit existing categories below.")
    else:
        st.text(f"Found {len(uncategorized)} uncategorized expenses.")

    # if there are uncategorized expenses, filter only for them
    # otherwise show all expenses
    show_all = st.checkbox("Show all expenses", value=uncategorized.empty)
    if not show_all:
        data = uncategorized

    if show_all or not uncategorized.empty: 
        edited = st.data_editor(
            data,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
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
        st.text("No categorized expenses found. Start by uploading some statements.")
    else:
        st.error(f"Failed to load or process data: {e}")
        st.text("Detailed traceback:")
        st.code(traceback.format_exc())