import streamlit as st
import config_general as c

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

def empty_space():
    """
    Returns an HTML <span> with a squiggly underline using text-decoration-style: wavy.
    """

    st.markdown("")
    st.markdown("")
