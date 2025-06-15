import time
import json
import base64
import traceback
import pandas as pd
import streamlit as st
import config_general as c

from io import BytesIO
from utils.user import User
from datetime import date, timedelta
from botocore.exceptions import ClientError
from streamlit_oauth import OAuth2Component, StreamlitOauthError

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
            streams = c.logs.describe_log_streams(
                logGroupName=log_group,
                orderBy="LastEventTime",
                descending=True,
                limit=3
            )

            for stream in streams.get("logStreams", []):
                stream_name = stream["logStreamName"]
                events = c.logs.get_log_events(
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

def get_step_status(execution_arn):
    history = c.sf.get_execution_history(
        executionArn=execution_arn,
        maxResults=1000,
        reverseOrder=True
    )

    current_step = None
    last_completed_step = None

    for event in history["events"]:
        if not current_step and event["type"] == "TaskStateEntered":
            current_step = event["stateEnteredEventDetails"]["name"]

        if not last_completed_step and event["type"] in ["TaskStateExited", "TaskSucceeded"]:
            last_completed_step = event["stateExitedEventDetails"]["name"]

        if event["type"] in ["TaskFailed", "ExecutionFailed"]:
            details = event.get("taskFailedEventDetails") or event.get("executionFailedEventDetails") or {}
            error_info = {
                "error": details.get("error", "UnknownError"),
                "cause": details.get("cause", "No cause provided"),
                "failed_step": current_step
            }

            st.error(f"Something went wrong at {current_step or 'unknown step'}: {error_info['error']} — {error_info['cause']}")

        if current_step and last_completed_step:
            break  # found both, break loop

    return current_step, last_completed_step

def create_text_filter(prompt_text, add_divider=True):
    if prompt_text is None:
        raise ValueError(MISSING_ARGUMENTS_NOTICE)
    
    # places a divider by default for aesthetics
    if add_divider:
        st.divider()

    st.text(prompt_text)
    return st.text_input(
        label = prompt_text, 
        placeholder = c.FILTER_PLACEHOLDER_TEXT,
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
        placeholder = c.FILTER_PLACEHOLDER_TEXT,
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
        response = c.s3.get_object(Bucket=c.S3_BUCKET, Key=st.session_state.MASTER_KEY)
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
        Key=f"{st.session_state.MASTER_KEY}",
        Body=out_buffer.getvalue()
    )

def extract_categories(obj):
    """
    Recursively extract all terminal string values from a nested structure (dicts/lists).

    Args:
        obj (dict, list, or str): A nested combination of dictionaries, lists, and string values.

    Returns:
        list of str: All string values found anywhere in the structure, in depth-first order.
    """

    res = []
    if isinstance(obj, dict):
        for value in obj.values():
            res.extend(extract_categories(value))

    elif isinstance(obj, list):
        for item in obj:
            res.extend(extract_categories(item))

    elif isinstance(obj, str):
        res.append(obj)

    return res

def get_auth(unique_key=None):
    """
    Displays an OAuth2 login button using the provided client configuration
    On successful login, gets an authentication token for Streamlit session state.

    Parameters:
        unique_key (str or None): Optional. 
        A unique key to prevent component duplication errors in Streamlit. 
        
        If not provided, a random key will be generated internally.
        But the generation is a function of element type and parameters, 
        so if this function is invoked multiple times, it'll produce a
        "multiple component_instance elements with the same auto-generated ID" error.

        So, pass unique_key argument to avoid this
    """

    try:
        # create a button to start the OAuth2 flow
        oauth2 = OAuth2Component(c.CLIENT_ID, c.CLIENT_SECRET, c.AUTHORIZE_ENDPOINT, c.TOKEN_ENDPOINT, c.TOKEN_ENDPOINT, c.REVOKE_ENDPOINT)
        result = oauth2.authorize_button(
            name="Get Started",
            icon="https://www.google.com.tw/favicon.ico",
            redirect_uri=c.REDIRECT_URI,
            scope="openid email profile",
            # streamlit will raise an error if elements are duplicated without unique keys 
            key=unique_key,
            extras_params={"access_type": "offline", "prompt": "select_account"},
            use_container_width=True,
            pkce='S256',
        )
        
        if result:
            token = result["token"]
            st.session_state["token"] = token

            # decode the id_token jwt and get the user's email address
            id_token = result["token"]["id_token"]
            payload = id_token.split(".")[1]
            # add padding to the payload if needed
            payload += "=" * (-len(payload) % 4)
            payload = json.loads(base64.b64decode(payload))

            # instantiate User object
            st.session_state["user"] = User(payload=payload)
            st.session_state["auth"] = st.session_state.user.email

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

def logout():
    # effectively resets the session
    st.session_state.clear()

    # rerun the app to reflect the new state
    st.rerun()