import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import io
import base64
import html
from typing import Optional, List


# ==================== HELPER FUNCTIONS (MUST BE DEFINED FIRST) ====================

def _format_text_for_html(text: str) -> str:
    """Escape HTML special characters and replace newlines with <br> tags for HTML rendering."""
    if not isinstance(text, str):
        return ""
    # Escape HTML special characters first to prevent HTML injection/breakage
    escaped_text = html.escape(text)
    # Then replace newlines with <br> tags
    return escaped_text.replace('\n', '<br>')


def _format_post_text_with_hashtags(post_text: str, hashtags: Optional[List[str]] = None) -> str:
    """Format post text with hashtags styled"""
    # Handle empty/None post text
    if not post_text:
        post_text = ""

    formatted_text = _format_text_for_html(post_text)

    # Add hashtags if provided and not already in text
    if hashtags:
        # Check if hashtags are already in the text
        text_lower = post_text.lower() if post_text else ""
        missing_hashtags = []

        for tag in hashtags:
            tag_clean = tag.lstrip('#').lower()
            if f'#{tag_clean}' not in text_lower:
                missing_hashtags.append(f'#{tag_clean}')

        if missing_hashtags:
            # Only add spacing if there was actual text
            if formatted_text:
                formatted_text += '<br><br>'
            formatted_text += '<span class="linkedin-hashtags">' + ' '.join(missing_hashtags) + '</span>'

    return formatted_text if formatted_text else "&nbsp;"


# ==================== MAIN RENDER FUNCTIONS ====================

