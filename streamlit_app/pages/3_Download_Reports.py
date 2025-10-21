import streamlit as st
from components.sidebar import render_sidebar
from components.branding import render_page_header_logo
from agent.database.db_manager import DatabaseManager
from agent.tools import (
    generate_and_download_qualification_excel,
    generate_reasoning_excel,
    generate_bid_plan_excel_bytes,
    generate_assignment_excel_bytes
)
from datetime import datetime, timezone, timedelta
from styles import apply_custom_styles
from auth import require_auth

st.set_page_config(
    page_title="Download Reports - Granite",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()

if not require_auth():
    st.stop()

render_page_header_logo()

render_sidebar("download")

db = DatabaseManager()

rfps = db.list_recent_rfps(limit=50)

if not rfps:
    st.markdown("# 📥 Download Reports")
    st.markdown("Generate and download analysis reports for your RFPs")
    st.markdown("---")
    st.info("📭 No RFPs found in the database. Process an RFP first to generate reports.")
else:
    st.markdown(f"# 📥 Download Reports")
    st.markdown(f"Generate and download analysis reports for your RFPs ({len(rfps)})")
    st.markdown("---")

    for rfp in rfps:
        rfp_id = rfp.get('rfp_id')
        client_name = rfp.get('client_name', 'Unknown')
        project_title = rfp.get('project_title', 'No title')
        processed_date = rfp.get('processed_date')
        status = rfp.get('status', 'unknown')

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

        # Check available reports
        qual_data = db.get_qualification_results(rfp_id)
        deliverables_data = db.get_rfp_deliverables(rfp_id)
        assignments_data = db.get_rfp_assignments(rfp_id)

        has_qual = bool(qual_data)
        has_bid = bool(deliverables_data and assignments_data)

        # Create card
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"#### 📄 {client_name} - {project_title}")
                st.caption(f"📌 RFP ID: `{rfp_id}` • 🕒 {date_str}")

                # Status badges
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
                if st.button("📥 Downloads →", key=f"view_downloads_{rfp_id}", use_container_width=True):
                    st.session_state[f"show_downloads_{rfp_id}"] = not st.session_state.get(f"show_downloads_{rfp_id}", False)
                    st.rerun()

            # Download buttons (shown when expanded)
            if st.session_state.get(f"show_downloads_{rfp_id}", False):
                st.divider()

                # Qualification reports
                if has_qual:
                    st.markdown("**📊 Qualification Reports**")
                    qual_col1, qual_col2 = st.columns(2)

                    with qual_col1:
                        if st.button("📊 Main Report", key=f"qual_{rfp_id}", use_container_width=True):
                            with st.spinner("Generating qualification report..."):
                                qual_bytes = generate_and_download_qualification_excel(rfp_id)
                                if qual_bytes:
                                    st.download_button(
                                        "⬇️ Download Qualification",
                                        data=qual_bytes,
                                        file_name=f"{rfp_id}_qualification.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_qual_{rfp_id}",
                                        use_container_width=True
                                    )
                                else:
                                    st.error("Failed to generate report")

                    with qual_col2:
                        if st.button("📝 Reasoning", key=f"reas_{rfp_id}", use_container_width=True):
                            with st.spinner("Generating reasoning report..."):
                                reas_bytes = generate_reasoning_excel(rfp_id)
                                if reas_bytes:
                                    st.download_button(
                                        "⬇️ Download Reasoning",
                                        data=reas_bytes,
                                        file_name=f"{rfp_id}_reasoning.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_reas_{rfp_id}",
                                        use_container_width=True
                                    )
                                else:
                                    st.error("Failed to generate report")

                # Bid Plan reports
                if has_bid:
                    st.markdown("**📋 Bid Plan Reports**")
                    bid_col1, bid_col2 = st.columns(2)

                    with bid_col1:
                        if st.button("📋 Bid Plan", key=f"bid_{rfp_id}", use_container_width=True):
                            with st.spinner("Generating bid plan..."):
                                bid_bytes = generate_bid_plan_excel_bytes(rfp_id)
                                if bid_bytes:
                                    st.download_button(
                                        "⬇️ Download Bid Plan",
                                        data=bid_bytes,
                                        file_name=f"{rfp_id}_bid_plan.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_bid_{rfp_id}",
                                        use_container_width=True
                                    )
                                else:
                                    st.error("Failed to generate report")

                    with bid_col2:
                        if st.button("👥 Assignments", key=f"assign_{rfp_id}", use_container_width=True):
                            with st.spinner("Generating assignments..."):
                                assign_bytes = generate_assignment_excel_bytes(rfp_id)
                                if assign_bytes:
                                    st.download_button(
                                        "⬇️ Download Assignments",
                                        data=assign_bytes,
                                        file_name=f"{rfp_id}_assignments.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_assign_{rfp_id}",
                                        use_container_width=True
                                    )
                                else:
                                    st.error("Failed to generate report")

                # Delete section
                st.divider()
                st.markdown("**🗑️ Delete RFP**")

                if st.button("🗑️ Delete This RFP", key=f"delete_{rfp_id}", type="secondary", use_container_width=True):
                    if 'confirm_delete' not in st.session_state:
                        st.session_state.confirm_delete = {}
                    st.session_state.confirm_delete[rfp_id] = True

                if st.session_state.get('confirm_delete', {}).get(rfp_id, False):
                    st.warning("⚠️ **Are you sure?** This will permanently delete all data for this RFP.")
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        if st.button("✅ Yes, Delete", key=f"confirm_delete_{rfp_id}", type="primary", use_container_width=True):
                            with st.spinner("Deleting RFP..."):
                                result = db.delete_rfp_document(rfp_id)
                                if result.get('success'):
                                    st.success(f"✅ {result.get('message')}")
                                    if 'confirm_delete' in st.session_state:
                                        st.session_state.confirm_delete.pop(rfp_id, None)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result.get('message')}")
                    with col_d2:
                        if st.button("❌ Cancel", key=f"cancel_delete_{rfp_id}", use_container_width=True):
                            st.session_state.confirm_delete.pop(rfp_id, None)
                            st.rerun()

            st.markdown("---")
