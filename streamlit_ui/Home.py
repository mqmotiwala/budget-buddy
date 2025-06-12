
import config as c
import streamlit as st
import utils.helpers as h

from sections.header import show_header 
from sections.upload import show_upload
from sections.landing import show_landing 
from sections.analytics import show_analytics
from sections.categorize import show_categorize

st.set_page_config(**c.STREAMLIT_PAGE_CONFIG)

if "auth" not in st.session_state:
    show_landing()

else:
    # initialize master data for session, if needed
    # the session state key is used to access master across all app logic
    # its forcefully reloaded when required by invoking h.load_master()
    if "master" not in st.session_state:
        st.session_state.master = h.load_master()

    show_header()
    show_upload()
    show_categorize()
    show_analytics()