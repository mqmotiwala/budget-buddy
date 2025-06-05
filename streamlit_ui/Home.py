import time 
import json
import boto3
import traceback
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime, timezone
import helpers.config as c 
from helpers.helpers import check_lambda_completed, create_text_filter, create_multiselect_filter
from botocore.exceptions import ClientError

s3 = boto3.client(
    "s3",
    aws_access_key_id=c.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=c.AWS_SECRET_ACCESS_KEY,
    region_name=c.AWS_REGION
)

# generate list of existing issuer folders in S3
response = s3.list_objects_v2(Bucket=c.S3_BUCKET, Prefix=f"{c.STATEMENTS_FOLDER}/", Delimiter="/")
existing_issuers = [prefix["Prefix"].split("/")[1] for prefix in response.get("CommonPrefixes", [])]

# ─── Header ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Budget Buddy", layout="wide")
st.title("👋 Hi! I'm your Budget Buddy")
st.text("Get started below!\nUse the sidebar to access the analytics page.")

# ─── Upload Section ────────────────────────────────────────────────────

st.header("Upload Statements")

# load master data
try:
    response = s3.get_object(Bucket=c.S3_BUCKET, Key=c.MASTER_KEY)
    raw = response["Body"].read()
    buffer = BytesIO(raw)

    master = pd.read_parquet(buffer)
    master = master.sort_values(by=c.DATE_COLUMN, ascending=True)

    latest_dates = master.groupby(c.ISSUER_COLUMN)[c.DATE_COLUMN].max()
    recommended_date = latest_dates.min().strftime("%A, %B %d, %Y")
    st.markdown(f"To prevent data gaps, give me statements from :rainbow[{recommended_date}] or earlier!")

    master_exists = True
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchKey':
        master_exists = False

issuer = st.selectbox("Select Issuer", existing_issuers, index=None)
file = st.file_uploader("Upload CSV File", type=["csv"])

if file and issuer:
    if st.button("📤 Upload Statement"):
        upload_s = time.time()
        upload_ms = int(upload_s) * 1000 # used to check against Lambda logs for successful completion
        formatted_time = datetime.fromtimestamp(upload_s, tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")

        new_statement_key = f"{c.STATEMENTS_FOLDER}/{issuer}/{issuer}_statement_{formatted_time}.csv"

        with st.status("Uploading to S3...", expanded=True) as status:
            try:
                s3.upload_fileobj(file, c.S3_BUCKET, new_statement_key)
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
        uncategorized = master[master[c.CATEGORY_COLUMN].isna()]
        TBD = master[(master[c.CATEGORY_COLUMN] == "TBD")]

        with st.expander("Apply filters", icon=":material/tune:"):
            # date filter
            prompt_text = "Filter by transaction dates"
            st.text(prompt_text)
            min_date, max_date = st.select_slider(
                label=prompt_text, 
                options=master[c.DATE_COLUMN], 
                value=(master[c.DATE_COLUMN].min(), master[c.DATE_COLUMN].max()),
                format_func=lambda x: x.strftime(c.PREFERRED_UI_DATE_FORMAT_STRFTIME),
                label_visibility='collapsed'
            )
            
            # description filter
            description_filter_setting = create_text_filter(prompt_text="Filter by description")

            # amount filter
            st.divider()
            prompt_text = "Filter by transaction amount"
            st.text(prompt_text)
            min_amount = int(master[c.AMOUNT_COLUMN].min())
            max_amount = int(master[c.AMOUNT_COLUMN].max())
            range_step = 10
            min_amount, max_amount = st.select_slider(
                label=prompt_text, 
                options=range(min_amount, max_amount + range_step, range_step),
                value=(min_amount, max_amount),
                format_func=lambda x: f"-${abs(x):,}" if x < 0 else f"${x:,}",
                label_visibility='collapsed'
            )
            
            # issuer filter
            filtered_issuers = create_multiselect_filter(prompt_text="Filter by statement issuer", options=existing_issuers, default=existing_issuers)

            # category filter            
            st.divider()
            prompt_text = "Filter by category"
            st.text(prompt_text)

            # if there are uncategorized expenses, filter only for them by default
            show_uncategorized_only = st.toggle("Show uncategorized only", value=not(uncategorized.empty))

            # otherwise, let user decide which categories to review
            filtered_categories = create_multiselect_filter(
                prompt_text = "Filter by category", 
                options = c.CATEGORIES, 
                # if there are no more uncategorized transactions, except for those marked as "TBD", then default to showing those.
                default = ["TBD"] if uncategorized.empty and not(TBD.empty) else None,
                disabled = show_uncategorized_only,
                include_aesthetics_boilerplate=False
            )

            # notes filter
            notes_filter_setting = create_text_filter("Filter by notes")

        date_filter = master[c.DATE_COLUMN].between(min_date, max_date)
        description_filter = master[c.DESCRIPTION_COLUMN].str.contains(description_filter_setting, case=False, na=False) if description_filter_setting else True
        amount_filter = master[c.AMOUNT_COLUMN].between(min_amount, max_amount)
        issuer_filter = master[c.ISSUER_COLUMN].isin(filtered_issuers) if filtered_issuers else True
        category_filter = master[c.CATEGORY_COLUMN].isna() if show_uncategorized_only else master[c.CATEGORY_COLUMN].isin(filtered_categories) if filtered_categories and len(filtered_categories) != len(c.CATEGORIES) else True
        notes_filter = master[c.NOTES_COLUMN].str.contains(notes_filter_setting, case=False, na=False) if notes_filter_setting else True

        display_df = master[date_filter & description_filter & amount_filter & issuer_filter & category_filter & notes_filter]

        if uncategorized.empty and TBD.empty:
            st.text(":rainbow[Nice!] All expenses are categorized.")
            st.text("You can still edit existing categories below.")
        else:
            st.markdown(f":rainbow[{len(uncategorized) + len(TBD)}/{len(master)}] expenses are uncategorized!")

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
                Bucket=c.S3_BUCKET,
                Key=c.MASTER_KEY,
                Body=out_buffer.getvalue()
            )
            
            st.success("Categorized data synced to cloud.")
            st.rerun()
    else:
        st.write("No categorized expenses found. Start by uploading some statements.")

except Exception as e:
    st.error(f"Failed to handle master data: {e}")
    st.text("Detailed traceback:")
    st.code(traceback.format_exc())