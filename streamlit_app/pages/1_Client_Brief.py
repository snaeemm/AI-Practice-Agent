import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.database.db_manager import DatabaseManager
from auth import require_auth
from styles import apply_custom_styles
import json

st.set_page_config(page_title="Client Brief Generator", page_icon="📋", layout="wide")

apply_custom_styles()

if not require_auth():
    st.stop()

st.title("📋 Client Brief Generator")

db_manager = DatabaseManager()

tab1, tab2 = st.tabs(["📝 View Briefs", "➕ Generate New Brief"])

with tab1:
    with tab1:
        st.subheader("📝 View Client Briefs")
    
        col1, col2 = st.columns([3, 1])
        with col1:
            search_client = st.text_input("🔍 Filter by client name", placeholder="Enter client name...")
        with col2:
            limit = st.number_input("Limit", min_value=10, max_value=100, value=50, step=10)
    
        if search_client:
            briefs = db_manager.list_client_briefs(client_name=search_client, limit=limit)
        else:
            briefs = db_manager.list_client_briefs(limit=limit)
    
        if not briefs:
            st.info("No client briefs found. Generate one using the 'Generate New Brief' tab or ask the agent to create one.")
        else:
            brief_options = {f"{b['client_name']} (ID: {b['id']}) - {b['created_date'].strftime("%Y-%m-%d %H:%M")}": b for b in briefs}
            selected_brief_option = st.selectbox(
                "Select a Client Brief to view",
                options=list(brief_options.keys()),
                format_func=lambda x: x.split(' (')[0] # Display only client name in dropdown
            )
    
            if selected_brief_option:
                selected_brief = brief_options[selected_brief_option]
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
    
                with tab_opportunity:
                    granite_opp = brief_data.get('granite_opportunity', {})
    
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
    
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"🗑️ Delete Brief {brief_id}", key=f"del_{brief_id}"):
                        db_manager.delete_client_brief(brief_id)
                        st.success(f"Brief {brief_id} deleted")
                        st.rerun()
with tab2:
    st.subheader("➕ Generate New Client Brief")
    st.info("💡 **Tip**: You can also ask the agent directly to generate a client brief by pasting your meeting notes in the chat.")

    st.markdown("### How to Generate a Client Brief:")
    st.markdown("1.  **Go to the Agent page** (sidebar navigation).")
    st.markdown("2.  **Paste your meeting notes** directly into the chat input field.")
    st.markdown("3.  Alternatively, **upload a document** (.txt, .docx, .pdf) containing your meeting notes.")
    st.markdown("4.  **Instruct the agent** to generate a client brief. For example, type:")
    st.code('Generate a client brief from these meeting notes')

    st.markdown("The agent will process your notes, extract key information, and automatically save the structured brief to the database. You can then view it in the 'View Briefs' tab.")

    st.markdown("### What the Agent Can Do:")
    st.markdown("- Extract client information, stakeholders, and business goals")
    st.markdown("- Map client needs to Granite capabilities and partners")
    st.markdown("- Suggest quick wins and long-term opportunities")
    st.markdown("- Generate bid win strategies")
