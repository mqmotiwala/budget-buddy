import config as c
import streamlit as st
import utils.auth as a
import utils.css as css

def show_header():
    cols = st.columns([0.9, 0.1])
    with cols[0]:
        st.title(f"👋 Hi {st.session_state.user.first_name}! I'm your Budget Buddy {c.BUDGET_BUDDY_ICON}")
    with cols[1]:
        st.button("Logout", key=c.LOGOUT_BUTTON_KEY_NAME)
        
    css.markdown(f"Let's get started — managing your finances just got {css.underline('simple and stress-free')}.")