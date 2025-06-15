import streamlit as st
import utils.css as css
import utils.helpers as h
import config_general as c

def show_header():
    _, col2 = st.columns([10, 1])
    with col2:
        if st.button("Logout"):
            h.logout()
    
    st.title(f"👋 Hi {st.session_state.user.first_name}! I'm your Budget Buddy {c.BUDGET_BUDDY_ICON}")
    st.markdown(f"Let's make tracking your finances {css.highlight("simple and stress free")}.", unsafe_allow_html=True)
