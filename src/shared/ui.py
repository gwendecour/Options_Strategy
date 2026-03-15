import streamlit as st
import os

def set_theme_css():
    """Injects static Dark Mode CSS."""
    st.session_state.theme = 'dark'
    
    css = """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #0e1117;
            color: #fafafa;
        }
        [data-testid="stHeader"] {
            background-color: rgba(14, 17, 23, 0.0);
        }
        /* Style for radio buttons as pill buttons */
        div[role="radiogroup"] label[data-baseweb="radio"] {
            background-color: rgba(150, 150, 150, 0.1) !important;
            border: 1px solid rgba(150, 150, 150, 0.2) !important;
            border-radius: 8px !important;
            margin-right: 10px !important;
            padding: 4px 12px !important;
            cursor: pointer !important;
            transition: all 0.2s ease;
        }
        div[role="radiogroup"] label[data-baseweb="radio"]:hover {
            background-color: rgba(150, 150, 150, 0.25) !important;
        }
        div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
            background-color: #475569 !important;
            border: 1px solid #334155 !important;
        }
        div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
            display: none !important;
        }
        div[role="radiogroup"] label p {
            font-size: 0.9rem !important;
            margin-bottom: 0px !important;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header():
    """
    Renders the header for the Strategy Lab.
    """
    set_theme_css()
    
    col1, col2 = st.columns([1, 10], vertical_alignment="center")
    with col1:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=50)
    with col2:
        st.title("Options Strategy")
    
    st.divider()
