from typing import Dict, Any, Optional, List
from .db_singleton import get_db

db = get_db()


def tool_query_database(
    query_type: str,
    rfp_id: Optional[str] = None,
    client_name: Optional[str] = None,
    industry: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Unified database query function for all data retrieval.

    Args:
        query_type: Type of query - "rfp" (single), "rfps" (list), or "history"
        rfp_id: RFP ID (required for query_type="rfp")
        client_name: Filter by client name (for history queries)
        industry: Filter by industry (for history queries)
        outcome: Filter by outcome: won, lost, no_bid, pending (for history queries)
        limit: Maximum results to return (default 20)

    Returns:
        Dictionary with query results

    Examples:
        tool_query_database(query_type="rfp", rfp_id="KHDA_2024")
        tool_query_database(query_type="rfps", limit=10)
        tool_query_database(query_type="history", client_name="KHDA", outcome="won")
    """
    try:
        if query_type == "rfp":
            if not rfp_id:
                return {
                    'success': False,
                    'error': 'Missing rfp_id',
                    'message': 'rfp_id is required for query_type="rfp"'
                }

            rfp_doc = db.get_rfp_document(rfp_id)
            if not rfp_doc:
                return {
                    'success': False,
                    'error': 'RFP not found',
                    'message': f'No RFP found with ID: {rfp_id}'
                }

            extracted_data = db.get_rfp_extracted_data(rfp_id)
            qualification = db.get_qualification_results(rfp_id)

            return {
                'success': True,
                'query_type': 'rfp',
                'rfp_document': rfp_doc,
                'extracted_data': extracted_data,
                'qualification': qualification,
                'message': f'Retrieved complete data for RFP: {rfp_id}'
            }

        elif query_type == "rfps":
            rfps = db.list_recent_rfps(limit=limit)

            return {
                'success': True,
                'query_type': 'rfps',
                'rfps': rfps,
                'count': len(rfps),
                'message': f'Found {len(rfps)} recent RFPs'
            }

        elif query_type == "history":
            insights = db.query_bid_history(
                client_name=client_name,
                industry=industry,
                outcome=outcome,
                limit=limit
            )

            return {
                'success': True,
                'query_type': 'history',
                'insights': insights,
                'count': len(insights),
                'message': f'Found {len(insights)} historical insights'
            }

        else:
            return {
                'success': False,
                'error': 'Invalid query_type',
                'message': f'query_type must be "rfp", "rfps", or "history", got: {query_type}'
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Database query failed: {str(e)}'
        }


def tool_get_bid_plan_data(rfp_id: str) -> Dict[str, Any]:
    """
    Get current bid plan data for agent review.
    Returns all deliverables, assignments, and overview data.

    Args:
        rfp_id: The RFP ID

    Returns:
        Dictionary with all bid plan data
    """
    try:
        deliverables = db.get_rfp_deliverables(rfp_id)
        assignments = db.get_rfp_assignments(rfp_id)
        raw_data = db.get_rfp_raw_data(rfp_id)

        if not deliverables:
            return {
                'success': False,
                'error': 'No data found',
                'message': f'No bid plan data found for RFP: {rfp_id}'
            }

        return {
            'success': True,
            'rfp_id': rfp_id,
            'client_and_opportunity': deliverables.get('client_and_opportunity'),
            'technical_deliverables': deliverables.get('technical_deliverables', []),
            'commercial_deliverables': deliverables.get('commercial_deliverables', []),
            'assignments': assignments.get('assignment_report', {}) if assignments else None,
            'overview': raw_data.get('rfp_data', {}) if raw_data else None,
            'message': f'Retrieved bid plan data for {rfp_id}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to get bid plan data: {str(e)}'
        }


def tool_get_qualification_data(rfp_id: str) -> Dict[str, Any]:
    """
    Get current qualification data for agent review.
    Returns complete qualification report.

    Args:
        rfp_id: The RFP ID

    Returns:
        Dictionary with qualification data
    """
    try:
        qualification = db.get_qualification_results(rfp_id)

        if not qualification:
            return {
                'success': False,
                'error': 'No data found',
                'message': f'No qualification data found for RFP: {rfp_id}'
            }

        report = qualification.get('qualification_report', {})

        return {
            'success': True,
            'rfp_id': rfp_id,
            'total_score': report.get('total_score'),
            'threshold': report.get('threshold'),
            'qualifies': report.get('qualifies'),
            'decision': 'PURSUE' if report.get('qualifies') else 'DECLINE',
            'rfp_classification': report.get('rfp_classification'),
            'executive_summary': report.get('executive_summary'),
            'recommendations': report.get('recommendations', []),
            'analyses': report.get('analyses', []),
            'qualification_context': report.get('qualification_context'),
            'message': f'Retrieved qualification data for {rfp_id}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to get qualification data: {str(e)}'
        }


def tool_update_qualification(
    rfp_id: str,
    field_path: str,
    new_value: Any
) -> Dict[str, Any]:
    """
    Update qualification data during planning discussions.

    Args:
        rfp_id: The RFP ID
        field_path: JSON path (e.g., "analyses.2.reasoning" or "threshold")
        new_value: New value to set

    Examples:
        tool_update_qualification("KHDA_2024", "threshold", 2.8)
        tool_update_qualification("KHDA_2024", "analyses.2.reasoning", "Updated reasoning")

    Returns:
        Dictionary with success status
    """
    try:
        db.update_qualification_field(rfp_id, field_path, new_value)

        return {
            'success': True,
            'rfp_id': rfp_id,
            'field_path': field_path,
            'new_value': new_value,
            'message': f'Updated qualification field: {field_path}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to update qualification: {str(e)}'
        }


def tool_update_deliverable(
    rfp_id: str,
    deliverable_type: str,
    deliverable_index: int,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update specific deliverable during bid planning.

    Args:
        rfp_id: The RFP ID
        deliverable_type: "technical" or "commercial"
        deliverable_index: Index of deliverable to update (0-based)
        updates: Dictionary of field updates

    Examples:
        tool_update_deliverable(
            "KHDA_2024",
            "technical",
            3,
            {"section": "Updated Section Name", "requirement": "New requirements"}
        )

    Returns:
        Dictionary with success status
    """
    try:
        db.update_deliverable(rfp_id, deliverable_type, deliverable_index, updates)

        return {
            'success': True,
            'rfp_id': rfp_id,
            'deliverable_type': deliverable_type,
            'deliverable_index': deliverable_index,
            'updates': updates,
            'message': f'Updated {deliverable_type} deliverable at index {deliverable_index}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to update deliverable: {str(e)}'
        }


def tool_update_assignment(
    rfp_id: str,
    section_name: str,
    new_owner: Optional[str] = None,
    new_reasoning: Optional[str] = None,
    alternative_partners: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update assignment decisions during planning discussions.

    Args:
        rfp_id: The RFP ID
        section_name: Name of the deliverable section
        new_owner: New assigned owner
        new_reasoning: Updated reasoning for assignment
        alternative_partners: Updated list of alternative partners

    Examples:
        tool_update_assignment(
            "KHDA_2024",
            "Technical Solution Architecture",
            new_owner="Accenture",
            new_reasoning="Better expertise in government systems"
        )

    Returns:
        Dictionary with success status
    """
    try:
        updates = {}
        if new_owner is not None:
            updates['assigned_owner'] = new_owner
        if new_reasoning is not None:
            updates['reasoning'] = new_reasoning
        if alternative_partners is not None:
            updates['alternative_partners'] = alternative_partners

        db.update_assignment(rfp_id, section_name, updates)

        return {
            'success': True,
            'rfp_id': rfp_id,
            'section_name': section_name,
            'updates': updates,
            'message': f'Updated assignment for section: {section_name}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to update assignment: {str(e)}'
        }


def tool_add_deliverable(
    rfp_id: str,
    deliverable_type: str,
    deliverable_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add new deliverable during planning discussions.

    Args:
        rfp_id: The RFP ID
        deliverable_type: "technical" or "commercial"
        deliverable_data: Complete deliverable data

    Examples:
        tool_add_deliverable(
            "KHDA_2024",
            "technical",
            {
                "section": "Data Migration Plan",
                "requirement": "Detailed plan for migrating legacy data",
                "evaluation_criteria": "Completeness and risk mitigation"
            }
        )

    Returns:
        Dictionary with success status
    """
    try:
        db.add_deliverable(rfp_id, deliverable_type, deliverable_data)

        return {
            'success': True,
            'rfp_id': rfp_id,
            'deliverable_type': deliverable_type,
            'deliverable_data': deliverable_data,
            'message': f'Added new {deliverable_type} deliverable: {deliverable_data.get("section", "Unnamed")}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to add deliverable: {str(e)}'
        }


def tool_remove_deliverable(
    rfp_id: str,
    deliverable_type: str,
    deliverable_index: int
) -> Dict[str, Any]:
    """
    Remove deliverable during planning discussions.

    Args:
        rfp_id: The RFP ID
        deliverable_type: "technical" or "commercial"
        deliverable_index: Index of deliverable to remove (0-based)

    Returns:
        Dictionary with success status
    """
    try:
        db.remove_deliverable(rfp_id, deliverable_type, deliverable_index)

        return {
            'success': True,
            'rfp_id': rfp_id,
            'deliverable_type': deliverable_type,
            'deliverable_index': deliverable_index,
            'message': f'Removed {deliverable_type} deliverable at index {deliverable_index}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to remove deliverable: {str(e)}'
        }


def tool_save_bid_insight(
    rfp_id: str,
    outcome: str,
    insight_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save insights from a completed bid for future reference.

    Args:
        rfp_id: The RFP ID
        outcome: Outcome of the bid (won, lost, no_bid)
        insight_data: Dictionary with lessons learned, win themes, etc.

    Returns:
        Dictionary with success status
    """
    try:
        rfp_doc = db.get_rfp_document(rfp_id)
        if not rfp_doc:
            return {
                'success': False,
                'error': 'RFP not found',
                'message': 'Cannot save insight for non-existent RFP'
            }

        insight_data['client_name'] = rfp_doc['client_name']
        insight_data['outcome'] = outcome

        insight_id = db.save_bid_insight(rfp_id, insight_data)

        return {
            'success': True,
            'insight_id': insight_id,
            'message': 'Bid insight saved successfully'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to save bid insight: {str(e)}'
        }
