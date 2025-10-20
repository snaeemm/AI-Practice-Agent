"""
Edit Components Module

Provides reusable UI components for editing RFP data, deliverables, assignments, and client briefs.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime


def render_edit_metadata(edited_by: Optional[str], edited_at: Optional[datetime]):
    """Show who last edited and when"""
    if edited_by and edited_at:
        if isinstance(edited_at, str):
            edited_at_str = edited_at
        else:
            edited_at_str = edited_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        st.caption(f"✏️ Last edited by **{edited_by}** on {edited_at_str}")


def render_edit_button() -> bool:
    """Render edit mode toggle button - returns whether in edit mode"""
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("✏️ Edit", use_container_width=True, key=f"edit_btn_{id(None)}"):
            return True
    return False


def render_qualification_edit_form(
    analyses: List[Dict[str, Any]],
    threshold: float,
    max_score: int = 4
) -> tuple[List[Dict[str, Any]], float, bool]:
    """
    Render editable qualification form
    Returns: (updated_analyses, updated_threshold, save_clicked)
    """

    with st.form("qualification_edit_form"):
        st.markdown("### ✏️ Edit Qualification")

        # Edit threshold
        col1, col2 = st.columns(2)
        with col1:
            new_threshold = st.number_input(
                "Qualification Threshold",
                value=threshold,
                min_value=0.0,
                max_value=float(max_score),
                step=0.1
            )

        updated_analyses = []

        for i, analysis in enumerate(analyses):
            st.markdown(f"#### {i + 1}. {analysis.get('criterion', 'Criterion')}")

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                new_score = st.selectbox(
                    "Score",
                    [1, 2, 3, 4],
                    index=int(analysis.get('score', 1)) - 1,
                    key=f"score_{i}"
                )

            with col2:
                new_weight = st.number_input(
                    "Weight",
                    value=float(analysis.get('weight', 1)),
                    min_value=0.1,
                    max_value=10.0,
                    step=0.1,
                    key=f"weight_{i}"
                )

            with col3:
                # Calculate and display weighted score
                weighted_score = (new_score / max_score) * new_weight
                st.metric("Weighted Score", f"{weighted_score:.2f}")

            new_reasoning = st.text_area(
                "Reasoning",
                value=analysis.get('reasoning', ''),
                height=80,
                key=f"reasoning_{i}"
            )

            # Update analysis with new values
            updated = dict(analysis)
            updated['score'] = new_score
            updated['weight'] = new_weight
            updated['weighted_score'] = weighted_score
            updated['reasoning'] = new_reasoning
            updated_analyses.append(updated)

            st.divider()

        # Display live total score calculation
        total_weighted = sum(a.get('weighted_score', 0) for a in updated_analyses)
        qualifies = total_weighted >= new_threshold

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Score", f"{total_weighted:.2f}")
        with col2:
            status = "✅ QUALIFIES" if qualifies else "❌ DOES NOT QUALIFY"
            st.markdown(f"**Status:** {status}")
        with col3:
            st.metric("Threshold", f"{new_threshold:.2f}")

        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancel_clicked:
            st.session_state.edit_mode_qual = False
            st.rerun()

        return updated_analyses, new_threshold, save_clicked


def render_deliverables_edit_form(
    technical_deliverables: List[Dict[str, Any]],
    commercial_deliverables: List[Dict[str, Any]],
    owners_list: List[str]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], bool]:
    """
    Render editable deliverables form
    Returns: (updated_technical, updated_commercial, save_clicked)
    """

    with st.form("deliverables_edit_form"):
        st.markdown("### ✏️ Edit Deliverables")

        updated_technical = list(technical_deliverables)
        updated_commercial = list(commercial_deliverables)

        # Track items to delete using session state
        if 'delete_indices_tech' not in st.session_state:
            st.session_state.delete_indices_tech = set()
        if 'delete_indices_comm' not in st.session_state:
            st.session_state.delete_indices_comm = set()

        # Edit technical deliverables
        st.markdown("#### Technical Deliverables")

        for i, deliv in enumerate(updated_technical):
            col1, col2, col3 = st.columns([0.05, 0.75, 0.2])

            with col1:
                # Checkbox to mark for deletion
                delete_marked = st.checkbox(
                    "Del",
                    value=i in st.session_state.delete_indices_tech,
                    key=f"tech_del_check_{i}",
                    label_visibility="collapsed"
                )
                if delete_marked:
                    st.session_state.delete_indices_tech.add(i)
                else:
                    st.session_state.delete_indices_tech.discard(i)

            with col2:
                st.markdown(f"**{i + 1}. {deliv.get('section', 'Section')}**")

                col_a, col_b = st.columns(2)
                with col_a:
                    updated_technical[i]['section'] = st.text_input(
                        "Section",
                        value=deliv.get('section', ''),
                        key=f"tech_section_{i}"
                    )
                    updated_technical[i]['format'] = st.text_input(
                        "Format",
                        value=deliv.get('format', ''),
                        key=f"tech_format_{i}"
                    )

                with col_b:
                    updated_technical[i]['owner'] = st.selectbox(
                        "Owner",
                        owners_list,
                        index=owners_list.index(deliv.get('owner', 'Unassigned')) if deliv.get('owner', 'Unassigned') in owners_list else 0,
                        key=f"tech_owner_{i}"
                    )
                    updated_technical[i]['page_limit'] = st.text_input(
                        "Page Limit",
                        value=str(deliv.get('page_limit', '')),
                        key=f"tech_page_{i}"
                    )

                updated_technical[i]['requirement'] = st.text_area(
                    "Requirement",
                    value=deliv.get('requirement', ''),
                    height=80,
                    key=f"tech_req_{i}"
                )

            st.divider()

        # Edit commercial deliverables
        st.markdown("#### Commercial Deliverables")

        for i, deliv in enumerate(updated_commercial):
            col1, col2, col3 = st.columns([0.05, 0.75, 0.2])

            with col1:
                # Checkbox to mark for deletion
                delete_marked = st.checkbox(
                    "Del",
                    value=i in st.session_state.delete_indices_comm,
                    key=f"comm_del_check_{i}",
                    label_visibility="collapsed"
                )
                if delete_marked:
                    st.session_state.delete_indices_comm.add(i)
                else:
                    st.session_state.delete_indices_comm.discard(i)

            with col2:
                st.markdown(f"**{i + 1}. {deliv.get('section', 'Section')}**")

                col_a, col_b = st.columns(2)
                with col_a:
                    updated_commercial[i]['section'] = st.text_input(
                        "Section",
                        value=deliv.get('section', ''),
                        key=f"comm_section_{i}"
                    )
                    updated_commercial[i]['format'] = st.text_input(
                        "Format",
                        value=deliv.get('format', ''),
                        key=f"comm_format_{i}"
                    )

                with col_b:
                    updated_commercial[i]['owner'] = st.selectbox(
                        "Owner",
                        owners_list,
                        index=owners_list.index(deliv.get('owner', 'Unassigned')) if deliv.get('owner', 'Unassigned') in owners_list else 0,
                        key=f"comm_owner_{i}"
                    )
                    updated_commercial[i]['page_limit'] = st.text_input(
                        "Page Limit",
                        value=str(deliv.get('page_limit', '')),
                        key=f"comm_page_{i}"
                    )

                updated_commercial[i]['requirement'] = st.text_area(
                    "Requirement",
                    value=deliv.get('requirement', ''),
                    height=80,
                    key=f"comm_req_{i}"
                )

            st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancel_clicked:
            st.session_state.edit_mode_deliv = False
            st.session_state.delete_indices_tech = set()
            st.session_state.delete_indices_comm = set()
            st.rerun()

        # Filter out marked items for deletion
        if save_clicked:
            updated_technical = [d for i, d in enumerate(updated_technical) if i not in st.session_state.delete_indices_tech]
            updated_commercial = [d for i, d in enumerate(updated_commercial) if i not in st.session_state.delete_indices_comm]
            st.session_state.delete_indices_tech = set()
            st.session_state.delete_indices_comm = set()

        return updated_technical, updated_commercial, save_clicked


def render_assignments_edit_form(
    assignments: List[Dict[str, Any]],
    owners_list: List[str]
) -> tuple[List[Dict[str, Any]], bool]:
    """
    Render editable assignments form
    Returns: (updated_assignments, save_clicked)
    """

    with st.form("assignments_edit_form"):
        st.markdown("### ✏️ Edit Assignments")

        updated_assignments = list(assignments)

        for i, assignment in enumerate(updated_assignments):
            st.markdown(f"#### {i + 1}. {assignment.get('deliverable_section', 'Section')}")

            col1, col2 = st.columns([2, 1])

            with col1:
                updated_assignments[i]['assigned_owner'] = st.selectbox(
                    "Assigned Owner",
                    owners_list,
                    index=owners_list.index(assignment.get('assigned_owner', 'Unassigned')) if assignment.get('assigned_owner', 'Unassigned') in owners_list else 0,
                    key=f"assign_owner_{i}"
                )

                updated_assignments[i]['reasoning'] = st.text_area(
                    "Reasoning",
                    value=assignment.get('reasoning', ''),
                    height=80,
                    key=f"assign_reason_{i}"
                )

            st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel_clicked = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancel_clicked:
            st.session_state.edit_mode_assign = False
            st.rerun()

        return updated_assignments, save_clicked
