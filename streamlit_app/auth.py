import streamlit as st
import bcrypt
from typing import Optional, Dict
from pathlib import Path

_migration_checked = False

def ensure_auth_migration():
    """Ensure auth migration has been run"""
    global _migration_checked

    if _migration_checked:
        return

    try:
        from agent.database.db_singleton import get_db
        db = get_db()

        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'rfp_users'
                    AND column_name = 'password_hash'
                """)

                if cursor.fetchone() is None:
                    migration_sql = Path(__file__).parent / "agent" / "database" / "add_auth_to_users.sql"

                    if migration_sql.exists():
                        with open(migration_sql, 'r') as f:
                            sql = f.read()

                        cursor.execute(sql)
                        conn.commit()
                        print("✅ Auth migration completed automatically")

        _migration_checked = True
    except Exception as e:
        print(f"⚠️ Migration check failed: {e}")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except:
        return False

def login(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate user and return user data if successful
    Returns None if authentication fails
    """
    ensure_auth_migration()

    from agent.database.db_singleton import get_db
    db = get_db()

    with db._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, username, full_name, password_hash,
                       is_active, must_change_password, email
                FROM rfp_users
                WHERE username = %s
            """, (username,))

            user = cursor.fetchone()

            if not user:
                return None

            user_id, username, full_name, password_hash, is_active, must_change_password, email = user

            if not is_active:
                return None

            if not verify_password(password, password_hash):
                return None

            cursor.execute("""
                UPDATE rfp_users
                SET last_active = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()

            return {
                'user_id': str(user_id),
                'username': username,
                'full_name': full_name,
                'email': email,
                'must_change_password': must_change_password
            }

def change_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """
    Change user password
    Returns (success: bool, message: str)
    """
    from agent.database.db_singleton import get_db
    db = get_db()

    with db._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT password_hash FROM rfp_users WHERE user_id = %s
            """, (user_id,))

            result = cursor.fetchone()
            if not result:
                return False, "User not found"

            current_hash = result[0]

            if not verify_password(old_password, current_hash):
                return False, "Current password is incorrect"

            if len(new_password) < 8:
                return False, "New password must be at least 8 characters"

            new_hash = hash_password(new_password)

            cursor.execute("""
                UPDATE rfp_users
                SET password_hash = %s, must_change_password = false
                WHERE user_id = %s
            """, (new_hash, user_id))
            conn.commit()

            return True, "Password changed successfully"

def init_session_state():
    """Initialize authentication session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'show_change_password' not in st.session_state:
        st.session_state.show_change_password = False

def logout():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.show_change_password = False

def render_login_page():
    """Render the login page"""
    st.title("🔐 Granetic")
    st.subheader("Please log in to continue")

    with st.form("login_form"):
        st.markdown('<p style="color: white;">Username</p>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="e.g., paul.wallis", label_visibility="collapsed")
        st.markdown('<p style="color: white;">Password</p>', unsafe_allow_html=True)
        password = st.text_input("Password", type="password", label_visibility="collapsed")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                user = login(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user

                    if user['must_change_password']:
                        st.session_state.show_change_password = True
                        st.warning("⚠️ You must change your password before continuing")

                    st.rerun()
                else:
                    st.error("Invalid username or password")

def render_change_password_dialog():
    """Render password change dialog"""
    st.subheader("🔑 Change Password")

    if st.session_state.user.get('must_change_password'):
        st.warning("⚠️ You must change your password before continuing")

    with st.form("change_password_form"):
        st.markdown('<p style="color: white;">Current Password</p>', unsafe_allow_html=True)
        old_password = st.text_input("Current Password", type="password", label_visibility="collapsed")
        st.markdown('<p style="color: white;">New Password</p>', unsafe_allow_html=True)
        new_password = st.text_input("New Password", type="password", label_visibility="collapsed")
        st.markdown('<p style="color: white;">Confirm New Password</p>', unsafe_allow_html=True)
        confirm_password = st.text_input("Confirm New Password", type="password", label_visibility="collapsed")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Change Password", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if cancel:
            if not st.session_state.user.get('must_change_password'):
                st.session_state.show_change_password = False
                st.rerun()

        if submit:
            if not old_password or not new_password or not confirm_password:
                st.error("Please fill in all fields")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            else:
                success, message = change_password(
                    st.session_state.user['user_id'],
                    old_password,
                    new_password
                )

                if success:
                    st.success(message)
                    st.session_state.user['must_change_password'] = False
                    st.session_state.show_change_password = False
                    st.rerun()
                else:
                    st.error(message)

def require_auth():
    """
    Decorator/check to require authentication
    Call this at the start of your app
    Returns True if authenticated, False otherwise
    """
    init_session_state()

    if not st.session_state.authenticated:
        render_login_page()
        return False

    if st.session_state.show_change_password:
        render_change_password_dialog()
        return False

    return True
