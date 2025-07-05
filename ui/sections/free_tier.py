import config as c
import streamlit as st
import utils.helpers as h

def show_free_tier_notice():
    # move into function to ensure st.session_state.user is initialized 
    FREE_TIER_NOTICE_TEXT = f"""
    Heads up, the free tier is excellent for exploring core features at no cost.  
    Want more? Upgrade to Premium!
    """

    with st.expander(label="Psst! You're on the free tier.", expanded=True):
        st.warning(FREE_TIER_NOTICE_TEXT)

        if st.button("Explore Premium"):
            h.switch_to_tab(c.GET_PREMIUM_TAB_NAME)