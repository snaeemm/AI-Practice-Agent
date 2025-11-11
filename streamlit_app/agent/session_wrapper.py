"""
Session Wrapper for ADK Agent
Transparently saves conversation history to PostgreSQL without exposing session management to the agent

OPTIMIZED: Uses cached session manager for performance.
"""

from typing import Optional
from agent.database.db_singleton import get_db
from agent.database.session_manager import SessionManager
from agent.database.cached_session_manager import CachedSessionManager
from agent.database.session_cache import SessionCache


class SessionContext:
    """
    Context manager that wraps ADK agent interactions and persists to PostgreSQL

    OPTIMIZED: Uses CachedSessionManager for performance.

    Usage:
        # Create or load session
        session = SessionContext.create("username", "My RFP Session")
        # or
        session = SessionContext.load(session_id)

        # Use with agent (ADK handles the rest)
        # Conversation is automatically saved to PostgreSQL
    """

    # Class-level cache instance (set by chat.py)
    _cache: Optional[SessionCache] = None

    @classmethod
    def set_cache(cls, cache: SessionCache):
        """Set the global cache instance (called by chat.py on startup)"""
        cls._cache = cache

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db = get_db()

        # Use regular SessionManager
        session_manager = SessionManager(self.db)

        # Wrap with cache if available, otherwise use uncached
        if self._cache is not None:
            self.session_mgr = CachedSessionManager(
                session_manager=session_manager,
                cache=self._cache
            )
        else:
            # Fallback to uncached (for backwards compatibility)
            self.session_mgr = session_manager

        # Verify session exists
        self.session = self.session_mgr.get_session(session_id)
        if not self.session:
            raise ValueError(f"Session not found: {session_id}")

        # CRITICAL: Always ensure cache is initialized for this session
        # This prevents race conditions and cache misses on first message
        if self._cache is not None:
            cached_messages = self._cache.get_messages(session_id)
            if cached_messages is None:
                # Cache miss - load from DB and initialize cache
                print(f"🔄 Cache miss for session {session_id} - loading from DB")
                existing_messages = session_manager.get_session_messages(session_id)
                self._cache.set_messages(session_id, existing_messages)
                print(f"✅ Cache initialized with {len(existing_messages)} messages")
            else:
                print(f"✅ Cache hit for session {session_id} - {len(cached_messages)} messages")

    @classmethod
    def create(cls, username: str = "default_user", session_name: Optional[str] = None):
        """Create new session"""
        db = get_db()
        session_mgr = SessionManager(db)

        user_id = session_mgr.get_or_create_user(username)
        session_id = session_mgr.create_session(user_id, session_name)

        # Initialize cache for new session (prevents race condition on first message)
        if cls._cache is not None:
            cls._cache.set_messages(session_id, [])

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

    def save_user_message_with_image(self, content: str, image_data: dict):
        """Save user message with image to database

        Args:
            content: Text message
            image_data: Dict with 'bytes' (base64 encoded) and 'mime_type'
        """
        import base64
        import json

        # Store image as metadata in message
        message_data = {
            'content': content,
            'image': {
                'bytes': base64.b64encode(image_data['bytes']).decode('utf-8'),
                'mime_type': image_data['mime_type']
            }
        }
        self.session_mgr.add_message(self.session_id, "user", json.dumps(message_data))

    def save_assistant_message(self, content: str):
        """Save assistant message to database"""
        self.session_mgr.add_message(self.session_id, "assistant", content)

    def save_generated_image(self, image_bytes: bytes, prompt: str, aspect_ratio: str = "1:1"):
        """Save a generated image to chat history for display

        Args:
            image_bytes: PNG image bytes
            prompt: The prompt used to generate the image
            aspect_ratio: Image aspect ratio
        """
        import base64
        import json

        # Store image as a special assistant message with image data
        message_data = {
            'type': 'generated_image',
            'image': {
                'bytes': base64.b64encode(image_bytes).decode('utf-8'),
                'prompt': prompt,
                'aspect_ratio': aspect_ratio
            }
        }
        self.session_mgr.add_message(self.session_id, "assistant", json.dumps(message_data))

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
