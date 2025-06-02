# streamlit_app/pages/Categorize.py

import streamlit as st
import boto3
import os
import pandas as pd

from utils.categorize import (
    load_master_dataframe,
    save_updated_dataframe,
    render_categorization_ui,
    add_category_column_if_missing
)

st.set_page_config(page_title="Categorize Expenses", layout="wide")
st.title("📂 Categorize Expenses")

# Load AWS credentials from Streamlit secrets
aws_access_key = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
aws_secret_key = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
aws_region = st.secrets["aws"]["AWS_REGION"]

bucket = "aws-budget-buddy"
key = "cleaned/master/master.csv"

# Initialize S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

# Load and render editable dataframe
try:
    df = load_master_dataframe(s3, bucket, key)
    df = add_category_column_if_missing(df)
    edited_df = render_categorization_ui(df)

    if st.button("💾 Save Categorized Data"):
        save_updated_dataframe(s3, edited_df, bucket, key)
        st.success("Categorized data saved back to S3.")
except Exception as e:
    st.error(f"Failed to load or process data: {e}")
