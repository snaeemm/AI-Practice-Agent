import streamlit as st
from typing import Dict, Any, Optional, List
import pandas as pd

def render_star_rating(score: int, max_score: int = 4) -> str:
    """Convert numeric score to star rating"""
    filled = "⭐" * score
    empty = "☆" * (max_score - score)
    return f"{filled}{empty}"

def render_status_badge(has_qual: bool, has_bid: bool):
    """Render status badges for qualification and bid plan"""
    col1, col2 = st.columns(2)
    with col1:
        if has_qual:
            st.success("✅ Qualification Complete")
        else:
            st.warning("❌ Not Yet Qualified")
    with col2:
        if has_bid:
            st.success("✅ Bid Plan Complete")
        else:
            st.warning("❌ Bid Plan Pending")

def render_qualification_view(qual_data: Optional[Dict[str, Any]]):
    """Render qualification report view"""
    if not qual_data:
        st.warning("❌ No qualification data available")
        return

    report = qual_data.get('qualification_report', {})

    if not report:
        st.warning("❌ Qualification report is empty")
        return

    # Decision Header with prominent display
    qualifies = report.get('qualifies', False)
    total_score = report.get('total_score', 0)
    threshold = report.get('threshold', 0)

    if qualifies:
        st.success("### ✅ RECOMMENDATION: PURSUE")
    else:
        st.error("### ❌ RECOMMENDATION: DECLINE")

    # Key Metrics Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Score", f"{total_score:.1f}", delta=f"{total_score - threshold:.1f} vs threshold")
    with col2:
        st.metric("Threshold", f"{threshold:.1f}")
    with col3:
        analyses = report.get('analyses', [])
        avg_score = sum(a.get('score', 0) for a in analyses) / len(analyses) if analyses else 0
        st.metric("Avg Score", f"{avg_score:.1f}/4", render_star_rating(int(avg_score)))

    st.markdown("---")

    # Scorecard Table
    st.markdown("### 📊 Qualification Scorecard")

    analyses = report.get('analyses', [])
    if analyses:
        # Display as cards instead of table for better readability
        for analysis in analyses:
            score = analysis.get('score', 0)
            criterion = analysis.get('criterion', 'N/A')
            weighted = analysis.get('weighted_score', 0)

            # Color code based on score - dark theme compatible
            if score >= 3:
                border_color = "#28a745"
                badge_color = "rgba(40, 167, 69, 0.2)"
            elif score >= 2:
                border_color = "#ffc107"
                badge_color = "rgba(255, 193, 7, 0.2)"
            else:
                border_color = "#dc3545"
                badge_color = "rgba(220, 53, 69, 0.2)"

            with st.container():
                st.markdown(f"""
                <div style="background-color: #16385c; border-left: 5px solid {border_color}; padding: 15px; margin-bottom: 15px; border-radius: 8px; border: 1px solid rgba(47, 115, 177, 0.3); border-left: 5px solid {border_color};">
                    <h4 style="margin: 0 0 10px 0; color: #ffffff;">{criterion}</h4>
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <span style="font-size: 1.3em;">{render_star_rating(score)}</span>
                            <span style="margin-left: 10px; color: #aaaaaa;">Score: {score}/4 | Weighted: {weighted:.2f}</span>
                        </div>
                        <div style="background: {badge_color}; border: 1px solid {border_color}; padding: 6px 12px; border-radius: 4px;">
                            <strong style="color: #ffffff;">{analysis.get('selected_option', 'N/A')}</strong>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Reasoning in expander
                with st.expander("📝 View Reasoning"):
                    st.write(analysis.get('reasoning', 'No reasoning provided'))

                    missing_justification = analysis.get('missing_data_justification')
                    if missing_justification:
                        st.markdown("**Missing Data Justification:**")
                        st.info(missing_justification)

    # Executive Summary
    exec_summary = report.get('executive_summary')
    if exec_summary:
        st.markdown("---")
        st.markdown("### 📋 Executive Summary")
        st.write(exec_summary)

    # Recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        st.markdown("---")
        st.markdown("### 💡 Recommendations")
        for rec in recommendations:
            st.markdown(f"• {rec}")

    # Strategic Context
    qual_context = report.get('qualification_context')
    if qual_context:
        st.markdown("---")
        st.markdown("### 🎯 Strategic Context")

        col1, col2 = st.columns(2)

        with col1:
            gaps = qual_context.get('capability_gaps', [])
            if gaps:
                st.markdown("**⚠️ Capability Gaps:**")
                for gap in gaps:
                    st.markdown(f"• {gap}")

            risks = qual_context.get('risk_factors', [])
            if risks:
                st.markdown("**⚠️ Risk Factors:**")
                for risk in risks:
                    st.markdown(f"• {risk}")

        with col2:
            advantages = qual_context.get('competitive_advantages', [])
            if advantages:
                st.markdown("**✅ Competitive Advantages:**")
                for adv in advantages:
                    st.markdown(f"• {adv}")

            opportunities = qual_context.get('opportunity_factors', [])
            if opportunities:
                st.markdown("**✨ Opportunity Factors:**")
                for opp in opportunities:
                    st.markdown(f"• {opp}")

def render_bid_plan_view(deliverables_data: Optional[Dict[str, Any]]):
    """Render bid plan deliverables view"""
    if not deliverables_data:
        st.warning("❌ No bid plan data available")
        return

    client_opp = deliverables_data.get('client_and_opportunity', 'N/A')
    st.info(f"**📊 Client & Opportunity:** {client_opp}")

    # Summary metrics
    technical = deliverables_data.get('technical_deliverables', [])
    commercial = deliverables_data.get('commercial_deliverables', [])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Deliverables", len(technical) + len(commercial))
    with col2:
        st.metric("Technical", len(technical))
    with col3:
        st.metric("Commercial", len(commercial))

    st.markdown("---")

    # Technical Deliverables
    if technical:
        st.markdown("### 📋 Technical Deliverables")
        for idx, item in enumerate(technical, 1):
            section = item.get('section', 'N/A')
            requirement = item.get('requirement', 'No requirement specified')
            format_type = item.get('format', '—')
            page_limit = item.get('page_limit', '—')
            owner = item.get('owner', 'Unassigned')

            # Owner badge color
            owner_color = "#0066cc" if owner != 'Unassigned' else "#999"

            with st.expander(f"**{idx}. {section}**", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**📄 Requirement:**")
                    st.write(requirement)
                with col2:
                    st.markdown(f"**Format:** {format_type}")
                    st.markdown(f"**Page Limit:** {page_limit}")
                    st.markdown(f"**👤 Owner:** <span style='color: {owner_color}; font-weight: bold;'>{owner}</span>", unsafe_allow_html=True)
    else:
        st.info("No technical deliverables found")

    st.markdown("---")

    # Commercial Deliverables
    if commercial:
        st.markdown("### 💰 Commercial Deliverables")
        for idx, item in enumerate(commercial, 1):
            section = item.get('section', 'N/A')
            requirement = item.get('requirement', 'No requirement specified')
            format_type = item.get('format', '—')
            page_limit = item.get('page_limit', '—')
            owner = item.get('owner', 'Unassigned')

            # Owner badge color
            owner_color = "#0066cc" if owner != 'Unassigned' else "#999"

            with st.expander(f"**{idx}. {section}**", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**📄 Requirement:**")
                    st.write(requirement)
                with col2:
                    st.markdown(f"**Format:** {format_type}")
                    st.markdown(f"**Page Limit:** {page_limit}")
                    st.markdown(f"**👤 Owner:** <span style='color: {owner_color}; font-weight: bold;'>{owner}</span>", unsafe_allow_html=True)
    else:
        st.info("No commercial deliverables found")

def render_assignments_view(assignments_data: Optional[Dict[str, Any]]):
    """Render assignment analysis view"""
    if not assignments_data:
        st.warning("❌ No assignment data available")
        return

    report = assignments_data.get('assignment_report', {})

    if not report:
        st.warning("❌ Assignment report is empty")
        return

    # Summary Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Deliverables", report.get('total_deliverables', 0))
    with col2:
        granite = report.get('granite_assigned', 0)
        st.metric("🔵 Granite", granite)
    with col3:
        partners = report.get('partner_assigned', 0)
        st.metric("🟢 Partners", partners)
    with col4:
        total = report.get('total_deliverables', 0)
        granite_pct = (granite / total * 100) if total > 0 else 0
        st.metric("Granite %", f"{granite_pct:.0f}%")

    st.markdown("---")

    # Assignments by owner type
    assignments = report.get('assignments', [])
    if assignments:
        # Separate by owner type
        granite_assignments = []
        partner_assignments = []

        for assignment in assignments:
            owner = assignment.get('assigned_owner', 'Unassigned')
            if 'Granite MENA' in owner or 'Granite Ireland' in owner:
                granite_assignments.append(assignment)
            else:
                partner_assignments.append(assignment)

        # Display Granite assignments
        if granite_assignments:
            st.markdown("### 🔵 Granite MENA Assignments")
            for assignment in granite_assignments:
                deliverable = assignment.get('deliverable_section', 'N/A')
                owner = assignment.get('assigned_owner', 'Unassigned')

                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #16385c; border-left: 5px solid #66b3ff; padding: 15px; margin-bottom: 10px; border-radius: 8px; border: 1px solid rgba(102, 179, 255, 0.3);">
                        <h4 style="margin: 0; color: #66b3ff;">📋 {deliverable}</h4>
                        <p style="margin: 5px 0 0 0; color: #aaaaaa;"><strong style="color: #ffffff;">Assigned to:</strong> {owner}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("📝 View Details"):
                        st.markdown("**Requirement:**")
                        st.write(assignment.get('deliverable_requirement', 'No requirement specified'))

                        st.markdown("**Assignment Reasoning:**")
                        st.info(assignment.get('reasoning', 'No reasoning provided'))

                        alternatives = assignment.get('alternative_partners', [])
                        if alternatives:
                            st.markdown("**Alternative Partners:**")
                            for alt in alternatives:
                                st.markdown(f"• {alt}")

        # Display Partner assignments
        if partner_assignments:
            st.markdown("---")
            st.markdown("### 🟢 Partner Assignments")
            for assignment in partner_assignments:
                deliverable = assignment.get('deliverable_section', 'N/A')
                owner = assignment.get('assigned_owner', 'Unassigned')

                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #16385c; border-left: 5px solid #28a745; padding: 15px; margin-bottom: 10px; border-radius: 8px; border: 1px solid rgba(40, 167, 69, 0.3);">
                        <h4 style="margin: 0; color: #5cb85c;">📋 {deliverable}</h4>
                        <p style="margin: 5px 0 0 0; color: #aaaaaa;"><strong style="color: #ffffff;">Assigned to:</strong> {owner}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("📝 View Details"):
                        st.markdown("**Requirement:**")
                        st.write(assignment.get('deliverable_requirement', 'No requirement specified'))

                        st.markdown("**Assignment Reasoning:**")
                        st.info(assignment.get('reasoning', 'No reasoning provided'))

                        alternatives = assignment.get('alternative_partners', [])
                        if alternatives:
                            st.markdown("**Alternative Partners:**")
                            for alt in alternatives:
                                st.markdown(f"• {alt}")
    else:
        st.info("No assignments found")

def render_raw_data_view(document_data: Optional[Dict[str, Any]]):
    """Render raw RFP metadata view"""
    if not document_data:
        st.warning("❌ No RFP data available")
        return

    rfp_data = document_data.get('rfp_data', {})

    if not rfp_data:
        st.warning("❌ RFP data is empty")
        return

    st.markdown("### 📄 Extracted RFP Metadata")

    # Helper to render estimated value fields
    def render_field(label: str, field_data: Optional[Dict[str, Any]]):
        if not field_data:
            st.markdown(f"**{label}:** —")
            return

        if isinstance(field_data, str):
            st.markdown(f"**{label}:** {field_data}")
            return

        value = field_data.get('value', '—')
        source = field_data.get('source', 'Unknown')
        confidence = field_data.get('confidence_level')

        # Color code source
        if source == 'Extracted':
            source_badge = "🟢 Extracted"
        elif source == 'Estimated':
            source_badge = "🟡 Estimated"
        elif source == 'User_Provided':
            source_badge = "🔵 User Provided"
        else:
            source_badge = "⚪ Unknown"

        st.markdown(f"**{label}:** {value}")
        st.caption(f"{source_badge} {f'| Confidence: {confidence}' if confidence else ''}")

    col1, col2 = st.columns(2)

    with col1:
        render_field("Client & Opportunity", rfp_data.get('client_and_opportunity'))
        render_field("Contract Value", rfp_data.get('estimated_contract_value'))
        render_field("Timeline", rfp_data.get('timeline'))
        render_field("Submission Deadline", rfp_data.get('submission_deadline'))
        render_field("Client Type", rfp_data.get('client_type'))
        render_field("Industry Sector", rfp_data.get('industry_sector'))

    with col2:
        render_field("Region", rfp_data.get('region'))
        render_field("RFP Type", rfp_data.get('rfp_type'))
        render_field("Complexity Indicators", rfp_data.get('complexity_indicators'))

    # Project Details
    st.markdown("---")
    st.markdown("### 📋 Project Details")

    objectives = rfp_data.get('project_objectives')
    if objectives:
        obj_value = objectives.get('value') if isinstance(objectives, dict) else objectives
        if obj_value:
            with st.expander("🎯 Project Objectives"):
                st.write(obj_value)

    scope = rfp_data.get('scope_of_work')
    if scope:
        scope_value = scope.get('value') if isinstance(scope, dict) else scope
        if scope_value:
            with st.expander("📐 Scope of Work"):
                st.write(scope_value)

    notes = rfp_data.get('additional_notes')
    if notes:
        notes_value = notes.get('value') if isinstance(notes, dict) else notes
        if notes_value:
            with st.expander("📝 Additional Notes"):
                st.write(notes_value)

def render_overview_tab(complete_data: Dict[str, Any]):
    """Render overview summary tab"""
    document = complete_data.get('document', {})
    qualification = complete_data.get('qualification', {})
    deliverables = complete_data.get('deliverables', {})
    assignments = complete_data.get('assignments', {})

    # Header Card
    st.markdown("### 📊 RFP Overview")

    # Just show project title
    project_title = document.get('project_title', 'N/A')
    st.markdown(f"**Project:** {project_title}")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if qualification:
            qual_report = qualification.get('qualification_report', {})
            score = qual_report.get('total_score', 0)
            threshold = qual_report.get('threshold', 0)
            st.metric("Qualification Score", f"{score:.1f}/{threshold:.1f}")
        else:
            st.metric("Qualification Score", "—")

    with col2:
        processed_date = document.get('processed_date')
        if processed_date:
            st.metric("Processed Date", processed_date.strftime("%Y-%m-%d"))
        else:
            st.metric("Processed Date", "—")

    with col3:
        st.markdown("**Status:**")
        if qualification:
            qual_report = qualification.get('qualification_report', {})
            qualifies = qual_report.get('qualifies', False)
            if qualifies:
                st.success("✅ PURSUE")
            else:
                st.error("❌ DECLINE")
        else:
            st.warning("⏳ Pending")

    # Additional metrics
    col1, col2 = st.columns(2)

    with col1:
        if assignments:
            report = assignments.get('assignment_report', {})
            total = report.get('total_deliverables', 0)
            st.metric("Total Deliverables", total)
        else:
            st.metric("Total Deliverables", "—")

    with col2:
        if deliverables:
            tech_count = len(deliverables.get('technical_deliverables', []))
            comm_count = len(deliverables.get('commercial_deliverables', []))
            st.metric("Tech/Comm Split", f"{tech_count}/{comm_count}")
        else:
            st.metric("Tech/Comm Split", "—")

    st.markdown("---")

    # Key Information
    st.markdown("### 📋 Key Information")

    raw_data = complete_data.get('raw_data', {})
    if raw_data and isinstance(raw_data, dict):
        rfp_data = raw_data.get('rfp_data', {})

        # Handle case where rfp_data might be a string (shouldn't happen but be defensive)
        if isinstance(rfp_data, str):
            import json
            try:
                rfp_data = json.loads(rfp_data)
            except:
                rfp_data = {}

        if isinstance(rfp_data, dict):
            def extract_value(field_data):
                if isinstance(field_data, dict):
                    return field_data.get('value')
                return field_data

            col1, col2 = st.columns(2)
            has_data = False

            with col1:
                budget = extract_value(rfp_data.get('estimated_contract_value'))
                if budget:
                    st.markdown(f"**💰 Budget:** {budget}")
                    has_data = True

                timeline = extract_value(rfp_data.get('timeline'))
                if timeline:
                    st.markdown(f"**⏱️ Timeline:** {timeline}")
                    has_data = True

                deadline = extract_value(rfp_data.get('submission_deadline'))
                if deadline:
                    st.markdown(f"**📅 Submission Deadline:** {deadline}")
                    has_data = True

            with col2:
                industry = extract_value(rfp_data.get('industry_sector'))
                if industry:
                    st.markdown(f"**🏭 Industry:** {industry}")
                    has_data = True

                region = extract_value(rfp_data.get('region'))
                if region:
                    st.markdown(f"**🌍 Region:** {region}")
                    has_data = True

                rfp_type = extract_value(rfp_data.get('rfp_type'))
                if rfp_type:
                    st.markdown(f"**📂 RFP Type:** {rfp_type}")
                    has_data = True

            if not has_data:
                st.info("No key information available yet")
        else:
            st.info("No key information available yet")
    else:
        st.info("No key information available yet")