def render_linkedin_preview(
    post_text: str,
    user_name: str,
    user_role: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    hashtags: Optional[List[str]] = None,
    profile_pic_url: Optional[str] = None
):
    """
    Render a LinkedIn-style post preview

    Args:
        post_text: The post caption/text
        user_name: Name to display
        user_role: Optional role/title
        image_bytes: Optional image bytes to display
        hashtags: Optional list of hashtags
        profile_pic_url: Optional profile picture URL
    """

    # Custom CSS for LinkedIn styling - HIGHLY SPECIFIC TO PREVENT CONFLICTS
    linkedin_css = """<style>
    /* Force LinkedIn preview to NOT use any slide styles */
    div.linkedin-preview-wrapper,
    div.linkedin-preview-wrapper * {
        animation: none !important;
        background: transparent !important;
    }

    div.linkedin-preview-wrapper div.linkedin-post {
        background: linear-gradient(135deg, #1a3a52 0%, #1a4d6d 100%) !important;
        border: 1px solid rgba(102, 179, 255, 0.3) !important;
        border-radius: 8px !important;
        padding: 0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        max-width: 600px !important;
        margin: 0 auto !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        min-height: auto !important;
        height: auto !important;
    }

    div.linkedin-preview-wrapper div.linkedin-post * {
        color: #ffffff !important;
        animation: none !important;
    }

    div.linkedin-preview-wrapper div.linkedin-post div {
        background: transparent !important;
        min-height: auto !important;
        height: auto !important;
    }

    div.linkedin-preview-wrapper div.linkedin-header {
        padding: 12px 16px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        background: transparent !important;
        min-height: auto !important;
        height: auto !important;
        border: none !important;
        box-shadow: none !important;
    }

    div.linkedin-preview-wrapper div.linkedin-avatar {
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        min-height: 48px !important;
        max-width: 48px !important;
        max-height: 48px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #1A3A52 0%, #2E5266 100%) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 20px !important;
        flex-shrink: 0 !important;
        position: relative !important;
        transform: none !important;
    }

    div.linkedin-preview-wrapper div.linkedin-user-info {
        flex: 1 !important;
        background: transparent !important;
        min-height: auto !important;
    }

    div.linkedin-preview-wrapper div.linkedin-user-name {
        font-weight: 600 !important;
        font-size: 14px !important;
        color: #ffffff !important;
        margin: 0 !important;
        line-height: 1.4 !important;
    }

    div.linkedin-preview-wrapper div.linkedin-user-role {
        font-size: 12px !important;
        color: rgba(255, 255, 255, 0.8) !important;
        margin: 0 !important;
        line-height: 1.4 !important;
    }

    div.linkedin-preview-wrapper div.linkedin-timestamp {
        font-size: 12px !important;
        color: rgba(255, 255, 255, 0.7) !important;
        margin: 2px 0 0 0 !important;
    }

    div.linkedin-preview-wrapper div.linkedin-content {
        padding: 0 16px 12px 16px !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #e8f1ff !important;
        white-space: pre-wrap !important;
        background: transparent !important;
        min-height: auto !important;
        border: none !important;
        box-shadow: none !important;
    }

    div.linkedin-preview-wrapper span.linkedin-hashtags {
        color: #66b3ff !important;
        font-weight: 400 !important;
    }

    div.linkedin-preview-wrapper div.linkedin-image-container {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        background: transparent !important;
        min-height: auto !important;
        position: relative !important;
        border: none !important;
        box-shadow: none !important;
    }

    div.linkedin-preview-wrapper div.linkedin-image-container img {
        width: 100% !important;
        height: auto !important;
        border-radius: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        filter: none !important;
        transform: none !important;
        position: relative !important;
    }

    div.linkedin-preview-wrapper div.linkedin-actions {
        padding: 8px 16px !important;
        border-top: 1px solid rgba(102, 179, 255, 0.2) !important;
        display: flex !important;
        justify-content: space-around !important;
        gap: 8px !important;
        background: transparent !important;
        min-height: auto !important;
        box-shadow: none !important;
    }

    div.linkedin-preview-wrapper div.linkedin-action-btn {
        flex: 1 !important;
        padding: 12px !important;
        background: transparent !important;
        border: none !important;
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        cursor: default !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        border-radius: 4px !important;
        min-height: auto !important;
        box-shadow: none !important;
    }

    div.linkedin-preview-wrapper div.linkedin-action-btn:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }

    div.linkedin-preview-wrapper div.linkedin-action-btn span {
        color: rgba(255, 255, 255, 0.8) !important;
    }

    div.linkedin-preview-wrapper div.linkedin-stats {
        padding: 8px 16px !important;
        border-top: 1px solid rgba(102, 179, 255, 0.2) !important;
        font-size: 12px !important;
        color: rgba(255, 255, 255, 0.7) !important;
        display: flex !important;
        justify-content: space-between !important;
        background: transparent !important;
        min-height: auto !important;
        box-shadow: none !important;
    }

    div.linkedin-preview-wrapper div.linkedin-stats span {
        color: rgba(255, 255, 255, 0.7) !important;
    }

    /* Override any Streamlit defaults */
    div.linkedin-preview-wrapper div.linkedin-post [data-testid="stMarkdownContainer"] * {
        color: inherit !important;
    }

    div.linkedin-preview-wrapper div.linkedin-post [class*="st"] {
        color: #ffffff !important;
    }

    /* Ensure divs don't get white background from global styles */
    div.linkedin-preview-wrapper div.linkedin-post [class*="element-container"] {
        background: transparent !important;
    }

    div.linkedin-preview-wrapper div.linkedin-post .stMarkdown {
        color: #ffffff !important;
        background: transparent !important;
    }

    /* CRITICAL: Prevent slide styles from applying to LinkedIn preview */
    div.linkedin-preview-wrapper,
    div.linkedin-preview-wrapper *,
    div.linkedin-preview-wrapper div,
    div.linkedin-preview-wrapper div.linkedin-post,
    div.linkedin-preview-wrapper div.linkedin-post * {
        position: relative !important;
    }

    /* Remove any slide-related classes that might bleed in */
    div.linkedin-preview-wrapper .slide-container,
    div.linkedin-preview-wrapper .slide-inner,
    div.linkedin-preview-wrapper .slide-watermark,
    div.linkedin-preview-wrapper .slide-content-slide,
    div.linkedin-preview-wrapper .slide-title-slide {
        display: none !important;
    }
    </style>""".strip()

    # Get user initials for avatar
    initials = ''.join([word[0].upper() for word in user_name.split()[:2]])

    # Convert image to base64 if provided
    image_html = ""
    if image_bytes:
        try:
            # Convert memoryview to bytes if needed
            if isinstance(image_bytes, memoryview):
                image_bytes = bytes(image_bytes)

            image_b64 = base64.b64encode(image_bytes).decode()
            image_html = f'<div class="linkedin-image-container"><img src="data:image/png;base64,{image_b64}" style="width: 100%; border-radius: 0; margin: 0; padding: 0;" /></div>'
        except Exception as e:
            image_html = f'<div style="color: #ff6b6b; padding: 1rem;">Error loading image: {str(e)}</div>'

    # Build complete HTML in one block - wrapped in unique class to prevent CSS conflicts
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        {linkedin_css}
    </head>
    <body style="margin: 0; padding: 0; background: transparent;">
        <div class="linkedin-preview-wrapper">
            <div class="linkedin-post">
                <div class="linkedin-header">
                    <div class="linkedin-avatar">{initials}</div>
                    <div class="linkedin-user-info">
                        <div class="linkedin-user-name">{user_name}</div>
                        {f'<div class="linkedin-user-role">{user_role}</div>' if user_role else ''}
                        <div class="linkedin-timestamp">Just now • 🌐</div>
                    </div>
                </div>

                <div class="linkedin-content">
                    {_format_post_text_with_hashtags(post_text, hashtags)}
                </div>

                {image_html}

                <div class="linkedin-stats">
                    <span>👍 0 • 💡 0 • ❤️ 0</span>
                    <span>0 comments • 0 reposts</span>
                </div>

                <div class="linkedin-actions">
                    <div class="linkedin-action-btn">
                        <span>👍</span> Like
                    </div>
                    <div class="linkedin-action-btn">
                        <span>💬</span> Comment
                    </div>
                    <div class="linkedin-action-btn">
                        <span>🔄</span> Repost
                    </div>
                    <div class="linkedin-action-btn">
                        <span>📨</span> Send
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """.strip()

    # Calculate dynamic height based on content
    # Base height + text length estimate + image height
    base_height = 200  # Header + actions + stats
    text_lines = len(post_text.split('\n')) if post_text else 0
    text_height = max(100, text_lines * 25)  # Approximate line height
    image_height = 400 if image_bytes else 0  # Estimated image height

    total_height = base_height + text_height + image_height
    # Cap between 400 and 1200 pixels
    dynamic_height = min(max(total_height, 400), 1200)

    # Render using st.components for true HTML rendering
    components.html(html_content, height=dynamic_height, scrolling=True)


def render_compact_post_card(
    post_text: str,
    image_bytes: Optional[bytes] = None,
    created_at: Optional[str] = None,
    post_topic: Optional[str] = None
):
    """
    Render a compact post card for history view

    Args:
        post_text: The post text
        image_bytes: Optional thumbnail image
        created_at: Timestamp string
        post_topic: Optional topic label
    """

    card_css = """
    <style>
    .post-card {
        background: linear-gradient(135deg, #1a3a52 0%, #1a4d6d 100%);
        border: 1px solid rgba(102, 179, 255, 0.3);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        transition: box-shadow 0.2s;
    }

    .post-card:hover {
        box-shadow: 0 4px 12px rgba(102, 179, 255, 0.3);
    }

    .post-card-topic {
        font-size: 11px;
        color: #66b3ff;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .post-card-text {
        font-size: 13px;
        line-height: 1.4;
        color: #e8f1ff;
        margin: 8px 0;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .post-card-timestamp {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.7);
    }
    </style>
    """.strip()

    st.markdown(card_css, unsafe_allow_html=True)

    # Container for card
    with st.container():
        # Image thumbnail if available
        if image_bytes:
            try:
                image = Image.open(io.BytesIO(image_bytes))
                st.image(image, use_container_width=True)
            except:
                pass

        # Text content
        card_html = f"""
        <div class="post-card">
            {f'<div class="post-card-topic">{post_topic}</div>' if post_topic else ''}
            <div class="post-card-text">{_format_text_for_html(post_text)}</div>
            {f'<div class="post-card-timestamp">{created_at}</div>' if created_at else ''}
        </div>
        """.strip()

        st.markdown(card_html, unsafe_allow_html=True)
