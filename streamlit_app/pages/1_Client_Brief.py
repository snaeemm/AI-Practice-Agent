import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.database.db_manager import DatabaseManager
from agent.database.ui_operations import UIOperations
from components.sidebar import render_sidebar
from components.edit_components import render_edit_metadata
from components.client_brief_edit import (
    render_client_overview_edit_form,
    render_granite_opportunity_edit_form
)
from auth import require_auth
from styles import apply_custom_styles
import json

st.set_page_config(page_title="Client Brief Generator", page_icon="📋", layout="wide")

apply_custom_styles()

if not require_auth():
    st.stop()

render_sidebar("client_brief")

st.title("📋 Client Brief")

db_manager = DatabaseManager()
ui_ops = UIOperations(db_manager)

# Initialize session state for brief selection and edit modes
if 'selected_brief_id' not in st.session_state:
    st.session_state.selected_brief_id = None
if 'edit_mode_brief_overview' not in st.session_state:
    st.session_state.edit_mode_brief_overview = False
if 'edit_mode_brief_opportunity' not in st.session_state:
    st.session_state.edit_mode_brief_opportunity = False

# Back button at top (always visible)
if st.session_state.selected_brief_id:
    col_back, col_space = st.columns([1, 10])
    with col_back:
        if st.button("🔙 Back to Briefs", use_container_width=True, key="back_to_briefs"):
            st.session_state.selected_brief_id = None
            st.rerun()
    st.markdown("---")

# View selected brief or show prompt
if not st.session_state.selected_brief_id:
    st.info("👈 Select a client brief from the sidebar to view its details")
