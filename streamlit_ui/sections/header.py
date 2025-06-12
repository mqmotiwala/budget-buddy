import streamlit as st

def show_header():
    st.set_page_config(page_title="Budget Buddy", layout="wide")
    st.title(f"👋 Hi! I'm your Budget Buddy")

    subtitle = """Hand me your statements and I'll help you gain insights into where your money goes.  
    Lets make tracking your finances *simple and stress-free.*
    """
    st.markdown(subtitle)