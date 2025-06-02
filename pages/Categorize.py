# streamlit_app/pages/Categorize.py

import streamlit as st
import boto3
import pandas as pd
import traceback
from categories import CATEGORIES
from io import BytesIO

# AWS secrets
AWS_ACCESS_KEY_ID = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]

S3_BUCKET = "aws-budget-buddy"
MASTER_KEY = "categorized_expenses.parquet"

CATEGORY_COLUMN = "category"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# ─── Streamlit Page UI ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Categorize Expenses", layout="wide")
st.title("Categorize Expenses")

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
        
        st.success("Categorized data saved back to S3.")

except Exception as e:
    st.error(f"Failed to load or process data: {e}")
    st.text("Detailed traceback:")
    st.code(traceback.format_exc())