else:
    brief_id = st.session_state.selected_brief_id

    # Fetch the brief details
    briefs = db_manager.list_client_briefs(limit=100)
    selected_brief = next((b for b in briefs if b['id'] == brief_id), None)

    if not selected_brief:
        st.error(f"Brief {brief_id} not found")
    else:
        brief_id = selected_brief['id']
        client_name = selected_brief['client_name']
        created_date = selected_brief['created_date'].strftime("%Y-%m-%d %H:%M") if selected_brief['created_date'] else "N/A"
        created_by = selected_brief.get('created_by') or "Agent"
        brief_data = selected_brief['brief_data']

        st.markdown(f"## {client_name} Brief")
        st.markdown(f"**ID:** {brief_id} | **Created:** {created_date} by {created_by}")

        tab_overview, tab_opportunity = st.tabs(["🏢 Client Overview", "💡 Granite Opportunity"])

        with tab_overview:
            client_overview = brief_data.get('client_overview', {})
            edit_history = db_manager.get_brief_edit_history(brief_id)

            if not st.session_state.edit_mode_brief_overview:
                # View mode
                st.subheader("🏢 Context & Organization")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Organization:** {client_overview.get('organization_overview', 'N/A')}")
                    st.markdown(f"**Industry:** {client_overview.get('industry', 'N/A')}")
                with col2:
                    st.markdown(f"**Size:** {client_overview.get('size_of_business', 'N/A')}")
                    st.markdown(f"**Region:** {client_overview.get('region_focus', 'N/A')}")
                with col3:
                    st.markdown(f"**Digital Maturity:** {client_overview.get('digital_maturity', 'N/A')}")
                    st.markdown(f"**Business Model:** {client_overview.get('business_model', 'N/A')}")

                if client_overview.get('context'):
                    st.markdown("---")
                    st.subheader("📝 Context")
                    st.info(client_overview['context'])

                if client_overview.get('recent_news'):
                    st.markdown("---")
                    st.subheader("📰 Recent News")
                    st.info(client_overview['recent_news'])

                st.markdown("---")
                st.subheader("👥 Stakeholders & Influence Map")
                stakeholders = client_overview.get('stakeholders', [])
                if stakeholders:
                    for sh in stakeholders:
                        st.markdown(f"- **{sh.get('name', 'N/A')}** ({sh.get('role', 'N/A')}) - Influence: {sh.get('influence', 'N/A')} - Relationship: {sh.get('relationship_with_granite', 'N/A')}")
                else:
                    st.info("No stakeholders listed")

                st.markdown("---")
                st.subheader("🎯 Business Goals & Priorities")
                goals = client_overview.get('business_goals', [])
                if goals:
                    for goal_group in goals:
                        st.markdown(f"**{goal_group.get('category', 'Goals')}:**")
                        for g in goal_group.get('goals', []):
                            st.markdown(f"- {g}")
                else:
                    st.info("No business goals listed")

                st.markdown("---")
                st.subheader("⚠️ Challenges")
                challenges = client_overview.get('challenges', [])
                if challenges:
                    for challenge_group in challenges:
                        st.markdown(f"**{challenge_group.get('category', 'Challenges')}:**")
                        for c in challenge_group.get('challenges', []):
                            st.markdown(f"- {c}")
                else:
                    st.info("No challenges listed")

                st.markdown("---")
                st.subheader("📊 KPIs & Success Measures")
                kpis = client_overview.get('kpis', [])
                if kpis:
                    for kpi in kpis:
                        st.markdown(f"- **{kpi.get('kpi_name', 'N/A')}**: {kpi.get('target', 'N/A')}")
                else:
                    st.info("No KPIs listed")

                st.markdown("---")
                st.subheader("⚔️ Competitive Landscape")
                comp = client_overview.get('competitive_landscape', {})
                if comp:
                    st.markdown(f"**Industry Leaders:** {', '.join(comp.get('industry_leaders', [])) or 'N/A'}")
                    st.markdown(f"**Vendors in Play:** {', '.join(comp.get('vendors_in_play', [])) or 'N/A'}")
                    if comp.get('client_perception'):
                        st.markdown(f"**Client Perception:** {comp['client_perception']}")
                else:
                    st.info("No competitive landscape data")

                st.markdown("---")
                st.subheader("💰 Budget & Procurement")
                budget = client_overview.get('budget_info', {})
                if budget:
                    st.markdown(f"**Budget Owners:** {', '.join(budget.get('budget_owners', [])) or 'N/A'}")
                    st.markdown(f"**Indicative Budget:** {budget.get('indicative_budget', 'N/A')}")
                    st.markdown(f"**Procurement Process:** {budget.get('procurement_process', 'N/A')}")
                    st.markdown(f"**Budget Approvers:** {', '.join(budget.get('budget_approvers', [])) or 'N/A'}")
                else:
                    st.info("No budget information")

                st.markdown("---")
                st.subheader("🚨 Risks & Blockers")
                risks = client_overview.get('risks_blockers', {})
                if risks:
                    st.markdown("**Potential Blockers:**")
                    if risks.get('potential_blockers'):
                        for blocker in risks.get('potential_blockers', []):
                            st.markdown(f"- {blocker}")
                    else:
                        st.markdown("- N/A")
                    st.markdown("**Risk Factors:**")
                    if risks.get('risk_factors'):
                        for risk in risks.get('risk_factors', []):
                            st.markdown(f"- {risk}")
                    else:
                        st.markdown("- N/A")
                    if risks.get('mitigation_strategy'):
                        st.markdown(f"**Mitigation Strategy:** {risks['mitigation_strategy']}")
                    st.markdown("**Champions (who can influence):**")
                    if risks.get('champions'):
                        for champion in risks.get('champions', []):
                            st.markdown(f"- {champion}")
                    else:
                        st.markdown("- N/A")
                else:
                    st.info("No risks/blockers listed")

                # Show edit metadata
                if edit_history:
                    st.divider()
                    render_edit_metadata(
                        edit_history.get('last_edited_by'),
                        edit_history.get('last_edited_at')
                    )

                # Edit button
                st.divider()
                if st.button("✏️ Edit Client Overview", key="edit_overview_btn"):
                    st.session_state.edit_mode_brief_overview = True
                    st.rerun()
            else:
                # Edit mode
                updated_overview, save_clicked = render_client_overview_edit_form(client_overview)

                if save_clicked:
                    # Prepare updated brief data
                    updated_brief_data = dict(brief_data)
                    updated_brief_data['client_overview'] = updated_overview

                    # Save to database
                    username = st.session_state.user.get('username', 'Unknown')
                    result = ui_ops.update_client_brief_full(
                        brief_id,
                        updated_brief_data,
                        username
                    )

                    if result['success']:
                        st.session_state.edit_mode_brief_overview = False
                        st.success("✅ Client Overview updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save: {result.get('message')}")

        with tab_opportunity:
            granite_opp = brief_data.get('granite_opportunity', {})
            edit_history = db_manager.get_brief_edit_history(brief_id)

            if not st.session_state.edit_mode_brief_opportunity:
                # View mode
                st.subheader("💡 How Granite Can Add Value")
                value_maps = granite_opp.get('value_mappings', [])
                if value_maps:
                    for vm in value_maps:
                        st.markdown(f"**Client Goal:** {vm.get('client_goal', 'N/A')}")
                        st.markdown(f"- **Granite Capability:** {vm.get('granite_capability', 'N/A')}")
                        if vm.get('partners_suggested'):
                            st.markdown(f"- **Suggested Partners:** {', '.join(vm['partners_suggested'])}")
                        if vm.get('high_level_solution'):
                            st.markdown(f"- **Solution:** {vm['high_level_solution']}")
                        st.divider()
                else:
                    st.info("No value mappings listed")

                st.subheader("🚀 Quick Wins & Pilot Ideas")
                quick_wins = granite_opp.get('quick_wins', [])
                if quick_wins:
                    for qw in quick_wins:
                        st.markdown(f"**{qw.get('title', 'Quick Win')}**")
                        st.markdown(f"- {qw.get('description', 'N/A')}")
                        if qw.get('target_stakeholder'):
                            st.markdown(f"- Target: {qw['target_stakeholder']}")
                        if qw.get('short_term_goal_alignment'):
                            st.markdown(f"- Aligns with: {qw['short_term_goal_alignment']}")
                        st.divider()
                else:
                    st.info("No quick wins listed")

                st.subheader("📈 Long-term Opportunities")
                long_term = granite_opp.get('long_term_opportunities', [])
                if long_term:
                    for lt in long_term:
                        st.markdown(f"**{lt.get('title', 'Opportunity')}**")
                        st.markdown(f"- {lt.get('description', 'N/A')}")
                        if lt.get('business_potential'):
                            st.markdown(f"- **Business Potential:** {lt['business_potential']}")
                        st.divider()
                else:
                    st.info("No long-term opportunities listed")

                st.subheader("🌟 Differentiators to Highlight")
                diffs = granite_opp.get('differentiators', [])
                if diffs:
                    for diff in diffs:
                        st.markdown(f"**{diff.get('title', 'Differentiator')}**")
                        st.markdown(f"- {diff.get('description', 'N/A')}")
                        st.divider()
                else:
                    st.info("No differentiators listed")

                st.subheader("📝 Bid Win Strategy Notes")
                strategy = granite_opp.get('bid_win_strategy_notes')
                if strategy:
                    st.info(strategy)
                else:
                    st.info("No strategy notes")

                # Show edit metadata
                if edit_history:
                    st.divider()
                    render_edit_metadata(
                        edit_history.get('last_edited_by'),
                        edit_history.get('last_edited_at')
                    )

                # Edit button
                st.divider()
                if st.button("✏️ Edit Granite Opportunity", key="edit_opportunity_btn"):
                    st.session_state.edit_mode_brief_opportunity = True
                    st.rerun()
            else:
                # Edit mode
                updated_opportunity, save_clicked = render_granite_opportunity_edit_form(granite_opp)

                if save_clicked:
                    # Prepare updated brief data
                    updated_brief_data = dict(brief_data)
                    updated_brief_data['granite_opportunity'] = updated_opportunity

                    # Save to database
                    username = st.session_state.user.get('username', 'Unknown')
                    result = ui_ops.update_client_brief_full(
                        brief_id,
                        updated_brief_data,
                        username
                    )

                    if result['success']:
                        st.session_state.edit_mode_brief_opportunity = False
                        st.success("✅ Granite Opportunity updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save: {result.get('message')}")

        st.divider()
        col1, col2 = st.columns([1, 10])
        with col1:
            if st.button(f"🗑️ Delete", use_container_width=True, key=f"del_{brief_id}"):
                db_manager.delete_client_brief(brief_id)
                st.success(f"Brief {brief_id} deleted")
                st.rerun()
