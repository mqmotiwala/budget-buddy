
import streamlit as st
import utils.helpers as h
import config_user as u
import config_general as c

from sections.faqs import show_faqs 
from sections.header import show_header 
from sections.upload import show_upload
from sections.landing import show_landing 
from sections.analytics import show_analytics
from sections.categorize import show_categorize

if "auth" not in st.session_state:
    st.set_page_config(**c.STREAMLIT_LANDING_PAGE_CONFIG)
    show_landing()
    show_faqs()

else:
    st.set_page_config(**c.STREAMLIT_GENERAL_PAGE_CONFIG)
    u.load_user_config()

    # initialize master data for session, if needed
    # the session state key is used to access master across all app logic
    # its forcefully reloaded when required by invoking h.load_master()
    if "master" not in st.session_state:
        st.session_state.master = h.load_master()

    show_header()
    show_upload()
    show_categorize()
    show_analytics()