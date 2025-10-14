import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat
from styles import apply_custom_styles
apply_custom_styles()
import streamlit as st

st.set_page_config(page_title="My Cool App", page_icon="🚀")

st.title("GRANITE - Bid Assistant")

session = render_sidebar()

if session:
    render_chat(session)
else:
    st.error("Failed to load session")