"""
Marketing Profile Onboarding Wizard
Guided multi-step setup for creating marketing profiles
"""

import streamlit as st
from typing import Dict, Any, Optional
from agent.database.db_manager import DatabaseManager
from agent.database.marketing_profile_manager import MarketingProfileManager
from agent.smart_profile_extractor import extract_profile_from_document, apply_extracted_data_to_session


def render_onboarding_wizard(
    db_manager: DatabaseManager,
    user_id: str,
    user_name: str
) -> Optional[str]:
    """
    Render the complete onboarding wizard

    Args:
        db_manager: Database manager instance
        user_id: Current user's ID
        user_name: Current user's name

    Returns:
        profile_id if successfully created, None otherwise
    """
    marketing_mgr = MarketingProfileManager(db_manager)

    # Initialize session state for wizard
    if 'onboarding_step' not in st.session_state:
        st.session_state.onboarding_step = 1

    if 'onboarding_data' not in st.session_state:
        st.session_state.onboarding_data = {}

    if 'smart_extraction_done' not in st.session_state:
        st.session_state.smart_extraction_done = False

    # Progress tracking
    total_steps = 5
    current_step = st.session_state.onboarding_step

    # Header
    st.markdown("# 🚀 Create Your Marketing Profile")
    st.markdown("Let's set up your profile to generate amazing LinkedIn content!")

    # Progress bar
    progress = (current_step - 1) / total_steps
    st.progress(progress)
    st.caption(f"Step {current_step} of {total_steps}")

    st.divider()

    # Render current step
    if current_step == 1:
        _render_step_profile_type()
    elif current_step == 2:
        _render_step_brand_identity()
    elif current_step == 3:
        _render_step_linkedin_strategy()
    elif current_step == 4:
        _render_step_preferences()
    elif current_step == 5:
        return _render_step_review_save(marketing_mgr, user_id)

    return None


