import streamlit as st


def apply_custom_styles():
    st.markdown("""<style>
/* --- Font Import --- */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

/* --- Global Font Application --- */
* {
    font-family: 'Montserrat', sans-serif !important;
}

/* --- Material Icons Support --- */
.material-icons,
.material-icons-outlined,
.material-icons-round,
.material-icons-sharp,
.material-icons-two-tone {
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
    -webkit-font-feature-settings: 'liga' !important;
    -moz-font-feature-settings: 'liga' !important;
    font-feature-settings: 'liga' !important;
}

/* Target Streamlit's internal icon elements */
[data-testid*="icon"] span,
[data-testid*="Icon"] span,
[class*="StyledIcon"] span,
[class*="icon"] span,
svg + span,
button span,
a span {
    font-family: 'Material Icons' !important;
    -webkit-font-feature-settings: 'liga' !important;
    -moz-font-feature-settings: 'liga' !important;
    font-feature-settings: 'liga' !important;
}

/* Ensure all spans use ligatures for icon rendering */
span {
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

/* st.metric styling */
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    color: #ffffff !important;
}

[data-testid="stMetricLabel"] > div,
[data-testid="stMetricValue"] > div {
    color: #ffffff !important;
}

/* Caption text */
.stCaption, [data-testid="stCaption"] {
    color: #aaaaaa !important;
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

/* Success boxes - keep green */
[data-testid="stAlert"][data-testid*="success"],
.stAlert-success {
    background-color: rgba(39, 114, 60, 0.9) !important;
    border: 1px solid rgba(76, 175, 80, 0.3) !important;
}

[data-testid="stAlert"][data-testid*="success"] p,
.stAlert-success p {
    color: #c8e6c9 !important;
    font-weight: 500;
}

[data-testid="stAlert"][data-testid*="success"] svg,
.stAlert-success svg {
    fill: #4caf50 !important;
}

/* Warning boxes - keep yellow/orange */
[data-testid="stAlert"][data-testid*="warning"],
.stAlert-warning {
    background-color: rgba(120, 81, 17, 0.9) !important;
    border: 1px solid rgba(255, 193, 7, 0.3) !important;
}

[data-testid="stAlert"][data-testid*="warning"] p,
.stAlert-warning p {
    color: #ffe082 !important;
    font-weight: 500;
}

[data-testid="stAlert"][data-testid*="warning"] svg,
.stAlert-warning svg {
    fill: #ffc107 !important;
}

/* Error boxes - keep red */
[data-testid="stAlert"][data-testid*="error"],
.stAlert-error {
    background-color: rgba(120, 29, 29, 0.9) !important;
    border: 1px solid rgba(244, 67, 54, 0.3) !important;
}

[data-testid="stAlert"][data-testid*="error"] p,
.stAlert-error p {
    color: #ffcdd2 !important;
    font-weight: 500;
}

[data-testid="stAlert"][data-testid*="error"] svg,
.stAlert-error svg {
    fill: #f44336 !important;
}

[data-testid="stAlert"] svg {
    color: #ffffff !important;
}

/* Slide Viewer Styling */
.slide-container {
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
}

.slide-watermark {
    position: absolute !important;
    top: 50% !important;
    right: 10px !important;
    transform: translateY(-50%) !important;
    transform-origin: center !important;
    max-width: 80px !important;
    height: auto !important;
}

.slide-watermark img {
    width: 100% !important;
    height: auto !important;
    display: block !important;
    filter: brightness(0) invert(1) opacity(1) !important;
}

.slide-inner {
    width: 100% !important;
    background: linear-gradient(135deg, #0a1828 0%, #0f2a3f 100%) !important;
    border-radius: 12px !important;
    padding: 50px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    border: 1px solid rgba(41, 128, 185, 0.3) !important;
}

.slide-title-slide {
    text-align: center !important;
    padding: 80px 50px !important;
    background: linear-gradient(135deg, #2980b9 0%, #3498db 100%) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
}

.slide-title-slide h1 {
    font-size: 56px !important;
    font-weight: 700 !important;
    margin: 0 0 30px 0 !important;
    line-height: 1.2 !important;
    color: #ffffff !important;
}

.slide-title-slide h3 {
    font-size: 28px !important;
    font-weight: 300 !important;
    margin: 30px 0 !important;
    opacity: 0.95 !important;
    color: #ffffff !important;
}

.slide-title-slide .brand {
    font-size: 16px !important;
    margin-top: 60px !important;
    letter-spacing: 3px !important;
    opacity: 0.8 !important;
    color: #ffffff !important;
}

.slide-content-slide h2 {
    font-size: 48px !important;
    color: #66b3ff !important;
    margin: 0 0 20px 0 !important;
    padding-bottom: 20px !important;
    border-bottom: 4px solid #3498db !important;
}

.slide-content-slide .bullet {
    font-size: 20px !important;
    color: #e8f1ff !important;
    margin: 20px 0 !important;
    padding-left: 30px !important;
    position: relative !important;
    line-height: 1.6 !important;
}

.slide-content-slide .bullet:before {
    content: "▸" !important;
    position: absolute !important;
    left: 0 !important;
    color: #66b3ff !important;
    font-size: 24px !important;
    font-weight: bold !important;
}

/* Nested Bullet Styling */
.slide-content-slide .bullet-nested {
    font-size: 17px !important;
    color: #b3d9ff !important;
    margin: 12px 0 !important;
    padding-left: 25px !important;
    position: relative !important;
    line-height: 1.5 !important;
}

.slide-content-slide .bullet-nested:before {
    content: "◦" !important;
    position: absolute !important;
    left: 5px !important;
    color: #99ccff !important;
    font-size: 16px !important;
}

</style>

<script>
// Replace keyboard_double_arrow_right text with arrow emoji
(function() {
    function fixIconText() {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        const nodes = [];
        while(node = walker.nextNode()) {
            if (node.textContent && node.textContent.includes('keyboard_double_arrow')) {
                nodes.push(node);
            }
        }

        nodes.forEach(node => {
            node.textContent = node.textContent.replace(/keyboard_double_arrow_right/g, '➡️');
            node.textContent = node.textContent.replace(/keyboard_double_arrow_left/g, '⬅️');
            node.textContent = node.textContent.replace(/keyboard_double_arrow/g, '⇄');
        });
    }

    // Run on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixIconText);
    } else {
        fixIconText();
    }

    // Watch for dynamic content changes (Streamlit updates)
    const observer = new MutationObserver(function(mutations) {
        fixIconText();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)
