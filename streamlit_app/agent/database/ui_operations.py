"""
UI Operations Module

Handles all database updates initiated from the Streamlit UI (not agent operations).
This module is separate from database_tools.py which contains agent-specific tools.

All operations include audit trail tracking (who edited, when, and previous version).
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .db_manager import DatabaseManager


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects and other non-serializable types"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        try:
            return super().default(obj)
        except TypeError:
            # Return string representation for non-serializable objects
            return str(obj)


class UIOperations:
    """Database operations for UI-initiated edits with audit trail tracking"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # ==================== Helper Methods ====================

    def _capture_edit_history(
        self,
        current_version: Dict[str, Any],
        edited_by: str,
        changes_summary: str
    ) -> List[Dict[str, Any]]:
        """Create edit history entry"""
        # Create a copy without the _edit_history to avoid circular references
        version_copy = dict(current_version)
        version_copy.pop("_edit_history", None)

        edit_entry = {
            "edited_by": edited_by,
            "edited_at": datetime.now(timezone.utc).isoformat(),
            "changes_summary": changes_summary,
            "previous_version": version_copy
        }

        # Get existing history or start new one
        existing_history = current_version.get("_edit_history", [])
        if not isinstance(existing_history, list):
            existing_history = []

        # Keep only last 10 edits to avoid bloat
        existing_history.append(edit_entry)
        return existing_history[-10:]

    # ==================== Qualification Editing ====================

    def update_qualification_full(
        self,
        rfp_id: str,
        updated_report: Dict[str, Any],
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Update complete qualification report with edit tracking

        Args:
            rfp_id: RFP ID
            updated_report: Complete updated qualification report
            edited_by: Username performing the edit

        Returns:
            Dict with success status and message
        """
        try:
            # Get current version for audit trail
            current = self.db.get_qualification_results(rfp_id)
            if not current:
                return {
                    "success": False,
                    "error": "RFP not found",
                    "message": f"No qualification found for RFP: {rfp_id}"
                }

            current_report = current.get("qualification_report", {})

            # Create edit history entry
            edit_history = self._capture_edit_history(
                current_report,
                edited_by,
                "Updated qualification report"
            )

            # Add edit metadata to new report
            updated_report["_edit_history"] = edit_history

            # Update database with edit tracking
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE qualification_results
                        SET qualification_report = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE rfp_id = %s
                    """, (
                        json.dumps(updated_report, cls=SafeJSONEncoder),
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        rfp_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "rfp_id": rfp_id,
                "edited_by": edited_by,
                "message": "Qualification report updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update qualification: {str(e)}"
            }

    def update_qualification_criterion(
        self,
        rfp_id: str,
        criterion_name: str,
        new_score: float,
        new_reasoning: str,
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Update a single qualification criterion

        Args:
            rfp_id: RFP ID
            criterion_name: Name of criterion to update
            new_score: New score (1-4)
            new_reasoning: New reasoning text
            edited_by: Username performing the edit

        Returns:
            Dict with success status
        """
        try:
            current = self.db.get_qualification_results(rfp_id)
            if not current:
                return {
                    "success": False,
                    "error": "RFP not found",
                    "message": f"No qualification found for RFP: {rfp_id}"
                }

            current_report = current.get("qualification_report", {})
            analyses = current_report.get("analyses", [])

            # Find and update the criterion
            found = False
            for analysis in analyses:
                if analysis.get("criterion") == criterion_name:
                    analysis["score"] = new_score
                    analysis["reasoning"] = new_reasoning
                    found = True
                    break

            if not found:
                return {
                    "success": False,
                    "error": "Criterion not found",
                    "message": f"Criterion '{criterion_name}' not found in analyses"
                }

            # Recalculate weighted scores if weights are available
            max_score = current_report.get("max_score", 4)
            for analysis in analyses:
                weight = analysis.get("weight", 1)
                score = analysis.get("score", 0)
                analysis["weighted_score"] = (score / max_score) * weight

            # Recalculate total score
            total_score = sum(a.get("weighted_score", 0) for a in analyses)
            current_report["total_score"] = total_score
            current_report["qualifies"] = total_score >= current_report.get(
                "threshold", 2.5
            )

            # Create edit history
            edit_history = self._capture_edit_history(
                current_report,
                edited_by,
                f"Updated criterion: {criterion_name}"
            )
            current_report["_edit_history"] = edit_history

            # Update database
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE qualification_results
                        SET qualification_report = %s,
                            total_score = %s,
                            qualifies = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE rfp_id = %s
                    """, (
                        json.dumps(current_report, cls=SafeJSONEncoder),
                        current_report["total_score"],
                        current_report["qualifies"],
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        rfp_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "rfp_id": rfp_id,
                "criterion": criterion_name,
                "new_score": new_score,
                "new_total_score": total_score,
                "edited_by": edited_by,
                "message": f"Updated criterion '{criterion_name}'"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update criterion: {str(e)}"
            }

    # ==================== Deliverables Editing ====================

    def update_deliverables_full(
        self,
        rfp_id: str,
        technical_deliverables: List[Dict[str, Any]],
        commercial_deliverables: List[Dict[str, Any]],
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Update complete deliverables list

        Args:
            rfp_id: RFP ID
            technical_deliverables: Updated technical deliverables list
            commercial_deliverables: Updated commercial deliverables list
            edited_by: Username performing the edit

        Returns:
            Dict with success status
        """
        try:
            current = self.db.get_rfp_deliverables(rfp_id)
            if not current:
                return {
                    "success": False,
                    "error": "Deliverables not found",
                    "message": f"No deliverables found for RFP: {rfp_id}"
                }

            # Prepare metadata
            deliverables_count = len(technical_deliverables) + len(
                commercial_deliverables
            )

            # Create edit history
            previous_version = {
                "technical": current.get("technical_deliverables", []),
                "commercial": current.get("commercial_deliverables", [])
            }
            edit_history = self._capture_edit_history(
                previous_version,
                edited_by,
                f"Updated deliverables ({deliverables_count} total)"
            )

            # Update database
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE rfp_deliverables
                        SET technical_deliverables = %s,
                            commercial_deliverables = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE rfp_id = %s
                    """, (
                        json.dumps(technical_deliverables, cls=SafeJSONEncoder),
                        json.dumps(commercial_deliverables, cls=SafeJSONEncoder),
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        rfp_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "rfp_id": rfp_id,
                "technical_count": len(technical_deliverables),
                "commercial_count": len(commercial_deliverables),
                "edited_by": edited_by,
                "message": "Deliverables updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update deliverables: {str(e)}"
            }

    def add_deliverable_ui(
        self,
        rfp_id: str,
        deliverable_type: str,
        deliverable_data: Dict[str, Any],
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Add new deliverable via UI

        Args:
            rfp_id: RFP ID
            deliverable_type: "technical" or "commercial"
            deliverable_data: Deliverable data to add
            edited_by: Username performing the edit

        Returns:
            Dict with success status
        """
        try:
            current = self.db.get_rfp_deliverables(rfp_id)
            if not current:
                return {
                    "success": False,
                    "error": "Deliverables not found",
                    "message": f"No deliverables found for RFP: {rfp_id}"
                }

            # Get current lists
            if deliverable_type == "technical":
                current_list = current.get("technical_deliverables", [])
                new_list = current_list + [deliverable_data]
                tech_deliv = new_list
                comm_deliv = current.get("commercial_deliverables", [])
            elif deliverable_type == "commercial":
                current_list = current.get("commercial_deliverables", [])
                new_list = current_list + [deliverable_data]
                tech_deliv = current.get("technical_deliverables", [])
                comm_deliv = new_list
            else:
                return {
                    "success": False,
                    "error": "Invalid deliverable type",
                    "message": "Must be 'technical' or 'commercial'"
                }

            # Create edit history
            previous_version = {
                "technical": current.get("technical_deliverables", []),
                "commercial": current.get("commercial_deliverables", [])
            }
            edit_history = self._capture_edit_history(
                previous_version,
                edited_by,
                f"Added {deliverable_type} deliverable"
            )

            # Update database
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE rfp_deliverables
                        SET technical_deliverables = %s,
                            commercial_deliverables = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE rfp_id = %s
                    """, (
                        json.dumps(tech_deliv, cls=SafeJSONEncoder),
                        json.dumps(comm_deliv, cls=SafeJSONEncoder),
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        rfp_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "rfp_id": rfp_id,
                "deliverable_type": deliverable_type,
                "edited_by": edited_by,
                "message": f"Added {deliverable_type} deliverable"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to add deliverable: {str(e)}"
            }

    def remove_deliverable_ui(
        self,
        rfp_id: str,
        deliverable_type: str,
        index: int,
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Remove deliverable via UI

        Args:
            rfp_id: RFP ID
            deliverable_type: "technical" or "commercial"
            index: Index of deliverable to remove (0-based)
            edited_by: Username performing the edit

        Returns:
            Dict with success status
        """
        try:
            current = self.db.get_rfp_deliverables(rfp_id)
            if not current:
                return {
                    "success": False,
                    "error": "Deliverables not found",
                    "message": f"No deliverables found for RFP: {rfp_id}"
                }

            # Get current lists
            if deliverable_type == "technical":
                current_list = current.get("technical_deliverables", [])
                if index >= len(current_list) or index < 0:
                    return {
                        "success": False,
                        "error": "Invalid index",
                        "message": f"Index {index} out of range"
                    }
                new_list = current_list[:index] + current_list[index + 1 :]
                tech_deliv = new_list
                comm_deliv = current.get("commercial_deliverables", [])
            elif deliverable_type == "commercial":
                current_list = current.get("commercial_deliverables", [])
                if index >= len(current_list) or index < 0:
                    return {
                        "success": False,
                        "error": "Invalid index",
                        "message": f"Index {index} out of range"
                    }
                new_list = current_list[:index] + current_list[index + 1 :]
                tech_deliv = current.get("technical_deliverables", [])
                comm_deliv = new_list
            else:
                return {
                    "success": False,
                    "error": "Invalid deliverable type",
                    "message": "Must be 'technical' or 'commercial'"
                }

            # Create edit history
            previous_version = {
                "technical": current.get("technical_deliverables", []),
                "commercial": current.get("commercial_deliverables", [])
            }
            edit_history = self._capture_edit_history(
                previous_version,
                edited_by,
                f"Removed {deliverable_type} deliverable at index {index}"
            )

            # Update database
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE rfp_deliverables
                        SET technical_deliverables = %s,
                            commercial_deliverables = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE rfp_id = %s
                    """, (
                        json.dumps(tech_deliv, cls=SafeJSONEncoder),
                        json.dumps(comm_deliv, cls=SafeJSONEncoder),
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        rfp_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "rfp_id": rfp_id,
                "deliverable_type": deliverable_type,
                "removed_index": index,
                "edited_by": edited_by,
                "message": f"Removed {deliverable_type} deliverable"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to remove deliverable: {str(e)}"
            }

    # ==================== Assignments Editing ====================

    def update_assignments_full(
        self,
        rfp_id: str,
        updated_assignments_report: Dict[str, Any],
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Update complete assignments report

        Args:
            rfp_id: RFP ID
            updated_assignments_report: Complete updated assignment report
            edited_by: Username performing the edit

        Returns:
            Dict with success status
        """
        try:
            current = self.db.get_rfp_assignments(rfp_id)
            if not current:
                return {
                    "success": False,
                    "error": "Assignments not found",
                    "message": f"No assignments found for RFP: {rfp_id}"
                }

            current_report = current.get("assignment_report", {})

            # Create edit history
            edit_history = self._capture_edit_history(
                current_report,
                edited_by,
                "Updated assignments report"
            )

            # Update database
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE rfp_assignments
                        SET assignment_report = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE rfp_id = %s
                    """, (
                        json.dumps(updated_assignments_report, cls=SafeJSONEncoder),
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        rfp_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "rfp_id": rfp_id,
                "edited_by": edited_by,
                "message": "Assignments updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update assignments: {str(e)}"
            }

    # ==================== Client Briefs Editing ====================

    def update_client_brief_full(
        self,
        brief_id: int,
        updated_brief_data: Dict[str, Any],
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Update complete client brief

        Args:
            brief_id: Client brief ID
            updated_brief_data: Updated brief data (client_overview + granite_opportunity)
            edited_by: Username performing the edit

        Returns:
            Dict with success status
        """
        try:
            current = self.db.get_client_brief(brief_id)
            if not current:
                return {
                    "success": False,
                    "error": "Brief not found",
                    "message": f"No client brief found with ID: {brief_id}"
                }

            current_brief_data = current.get("brief_data", {})

            # Create edit history
            edit_history = self._capture_edit_history(
                current_brief_data,
                edited_by,
                "Updated client brief"
            )

            # Update database
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE client_briefs
                        SET brief_data = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE id = %s
                    """, (
                        json.dumps(updated_brief_data, cls=SafeJSONEncoder),
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        brief_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "brief_id": brief_id,
                "edited_by": edited_by,
                "message": "Client brief updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update client brief: {str(e)}"
            }

    def update_client_brief_section(
        self,
        brief_id: int,
        section_name: str,
        section_data: Dict[str, Any],
        edited_by: str
    ) -> Dict[str, Any]:
        """
        Update single section of client brief (client_overview or granite_opportunity)

        Args:
            brief_id: Client brief ID
            section_name: "client_overview" or "granite_opportunity"
            section_data: Updated section data
            edited_by: Username performing the edit

        Returns:
            Dict with success status
        """
        try:
            current = self.db.get_client_brief(brief_id)
            if not current:
                return {
                    "success": False,
                    "error": "Brief not found",
                    "message": f"No client brief found with ID: {brief_id}"
                }

            current_brief_data = current.get("brief_data", {})

            if section_name not in ["client_overview", "granite_opportunity"]:
                return {
                    "success": False,
                    "error": "Invalid section",
                    "message": "Section must be 'client_overview' or 'granite_opportunity'"
                }

            # Create edit history
            previous_section = current_brief_data.get(section_name, {})
            edit_history = self._capture_edit_history(
                {"section": section_name, "data": previous_section},
                edited_by,
                f"Updated {section_name}"
            )

            # Update the section
            current_brief_data[section_name] = section_data

            # Update database
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE client_briefs
                        SET brief_data = %s,
                            last_edited_by = %s,
                            last_edited_at = CURRENT_TIMESTAMP,
                            edit_history = %s
                        WHERE id = %s
                    """, (
                        json.dumps(current_brief_data, cls=SafeJSONEncoder),
                        edited_by,
                        json.dumps(edit_history, cls=SafeJSONEncoder),
                        brief_id
                    ))
                    conn.commit()

            return {
                "success": True,
                "brief_id": brief_id,
                "section": section_name,
                "edited_by": edited_by,
                "message": f"Updated {section_name} successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update client brief section: {str(e)}"
            }
