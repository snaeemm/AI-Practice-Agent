"""
Beautiful slide viewer component for presentations with HTML/CSS styling.
CSS is defined in styles.py for proper integration with dark theme.
"""

import streamlit as st
from typing import List, Dict, Any
from pathlib import Path
import base64


def _is_title_slide(slide_data: Dict[str, Any]) -> bool:
    """Detect if a slide should be displayed as a title slide."""
    points = slide_data.get("points", [])

    if len(points) == 0:
        return True
    elif len(points) == 1 and len(str(points[0])) < 100:
        return True

    return False


@st.cache_data
def _get_logo_base64() -> str:
    """Load and encode the vertical logo as base64 (cached for performance)."""
    logo_path = Path(__file__).parent.parent / "company_logo_vertical.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def render_slide_viewer(slides: List[Dict[str, Any]]) -> None:
    """
    Render an interactive slide viewer with beautiful HTML/CSS styling.

    Args:
        slides: List of slide dictionaries with 'title' and 'points' keys
    """
    if not slides:
        st.info("No slides to display")
        return

    # Get logo as base64
    logo_base64 = _get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Logo" />' if logo_base64 else 'GRANITE'

    # Initialize session state for slide navigation
    if "current_slide" not in st.session_state:
        st.session_state.current_slide = 0
    if "previous_slide_idx" not in st.session_state:
        st.session_state.previous_slide_idx = 0

    # Current slide with bounds checking
    current_idx = st.session_state.current_slide
    previous_idx = st.session_state.previous_slide_idx

    # Reset to 0 if index is out of bounds (e.g., after deletion)
    if current_idx >= len(slides):
        st.session_state.current_slide = 0
        current_idx = 0

    current_slide = slides[current_idx]
    title = current_slide.get("title", "Untitled")
    points = current_slide.get("points", [])
    is_title = current_idx == 0 and _is_title_slide(current_slide)

    # Build the slide HTML
    if is_title:
        # Title slide
        subtitle_html = ""
        if len(points) == 1:
            subtitle_html = f"<h3>{points[0]}</h3>"

        slide_html = f"""
        <div class="slide-container">
            <div class="slide-inner slide-title-slide">
                <h1>{title}</h1>
                {subtitle_html}
            </div>
            <div class="slide-watermark">{logo_html}</div>
        </div>
        """
    else:
        # Content slide
        bullets_html = ""
        if points:
            for point in points:
                if isinstance(point, dict):
                    # Nested bullet with sub-points
                    main_text = point.get("text", "")
                    sub_points = point.get("sub_points", [])

                    bullets_html += f'<div class="bullet">{main_text}</div>'

                    if sub_points:
                        bullets_html += '<div style="margin-left: 20px;">'
                        for sub_point in sub_points:
                            bullets_html += f'<div class="bullet-nested">{sub_point}</div>'
                        bullets_html += '</div>'
                else:
                    # Simple string bullet
                    bullets_html += f'<div class="bullet">{point}</div>'
        else:
            bullets_html = '<div style="color: #95a5a6; font-style: italic; padding-left: 30px;">No content</div>'

        slide_html = f"""
        <div class="slide-container">
            <div class="slide-inner slide-content-slide">
                <h2>{title}</h2>
                {bullets_html}
            </div>
            <div class="slide-watermark">{logo_html}</div>
        </div>
        """

    # Render the slide
    st.markdown(slide_html, unsafe_allow_html=True)

    # Navigation controls
    st.markdown("---")

    col_prev, col_dots, col_counter, col_next = st.columns([1, 3, 2, 1])

    with col_prev:
        if st.button("⬅️ Prev", key="prev_slide", use_container_width=True):
            st.session_state.previous_slide_idx = current_idx
            if current_idx > 0:
                st.session_state.current_slide -= 1
            else:
                st.session_state.current_slide = len(slides) - 1
            st.rerun()

    with col_dots:
        # Show indicator dots
        dots = ""
        for i in range(len(slides)):
            if i == current_idx:
                dots += "🔵 "
            else:
                dots += "⚪ "
        st.markdown(dots, help="Current slide indicator")

    with col_counter:
        st.markdown(f"#### Slide {current_idx + 1}/{len(slides)}")

    with col_next:
        if st.button("Next ➡️", key="next_slide", use_container_width=True):
            st.session_state.previous_slide_idx = current_idx
            if current_idx < len(slides) - 1:
                st.session_state.current_slide += 1
            else:
                st.session_state.current_slide = 0
            st.rerun()
