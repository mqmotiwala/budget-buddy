import time
import streamlit as st
import boto3
from helpers.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logs = boto3.client(
    "logs",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

LAMBDA_TIMEOUT = 30  # seconds
POLL_INTERVAL = 1    # seconds
SUCCESSFUL_CONFIRMATION_TEXT = "SUCCESS" # Lambda functions log this explicitly

def check_lambda_completed(log_group, confirmation_text=SUCCESSFUL_CONFIRMATION_TEXT, timeout=LAMBDA_TIMEOUT, poll_interval=POLL_INTERVAL):
    """
    Polls recent log streams in the given log group to confirm completion message.
    """

    for _ in range(timeout // poll_interval):
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

                if any(confirmation_text in e["message"] for e in events):
                    return True
        
        except Exception as e:
            st.warning(f"Log check failed: {e}")

        time.sleep(poll_interval)
    
    return False
