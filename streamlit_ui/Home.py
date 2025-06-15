
import streamlit as st
import utils.helpers as h
import config_user as u
import config_general as c

from sections.faqs import show_faqs 
from sections.header import show_header 
from sections.upload import show_upload
from sections.landing import show_landing 
from sections.features import show_features 
from sections.analytics import show_analytics
from sections.categorize import show_categorize

if "auth" not in st.session_state:
    st.set_page_config(**c.STREAMLIT_LANDING_PAGE_CONFIG)
    show_landing()
    h.get_auth(unique_key = "1")
    show_features()
    show_faqs()
    h.get_auth(unique_key = "2")

else:
    u.load_user_config()

    # initialize master data for session, if needed
    # the session state key is used to access master across all app logic
    # its forcefully reloaded when required by invoking h.load_master()
    if "master" not in st.session_state:
        st.session_state.master = h.load_master()

    # setting page config here as opposed to at the top of the conditional block
    # allows Streamlit to switch between centered -> wide layout view more seamlessly
    st.set_page_config(**c.STREAMLIT_GENERAL_PAGE_CONFIG)
    show_header()
    show_upload()
    show_categorize()
    show_analytics()