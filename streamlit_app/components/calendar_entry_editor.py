"""
Calendar Entry Editor Modal
Modal dialog for creating and editing calendar entries
"""

import streamlit as st
from datetime import datetime, time
from typing import Dict, Any, Optional


def render_calendar_entry_editor(
    marketing_mgr,
    user_id: str,
    profile_id: str,
    entry: Optional[Dict[str, Any]] = None,
    default_date: Optional[datetime] = None
) -> bool:
    """
    Render a modal dialog for creating/editing a calendar entry

    Args:
        marketing_mgr: MarketingProfileManager instance
        user_id: Current user ID
        profile_id: Current profile ID
        entry: Existing entry to edit (None for new entry)
        default_date: Default date for new entries

    Returns:
        bool: True if saved successfully, False otherwise
    """

    is_edit_mode = entry is not None

    st.markdown(f"### {'✏️ Edit' if is_edit_mode else '➕ Add'} Calendar Entry")

    # Initialize form values
    if is_edit_mode:
        scheduled_date = entry.get('scheduled_date', datetime.now().date())
        scheduled_time = entry.get('scheduled_time')
        topic = entry.get('topic', '')
        content_type = entry.get('content_type', 'linkedin_post')
        theme = entry.get('theme', '')
        status = entry.get('status', 'planned')
        draft_text = entry.get('draft_text', '')
    else:
        scheduled_date = default_date.date() if default_date else datetime.now().date()
        scheduled_time = None
        # Check for prefilled data from "Add to Calendar" action
        topic = st.session_state.get('calendar_prefill_topic', '')
        content_type = 'linkedin_post'
        theme = ''
        status = 'planned'
        draft_text = ''

    # Form
    with st.form(key=f"calendar_entry_form_{entry.get('calendar_id', 'new')}"):

        # Date and Time
        col1, col2 = st.columns([2, 1])

        with col1:
            new_date = st.date_input(
                "📅 Scheduled Date",
                value=scheduled_date,
                help="When should this content be published?"
            )

        with col2:
            include_time = st.checkbox("Set specific time", value=scheduled_time is not None)

        if include_time:
            new_time = st.time_input(
                "⏰ Time",
                value=scheduled_time if scheduled_time else time(9, 0),
                help="Specific time to publish"
            )
        else:
            new_time = None

        # Topic
        new_topic = st.text_area(
            "📝 Topic/Title",
            value=topic,
            placeholder="What will this post be about? (e.g., 'Share insights on AI trends in healthcare')",
            height=100,
            help="Describe what you want to post about"
        )

        # Content Type and Theme
        col1, col2 = st.columns(2)

        with col1:
            new_content_type = st.selectbox(
                "🎬 Content Type",
                options=[
                    'linkedin_post',
                    'instagram_post',
                    'article',
                    'announcement',
                    'thought_leadership',
                    'tips',
                    'company_culture',
                    'personal_story'
                ],
                index=['linkedin_post', 'instagram_post', 'article', 'announcement',
                       'thought_leadership', 'tips', 'company_culture', 'personal_story'].index(content_type) if content_type in ['linkedin_post', 'instagram_post', 'article', 'announcement', 'thought_leadership', 'tips', 'company_culture', 'personal_story'] else 0,
                help="Type of content to create"
            )

        with col2:
            new_theme = st.text_input(
                "🏷️ Theme (Optional)",
                value=theme,
                placeholder="e.g., AI Innovation, Leadership",
                help="Link to a content theme from your strategy"
            )

        # Status
        new_status = st.selectbox(
            "📊 Status",
            options=['planned', 'drafted', 'posted', 'skipped'],
            index=['planned', 'drafted', 'posted', 'skipped'].index(status) if status in ['planned', 'drafted', 'posted', 'skipped'] else 0,
            help="Current status of this calendar entry"
        )

        # Draft Text (optional)
        with st.expander("📄 Draft Text (Optional)", expanded=bool(draft_text)):
            new_draft_text = st.text_area(
                "Draft content",
                value=draft_text,
                placeholder="Add draft content or notes here...",
                height=150,
                label_visibility="collapsed"
            )

        # Form buttons
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            submit = st.form_submit_button(
                "💾 Save Entry",
                use_container_width=True,
                type="primary"
            )

        with col2:
            if is_edit_mode:
                delete = st.form_submit_button(
                    "🗑️ Delete",
                    use_container_width=True
                )
            else:
                delete = False

        with col3:
            cancel = st.form_submit_button(
                "Cancel",
                use_container_width=True
            )

        # Handle form submission
        if submit:
            if not new_topic or len(new_topic.strip()) < 5:
                st.error("⚠️ Please provide a topic with at least 5 characters")
                return False

            try:
                # Combine date and time if specified
                scheduled_datetime = datetime.combine(new_date, new_time) if new_time else datetime.combine(new_date, time(0, 0))

                if is_edit_mode:
                    # Update existing entry
                    success = marketing_mgr.update_calendar_entry(
                        calendar_id=entry['calendar_id'],
                        scheduled_date=scheduled_datetime,
                        scheduled_time=scheduled_datetime if new_time else None,
                        topic=new_topic.strip(),
                        content_type=new_content_type,
                        theme=new_theme.strip() if new_theme else None,
                        status=new_status,
                        draft_text=new_draft_text.strip() if new_draft_text else None
                    )

                    if success:
                        st.success("✅ Calendar entry updated successfully!")
                        st.session_state.show_calendar_editor = False
                        st.session_state.editing_calendar_entry = None
                        return True
                    else:
                        st.error("❌ Failed to update calendar entry")
                        return False
                else:
                    # Create new entry
                    calendar_id = marketing_mgr.create_calendar_entry(
                        user_id=user_id,
                        profile_id=profile_id,
                        scheduled_date=scheduled_datetime,
                        topic=new_topic.strip(),
                        content_type=new_content_type,
                        theme=new_theme.strip() if new_theme else None,
                        status=new_status,
                        draft_text=new_draft_text.strip() if new_draft_text else None,
                        scheduled_time=scheduled_datetime if new_time else None
                    )

                    if calendar_id:
                        st.success("✅ Calendar entry created successfully!")
                        st.session_state.show_calendar_editor = False
                        # Clear prefill data
                        if 'calendar_prefill_topic' in st.session_state:
                            del st.session_state.calendar_prefill_topic
                        if 'calendar_prefill_post_id' in st.session_state:
                            del st.session_state.calendar_prefill_post_id
                        return True
                    else:
                        st.error("❌ Failed to create calendar entry")
                        return False

            except Exception as e:
                st.error(f"❌ Error saving calendar entry: {e}")
                return False

        if delete:
            if st.session_state.get('confirm_delete_calendar_entry') == entry.get('calendar_id'):
                # Actually delete
                try:
                    success = marketing_mgr.delete_calendar_entry(entry['calendar_id'])

                    if success:
                        st.success("✅ Calendar entry deleted successfully!")
                        st.session_state.show_calendar_editor = False
                        st.session_state.editing_calendar_entry = None
                        st.session_state.confirm_delete_calendar_entry = None
                        return True
                    else:
                        st.error("❌ Failed to delete calendar entry")
                        return False

                except Exception as e:
                    st.error(f"❌ Error deleting calendar entry: {e}")
                    return False
            else:
                # Ask for confirmation
                st.session_state.confirm_delete_calendar_entry = entry.get('calendar_id')
                st.warning("⚠️ Click Delete again to confirm deletion")
                return False

        if cancel:
            st.session_state.show_calendar_editor = False
            st.session_state.editing_calendar_entry = None
            st.session_state.confirm_delete_calendar_entry = None
            st.rerun()

    return False


