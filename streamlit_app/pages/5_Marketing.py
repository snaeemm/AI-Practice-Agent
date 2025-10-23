import streamlit as st
from auth import require_auth
from styles import apply_custom_styles
from components.sidebar import render_sidebar
from components.branding import render_page_header_logo
from components.marketing_onboarding import render_onboarding_wizard
from components.profile_selector import render_profile_selector, render_profile_summary_card, render_profile_editor, render_profile_stats
from components.linkedin_preview import render_linkedin_preview, render_compact_post_card
from PIL import Image
import io
import time
from datetime import datetime
import zipfile

# Database imports
from agent.database.db_manager import DatabaseManager
from agent.database.marketing_profile_manager import MarketingProfileManager
from agent.linkedin_post_generator import LinkedInPostGenerator
from agent.config.settings import settings

st.set_page_config(page_title="Marketing - Granite", page_icon="📱", layout="wide")

apply_custom_styles()

# Additional CSS override for this page to fix text visibility and LinkedIn preview
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

/* CRITICAL: Fix LinkedIn preview - prevent slide styles */
div.linkedin-preview-wrapper {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: auto !important;
    height: auto !important;
    display: block !important;
    position: relative !important;
    animation: none !important;
    border: none !important;
    box-shadow: none !important;
}

div.linkedin-preview-wrapper div.linkedin-post {
    background: linear-gradient(135deg, #1a3a52 0%, #1a4d6d 100%) !important;
    animation: none !important;
    min-height: auto !important;
    height: auto !important;
}

div.linkedin-preview-wrapper div.linkedin-post * {
    background: transparent !important;
    animation: none !important;
}

div.linkedin-preview-wrapper div.linkedin-post div.linkedin-avatar {
    background: linear-gradient(135deg, #1A3A52 0%, #2E5266 100%) !important;
}

/* Ensure no slide classes leak into LinkedIn preview */
div.linkedin-preview-wrapper .slide-container,
div.linkedin-preview-wrapper .slide-inner,
div.linkedin-preview-wrapper .slide-watermark {
    display: none !important;
}

/* Ensure no white backgrounds in marketing page */
.main [data-testid="column"]:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    background: transparent !important;
}

.main [data-testid="stVerticalBlock"]:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    background: transparent !important;
}

