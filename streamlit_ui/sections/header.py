import config as c
import streamlit as st
import utils.auth as a
import utils.css as css

def show_header():
    _, col2 = st.columns([10, 1])
    with col2:
        if st.button("Logout"):
            a.logout()
    
    st.title(f"👋 Hi {st.session_state.user.first_name}! I'm your Budget Buddy {c.BUDGET_BUDDY_ICON}")
    css.markdown(f"Let's get started — managing your finances just got {css.underline('simple and stress-free')}.")
