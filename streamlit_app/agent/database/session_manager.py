"""
Session Manager for PostgreSQL-backed persistent sessions
Handles users, sessions, messages, and RFP associations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class SessionManager:
    """Manage user sessions and conversation history in PostgreSQL"""

    def __init__(self, db):
        """
        Initialize SessionManager

        Args:
            db: DatabaseManager instance
        """
        self.db = db

    # ==================== User Management ====================

    def create_user(self, username: str, email: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """
        Create new user

        Args:
            username: Unique username
            email: Optional email address
            metadata: Optional user metadata

        Returns:
            user_id (UUID as string)
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rfp_users (username, email, user_metadata)
                    VALUES (%s, %s, %s)
                    RETURNING user_id
                """, (username, email, json.dumps(metadata or {})))
                conn.commit()
                return str(cursor.fetchone()[0])

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        from psycopg2.extras import RealDictCursor

        with self.db._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM rfp_users WHERE username = %s
                """, (username,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id"""
        from psycopg2.extras import RealDictCursor

        with self.db._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM rfp_users WHERE user_id = %s
                """, (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def get_or_create_user(self, username: str, email: Optional[str] = None) -> str:
        """
        Get existing user or create new one

        Args:
            username: Username
            email: Optional email

        Returns:
            user_id (UUID as string)
        """
        user = self.get_user(username)
        if user:
            return str(user['user_id'])
        return self.create_user(username, email)

    def update_user_activity(self, user_id: str):
        """Update user's last_active timestamp"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_users
                    SET last_active = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()

    # ==================== Session Management ====================

    def create_session(
        self,
        user_id: str,
        session_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create new session

        Args:
            user_id: User ID
            session_name: Optional session name
            metadata: Optional session metadata

        Returns:
            session_id (UUID as string)
        """
        if not session_name:
            session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rfp_sessions (user_id, session_name, session_metadata)
                    VALUES (%s, %s, %s)
                    RETURNING session_id
                """, (user_id, session_name, json.dumps(metadata or {})))
                conn.commit()
                return str(cursor.fetchone()[0])

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details"""
        from psycopg2.extras import RealDictCursor

        with self.db._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM rfp_sessions WHERE session_id = %s
                """, (session_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

    def list_user_sessions(
        self,
        user_id: str,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Dict]:
        """
        List all sessions for a user

        Args:
            user_id: User ID
            active_only: Only return active sessions
            limit: Maximum sessions to return

        Returns:
            List of session dictionaries
        """
        from psycopg2.extras import RealDictCursor

        query = "SELECT * FROM rfp_sessions WHERE user_id = %s"
        params = [user_id]

        if active_only:
            query += " AND is_active = true"

        query += " ORDER BY updated_at DESC LIMIT %s"
        params.append(limit)

        with self.db._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

    def update_session_activity(self, session_id: str):
        """Update session's last activity timestamp (triggers auto-update)"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_sessions
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                """, (session_id,))
                conn.commit()

    def rename_session(self, session_id: str, new_name: str):
        """Rename a session"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_sessions
                    SET session_name = %s
                    WHERE session_id = %s
                """, (new_name, session_id))
                conn.commit()

    def close_session(self, session_id: str):
        """Mark session as inactive"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_sessions
                    SET is_active = false
                    WHERE session_id = %s
                """, (session_id,))
                conn.commit()

    def delete_session(self, session_id: str):
        """Permanently delete session and all messages"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM rfp_sessions WHERE session_id = %s
                """, (session_id,))
                conn.commit()

    # ==================== Message Management ====================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict] = None,
        tool_result: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add message to session

        Args:
            session_id: Session ID
            role: Message role ('user', 'assistant', 'system', 'tool')
            content: Message content
            tool_name: Tool name (for tool messages)
            tool_args: Tool arguments (for tool messages)
            tool_result: Tool result (for tool messages)
            metadata: Optional message metadata

        Returns:
            message_id (UUID as string)
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COALESCE(MAX(sequence_number), 0) + 1
                    FROM rfp_messages
                    WHERE session_id = %s
                """, (session_id,))
                sequence_number = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO rfp_messages
                    (session_id, role, content, tool_name, tool_args, tool_result,
                     message_metadata, sequence_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING message_id
                """, (
                    session_id, role, content, tool_name,
                    json.dumps(tool_args) if tool_args else None,
                    json.dumps(tool_result) if tool_result else None,
                    json.dumps(metadata or {}),
                    sequence_number
                ))
                conn.commit()

                self.update_session_activity(session_id)

                return str(cursor.fetchone()[0])

    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        role_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Get messages for a session in chronological order

        Args:
            session_id: Session ID
            limit: Maximum messages to return (most recent)
            role_filter: Filter by role ('user', 'assistant', etc.)

        Returns:
            List of message dictionaries
        """
        from psycopg2.extras import RealDictCursor

        query = "SELECT * FROM rfp_messages WHERE session_id = %s"
        params = [session_id]

        if role_filter:
            query += " AND role = %s"
            params.append(role_filter)

        query += " ORDER BY sequence_number ASC"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        with self.db._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

    def get_conversation_history(
        self,
        session_id: str,
        format: str = "dict"
    ) -> List[Dict]:
        """
        Get formatted conversation history

        Args:
            session_id: Session ID
            format: Output format ('dict' or 'adk' for ADK-compatible format)

        Returns:
            List of formatted messages
        """
        messages = self.get_session_messages(session_id)

        if format == "adk":
            history = []
            for msg in messages:
                if msg['role'] == 'tool':
                    continue

                adk_msg = {
                    'role': msg['role'],
                    'parts': [{'text': msg['content']}] if msg['content'] else []
                }
                history.append(adk_msg)
            return history

        return messages

    def clear_session_messages(self, session_id: str, keep_last_n: int = 0):
        """
        Clear old messages from session

        Args:
            session_id: Session ID
            keep_last_n: Number of recent messages to keep
        """
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                if keep_last_n > 0:
                    cursor.execute("""
                        DELETE FROM rfp_messages
                        WHERE session_id = %s
                        AND sequence_number < (
                            SELECT MAX(sequence_number) - %s
                            FROM rfp_messages
                            WHERE session_id = %s
                        )
                    """, (session_id, keep_last_n, session_id))
                else:
                    cursor.execute("""
                        DELETE FROM rfp_messages WHERE session_id = %s
                    """, (session_id,))
                conn.commit()

    # ==================== RFP Association ====================

    def associate_rfp_with_session(self, session_id: str, rfp_id: str):
        """Link RFP to session"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO rfp_session_rfps (session_id, rfp_id)
                    VALUES (%s, %s)
                    ON CONFLICT (session_id, rfp_id) DO NOTHING
                """, (session_id, rfp_id))
                conn.commit()

    def set_active_rfp(self, session_id: str, rfp_id: str):
        """Set currently active RFP for session"""
        self.associate_rfp_with_session(session_id, rfp_id)

        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE rfp_sessions
                    SET active_rfp_id = %s
                    WHERE session_id = %s
                """, (rfp_id, session_id))
                conn.commit()

    def get_session_rfps(self, session_id: str) -> List[str]:
        """Get all RFPs associated with session"""
        with self.db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT rfp_id FROM rfp_session_rfps
                    WHERE session_id = %s
                    ORDER BY added_at DESC
                """, (session_id,))
                return [row[0] for row in cursor.fetchall()]

    def get_active_rfp(self, session_id: str) -> Optional[str]:
        """Get currently active RFP for session"""
        session = self.get_session(session_id)
        return session['active_rfp_id'] if session else None

    # ==================== Context Management ====================

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session context

        Returns dict with:
        - session: session details
        - user: user details
        - active_rfp: active RFP ID
        - rfps: list of associated RFPs
        - recent_messages: last 10 messages
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        user = self.get_user_by_id(str(session['user_id']))
        messages = self.get_session_messages(session_id, limit=10)
        rfps = self.get_session_rfps(session_id)

        return {
            'session': session,
            'user': user,
            'active_rfp': session.get('active_rfp_id'),
            'rfps': rfps,
            'recent_messages': messages
        }
