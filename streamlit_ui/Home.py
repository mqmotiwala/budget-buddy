
import config as c
import streamlit as st
import utils.auth as a
import utils.css as css

from sections.faqs import show_faqs 
from sections.header import show_header 
from sections.upload import show_upload
from sections.landing import show_landing 
from sections.features import show_features 
from sections.analytics import show_analytics
from sections.categorize import show_categorize
from sections.free_tier import show_free_tier_notice
from sections.customize_categories import show_customize_categories

if "auth" not in st.session_state:
    st.set_page_config(**c.STREAMLIT_LANDING_PAGE_CONFIG)

    show_landing()
    a.get_auth(unique_key=1)
    show_features()
    show_faqs()
    a.get_auth(unique_key=2)

else:
    # initialize master data for session, if needed
    # the session state key is used to access master across all app logic
    # its forcefully reloaded when required by invoking h.load_master()
    if not hasattr(st.session_state.user, "master"):
        st.session_state.user.load_master()

    # setting page config here as opposed to at the top of the conditional block
    # allows Streamlit to switch between centered -> wide layout view more seamlessly
    st.set_page_config(**c.STREAMLIT_GENERAL_PAGE_CONFIG)

    show_header()
    if not st.session_state.user.is_premium: 
        show_free_tier_notice()

    tabs = st.tabs(["Budget Buddy", "Customize Categories"])
    with tabs[0]:
        show_upload()
        show_categorize()
        show_analytics()

    with tabs[1]:
        show_customize_categories()