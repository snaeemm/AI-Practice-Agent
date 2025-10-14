import streamlit as st


def apply_custom_styles():
    st.markdown("""<style>
/* --- Main Background --- */
.main, .stApp {
    background: linear-gradient(135deg, #0a1828 0%, #102d47 50%, #0a1828 100%) !important;
    color: #ffffff !important;
}

[data-testid="stHeader"] {
    background: linear-gradient(135deg, #0c223b 0%, #123a61 50%, #1a527f 100%) !important;
    border-bottom: 1px solid rgba(120,180,255,0.2);
    color: #ffffff !important;
}

.stMarkdown p,
.stMarkdown div,
.stMarkdown span,
.stMarkdown li,
.stMarkdown h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d243d 0%, #132f4d 60%, #153b5b 100%) !important;
    color: #ffffff !important;
    border-right: 1px solid rgba(0, 150, 255, 0.2);
    padding: 1rem !important;
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] label {
    color: #dbe9ff !important;
    font-weight: 500;
    margin-bottom: 0.25rem !important;
}
section[data-testid="stSidebar"] label + div {
    margin-bottom: 0.75rem !important;
}

section[data-testid="stSidebar"] div[data-testid*="stInput"] {
    width: 100% !important;
    min-width: 100% !important;
    max-width: none !important;
}
section[data-testid="stSidebar"] div[data-baseweb="input"] {
    width: 100% !important;
}

section[data-testid="stSidebar"] div[data-baseweb="input"] div[data-baseweb="baseinput"] {
    background-color: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    color: #1a1a1a !important;
    width: 100% !important;
}

section[data-testid="stSidebar"] input[type="text"],
section[data-testid="stSidebar"] select,
section[data-testid="stSidebar"] textarea {
    background-color: transparent !important;
    color: #1a1a1a !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.4rem 0.6rem !important;
    width: 100% !important;
}

section[data-testid="stSidebar"] input::placeholder {
    color: rgba(50, 50, 50, 0.7) !important;
}

section[data-testid="stSidebar"] details[open] code {
    background-color: rgba(20, 65, 110, 0.95) !important;
    color: #ffffff !important;
    padding: 2px 5px !important;
    border-radius: 4px !important;
    white-space: normal !important;
    word-break: break-all !important;
    overflow-wrap: break-word !important;
    display: inline-block !important;
    max-width: 100% !important;
}

section[data-testid="stSidebar"] details[open] code span {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] div[data-baseweb="input"] {
    background-color: rgba(29, 77, 127, 0.5) !important;
    border: 1px solid #2f73b1 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    min-height: 2.5rem !important;
    padding: 0 0.5rem !important;
}

section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"]:has(+ div[data-testid="stSelectbox"]) {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
    font-weight: 600 !important;
    color: #99ccff !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] div[data-baseweb="input"]:focus-within {
    border-color: #2f73b1 !important;
    box-shadow: none !important;
    outline: none !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] div[data-baseweb="input"] input {
    color: #ffffff !important;
}

[data-testid="stStatusContainer"] {
    background-color: #1a527f !important;
    border: 1px solid #2f73b1 !important;
    border-radius: 8px !important;
}

[data-testid="stStatusContainer"] * {
    color: #1a1a1a !important;
}
[data-testid="stStatusContainer"] svg path {
    fill: #1a1a1a !important;
}

[data-testid="stExpander"] [data-testid="stExpanderHeader"] {
    background-color: #16385c !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

[data-testid="stExpander"] [data-testid="stExpanderHeader"]:hover {
    background-color: #1d4d7f !important;
    color: #ffffff !important;
}

[data-testid="stExpander"] [data-testid="stExpanderContent"] {
    background-color: rgba(10,25,40,0.8) !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 0 0 8px 8px !important;
    border: 1px solid #16385c;
    border-top: none;
}

[data-testid="stChatMessageContent"] {
    background-color: rgba(255,255,255,0.05) !important;
    border-radius: 10px !important;
    padding: 10px 16px !important;
    color: #ffffff !important;
}
[data-testid="stChatMessageContent"] code {
    background-color: rgba(255,255,255,0.1) !important;
    color: #a0e6ff !important;
}

.stTabs [data-baseweb="tab"] {
    background-color: #16385c;
    color: #ffffff !important;
    border-radius: 6px 6px 0 0;
    border: none;
    font-weight: 500;
    min-width: 120px !important;
    padding: 0.6rem 1.2rem !important;
    text-align: center !important;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #1d4d7f;
    color: #ffffff !important;
}
.stTabs [aria-selected="true"] {
    background-color: #1b4f77 !important;
    color: #ffffff !important;
    border-bottom: 2px solid #66b3ff;
}

button, section[data-testid="stSidebar"] button {
    background-color: #1d4d7f !important;
    border: 1px solid #2f73b1 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}
button:hover {
    background-color: #2a6fa3 !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] details summary {
    background-color: rgba(29,77,127,0.9) !important;
    color: #ffffff !important;
    font-weight: 500;
    border-radius: 6px !important;
    padding: 0.5rem 0.75rem !important;
    margin-bottom: 0.25rem !important;
}

section[data-testid="stSidebar"] details[open] {
    background-color: rgba(10,25,40,0.8) !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 6px !important;
}

section[data-testid="stSidebar"] details[open] button {
    margin-top: 0.75rem !important;
}

section[data-testid="stSidebar"] div[data-testid="stInfo"] {
    background-color: rgba(29,77,127,0.9) !important;
    padding: 0.6rem 0.75rem !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    margin-bottom: 0.5rem !important;
}

section[data-testid="stSidebar"] hr {
    border-top: 1px solid rgba(255,255,255,0.15) !important;
    margin: 0.5rem 0 !important;
}

[data-testid="stChatInput"] {
    padding-bottom: 0rem !important;
    margin-bottom: -2rem !important;
}

.main .block-container {
    padding-bottom: 1rem !important;
    min-height: 80vh !important;
    display: flex !important;
    flex-direction: column !important;
}

.main .block-container > div:first-child {
    flex-grow: 1 !important;
}

.thinking-box {
    background: rgba(255,255,255,0.05) !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    margin: 4px 0 !important;
    font-size: 0.9em !important;
    color: #aaa !important;
}

.thinking-box + div p,
.thinking-box + div {
    font-size: 0.9em !important;
    color: #ddd !important;
    margin-left: 1.5em !important;
    padding: 4px 0 !important;
}

</style>""", unsafe_allow_html=True)
