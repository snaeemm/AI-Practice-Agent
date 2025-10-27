"""
Post Preview Card Component
Enhanced component for displaying post preview cards with better layout and metadata
"""

import streamlit as st
from PIL import Image
import io
from datetime import datetime
from typing import Dict, Any, Optional, Callable


def render_post_preview_card(
    post: Dict[str, Any],
    on_view: Optional[Callable] = None,
    on_repost: Optional[Callable] = None,
    on_add_to_calendar: Optional[Callable] = None,
    compact: bool = False
) -> None:
    """
    Render a single post preview card

    Args:
        post: Post dictionary with metadata
        on_view: Callback when "View" button is clicked
        on_repost: Callback when "Repost" button is clicked
        on_add_to_calendar: Callback when "Add to Calendar" button is clicked
        compact: If True, use compact layout
    """

    post_id = post.get('post_id')
    platform = post.get('platform', 'linkedin')
    platform_emoji = "💼" if platform == "linkedin" else "📸"
    platform_name = platform.title()
    was_posted = post.get('was_posted', False)
    topic = post.get('post_topic', 'Untitled')
    created_at = post.get('created_at', 'Unknown')

    with st.container():
        # Card wrapper with hover effect
        st.markdown("""
            <style>
            .post-card {
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 0;
                margin-bottom: 16px;
                background: rgba(255,255,255,0.02);
                transition: all 0.3s ease;
                overflow: hidden;
            }
            .post-card:hover {
                border-color: rgba(102, 179, 255, 0.5);
                background: rgba(255,255,255,0.05);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            </style>
        """, unsafe_allow_html=True)

        # Image thumbnail
        if post.get('image_bytes'):
            try:
                image_data = post['image_bytes']
                if isinstance(image_data, memoryview):
                    image_data = bytes(image_data)

                img = Image.open(io.BytesIO(image_data))

                # Aspect ratio based on platform
                if platform == 'instagram':
                    # 4:5 for Instagram
                    target_height = int(st.session_state.get('card_width', 300) * 1.25)
                else:
                    # 1:1 for LinkedIn
                    target_height = st.session_state.get('card_width', 300)

                st.image(img, use_container_width=True)
            except Exception as e:
                # Fallback placeholder
                st.markdown(f"""
                    <div style='
                        background: linear-gradient(135deg, rgba(102, 179, 255, 0.2), rgba(102, 179, 255, 0.05));
                        padding: 80px 20px;
                        text-align: center;
                        border-radius: 8px 8px 0 0;
                        color: rgba(255,255,255,0.6);
                        font-size: 48px;
                    '>
                        {platform_emoji}
                    </div>
                """, unsafe_allow_html=True)
        else:
            # No image placeholder
            st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, rgba(102, 179, 255, 0.15), rgba(102, 179, 255, 0.05));
                    padding: 60px 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                    color: rgba(255,255,255,0.4);
                    font-size: 48px;
                '>
                    {platform_emoji}
                </div>
            """, unsafe_allow_html=True)

        # Content section
        with st.container():
            # Platform and Status Badges
            col1, col2 = st.columns([2, 1])

            with col1:
                # Platform badge
                if platform == "linkedin":
                    badge_style = "background: rgba(0, 119, 181, 0.3); color: #0077b5; border: 1px solid rgba(0, 119, 181, 0.5);"
                else:
                    badge_style = "background: rgba(225, 48, 108, 0.3); color: #E1306C; border: 1px solid rgba(225, 48, 108, 0.5);"

                st.markdown(f'''
                    <span style="
                        display: inline-block;
                        padding: 4px 10px;
                        border-radius: 12px;
                        font-size: 11px;
                        font-weight: 600;
                        {badge_style}
                    ">{platform_emoji} {platform_name}</span>
                ''', unsafe_allow_html=True)

            with col2:
                # Status badge
                if was_posted:
                    status_badge = '<span style="display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; background: rgba(40, 167, 69, 0.3); color: #28a745; border: 1px solid rgba(40, 167, 69, 0.5);">✅ Posted</span>'
                else:
                    status_badge = '<span style="display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; background: rgba(255, 193, 7, 0.3); color: #ffc107; border: 1px solid rgba(255, 193, 7, 0.5);">📝 Draft</span>'

                st.markdown(status_badge, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Topic/Title
            topic_display = topic[:60] + "..." if len(topic) > 60 else topic
            st.markdown(f"**{topic_display}**")

            # Metadata row
            metadata_parts = []

            # Date
            if isinstance(created_at, datetime):
                date_str = created_at.strftime('%b %d, %Y')
            elif isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = dt.strftime('%b %d, %Y')
                except:
                    date_str = created_at[:10] if len(created_at) >= 10 else created_at
            else:
                date_str = 'Unknown'

            metadata_parts.append(f"📅 {date_str}")

            # Post type
            post_type = post.get('post_type')
            if post_type:
                post_type_display = post_type.replace('_', ' ').title()
                metadata_parts.append(f"🎬 {post_type_display}")

            # Theme
            # For older posts, try to extract from hashtags or profile
            theme = post.get('theme')
            if theme:
                metadata_parts.append(f"🏷️ {theme}")

            # Rating
            user_rating = post.get('user_rating')
            if user_rating:
                stars = "⭐" * int(user_rating)
                metadata_parts.append(f"{stars} ({user_rating}/5)")

            st.caption(" • ".join(metadata_parts))

            st.markdown("<br>", unsafe_allow_html=True)

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👁️ View", key=f"view_{post_id}", use_container_width=True):
                    if on_view:
                        on_view(post)

            with col2:
                if st.button("🔄 Repost", key=f"repost_{post_id}", use_container_width=True):
                    if on_repost:
                        on_repost(post)

            with col3:
                if st.button("📅+", key=f"calendar_{post_id}", use_container_width=True, help="Add to Calendar"):
                    if on_add_to_calendar:
                        on_add_to_calendar(post)


def render_post_grid(
    posts: list[Dict[str, Any]],
    columns: int = 3,
    on_view: Optional[Callable] = None,
    on_repost: Optional[Callable] = None,
    on_add_to_calendar: Optional[Callable] = None
) -> None:
    """
    Render posts in a grid layout

    Args:
        posts: List of post dictionaries
        columns: Number of columns in the grid (default: 3)
        on_view: Callback when "View" button is clicked
        on_repost: Callback when "Repost" button is clicked
        on_add_to_calendar: Callback when "Add to Calendar" button is clicked
    """

    if not posts:
        st.info("No posts to display")
        return

    # Render in grid
    for i in range(0, len(posts), columns):
        cols = st.columns(columns)

        for j in range(columns):
            idx = i + j
            if idx < len(posts):
                with cols[j]:
                    render_post_preview_card(
                        post=posts[idx],
                        on_view=on_view,
                        on_repost=on_repost,
                        on_add_to_calendar=on_add_to_calendar
                    )


def render_post_filters(
    platforms: list[str] = ['linkedin', 'instagram'],
    post_types: list[str] = []
) -> Dict[str, Any]:
    """
    Render filter controls for posts

    Args:
        platforms: Available platforms
        post_types: Available post types

    Returns:
        Dictionary with selected filters
    """

    st.markdown("#### 🔍 Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        platform_filter = st.multiselect(
            "Platform",
            options=platforms,
            default=platforms,
            label_visibility="collapsed"
        )

    with col2:
        status_filter = st.multiselect(
            "Status",
            options=['Posted', 'Draft'],
            default=['Posted', 'Draft'],
            label_visibility="collapsed"
        )

    with col3:
        if post_types:
            type_filter = st.multiselect(
                "Type",
                options=post_types,
                default=post_types,
                label_visibility="collapsed"
            )
        else:
            type_filter = []

    with col4:
        sort_by = st.selectbox(
            "Sort by",
            options=['Date (Newest)', 'Date (Oldest)', 'Rating (High)', 'Rating (Low)'],
            label_visibility="collapsed"
        )

    # Search
    search_query = st.text_input(
        "🔎 Search posts...",
        placeholder="Search by topic or content",
        label_visibility="collapsed"
    )

    return {
        'platforms': platform_filter,
        'statuses': [s.lower() for s in status_filter],  # Convert to lowercase
        'types': type_filter,
        'sort_by': sort_by,
        'search': search_query
    }


def filter_and_sort_posts(
    posts: list[Dict[str, Any]],
    filters: Dict[str, Any]
) -> list[Dict[str, Any]]:
    """
    Filter and sort posts based on filter criteria

    Args:
        posts: List of post dictionaries
        filters: Filter criteria from render_post_filters

    Returns:
        Filtered and sorted list of posts
    """

    filtered = posts

    # Platform filter
    if filters.get('platforms'):
        filtered = [p for p in filtered if p.get('platform') in filters['platforms']]

    # Status filter
    if filters.get('statuses'):
        status_map = {'posted': True, 'draft': False}
        status_values = [status_map.get(s) for s in filters['statuses'] if s in status_map]
        if status_values:
            filtered = [p for p in filtered if p.get('was_posted') in status_values]

    # Type filter
    if filters.get('types'):
        filtered = [p for p in filtered if p.get('post_type') in filters['types']]

    # Search filter
    if filters.get('search'):
        search_lower = filters['search'].lower()
        filtered = [p for p in filtered
                    if search_lower in p.get('post_topic', '').lower()
                    or search_lower in p.get('generated_text', '').lower()]

    # Sort
    sort_by = filters.get('sort_by', 'Date (Newest)')

    if sort_by == 'Date (Newest)':
        filtered = sorted(filtered, key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_by == 'Date (Oldest)':
        filtered = sorted(filtered, key=lambda x: x.get('created_at', ''))
    elif sort_by == 'Rating (High)':
        filtered = sorted(filtered, key=lambda x: x.get('user_rating', 0) or 0, reverse=True)
    elif sort_by == 'Rating (Low)':
        filtered = sorted(filtered, key=lambda x: x.get('user_rating', 0) or 0)

    return filtered
