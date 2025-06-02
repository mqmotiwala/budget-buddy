# streamlit_app/utils/categorize.py

import pandas as pd
import streamlit as st

CATEGORIES = [
    "Groceries", "Dining", "Transport", "Travel", "Utilities",
    "Subscriptions", "Healthcare", "Entertainment", "Other"
]

CATEGORY_COL = "category"


def load_master_dataframe(s3_client, bucket, key):
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj["Body"])
    return df


def save_updated_dataframe(s3_client, df, bucket, key):
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=df.to_csv(index=False).encode("utf-8")
    )


def render_categorization_ui(df, editable_cols=[CATEGORY_COL]):
    st.write("### Categorize Transactions")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            CATEGORY_COL: st.column_config.SelectboxColumn(
                "Category",
                options=CATEGORIES,
                required=False,
            )
        }
    )
    return edited_df


def add_category_column_if_missing(df):
    if CATEGORY_COL not in df.columns:
        df[CATEGORY_COL] = ""
    return df
