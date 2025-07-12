import time 
import json
import random
import traceback
import config as c
import streamlit as st
import utils.helpers as h
from datetime import datetime, timezone

def show_upload():
    # ensure master data is loaded
    if not hasattr(st.session_state.user, "master"):
        st.session_state.user.load_master()
    master = st.session_state.user.master

    st.header("🗂️ Upload Statements")
    
    if h.user_is_premium():
        # never impose upload limits on premium users
        disabled = False
    else:
        # show statement processing limit notice if free-tier
        num_uploads = getattr(st.session_state.user, 'num_uploads', 0)
        num_remaining_uploads = c.MAX_FREE_STATEMENT_UPLOADS - num_uploads
        
        # evaluate if file uploading should be disabled
        if num_remaining_uploads <= 0:
            st.error(f"You can only process {c.MAX_FREE_STATEMENT_UPLOADS} statements on the free tier. Upgrade to premium!", icon="🚫")
            disabled = True
        else:
            st.warning(f"You can process {num_remaining_uploads} more statements.")
            disabled = False

    file = st.file_uploader("Upload CSV File", type=["csv"], on_change=h.clear_issuer_selection, help=c.FILE_UPLOADER_HELP_TEXT, disabled=disabled)
    
    issuer_disabled = disabled or not file
    issuer_placeholder = "Upload a statement first." if file is None else "Select the issuer for this statement; or add a new one."
    issuer = st.selectbox(
        "Select Issuer",
        c.KNOWN_ISSUERS, 
        index=None, 
        key="issuer", 
        disabled=issuer_disabled, 
        accept_new_options=True, 
        placeholder=issuer_placeholder
    )

    if issuer is not None and issuer not in c.KNOWN_ISSUERS:
        # logic to follow
        st.write("🆕 New Issuer")

    if file and issuer:
        if st.button("📤 Upload Statement"):
            upload_s = time.time()
            formatted_time = datetime.fromtimestamp(upload_s, tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")

            new_statement_key = f"{st.session_state.user.STATEMENTS_FOLDER}/{issuer}/{issuer}_statement_{formatted_time}.csv"

            with st.status("Uploading to cloud...", expanded=True) as status:
                try:
                    c.s3.upload_fileobj(file, c.S3_BUCKET, new_statement_key)
                    st.write("🟢 Uploaded to cloud ☁️")
                except Exception as e:
                    status.update(label="Upload failed", state="error")
                    st.error(f"🔴 Upload failed: {e}")
                    st.code(traceback.format_exc())
                    st.stop()

                input_payload = {"key": new_statement_key}
                response = c.sf.start_execution(
                    stateMachineArn=c.UPLOAD_STATE_MACHINE,
                    input=json.dumps(input_payload)
                )

                execution_arn = response["executionArn"]
                completed_reference = None
                used_msgs = set()
                msg = None
                while c.sf.describe_execution(executionArn=execution_arn)["status"] not in c.UPLOAD_STATE_MACHINE_TERMINAL_STATES:
                    current, completed = h.get_step_status(execution_arn)

                    # get a msg not yet used
                    available_msgs = c.LAMBDAS.get(current)["progress"]
                    unused_msgs = list(set(available_msgs) - used_msgs)

                    if unused_msgs:
                        msg = random.choice(unused_msgs)
                        used_msgs.add(msg)
                        h.animate_typing(msg)
                    else:
                        # all messages used, allow reuse
                        used_msgs.clear()

                    if completed != completed_reference:
                        completed_reference = completed
                        st.write(c.LAMBDAS.get(completed)["success"])
                      
                    time.sleep(0.5)

                # One last check to emit final completed step's success message
                current, completed = h.get_step_status(execution_arn)
                if completed != completed_reference:
                    st.write(c.LAMBDAS.get(completed)["success"])

                status.update(label="done!", state="complete", expanded=False)

                # increment num_uploads counter
                st.session_state.user.update_num_uploads()

                # update master contents
                st.session_state.user.load_master()
