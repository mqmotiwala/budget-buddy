import time 
import json
import traceback
import config as c 
import streamlit as st
import utils.helpers as h
from datetime import datetime, timezone

def show_upload():
    st.header("🗂️ Upload Statements")
    
    master = st.session_state.master
    if master is not None and not master.empty:
        latest_dates = master.groupby(c.ISSUER_COLUMN)[c.DATE_COLUMN].max()
        recommended_date = latest_dates.min().strftime("%A, %B %d, %Y")
        st.markdown(f"To prevent data gaps, give me statements from :rainbow[{recommended_date}] or earlier!")

    file = st.file_uploader("Upload CSV File", type=["csv"], on_change=h.clear_issuer_selection, help=c.FILE_UPLOADER_HELP_TEXT)
    issuer = st.selectbox("Select Issuer", c.EXISTING_ISSUERS, index=None, key="issuer")

    if file and issuer:
        if st.button("📤 Upload Statement"):
            upload_s = time.time()
            upload_ms = int(upload_s) * 1000 # used to check against Lambda logs for successful completion
            formatted_time = datetime.fromtimestamp(upload_s, tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")

            new_statement_key = f"{c.STATEMENTS_FOLDER}/{issuer}/{issuer}_statement_{formatted_time}.csv"

            with st.status("Uploading to S3...", expanded=True) as status:
                try:
                    c.s3.upload_fileobj(file, c.S3_BUCKET, new_statement_key)
                    status.write("🟢 Uploaded to S3")
                except Exception as e:
                    status.update(label="Upload failed", state="error")
                    st.error(f"🔴 Upload failed: {e}")
                    st.code(traceback.format_exc())
                    st.stop()

                # Check Lambdas completed
                for lambda_function in ["parse_statement", "update_master"]:
                    status.update(label=f"🟠 Waiting for `{lambda_function}` Lambda function to complete...")
                    res = h.check_lambda_completed(f"/aws/lambda/{lambda_function}", upload_ms)

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

                # update master contents
                st.session_state.master = h.load_master()
