import streamlit as st
from components.sidebar import render_sidebar
from agent.database.db_manager import DatabaseManager
from agent.tools import (
    generate_and_download_qualification_excel,
    generate_reasoning_excel,
    generate_bid_plan_excel_bytes,
    generate_assignment_excel_bytes
)
from datetime import datetime
from styles import apply_custom_styles
from auth import require_auth

st.set_page_config(
    page_title="Download Reports - GRANITE",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()

if not require_auth():
    st.stop()

render_sidebar()

st.title("📥 Download Reports")
st.markdown("---")

db = DatabaseManager()

rfps = db.list_recent_rfps(limit=50)

if not rfps:
    st.info("No RFPs found in the database. Process an RFP first to generate reports.")
else:
    st.markdown(f"### Available RFPs ({len(rfps)})")

    for rfp in rfps:
        rfp_id = rfp.get('rfp_id')
        client_name = rfp.get('client_name', 'Unknown')
        project_title = rfp.get('project_title', 'No title')
        processed_date = rfp.get('processed_date')
        status = rfp.get('status', 'unknown')

        if processed_date:
            try:
                date_str = processed_date.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = str(processed_date)
        else:
            date_str = "Unknown date"

        with st.expander(f"📄 {client_name} - {project_title}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**RFP ID:** `{rfp_id}`")
                st.markdown(f"**Client:** {client_name}")
                st.markdown(f"**Project:** {project_title}")
                st.markdown(f"**Processed:** {date_str}")
                st.markdown(f"**Status:** {status}")

            with col2:
                st.markdown("#### Available Reports")

                qual_data = db.get_qualification_results(rfp_id)
                deliverables_data = db.get_rfp_deliverables(rfp_id)
                assignments_data = db.get_rfp_assignments(rfp_id)

                if qual_data:
                    st.success("✅ Qualification Report")

                    col_q1, col_q2 = st.columns(2)

                    with col_q1:
                        if st.button("📊 Main Report", key=f"qual_{rfp_id}"):
                            with st.spinner("Generating qualification report..."):
                                qual_bytes = generate_and_download_qualification_excel(rfp_id)
                                if qual_bytes:
                                    st.download_button(
                                        "⬇️ Download",
                                        data=qual_bytes,
                                        file_name=f"{rfp_id}_qualification.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_qual_{rfp_id}"
                                    )
                                else:
                                    st.error("Failed to generate report")

                    with col_q2:
                        if st.button("📝 Reasoning", key=f"reas_{rfp_id}"):
                            with st.spinner("Generating reasoning report..."):
                                reas_bytes = generate_reasoning_excel(rfp_id)
                                if reas_bytes:
                                    st.download_button(
                                        "⬇️ Download",
                                        data=reas_bytes,
                                        file_name=f"{rfp_id}_reasoning.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_reas_{rfp_id}"
                                    )
                                else:
                                    st.error("Failed to generate report")
                else:
                    st.warning("❌ No Qualification Data")

                if deliverables_data and assignments_data:
                    st.success("✅ Bid Plan Reports")

                    col_b1, col_b2 = st.columns(2)

                    with col_b1:
                        if st.button("📋 Bid Plan", key=f"bid_{rfp_id}"):
                            with st.spinner("Generating bid plan..."):
                                bid_bytes = generate_bid_plan_excel_bytes(rfp_id)
                                if bid_bytes:
                                    st.download_button(
                                        "⬇️ Download",
                                        data=bid_bytes,
                                        file_name=f"{rfp_id}_bid_plan.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_bid_{rfp_id}"
                                    )
                                else:
                                    st.error("Failed to generate report")

                    with col_b2:
                        if st.button("👥 Assignments", key=f"assign_{rfp_id}"):
                            with st.spinner("Generating assignments..."):
                                assign_bytes = generate_assignment_excel_bytes(rfp_id)
                                if assign_bytes:
                                    st.download_button(
                                        "⬇️ Download",
                                        data=assign_bytes,
                                        file_name=f"{rfp_id}_assignments.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"dl_assign_{rfp_id}"
                                    )
                                else:
                                    st.error("Failed to generate report")
                else:
                    st.warning("❌ No Bid Plan Data")

            st.markdown("---")

st.markdown("### 📊 Report Types")
st.markdown("""
- **Qualification Report**: Main qualification analysis with scoring
- **Reasoning Report**: Detailed reasoning for each criterion
- **Bid Plan**: Complete deliverables and planning
- **Assignments**: Team/partner assignment analysis
""")
