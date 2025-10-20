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


def render_client_brief_sidebar(username):
    """Sidebar for Client Brief page - shows search and brief list for quick navigation"""
    from agent.database.db_manager import DatabaseManager

    st.markdown("### 📋 Client Briefs")

    # Search input
    search_client = st.text_input(
        "🔍 Filter by client name",
        placeholder="Enter client name...",
        value=st.session_state.get('brief_search', ''),
        key="sidebar_brief_search"
    )

    # Store in session state
    st.session_state.brief_search = search_client

    # Set default limit (not exposed in UI)
    if 'brief_limit' not in st.session_state:
        st.session_state.brief_limit = 50

    st.divider()

    # Fetch and display briefs
    db = DatabaseManager()
    limit = st.session_state.brief_limit

    if search_client:
        briefs = db.list_client_briefs(client_name=search_client, limit=limit)
    else:
        briefs = db.list_client_briefs(limit=limit)

    if briefs:
        for brief in briefs:
            brief_id = brief.get('id')
            client_name = brief.get('client_name', 'Unknown')
            created_date = brief.get('created_date')

            # Format date for caption
            try:
                from datetime import timezone, timedelta
                uae_tz = timezone(timedelta(hours=4))
                if created_date.tzinfo is None:
                    created_date = created_date.replace(tzinfo=timezone.utc)
                uae_date = created_date.astimezone(uae_tz)
                date_str = uae_date.strftime("%b %d, %Y at %H:%M")
            except:
                date_str = str(created_date)[:10] if created_date else "N/A"

            # Create button with truncated name (single line)
            button_label = client_name[:30] + "..." if len(client_name) > 30 else client_name
            if st.button(
                f"📋 {button_label}",
                key=f"brief_{brief_id}",
                use_container_width=True,
                help=client_name
            ):
                st.session_state.selected_brief_id = brief_id
                st.rerun()

            # Show date/time as caption below button
            st.caption(f"Created: {date_str}")
    else:
        st.info("No client briefs found. Ask the agent to generate one.")


def render_presentations_sidebar(username):
    """Sidebar for Presentations page - shows search and presentation list for quick navigation"""
    from agent.database.db_manager import DatabaseManager

    st.markdown("### 📊 Presentations")

    # Search input
    search_title = st.text_input(
        "🔍 Filter by title",
        placeholder="Enter presentation title...",
        value=st.session_state.get('pres_search', ''),
        key="sidebar_pres_search"
    )

    # Store in session state
    st.session_state.pres_search = search_title

    # Set default limit (not exposed in UI)
    if 'pres_limit' not in st.session_state:
        st.session_state.pres_limit = 50

    st.divider()

    # Fetch and display presentations
    db = DatabaseManager()
    limit = st.session_state.pres_limit

    presentations = db.list_presentations(limit=limit)

    # Filter presentations if search is active
    if search_title:
        presentations = [p for p in presentations if search_title.lower() in p.get('presentation_title', '').lower()]

    if presentations:
        for pres in presentations:
            pres_id = pres.get('id')
            title = pres.get('presentation_title', 'Untitled')
            slide_count = pres.get('slide_count', 0)
            updated_at = pres.get('updated_at')

            # Format date for caption
            try:
                from datetime import timezone, timedelta
                uae_tz = timezone(timedelta(hours=4))
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                uae_date = updated_at.astimezone(uae_tz)
                date_str = uae_date.strftime("%b %d, %Y at %H:%M")
            except:
                date_str = str(updated_at)[:10] if updated_at else "N/A"

            # Create button with truncated name (single line)
            button_label = title[:30] + "..." if len(title) > 30 else title
            if st.button(
                f"📊 {button_label}",
                key=f"pres_{pres_id}",
                use_container_width=True,
                help=title
            ):
                st.session_state.selected_presentation_id = pres_id
                st.rerun()

            # Show date and slide count as caption below button
            st.caption(f"📄 {slide_count} slides • {date_str}")
    else:
        st.info("No presentations found. Ask the agent to create one.")


def render_sidebar(page_context="default"):
    """Render sidebar based on page context

    Args:
        page_context: "agent", "dashboard", "client_brief", "download", "help"
    """
    with st.sidebar:
        st.title("⚙️ Granite")

        username = render_user_section()

        st.divider()

        # Show different content based on page context
        if page_context == "dashboard":
            # Dashboard: Show RFP quick nav
            render_dashboard_sidebar(username)
            st.divider()
            render_user_actions()
            return None

        elif page_context == "client_brief":
            # Client Brief: Show search and filter
            render_client_brief_sidebar(username)
            st.divider()
            render_user_actions()
            return None

        elif page_context == "presentations":
            # Presentations: Show search and filter
            render_presentations_sidebar(username)
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
