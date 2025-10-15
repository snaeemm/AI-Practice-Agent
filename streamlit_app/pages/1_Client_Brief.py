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
    st.subheader("Client Briefs")

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
        st.write(f"Found **{len(briefs)}** client brief(s)")

        for brief in briefs:
            brief_id = brief['id']
            client_name = brief['client_name']
            created_date = brief['created_date'].strftime("%Y-%m-%d %H:%M") if brief['created_date'] else "N/A"
            created_by = brief.get('created_by') or "Agent"

            with st.expander(f"**{client_name}** - ID: {brief_id} | Created: {created_date} by {created_by}"):
                brief_data = brief['brief_data']

                tab_overview, tab_opportunity = st.tabs(["🏢 Client Overview", "💡 Granite Opportunity"])

                with tab_overview:
                    client_overview = brief_data.get('client_overview', {})

                    st.markdown("### Context & Organization")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Organization:** {client_overview.get('organization_overview', 'N/A')}")
                        st.write(f"**Industry:** {client_overview.get('industry', 'N/A')}")
                        st.write(f"**Size:** {client_overview.get('size_of_business', 'N/A')}")
                    with col2:
                        st.write(f"**Region:** {client_overview.get('region_focus', 'N/A')}")
                        st.write(f"**Digital Maturity:** {client_overview.get('digital_maturity', 'N/A')}")
                        st.write(f"**Business Model:** {client_overview.get('business_model', 'N/A')}")

                    if client_overview.get('context'):
                        st.markdown("**Context:**")
                        st.info(client_overview['context'])

                    if client_overview.get('recent_news'):
                        st.markdown("**Recent News:**")
                        st.info(client_overview['recent_news'])

                    st.markdown("### Stakeholders & Influence Map")
                    stakeholders = client_overview.get('stakeholders', [])
                    if stakeholders:
                        for sh in stakeholders:
                            st.markdown(f"- **{sh.get('name', 'N/A')}** ({sh.get('role', 'N/A')}) - Influence: {sh.get('influence', 'N/A')} - Relationship: {sh.get('relationship_with_granite', 'N/A')}")
                    else:
                        st.write("No stakeholders listed")

                    st.markdown("### Business Goals & Priorities")
                    goals = client_overview.get('business_goals', [])
                    if goals:
                        for goal_group in goals:
                            st.markdown(f"**{goal_group.get('category', 'Goals')}:**")
                            for g in goal_group.get('goals', []):
                                st.markdown(f"- {g}")
                    else:
                        st.write("No business goals listed")

                    st.markdown("### Challenges")
                    challenges = client_overview.get('challenges', [])
                    if challenges:
                        for challenge_group in challenges:
                            st.markdown(f"**{challenge_group.get('category', 'Challenges')}:**")
                            for c in challenge_group.get('challenges', []):
                                st.markdown(f"- {c}")
                    else:
                        st.write("No challenges listed")

                    st.markdown("### KPIs & Success Measures")
                    kpis = client_overview.get('kpis', [])
                    if kpis:
                        for kpi in kpis:
                            st.markdown(f"- **{kpi.get('kpi_name', 'N/A')}**: {kpi.get('target', 'N/A')}")
                    else:
                        st.write("No KPIs listed")

                    st.markdown("### Competitive Landscape")
                    comp = client_overview.get('competitive_landscape', {})
                    if comp:
                        st.write(f"**Industry Leaders:** {', '.join(comp.get('industry_leaders', []))}")
                        st.write(f"**Vendors in Play:** {', '.join(comp.get('vendors_in_play', []))}")
                        if comp.get('client_perception'):
                            st.write(f"**Client Perception:** {comp['client_perception']}")
                    else:
                        st.write("No competitive landscape data")

                    st.markdown("### Budget & Procurement")
                    budget = client_overview.get('budget_info', {})
                    if budget:
                        st.write(f"**Budget Owners:** {', '.join(budget.get('budget_owners', []))}")
                        st.write(f"**Indicative Budget:** {budget.get('indicative_budget', 'N/A')}")
                        st.write(f"**Procurement Process:** {budget.get('procurement_process', 'N/A')}")
                        st.write(f"**Budget Approvers:** {', '.join(budget.get('budget_approvers', []))}")
                    else:
                        st.write("No budget information")

                    st.markdown("### Risks & Blockers")
                    risks = client_overview.get('risks_blockers', {})
                    if risks:
                        st.write("**Potential Blockers:**")
                        for blocker in risks.get('potential_blockers', []):
                            st.markdown(f"- {blocker}")
                        st.write("**Risk Factors:**")
                        for risk in risks.get('risk_factors', []):
                            st.markdown(f"- {risk}")
                        if risks.get('mitigation_strategy'):
                            st.write(f"**Mitigation Strategy:** {risks['mitigation_strategy']}")
                        st.write("**Champions (who can influence):**")
                        for champion in risks.get('champions', []):
                            st.markdown(f"- {champion}")
                    else:
                        st.write("No risks/blockers listed")

                with tab_opportunity:
                    granite_opp = brief_data.get('granite_opportunity', {})

                    st.markdown("### How Granite Can Add Value")
                    value_maps = granite_opp.get('value_mappings', [])
                    if value_maps:
                        for vm in value_maps:
                            st.markdown(f"**Client Goal:** {vm.get('client_goal', 'N/A')}")
                            st.markdown(f"- **Granite Capability:** {vm.get('granite_capability', 'N/A')}")
                            if vm.get('partners_suggested'):
                                st.markdown(f"- **Suggested Partners:** {', '.join(vm['partners_suggested'])}")
                            if vm.get('high_level_solution'):
                                st.markdown(f"- **Solution:** {vm['high_level_solution']}")
                            st.markdown("---")
                    else:
                        st.write("No value mappings listed")

                    st.markdown("### Quick Wins & Pilot Ideas")
                    quick_wins = granite_opp.get('quick_wins', [])
                    if quick_wins:
                        for qw in quick_wins:
                            st.markdown(f"**{qw.get('title', 'Quick Win')}**")
                            st.markdown(f"- {qw.get('description', 'N/A')}")
                            if qw.get('target_stakeholder'):
                                st.markdown(f"- Target: {qw['target_stakeholder']}")
                            if qw.get('short_term_goal_alignment'):
                                st.markdown(f"- Aligns with: {qw['short_term_goal_alignment']}")
                            st.markdown("---")
                    else:
                        st.write("No quick wins listed")

                    st.markdown("### Long-term Opportunities")
                    long_term = granite_opp.get('long_term_opportunities', [])
                    if long_term:
                        for lt in long_term:
                            st.markdown(f"**{lt.get('title', 'Opportunity')}**")
                            st.markdown(f"- {lt.get('description', 'N/A')}")
                            if lt.get('business_potential'):
                                st.markdown(f"- **Business Potential:** {lt['business_potential']}")
                            st.markdown("---")
                    else:
                        st.write("No long-term opportunities listed")

                    st.markdown("### Differentiators to Highlight")
                    diffs = granite_opp.get('differentiators', [])
                    if diffs:
                        for diff in diffs:
                            st.markdown(f"**{diff.get('title', 'Differentiator')}**")
                            st.markdown(f"- {diff.get('description', 'N/A')}")
                    else:
                        st.write("No differentiators listed")

                    st.markdown("### Bid Win Strategy Notes")
                    strategy = granite_opp.get('bid_win_strategy_notes')
                    if strategy:
                        st.info(strategy)
                    else:
                        st.write("No strategy notes")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"🗑️ Delete Brief {brief_id}", key=f"del_{brief_id}"):
                        db_manager.delete_client_brief(brief_id)
                        st.success(f"Brief {brief_id} deleted")
                        st.rerun()

with tab2:
    st.subheader("Generate New Client Brief")
    st.info("💡 **Tip**: You can also ask the agent directly to generate a client brief by pasting your meeting notes in the chat.")

    st.markdown("The agent can:")
    st.markdown("- Extract client information, stakeholders, and business goals")
    st.markdown("- Map client needs to Granite capabilities and partners")
    st.markdown("- Suggest quick wins and long-term opportunities")
    st.markdown("- Generate bid win strategies")

    st.markdown("---")
    st.markdown("**Go to the Agent page and paste your meeting notes**, or upload a document (.txt, .docx, .pdf) and say:")
    st.code('Generate a client brief from these meeting notes')

    st.markdown("The agent will process your notes and save the brief to the database automatically.")
