"""
Session Context Helper
Provides access to current session's user_id and session_id for tools that need it
Uses global storage with thread IDs to work across sub-agent boundaries
"""

import streamlit as st
from typing import Optional
import threading

# Global storage for session context (keyed by thread ID for isolation)
_session_storage = {}
_storage_lock = threading.Lock()

def _get_current_thread_id() -> int:
    """Get current thread ID"""
    return threading.get_ident()

def _store_session_context(user_id: str, session_id: str):
    """Store session context for current thread"""
    thread_id = _get_current_thread_id()
    with _storage_lock:
        _session_storage[thread_id] = {
            'user_id': user_id,
            'session_id': session_id
        }

def _get_session_context() -> Optional[dict]:
    """Get session context for current thread"""
    thread_id = _get_current_thread_id()
    with _storage_lock:
        return _session_storage.get(thread_id)


def get_current_user_id() -> Optional[str]:
    """
    Get the current user_id from context.

    This allows tools to access the session's user_id without requiring
    it to be passed as a parameter. Works in sub-agents and async contexts.

    Returns:
        str: The user_id from the current session, or None if not available
    """
    try:
        # First try to get from context variable (works in sub-agents)
        user_id = _current_user_id.get()
        if user_id:
            return user_id

        # Fallback: Try to get from Streamlit session state (main thread only)
        if 'current_user_id' in st.session_state:
            return st.session_state.current_user_id

        # Alternative: try to get from session object if it exists
        if 'session' in st.session_state:
            session = st.session_state.session
            if hasattr(session, 'session') and 'user_id' in session.session:
                return str(session.session['user_id'])

        return None
    except Exception as e:
        print(f"⚠️ Error getting user_id from session: {e}")
        return None


def set_current_user_id(user_id: str):
    """
    Store the current user_id in both context variable and Streamlit session state.

    Args:
        user_id: The user_id to store
    """
    try:
        # Set in context variable (works across async boundaries and sub-agents)
        _current_user_id.set(user_id)

        # Also set in streamlit session state for backwards compatibility
        st.session_state.current_user_id = user_id
    except Exception as e:
        print(f"⚠️ Error setting user_id in session: {e}")


def get_user_id_from_session_id(session_id: str) -> Optional[str]:
    """
    Look up user_id from session_id via database.

    This is the most reliable way to get user_id in sub-agents since it doesn't
    depend on context variables or session state propagation.

    Args:
        session_id: The ADK session ID

    Returns:
        str: The user_id for this session, or None if not found
    """
    try:
        from agent.database.db_singleton import get_db
        from agent.database.session_manager import SessionManager

        db = get_db()
        session_mgr = SessionManager(db)

        session = session_mgr.get_session(session_id)
        if session and 'user_id' in session:
            return str(session['user_id'])

        return None
    except Exception as e:
        print(f"⚠️ Error looking up user_id from session_id {session_id}: {e}")
        import traceback
        traceback.print_exc()
        return None
