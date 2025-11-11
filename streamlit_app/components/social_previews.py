"""
Social Media Preview Components
Platform-specific preview cards for LinkedIn and Instagram
"""

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import io
import base64
import html
from typing import Optional, List


# ==================== HELPER FUNCTIONS ====================

def _format_text_for_html(text: str) -> str:
    """Convert markdown to HTML and handle formatting."""
    if not isinstance(text, str):
        return ""

    # Escape HTML special characters first
    escaped_text = html.escape(text)

    # Convert markdown to HTML
    # Bold: **text** or __text__
    import re
    escaped_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped_text)
    escaped_text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', escaped_text)

    # Italic: *text* or _text_
    escaped_text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped_text)
    escaped_text = re.sub(r'_(.+?)_', r'<em>\1</em>', escaped_text)

    # Replace newlines with <br> tags
    escaped_text = escaped_text.replace('\n', '<br>')

    return escaped_text


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
            formatted_text += '<span class="social-hashtags">' + ' '.join(missing_hashtags) + '</span>'

    return formatted_text if formatted_text else "&nbsp;"


# ==================== LINKEDIN PREVIEW ====================

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

    # Simple preview CSS - just text and image
    linkedin_css = """<style>
    div.preview-wrapper {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: linear-gradient(135deg, #1a3a52 0%, #1a4d6d 100%);
        border: 1px solid rgba(102, 179, 255, 0.3);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        padding: 0;
        margin: 0 auto;
        max-width: 600px;
    }

    div.preview-image {
        width: 100%;
        background: #000;
    }

    div.preview-image img {
        width: 100%;
        height: auto;
        display: block;
    }

    div.preview-content {
        padding: 24px;
        font-size: 15px;
        line-height: 1.6;
        color: #ffffff;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    div.preview-content strong {
        font-weight: 600;
        color: #ffffff;
    }

    div.preview-content em {
        font-style: italic;
        color: #ffffff;
    }

    span.social-hashtags {
        color: #66b3ff;
        font-weight: 400;
    }

    div.preview-badge {
        padding: 16px 24px;
        border-top: 1px solid rgba(102, 179, 255, 0.2);
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
        text-align: center;
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
            image_html = f'<div class="preview-image"><img src="data:image/png;base64,{image_b64}" /></div>'
        except Exception as e:
            image_html = f'<div style="color: #ff6b6b; padding: 1rem; text-align: center;">Error loading image: {str(e)}</div>'

    # Build simple HTML - just image and text
    platform_badge = "💼 LinkedIn Post"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        {linkedin_css}
    </head>
    <body style="margin: 0; padding: 0; background: transparent;">
        <div class="preview-wrapper">
            {image_html}

            <div class="preview-content">
                {_format_post_text_with_hashtags(post_text, hashtags)}
            </div>

            <div class="preview-badge">{platform_badge}</div>
        </div>
    </body>
    </html>
    """.strip()

    # Calculate dynamic height
    base_height = 200
    text_lines = len(post_text.split('\n')) if post_text else 0
    text_height = max(100, text_lines * 25)
    image_height = 400 if image_bytes else 0
    total_height = min(max(base_height + text_height + image_height, 400), 1200)

    components.html(html_content, height=total_height, scrolling=True)


# ==================== INSTAGRAM PREVIEW ====================

def render_instagram_preview(
    post_text: str,
    user_name: str,
    image_bytes: Optional[bytes] = None,
    hashtags: Optional[List[str]] = None,
    profile_pic_url: Optional[str] = None
):
    """
    Render an Instagram-style post preview

    Args:
        post_text: The post caption/text
        user_name: Username to display
        image_bytes: Optional image bytes to display
        hashtags: Optional list of hashtags
        profile_pic_url: Optional profile picture URL
    """

    # Simple preview CSS - just text and image (same as LinkedIn)
    instagram_css = """<style>
    div.preview-wrapper {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: linear-gradient(135deg, #1a3a52 0%, #1a4d6d 100%);
        border: 1px solid rgba(102, 179, 255, 0.3);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        padding: 0;
        margin: 0 auto;
        max-width: 600px;
    }

    div.preview-image {
        width: 100%;
        background: #000;
    }

    div.preview-image img {
        width: 100%;
        height: auto;
        display: block;
    }

    div.preview-content {
        padding: 24px;
        font-size: 15px;
        line-height: 1.6;
        color: #ffffff;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    div.preview-content strong {
        font-weight: 600;
        color: #ffffff;
    }

    div.preview-content em {
        font-style: italic;
        color: #ffffff;
    }

    span.social-hashtags {
        color: #66b3ff;
        font-weight: 400;
    }

    div.preview-badge {
        padding: 16px 24px;
        border-top: 1px solid rgba(102, 179, 255, 0.2);
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
        text-align: center;
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
            image_html = f'<div class="preview-image"><img src="data:image/png;base64,{image_b64}" /></div>'
        except Exception as e:
            image_html = f'<div style="color: #ff6b6b; padding: 1rem; text-align: center;">Error loading image: {str(e)}</div>'

    # Build simple HTML - just image and text
    platform_badge = "📸 Instagram Post"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        {instagram_css}
    </head>
    <body style="margin: 0; padding: 0; background: transparent;">
        <div class="preview-wrapper">
            {image_html}

            <div class="preview-content">
                {_format_post_text_with_hashtags(post_text, hashtags)}
            </div>

            <div class="preview-badge">{platform_badge}</div>
        </div>
    </body>
    </html>
    """.strip()

    # Calculate dynamic height (Instagram uses square 1:1 images)
    base_height = 250
    text_lines = len(post_text.split('\n')) if post_text else 0
    text_height = max(80, text_lines * 20)
    image_height = 470 if image_bytes else 100  # Square 1:1 aspect ratio
    total_height = min(max(base_height + text_height + image_height, 500), 1200)

    components.html(html_content, height=total_height, scrolling=True)


# ==================== UNIFIED PREVIEW ====================

def render_social_preview(
    platform: str,
    post_text: str,
    user_name: str,
    user_role: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    hashtags: Optional[List[str]] = None,
    profile_pic_url: Optional[str] = None
):
    """
    Render platform-specific social media preview

    Args:
        platform: 'linkedin' or 'instagram'
        post_text: The post caption/text
        user_name: Name/username to display
        user_role: Optional role/title (LinkedIn only)
        image_bytes: Optional image bytes to display
        hashtags: Optional list of hashtags
        profile_pic_url: Optional profile picture URL
    """
    if platform.lower() == 'linkedin':
        render_linkedin_preview(
            post_text=post_text,
            user_name=user_name,
            user_role=user_role,
            image_bytes=image_bytes,
            hashtags=hashtags,
            profile_pic_url=profile_pic_url
        )
    elif platform.lower() == 'instagram':
        render_instagram_preview(
            post_text=post_text,
            user_name=user_name,
            image_bytes=image_bytes,
            hashtags=hashtags,
            profile_pic_url=profile_pic_url
        )
    else:
        st.error(f"Unsupported platform: {platform}. Choose 'linkedin' or 'instagram'.")
