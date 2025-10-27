"""
Content Calendar Manager Component
Displays and manages content calendar with week/month views
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable


def get_week_dates(start_date: datetime) -> List[datetime]:
    """Get 7 days starting from start_date"""
    return [start_date + timedelta(days=i) for i in range(7)]


def get_status_emoji_and_color(status: str) -> tuple[str, str]:
    """Get emoji and color for calendar entry status"""
    status_map = {
        'posted': ('✅', '#28a745'),
        'drafted': ('📝', '#ffc107'),
        'planned': ('💡', '#17a2b8'),
        'skipped': ('❌', '#6c757d')
    }
    return status_map.get(status.lower(), ('📌', '#6c757d'))


def render_calendar_week_view(
    calendar_entries: List[Dict[str, Any]],
    profile_id: str,
    user_id: str,
    on_add_entry: Optional[Callable] = None,
    on_edit_entry: Optional[Callable] = None,
    week_offset: int = 0
) -> None:
    """
    Render a week view of the content calendar

    Args:
        calendar_entries: List of calendar entry dictionaries
        profile_id: Current profile ID
        user_id: Current user ID
        on_add_entry: Callback for adding new entry
        on_edit_entry: Callback for editing entry
        week_offset: Number of weeks to offset from current week (0 = current, 1 = next week, -1 = last week)
    """

    # Calculate week dates
    today = datetime.now()
    # Start from Monday of the current week
    start_of_week = today - timedelta(days=today.weekday())
    # Apply week offset
    start_of_week = start_of_week + timedelta(weeks=week_offset)
    week_dates = get_week_dates(start_of_week)

    # Navigation
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

    with col_nav1:
        if st.button("← Previous Week"):
            st.session_state.calendar_week_offset = st.session_state.get('calendar_week_offset', 0) - 1
            st.rerun()

    with col_nav2:
        week_start_str = week_dates[0].strftime('%b %d')
        week_end_str = week_dates[6].strftime('%b %d, %Y')
        st.markdown(f"<h4 style='text-align: center;'>📅 {week_start_str} - {week_end_str}</h4>", unsafe_allow_html=True)

        if week_offset != 0:
            if st.button("↩️ Back to Current Week", use_container_width=True):
                st.session_state.calendar_week_offset = 0
                st.rerun()

    with col_nav3:
        if st.button("Next Week →"):
            st.session_state.calendar_week_offset = st.session_state.get('calendar_week_offset', 0) + 1
            st.rerun()

    st.markdown("---")

    # Group entries by date
    entries_by_date = {}
    for entry in calendar_entries:
        entry_date = entry['scheduled_date']
        if entry_date not in entries_by_date:
            entries_by_date[entry_date] = []
        entries_by_date[entry_date].append(entry)

    # Render calendar grid
    cols = st.columns(7)

    for i, (col, date) in enumerate(zip(cols, week_dates)):
        with col:
            # Day header
            day_name = date.strftime('%a')
            day_num = date.strftime('%d')
            is_today = date.date() == today.date()
            is_past = date.date() < today.date()

            # Header styling
            if is_today:
                header_style = "background: rgba(102, 179, 255, 0.3); border: 2px solid #66b3ff; border-radius: 8px; padding: 8px; text-align: center; margin-bottom: 8px;"
            elif is_past:
                header_style = "background: rgba(108, 117, 125, 0.2); border: 1px solid rgba(108, 117, 125, 0.3); border-radius: 8px; padding: 8px; text-align: center; margin-bottom: 8px;"
            else:
                header_style = "background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 8px; text-align: center; margin-bottom: 8px;"

            st.markdown(f"""
                <div style="{header_style}">
                    <div style="font-weight: 600; font-size: 14px; color: #ffffff;">{day_name}</div>
                    <div style="font-size: 20px; font-weight: 700; color: #ffffff;">{day_num}</div>
                </div>
            """, unsafe_allow_html=True)

            # Get entries for this date
            date_entries = entries_by_date.get(date.date(), [])

            if date_entries:
                for entry in date_entries:
                    status_emoji, status_color = get_status_emoji_and_color(entry['status'])

                    # Entry card
                    topic_short = entry['topic'][:30] + "..." if len(entry['topic']) > 30 else entry['topic']
                    theme_badge = f"<span style='font-size: 10px; color: rgba(255,255,255,0.7);'>🏷️ {entry['theme']}</span>" if entry.get('theme') else ""

                    card_html = f"""
                    <div style="
                        background: rgba(255, 255, 255, 0.05);
                        border-left: 3px solid {status_color};
                        border-radius: 6px;
                        padding: 8px;
                        margin-bottom: 6px;
                        cursor: pointer;
                        transition: all 0.2s;
                    " onmouseover="this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.background='rgba(255,255,255,0.05)'">
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 14px; margin-right: 4px;">{status_emoji}</span>
                            <span style="font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.9);">{entry['content_type']}</span>
                        </div>
                        <div style="font-size: 12px; color: #ffffff; margin-bottom: 4px; line-height: 1.3;">{topic_short}</div>
                        {theme_badge}
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Edit button for each entry
                    if st.button("✏️", key=f"edit_{entry['calendar_id']}", help="Edit this entry"):
                        if on_edit_entry:
                            on_edit_entry(entry)
            else:
                # Empty state
                st.markdown("""
                    <div style="
                        padding: 16px 8px;
                        text-align: center;
                        color: rgba(255,255,255,0.3);
                        font-size: 12px;
                        font-style: italic;
                        min-height: 60px;
                    ">
                        No posts scheduled
                    </div>
                """, unsafe_allow_html=True)

            # Add entry button for each day
            if st.button("➕ Add", key=f"add_{date.date()}", use_container_width=True, type="secondary"):
                if on_add_entry:
                    on_add_entry(date)


def render_calendar_summary(
    calendar_entries: List[Dict[str, Any]]
) -> None:
    """
    Render a summary of calendar statistics

    Args:
        calendar_entries: List of calendar entry dictionaries
    """

    # Count by status
    status_counts = {
        'posted': 0,
        'drafted': 0,
        'planned': 0,
        'skipped': 0
    }

    theme_counts = {}

    for entry in calendar_entries:
        status = entry.get('status', 'planned').lower()
        if status in status_counts:
            status_counts[status] += 1

        theme = entry.get('theme')
        if theme:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

    # Display stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("✅ Posted", status_counts['posted'])

    with col2:
        st.metric("📝 Drafted", status_counts['drafted'])

    with col3:
        st.metric("💡 Planned", status_counts['planned'])

    with col4:
        total = sum(status_counts.values())
        st.metric("📊 Total", total)

    # Theme distribution
    if theme_counts:
        st.markdown("#### 🎨 Theme Distribution")
        theme_cols = st.columns(min(len(theme_counts), 4))
        for i, (theme, count) in enumerate(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)):
            with theme_cols[i % 4]:
                st.markdown(f"**{theme}**: {count}")


def render_calendar_legend() -> None:
    """Render a legend explaining calendar status symbols"""

    st.markdown("""
    <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 16px;">
        <div style="font-weight: 600; margin-bottom: 8px; color: #ffffff;">Legend</div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 13px;">
            <div><span style="color: #28a745;">✅</span> Posted</div>
            <div><span style="color: #ffc107;">📝</span> Drafted</div>
            <div><span style="color: #17a2b8;">💡</span> Planned</div>
            <div><span style="color: #6c757d;">❌</span> Skipped</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
