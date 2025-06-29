import config as c
import streamlit as st

PREMIUM_PRICE = 19.99
num_remaining_uploads = c.MAX_FREE_STATEMENT_UPLOADS - getattr(st.session_state.user, 'num_uploads', 0)
FREE_TIER_NOTICE_TEXT = f"""
Heads up, the free tier is excellent for exploring core budgeting features at no cost.       
Upgrade to Premium to process unlimited statements and custom categories.  

{f"You can process {num_remaining_uploads} more statements." if num_remaining_uploads > 0 else "You've hit the free tier statements processing limit."}
"""

def show_free_tier_notice():
    with st.expander(label="Psst! You're on the free tier."):
        st.warning(FREE_TIER_NOTICE_TEXT)

        st.button("Get Premium")