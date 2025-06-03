import streamlit as st

# AWS secrets
AWS_ACCESS_KEY_ID = st.secrets["aws"]["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = st.secrets["aws"]["AWS_REGION"]

# Expense categories
CATEGORIES = [
    "Groceries", 
    "Dining", 
    "Transport", 
    "Travel", 
    "Utilities",
    "Subscriptions", 
    "Healthcare", 
    "Entertainment", 
    "Other"
]

