import time
import json
import boto3
import base64
import traceback
import config as c 
import pandas as pd
import streamlit as st

from io import BytesIO
from datetime import date, timedelta
from botocore.exceptions import ClientError
from streamlit_oauth import OAuth2Component, StreamlitOauthError
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, FILTER_PLACEHOLDER_TEXT

logs = boto3.client(
    "logs",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

LAMBDA_TIMEOUT = 30  # seconds
POLL_INTERVAL = 1    # seconds

# Lambda functions log these explicitly
SUCCESSFUL_CONFIRMATION_TEXT = "SUCCESS"
ERROR_CONFIRMATION_TEXT = "FAILURE" 

MISSING_ARGUMENTS_NOTICE = "Missing one or more required arguments."

def check_lambda_completed(log_group, invocation_time):
    """
    Polls recent log streams in the given log group to detect Lambda execution result.

    Args:
        log_group (str): Name of the CloudWatch log group.
        invocation_time (int): Epoch timestamp (in ms) of Lambda invocation to filter logs.

    Returns:
        True: if a successful confirmation message is found.
        list[str]: log messages if an error confirmation is found.
        False: if no confirmation is found before timeout.
    """

    for _ in range(LAMBDA_TIMEOUT // POLL_INTERVAL):
        try:
            streams = logs.describe_log_streams(
                logGroupName=log_group,
                orderBy="LastEventTime",
                descending=True,
                limit=3
            )

            for stream in streams.get("logStreams", []):
                stream_name = stream["logStreamName"]
                events = logs.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream_name,
                    startFromHead=False
                ).get("events", [])

                valid_events = [e for e in events if e["timestamp"] >= invocation_time]
                logged_messages = [e["message"] for e in valid_events]

                if any(SUCCESSFUL_CONFIRMATION_TEXT in msg for msg in logged_messages):
                    return True
                
                elif any(ERROR_CONFIRMATION_TEXT in msg for msg in logged_messages):
                    return valid_events
        
        except Exception as e:
            st.warning(f"Log check failed: {e}")
            st.text("Detailed traceback:")
            st.code(traceback.format_exc())
            
            break

        time.sleep(POLL_INTERVAL)
    
    return False

def create_text_filter(prompt_text, add_divider=True):
    if prompt_text is None:
        raise ValueError(MISSING_ARGUMENTS_NOTICE)
    
    # places a divider by default for aesthetics
    if add_divider:
        st.divider()

    st.text(prompt_text)
    return st.text_input(
        label = prompt_text, 
        placeholder = FILTER_PLACEHOLDER_TEXT,
        label_visibility = 'collapsed'
    ) 

def create_multiselect_filter(prompt_text, options, default, disabled=False, include_aesthetics_boilerplate=True):
    if include_aesthetics_boilerplate:
        st.divider()
        st.text(prompt_text)
    
    return st.multiselect(
        label = prompt_text,
        options = options,
        default = default,
        placeholder = FILTER_PLACEHOLDER_TEXT,
        label_visibility ='collapsed',
        disabled = disabled
    )

def get_time_range_dates(time_range):
    today = date.today()

    if time_range == "Current Month":
        start = today.replace(day=1)
        end = today

    elif time_range == "Current Year":
        start = today.replace(month=1, day=1)
        end = today

    elif time_range == "Last Month":
        first_day_this_month = today.replace(day=1)
        end = last_day_last_month = first_day_this_month - timedelta(days=1)
        start = last_day_last_month.replace(day=1)

    elif time_range == "Trailing 3 Months":
        start_month = today.month - 3
        start_year = today.year
        if start_month <= 0:
            start_month += 12
            start_year -= 1

        start = date(start_year, start_month, 1)
        end = today

    elif time_range == "Trailing 6 Months":
        start_month = today.month - 6
        start_year = today.year
        if start_month <= 0:
            start_month += 12
            start_year -= 1

        start = date(start_year, start_month, 1)
        end = today

    elif time_range == "Trailing Year":
        start = today.replace(year=today.year-1)
        end = today

    elif time_range == "Last Year":
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)

    else:
        raise ValueError(f"Unsupported time range: {time_range}")
    
    return start, end

def clear_issuer_selection():
    """Callback to clear issuer selection when a new file is uploaded."""
    st.session_state.issuer = None

def hex_to_rgba(hex_color, alpha=0.1):
    """
    Convert a hex color string to an RGBA tuple.
    
    Args:
        hex_color (str): Hex color string (e.g., '#FF5733').
        alpha (float): Alpha value for transparency (0.0 to 1.0).
    
    Returns:
        str: string formatted as: rgba(<RGBA color tuple>).
        str is used to be compatible with Plotly.
    """

    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return f"rgba({r},{g},{b},{alpha})"

def load_master():
    master = None

    # load master data
    try:
        response = c.s3.get_object(Bucket=c.S3_BUCKET, Key=c.MASTER_KEY)
        raw = response["Body"].read()
        buffer = BytesIO(raw)

        master = pd.read_parquet(buffer)
        master = master.sort_values(by=c.DATE_COLUMN, ascending=False)

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # master doesn't exist, skip loading
            pass

    return master

def update_master(master):
    """
    Update master in S3 with the provided DataFrame.
    
    Args:
        master (pd.DataFrame): The DataFrame to upload as the new master.
    """
    # Save to Parquet in memory
    out_buffer = BytesIO()
    master.to_parquet(out_buffer, index=False, compression='snappy')

    # Upload updated master file
    c.s3.put_object(
        Bucket=c.S3_BUCKET,
        Key=f"{c.MASTER_KEY}",
        Body=out_buffer.getvalue()
    )

def get_auth():
    """
    Get the authentication token for Streamlit session state.
    """

    try:
        # create a button to start the OAuth2 flow
        oauth2 = OAuth2Component(c.CLIENT_ID, c.CLIENT_SECRET, c.AUTHORIZE_ENDPOINT, c.TOKEN_ENDPOINT, c.TOKEN_ENDPOINT, c.REVOKE_ENDPOINT)
        result = oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com.tw/favicon.ico",
            redirect_uri=c.REDIRECT_URI,
            scope="openid email profile",
            key="google",
            extras_params={"prompt": "consent", "access_type": "offline"},
            use_container_width=True,
            pkce='S256',
        )
        
        if result:
            # decode the id_token jwt and get the user's email address
            id_token = result["token"]["id_token"]
            # verify the signature is an optional step for security
            payload = id_token.split(".")[1]
            # add padding to the payload if needed
            payload += "=" * (-len(payload) % 4)
            payload = json.loads(base64.b64decode(payload))
            email = payload["email"]

            st.session_state["auth"] = email
            st.session_state["token"] = result["token"]

            # rerun the app to reflect the new state
            st.rerun()

    except StreamlitOauthError as e:
        # user cancelled the OAuth2 flow
        pass

    except Exception as e:
        st.error(f"An error occurred during authentication: {e}")
        st.text("Detailed traceback:")
        st.code(traceback.format_exc())
        st.stop()