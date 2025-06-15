import streamlit as st
import utils.helpers as h
import config_general as c
import utils.css as css
from streamlit_player import st_player

def show_landing():
    st.title(f"👋 Hi! I'm your Budget Buddy {c.BUDGET_BUDDY_ICON}")
    css.markdown(f"##### Together, we'll make tracking your finances {css.highlight("simple and stress free", tilt=1.5)}")
    
    explanation_text = f"""
    I'll help you bring all your accounts together into one clear view,  
    so you can keep tabs on your finances and get back to doing the things you *{css.underline("actually")}* enjoy.
    """
    
    css.markdown(f"{(explanation_text)}")
    
    st_player("https://www.youtube.com/watch?v=fEscsUoQc70")
