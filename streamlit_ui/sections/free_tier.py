import config as c
import streamlit as st
import utils.css as css

PREMIUM_PRICE = 19.99
FREE_TIER_NOTICE_TEXT = f"""
Heads up, the free tier is excellent for exploring core budgeting features at no cost.       
Upgrade to Premium to process unlimited statements and custom categories.
"""

def show_free_tier_notice():
    with st.expander(label="Psst! You're on the free tier."):
        st.warning(FREE_TIER_NOTICE_TEXT)

        st.button("Get Premium")