"""
Profile Selector Component
Allows users to select and switch between marketing profiles
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from agent.database.marketing_profile_manager import MarketingProfileManager


def render_profile_selector(
    marketing_mgr: MarketingProfileManager,
    user_id: str,
    current_profile_id: Optional[str] = None
) -> Optional[str]:
    """
    Render profile selector dropdown

    Args:
        marketing_mgr: Marketing profile manager instance
        user_id: Current user's ID
        current_profile_id: Currently selected profile ID

    Returns:
        Selected profile_id or None
    """

    # Get user's profiles
    profiles = marketing_mgr.get_user_profiles(user_id)

    if not profiles:
        st.warning("No marketing profiles found. Create one to get started!")
        if st.button("Create Your First Profile", type="primary"):
            st.session_state.show_onboarding = True
            st.rerun()
        return None

    # Profile selector
    profile_options = {}
    for profile in profiles:
        icon = "👤" if profile['profile_type'] == 'personal' else "🏢"
        default_marker = " ⭐" if profile.get('is_default') else ""
        label = f"{icon} {profile['profile_name']}{default_marker}"
        profile_options[label] = profile['profile_id']

    # Determine current selection
    if current_profile_id:
        # Find the label for current profile
        current_label = None
        for label, pid in profile_options.items():
            if pid == current_profile_id:
                current_label = label
                break

        if current_label:
            index = list(profile_options.keys()).index(current_label)
        else:
            index = 0
    else:
        # Try to find default profile
        default_profile = marketing_mgr.get_default_profile(user_id)
        if default_profile:
            for i, (label, pid) in enumerate(profile_options.items()):
                if pid == default_profile['profile_id']:
                    index = i
                    break
            else:
                index = 0
        else:
            index = 0

    # Render selector
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        selected_label = st.selectbox(
            "Active Profile",
            options=list(profile_options.keys()),
            index=index,
            key="profile_selector_dropdown"
        )

        selected_profile_id = profile_options[selected_label]

    with col2:
        if st.button("⚙️ Edit", use_container_width=True, key="edit_profile_btn"):
            st.session_state.editing_profile_id = selected_profile_id
            st.session_state.show_profile_editor = True
            st.rerun()

    with col3:
        if st.button("➕ New", use_container_width=True, key="new_profile_btn"):
            st.session_state.show_onboarding = True
            st.rerun()

    return selected_profile_id


def render_profile_summary_card(profile: Dict[str, Any]):
    """
    Render a compact summary card of the current profile

    Args:
        profile: Profile dictionary
    """

    icon = "👤" if profile['profile_type'] == 'personal' else "🏢"

    # Build summary text
    summary_parts = []

    if profile.get('industry'):
        summary_parts.append(f"Industry: {profile['industry']}")

    if profile.get('target_audience'):
        audience_short = profile['target_audience'][:50] + "..." if len(profile['target_audience']) > 50 else profile['target_audience']
        summary_parts.append(f"Audience: {audience_short}")

    if profile.get('default_tone'):
        summary_parts.append(f"Tone: {profile['default_tone'].title()}")

    summary_text = " • ".join(summary_parts) if summary_parts else "No details provided"

    # Render card
    st.info(f"""
**{icon} {profile['profile_name']}**

{summary_text}
    """)


def render_profile_editor(
    marketing_mgr: MarketingProfileManager,
    profile_id: str
):
    """
    Render inline profile editor

    Args:
        marketing_mgr: Marketing profile manager instance
        profile_id: Profile ID to edit
    """

    profile = marketing_mgr.get_profile(profile_id)

    if not profile:
        st.error("Profile not found")
        return

    st.markdown(f"### Edit Profile: {profile['profile_name']}")

    with st.form("profile_editor_form"):
        # Profile name
        profile_name = st.text_input(
            "Profile Name",
            value=profile.get('profile_name', ''),
            help="Display name for this profile"
        )

        # Brand voice
        brand_voice = st.text_area(
            "Brand Voice",
            value=profile.get('brand_voice', ''),
            help="Describe your communication style",
            height=80
        )

        # Target audience
        target_audience = st.text_area(
            "Target Audience",
            value=profile.get('target_audience', ''),
            help="Who are you trying to reach?",
            height=80
        )

        # Content themes
        current_themes = profile.get('content_themes', [])
        content_themes_str = ', '.join(current_themes) if current_themes else ''

        content_themes_input = st.text_input(
            "Content Themes (comma-separated)",
            value=content_themes_str,
            help="Topics you regularly post about"
        )

        # Default tone
        tone_options = ["professional", "inspirational", "educational", "conversational", "provocative"]
        current_tone = profile.get('default_tone', 'professional')
        tone_index = tone_options.index(current_tone) if current_tone in tone_options else 0

        default_tone = st.selectbox(
            "Default Tone",
            options=tone_options,
            index=tone_index
        )

        # Image style
        style_options = ["professional", "minimalist", "vibrant", "photorealistic", "abstract"]
        current_style = profile.get('image_style_preference', 'professional')
        style_index = style_options.index(current_style) if current_style in style_options else 0

        image_style_preference = st.selectbox(
            "Image Style Preference",
            options=style_options,
            index=style_index
        )

        # Is default
        is_default = st.checkbox(
            "Set as default profile",
            value=profile.get('is_default', False),
            help="The default profile will be automatically selected"
        )

        # Submit
        col1, col2 = st.columns([1, 1])

        with col1:
            submitted = st.form_submit_button("Save Changes", use_container_width=True, type="primary")

        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            # Parse content themes
            new_themes = [t.strip() for t in content_themes_input.split(',') if t.strip()]

            # Update profile
            updates = {
                'profile_name': profile_name,
                'brand_voice': brand_voice,
                'target_audience': target_audience,
                'content_themes': new_themes,
                'default_tone': default_tone,
                'image_style_preference': image_style_preference
            }

            success = marketing_mgr.update_profile(profile_id, **updates)

            if success and is_default != profile.get('is_default', False):
                marketing_mgr.set_default_profile(profile['user_id'], profile_id)

            if success:
                st.success("✅ Profile updated successfully!")
                st.session_state.show_profile_editor = False
                if 'editing_profile_id' in st.session_state:
                    del st.session_state.editing_profile_id
                st.rerun()
            else:
                st.error("❌ Failed to update profile")

        if cancelled:
            st.session_state.show_profile_editor = False
            if 'editing_profile_id' in st.session_state:
                del st.session_state.editing_profile_id
            st.rerun()


def render_profile_stats(
    marketing_mgr: MarketingProfileManager,
    profile_id: str
):
    """
    Render statistics for a profile

    Args:
        marketing_mgr: Marketing profile manager instance
        profile_id: Profile ID
    """

    stats = marketing_mgr.get_profile_stats(profile_id)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Posts", stats['total_posts'])

    with col2:
        st.metric("Actually Posted", stats['posted_count'])

    with col3:
        avg_rating = stats['avg_rating']
        rating_display = f"{avg_rating:.1f} ⭐" if avg_rating else "N/A"
        st.metric("Avg Rating", rating_display)