.main [class*="element-container"]:not(.linkedin-preview-wrapper):not(.linkedin-preview-wrapper *) {
    background: transparent !important;
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

@st.cache_resource
def get_marketing_manager():
    db = get_db_manager()
    return MarketingProfileManager(db)

db_manager = get_db_manager()
marketing_mgr = get_marketing_manager()

# Initialize session state
if 'show_onboarding' not in st.session_state:
    st.session_state.show_onboarding = False

if 'show_profile_editor' not in st.session_state:
    st.session_state.show_profile_editor = False

if 'current_profile_id' not in st.session_state:
    # Try to load default profile
    default_profile = marketing_mgr.get_default_profile(user_id)
    if default_profile:
        st.session_state.current_profile_id = default_profile['profile_id']
    else:
        st.session_state.current_profile_id = None

if 'generated_post' not in st.session_state:
    st.session_state.generated_post = None

if 'post_history' not in st.session_state:
    st.session_state.post_history = []

# ==================== MAIN APP LOGIC ====================

# Check if user needs onboarding
profiles = marketing_mgr.get_user_profiles(user_id)

# Show onboarding wizard if requested or no profiles exist
if st.session_state.show_onboarding or (len(profiles) == 0 and not st.session_state.get('onboarding_dismissed')):
    new_profile_id = render_onboarding_wizard(db_manager, user_id, user_name)

    if new_profile_id:
        st.session_state.current_profile_id = new_profile_id
        st.session_state.show_onboarding = False
        st.success("🎉 Profile created! You can now generate LinkedIn posts.")
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

st.markdown("# 📱 LinkedIn Post Generator")
st.markdown("### AI-Powered Content Creation with Context")

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

    # ==================== MAIN LAYOUT ====================

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 🎯 Create LinkedIn Post")

        # Tab selection for mode
        mode_tab = st.radio(
            "Choose Mode",
            options=["Guided Workflow", "Advanced (Manual)"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if mode_tab == "Guided Workflow":
            # ========== GUIDED WORKFLOW ==========

            # Step 1: Topic
            st.markdown("#### Step 1: What do you want to post about?")

            topic = st.text_area(
                "Describe your topic or goal",
                placeholder="Example: Announce our new AI product launch, share insights on remote work trends, celebrate a team milestone",
                height=100,
                help="Be specific! The more context you provide, the better the post will be.",
                key="topic_input"
            )

            st.caption("💡 Examples: Product launches, hiring announcements, industry insights, thought leadership, tips & advice")

            st.markdown("---")

            # Step 2: Post Type
            st.markdown("#### Step 2: Choose Post Type (Optional)")

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

            # Step 2.5: Optional Reference Images
            st.markdown("#### Optional: Upload Reference Images")
            st.caption("Upload images to guide the AI's image generation style (optional)")

            uploaded_files = st.file_uploader(
                "Choose reference images",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=True,
                help="Upload 1-5 reference images to guide the style",
                label_visibility="collapsed",
                key="guided_mode_uploader"
            )

            if uploaded_files:
                st.markdown(f"**Uploaded: {len(uploaded_files)} image(s)**")
                cols = st.columns(min(len(uploaded_files), 5))
                for idx, uploaded_file in enumerate(uploaded_files[:5]):
                    with cols[idx % 5]:
                        img = Image.open(uploaded_file)
                        st.image(img, use_container_width=True)

            st.markdown("---")

            # Step 3: Generate
            st.markdown("#### Step 3: Generate Your Post")

            col_gen1, col_gen2 = st.columns([2, 1])

            with col_gen1:
                generate_btn = st.button(
                    "🎨 Generate LinkedIn Post",
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

                    # Process reference images if uploaded
                    reference_images = []
                    if uploaded_files and include_image:
                        for uploaded_file in uploaded_files[:5]:
                            img = Image.open(uploaded_file)
                            reference_images.append(img)

                    with st.spinner(f"🎯 Analyzing your profile and generating post... This may take 20-30 seconds..."):
                        try:
                            generator = LinkedInPostGenerator()

                            result = generator.generate_complete_post(
                                topic=topic.strip(),
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
                                        gemini_reasoning=result.get('reasoning')
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

        else:
            # ========== ADVANCED MODE (Original functionality) ==========

            st.markdown("#### Advanced Image Generation")
            st.caption("Direct control over image generation parameters")

            # Import old image generator
            from agent.image_generator import generate_image_from_prompt

            prompt = st.text_area(
                "📝 Image Description",
                placeholder="Example: A futuristic Dubai skyline at golden hour with modern glass buildings, photorealistic, high quality, professional photography",
                height=120,
                help="Describe what you want to see in the image. Be specific about style, mood, colors, and composition.",
                key="advanced_prompt"
            )

            # Reference images upload
            st.markdown("#### 📎 Reference Images (Optional)")
            uploaded_files = st.file_uploader(
                "Choose reference images",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=True,
                help="Upload 1-5 reference images",
                label_visibility="collapsed"
            )

            if uploaded_files:
                st.markdown(f"**Uploaded: {len(uploaded_files)} image(s)**")
                cols = st.columns(min(len(uploaded_files), 5))
                for idx, uploaded_file in enumerate(uploaded_files[:5]):
                    with cols[idx % 5]:
                        img = Image.open(uploaded_file)
                        st.image(img, use_container_width=True)

            st.markdown("---")

            col_settings1, col_settings2 = st.columns(2)

            with col_settings1:
                aspect_ratio = st.selectbox(
                    "📐 Aspect Ratio",
                    options=["1:1 (Square)", "16:9 (Landscape)", "9:16 (Portrait)"],
                    index=0
                )
                aspect_ratio = aspect_ratio.split(" ")[0]

            with col_settings2:
                num_variations = st.selectbox("🎲 Variations", options=[1, 2, 3, 4], index=0)

            with st.expander("⚙️ Advanced Options"):
                negative_prompt = st.text_input(
                    "🚫 Negative Prompt",
                    placeholder="Example: blurry, low quality, distorted",
                    help="What to avoid in the image"
                )

            st.markdown("---")

            generate_advanced_btn = st.button("🎨 Generate Image", use_container_width=True, type="primary")

            if generate_advanced_btn:
                if not prompt or len(prompt.strip()) < 5:
                    st.error("⚠️ Please enter a description (at least 5 characters)")
                else:
                    start_time = time.time()

                    reference_images = []
                    if uploaded_files:
                        for uploaded_file in uploaded_files[:5]:
                            img = Image.open(uploaded_file)
                            reference_images.append(img)

                    with st.spinner(f"🎨 Generating image... This may take 10-20 seconds..."):
                        result = generate_image_from_prompt(
                            prompt=prompt.strip(),
                            aspect_ratio=aspect_ratio,
                            number_of_images=num_variations,
                            reference_images=reference_images if reference_images else None,
                            negative_prompt=negative_prompt if negative_prompt else None
                        )

                    elapsed_time = time.time() - start_time

                    if result['success']:
                        st.success(f"✅ Image generated in {elapsed_time:.1f} seconds!")

                        # Store as simple generated post
                        st.session_state.generated_post = {
                            'success': True,
                            'post_text': '',
                            'image_bytes': result['image_bytes'],
                            'image_prompt': prompt,
                            'hashtags': [],
                            'reasoning': 'Generated via advanced mode'
                        }

                        st.rerun()
                    else:
                        st.error(f"❌ Failed to generate image: {result['error']}")

    # ==================== RIGHT COLUMN: PREVIEW ====================

    with col_right:
        st.markdown("### 📸 Preview")

        if st.session_state.generated_post:
            post_data = st.session_state.generated_post

            # LinkedIn Preview
            user_role = current_profile.get('role_title') or current_profile.get('industry')

            render_linkedin_preview(
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
                # Convert memoryview to bytes if needed
                image_data = post_data['image_bytes']
                if isinstance(image_data, memoryview):
                    image_data = bytes(image_data)

                st.download_button(
                    label="📥 Download Image",
                    data=image_data,
                    file_name=f"linkedin_post_{int(time.time())}.png",
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
                    file_name=f"linkedin_post_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            # Download complete package as ZIP
            if post_data.get('image_bytes') and post_data.get('post_text'):
                # Create ZIP in memory
                zip_buffer = io.BytesIO()

                # Convert memoryview to bytes if needed
                image_data = post_data['image_bytes']
                if isinstance(image_data, memoryview):
                    image_data = bytes(image_data)

                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add image
                    zip_file.writestr(f"linkedin_post_image.png", image_data)

                    # Add text
                    zip_file.writestr(f"linkedin_post_text.txt", post_text_with_hashtags)

                    # Add markdown with both
                    markdown_content = f"""# LinkedIn Post

{post_text_with_hashtags}

---

**Generated by Granite Marketing AI**
- Profile: {current_profile['profile_name']}
- Topic: {post_data.get('post_topic', 'N/A')}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Image: See linkedin_post_image.png
"""
                    zip_file.writestr(f"README.md", markdown_content)

                zip_buffer.seek(0)

                st.download_button(
                    label="📦 Download Package (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"linkedin_post_package_{int(time.time())}.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        else:
            st.info("👈 Generate a post to see the preview here")

    # ==================== POST HISTORY ====================

    st.divider()

    st.markdown("### 🕒 Recent Posts")

    # Load recent posts
    recent_posts = marketing_mgr.get_user_posts(user_id, profile_id=selected_profile_id, limit=20)

    if recent_posts:
        # Filter and display options
        col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])

        with col_filter1:
            st.markdown(f"**{len(recent_posts)} post(s) generated with this profile**")

        with col_filter2:
            show_posted_only = st.checkbox("Posted only", value=False)

        with col_filter3:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.warning("Clear all feature not implemented (database preservation)")

        # Filter
        if show_posted_only:
            recent_posts = [p for p in recent_posts if p.get('was_posted')]

        # Display in grid
        cols_per_row = 3
        for i in range(0, len(recent_posts), cols_per_row):
            cols = st.columns(cols_per_row)

            for j in range(cols_per_row):
                idx = i + j
                if idx < len(recent_posts):
                    post = recent_posts[idx]

                    with cols[j]:
                        # Compact card
                        if post.get('image_bytes'):
                            try:
                                img = Image.open(io.BytesIO(post['image_bytes']))
                                st.image(img, use_container_width=True)
                            except:
                                pass

                        st.caption(f"**{post.get('post_topic', 'Untitled')[:40]}...**")
                        st.caption(f"{post.get('created_at', 'Unknown time')}")

                        if st.button("👁️ View", key=f"view_post_{post['post_id']}", use_container_width=True):
                            # Load this post as current
                            st.session_state.generated_post = post
                            st.rerun()
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

with st.expander("💡 Tips for Better LinkedIn Posts"):
    st.markdown("""
    ### How to Create Engaging LinkedIn Content

    **1. Be Specific with Your Topic**
    - ✅ Good: "Share our company's journey to achieving carbon neutrality and lessons learned"
    - ❌ Vague: "Post about environment stuff"

    **2. Trust Your Profile Context**
    - Your profile already contains your brand voice, audience, and themes
    - The AI will use this context automatically
    - Just focus on what you want to say today

    **3. LinkedIn Best Practices**
    - **Hook**: First line grabs attention (people see it in feed)
    - **Value**: Provide insights, lessons, or actionable advice
    - **CTA**: End with a question or call-to-action to drive engagement
    - **Length**: 150-300 words is optimal for engagement

    **4. Post Types That Work**
    - **Announcements**: Product launches, hiring, company milestones
    - **Thought Leadership**: Industry insights backed by data or experience
    - **Tips & Advice**: Actionable how-to content
    - **Stories**: Personal experiences with lessons learned
    - **Culture**: Behind-the-scenes, team highlights

    **5. Optimize Your Images**
    - Square (1:1) works best for LinkedIn feed visibility
    - Keep text minimal (LinkedIn adds the post text)
    - Use brand colors for consistency
    - Professional but eye-catching

    ### Profile Tips

    - **Update your profile** when your focus changes
    - **Add example posts** to teach the AI your style
    - **Create multiple profiles** for different personas (personal + company)
    - **Set a default** for quick access

    ### Troubleshooting

    - **Generic output?** → Add more context to your topic description
    - **Wrong tone?** → Check your profile's default tone setting
    - **Image doesn't match?** → Be more specific about image needs in your topic
    - **API errors?** → Check your GOOGLE_API_KEY and quota limits
    """)

# Footer
st.divider()
col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    st.markdown("**Powered by:** Google Gemini 2.5 Flash (Text + Image)")
    st.markdown("**Current Profile:** " + current_profile.get('profile_name', 'None') if selected_profile_id else "**No profile selected**")

with col_footer2:
    st.markdown("**Free Tier:** Limited usage per day")
    st.markdown(f"**Profiles:** {len(profiles)}")
