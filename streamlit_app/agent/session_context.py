"""
Session Context Helper
Provides access to current session's user_id for tools that need it
"""

import streamlit as st
from typing import Optional


def get_current_user_id() -> Optional[str]:
    """
    Get the current user_id from Streamlit session state.

    This allows tools to access the session's user_id without requiring
    it to be passed as a parameter.

    Returns:
        str: The user_id from the current session, or None if not available
    """
    try:
        # Try to get from Streamlit session state
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
    Store the current user_id in Streamlit session state for tools to access.

    Args:
        user_id: The user_id to store
    """
    try:
        st.session_state.current_user_id = user_id
    except Exception as e:
        print(f"⚠️ Error setting user_id in session: {e}")
