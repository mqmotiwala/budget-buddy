# streamlit_ui/pages/Analytics.py

import streamlit as st
import boto3
import pandas as pd
from io import BytesIO
import altair as alt
from helpers.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

S3_BUCKET = "aws-budget-buddy"
AMOUNT_COLUMN = "amount"
CATEGORY_COLUMN = "category"
DATE_COLUMN = "transaction_date"
MASTER_KEY = "categorized_expenses.parquet"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

st.set_page_config(page_title="Spending Analytics", layout="wide")
st.title("📊 Spending Analytics")

try:
    response = s3.get_object(Bucket=S3_BUCKET, Key=MASTER_KEY)
    buffer = BytesIO(response["Body"].read())
    df = pd.read_parquet(buffer)

    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce").dt.date
    df = df.dropna(subset=[DATE_COLUMN, CATEGORY_COLUMN, AMOUNT_COLUMN])

    # Monthly totals by category
    df["month"] = pd.to_datetime(df[DATE_COLUMN]).dt.to_period("M").astype(str)
    monthly_totals = df.groupby(["month", CATEGORY_COLUMN])[AMOUNT_COLUMN].sum().reset_index()

    chart = alt.Chart(monthly_totals).mark_bar().encode(
        x="month:O",
        y=alt.Y(f"{AMOUNT_COLUMN}:Q", title="Total Spent"),
        color=CATEGORY_COLUMN,
        tooltip=["month", CATEGORY_COLUMN, AMOUNT_COLUMN]
    ).properties(
        width=800,
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

    # Summary table
    st.subheader("Total by Category")
    total_by_cat = df.groupby(CATEGORY_COLUMN)[AMOUNT_COLUMN].sum().sort_values(ascending=False)
    st.dataframe(total_by_cat.reset_index())

except Exception as e:
    st.error(f"Failed to load or process data: {e}")
