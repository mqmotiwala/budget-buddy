import time 
import json
import boto3
import traceback
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime, timezone
import helpers.config as c 
from helpers.helpers import check_lambda_completed
from botocore.exceptions import ClientError

S3_BUCKET = "aws-budget-buddy"
STATEMENTS_FOLDER = "statements"
MASTER_KEY = "categorized_expenses.parquet"

s3 = boto3.client(
    "s3",
    aws_access_key_id=c.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=c.AWS_SECRET_ACCESS_KEY,
    region_name=c.AWS_REGION
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

# load master data
try:
    response = s3.get_object(Bucket=S3_BUCKET, Key=MASTER_KEY)
    raw = response["Body"].read()
    buffer = BytesIO(raw)

    master = pd.read_parquet(buffer)
    master = master.sort_values(by="transaction_date", ascending=True)

    latest_dates = master.groupby("statement_issuer")["transaction_date"].max()
    recommended_date = latest_dates.min().strftime("%A, %B %d, %Y")
    st.markdown(f"To prevent data gaps, give me statements from :rainbow[{recommended_date}] or earlier!")

    master_exists = True
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchKey':
        master_exists = False

issuer = st.selectbox("Select Issuer", existing_issuers, index=None, key="issuer_select")
file = st.file_uploader("Upload CSV File", type=["csv"], key="file_uploader")

if file and issuer:
    if st.button("📤 Upload Statement"):
        upload_s = time.time()
        upload_ms = int(upload_s) * 1000 # used to check against Lambda logs for successful completion
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
                status.update(label=f"🟠 Waiting for `{lambda_function}` Lambda function to complete...")
                res = check_lambda_completed(f"/aws/lambda/{lambda_function}", upload_ms)

                if isinstance(res, list):
                    # logs containing error msg detected
                    error_msg = f"🔴 `{lambda_function}` errored out"
                    st.error(error_msg)      
                    status.update(label=error_msg, state="error")                     
                    st.code(json.dumps(res, indent=4), language="json")
                    st.stop()
                else:
                    if res:
                        status.write(f"🟢 `{lambda_function}` completed")
                    else:
                        status.update(label=f"{lambda_function}() timed out", state="error")
                        st.warning(f"🔴 Could not verify {lambda_function} executed in time.")
                        st.stop()
                
            status.update(label="done!", state="complete", expanded=False)

            # force streamlit to rerun the page
            # this will grab the new master contents
            st.rerun()

# ─── Categorize Section ────────────────────────────────────────────────────

st.header("Categorize Expenses")

try:
    if master_exists:
        uncategorized = master[master[c.CATEGORY_COLUMN].isna() | (master[c.CATEGORY_COLUMN] == "")]

        if uncategorized.empty:
            st.text("Nice! all expenses are categorized.")
            st.text("You can still edit existing categories below.")
        else:
            st.text(f"Found {len(uncategorized)} uncategorized expenses.")

        # if there are uncategorized expenses, filter only for them
        # otherwise show all expenses
        show_all = st.checkbox("Show all expenses", value=uncategorized.empty)
        display_df = master if show_all else uncategorized

        edited = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            column_config=c.column_configs
        )

        if st.button("💾 Save Changes"):
            # Update original master with edited categories
            master.update(edited)

            # Save to Parquet in memory
            out_buffer = BytesIO()
            master.to_parquet(out_buffer, index=False, compression='snappy')

            # Upload updated master file
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=MASTER_KEY,
                Body=out_buffer.getvalue()
            )
            
            st.success("Categorized data synced to cloud.")
    else:
        st.write("No categorized expenses found. Start by uploading some statements.")

except Exception as e:
    st.error(f"Failed to handle master data: {e}")
    st.text("Detailed traceback:")
    st.code(traceback.format_exc())