import streamlit as st

def show_header():
    _, col2 = st.columns([10, 1])
    with col2:
        if st.button("Logout"):
            del st.session_state["auth"]
            del st.session_state["token"]

            # rerun the app to reflect the new state
            st.rerun()
    
    st.title("👋 Hi! I'm your Budget Buddy")

    subtitle = """Hand me your statements and I'll help you gain insights into where your money goes.  
    Lets make tracking your finances *simple and stress-free.*
    """
    st.markdown(subtitle)