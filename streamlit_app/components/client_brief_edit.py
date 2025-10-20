"""
Client Brief Edit Components

Provides editable forms for client brief sections.
"""

import streamlit as st
from typing import Dict, Any, Optional, List


def render_client_overview_edit_form(
    overview_data: Dict[str, Any]
) -> tuple[Dict[str, Any], bool]:
    """
    Render editable client overview form
    Returns: (updated_overview, save_clicked)
    """

    with st.form("overview_edit_form"):
        st.markdown("### ✏️ Edit Client Overview")

        overview = dict(overview_data)

        # Organization section
        st.markdown("#### 🏢 Organization")
        col1, col2 = st.columns(2)
        with col1:
            overview['organization_overview'] = st.text_input(
                "Organization", overview.get('organization_overview', '')
            )
            overview['industry'] = st.text_input(
                "Industry", overview.get('industry', '')
            )
        with col2:
            overview['size_of_business'] = st.text_input(
                "Size of Business", overview.get('size_of_business', '')
            )
            overview['region_focus'] = st.text_input(
                "Region Focus", overview.get('region_focus', '')
            )

        overview['digital_maturity'] = st.text_input(
            "Digital Maturity", overview.get('digital_maturity', '')
        )
        overview['business_model'] = st.text_input(
            "Business Model", overview.get('business_model', '')
        )

        overview['context'] = st.text_area(
            "Context", overview.get('context', ''), height=100
        )
        overview['recent_news'] = st.text_area(
            "Recent News", overview.get('recent_news', ''), height=100
        )

        # Stakeholders
        st.markdown("#### 👥 Stakeholders")
        stakeholders = overview.get('stakeholders', [])
        num_stakeholders = st.number_input(
            "Number of Stakeholders", value=len(stakeholders), min_value=0, max_value=20
        )

        new_stakeholders = []
        for i in range(num_stakeholders):
            if i < len(stakeholders):
                sh = stakeholders[i]
            else:
                sh = {}

            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input(
                    f"Stakeholder {i + 1} Name", sh.get('name', ''), key=f"sh_name_{i}"
                )
            with col2:
                role = st.text_input(
                    f"Stakeholder {i + 1} Role", sh.get('role', ''), key=f"sh_role_{i}"
                )
            with col3:
                influence = st.selectbox(
                    f"Stakeholder {i + 1} Influence",
                    ["High", "Medium", "Low"],
                    index=["High", "Medium", "Low"].index(sh.get('influence', 'Medium')),
                    key=f"sh_influence_{i}"
                )
            relationship = st.text_input(
                f"Stakeholder {i + 1} Relationship",
                sh.get('relationship_with_granite', ''),
                key=f"sh_rel_{i}"
            )

            new_stakeholders.append({
                'name': name,
                'role': role,
                'influence': influence,
                'relationship_with_granite': relationship
            })

        overview['stakeholders'] = new_stakeholders

        # Business Goals
        st.markdown("#### 🎯 Business Goals")
        goals = overview.get('business_goals', [])
        new_goals = []
        num_goal_groups = st.number_input(
            "Number of Goal Categories", value=len(goals), min_value=0, max_value=10, key="num_goals"
        )

        for i in range(num_goal_groups):
            if i < len(goals):
                goal_group = goals[i]
            else:
                goal_group = {'category': '', 'goals': []}

            with st.expander(f"Goal Category {i + 1}: {goal_group.get('category', 'N/A')}"):
                category = st.text_input(
                    "Category", goal_group.get('category', ''), key=f"goal_cat_{i}"
                )
                goals_list = goal_group.get('goals', [])
                goals_text = st.text_area(
                    "Goals (one per line)",
                    '\n'.join(goals_list),
                    height=100,
                    key=f"goal_text_{i}"
                )
                goals_list = [g.strip() for g in goals_text.split('\n') if g.strip()]

                new_goals.append({'category': category, 'goals': goals_list})

        overview['business_goals'] = new_goals

        # Challenges
        st.markdown("#### ⚠️ Challenges")
        challenges = overview.get('challenges', [])
        new_challenges = []
        num_challenge_groups = st.number_input(
            "Number of Challenge Categories",
            value=len(challenges),
            min_value=0,
            max_value=10,
            key="num_challenges"
        )

        for i in range(num_challenge_groups):
            if i < len(challenges):
                challenge_group = challenges[i]
            else:
                challenge_group = {'category': '', 'challenges': []}

            with st.expander(f"Challenge Category {i + 1}: {challenge_group.get('category', 'N/A')}"):
                category = st.text_input(
                    "Category", challenge_group.get('category', ''), key=f"challenge_cat_{i}"
                )
                challenges_list = challenge_group.get('challenges', [])
                challenges_text = st.text_area(
                    "Challenges (one per line)",
                    '\n'.join(challenges_list),
                    height=100,
                    key=f"challenge_text_{i}"
                )
                challenges_list = [c.strip() for c in challenges_text.split('\n') if c.strip()]

                new_challenges.append({'category': category, 'challenges': challenges_list})

        overview['challenges'] = new_challenges

        # KPIs
        st.markdown("#### 📊 KPIs & Success Measures")
        kpis = overview.get('kpis', [])
        num_kpis = st.number_input(
            "Number of KPIs", value=len(kpis), min_value=0, max_value=20, key="num_kpis"
        )

        new_kpis = []
        for i in range(num_kpis):
            if i < len(kpis):
                kpi = kpis[i]
            else:
                kpi = {}

            col1, col2 = st.columns(2)
            with col1:
                kpi_name = st.text_input(
                    f"KPI {i + 1} Name", kpi.get('kpi_name', ''), key=f"kpi_name_{i}"
                )
            with col2:
                target = st.text_input(
                    f"KPI {i + 1} Target", kpi.get('target', ''), key=f"kpi_target_{i}"
                )

            new_kpis.append({'kpi_name': kpi_name, 'target': target})

        overview['kpis'] = new_kpis

        # Budget Info
        st.markdown("#### 💰 Budget & Procurement")
        budget = overview.get('budget_info', {})
        new_budget = {}

        col1, col2 = st.columns(2)
        with col1:
            owners_text = st.text_area(
                "Budget Owners (comma-separated)",
                ', '.join(budget.get('budget_owners', [])),
                height=50,
                key="budget_owners"
            )
            new_budget['budget_owners'] = [o.strip() for o in owners_text.split(',') if o.strip()]

            new_budget['indicative_budget'] = st.text_input(
                "Indicative Budget", budget.get('indicative_budget', '')
            )

        with col2:
            new_budget['procurement_process'] = st.text_input(
                "Procurement Process", budget.get('procurement_process', '')
            )
            approvers_text = st.text_area(
                "Budget Approvers (comma-separated)",
                ', '.join(budget.get('budget_approvers', [])),
                height=50,
                key="budget_approvers"
            )
            new_budget['budget_approvers'] = [a.strip() for a in approvers_text.split(',') if a.strip()]

        overview['budget_info'] = new_budget

        # Risks & Blockers
        st.markdown("#### 🚨 Risks & Blockers")
        risks = overview.get('risks_blockers', {})
        new_risks = {}

        col1, col2 = st.columns(2)
        with col1:
            blockers_text = st.text_area(
                "Potential Blockers (one per line)",
                '\n'.join(risks.get('potential_blockers', [])),
                height=80,
                key="blockers"
            )
            new_risks['potential_blockers'] = [b.strip() for b in blockers_text.split('\n') if b.strip()]

            risk_text = st.text_area(
                "Risk Factors (one per line)",
                '\n'.join(risks.get('risk_factors', [])),
                height=80,
                key="risk_factors"
            )
            new_risks['risk_factors'] = [r.strip() for r in risk_text.split('\n') if r.strip()]

        with col2:
            new_risks['mitigation_strategy'] = st.text_area(
                "Mitigation Strategy", risks.get('mitigation_strategy', ''), height=80
            )
            champions_text = st.text_area(
                "Champions (one per line)",
                '\n'.join(risks.get('champions', [])),
                height=80,
                key="champions"
            )
            new_risks['champions'] = [c.strip() for c in champions_text.split('\n') if c.strip()]

        overview['risks_blockers'] = new_risks

        # Save buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancel_clicked:
            st.session_state.edit_mode_brief_overview = False
            st.rerun()

        return overview, save_clicked


