import streamlit as st


def apply_custom_styles():
    st.markdown("""<style>
/* --- Font Import --- */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

/* --- Material Icons Support (MUST come before global font) --- */
.material-icons,
.material-icons-outlined,
.material-icons-round,
.material-icons-sharp,
.material-icons-two-tone,
[class*="material-icons"],
span[class*="material"],
i[class*="material"] {
    font-family: 'Material Icons' !important;
    font-weight: normal !important;
    font-style: normal !important;
    font-size: 24px !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-smoothing: antialiased !important;
    text-rendering: optimizeLegibility !important;
    -moz-osx-font-smoothing: grayscale !important;
    font-feature-settings: 'liga' !important;
}

/* --- Global Font Application --- */
body, html {
    font-family: 'Montserrat', sans-serif;
}

/* Hide text fallback for Material Icons when font is loading */
.material-icons:not(:empty),
button .material-icons {
    text-indent: 0 !important;
    overflow: visible !important;
}

/* Fix Streamlit button icons on mobile */
button span[class*="material"] {
    font-family: 'Material Icons' !important;
}

/* Hide the literal text when Material Icons fail to render */
*:not(input):not(textarea) {
    text-rendering: optimizeLegibility;
}

/* Force Material Icons rendering for common icon containers */
[class*="icon"],
[class*="Icon"],
span[class*="st"] {
    -webkit-font-feature-settings: 'liga';
    -moz-font-feature-settings: 'liga';
    font-feature-settings: 'liga';
}

/* --- High Quality Image Rendering --- */
img {
    image-rendering: -webkit-optimize-contrast !important;
    image-rendering: crisp-edges !important;
    -ms-interpolation-mode: nearest-neighbor !important;
}

/* Override for logos - smooth high quality rendering */
[data-testid="stImage"] img,
.stImage img {
    image-rendering: high-quality !important;
    image-rendering: -webkit-optimize-contrast !important;
    -ms-interpolation-mode: bicubic !important;
    transition: all 0.3s ease !important;
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3)) !important;
}

[data-testid="stImage"] img:hover,
.stImage img:hover {
    transform: scale(1.02) !important;
    filter: drop-shadow(0 8px 16px rgba(102, 179, 255, 0.4)) !important;
}

/* --- Main Background --- */
.main, .stApp {
    background: linear-gradient(135deg, #0a1828 0%, #102d47 50%, #0a1828 100%) !important;
    color: #ffffff !important;
    font-family: 'Montserrat', sans-serif !important;
}

[data-testid="stHeader"] {
    background: linear-gradient(135deg, #0c223b 0%, #123a61 50%, #1a527f 100%) !important;
    border-bottom: 1px solid rgba(120,180,255,0.2);
    color: #ffffff !important;
    backdrop-filter: blur(10px) !important;
    animation: slideInRight 0.6s ease-out !important;
}

.stMarkdown p,
.stMarkdown div,
.stMarkdown span,
.stMarkdown li,
.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3,
.stMarkdown h4,
.stMarkdown h5,
.stMarkdown h6,
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

/* Animated headings */
h1, .stMarkdown h1 {
    animation: fadeInUp 0.6s ease-out !important;
    text-shadow: 0 2px 10px rgba(102, 179, 255, 0.3) !important;
    font-weight: 700 !important;
}

h2, .stMarkdown h2 {
    animation: fadeInUp 0.7s ease-out !important;
    text-shadow: 0 1px 8px rgba(102, 179, 255, 0.2) !important;
}

h3, .stMarkdown h3,
h4, .stMarkdown h4 {
    animation: fadeInUp 0.8s ease-out !important;
}

/* st.metric styling with animations */
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    color: #ffffff !important;
}

[data-testid="stMetricLabel"] > div,
[data-testid="stMetricValue"] > div {
    color: #ffffff !important;
}

/* Animate metric values */
[data-testid="stMetricValue"] {
    animation: scaleUp 0.5s ease-out !important;
    font-weight: 700 !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

/* Metric container hover effect */
[data-testid="stMetric"] {
    transition: all 0.3s ease !important;
    padding: 1rem !important;
    border-radius: 8px !important;
    background: rgba(255, 255, 255, 0.03) !important;
}

[data-testid="stMetric"]:hover {
    background: rgba(255, 255, 255, 0.06) !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 6px 16px rgba(41, 128, 185, 0.2) !important;
}

/* Caption text */
.stCaption, [data-testid="stCaption"] {
    color: #aaaaaa !important;
}

.main .stCaption, .main [data-testid="stCaption"] {
    color: #cccccc !important;
}

/* Ensure all text in main is light colored */
.main p, .main span, .main div {
    color: #ffffff !important;
}

.main .element-container p,
.main .element-container span,
.main .element-container div {
    color: #ffffff !important;
}

/* Override any black text in main content */
.main * {
    color: inherit !important;
}

/* But ensure root elements are white */
.main > * {
    color: #ffffff !important;
}

.main .block-container * {
    color: #ffffff !important;
}

/* Except for input fields which need dark text */
.main input[type="text"],
.main textarea,
.main [data-baseweb="input"] input,
.main [data-baseweb="select"] div[data-baseweb="input"] input,
.main [data-baseweb="select"] div[data-baseweb="input"] div,
.main [role="option"],
.main [data-baseweb="tag"],
.main [data-baseweb="tag"] span {
    color: #1a1a1a !important;
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
    transition: all 0.3s ease !important;
}

section[data-testid="stSidebar"] input::placeholder {
    color: rgba(50, 50, 50, 0.7) !important;
}

/* Enhanced input focus states */
section[data-testid="stSidebar"] input[type="text"]:focus,
section[data-testid="stSidebar"] textarea:focus {
    animation: glow 2s ease-in-out infinite !important;
    outline: none !important;
}

/* Main content input fields with glow */
.main input[type="text"]:focus,
.main textarea:focus,
.main select:focus {
    animation: glow 2s ease-in-out infinite !important;
    outline: none !important;
    border-color: rgba(102, 179, 255, 0.6) !important;
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

/* ==================== MAIN CONTENT FORM ELEMENTS ==================== */

/* Main content selectboxes and dropdowns */
.main [data-baseweb="select"] {
    background-color: transparent !important;
}

.main [data-baseweb="select"] > div:first-child {
    background-color: transparent !important;
    border: none !important;
}

.main [data-baseweb="select"] div[data-baseweb="input"] {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(102, 179, 255, 0.3) !important;
    border-radius: 8px !important;
    color: #1a1a1a !important;
    min-height: 2.8rem !important;
    padding: 0.5rem 0.75rem !important;
    transition: all 0.3s ease !important;
}

.main [data-baseweb="select"] div[data-baseweb="input"]:hover {
    background-color: rgba(255, 255, 255, 1) !important;
    border-color: rgba(102, 179, 255, 0.5) !important;
    box-shadow: 0 0 10px rgba(102, 179, 255, 0.15) !important;
}

.main [data-baseweb="select"] div[data-baseweb="input"]:focus-within {
    background-color: rgba(255, 255, 255, 1) !important;
    border-color: rgba(102, 179, 255, 0.6) !important;
    box-shadow: 0 0 15px rgba(102, 179, 255, 0.25) !important;
    outline: none !important;
}

.main [data-baseweb="select"] div[data-baseweb="input"] input,
.main [data-baseweb="select"] div[data-baseweb="input"] div {
    color: #1a1a1a !important;
}

/* Dropdown menu styling */
.main [data-baseweb="popover"] {
    background-color: rgba(255, 255, 255, 0.98) !important;
    border: 1px solid rgba(102, 179, 255, 0.3) !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
}

.main [data-baseweb="menu"] {
    background-color: rgba(255, 255, 255, 0.98) !important;
}

.main [role="option"] {
    color: #1a1a1a !important;
    background-color: transparent !important;
    padding: 0.6rem 1rem !important;
    transition: all 0.2s ease !important;
}

.main [role="option"]:hover {
    background-color: rgba(102, 179, 255, 0.15) !important;
    color: #000000 !important;
}

.main [role="option"][aria-selected="true"] {
    background-color: rgba(102, 179, 255, 0.25) !important;
    color: #000000 !important;
    font-weight: 600 !important;
}

/* Main content text inputs */
.main input[type="text"]:not([data-testid="stChatInput"] input),
.main [data-baseweb="input"] input {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(102, 179, 255, 0.3) !important;
    border-radius: 8px !important;
    color: #1a1a1a !important;
    padding: 0.6rem 0.75rem !important;
    transition: all 0.3s ease !important;
}

.main input[type="text"]:hover:not([data-testid="stChatInput"] input) {
    background-color: rgba(255, 255, 255, 1) !important;
    border-color: rgba(102, 179, 255, 0.5) !important;
}

.main input[type="text"]:focus:not([data-testid="stChatInput"] input) {
    background-color: rgba(255, 255, 255, 1) !important;
    border-color: rgba(102, 179, 255, 0.6) !important;
    box-shadow: 0 0 15px rgba(102, 179, 255, 0.25) !important;
}

.main input[type="text"]::placeholder {
    color: rgba(26, 26, 26, 0.5) !important;
}

/* Main content multiselect */
.main [data-baseweb="tag"] {
    background-color: rgba(102, 179, 255, 0.2) !important;
    border: 1px solid rgba(102, 179, 255, 0.4) !important;
    color: #1a1a1a !important;
    border-radius: 6px !important;
    padding: 0.25rem 0.5rem !important;
    margin: 0.25rem !important;
}

.main [data-baseweb="tag"] span {
    color: #1a1a1a !important;
}

/* Multiselect container - auto expand */
.main div[data-baseweb="select"] > div {
    min-height: 2.8rem !important;
    height: auto !important;
    max-height: none !important;
}

/* Multiselect input container with tags */
.main div[data-baseweb="select"] div[data-baseweb="input"] {
    min-height: 2.8rem !important;
    height: auto !important;
    max-height: none !important;
    flex-wrap: wrap !important;
    padding: 0.4rem !important;
}

/* Hide selected items from dropdown list */
.main [role="listbox"] [role="option"][aria-selected="true"] {
    display: none !important;
}

/* Better visibility for multiselect options */
.main [role="listbox"] [role="option"] {
    padding: 0.7rem 1rem !important;
    color: #1a1a1a !important;
    font-weight: 500 !important;
}

.main [role="listbox"] [role="option"]:hover {
    background-color: rgba(102, 179, 255, 0.2) !important;
    color: #000000 !important;
}

/* Main content radio buttons - enhanced visibility */
.main [role="radiogroup"] {
    background-color: rgba(255, 255, 255, 0.03) !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
}

.main [role="radiogroup"] label {
    color: #ffffff !important;
}

.main [role="radiogroup"] label span {
    color: #ffffff !important;
}

.main [role="radiogroup"] label div {
    color: #ffffff !important;
}

.main [role="radiogroup"] p {
    color: #ffffff !important;
}

/* Radio button options text */
.main [role="radiogroup"] label[data-baseweb="radio"] {
    color: #ffffff !important;
}

.main [role="radiogroup"] label[data-baseweb="radio"] > div {
    color: #ffffff !important;
}

.main [role="radiogroup"] [class*="st"] {
    color: #ffffff !important;
}

.main [data-testid="stRadio"] label {
    color: #ffffff !important;
}

.main [data-testid="stRadio"] label > div {
    color: #ffffff !important;
}

.main [data-testid="stRadio"] label > div > div {
    color: #ffffff !important;
}

.main [data-testid="stRadio"] [role="radiogroup"] label {
    color: #ffffff !important;
}

/* Force all descendants of radio to be white */
.main [data-testid="stRadio"] * {
    color: #ffffff !important;
}

.main [role="radio"] {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid rgba(102, 179, 255, 0.3) !important;
    width: 20px !important;
    height: 20px !important;
    transition: all 0.2s ease !important;
}

.main [role="radio"]:hover {
    border-color: rgba(102, 179, 255, 0.6) !important;
    box-shadow: 0 0 8px rgba(102, 179, 255, 0.3) !important;
}

.main [role="radio"][aria-checked="true"] {
    background-color: #3498db !important;
    border-color: #2980b9 !important;
    box-shadow: 0 0 12px rgba(52, 152, 219, 0.5) !important;
}

.main [role="radio"] + div {
    color: #ffffff !important;
    font-weight: 500 !important;
}

.main [role="radio"] ~ div {
    color: #ffffff !important;
}

/* Main content labels */
.main label {
    color: #e8f1ff !important;
    font-weight: 500 !important;
    margin-bottom: 0.5rem !important;
}

/* Main content color pickers */
.main input[type="color"] {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid rgba(102, 179, 255, 0.3) !important;
    border-radius: 8px !important;
    width: 80px !important;
    height: 45px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

.main input[type="color"]:hover {
    border-color: rgba(102, 179, 255, 0.6) !important;
    box-shadow: 0 0 15px rgba(102, 179, 255, 0.3) !important;
    transform: scale(1.05) !important;
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
    animation: fadeInUp 0.4s ease-out !important;
    transition: all 0.3s ease !important;
}

[data-testid="stChatMessageContent"]:hover {
    background-color: rgba(255,255,255,0.08) !important;
    transform: translateX(5px) !important;
}

[data-testid="stChatMessageContent"] code {
    background-color: rgba(255,255,255,0.1) !important;
    color: #a0e6ff !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stChatMessageContent"] code:hover {
    background-color: rgba(255,255,255,0.15) !important;
    color: #c0f0ff !important;
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

/* Smaller font for RFP dashboard sidebar navigation buttons */
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
    font-size: 0.85rem !important;
    padding: 0.5rem 0.7rem !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    line-height: 1.4 !important;
    min-height: 2.2rem !important;
    height: auto !important;
    margin-bottom: 0.25rem !important;
}

/* Caption below sidebar buttons */
section[data-testid="stSidebar"] .stCaption {
    margin-top: -0.25rem !important;
    margin-bottom: 0.5rem !important;
    font-size: 0.75rem !important;
    opacity: 0.8 !important;
}

/* --- ENHANCED CARD STYLING --- */

/* Add subtle border and shadow to containers */
.main .block-container > div > div {
    border: 1px solid rgba(41, 128, 185, 0.1) !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
    margin-bottom: 0.5rem !important;
    background: rgba(255, 255, 255, 0.02) !important;
}

/* Enhanced card hover state */
.main .block-container > div > div:hover {
    border-color: rgba(102, 179, 255, 0.3) !important;
    background: rgba(255, 255, 255, 0.04) !important;
    box-shadow: 0 4px 20px rgba(41, 128, 185, 0.15) !important;
}

/* --- DOWNLOAD BUTTONS & SPECIAL EFFECTS --- */

/* Primary download buttons */
button[kind="primary"],
button[data-testid*="download"] {
    background: linear-gradient(135deg, #2980b9 0%, #3498db 100%) !important;
    border: none !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    position: relative !important;
    overflow: hidden !important;
}

button[kind="primary"]:hover,
button[data-testid*="download"]:hover {
    background: linear-gradient(135deg, #3498db 0%, #5dade2 100%) !important;
    animation: bounce 0.6s ease !important;
}

/* Removed ripple effect - was covering content */

/* Loading spinner - removed animation */
[data-testid="stSpinner"] > div {
    border-color: rgba(102, 179, 255, 0.3) !important;
    border-top-color: #66b3ff !important;
}

/* Progress bars */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #2980b9, #3498db, #5dade2) !important;
    background-size: 200% 100% !important;
    animation: gradientShift 2s ease infinite !important;
}

/* --- SKELETON LOADING SCREENS --- */

/* Skeleton placeholder animation */
.skeleton {
    background: linear-gradient(90deg,
        rgba(255, 255, 255, 0.05) 0%,
        rgba(255, 255, 255, 0.1) 50%,
        rgba(255, 255, 255, 0.05) 100%) !important;
    background-size: 200% 100% !important;
    animation: shimmer 1.5s ease-in-out infinite !important;
    border-radius: 6px !important;
}

/* Skeleton for text lines */
.skeleton-text {
    height: 1rem !important;
    margin-bottom: 0.5rem !important;
}

/* Skeleton for buttons */
.skeleton-button {
    height: 2.5rem !important;
    width: 100px !important;
}

/* --- CUSTOM SCROLLBAR --- */

/* For WebKit browsers (Chrome, Safari, Edge) */
::-webkit-scrollbar {
    width: 10px !important;
    height: 10px !important;
}

::-webkit-scrollbar-track {
    background: rgba(10, 24, 40, 0.5) !important;
    border-radius: 10px !important;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #2980b9 0%, #3498db 100%) !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #3498db 0%, #5dade2 100%) !important;
    box-shadow: 0 0 10px rgba(102, 179, 255, 0.5) !important;
}

/* For Firefox */
* {
    scrollbar-width: thin !important;
    scrollbar-color: #3498db rgba(10, 24, 40, 0.5) !important;
}

/* --- TEXT SELECTION STYLING --- */

::selection {
    background: rgba(52, 152, 219, 0.4) !important;
    color: #ffffff !important;
    text-shadow: 0 0 8px rgba(102, 179, 255, 0.5) !important;
}

::-moz-selection {
    background: rgba(52, 152, 219, 0.4) !important;
    color: #ffffff !important;
    text-shadow: 0 0 8px rgba(102, 179, 255, 0.5) !important;
}

/* --- ENHANCED TABLE STYLING --- */

/* Data tables */
[data-testid="stDataFrame"],
.stDataFrame {
    animation: fadeInUp 0.5s ease-out !important;
}

/* Table headers */
[data-testid="stDataFrame"] thead th,
.stDataFrame thead th {
    background: linear-gradient(135deg, #1d4d7f 0%, #2a6fa3 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    font-size: 0.85rem !important;
    padding: 0.75rem !important;
    border-bottom: 2px solid #66b3ff !important;
}

/* Table rows */
[data-testid="stDataFrame"] tbody tr,
.stDataFrame tbody tr {
    transition: all 0.2s ease !important;
}

[data-testid="stDataFrame"] tbody tr:hover,
.stDataFrame tbody tr:hover {
    background: rgba(102, 179, 255, 0.1) !important;
    transform: scale(1.01) !important;
    box-shadow: 0 2px 8px rgba(41, 128, 185, 0.2) !important;
}

/* Table cells */
[data-testid="stDataFrame"] tbody td,
.stDataFrame tbody td {
    padding: 0.6rem !important;
    border-bottom: 1px solid rgba(102, 179, 255, 0.1) !important;
}

/* --- ENHANCED FORM ELEMENTS --- */

/* Text areas */
textarea {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(102, 179, 255, 0.3) !important;
    border-radius: 8px !important;
    color: #1a1a1a !important;
    padding: 0.75rem !important;
    transition: all 0.3s ease !important;
    font-family: 'Montserrat', sans-serif !important;
}

textarea::placeholder {
    color: rgba(26, 26, 26, 0.5) !important;
}

textarea:focus {
    background: rgba(255, 255, 255, 1) !important;
    border-color: rgba(102, 179, 255, 0.6) !important;
    box-shadow: 0 0 20px rgba(102, 179, 255, 0.3) !important;
}

/* Checkboxes and radio buttons */
input[type="checkbox"],
input[type="radio"] {
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

input[type="checkbox"]:hover,
input[type="radio"]:hover {
    transform: scale(1.1) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(102, 179, 255, 0.3) !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    transition: all 0.3s ease !important;
    background: rgba(255, 255, 255, 0.02) !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(102, 179, 255, 0.6) !important;
    background: rgba(255, 255, 255, 0.05) !important;
    box-shadow: 0 0 20px rgba(102, 179, 255, 0.2) !important;
    transform: scale(1.01) !important;
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
    background: transparent !important;
    border: none !important;
}

/* Remove the wrapper box/container background */
[data-testid="stChatInput"] > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* Chat input field styling - clean and minimal */
[data-testid="stChatInput"] input,
[data-testid="stChatInput"] textarea {
    color: #1a1a1a !important;
    background-color: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(102, 179, 255, 0.3) !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stChatInput"] input:focus,
[data-testid="stChatInput"] textarea:focus {
    background-color: #ffffff !important;
    border-color: rgba(102, 179, 255, 0.6) !important;
    box-shadow: 0 0 10px rgba(102, 179, 255, 0.15) !important;
    outline: none !important;
}

[data-testid="stChatInput"] input::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(26, 26, 26, 0.5) !important;
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

/* Improve alert boxes text readability while preserving colors */
[data-testid="stAlert"] {
    padding: 1rem !important;
    border-radius: 8px !important;
}

[data-testid="stAlert"] > div {
    color: #ffffff !important;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div {
    color: #ffffff !important;
}

/* Info boxes - blue with light text */
[data-testid="stAlert"][data-testid*="info"],
.stAlert-info {
    background-color: rgba(29, 77, 127, 0.9) !important;
}

[data-testid="stAlert"][data-testid*="info"] [data-testid="stMarkdownContainer"] p,
.stAlert-info p {
    color: #e8f1ff !important;
    font-weight: 500;
}

/* Success boxes - keep green with enhanced animation */
[data-testid="stAlert"][data-testid*="success"],
.stAlert-success {
    background: linear-gradient(135deg, rgba(39, 114, 60, 0.9) 0%, rgba(56, 142, 60, 0.9) 100%) !important;
    border: 1px solid rgba(76, 175, 80, 0.5) !important;
    box-shadow: 0 4px 20px rgba(76, 175, 80, 0.2) !important;
    animation: fadeInUp 0.4s ease-out, pulse 2s ease-in-out infinite !important;
}

[data-testid="stAlert"][data-testid*="success"] p,
.stAlert-success p {
    color: #c8e6c9 !important;
    font-weight: 600 !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

[data-testid="stAlert"][data-testid*="success"] svg,
.stAlert-success svg {
    fill: #4caf50 !important;
    filter: drop-shadow(0 2px 4px rgba(76, 175, 80, 0.5)) !important;
}

/* Success checkmark animation */
@keyframes checkmark {
    0% {
        transform: scale(0) rotate(-45deg);
        opacity: 0;
    }
    50% {
        transform: scale(1.2) rotate(-45deg);
        opacity: 1;
    }
    100% {
        transform: scale(1) rotate(0deg);
        opacity: 1;
    }
}

[data-testid="stAlert"][data-testid*="success"] svg {
    animation: checkmark 0.5s ease-out !important;
}

/* Warning boxes - keep yellow/orange with enhanced styling */
[data-testid="stAlert"][data-testid*="warning"],
.stAlert-warning {
    background: linear-gradient(135deg, rgba(120, 81, 17, 0.9) 0%, rgba(142, 95, 20, 0.9) 100%) !important;
    border: 1px solid rgba(255, 193, 7, 0.5) !important;
    box-shadow: 0 4px 20px rgba(255, 193, 7, 0.2) !important;
    animation: fadeInUp 0.4s ease-out !important;
}

[data-testid="stAlert"][data-testid*="warning"] p,
.stAlert-warning p {
    color: #ffe082 !important;
    font-weight: 600 !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

[data-testid="stAlert"][data-testid*="warning"] svg,
.stAlert-warning svg {
    fill: #ffc107 !important;
    filter: drop-shadow(0 2px 4px rgba(255, 193, 7, 0.5)) !important;
    animation: pulse 2s ease-in-out infinite !important;
}

/* Error boxes - keep red with shake animation */
[data-testid="stAlert"][data-testid*="error"],
.stAlert-error {
    background: linear-gradient(135deg, rgba(120, 29, 29, 0.9) 0%, rgba(183, 28, 28, 0.9) 100%) !important;
    border: 1px solid rgba(244, 67, 54, 0.5) !important;
    box-shadow: 0 4px 20px rgba(244, 67, 54, 0.3) !important;
    animation: fadeInUp 0.4s ease-out, shake 0.5s ease-out !important;
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}

[data-testid="stAlert"][data-testid*="error"] p,
.stAlert-error p {
    color: #ffcdd2 !important;
    font-weight: 600 !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

[data-testid="stAlert"][data-testid*="error"] svg,
.stAlert-error svg {
    fill: #f44336 !important;
    filter: drop-shadow(0 2px 4px rgba(244, 67, 54, 0.5)) !important;
}

[data-testid="stAlert"] svg {
    color: #ffffff !important;
}

/* --- ANIMATIONS & TRANSITIONS --- */

/* Smooth scroll behavior */
html {
    scroll-behavior: smooth !important;
}

/* Fade-in animation for cards */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Pulsing animation for status badges */
@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.8;
    }
}

/* Shimmer animation for loading states */
@keyframes shimmer {
    0% {
        background-position: -1000px 0;
    }
    100% {
        background-position: 1000px 0;
    }
}

/* Animated gradient background */
@keyframes gradientShift {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

/* Glow effect for focus states */
@keyframes glow {
    0%, 100% {
        box-shadow: 0 0 5px rgba(102, 179, 255, 0.3);
    }
    50% {
        box-shadow: 0 0 20px rgba(102, 179, 255, 0.6), 0 0 30px rgba(102, 179, 255, 0.4);
    }
}

/* Bounce animation for interactive elements */
@keyframes bounce {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-5px);
    }
}

/* Slide in from right */
@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Scale up animation */
@keyframes scaleUp {
    from {
        transform: scale(0.95);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}

/* Apply fade-in to containers */
.main .block-container > div > div {
    animation: fadeInUp 0.5s ease-out;
}

/* Smooth transitions for all interactive elements */
button, a, [role="button"] {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Enhanced button hover effects */
button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3) !important;
}

button:active {
    transform: translateY(0) !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
}

/* Status badge animations */
[data-testid="stAlert"] {
    animation: fadeInUp 0.4s ease-out !important;
    transition: all 0.3s ease !important;
}

/* Success badges pulse gently */
.stAlert-success, [data-baseweb="notification"] {
    animation: fadeInUp 0.4s ease-out, pulse 2s ease-in-out infinite !important;
}

/* Card hover effects for containers */
.main .block-container > div > div:hover {
    transform: scale(1.01) !important;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Glassmorphism effect for sidebar */
section[data-testid="stSidebar"] {
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
}

/* Smooth expand/collapse for expanders */
[data-testid="stExpander"] {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

[data-testid="stExpander"][aria-expanded="true"] {
    box-shadow: 0 4px 12px rgba(41, 128, 185, 0.2) !important;
}

/* Tab transition effects */
.stTabs [data-baseweb="tab"] {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stTabs [aria-selected="true"] {
    transform: translateY(-2px) !important;
}

/* Slide Viewer Styling with Enhanced Transitions */
/* IMPORTANT: Slide styles should NOT apply to LinkedIn preview */

/* Slide transition animations */
@keyframes slideInFromRight {
    from {
        opacity: 0;
        transform: translateX(100px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideInFromLeft {
    from {
        opacity: 0;
        transform: translateX(-100px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideOutToLeft {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(-100px);
    }
}

@keyframes slideOutToRight {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(100px);
    }
}

/* Scoped to NOT affect linkedin-preview-wrapper */
.slide-container:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    background: linear-gradient(135deg, #1a3a52 0%, #1a4d6d 100%) !important;
    border-radius: 16px !important;
    padding: 30px !important;
    margin: 20px 0 !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    min-height: 450px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
    animation: slideInFromRight 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Smooth transition on slide changes */
.slide-container:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *),
.slide-inner:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.slide-watermark:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    position: absolute !important;
    top: 50% !important;
    right: 10px !important;
    transform: translateY(-50%) !important;
    transform-origin: center !important;
    max-width: 80px !important;
    height: auto !important;
}

.slide-watermark:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) img {
    width: 100% !important;
    height: auto !important;
    display: block !important;
    filter: brightness(0) invert(1) opacity(1) !important;
}

.slide-inner:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    width: 100% !important;
    background: linear-gradient(135deg, #0a1828 0%, #0f2a3f 100%) !important;
    border-radius: 12px !important;
    padding: 50px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    border: 1px solid rgba(41, 128, 185, 0.3) !important;
}

.slide-title-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    text-align: center !important;
    padding: 80px 50px !important;
    background: linear-gradient(135deg, #2980b9 0%, #3498db 100%) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
}

.slide-title-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) h1 {
    font-size: 56px !important;
    font-weight: 700 !important;
    margin: 0 0 30px 0 !important;
    line-height: 1.2 !important;
    color: #ffffff !important;
}

.slide-title-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) h3 {
    font-size: 28px !important;
    font-weight: 300 !important;
    margin: 30px 0 !important;
    opacity: 0.95 !important;
    color: #ffffff !important;
}

.slide-title-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) .brand {
    font-size: 16px !important;
    margin-top: 60px !important;
    letter-spacing: 3px !important;
    opacity: 0.8 !important;
    color: #ffffff !important;
}

.slide-content-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) h2 {
    font-size: 48px !important;
    color: #66b3ff !important;
    margin: 0 0 20px 0 !important;
    padding-bottom: 20px !important;
    border-bottom: 4px solid #3498db !important;
}

.slide-content-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) .bullet {
    font-size: 20px !important;
    color: #e8f1ff !important;
    margin: 20px 0 !important;
    padding-left: 30px !important;
    position: relative !important;
    line-height: 1.6 !important;
}

.slide-content-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) .bullet:before {
    content: "▸" !important;
    position: absolute !important;
    left: 0 !important;
    color: #66b3ff !important;
    font-size: 24px !important;
    font-weight: bold !important;
}

/* Nested Bullet Styling */
.slide-content-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) .bullet-nested {
    font-size: 17px !important;
    color: #b3d9ff !important;
    margin: 12px 0 !important;
    padding-left: 25px !important;
    position: relative !important;
    line-height: 1.5 !important;
}

.slide-content-slide:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) .bullet-nested:before {
    content: "◦" !important;
    position: absolute !important;
    left: 5px !important;
    color: #99ccff !important;
    font-size: 16px !important;
}

</style>""", unsafe_allow_html=True)
