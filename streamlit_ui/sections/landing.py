import streamlit as st
import utils.helpers as h

def show_landing():
    st.title("👋 Hi! I'm your Budget Buddy")
    subtitle = "Lets make tracking your finances *simple and stress-free.*"
    st.markdown(subtitle)

    h.get_auth()

    st.divider()

    st.markdown("## 📖 Frequently Asked Questions")

    with st.expander("What is Budget Buddy?"):
        st.write("Budget Buddy is a personal finance assistant that helps you analyze your spending by uploading your bank statements. Think of it as Mint, but simpler and more focused on clarity.")

    with st.expander("Is my data secure?"):
        st.write("Yes. Your data is processed in memory and never shared. In the future, we'll offer encrypted cloud sync with full user control.")



