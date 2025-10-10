import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat

st.set_page_config(
    page_title="GRANITE - Bid Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* --- Main Background --- */
.main, .stApp {
    background: linear-gradient(135deg, #0a1828 0%, #102d47 50%, #0a1828 100%) !important;
    color: #ffffff !important;  /* Default app text to white */
}

/* Header gradient text */
[data-testid="stHeader"] {
    background: linear-gradient(135deg, #0c223b 0%, #123a61 50%, #1a527f 100%) !important;
    border-bottom: 1px solid rgba(120,180,255,0.2);
    color: #ffffff !important;  /* header text white */
}

/* All markdown / text content */
.stMarkdown p, 
.stMarkdown div, 
.stMarkdown span, 
.stMarkdown li, 
.stMarkdown h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;  /* white text everywhere */
}

/* Sidebar background and base styles */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d243d 0%, #132f4d 60%, #153b5b 100%) !important;
    color: #ffffff !important;
    border-right: 1px solid rgba(0, 150, 255, 0.2);
    padding: 1rem !important;
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important; /* all sidebar text white */
}

/* Sidebar labels (Username, Session name) */
section[data-testid="stSidebar"] label {
    color: #dbe9ff !important;
    font-weight: 500;
    margin-bottom: 0.25rem !important;
}
/* NEW: Add vertical space after labels/inputs */
section[data-testid="stSidebar"] label + div {
    margin-bottom: 0.75rem !important; 
}


/* ---------------------------------------------------------------------- */
/* --- INPUTS FIX: ADOPTING THE LIGHTER 'SESSION NAME' STYLE GLOBALLY --- */
/* ---------------------------------------------------------------------- */

/* FIX 1: Ensure the outermost Streamlit container is full width */
section[data-testid="stSidebar"] div[data-testid*="stInput"] {
    width: 100% !important; 
    min-width: 100% !important;
    max-width: none !important;
}
/* FIX 2: Ensure the intermediate container is also full width (CRITICAL for size fix) */
section[data-testid="stSidebar"] div[data-baseweb="input"] {
    width: 100% !important;
}

/* Target the container DIV (which holds the light background color) */
section[data-testid="stSidebar"] div[data-baseweb="input"] div[data-baseweb="baseinput"] {
    background-color: rgba(255, 255, 255, 0.9) !important; /* Lighter/solid background (The preferred style) */
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    color: #1a1a1a !important; /* Forces dark text on the input container */
    width: 100% !important; /* Ensures the input background is full width */
}

/* Target the actual input element (text, select, textarea) */
section[data-testid="stSidebar"] input[type="text"],
section[data-testid="stSidebar"] select,
section[data-testid="stSidebar"] textarea {
    background-color: transparent !important; /* Make transparent to show container background */
    color: #1a1a1a !important; /* Dark text for readability on light background */
    border: none !important;
    border-radius: 6px !important;
    padding: 0.4rem 0.6rem !important;
    width: 100% !important;
}


/* Placeholder text color (should be dark/gray on the light background) */
section[data-testid="stSidebar"] input::placeholder {
    color: rgba(50, 50, 50, 0.7) !important; 
}


/* *** TARGETED FIX for Session ID (which is an inline code block) *** */
/* Target the inline code (the dark background box) and fix the font color and clip issue */
section[data-testid="stSidebar"] details[open] code {
    /* VISIBILITY FIX: Force light text on dark background */
    background-color: rgba(20, 65, 110, 0.95) !important; /* Slightly darker background for contrast */
    color: #ffffff !important; /* Set to pure white for maximum visibility - this is the fallback */
    padding: 2px 5px !important;
    border-radius: 4px !important;
    /* RESPONSIVE FIX: Allow code to wrap/shrink with sidebar */
    white-space: normal !important;
    word-break: break-all !important;
    overflow-wrap: break-word !important;
    display: inline-block !important;
    max-width: 100% !important; /* Constrain to sidebar width */
}

/* Target the span inside the code block for maximum specificity */
section[data-testid="stSidebar"] details[open] code span {
    color: #ffffff !important; /* FINAL ATTEMPT to force white color on the text itself */
}


/* ---------------------------------------------------------------------- */
/* --- SELECT SESSION / SELECTBOX FIX --- */
/* ---------------------------------------------------------------------- */

/* Fixes the input box background (the main container for the dropdown) */
section[data-testid="stSidebar"] [data-baseweb="select"] div[data-baseweb="input"] {
    background-color: rgba(29, 77, 127, 0.5) !important; /* Keep this element dark blue */
    border: 1px solid #2f73b1 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    min-height: 2.5rem !important;
    padding: 0 0.5rem !important;
}

/* NEW LAYOUT FIX: Target and push down the text showing the current session to give it space */
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"]:has(+ div[data-testid="stSelectbox"]) {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
    /* Optional: Make the current session text bolder/more distinct */
    font-weight: 600 !important;
    color: #99ccff !important;
}

