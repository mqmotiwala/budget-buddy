import time
import boto3
import traceback
import streamlit as st
from helpers.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, FILTER_PLACEHOLDER_TEXT

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