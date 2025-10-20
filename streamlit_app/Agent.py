import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat
from styles import apply_custom_styles
from auth import require_auth

st.set_page_config(page_title="Granetic", page_icon="⚙️")

apply_custom_styles()

if not require_auth():
    st.stop()

st.title("⚙️ Granetic")

session = render_sidebar()

if session:
    render_chat(session)
else:
    st.error("Failed to load session")