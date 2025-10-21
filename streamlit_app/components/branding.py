"""
Centralized branding components using Streamlit's native image display.
Clean, simple logo rendering across the app.
"""

import streamlit as st
from pathlib import Path


def _get_logo_path(logo_type: str = "horizontal") -> Path:
    """Get the absolute path to a logo file.

    Args:
        logo_type: 'horizontal' or 'vertical'

    Returns:
        Path object to logo file
    """
    component_dir = Path(__file__).parent
    app_dir = component_dir.parent

    if logo_type == "vertical":
        return app_dir / "company_logo_vertical.png"
    else:  # horizontal is default
        return app_dir / "company_logo_horizontal.png"


def render_sidebar_logo() -> None:
    """Render horizontal logo in sidebar with Streamlit's native image display."""
    logo_path = _get_logo_path("horizontal")
    if logo_path.exists():
        st.image(str(logo_path), width=150, output_format="PNG")
        st.markdown("")  # Add spacing
    else:
        st.write("⚙️ Granite")


def render_page_header_logo(width_pct: int = 80, max_width: int = 200) -> None:
    """Render horizontal logo at top of page content area.

    Args:
        width_pct: Width percentage (0-100) of container
        max_width: Maximum width of logo in pixels
    """
    logo_path = _get_logo_path("horizontal")
    if logo_path.exists():
        # Center the logo using columns
        col1, col2, col3 = st.columns([1, width_pct, 1])
        with col2:
            st.image(str(logo_path), width=max_width, output_format="PNG")
        st.markdown("")  # Add spacing
    else:
        st.write("📊 Page Header")


def get_vertical_logo_path() -> Path:
    """Get path to vertical logo for direct use."""
    return _get_logo_path("vertical")


def render_slide_logo() -> None:
    """Render vertical logo for use in slide previews.

    This returns the image path for use in slide HTML rendering.
    """
    logo_path = _get_logo_path("vertical")
    return str(logo_path) if logo_path.exists() else None
