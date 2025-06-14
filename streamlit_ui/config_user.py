'''
contains all config settings that are user-specific
'''

import io
import json
import streamlit as st
import utils.helpers as h
import config_general as c
from botocore.exceptions import ClientError

# auth based settings
def load_user_config():
    st.session_state.ROOT_FOLDER = st.session_state.auth # auth = user email
    st.session_state.STATEMENTS_FOLDER = f"{st.session_state.ROOT_FOLDER}/statements"
    st.session_state.MASTER_KEY = f"{st.session_state.ROOT_FOLDER}/categorized_expenses.parquet"
    st.session_state.CATEGORIES_KEY = f"{st.session_state.ROOT_FOLDER}/categories.json"

    try:
        response = c.s3.get_object(Bucket=c.S3_BUCKET, Key=st.session_state.CATEGORIES_KEY)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # user has no defined categories
            # initialize a default response object that will pass downstream commands
            response = {"Body": io.BytesIO(b"{}")}

    st.session_state.CATEGORIES_BODY = json.loads(response['Body'].read().decode("utf-8"))
    st.session_state.CATEGORIES = h.extract_categories(st.session_state.CATEGORIES_BODY)
    st.session_state.EXPENSES_CATEGORIES = h.extract_categories(st.session_state.CATEGORIES_BODY.get(c.EXPENSES_PARENT_CATEGORY_KEY, {}))
    st.session_state.NON_EXPENSES_CATEGORIES = h.extract_categories(st.session_state.CATEGORIES_BODY.get(c.NON_EXPENSES_PARENT_CATEGORY_KEY, {}))

    # existing issuers
    response = c.s3.list_objects_v2(Bucket=c.S3_BUCKET, Prefix=f"{st.session_state.STATEMENTS_FOLDER}/", Delimiter="/")

    # CommonPrefixes structure looks like: 
    # [{"Prefix":"mqmotiwala@gmail.com/statements/amazon/"}], so
    # .split('/')[-1] is an empty string
    # .split('/')[-2] is the statement issuer
    st.session_state.EXISTING_ISSUERS = [prefix["Prefix"].split("/")[-2] for prefix in response.get("CommonPrefixes", [])]

    