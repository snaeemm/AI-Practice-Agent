import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat
from components.branding import render_page_header_logo
from styles import apply_custom_styles
from auth import require_auth

st.set_page_config(page_title="Granite", page_icon="⚙️")

apply_custom_styles()

if not require_auth():
    st.stop()

render_page_header_logo(max_width=300)

session = render_sidebar()

if session:
    render_chat(session)
else:
    st.error("Failed to load session")