def show_calendar_entry_details(entry: Dict[str, Any]) -> None:
    """
    Display read-only details of a calendar entry

    Args:
        entry: Calendar entry dictionary
    """

    # Status badge
    status_emoji_map = {
        'posted': '✅',
        'drafted': '📝',
        'planned': '💡',
        'skipped': '❌'
    }

    status_emoji = status_emoji_map.get(entry.get('status', 'planned'), '📌')

    st.markdown(f"### {status_emoji} {entry.get('topic', 'Untitled')}")

    # Metadata
    col1, col2, col3 = st.columns(3)

    with col1:
        date_str = entry.get('scheduled_date').strftime('%b %d, %Y') if entry.get('scheduled_date') else 'N/A'
        st.markdown(f"**📅 Date:** {date_str}")

    with col2:
        st.markdown(f"**🎬 Type:** {entry.get('content_type', 'N/A')}")

    with col3:
        st.markdown(f"**📊 Status:** {entry.get('status', 'N/A').title()}")

    # Theme
    if entry.get('theme'):
        st.markdown(f"**🏷️ Theme:** {entry['theme']}")

    # Time
    if entry.get('scheduled_time'):
        time_str = entry['scheduled_time'].strftime('%I:%M %p')
        st.markdown(f"**⏰ Time:** {time_str}")

    # Draft text
    if entry.get('draft_text'):
        with st.expander("📄 Draft Text", expanded=True):
            st.text(entry['draft_text'])

    # Linked post
    if entry.get('final_post_id'):
        st.info(f"🔗 Linked to generated post: {entry['final_post_id']}")

    # Performance notes
    if entry.get('performance_notes'):
        with st.expander("📊 Performance Notes"):
            st.text(entry['performance_notes'])

    st.markdown("---")
