import streamlit as st
from agent.session_wrapper import create_session, load_session, list_sessions


def render_user_section():
    if 'user' in st.session_state and st.session_state.user:
        user = st.session_state.user
        st.markdown(f"### 👤 {user.get('full_name', user['username'])}")
        st.caption(f"@{user['username']}")
        return user['username']
    return None


def render_user_actions():
    if 'user' in st.session_state and st.session_state.user:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Change Password", use_container_width=True):
                st.session_state.show_change_password = True
                st.rerun()
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                from auth import logout
                logout()
                st.rerun()


def render_session_selector(username, sessions):
    if not sessions:
        st.info("No existing sessions. Create one below.")
        return None

    session_options = {
        f"{s['session_name']} ({s['session_id'][:8]})": s['session_id']
        for s in sessions
    }

    selected_label = st.selectbox(
        "📂 Select Session",
        options=list(session_options.keys()),
        key="session_selector",
        help="Choose from your existing sessions"
    )

    if selected_label:
        selected_session_id = session_options[selected_label]
        if 'session_id' not in st.session_state or st.session_state.session_id != selected_session_id:
            st.session_state.session_id = selected_session_id
            if 'session_object' in st.session_state:
                del st.session_state.session_object
            st.rerun()
        return selected_session_id
    return None


def render_new_session_form(username):
    with st.expander("➕ Create New Session", expanded=False):
        with st.form(key="create_session_form", clear_on_submit=True):
            new_session_name = st.text_input(
                "Session name",
                placeholder="e.g., KHDA RFP",
                help="Give your session a descriptive name"
            )

            submitted = st.form_submit_button("Create Session", use_container_width=True, type="primary")

            if submitted:
                if new_session_name:
                    session = create_session(username, new_session_name)
                    st.session_state.session_id = session.session_id
                    st.session_state.session_object = session
                    st.success(f"✅ Created: {new_session_name}")
                    st.rerun()
                else:
                    st.error("⚠️ Please enter a session name")


def render_session_info(session):
    with st.expander("📋 Session Info", expanded=True):
        st.caption(f"**ID:** `{st.session_state.session_id}`") 


        active_rfp = session.get_active_rfp()
        if active_rfp:
            st.success(f"📄 **Active RFP:** {active_rfp}")
        else:
            st.info("No active RFP")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔒 Close", use_container_width=True, help="Close session (data preserved)"):
                session.close()
                del st.session_state.session_id
                del st.session_state.session_object
                st.rerun()
        with col2:
            if st.button("🗑️ Delete", use_container_width=True, help="Permanently delete session"):
                session.delete()
                del st.session_state.session_id
                del st.session_state.session_object
                st.rerun()


def render_dashboard_sidebar(username):
    """Sidebar for RFP Dashboard - shows RFP list for quick navigation"""
    from agent.database.db_manager import DatabaseManager

    st.markdown("### 📊 Quick Navigation")

    db = DatabaseManager()
    rfps = db.list_recent_rfps(limit=20)

    if rfps:
        for rfp in rfps:
            rfp_id = rfp.get('rfp_id')
            project_title = rfp.get('project_title', 'No Title')

            # Create compact button with truncated title
            button_label = project_title[:30] + "..." if len(project_title) > 30 else project_title
            if st.button(button_label, key=f"nav_{rfp_id}", use_container_width=True, help=project_title):
                st.session_state.selected_rfp = rfp_id
                st.rerun()
    else:
        st.info("No RFPs found")


def render_sidebar(page_context="default"):
    """Render sidebar based on page context

    Args:
        page_context: "agent", "dashboard", "download", "help"
    """
    with st.sidebar:
        st.title("🎯 Bid Assistant")

        username = render_user_section()

        st.divider()

        # Show different content based on page context
        if page_context == "dashboard":
            # Dashboard: Show RFP quick nav
            render_dashboard_sidebar(username)
            st.divider()
            render_user_actions()
            return None

        elif page_context in ["download", "help"]:
            # Minimal sidebar: just user actions
            render_user_actions()
            return None

        else:
            # Agent page: Full session management
            sessions = list_sessions(username)

            render_session_selector(username, sessions)

            st.divider()

            render_new_session_form(username)

            if 'session_id' not in st.session_state:
                session = create_session(username, f"Session {len(sessions) + 1}")
                st.session_state.session_id = session.session_id
                st.session_state.session_object = session
                return session
            else:
                try:
                    if 'session_object' not in st.session_state:
                        session = load_session(st.session_state.session_id)
                        st.session_state.session_object = session
                    else:
                        session = st.session_state.session_object

                    st.divider()

                    render_session_info(session)

                    st.divider()

                    render_user_actions()

                    return session
                except Exception as e:
                    st.error(f"❌ Error loading session: {e}")
                    del st.session_state.session_id
                    st.rerun()
