import config as c
import streamlit as st
import utils.css as css

PREMIUM_PRICE = 19.99
FREE_TIER_NOTICE_TEXT = f"""
You're on the free tier.  
Upgrade to Premium to process unlimited statements and custom categories.
"""

def show_free_tier_notice():
    st.warning(FREE_TIER_NOTICE_TEXT)
    st.button("Get Premium")

    css.divider()