def _render_step_profile_type():
    """Step 1: Choose profile type and basic info"""
    st.markdown("### Step 1: Profile Type")
    st.markdown("Are you creating content as an individual or for a company?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👤 Personal Brand", use_container_width=True, type="primary" if st.session_state.onboarding_data.get('profile_type') == 'personal' else "secondary"):
            st.session_state.onboarding_data['profile_type'] = 'personal'
            st.rerun()

        st.caption("For: Consultants, founders, thought leaders, professionals building personal brand")

    with col2:
        if st.button("🏢 Company Account", use_container_width=True, type="primary" if st.session_state.onboarding_data.get('profile_type') == 'company' else "secondary"):
            st.session_state.onboarding_data['profile_type'] = 'company'
            st.rerun()

        st.caption("For: Corporate accounts, startups, agencies posting on behalf of company")

    if st.session_state.onboarding_data.get('profile_type'):
        st.success(f"✓ Selected: {st.session_state.onboarding_data['profile_type'].title()}")

        st.markdown("---")

        # Smart extraction from resume/bio
        if not st.session_state.smart_extraction_done:
            st.markdown("### 🚀 Quick Start: Upload Your Resume/Bio (Optional)")
            st.caption("AI will analyze your document and pre-fill the form to save you time!")

            uploaded_file = st.file_uploader(
                "Upload resume, CV, LinkedIn profile, or professional bio",
                type=['pdf', 'docx', 'txt'],
                help="Upload a document containing your professional information. AI will extract relevant details automatically.",
                key="resume_uploader"
            )

            if uploaded_file:
                col_extract1, col_extract2 = st.columns([3, 1])

                with col_extract1:
                    st.info(f"📄 **File uploaded:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

                with col_extract2:
                    if st.button("🤖 Extract Info", type="primary", use_container_width=True):
                        with st.spinner("🤖 Analyzing your document with AI... This may take 10-20 seconds..."):
                            file_type = uploaded_file.name.split('.')[-1].lower()
                            file_bytes = uploaded_file.read()

                            result = extract_profile_from_document(
                                file_bytes=file_bytes,
                                filename=uploaded_file.name,
                                file_type=file_type
                            )

                            if result['success']:
                                extracted_data = result['extracted_data']
                                confidence = result.get('confidence_score', 0.0)

                                # Apply extracted data to session
                                st.session_state.onboarding_data = apply_extracted_data_to_session(
                                    extracted_data,
                                    st.session_state.onboarding_data,
                                    st.session_state.onboarding_data['profile_type']
                                )

                                st.session_state.smart_extraction_done = True

                                st.success(f"✅ **Extracted Successfully!** (Confidence: {confidence:.0%})")

                                # Show what was found
                                found_items = []
                                if extracted_data.get('full_name'):
                                    found_items.append(f"Name: {extracted_data['full_name']}")
                                if extracted_data.get('role_title'):
                                    found_items.append(f"Role: {extracted_data['role_title']}")
                                if extracted_data.get('expertise_areas'):
                                    found_items.append(f"Expertise: {', '.join(extracted_data['expertise_areas'][:3])}")

                                if found_items:
                                    st.info("📋 **Found:**\n" + "\n".join([f"- {item}" for item in found_items]))

                                st.info("👇 **Review and edit the pre-filled information below before continuing**")

                                # Show suggestions if available
                                suggestions = result.get('suggestions', [])
                                if suggestions:
                                    with st.expander("💡 AI Suggestions for Your Content Strategy"):
                                        for suggestion in suggestions:
                                            st.markdown(f"- {suggestion}")

                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error', 'Failed to extract information')}")
                                st.warning("💡 **Tip:** Ensure the document is a resume, CV, or professional bio with clear text content.")

            st.markdown("---")
        else:
            st.success("✅ **Information extracted from your document!** Review and edit below.")
            if st.button("🔄 Upload Different Document", use_container_width=False):
                st.session_state.smart_extraction_done = False
                st.rerun()

            st.markdown("---")

        # Profile name
        profile_name = st.text_input(
            "Profile Name",
            value=st.session_state.onboarding_data.get('profile_name', ''),
            placeholder="e.g., 'Shahzeb Personal' or 'Acme Corp Marketing'",
            help="A friendly name to identify this profile"
        )

        if profile_name:
            st.session_state.onboarding_data['profile_name'] = profile_name

        # Industry
        industries = [
            "Technology", "Finance", "Healthcare", "Education", "Marketing",
            "Real Estate", "Consulting", "E-commerce", "Manufacturing",
            "Media & Entertainment", "Professional Services", "Other"
        ]

        industry = st.selectbox(
            "Industry",
            options=industries,
            index=industries.index(st.session_state.onboarding_data.get('industry', 'Technology'))
        )
        st.session_state.onboarding_data['industry'] = industry

        st.markdown("---")

        # Navigation
        col_skip, col_next = st.columns([1, 1])

        with col_skip:
            if st.button("Skip Setup (Use Defaults)", use_container_width=True):
                # Create minimal profile and skip to end
                st.session_state.onboarding_data['skip_to_end'] = True
                st.session_state.onboarding_step = 5
                st.rerun()

        with col_next:
            if st.button("Next →", use_container_width=True, type="primary", disabled=not profile_name):
                st.session_state.onboarding_step = 2
                st.rerun()


def _render_step_brand_identity():
    """Step 2: Brand identity (personal or company specific)"""
    profile_type = st.session_state.onboarding_data.get('profile_type', 'personal')

    st.markdown("### Step 2: Brand Identity")

    if profile_type == 'personal':
        st.markdown("Tell us about your personal brand")

        # Role/Title
        role_title = st.text_input(
            "Your Role/Title",
            value=st.session_state.onboarding_data.get('role_title', ''),
            placeholder="e.g., 'CEO & Founder', 'Marketing Director', 'AI Consultant'",
            help="How do you introduce yourself professionally?"
        )
        if role_title:
            st.session_state.onboarding_data['role_title'] = role_title

        # Expertise areas
        st.markdown("**Your Expertise Areas**")
        expertise_options = [
            "AI/ML", "Digital Marketing", "SaaS", "Leadership", "Sales",
            "Product Management", "Data Science", "Design", "Finance",
            "Entrepreneurship", "Tech Strategy", "Content Creation"
        ]

        selected_expertise = st.multiselect(
            "Select your areas of expertise",
            options=expertise_options,
            default=st.session_state.onboarding_data.get('expertise_areas', []),
            help="What topics do you have deep knowledge in?",
            key="expertise_multiselect"
        )

        custom_expertise = st.text_input(
            "Add custom expertise (comma-separated)",
            placeholder="e.g., Blockchain, Climate Tech"
        )

        if custom_expertise:
            custom_list = [e.strip() for e in custom_expertise.split(',') if e.strip()]
            selected_expertise.extend(custom_list)

        if selected_expertise:
            st.session_state.onboarding_data['expertise_areas'] = list(set(selected_expertise))

        # Personal bio
        personal_bio = st.text_area(
            "Short Bio (150-300 characters)",
            value=st.session_state.onboarding_data.get('personal_bio', ''),
            placeholder="e.g., 'Helping companies scale with AI. Former Google PM. Stanford CS. Sharing lessons on leadership and innovation.'",
            max_chars=300,
            help="A concise description of who you are and what you do"
        )
        if personal_bio:
            st.session_state.onboarding_data['personal_bio'] = personal_bio

    else:  # company
        st.markdown("Tell us about your company")

        # Company size
        company_size = st.selectbox(
            "Company Size",
            options=["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"],
            index=0
        )
        st.session_state.onboarding_data['company_size'] = company_size

    # Brand voice (common for both)
    st.markdown("---")
    st.markdown("**Brand Voice**")
    st.caption("How would you describe your communication style?")

    brand_voice_presets = {
        "Professional & Authoritative": "Professional, data-driven, authoritative",
        "Friendly & Approachable": "Conversational, friendly, approachable",
        "Innovative & Bold": "Innovative, bold, forward-thinking",
        "Educational & Helpful": "Educational, helpful, expert guidance",
        "Inspirational & Motivating": "Inspirational, motivating, uplifting",
        "Custom": "custom"
    }

    selected_voice = st.selectbox(
        "Choose a brand voice preset",
        options=list(brand_voice_presets.keys())
    )

    if selected_voice == "Custom":
        custom_voice = st.text_input(
            "Describe your brand voice",
            value=st.session_state.onboarding_data.get('brand_voice', ''),
            placeholder="e.g., 'Technical but accessible, with humor and personal stories'"
        )
        if custom_voice:
            st.session_state.onboarding_data['brand_voice'] = custom_voice
    else:
        st.session_state.onboarding_data['brand_voice'] = brand_voice_presets[selected_voice]

    # Brand colors (optional)
    with st.expander("🎨 Brand Colors (Optional)"):
        col1, col2, col3 = st.columns(3)

        with col1:
            primary_color = st.color_picker(
                "Primary Color",
                value=st.session_state.onboarding_data.get('brand_colors', {}).get('primary', '#1A3A52')
            )

        with col2:
            secondary_color = st.color_picker(
                "Secondary Color",
                value=st.session_state.onboarding_data.get('brand_colors', {}).get('secondary', '#F4A261')
            )

        with col3:
            accent_color = st.color_picker(
                "Accent Color",
                value=st.session_state.onboarding_data.get('brand_colors', {}).get('accent', '#E76F51')
            )

        st.session_state.onboarding_data['brand_colors'] = {
            'primary': primary_color,
            'secondary': secondary_color,
            'accent': accent_color
        }

    # Navigation
    st.markdown("---")
    col_back, col_next = st.columns([1, 1])

    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.onboarding_step = 1
            st.rerun()

    with col_next:
        can_proceed = (
            (profile_type == 'personal' and st.session_state.onboarding_data.get('role_title')) or
            (profile_type == 'company' and st.session_state.onboarding_data.get('company_size'))
        )
        if st.button("Next →", use_container_width=True, type="primary", disabled=not can_proceed):
            st.session_state.onboarding_step = 3
            st.rerun()


def _render_step_linkedin_strategy():
    """Step 3: LinkedIn content strategy"""
    st.markdown("### Step 3: LinkedIn Strategy")
    st.markdown("Help us understand your LinkedIn content goals")

    # Target audience
    target_audience = st.text_area(
        "Who is your target audience?",
        value=st.session_state.onboarding_data.get('target_audience', ''),
        placeholder="e.g., 'C-level executives in fintech', 'Early-stage startup founders', 'Marketing professionals in B2B SaaS'",
        help="Who are you trying to reach with your content?",
        height=80
    )
    if target_audience:
        st.session_state.onboarding_data['target_audience'] = target_audience

    # Content themes
    st.markdown("**Content Themes**")
    st.caption("What topics do you want to post about?")

    theme_options = [
        "AI & Technology", "Leadership & Management", "Startup Growth",
        "Marketing Strategy", "Sales & Business Development", "Product Development",
        "Industry Insights", "Company Culture", "Personal Development",
        "Innovation", "Data & Analytics", "Customer Success"
    ]

    selected_themes = st.multiselect(
        "Select content themes",
        options=theme_options,
        default=st.session_state.onboarding_data.get('content_themes', []),
        help="Pick 3-5 themes you'll regularly post about",
        key="content_themes_multiselect"
    )

    custom_themes = st.text_input(
        "Add custom themes (comma-separated)",
        placeholder="e.g., Remote Work, Climate Tech"
    )

    if custom_themes:
        custom_list = [t.strip() for t in custom_themes.split(',') if t.strip()]
        selected_themes.extend(custom_list)

    if selected_themes:
        st.session_state.onboarding_data['content_themes'] = list(set(selected_themes))

    # Typical post style
    st.markdown("---")
    typical_post_style = st.text_area(
        "Describe your typical post style (optional)",
        value=st.session_state.onboarding_data.get('typical_post_style', ''),
        placeholder="e.g., 'Data-backed insights with personal anecdotes and actionable takeaways'",
        help="How do you usually structure your posts?",
        height=80
    )
    if typical_post_style:
        st.session_state.onboarding_data['typical_post_style'] = typical_post_style

    # Example posts for learning
    with st.expander("📝 Paste Example Posts (Optional but Recommended)"):
        st.caption("Paste 1-2 of your best-performing posts so we can learn your style")

        example_1 = st.text_area(
            "Example Post 1",
            value=st.session_state.onboarding_data.get('example_post_1_text', ''),
            placeholder="Paste a LinkedIn post you like...",
            height=120,
            key="example_1"
        )

        example_1_note = st.text_input(
            "Performance note (optional)",
            value=st.session_state.onboarding_data.get('example_post_1_note', ''),
            placeholder="e.g., '500 likes, 50 comments'",
            key="note_1"
        )

        if example_1:
            st.session_state.onboarding_data['example_post_1_text'] = example_1
            st.session_state.onboarding_data['example_post_1_note'] = example_1_note

        st.markdown("---")

        example_2 = st.text_area(
            "Example Post 2",
            value=st.session_state.onboarding_data.get('example_post_2_text', ''),
            placeholder="Paste another LinkedIn post...",
            height=120,
            key="example_2"
        )

        example_2_note = st.text_input(
            "Performance note (optional)",
            value=st.session_state.onboarding_data.get('example_post_2_note', ''),
            placeholder="e.g., '300 likes, 20 shares'",
            key="note_2"
        )

        if example_2:
            st.session_state.onboarding_data['example_post_2_text'] = example_2
            st.session_state.onboarding_data['example_post_2_note'] = example_2_note

    # Navigation
    st.markdown("---")
    col_back, col_next = st.columns([1, 1])

    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.onboarding_step = 2
            st.rerun()

    with col_next:
        can_proceed = target_audience and selected_themes
        if st.button("Next →", use_container_width=True, type="primary", disabled=not can_proceed):
            st.session_state.onboarding_step = 4
            st.rerun()


def _render_step_preferences():
    """Step 4: Generation preferences"""
    st.markdown("### Step 4: Content Preferences")
    st.markdown("Customize how content is generated for you")

    # Default tone
    st.markdown("**Default Tone**")
    tone_options = {
        "Professional": "Balanced, professional, suitable for business context",
        "Inspirational": "Motivating, uplifting, energizing",
        "Educational": "Teaching-focused, informative, helpful",
        "Conversational": "Casual, friendly, relatable",
        "Provocative": "Thought-provoking, challenges status quo"
    }

    selected_tone = st.radio(
        "Choose your preferred tone",
        options=list(tone_options.keys()),
        index=0,
        help="This can be changed per-post, but sets the default"
    )

    st.caption(f"*{tone_options[selected_tone]}*")
    st.session_state.onboarding_data['default_tone'] = selected_tone.lower()

    # Image style
    st.markdown("---")
    st.markdown("**Image Style Preference**")

    image_style_options = {
        "Professional": "Clean, corporate, business-appropriate",
        "Minimalist": "Simple, clean lines, less is more",
        "Vibrant": "Colorful, energetic, eye-catching",
        "Photorealistic": "Realistic photography style",
        "Abstract": "Artistic, conceptual, creative"
    }

    selected_style = st.radio(
        "Choose your preferred image style",
        options=list(image_style_options.keys()),
        index=0
    )

    st.caption(f"*{image_style_options[selected_style]}*")
    st.session_state.onboarding_data['image_style_preference'] = selected_style.lower()

    # Topics to avoid
    st.markdown("---")
    st.markdown("**Topics to Avoid (Optional)**")

    avoid_topics = st.text_input(
        "Topics you want to avoid (comma-separated)",
        value=', '.join(st.session_state.onboarding_data.get('avoid_topics', [])),
        placeholder="e.g., politics, religion, controversial topics",
        help="We'll avoid generating content about these topics"
    )

    if avoid_topics:
        topics_list = [t.strip() for t in avoid_topics.split(',') if t.strip()]
        st.session_state.onboarding_data['avoid_topics'] = topics_list

    # Navigation
    st.markdown("---")
    col_back, col_next = st.columns([1, 1])

    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.onboarding_step = 3
            st.rerun()

    with col_next:
        if st.button("Next → Review", use_container_width=True, type="primary"):
            st.session_state.onboarding_step = 5
            st.rerun()


def _render_step_review_save(marketing_mgr: MarketingProfileManager, user_id: str) -> Optional[str]:
    """Step 5: Review and save"""
    st.markdown("### Step 5: Review & Save")

    data = st.session_state.onboarding_data

    # Display summary
    st.markdown("**Profile Summary**")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"""
**Basic Info**
- Type: {data.get('profile_type', 'N/A').title()}
- Name: {data.get('profile_name', 'N/A')}
- Industry: {data.get('industry', 'N/A')}
        """)

        if data.get('profile_type') == 'personal':
            st.info(f"""
**Personal Brand**
- Role: {data.get('role_title', 'N/A')}
- Expertise: {', '.join(data.get('expertise_areas', [])[:3])}
            """)
        else:
            st.info(f"""
**Company Info**
- Size: {data.get('company_size', 'N/A')}
            """)

    with col2:
        st.info(f"""
**LinkedIn Strategy**
- Audience: {data.get('target_audience', 'N/A')[:50]}...
- Themes: {', '.join(data.get('content_themes', [])[:3])}
        """)

        st.info(f"""
**Preferences**
- Tone: {data.get('default_tone', 'professional').title()}
- Image Style: {data.get('image_style_preference', 'professional').title()}
        """)

    # Set as default option
    st.markdown("---")
    is_default = st.checkbox(
        "Set as default profile",
        value=True,
        help="The default profile will be automatically selected when you create new posts"
    )

    # Save button
    st.markdown("---")

    col_back, col_save = st.columns([1, 1])

    with col_back:
        if st.button("← Back to Edit", use_container_width=True):
            st.session_state.onboarding_step = 4
            st.rerun()

    with col_save:
        if st.button("✅ Create Profile", use_container_width=True, type="primary"):
            # Prepare example posts
            example_posts = []
            if data.get('example_post_1_text'):
                example_posts.append({
                    'text': data['example_post_1_text'],
                    'performance_note': data.get('example_post_1_note', '')
                })
            if data.get('example_post_2_text'):
                example_posts.append({
                    'text': data['example_post_2_text'],
                    'performance_note': data.get('example_post_2_note', '')
                })

            # Create profile
            try:
                # Debug logging
                print(f"🔍 Creating profile with user_id: {user_id}")

                profile_id = marketing_mgr.create_profile(
                    user_id=user_id,
                    profile_type=data.get('profile_type', 'personal'),
                    profile_name=data.get('profile_name', 'My Profile'),
                    brand_voice=data.get('brand_voice'),
                    industry=data.get('industry'),
                    target_audience=data.get('target_audience'),
                    content_themes=data.get('content_themes'),
                    default_tone=data.get('default_tone', 'professional'),
                    image_style_preference=data.get('image_style_preference', 'professional'),
                    is_default=is_default,
                    # Optional fields
                    brand_colors=data.get('brand_colors'),
                    company_size=data.get('company_size'),
                    role_title=data.get('role_title'),
                    expertise_areas=data.get('expertise_areas'),
                    personal_bio=data.get('personal_bio'),
                    typical_post_style=data.get('typical_post_style'),
                    example_posts=example_posts if example_posts else None,
                    avoid_topics=data.get('avoid_topics')
                )

                st.success("🎉 Profile created successfully!")

                # Clear onboarding state
                st.session_state.onboarding_step = 1
                st.session_state.onboarding_data = {}
                st.session_state.show_onboarding = False
                st.session_state.smart_extraction_done = False

                return profile_id

            except Exception as e:
                st.error(f"❌ Error creating profile: {e}")
                st.error(f"🔍 Debug Info: user_id={user_id}, profile_name={data.get('profile_name')}")
                import traceback
                st.code(traceback.format_exc())
                return None

    return None
