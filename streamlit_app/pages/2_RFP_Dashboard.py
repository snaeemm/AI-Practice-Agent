import streamlit as st
from components.sidebar import render_sidebar
from components.branding import render_page_header_logo
from components.report_viewers import (
    render_status_badge,
    render_qualification_view,
    render_bid_plan_view,
    render_assignments_view,
    render_overview_tab
)
from components.edit_components import (
    render_edit_metadata,
    render_edit_button,
    render_qualification_edit_form,
    render_deliverables_edit_form,
    render_assignments_edit_form
)
from agent.database.db_manager import DatabaseManager
from agent.database.ui_operations import UIOperations
from styles import apply_custom_styles
from auth import require_auth
from datetime import timezone, timedelta
import json

st.set_page_config(
    page_title="RFP Dashboard - Granite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()

if not require_auth():
    st.stop()

render_sidebar("dashboard")

render_page_header_logo()
st.title("📊 RFP Dashboard")
st.markdown("---")

# Initialize database and UI operations
db = DatabaseManager()
ui_ops = UIOperations(db)

# Session state for navigation and edit modes
if 'selected_rfp' not in st.session_state:
    st.session_state.selected_rfp = None
if 'edit_mode_qual' not in st.session_state:
    st.session_state.edit_mode_qual = False
if 'edit_mode_deliv' not in st.session_state:
    st.session_state.edit_mode_deliv = False
if 'edit_mode_assign' not in st.session_state:
    st.session_state.edit_mode_assign = False

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
            # Get edit metadata
            edit_history = db.get_qualification_edit_history(rfp_id)

            if not st.session_state.edit_mode_qual:
                # View mode
                render_qualification_view(qualification)

                # Show edit metadata
                if edit_history:
                    st.divider()
                    render_edit_metadata(
                        edit_history.get('last_edited_by'),
                        edit_history.get('last_edited_at')
                    )

                # Edit button
                st.divider()
                if st.button("✏️ Edit Qualification", key="edit_qual_btn"):
                    st.session_state.edit_mode_qual = True
                    st.rerun()
            else:
                # Edit mode
                report = qualification.get('qualification_report', {})
                analyses = report.get('analyses', [])
                threshold = report.get('threshold', 2.5)
                max_score = report.get('max_score', 4)

                updated_analyses, updated_threshold, save_clicked = render_qualification_edit_form(
                    analyses,
                    threshold,
                    max_score
                )

                if save_clicked:
                    # Prepare updated report
                    updated_report = dict(report)
                    updated_report['analyses'] = updated_analyses
                    updated_report['threshold'] = updated_threshold

                    # Recalculate scores
                    for analysis in updated_report['analyses']:
                        weight = analysis.get('weight', 1)
                        score = analysis.get('score', 0)
                        analysis['weighted_score'] = (score / max_score) * weight

                    total_score = sum(a.get('weighted_score', 0) for a in updated_report['analyses'])
                    updated_report['total_score'] = total_score
                    updated_report['qualifies'] = total_score >= updated_threshold

                    # Save to database
                    username = st.session_state.user.get('username', 'Unknown')
                    result = ui_ops.update_qualification_full(
                        rfp_id,
                        updated_report,
                        username
                    )

                    if result['success']:
                        st.session_state.edit_mode_qual = False
                        st.success("✅ Qualification updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save: {result.get('message')}")
        else:
            st.warning("❌ This RFP has not been qualified yet.")
            st.info("💡 Upload the RFP document and run qualification to see results here.")

    # Tab 3: Bid Plan
    with tabs[2]:
        if has_bid:
            # Get edit metadata
            edit_history = db.get_deliverables_edit_history(rfp_id)

            if not st.session_state.edit_mode_deliv:
                # View mode
                render_bid_plan_view(deliverables)

                # Show edit metadata
                if edit_history:
                    st.divider()
                    render_edit_metadata(
                        edit_history.get('last_edited_by'),
                        edit_history.get('last_edited_at')
                    )

                # Edit button
                st.divider()
                if st.button("✏️ Edit Bid Plan", key="edit_deliv_btn"):
                    st.session_state.edit_mode_deliv = True
                    st.rerun()
            else:
                # Edit mode - load owners list from capabilities
                try:
                    capabilities = db.get_config_file('capabilities.json')
                    owners_list = []
                    if capabilities:
                        owners_list.append("Granite MENA")
                        if 'partners' in capabilities:
                            for partner in capabilities.get('partners', []):
                                owners_list.append(partner.get('partner_name', 'Unknown'))
                    if not owners_list:
                        owners_list = ["Granite MENA", "Partner A", "Partner B"]
                except:
                    owners_list = ["Granite MENA", "Partner A", "Partner B"]

                tech_deliv = deliverables.get('technical_deliverables', [])
                comm_deliv = deliverables.get('commercial_deliverables', [])

                updated_tech, updated_comm, save_clicked = render_deliverables_edit_form(
                    tech_deliv,
                    comm_deliv,
                    owners_list
                )

                if save_clicked:
                    # Save to database
                    username = st.session_state.user.get('username', 'Unknown')
                    result = ui_ops.update_deliverables_full(
                        rfp_id,
                        updated_tech,
                        updated_comm,
                        username
                    )

                    if result['success']:
                        st.session_state.edit_mode_deliv = False
                        st.success("✅ Deliverables updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save: {result.get('message')}")
        else:
            st.warning("❌ Bid plan has not been created yet.")
            if has_qual:
                st.info("💡 Run bid planning in the chat to generate deliverables and see them here.")
            else:
                st.info("💡 Qualify the RFP first, then run bid planning to see results here.")

    # Tab 4: Assignments
    with tabs[3]:
        if assignments:
            # Get edit metadata
            edit_history = db.get_assignments_edit_history(rfp_id)

            if not st.session_state.edit_mode_assign:
                # View mode
                render_assignments_view(assignments)

                # Show edit metadata
                if edit_history:
                    st.divider()
                    render_edit_metadata(
                        edit_history.get('last_edited_by'),
                        edit_history.get('last_edited_at')
                    )

                # Edit button
                st.divider()
                if st.button("✏️ Edit Assignments", key="edit_assign_btn"):
                    st.session_state.edit_mode_assign = True
                    st.rerun()
            else:
                # Edit mode - load owners list from capabilities
                try:
                    capabilities = db.get_config_file('capabilities.json')
                    owners_list = []
                    if capabilities:
                        owners_list.append("Granite MENA")
                        if 'partners' in capabilities:
                            for partner in capabilities.get('partners', []):
                                owners_list.append(partner.get('partner_name', 'Unknown'))
                    if not owners_list:
                        owners_list = ["Granite MENA", "Partner A", "Partner B"]
                except:
                    owners_list = ["Granite MENA", "Partner A", "Partner B"]

                report = assignments.get('assignment_report', {})
                assignment_list = report.get('assignments', [])

                updated_assignments, save_clicked = render_assignments_edit_form(
                    assignment_list,
                    owners_list
                )

                if save_clicked:
                    # Prepare updated report
                    updated_report = dict(report)
                    updated_report['assignments'] = updated_assignments

                    # Recalculate counts
                    granite_count = sum(
                        1 for a in updated_report['assignments']
                        if 'Granite' in a.get('assigned_owner', '')
                    )
                    partner_count = len(updated_report['assignments']) - granite_count
                    updated_report['granite_assigned'] = granite_count
                    updated_report['partner_assigned'] = partner_count

                    # Save to database
                    username = st.session_state.user.get('username', 'Unknown')
                    result = ui_ops.update_assignments_full(
                        rfp_id,
                        updated_report,
                        username
                    )

                    if result['success']:
                        st.session_state.edit_mode_assign = False
                        st.success("✅ Assignments updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save: {result.get('message')}")
        else:
            st.warning("❌ No assignment data available.")
            if has_bid:
                st.info("💡 Assignment data should be generated with the bid plan.")
            else:
                st.info("💡 Create a bid plan first to see assignment analysis.")
