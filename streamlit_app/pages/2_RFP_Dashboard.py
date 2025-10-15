import streamlit as st
from components.sidebar import render_sidebar
from components.report_viewers import (
    render_status_badge,
    render_qualification_view,
    render_bid_plan_view,
    render_assignments_view,
    render_overview_tab
)
from agent.database.db_manager import DatabaseManager
from styles import apply_custom_styles
from auth import require_auth
from datetime import timezone, timedelta

st.set_page_config(
    page_title="RFP Dashboard - GRANITE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()

if not require_auth():
    st.stop()

render_sidebar("dashboard")

# Initialize database
db = DatabaseManager()

# Session state for navigation
if 'selected_rfp' not in st.session_state:
    st.session_state.selected_rfp = None

# Main Dashboard View
if not st.session_state.selected_rfp:
    st.markdown("# 📊 RFP Dashboard")
    st.markdown("View and analyze all your processed RFPs")
    st.markdown("---")

    # Fetch all RFPs
    rfps = db.list_recent_rfps(limit=100)

    if not rfps:
        st.info("📭 No RFPs found. Process an RFP to see it here!")
    else:
        st.markdown(f"## 📋 Available RFPs ({len(rfps)})")

        # Display RFPs as cards
        for rfp in rfps:
            rfp_id = rfp.get('rfp_id')
            client_name = rfp.get('client_name', 'Unknown Client')
            project_title = rfp.get('project_title', 'No Title')
            processed_date = rfp.get('processed_date')
            status = rfp.get('status', 'unknown')

            # Check if qualification and bid plan exist
            qual_data = db.get_qualification_results(rfp_id)
            deliverables_data = db.get_rfp_deliverables(rfp_id)

            has_qual = bool(qual_data)
            has_bid = bool(deliverables_data)

            # Format date
            if processed_date:
                try:
                    uae_tz = timezone(timedelta(hours=4))
                    if processed_date.tzinfo is None:
                        processed_date = processed_date.replace(tzinfo=timezone.utc)
                    uae_date = processed_date.astimezone(uae_tz)
                    date_str = uae_date.strftime("%B %d, %Y at %H:%M")
                except:
                    date_str = str(processed_date)
            else:
                date_str = "Unknown date"

            # Create card
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"#### 📄 {project_title}")
                    st.caption(f"🕒 Processed: {date_str}")

                    # Status badges in same row
                    badge_col1, badge_col2 = st.columns(2)
                    with badge_col1:
                        if has_qual:
                            qual_report = qual_data.get('qualification_report', {})
                            qualifies = qual_report.get('qualifies', False)
                            if qualifies:
                                st.success("✅ Qualified - PURSUE")
                            else:
                                st.error("❌ Qualified - DECLINE")
                        else:
                            st.warning("⏳ Not Yet Qualified")

                    with badge_col2:
                        if has_bid:
                            st.success("✅ Bid Plan Complete")
                        else:
                            st.warning("⏳ Bid Plan Pending")

                with col2:
                    if st.button("View Details →", key=f"view_{rfp_id}", use_container_width=True):
                        st.session_state.selected_rfp = rfp_id
                        st.rerun()

                st.markdown("---")

# Detailed RFP View
else:
    rfp_id = st.session_state.selected_rfp

    # Back button
    if st.button("🔙 Back to Dashboard"):
        st.session_state.selected_rfp = None
        st.rerun()

    # Fetch complete data
    complete_data = db.get_complete_rfp_data(rfp_id)

    document = complete_data.get('document', {})
    qualification = complete_data.get('qualification')
    deliverables = complete_data.get('deliverables')
    assignments = complete_data.get('assignments')
    raw_data = complete_data.get('raw_data')

    # Header
    project_title = document.get('project_title', 'No Title')

    st.markdown(f"## 📄 {project_title}")
    st.markdown("---")

    # Status badges
    has_qual = bool(qualification)
    has_bid = bool(deliverables)
    render_status_badge(has_qual, has_bid)

    st.markdown("---")

    # Tabs
    tabs = st.tabs(["📊 Overview", "✅ Qualification", "📋 Bid Plan", "👥 Assignments"])

    # Tab 1: Overview
    with tabs[0]:
        render_overview_tab(complete_data)

    # Tab 2: Qualification
    with tabs[1]:
        if has_qual:
            render_qualification_view(qualification)
        else:
            st.warning("❌ This RFP has not been qualified yet.")
            st.info("💡 Upload the RFP document and run qualification to see results here.")

    # Tab 3: Bid Plan
    with tabs[2]:
        if has_bid:
            render_bid_plan_view(deliverables)
        else:
            st.warning("❌ Bid plan has not been created yet.")
            if has_qual:
                st.info("💡 Run bid planning in the chat to generate deliverables and see them here.")
            else:
                st.info("💡 Qualify the RFP first, then run bid planning to see results here.")

    # Tab 4: Assignments
    with tabs[3]:
        if assignments:
            render_assignments_view(assignments)
        else:
            st.warning("❌ No assignment data available.")
            if has_bid:
                st.info("💡 Assignment data should be generated with the bid plan.")
            else:
                st.info("💡 Create a bid plan first to see assignment analysis.")
