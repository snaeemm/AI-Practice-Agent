import streamlit as st
from auth import require_auth
from styles import apply_custom_styles
from components.sidebar import render_sidebar
from components.branding import render_page_header_logo
from components.marketing_onboarding import render_onboarding_wizard
from components.profile_selector import render_profile_selector, render_profile_editor, render_profile_stats
from components.social_previews import render_social_preview
from components.calendar_manager import render_calendar_week_view, render_calendar_summary, render_calendar_legend
from components.calendar_entry_editor import render_calendar_entry_editor
from components.post_preview_card import render_post_grid, render_post_filters, filter_and_sort_posts
from PIL import Image
import io
import time
from datetime import datetime, timedelta
import zipfile

# Database imports
from agent.database.db_manager import DatabaseManager
from agent.database.marketing_profile_manager import MarketingProfileManager
from agent.social_media_post_generator import SocialMediaPostGenerator
from agent.config.settings import settings

st.set_page_config(page_title="Marketing - Granite", page_icon="📱", layout="wide")

apply_custom_styles()

# Additional CSS override for this page to fix text visibility
st.markdown("""
<style>
/* Force all radio button text to be white */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label span,
[data-testid="stRadio"] label div,
[data-testid="stRadio"] label p,
[data-testid="stRadio"] * {
    color: #ffffff !important;
}

/* All text elements white */
.main label {
    color: #ffffff !important;
}

.main [data-testid="stMarkdownContainer"] {
    color: #ffffff !important;
}

.main [data-testid="stMarkdownContainer"] * {
    color: #ffffff !important;
}

.main [data-testid="stText"] {
    color: #ffffff !important;
}

.main .stMarkdown {
    color: #ffffff !important;
}

.main .stMarkdown p,
.main .stMarkdown span,
.main .stMarkdown div {
    color: #ffffff !important;
}

/* File uploader label */
div[data-testid="stFileUploader"] label {
    color: #ffffff !important;
}

/* Checkbox labels */
div[data-testid="stCheckbox"] label {
    color: #ffffff !important;
}

div[data-testid="stCheckbox"] label span {
    color: #ffffff !important;
}

div[data-testid="stCheckbox"] label div {
    color: #ffffff !important;
}

div[data-testid="stCheckbox"] label p {
    color: #ffffff !important;
}

div[data-testid="stCheckbox"] * {
    color: #ffffff !important;
}

/* Text area labels */
div[data-testid="stTextArea"] label {
    color: #ffffff !important;
}

/* Text input labels */
div[data-testid="stTextInput"] label {
    color: #ffffff !important;
}

/* Selectbox labels */
div[data-testid="stSelectbox"] label {
    color: #ffffff !important;
}

/* Number input labels */
div[data-testid="stNumberInput"] label {
    color: #ffffff !important;
}

/* Caption text */
.main [data-testid="stCaption"] {
    color: #cccccc !important;
}

/* Expander headers */
[data-testid="stExpander"] summary {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# Authentication
user_info = require_auth()
if not user_info:
    st.stop()

# Get user info from session
user_id = st.session_state.user.get('user_id') if st.session_state.user else None
user_name = st.session_state.user.get('full_name', 'User') if st.session_state.user else 'User'

# Validate user_id
if not user_id:
    st.error("❌ Authentication Error: No user ID found in session. Please log in again.")
    st.info("💡 **Solution:** Return to the home page and log in again to continue.")
    st.stop()

render_page_header_logo(max_width=300)
render_sidebar("marketing")

# Initialize database managers
@st.cache_resource
def get_db_manager():
    return DatabaseManager()

@st.cache_resource(ttl=None, show_spinner=False)
def get_marketing_manager(_db_manager):
    """Create marketing manager - underscore prefix prevents hashing"""
    return MarketingProfileManager(_db_manager)

db_manager = get_db_manager()
marketing_mgr = get_marketing_manager(db_manager)

# Initialize session state
if 'show_onboarding' not in st.session_state:
    st.session_state.show_onboarding = False

if 'show_profile_editor' not in st.session_state:
    st.session_state.show_profile_editor = False

if 'current_profile_id' not in st.session_state:
    default_profile = marketing_mgr.get_default_profile(user_id)
    if default_profile:
        st.session_state.current_profile_id = default_profile['profile_id']
    else:
        st.session_state.current_profile_id = None

if 'generated_post' not in st.session_state:
    st.session_state.generated_post = None

if 'selected_platform' not in st.session_state:
    st.session_state.selected_platform = 'linkedin'

if 'prefilled_topic' not in st.session_state:
    st.session_state.prefilled_topic = ''

if 'calendar_week_offset' not in st.session_state:
    st.session_state.calendar_week_offset = 0

if 'show_calendar_editor' not in st.session_state:
    st.session_state.show_calendar_editor = False

if 'editing_calendar_entry' not in st.session_state:
    st.session_state.editing_calendar_entry = None

if 'calendar_default_date' not in st.session_state:
    st.session_state.calendar_default_date = None

# ==================== MAIN APP LOGIC ====================

# Check if user needs onboarding
profiles = marketing_mgr.get_user_profiles(user_id)

# Show onboarding wizard if requested or no profiles exist
if st.session_state.show_onboarding or (len(profiles) == 0 and not st.session_state.get('onboarding_dismissed')):
    new_profile_id = render_onboarding_wizard(db_manager, user_id, user_name)

    if new_profile_id:
        st.session_state.current_profile_id = new_profile_id
        st.session_state.show_onboarding = False
        st.success("🎉 Profile created! You can now generate social media posts.")
        time.sleep(2)
        st.rerun()

    # Dismiss button for users who want to skip
    if len(profiles) == 0:
        st.divider()
        if st.button("I'll set this up later"):
            st.session_state.onboarding_dismissed = True
            st.rerun()

    st.stop()

# Show profile editor if requested
if st.session_state.show_profile_editor and st.session_state.get('editing_profile_id'):
    render_profile_editor(marketing_mgr, st.session_state.editing_profile_id)
    st.stop()

# ==================== HEADER ====================

st.markdown("# 📱 Social Media Post Generator")
st.markdown("### AI-Powered Content for LinkedIn & Instagram")

st.divider()

# Profile selector
selected_profile_id = render_profile_selector(marketing_mgr, user_id, st.session_state.current_profile_id)

if selected_profile_id:
    st.session_state.current_profile_id = selected_profile_id

    # Load profile data
    current_profile = marketing_mgr.get_profile(selected_profile_id)

    if not current_profile:
        st.error("Failed to load profile")
        st.stop()

    st.divider()

    # ==================== STRATEGY BANNER (Optional) ====================

    # Show content themes if available
    if current_profile.get('content_themes'):
        themes_text = ', '.join(current_profile['content_themes'][:3])
        st.info(f"📊 **Content Themes:** {themes_text}")

    # ==================== MAIN 2-COLUMN LAYOUT ====================

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 🎯 Create Post")

        # Platform Selector
        st.markdown("#### Choose Platform")

        platform_col1, platform_col2 = st.columns(2)

        with platform_col1:
            linkedin_type = "primary" if st.session_state.selected_platform == 'linkedin' else "secondary"
            if st.button("💼 LinkedIn\n\nProfessional networking", key="btn_linkedin", use_container_width=True, type=linkedin_type):
                st.session_state.selected_platform = 'linkedin'
                st.rerun()

        with platform_col2:
            instagram_type = "primary" if st.session_state.selected_platform == 'instagram' else "secondary"
            if st.button("📸 Instagram\n\nVisual storytelling", key="btn_instagram", use_container_width=True, type=instagram_type):
                st.session_state.selected_platform = 'instagram'
                st.rerun()

        selected_platform = st.session_state.selected_platform
        platform_emoji = "💼" if selected_platform == "linkedin" else "📸"
        platform_name = selected_platform.title()

        st.markdown("---")

        # Topic Input with Smart Suggestions
        st.markdown("#### What do you want to post about?")

        # Show theme-based suggestions
        if current_profile.get('content_themes'):
            with st.expander("💡 Suggested Topics (click to use)"):
                for theme in current_profile['content_themes'][:3]:
                    if st.button(f"📌 {theme}", key=f"suggest_{theme}", use_container_width=True):
                        st.session_state.prefilled_topic = f"Share insights about {theme}"
                        st.rerun()

        topic = st.text_area(
            "Describe your topic or goal",
            value=st.session_state.prefilled_topic,
            placeholder=f"Example: Announce our AI product launch, share insights on remote work trends, celebrate a team milestone",
            height=120,
            help="Be specific! The more context you provide, the better the post will be.",
            key="topic_input"
        )

        # Clear prefill after use
        if st.session_state.prefilled_topic and topic:
            st.session_state.prefilled_topic = ''

        # Platform-specific tips
        platform_tips = {
            'linkedin': "💡 **LinkedIn tip:** Professional tone, data-driven insights, engagement questions work best",
            'instagram': "💡 **Instagram tip:** Visual storytelling, authentic voice, emojis, action CTAs"
        }
        st.caption(platform_tips[selected_platform])

        st.markdown("---")

        # Post Type Selection
        st.markdown("#### Post Type (Optional)")

        post_types = {
            "Let AI Decide": None,
            "📢 Announcement": "announcement",
            "💡 Thought Leadership": "thought_leadership",
            "✅ Tips & Advice": "tips",
            "🏢 Company Culture": "company_culture",
            "📖 Personal Story": "personal_story"
        }

        selected_post_type = st.radio(
            "Post type",
            options=list(post_types.keys()),
            horizontal=False,
            label_visibility="collapsed"
        )

        post_type = post_types[selected_post_type]

        st.markdown("---")

        # Reference Images Upload
        st.markdown("#### Reference Images (Optional)")
        st.caption("Upload images to guide the AI's image generation style")

        uploaded_files = st.file_uploader(
            "Choose reference images",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True,
            help="Upload 1-5 reference images to guide style",
            label_visibility="collapsed",
            key="ref_images"
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} image(s) uploaded**")
            cols = st.columns(min(len(uploaded_files), 5))
            for idx, uploaded_file in enumerate(uploaded_files[:5]):
                with cols[idx % 5]:
                    img = Image.open(uploaded_file)
                    st.image(img, use_container_width=True)

        st.markdown("---")

        # Generate Button
        col_gen1, col_gen2 = st.columns([2, 1])

        with col_gen1:
            generate_btn = st.button(
                f"🎨 Generate {platform_name} Post",
                use_container_width=True,
                type="primary"
            )

        with col_gen2:
            include_image = st.checkbox("Include Image", value=True)

        if generate_btn:
            if not topic or len(topic.strip()) < 10:
                st.error("⚠️ Please provide more detail about your topic (at least 10 characters)")
            else:
                start_time = time.time()

                # Process reference images
                reference_images = []
                if uploaded_files and include_image:
                    for uploaded_file in uploaded_files[:5]:
                        img = Image.open(uploaded_file)
                        reference_images.append(img)

                with st.spinner(f"🎯 Generating your {platform_name} post... This may take 20-30 seconds..."):
                    try:
                        generator = SocialMediaPostGenerator()

                        result = generator.generate_complete_post(
                            topic=topic.strip(),
                            platform=selected_platform,
                            post_type=post_type,
                            profile=current_profile,
                            generate_image=include_image,
                            reference_images=reference_images if reference_images else None
                        )

                        elapsed_time = time.time() - start_time

                        if result['success']:
                            st.success(f"✅ Post generated in {elapsed_time:.1f} seconds!")

                            # Store in session state
                            st.session_state.generated_post = result

                            # Save to database
                            try:
                                post_id = marketing_mgr.save_generated_post(
                                    user_id=user_id,
                                    profile_id=selected_profile_id,
                                    post_topic=topic,
                                    generated_text=result['post_text'],
                                    image_bytes=result.get('image_bytes'),
                                    image_prompt=result.get('image_prompt'),
                                    hashtags=result.get('hashtags'),
                                    post_type=result.get('post_type_detected'),
                                    tone_used=current_profile.get('default_tone'),
                                    image_style_used=current_profile.get('image_style_preference'),
                                    gemini_reasoning=result.get('reasoning'),
                                    platform=selected_platform
                                )

                                st.session_state.generated_post['post_id'] = post_id

                            except Exception as e:
                                st.warning(f"Post generated but failed to save to database: {e}")

                            st.rerun()
                        else:
                            st.error(f"❌ Failed to generate post")
                            st.error(f"**Error:** {result.get('error', 'Unknown error')}")

                            # Show helpful error info
                            error_msg = result.get('error', '').lower()
                            if "quota" in error_msg:
                                st.info("💡 **Solution:** Free tier limit reached. Try again later or upgrade to paid tier.")
                            elif "api key" in error_msg:
                                st.info("💡 **Solution:** Check your GOOGLE_API_KEY in the .env file.")

                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")
                        import traceback
                        st.code(traceback.format_exc())

    # ==================== RIGHT COLUMN: PREVIEW + ACTIONS ====================

    with col_right:
        st.markdown("### 📸 Preview")

        if st.session_state.generated_post:
            post_data = st.session_state.generated_post
            post_platform = post_data.get('platform', 'linkedin')

            # Platform-specific preview
            user_role = current_profile.get('role_title') or current_profile.get('industry')

            render_social_preview(
                platform=post_platform,
                post_text=post_data.get('post_text', ''),
                user_name=user_name,
                user_role=user_role,
                image_bytes=post_data.get('image_bytes'),
                hashtags=post_data.get('hashtags', [])
            )

            st.markdown("---")

            # Gemini's Reasoning
            if post_data.get('reasoning'):
                with st.expander("🧠 Why this approach?"):
                    st.markdown(post_data['reasoning'])

            # Action Buttons
            st.markdown("### Actions")

            col_action1, col_action2 = st.columns(2)

            with col_action1:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.generated_post = None
                    st.rerun()

            with col_action2:
                if st.button("⭐ Mark Posted", use_container_width=True):
                    if post_data.get('post_id'):
                        marketing_mgr.update_post_feedback(
                            post_id=post_data['post_id'],
                            was_posted=True
                        )
                        st.success("✅ Marked as posted!")

            # Download Options
            st.markdown("---")
            st.markdown("**Download**")

            # Download image
            if post_data.get('image_bytes'):
                image_data = post_data['image_bytes']
                if isinstance(image_data, memoryview):
                    image_data = bytes(image_data)

                st.download_button(
                    label="📥 Download Image",
                    data=image_data,
                    file_name=f"{post_platform}_post_{int(time.time())}.png",
                    mime="image/png",
                    use_container_width=True
                )

            # Download text
            if post_data.get('post_text'):
                post_text_with_hashtags = post_data['post_text']
                if post_data.get('hashtags'):
                    post_text_with_hashtags += "\n\n" + " ".join([f"#{tag.lstrip('#')}" for tag in post_data['hashtags']])

                st.download_button(
                    label="📄 Download Text",
                    data=post_text_with_hashtags,
                    file_name=f"{post_platform}_post_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            # Download complete package as ZIP
            if post_data.get('image_bytes') and post_data.get('post_text'):
                zip_buffer = io.BytesIO()

                image_data = post_data['image_bytes']
                if isinstance(image_data, memoryview):
                    image_data = bytes(image_data)

                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.writestr(f"{post_platform}_post_image.png", image_data)
                    zip_file.writestr(f"{post_platform}_post_text.txt", post_text_with_hashtags)

                    markdown_content = f"""# {post_platform.title()} Post

{post_text_with_hashtags}

---

**Generated by Granite Marketing AI**
- Profile: {current_profile['profile_name']}
- Platform: {post_platform.title()}
- Topic: {topic}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Image: See {post_platform}_post_image.png
"""
                    zip_file.writestr(f"README.md", markdown_content)

                zip_buffer.seek(0)

                st.download_button(
                    label="📦 Download Package (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{post_platform}_post_package_{int(time.time())}.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        else:
            st.info("👈 Generate a post to see the preview here")

    # ==================== WEEKLY CONTENT CALENDAR ====================

    st.divider()

    st.markdown("### 📅 Content Calendar")

    # Show calendar editor modal if active
    if st.session_state.show_calendar_editor:
        with st.container():
            st.markdown("---")
            render_calendar_entry_editor(
                marketing_mgr=marketing_mgr,
                user_id=user_id,
                profile_id=selected_profile_id,
                entry=st.session_state.editing_calendar_entry,
                default_date=st.session_state.calendar_default_date
            )
            st.markdown("---")

            if st.button("✖️ Close Editor"):
                st.session_state.show_calendar_editor = False
                st.session_state.editing_calendar_entry = None
                st.session_state.calendar_default_date = None
                st.rerun()
    else:
        # Get calendar data
        week_offset = st.session_state.get('calendar_week_offset', 0)

        # Calculate date range for current week view
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        start_of_week = start_of_week + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=6)  # Sunday

        # Fetch calendar entries from database
        calendar_entries = marketing_mgr.get_profile_calendar(
            profile_id=selected_profile_id,
            start_date=start_of_week,
            end_date=end_of_week
        )

        # Callbacks for calendar interactions
        def handle_add_entry(date: datetime):
            st.session_state.show_calendar_editor = True
            st.session_state.editing_calendar_entry = None
            st.session_state.calendar_default_date = date
            st.rerun()

        def handle_edit_entry(entry: dict):
            st.session_state.show_calendar_editor = True
            st.session_state.editing_calendar_entry = entry
            st.session_state.calendar_default_date = None
            st.rerun()

        # Render calendar legend
        render_calendar_legend()

        # Render calendar
        render_calendar_week_view(
            calendar_entries=calendar_entries,
            profile_id=selected_profile_id,
            user_id=user_id,
            on_add_entry=handle_add_entry,
            on_edit_entry=handle_edit_entry,
            week_offset=week_offset
        )

        # Calendar summary stats
        if calendar_entries:
            st.markdown("---")
            render_calendar_summary(calendar_entries)

    # ==================== AI CALENDAR PLANNER ====================

    st.divider()

    with st.expander("🤖 AI Calendar Planner", expanded=False):
        st.markdown("""
        Let the marketing agent help you plan your content calendar based on your strategy,
        recent post performance, and content themes.
        """)

        col1, col2 = st.columns([2, 1])

        with col1:
            plan_duration = st.selectbox(
                "Planning horizon",
                options=["Next week (7 days)", "Next 2 weeks (14 days)", "Next month (30 days)"],
                index=0
            )

        with col2:
            posts_per_week = st.number_input(
                "Posts per week",
                min_value=1,
                max_value=7,
                value=3,
                help="Target number of posts per week"
            )

        if st.button("🎯 Generate Calendar Plan", use_container_width=True, type="primary"):
            st.info("""
            💡 **To use AI Calendar Planning:**

            The marketing agent can create a full content calendar for you! To use this feature:

            1. Go to the main chat interface (Home page)
            2. Ask the agent: *"Plan a content calendar for my [profile name] for the next [duration]"*
            3. The agent will analyze your strategy, recent performance, and create a calendar plan
            4. Once created, the calendar will appear here automatically!

            **Example prompts:**
            - "Plan a 2-week content calendar for my profile with 3 posts per week"
            - "Suggest topics for next week's LinkedIn posts"
            - "Create a content calendar focused on AI Innovation theme"
            """)

            st.markdown("""
            <div style="background: rgba(102, 179, 255, 0.1); padding: 16px; border-radius: 8px; border-left: 4px solid #66b3ff; margin-top: 16px;">
                <strong>🚀 Coming Soon:</strong> Direct AI calendar planning from this page!<br>
                For now, use the conversational interface on the Home page to access the marketing agent's calendar planning capabilities.
            </div>
            """, unsafe_allow_html=True)

    # ==================== POST HISTORY ====================

    st.divider()

    st.markdown("### 🕒 Recent Posts")

    # Load recent posts
    recent_posts = marketing_mgr.get_user_posts(user_id, profile_id=selected_profile_id, limit=50)

    if recent_posts:
        st.markdown(f"**{len(recent_posts)} post(s) generated**")

        # Render filters
        filters = render_post_filters(
            platforms=['linkedin', 'instagram'],
            post_types=list(set([p.get('post_type') for p in recent_posts if p.get('post_type')]))
        )

        # Apply filters
        filtered_posts = filter_and_sort_posts(recent_posts, filters)

        if filtered_posts:
            st.markdown(f"*Showing {len(filtered_posts)} of {len(recent_posts)} posts*")

            # Callbacks for post actions
            def handle_view_post(post: dict):
                st.session_state.generated_post = post
                st.session_state.selected_platform = post.get('platform', 'linkedin')
                st.rerun()

            def handle_repost(post: dict):
                # Pre-fill the topic input for regeneration
                st.session_state.prefilled_topic = post.get('post_topic', '')
                st.session_state.selected_platform = post.get('platform', 'linkedin')
                st.success("💡 Topic loaded! Scroll up to the post generator to create a new version.")
                # Scroll to top would require JS, so we just show a message

            def handle_add_to_calendar(post: dict):
                # Open calendar editor with this post's topic pre-filled
                st.session_state.show_calendar_editor = True
                st.session_state.calendar_default_date = datetime.now() + timedelta(days=1)
                st.session_state.editing_calendar_entry = None
                # Store post info for pre-filling
                st.session_state.calendar_prefill_topic = post.get('post_topic', '')
                st.session_state.calendar_prefill_post_id = post.get('post_id')
                st.rerun()

            # Render posts in 3-column grid
            render_post_grid(
                posts=filtered_posts,
                columns=3,
                on_view=handle_view_post,
                on_repost=handle_repost,
                on_add_to_calendar=handle_add_to_calendar
            )
        else:
            st.info("No posts match the current filters")
    else:
        st.info("No posts generated yet with this profile")

    # ==================== PROFILE STATS ====================

    st.divider()

    with st.expander("📊 Profile Statistics"):
        render_profile_stats(marketing_mgr, selected_profile_id)

else:
    st.warning("No profile selected. Please create a profile to get started.")

# ==================== HELP SECTION ====================

st.divider()

with st.expander("💡 Tips for Better Social Media Posts"):
    st.markdown("""
    ### Platform-Specific Best Practices

    #### LinkedIn 💼
    - **Hook**: First line grabs attention (visible in feed)
    - **Value**: Data-driven insights, industry expertise
    - **Length**: 150-300 words optimal
    - **CTA**: End with engagement question
    - **Hashtags**: 3-5 professional industry tags
    - **Tone**: Professional, thought-provoking, authoritative

    #### Instagram 📸
    - **Visual First**: Image is the star, text complements
    - **Authentic Voice**: Conversational, relatable storytelling
    - **Length**: 125-150 words, short paragraphs
    - **CTA**: Action-driven (DM, link in bio, save this)
    - **Hashtags**: 8-12 mix of trending + niche tags
    - **Tone**: Authentic, engaging, strategic emojis

    ### General Tips

    1. **Be Specific**: "Share our carbon neutrality journey" > "Post about environment"
    2. **Trust Your Profile**: Your brand voice and audience are already configured
    3. **Reference Images**: Upload style examples for consistent visuals
    4. **Optimize Images**: AI generates platform-specific visual prompts automatically

    ### Profile Tips

    - **Update your profile** when your focus changes
    - **Add example posts** to teach the AI your style
    - **Create multiple profiles** for different personas (personal + company)
    - **Set a default** for quick access

    ### Troubleshooting

    - **Generic output?** → Add more context to your topic
    - **Wrong tone?** → Check profile's default tone setting
    - **Image doesn't match?** → Upload reference images for style guidance
    - **API errors?** → Check GOOGLE_API_KEY and quota limits
    """)

# Footer
st.divider()
col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    st.markdown("**Powered by:** Google Gemini 2.5 Flash (Text + Image)")
    st.markdown("**Current Profile:** " + current_profile.get('profile_name', 'None') if selected_profile_id else "**No profile selected**")

with col_footer2:
    st.markdown("**Platforms:** LinkedIn, Instagram")
    st.markdown(f"**Profiles:** {len(profiles)}")
