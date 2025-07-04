import config as c
import streamlit as st
import utils.helpers as h

def set_app_wide_styling():
    """
    Applies specific styling choices app wide.
    """
    
    # enforce color styling on multiselect widgets
    # this still respects the base styling for disabled multiselect widgets
    MULTISELECT_COLOR = "#F6E8BE"
    css = f"""
    <style>
        .stMultiSelect span[data-baseweb="tag"]:not([aria-disabled="true"]) {{
            background-color: {MULTISELECT_COLOR} !important;
            color: black !important;
        }}
    </style>
    """

    # iframes with height=0 must have `display: none` styling
    # see utils.helpers.switch_to_tab() for context
    css += """
    <style>
        .element-container:has(iframe[height="0"]) {
            display: none;
        }
    </style>
    """

    # right align logout button
    css += f"""
    <style>
        div.st-key-{c.LOGOUT_BUTTON_KEY_NAME} div.stButton {{
            display: flex;            
            justify-content: flex-end;
        }}
    </style>
    """

    css += f"""
    <style>
      .is-badge {{
        background-color: {h.hex_to_rgba(c.BUDGET_BUDDY_COLOR)};
        color: #505050 !important;
      }}
    </style>
    """

    st.html(css)

def highlight(text, background=c.BUDGET_BUDDY_COLOR, color="black", font_weight="normal", font_size="inherit", tilt=0):
    """
    Returns an HTML <span> with inline styles for highlighting text in Streamlit markdown.
    """
    return (
        f"<span style='"
        f"background-color:{background}; "
        f"color:{color}; "
        f"font-weight:{font_weight}; "
        f"font-size:{font_size}; "
        f"transform: rotate({tilt}deg); "
        f"border-radius: 6px; "
        f"display: inline-block; "
        f"padding: 2px 6px;'>"
        f"{text}</span>"
    )

def center(text, margin="1em 0"):
    """
    Returns an HTML <div> with inline styles to center-align the text.
    """
    return f"<div style='text-align: center; margin: {margin};'>{text}</div>"

def markdown(text):
    """
    wrapper on st.markdown() to allow custom_css
    """

    return st.markdown(text, unsafe_allow_html=True)

def divider(color=c.BUDGET_BUDDY_COLOR, thickness="1px", margin="1.5em 0"):
    """
    creates a divider styled with custom color, thickness, and margin.
    styled to match Streamlit dividers
    """

    html_text = f"<hr style='border: none; border-top: {thickness} solid {color}; margin: {margin};' />"
    return markdown(html_text)

def underline(text, color=c.BUDGET_BUDDY_COLOR, thickness="2px", offset="2px", style="solid"):
    """
    Returns an HTML <span> with an underline styling, defaults to using text-decoration-style: solid.
    """

    if not style in ["solid", "double", "dotted", "dashed", "wavy"]:
        raise ValueError("Invalid style")
    
    return (
        f"<span style='"
        f"text-decoration: underline; "
        f"text-decoration-color: {color}; "
        f"text-decoration-style: {style}; "
        f"text-underline-offset: {offset}; "
        f"text-decoration-thickness: {thickness};"
        f"'>{text}</span>"
    )

def header(text, lvl=1, underline_text=True):
    """
    wrapper on st.markdown to shorthand different markdown levels

    args:
        lvl (int): Markdown level to use. Must be valid.
        underline_text (bool): whether or not to underline text
    """

    if not lvl in range(1, 7):
        raise ValueError("Markdown levels must be between 1 to 6")
    
    if underline_text:
        return markdown(f"{"#"*lvl} {underline(text)}")
    else:
        return st.markdown(f"{"#"*lvl} {text}")
    
def empty_space():
    """
    Returns an HTML <span> with a squiggly underline using text-decoration-style: wavy.
    """

    st.markdown("")
    st.markdown("")

def remove_streamlit_menu():
    """
    Removes the Streamlit menu items

    Note: this function has low utility because Streamlit offers a native way of achieving this effect by setting toolbarMode value in config.toml
    See docs: https://docs.streamlit.io/develop/api-reference/configuration/config.toml
    """
    style_text = """
        <style>
            #MainMenu, footer, header {visibility: hidden;}
        </style>
    """
    st.markdown(style_text, unsafe_allow_html=True)

