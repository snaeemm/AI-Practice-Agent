import streamlit as st
from agent.session_wrapper import create_session, load_session, list_sessions


def render_user_section():
    if 'username' not in st.session_state:
        st.session_state.username = "default_user"

    username = st.text_input(
        "👤 Username",
        value=st.session_state.username,
        key="username_input",
        help="Your unique username for session management"
    )
    st.session_state.username = username
    return username


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


def render_sidebar():
    with st.sidebar:
        st.title("🎯 Bid Assistant")


        username = render_user_section()

        st.divider()

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

                return session
            except Exception as e:
                st.error(f"❌ Error loading session: {e}")
                del st.session_state.session_id
                st.rerun()
