import psycopg2
from psycopg2 import pool, extras
from psycopg2.extras import RealDictCursor, Json
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import settings

class DatabaseManager:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or settings.DATABASE_URL

        if not self.connection_string:
            raise ValueError("DATABASE_URL must be set in .env file")

        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                settings.DB_POOL_MIN_CONN,
                settings.DB_POOL_MAX_CONN,
                self.connection_string
            )

            if not self.connection_pool:
                raise Exception("Connection pool creation failed")

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"❌ Error creating connection pool: {error}")
            raise

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            conn.set_session(autocommit=False)
            yield conn
        except (Exception, psycopg2.DatabaseError) as error:
            if conn:
                conn.rollback()
            raise error
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def _init_database(self):
        """Initialize database schema from SQL file"""
        schema_path = Path(__file__).parent / "postgres_schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Database schema not found: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
                print("✅ Database schema initialized")

    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("✅ All database connections closed")

    # ==================== RFP Documents ====================

    def create_rfp_document(
        self,
        rfp_id: str,
        client_name: str,
        project_title: str,
        pdf_path: Optional[str] = None,
        submission_deadline: Optional[str] = None
    ) -> str:
        """Create or update RFP document"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rfp_documents (rfp_id, client_name, project_title, pdf_path, submission_deadline)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (rfp_id)
                    DO UPDATE SET
                        client_name = EXCLUDED.client_name,
                        project_title = EXCLUDED.project_title,
                        pdf_path = EXCLUDED.pdf_path,
                        submission_deadline = EXCLUDED.submission_deadline,
                        updated_date = CURRENT_TIMESTAMP
                """, (rfp_id, client_name, project_title, pdf_path, submission_deadline))
                conn.commit()
        return rfp_id

    def get_rfp_document(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        """Get RFP document metadata"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM rfp_documents WHERE rfp_id = %s", (rfp_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def list_recent_rfps(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent RFPs"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM rfp_documents
                    ORDER BY processed_date DESC LIMIT %s
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]

    def update_rfp_status(self, rfp_id: str, status: str):
        """Update RFP status"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_documents SET status = %s WHERE rfp_id = %s
                """, (status, rfp_id))
                conn.commit()

    # ==================== RFP Raw Data (Complete RFPData model) ====================

    def save_rfp_raw_data(self, rfp_id: str, rfp_data: Dict[str, Any]) -> int:
        """Save complete RFP extraction data as JSONB"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rfp_raw_data (rfp_id, rfp_data)
                    VALUES (%s, %s)
                    RETURNING id
                """, (rfp_id, Json(rfp_data)))
                conn.commit()
                return cursor.fetchone()[0]

    def get_rfp_raw_data(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        """Get complete RFP raw data"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM rfp_raw_data
                    WHERE rfp_id = %s
                    ORDER BY extracted_date DESC LIMIT 1
                """, (rfp_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def update_rfp_raw_data(self, rfp_id: str, updates: Dict[str, Any]):
        """Update RFP raw data using JSONB merge"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_raw_data
                    SET rfp_data = rfp_data || %s::jsonb
                    WHERE rfp_id = %s
                """, (json.dumps(updates), rfp_id))
                conn.commit()

    def save_raw_document_text(self, rfp_id: str, raw_text: str):
        """Save or update raw extracted document text"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_raw_data
                    SET raw_document_text = %s
                    WHERE rfp_id = %s
                """, (raw_text, rfp_id))
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO rfp_raw_data (rfp_id, rfp_data, raw_document_text)
                        VALUES (%s, '{}'::jsonb, %s)
                    """, (rfp_id, raw_text))
                conn.commit()

    def get_raw_document_text(self, rfp_id: str) -> Optional[str]:
        """Retrieve raw extracted document text"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT raw_document_text FROM rfp_raw_data
                    WHERE rfp_id = %s
                    ORDER BY extracted_date DESC LIMIT 1
                """, (rfp_id,))
                row = cursor.fetchone()
                return row[0] if row and row[0] else None

    # ==================== Deliverables ====================

    def save_rfp_deliverables(self, rfp_id: str, deliverables_data: Dict[str, Any]) -> int:
        """Save deliverables data"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rfp_deliverables
                    (rfp_id, client_and_opportunity, technical_deliverables,
                     commercial_deliverables, deliverables_metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    rfp_id,
                    deliverables_data.get('client_and_opportunity'),
                    Json(deliverables_data.get('technical_deliverables', [])),
                    Json(deliverables_data.get('commercial_deliverables', [])),
                    Json(deliverables_data.get('deliverables_metadata', {}))
                ))
                conn.commit()
                return cursor.fetchone()[0]

    def get_rfp_deliverables(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        """Get deliverables data"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM rfp_deliverables
                    WHERE rfp_id = %s
                    ORDER BY extracted_date DESC LIMIT 1
                """, (rfp_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def update_deliverable(
        self,
        rfp_id: str,
        deliverable_type: str,
        index: int,
        updates: Dict[str, Any]
    ):
        """Update specific deliverable in JSONB array"""
        column = f"{deliverable_type}_deliverables"

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for key, value in updates.items():
                    cursor.execute(f"""
                        UPDATE rfp_deliverables
                        SET {column} = jsonb_set(
                            {column},
                            %s,
                            %s,
                            true
                        )
                        WHERE rfp_id = %s
                    """, (f'{{{index},{key}}}', json.dumps(value), rfp_id))
                conn.commit()

    def add_deliverable(
        self,
        rfp_id: str,
        deliverable_type: str,
        deliverable_data: Dict[str, Any]
    ):
        """Add new deliverable to JSONB array"""
        column = f"{deliverable_type}_deliverables"

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE rfp_deliverables
                    SET {column} = {column} || %s::jsonb
                    WHERE rfp_id = %s
                """, (json.dumps([deliverable_data]), rfp_id))
                conn.commit()

    def remove_deliverable(
        self,
        rfp_id: str,
        deliverable_type: str,
        index: int
    ):
        """Remove deliverable from JSONB array"""
        column = f"{deliverable_type}_deliverables"

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE rfp_deliverables
                    SET {column} = {column} - %s
                    WHERE rfp_id = %s
                """, (index, rfp_id))
                conn.commit()

    # ==================== Assignments ====================

    def save_rfp_assignments(self, rfp_id: str, assignment_data: Dict[str, Any]) -> int:
        """Save assignment analysis"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rfp_assignments
                    (rfp_id, assignment_report, total_deliverables, granite_assigned, partner_assigned)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    rfp_id,
                    Json(assignment_data),
                    assignment_data.get('total_deliverables', 0),
                    assignment_data.get('granite_assigned', 0),
                    assignment_data.get('partner_assigned', 0)
                ))
                conn.commit()
                return cursor.fetchone()[0]

    def get_rfp_assignments(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        """Get assignment analysis"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM rfp_assignments
                    WHERE rfp_id = %s
                    ORDER BY analysis_date DESC LIMIT 1
                """, (rfp_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def update_assignment(self, rfp_id: str, section_name: str, updates: Dict[str, Any]):
        """Update assignment by section name"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT assignment_report FROM rfp_assignments
                    WHERE rfp_id = %s
                    ORDER BY analysis_date DESC LIMIT 1
                """, (rfp_id,))
                row = cursor.fetchone()

                if not row:
                    raise ValueError(f"No assignments found for rfp_id: {rfp_id}")

                report = dict(row)['assignment_report']
                assignments = report.get('assignments', [])

                for i, assignment in enumerate(assignments):
                    if assignment.get('deliverable_section') == section_name:
                        for key, value in updates.items():
                            assignment[key] = value
                        assignments[i] = assignment

                        with conn.cursor() as update_cursor:
                            update_cursor.execute("""
                                UPDATE rfp_assignments
                                SET assignment_report = jsonb_set(
                                    assignment_report,
                                    '{assignments}',
                                    %s::jsonb
                                )
                                WHERE rfp_id = %s
                            """, (json.dumps(assignments), rfp_id))

                        self.recalculate_assignment_counts(rfp_id)
                        conn.commit()
                        return

                raise ValueError(f"Section '{section_name}' not found in assignments")

    def recalculate_assignment_counts(self, rfp_id: str):
        """Recalculate granite_assigned and partner_assigned counts"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT assignment_report FROM rfp_assignments
                    WHERE rfp_id = %s
                    ORDER BY analysis_date DESC LIMIT 1
                """, (rfp_id,))
                row = cursor.fetchone()

                if not row:
                    return

                report = dict(row)['assignment_report']
                assignments = report.get('assignments', [])

                granite_count = sum(1 for a in assignments if 'Granite' in a.get('assigned_owner', ''))
                partner_count = len(assignments) - granite_count

                with conn.cursor() as update_cursor:
                    update_cursor.execute("""
                        UPDATE rfp_assignments
                        SET granite_assigned = %s, partner_assigned = %s
                        WHERE rfp_id = %s
                    """, (granite_count, partner_count, rfp_id))
                conn.commit()

    # ==================== Generated Files (Excel Reports) ====================

    def save_generated_file(self, session_id: str, file_name: str, file_type: str, file_data: bytes, rfp_id: str = None) -> int:
        """Save generated Excel file to database (session_id can be None for global files)"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO generated_files
                    (session_id, file_name, file_type, file_data, rfp_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (session_id, file_name, file_type, file_data, rfp_id))
                conn.commit()
                return cursor.fetchone()[0]

    def get_recent_generated_files(self, limit: int = 10):
        """Get recent generated files globally (not per-session)"""
        from psycopg2.extras import RealDictCursor
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, file_name, file_type, created_at, downloaded, rfp_id
                    FROM generated_files
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
                return cursor.fetchall()

    def get_session_generated_files(self, session_id: str):
        """Get all generated files for a session"""
        from psycopg2.extras import RealDictCursor
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, file_name, file_type, created_at, downloaded, rfp_id
                    FROM generated_files
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                """, (session_id,))
                return [dict(row) for row in cursor.fetchall()]

    def get_generated_file_data(self, file_id: int) -> Optional[bytes]:
        """Get the actual file bytes for download"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT file_data FROM generated_files WHERE id = %s
                """, (file_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    return bytes(row[0])
                return None

    def mark_file_downloaded(self, file_id: int):
        """Mark a file as downloaded"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE generated_files
                    SET downloaded = TRUE
                    WHERE id = %s
                """, (file_id,))
                conn.commit()

    def cleanup_old_files(self):
        """Delete files older than 24 hours"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM generated_files
                    WHERE created_at < NOW() - INTERVAL '24 hours'
                """)
                conn.commit()

    # ==================== Qualification Results ====================

    def save_qualification_results(self, rfp_id: str, qualification_data: Dict[str, Any]) -> int:
        """Save qualification results"""
        print(f"\n🔍 [DB SAVE] Attempting to save qualification results for: {rfp_id}")
        print(f"   Data keys: {list(qualification_data.keys())}")
        print(f"   Total score: {qualification_data.get('total_score')}")
        print(f"   Threshold: {qualification_data.get('threshold')}")
        print(f"   Qualifies: {qualification_data.get('qualifies')}")
        print(f"   Classification: {qualification_data.get('rfp_classification')}")

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO qualification_results
                        (rfp_id, qualification_report, total_score, threshold,
                         qualifies, rfp_classification)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        rfp_id,
                        Json(qualification_data),
                        qualification_data.get('total_score'),
                        qualification_data.get('threshold'),
                        qualification_data.get('qualifies'),
                        qualification_data.get('rfp_classification')
                    ))
                    conn.commit()
                    result_id = cursor.fetchone()[0]
                    print(f"✅ [DB SAVE] Successfully saved qualification with ID: {result_id}")
                    return result_id
        except Exception as e:
            print(f"❌ [DB SAVE] FAILED to save qualification results!")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise so calling code knows it failed

    def get_qualification_results(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        """Get qualification results"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM qualification_results
                    WHERE rfp_id = %s
                    ORDER BY qualified_date DESC LIMIT 1
                """, (rfp_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def update_qualification_field(self, rfp_id: str, field_path: str, new_value: Any):
        """
        Update specific field in qualification JSONB using jsonb_set()

        Args:
            rfp_id: RFP ID
            field_path: JSON path (e.g., "analyses.2.reasoning" or "threshold")
            new_value: New value to set

        Example:
            db.update_qualification_field("KHDA_2024", "analyses.2.reasoning", "Updated reasoning")
            db.update_qualification_field("KHDA_2024", "threshold", 2.8)
        """
        path_parts = field_path.replace('[', '.').replace(']', '').split('.')
        json_path = '{' + ','.join(path_parts) + '}'

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE qualification_results
                    SET qualification_report = jsonb_set(
                        qualification_report,
                        %s,
                        %s,
                        true
                    )
                    WHERE rfp_id = %s
                """, (json_path, json.dumps(new_value), rfp_id))
                conn.commit()

    # ==================== Capabilities Match ====================

    def save_capabilities_match(self, rfp_id: str, capabilities_data: Dict[str, Any]) -> int:
        """Save capabilities match analysis"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO capabilities_match
                    (rfp_id, matched_capabilities, partner_recommendations, capability_gaps, match_score)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    rfp_id,
                    Json(capabilities_data.get('matched_capabilities', [])),
                    Json(capabilities_data.get('partner_recommendations', [])),
                    Json(capabilities_data.get('capability_gaps', [])),
                    capabilities_data.get('match_score')
                ))
                conn.commit()
                return cursor.fetchone()[0]

    # ==================== Bid History Insights ====================

    def save_bid_insight(self, rfp_id: str, insight_data: Dict[str, Any]) -> int:
        """Save bid history insight"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO bid_history_insights
                    (rfp_id, client_name, industry, outcome, insight_data)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    rfp_id,
                    insight_data.get('client_name'),
                    insight_data.get('industry'),
                    insight_data.get('outcome'),
                    Json(insight_data)
                ))
                conn.commit()
                return cursor.fetchone()[0]

    def query_bid_history(
        self,
        client_name: Optional[str] = None,
        industry: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query bid history with filters"""
        query = "SELECT * FROM bid_history_insights WHERE 1=1"
        params = []

        if client_name:
            query += " AND client_name ILIKE %s"
            params.append(f"%{client_name}%")

        if industry:
            query += " AND industry ILIKE %s"
            params.append(f"%{industry}%")

        if outcome:
            query += " AND outcome = %s"
            params.append(outcome)

        query += " ORDER BY created_date DESC LIMIT %s"
        params.append(limit)

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

    # ==================== Complete Data Retrieval ====================

    def get_complete_rfp_data(self, rfp_id: str) -> Dict[str, Any]:
        """Get ALL data for an RFP (for report generation)"""
        return {
            'document': self.get_rfp_document(rfp_id),
            'raw_data': self.get_rfp_raw_data(rfp_id),
            'deliverables': self.get_rfp_deliverables(rfp_id),
            'assignments': self.get_rfp_assignments(rfp_id),
            'qualification': self.get_qualification_results(rfp_id)
        }

    # ==================== Session Management (Lazy Loading) ====================

    @property
    def session_manager(self):
        """Lazy load SessionManager to avoid circular imports"""
        if not hasattr(self, '_session_manager'):
            from .session_manager import SessionManager
            self._session_manager = SessionManager(self)
        return self._session_manager

    def create_session(self, user_id: str, session_name: Optional[str] = None) -> str:
        """Create new session"""
        return self.session_manager.create_session(user_id, session_name)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details"""
        return self.session_manager.get_session(session_id)

    def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get session messages"""
        return self.session_manager.get_session_messages(session_id, limit)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict] = None,
        tool_result: Optional[Dict] = None
    ) -> str:
        """Add message to session"""
        return self.session_manager.add_message(
            session_id, role, content, tool_name, tool_args, tool_result
        )

    def get_or_create_user(self, username: str, email: Optional[str] = None) -> str:
        """Get or create user"""
        return self.session_manager.get_or_create_user(username, email)

    def list_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """List user sessions"""
        return self.session_manager.list_user_sessions(user_id, active_only)
