import time
import traceback
import config as c
import streamlit as st
from streamlit.components.v1 import html

from datetime import date, timedelta

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

def get_index(lst, idx, default=None):
    """
    Safely get value at list index
    
    Returns:
        list value at index, if index exists, otherwise returns default
    """
    try:
        return lst[idx]
    except IndexError:
        return default

def switch_to_tab(tab_name):
    """
        Streamlit does not offer a programmatic way to switch between st.tabs 
        As a workaround, we inject JavaScript that:
            finds the tab element in the DOM by its innerText value
            and performs a click() on the element

        Note: 
            Streamlit's rendering model checks if an HTML component has already been rendered
            and skips re-rendering if no change is detected.

            To bypass this, each script is given a unique id 

            Lastly, streamlit.components.v1.html inserts an iframe which contains the script that's ran.
            Even with kwarg height=0, the iframe still takes up space and has padding.
            This is a known issue, see: https://github.com/streamlit/streamlit/issues/6605

            To fix this, css.set_app_wide_styling() includes a style 
            where iframes with height=0 have `display: none` styling applied. 

        Args 
            tab_name (str): name of tab to switch to
    """

    safe_name = tab_name.replace('"', '\\"')
    js = f"""
    <script id={time.time()}>
        function clickTab() {{
            const tabs = parent.document.querySelectorAll('button[role="tab"]');
            for (const tab of tabs) {{
                if (tab.innerText.trim() === "{safe_name}") {{
                    tab.click();
                    return;
                }}
            }}
        }}

        clickTab();
    </script>
    """

    html(js, height=0)