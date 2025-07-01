
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
    css.set_app_wide_styling()

    show_header()
    if not st.session_state.user.is_premium: 
        show_free_tier_notice()

    tabs = st.tabs(["Budget Buddy", "Customize Categories", "Statement Issuers", "Get Premium", "Privacy Policy", "Communications Hub"])
    with tabs[0]:
        show_upload()
        show_categorize()
        show_analytics()

    with tabs[1]:
        show_customize_categories()

    with tabs[2]:
        from streamlit.components.v1 import html

        def switch_tabs_programmatically(button_text="Get Premium", tab_text="Get Premium"):
            html(f"""<script>
            (() => {{
                
                let button = [...window.parent.document.querySelectorAll("button")].filter(button => {{
                    console.log(">>>", button.innerText)
                    return button.innerText.includes("{button_text}")
                }})[0];

                if(button) {{
                    button.onclick = () => {{
                        var tabGroup = window.parent.document.getElementsByClassName("stTabs")[0]
                        const tabButton = [...tabGroup.querySelectorAll("button")].filter(button => {{
                            return button.innerText.includes("{tab_text}")
                        }})[0];
                        if(tabButton) {{
                            tabButton.click();
                        }} else {{
                            console.log("tab button {tab_text} not found")
                        }}
                    }}
                }} else {{
                    console.log("button not found: {button_text}")
                }}
            }})();
            </script>""", height=0)

        last_row = st.container()
        last_row.button("Get Premium", key="Get Premium")
        switch_tabs_programmatically()

    with tabs[3]:
        import streamlit as st
        from streamlit.components.v1 import html

        def switch_tab_by_index(index: int):
            js = f"""
            <script>
            (function clickTabByIndex() {{
                // Try different selectors
                var selectors = [
                    'button[role="tab"]',
                    'button[data-baseweb="tab"]',
                    'button[data-testid="stWidgetTab"]',
                    '.stTabs button'
                ];

                for (var s = 0; s < selectors.length; s++) {{
                    var tabs = window.parent.document.querySelectorAll(selectors[s]);
                    if (tabs.length > {index}) {{
                        tabs[{index}].click();
                        return true;
                    }}
                }}
                return false;
            }})();

            // Also try with delays in case initial render hasn’t completed
            setTimeout(clickTabByIndex, 300);
            setTimeout(clickTabByIndex, 1000);
            </script>
            """
            html(js, height=0)

        if st.button("Go to Tab B"):
            switch_tab_by_index(1)
