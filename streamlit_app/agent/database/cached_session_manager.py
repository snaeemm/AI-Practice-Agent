"""
Cached wrapper around SessionManager for performance optimization.
Uses in-memory cache with background sync to PostgreSQL.
"""

from typing import Dict, Any, List, Optional

from .session_manager import SessionManager
from .session_cache import SessionCache


class CachedSessionManager:
    """
    Wrapper around SessionManager that uses in-memory caching.

    - Message reads come from cache (0 DB queries)
    - Message writes append to cache + queue for background sync
    - Session activity updates are queued
    """

    def __init__(
        self,
        session_manager: SessionManager,
        cache: SessionCache
    ):
        self.session_manager = session_manager
        self.cache = cache
        self.db = session_manager.db

    # ==================== Delegate to SessionManager ====================

    def create_user(self, username: str, email: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """Create new user (direct to DB)"""
        return self.session_manager.create_user(username, email, metadata)

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username (direct to DB)"""
        return self.session_manager.get_user(username)

    def get_or_create_user(self, username: str, email: Optional[str] = None) -> str:
        """Get or create user (direct to DB)"""
        return self.session_manager.get_or_create_user(username, email)

    def create_session(
        self,
        user_id: str,
        session_name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create new session (direct to DB)"""
        return self.session_manager.create_session(user_id, session_name, metadata)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session info (direct to DB)"""
        return self.session_manager.get_session(session_id)

    def list_user_sessions(
        self,
        user_id: str,
        limit: Optional[int] = None,
        active_only: bool = False
    ) -> List[Dict]:
        """List user sessions (direct to DB)"""
        return self.session_manager.list_user_sessions(user_id, limit, active_only)

    def delete_session(self, session_id: str):
        """Delete session (direct to DB + clear cache)"""
        self.session_manager.delete_session(session_id)
        self.cache.clear_messages(session_id)

    # ==================== Message Management (CACHED) ====================

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
        Add message to session.

        OPTIMIZED: Appends to cache immediately, queues for background sync.
        Returns immediately without waiting for PostgreSQL.
        """
        # Get next sequence number from cache (no DB query!)
        sequence_number = self.cache.get_next_sequence_number(session_id)

        # Append to cache immediately (instant UI update)
        self.cache.append_message(
            session_id=session_id,
            role=role,
            content=content or "",
            sequence_number=sequence_number,
            message_id=None  # Will be assigned by DB during sync
        )

        # Queue session activity update (timestamp)
        self.cache.queue_session_update(session_id)

        # Return a placeholder message_id (actual ID assigned during background sync)
        return f"pending-{session_id}-{sequence_number}"

    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        role_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Get messages for a session.

        OPTIMIZED: Returns from cache if available (0 DB queries).
        Falls back to DB on cache miss, then caches the result.
        """
        # Try cache first
        cached_messages = self.cache.get_messages(session_id)

        if cached_messages is not None:
            # Apply filters if needed
            messages = cached_messages
            if role_filter:
                messages = [m for m in messages if m['role'] == role_filter]
            if limit:
                messages = messages[-limit:]  # Most recent N messages
            return messages

        # Cache miss - load from DB and cache
        messages = self.session_manager.get_session_messages(
            session_id=session_id,
            limit=limit,
            role_filter=role_filter
        )

        # Cache the full message list (before filtering)
        if not role_filter and not limit:
            self.cache.set_messages(session_id, messages)

        return messages

    def update_session_activity(self, session_id: str):
        """
        Update session activity timestamp.

        OPTIMIZED: Queued for background sync instead of immediate DB write.
        """
        self.cache.queue_session_update(session_id)

    # ==================== Delegate other methods ====================

    def set_active_rfp(self, session_id: str, rfp_id: str):
        """Set active RFP for session (direct to DB)"""
        return self.session_manager.set_active_rfp(session_id, rfp_id)

    def get_active_rfp(self, session_id: str) -> Optional[str]:
        """Get active RFP for session (direct to DB)"""
        return self.session_manager.get_active_rfp(session_id)

    def close_session(self, session_id: str):
        """Close session (direct to DB)"""
        return self.session_manager.close_session(session_id)

    # ==================== Statistics ====================

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return self.cache.get_stats()