/* Removes the gray element that displays the selected value (for the dark select box) */
section[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    background-color: transparent !important; 
    border: none !important;
    box-shadow: none !important;
}

/* Removes the focus/error border from the selectbox */
section[data-testid="stSidebar"] [data-baseweb="select"] div[data-baseweb="input"]:focus-within {
    border-color: #2f73b1 !important; 
    box-shadow: none !important;
    outline: none !important;
}

/* Ensures the text inside the input container is white */
section[data-testid="stSidebar"] [data-baseweb="select"] div[data-baseweb="input"] input {
    color: #ffffff !important;
}


/* ---------------------------------------------------------------------- */
/* --- GENERAL STYLES (Expander, Buttons, Chat, Status) --- */
/* ---------------------------------------------------------------------- */

/* Status/Progress Container (Agent is processing...) */
[data-testid="stStatusContainer"] {
    /* Keep the custom dark background for the container box */
    background-color: #1a527f !important;
    border: 1px solid #2f73b1 !important;
    border-radius: 8px !important;
}

/* FIX: Force dark text and spinner for visibility against any potential light inner background */
[data-testid="stStatusContainer"] * { 
    color: #1a1a1a !important; /* Force dark text */
}
/* Target the circular progress bar (spinner) elements and force dark fill */
[data-testid="stStatusContainer"] svg path {
    fill: #1a1a1a !important; /* Dark color for the spinner element itself */
}


/* Expander header in the main content area (Thinking steps) */
[data-testid="stExpander"] [data-testid="stExpanderHeader"] {
    background-color: #16385c !important; /* Slightly darker than status */
    color: #ffffff !important;
    border-radius: 8px !important;
}

[data-testid="stExpander"] [data-testid="stExpanderHeader"]:hover {
    background-color: #1d4d7f !important; /* Darken on hover */
    color: #ffffff !important;
}

/* Ensure content background is also dark themed for the expander */
[data-testid="stExpander"] [data-testid="stExpanderContent"] {
    background-color: rgba(10,25,40,0.8) !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 0 0 8px 8px !important;
    border: 1px solid #16385c;
    border-top: none;
}


/* Chat messages */
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

/* Tabs */
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

/* Buttons */
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


/* Sidebar Expander header */
section[data-testid="stSidebar"] details summary {
    background-color: rgba(29,77,127,0.9) !important;
    color: #ffffff !important;
    font-weight: 500;
    border-radius: 6px !important;
    padding: 0.5rem 0.75rem !important;
    margin-bottom: 0.25rem !important;
}

/* Sidebar Expander content */
section[data-testid="stSidebar"] details[open] {
    background-color: rgba(10,25,40,0.8) !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 6px !important;
}

/* Buttons inside expander */
section[data-testid="stSidebar"] details[open] button {
    margin-top: 0.75rem !important; /* Increased space above button in expander */
}

/* Info boxes (e.g., "No existing sessions") */
section[data-testid="stSidebar"] div[data-testid="stInfo"] {
    background-color: rgba(29,77,127,0.9) !important;
    padding: 0.6rem 0.75rem !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    margin-bottom: 0.5rem !important;
}

/* Dividers */
section[data-testid="stSidebar"] hr {
    border-top: 1px solid rgba(255,255,255,0.15) !important;
    margin: 0.5rem 0 !important;
}

/* 1. Reduce the space/padding below the Chat Input */
[data-testid="stChatInput"] {
    /* Set padding to zero if you want the absolute minimum space */
    padding-bottom: 0rem !important;
    
    /* Use a negative margin to pull the content/footer up and effectively reduce the total space */
    margin-bottom: -2rem !important; 
}

/* 2. Reduce the space/padding at the bottom of the main content area */
.main .block-container {
    /* Set the bottom padding to a very small value, or 0. */
    padding-bottom: 1rem !important;
    min-height: 80vh !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Push content to fill space so buttons stay near bottom */
.main .block-container > div:first-child {
    flex-grow: 1 !important;
}

/* Thinking box styling */
.thinking-box {
    background: rgba(255,255,255,0.05) !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    margin: 4px 0 !important;
    font-size: 0.9em !important;
    color: #aaa !important;
}

/* Thinking content styling - allows markdown to render */
.thinking-box + div p,
.thinking-box + div {
    font-size: 0.9em !important;
    color: #ddd !important;
    margin-left: 1.5em !important;
    padding: 4px 0 !important;
}

</style>

""", unsafe_allow_html=True)



# --- APP CONTENT ---
st.title("GRANITE - Bid Assistant")

session = render_sidebar()

if session:
    render_chat(session)
else:
    st.error("Failed to load session")
