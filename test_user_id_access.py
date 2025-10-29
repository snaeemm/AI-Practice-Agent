#!/usr/bin/env python3
"""
Test script to verify user_id accessibility in marketing agent tools
Tests the actual execution flow to see what context is available
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'streamlit_app')))

from dotenv import load_dotenv
load_dotenv('streamlit_app/agent/.env')

from agent.session_context import get_current_user_id, set_current_user_id
from agent.session_wrapper import SessionContext
from agent.database.db_singleton import get_db
from agent.database.session_manager import SessionManager
from agent.database.marketing_profile_manager import MarketingProfileManager

def test_session_to_user_id_lookup():
    """Test if we can get user_id from session_id via database"""
    print("\n" + "="*80)
    print("TEST 1: Can we look up user_id from session_id?")
    print("="*80)

    db = get_db()
    session_mgr = SessionManager(db)

    # Get or create test user
    user_id = session_mgr.get_or_create_user("test_user")
    print(f"✅ Test user_id: {user_id}")

    # Create a test session
    session_id = session_mgr.create_session(user_id, "Test Session")
    print(f"✅ Test session_id: {session_id}")

    # Now try to look up user_id from session_id
    session = session_mgr.get_session(session_id)
    print(f"\n📋 Session data: {session}")

    if session and 'user_id' in session:
        retrieved_user_id = str(session['user_id'])
        print(f"\n✅ SUCCESS: Retrieved user_id from session_id: {retrieved_user_id}")
        print(f"   Match: {retrieved_user_id == user_id}")
        return True, session_id, user_id
    else:
        print(f"\n❌ FAILED: Could not retrieve user_id from session_id")
        return False, None, None

def test_context_vars():
    """Test if contextvars work"""
    print("\n" + "="*80)
    print("TEST 2: Do contextvars work across function calls?")
    print("="*80)

    # Set user_id in context
    test_user_id = "test-user-123"
    set_current_user_id(test_user_id)
    print(f"✅ Set user_id in context: {test_user_id}")

    # Try to retrieve it
    retrieved = get_current_user_id()
    print(f"📋 Retrieved user_id: {retrieved}")

    if retrieved == test_user_id:
        print(f"✅ SUCCESS: Context vars work!")
        return True
    else:
        print(f"❌ FAILED: Context vars don't work (got: {retrieved})")
        return False

def test_profile_query_with_session_id(session_id):
    """Test if we can query profiles using session_id -> user_id lookup"""
    print("\n" + "="*80)
    print("TEST 3: Can we query profiles via session_id lookup?")
    print("="*80)

    db = get_db()
    session_mgr = SessionManager(db)
    profile_mgr = MarketingProfileManager(db)

    # Look up user_id from session_id
    session = session_mgr.get_session(session_id)
    if not session:
        print(f"❌ FAILED: Session not found: {session_id}")
        return False

    user_id = str(session['user_id'])
    print(f"✅ Looked up user_id from session: {user_id}")

    # Query profiles
    profiles = profile_mgr.get_user_profiles(user_id)
    print(f"\n📋 Found {len(profiles)} profiles:")
    for p in profiles:
        print(f"   - {p['profile_name']} ({p['profile_type']})")

    print(f"\n✅ SUCCESS: Profile query works with session_id lookup!")
    return True

def test_create_wrapper_function():
    """Test creating a wrapper function that does session_id -> user_id lookup"""
    print("\n" + "="*80)
    print("TEST 4: Can we create a wrapper function for tools?")
    print("="*80)

    def get_user_id_from_session(session_id: str) -> str:
        """Helper function to get user_id from session_id"""
        db = get_db()
        session_mgr = SessionManager(db)
        session = session_mgr.get_session(session_id)
        if session and 'user_id' in session:
            return str(session['user_id'])
        return None

    # Test it
    _, test_session_id, expected_user_id = test_session_to_user_id_lookup()
    if not test_session_id:
        print("❌ Cannot test without session_id")
        return False

    retrieved_user_id = get_user_id_from_session(test_session_id)
    print(f"\n📋 Wrapper function returned: {retrieved_user_id}")
    print(f"   Expected: {expected_user_id}")

    if retrieved_user_id == expected_user_id:
        print(f"\n✅ SUCCESS: Wrapper function works!")
        print(f"\n💡 SOLUTION: Tools can use this wrapper to get user_id from session_id")
        return True
    else:
        print(f"❌ FAILED: Wrapper returned wrong user_id")
        return False

def main():
    print("\n" + "="*80)
    print("TESTING USER_ID ACCESSIBILITY FOR MARKETING AGENT TOOLS")
    print("="*80)

    # Run tests
    success1, session_id, user_id = test_session_to_user_id_lookup()
    success2 = test_context_vars()

    if success1 and session_id:
        success3 = test_profile_query_with_session_id(session_id)
        success4 = test_create_wrapper_function()
    else:
        success3 = False
        success4 = False

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✅ Session -> User ID lookup:        {'PASS' if success1 else 'FAIL'}")
    print(f"✅ Context vars:                     {'PASS' if success2 else 'FAIL'}")
    print(f"✅ Profile query via session lookup: {'PASS' if success3 else 'FAIL'}")
    print(f"✅ Wrapper function:                 {'PASS' if success4 else 'FAIL'}")

    if all([success1, success2, success3, success4]):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n💡 SOLUTION:")
        print("   1. Tools need access to session_id (not just user_id)")
        print("   2. Create helper: get_user_id_from_session(session_id)")
        print("   3. Tools call: user_id = get_user_id_from_session(session_id)")
        print("   4. Then query profiles with user_id")
    else:
        print("\n❌ SOME TESTS FAILED - need different approach")

    print("="*80 + "\n")

if __name__ == "__main__":
    main()
