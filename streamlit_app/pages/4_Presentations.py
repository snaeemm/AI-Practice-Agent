
import streamlit as st
from components.sidebar import render_sidebar
from components.branding import render_page_header_logo
from components.slide_viewer import render_slide_viewer
from agent.database.db_manager import DatabaseManager
from styles import apply_custom_styles
from auth import require_auth

st.set_page_config(
    page_title="Presentations - Granite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()

if not require_auth():
    st.stop()

render_sidebar("presentations")

render_page_header_logo()
st.title("📊 Presentations")
st.markdown("Create, view, and edit structured presentations for Gamma.app")
st.markdown("---")

db = DatabaseManager()

# Initialize session state for presentation selection
if 'selected_presentation_id' not in st.session_state:
    st.session_state.selected_presentation_id = None
if 'edit_mode_presentation' not in st.session_state:
    st.session_state.edit_mode_presentation = False

# Back button at top (always visible)
if st.session_state.selected_presentation_id:
    col_back, col_space = st.columns([1, 10])
    with col_back:
        if st.button("🔙 Back to Presentations", use_container_width=True, key="back_to_presentations"):
            st.session_state.selected_presentation_id = None
            st.session_state.edit_mode_presentation = False
            st.rerun()
    st.markdown("---")

# Get all presentations
presentations = db.list_presentations(limit=50)

# View selected presentation or dashboard
if not st.session_state.selected_presentation_id:
    if not presentations:
        st.info("📭 No presentations found. Ask the agent to create one!")
    else:
        st.markdown(f"## 📊 Select a Presentation ({len(presentations)})")

        # Display presentations as cards
        for pres in presentations:
            pres_id = pres.get('id')
            title = pres.get('presentation_title', 'Untitled')
            description = pres.get('presentation_description')
            slide_count = pres.get('slide_count', 0)
            updated_at = pres.get('updated_at')

            # Format date
            if updated_at:
                try:
                    from datetime import timezone, timedelta
                    uae_tz = timezone(timedelta(hours=4))
                    if updated_at.tzinfo is None:
                        updated_at = updated_at.replace(tzinfo=timezone.utc)
                    uae_date = updated_at.astimezone(uae_tz)
                    date_str = uae_date.strftime("%b %d, %Y at %H:%M")
                except:
                    date_str = str(updated_at)
            else:
                date_str = "Unknown date"

            # Create card
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"#### 📊 {title}")
                    st.caption(f"📅 Updated: {date_str} | 📄 {slide_count} slides")
                    if description:
                        st.caption(f"📝 {description}")

                with col2:
                    if st.button("View Details →", key=f"view_{pres_id}", use_container_width=True):
                        st.session_state.selected_presentation_id = pres_id
                        st.rerun()

                st.markdown("---")
else:
    pres_id = st.session_state.selected_presentation_id

    # Fetch the presentation details
    presentations = db.list_presentations(limit=100)
    selected_pres = next((p for p in presentations if p['id'] == pres_id), None)

    if not selected_pres:
        st.error(f"Presentation {pres_id} not found")
    else:
        pres_id = selected_pres['id']
        title = selected_pres['presentation_title']
        description = selected_pres['presentation_description']
        structure = selected_pres['presentation_structure']
        slides = structure.get('slides', [])
        slide_count = len(slides)
        updated_at = selected_pres['updated_at']

        if updated_at:
            try:
                from datetime import timezone, timedelta
                uae_tz = timezone(timedelta(hours=4))
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                uae_date = updated_at.astimezone(uae_tz)
                date_str = uae_date.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = str(updated_at)
        else:
            date_str = "N/A"

        st.markdown(f"## {title}")
        st.markdown(f"**Updated:** {date_str} | **Slides:** {slide_count}")
        if description:
            st.info(f"📝 {description}")

        st.markdown("---")

        # Tabbed interface for Preview and Raw Content
        tab_preview, tab_raw = st.tabs(["✨ Preview", "📝 Raw Content"])

        with tab_preview:
            st.subheader("📊 Slide Preview")
            render_slide_viewer(slides)

        with tab_raw:
            st.subheader("📄 Slide Content")
            # Display slides with better formatting
            for idx, slide in enumerate(slides):
                with st.container(border=True):
                    slide_title = slide.get('title', f'Slide {idx + 1}')
                    points = slide.get('points', [])

                    st.write(f"**Slide {idx + 1}: {slide_title}**")

                    if points:
                        for point in points:
                            st.write(f"• {point}")
                    else:
                        st.caption("(No bullet points)")

        st.markdown("---")

        # Action buttons
        col_download, col_delete = st.columns(2)

        with col_download:
            if st.button("⬇️ Download .pptx", key=f"download_ppt_{pres_id}", use_container_width=True):
                with st.spinner("Generating presentation..."):
                    # Generate from saved structure
                    from agent.ppt_agent.ppt_tools import _create_presentation_bytes
                    ppt_bytes = _create_presentation_bytes(slides)
                    if ppt_bytes:
                        st.download_button(
                            "📥 Click to Download",
                            data=ppt_bytes,
                            file_name=f"{title.replace(' ', '_')}.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            key=f"dl_btn_ppt_{pres_id}",
                            use_container_width=True
                        )
                    else:
                        st.error("Failed to generate presentation")

        with col_delete:
            if st.button("🗑️ Delete", key=f"delete_ppt_{pres_id}", use_container_width=True):
                st.warning(f"Are you sure you want to delete '{title}'?")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("✅ Yes, Delete", key=f"confirm_delete_{pres_id}"):
                        db.delete_presentation(pres_id)
                        st.success(f"✅ Presentation deleted successfully!")
                        st.session_state.selected_presentation_id = None
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key=f"cancel_delete_{pres_id}"):
                        st.rerun()
