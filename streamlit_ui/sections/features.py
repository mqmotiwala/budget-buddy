import config as c
import streamlit as st
import utils.css as css

def show_features():
    css.divider()

    with st.container():
        st.subheader("All transactions from all accounts — in one place.")
        css.markdown(
            f"""Do you juggle multiple jobs, freelance gigs, or credit cards?  
            No problem, {css.underline("Budget Buddy automatically consolidates everything")}."""
        )
        st.image(f"{c.ASSETS_PATH}/feature_001.png")

    css.empty_space()

    with st.container():
        st.subheader("Visualize the Flow of Money")
        css.markdown(
            f"""{css.underline("No more uncertainty", style="solid")}, get a crystal-clear picture of your finances.  
            Explore intuitive dashboards that show you everything at a glance 
            *and* dive deep when you need to."""
        )

        st.image(f"{c.ASSETS_PATH}/feature_002.png")

    css.empty_space()

    with st.container():
        st.subheader("Smart Categorization")
        css.markdown(
            f"""Everyone tracks things differently. Categorize your expenses to match *{css.underline("you")}*."""    
        )
        st.image(f"{c.ASSETS_PATH}/feature_002.png")