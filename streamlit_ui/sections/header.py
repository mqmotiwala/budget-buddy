import streamlit as st
import utils.helpers as h

def show_header():
    _, col2 = st.columns([10, 1])
    with col2:
        if st.button("Logout"):
            h.logout()
    
    st.title(f"👋 Hi {st.session_state.user.first_name}! I'm your Budget Buddy")

    subtitle = """Hand me your statements and I'll help you gain insights into where your money goes.  
    Lets make tracking your finances *simple and stress-free.*
    """
    st.markdown(subtitle)