def render_granite_opportunity_edit_form(
    opportunity_data: Dict[str, Any]
) -> tuple[Dict[str, Any], bool]:
    """
    Render editable granite opportunity form
    Returns: (updated_opportunity, save_clicked)
    """

    with st.form("opportunity_edit_form"):
        st.markdown("### ✏️ Edit Granite Opportunity")

        opportunity = dict(opportunity_data)

        # Value Mappings
        st.markdown("#### 💡 Value Mappings")
        value_maps = opportunity.get('value_mappings', [])
        num_mappings = st.number_input(
            "Number of Value Mappings", value=len(value_maps), min_value=0, max_value=20, key="num_mappings"
        )

        new_mappings = []
        for i in range(num_mappings):
            if i < len(value_maps):
                vm = value_maps[i]
            else:
                vm = {}

            with st.expander(f"Value Mapping {i + 1}"):
                goal = st.text_input(
                    "Client Goal", vm.get('client_goal', ''), key=f"vm_goal_{i}"
                )
                capability = st.text_input(
                    "Granite Capability", vm.get('granite_capability', ''), key=f"vm_cap_{i}"
                )
                partners_text = st.text_input(
                    "Suggested Partners (comma-separated)",
                    ', '.join(vm.get('partners_suggested', [])),
                    key=f"vm_partners_{i}"
                )
                solution = st.text_area(
                    "Solution", vm.get('high_level_solution', ''), height=80, key=f"vm_solution_{i}"
                )

                new_mappings.append({
                    'client_goal': goal,
                    'granite_capability': capability,
                    'partners_suggested': [p.strip() for p in partners_text.split(',') if p.strip()],
                    'high_level_solution': solution
                })

        opportunity['value_mappings'] = new_mappings

        # Quick Wins
        st.markdown("#### 🚀 Quick Wins & Pilot Ideas")
        quick_wins = opportunity.get('quick_wins', [])
        num_qw = st.number_input(
            "Number of Quick Wins", value=len(quick_wins), min_value=0, max_value=20, key="num_qw"
        )

        new_qw = []
        for i in range(num_qw):
            if i < len(quick_wins):
                qw = quick_wins[i]
            else:
                qw = {}

            with st.expander(f"Quick Win {i + 1}: {qw.get('title', 'N/A')}"):
                title = st.text_input("Title", qw.get('title', ''), key=f"qw_title_{i}")
                desc = st.text_area("Description", qw.get('description', ''), height=80, key=f"qw_desc_{i}")
                target = st.text_input(
                    "Target Stakeholder", qw.get('target_stakeholder', ''), key=f"qw_target_{i}"
                )
                alignment = st.text_input(
                    "Alignment", qw.get('short_term_goal_alignment', ''), key=f"qw_align_{i}"
                )

                new_qw.append({
                    'title': title,
                    'description': desc,
                    'target_stakeholder': target,
                    'short_term_goal_alignment': alignment
                })

        opportunity['quick_wins'] = new_qw

        # Long-term Opportunities
        st.markdown("#### 📈 Long-term Opportunities")
        long_term = opportunity.get('long_term_opportunities', [])
        num_lt = st.number_input(
            "Number of Long-term Opportunities", value=len(long_term), min_value=0, max_value=20, key="num_lt"
        )

        new_lt = []
        for i in range(num_lt):
            if i < len(long_term):
                lt = long_term[i]
            else:
                lt = {}

            with st.expander(f"Opportunity {i + 1}: {lt.get('title', 'N/A')}"):
                title = st.text_input("Title", lt.get('title', ''), key=f"lt_title_{i}")
                desc = st.text_area("Description", lt.get('description', ''), height=80, key=f"lt_desc_{i}")
                potential = st.text_input(
                    "Business Potential", lt.get('business_potential', ''), key=f"lt_potential_{i}"
                )

                new_lt.append({
                    'title': title,
                    'description': desc,
                    'business_potential': potential
                })

        opportunity['long_term_opportunities'] = new_lt

        # Differentiators
        st.markdown("#### 🌟 Differentiators to Highlight")
        diffs = opportunity.get('differentiators', [])
        num_diffs = st.number_input(
            "Number of Differentiators", value=len(diffs), min_value=0, max_value=20, key="num_diffs"
        )

        new_diffs = []
        for i in range(num_diffs):
            if i < len(diffs):
                diff = diffs[i]
            else:
                diff = {}

            with st.expander(f"Differentiator {i + 1}: {diff.get('title', 'N/A')}"):
                title = st.text_input("Title", diff.get('title', ''), key=f"diff_title_{i}")
                desc = st.text_area("Description", diff.get('description', ''), height=80, key=f"diff_desc_{i}")

                new_diffs.append({'title': title, 'description': desc})

        opportunity['differentiators'] = new_diffs

        # Bid Win Strategy Notes
        st.markdown("#### 📝 Bid Win Strategy Notes")
        opportunity['bid_win_strategy_notes'] = st.text_area(
            "Strategy Notes", opportunity.get('bid_win_strategy_notes', ''), height=120
        )

        # Save buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancel_clicked:
            st.session_state.edit_mode_brief_opportunity = False
            st.rerun()

        return opportunity, save_clicked
