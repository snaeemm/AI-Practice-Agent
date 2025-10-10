"""
Session Wrapper for ADK Agent
Transparently saves conversation history to PostgreSQL without exposing session management to the agent
"""

from typing import Optional
from agent.database.db_singleton import get_db
from agent.database.session_manager import SessionManager


class SessionContext:
    """
    Context manager that wraps ADK agent interactions and persists to PostgreSQL

    Usage:
        # Create or load session
        session = SessionContext.create("username", "My RFP Session")
        # or
        session = SessionContext.load(session_id)

        # Use with agent (ADK handles the rest)
        # Conversation is automatically saved to PostgreSQL
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db = get_db()
        self.session_mgr = SessionManager(self.db)

        # Verify session exists
        self.session = self.session_mgr.get_session(session_id)
        if not self.session:
            raise ValueError(f"Session not found: {session_id}")

    @classmethod
    def create(cls, username: str = "default_user", session_name: Optional[str] = None):
        """Create new session"""
        db = get_db()
        session_mgr = SessionManager(db)

        user_id = session_mgr.get_or_create_user(username)
        session_id = session_mgr.create_session(user_id, session_name)
        return cls(session_id)

    @classmethod
    def load(cls, session_id: str):
        """Load existing session"""
        return cls(session_id)

    @classmethod
    def list_sessions(cls, username: str = "default_user"):
        """List user's sessions"""
        db = get_db()
        session_mgr = SessionManager(db)

        user = session_mgr.get_user(username)
        if not user:
            return []

        return session_mgr.list_user_sessions(str(user['user_id']))

    def save_user_message(self, content: str):
        """Save user message to database"""
        self.session_mgr.add_message(self.session_id, "user", content)

    def save_assistant_message(self, content: str):
        """Save assistant message to database"""
        self.session_mgr.add_message(self.session_id, "assistant", content)

    def save_tool_call(self, tool_name: str, tool_args: dict, tool_result: dict):
        """Save tool call to database"""
        self.session_mgr.add_message(
            self.session_id,
            "tool",
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result
        )

    def get_history(self):
        """Get conversation history"""
        return self.session_mgr.get_session_messages(self.session_id)

    def set_active_rfp(self, rfp_id: str):
        """Associate RFP with this session"""
        self.session_mgr.set_active_rfp(self.session_id, rfp_id)

    def get_active_rfp(self) -> Optional[str]:
        """Get active RFP for this session"""
        return self.session_mgr.get_active_rfp(self.session_id)

    def close(self):
        """Mark session as inactive"""
        self.session_mgr.close_session(self.session_id)

    def delete(self):
        """Delete session permanently"""
        self.session_mgr.delete_session(self.session_id)


# Simple helper functions for easy usage
def create_session(username: str = "default_user", session_name: Optional[str] = None) -> SessionContext:
    """Create new session and return context"""
    return SessionContext.create(username, session_name)


def load_session(session_id: str) -> SessionContext:
    """Load existing session"""
    return SessionContext.load(session_id)


def list_sessions(username: str = "default_user"):
    """List user's sessions"""
    return SessionContext.list_sessions(username)
