"""
Social Media Post Generator with Multi-Platform Support
Generates high-quality social media posts for LinkedIn and Instagram
with platform-specific optimization and 3-phase image generation
"""

import json
from typing import Dict, Any, Optional, List
import google.generativeai as genai
import os
from dotenv import load_dotenv

from agent.image_generator import generate_image_from_prompt

load_dotenv()


# Platform-specific configuration
PLATFORM_CONFIG = {
    'linkedin': {
        'tone': 'professional, thought-provoking, authoritative',
        'length_words': '150-300 words',
        'length_chars': 'optimal 1300-2600 characters',
        'hashtag_count': '3-5',
        'hashtag_style': 'professional industry tags',
        'writing_style': 'data-driven insights, industry expertise, thought leadership',
        'cta_style': 'engagement questions to spark discussion',
        'emoji_usage': 'minimal, strategic placement only',
        'paragraph_style': 'clear paragraphs with line breaks',
        'audience': 'professionals, decision-makers, industry peers',
        'image_aspect': '1:1',
        'image_style': 'professional photography, clean, modern, corporate aesthetic'
    },
    'instagram': {
        'tone': 'conversational, authentic, relatable, storytelling',
        'length_words': '125-150 words',
        'length_chars': 'optimal 1000-1500 characters',
        'hashtag_count': '8-12',
        'hashtag_style': 'mix of trending, niche, and branded tags',
        'writing_style': 'visual storytelling, personal narratives, behind-the-scenes',
        'cta_style': 'action-driven (DM me, link in bio, save this, share with)',
        'emoji_usage': 'strategic throughout, enhance readability',
        'paragraph_style': 'short lines, frequent breaks, easy scanning',
        'audience': 'lifestyle-focused, visual consumers, community',
        'image_aspect': '4:5',
        'image_style': 'lifestyle photography, vibrant, authentic, engaging, visually striking'
    }
}


class SocialMediaPostGenerator:
    """Generates platform-specific social media posts with optimized image generation"""

    def __init__(self):
        """Initialize Gemini API"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025")
        self.model = genai.GenerativeModel(model_name)

    def generate_post(
        self,
        topic: str,
        platform: str = 'linkedin',
        post_type: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a social media post with platform-specific optimization

        Args:
            topic: What the user wants to post about
            platform: 'linkedin' or 'instagram'
            post_type: Type of post (announcement, thought_leadership, tips, etc.)
            profile: Marketing profile dictionary with brand context
            additional_context: Any extra context from the user

        Returns:
            Dictionary with:
            - success: bool
            - post_text: str (the post caption)
            - hashtags: List[str]
            - image_concept: str (basic concept for image generation)
            - reasoning: str (why Gemini made these choices)
            - error: str (if failed)
        """
        try:
            # Validate platform
            if platform not in PLATFORM_CONFIG:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {platform}. Choose linkedin or instagram.'
                }

            # Build rich context prompt
            prompt = self._build_context_prompt(topic, platform, post_type, profile, additional_context)

            print(f"🎯 Generating {platform.title()} post about: {topic[:100]}...")
            if profile:
                print(f"   Using profile: {profile.get('profile_name', 'Unknown')}")

            # Generate with Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text

            print(f"✅ Gemini response received ({len(response_text)} chars)")

            # Parse JSON response
            result = self._parse_gemini_response(response_text)

            if not result:
                return {
                    'success': False,
                    'error': 'Failed to parse Gemini response as JSON',
                    'raw_response': response_text[:500]
                }

            return {
                'success': True,
                'post_text': result.get('post_text', ''),
                'hashtags': result.get('hashtags', []),
                'image_concept': result.get('image_concept', ''),
                'reasoning': result.get('reasoning', ''),
                'post_type_detected': result.get('post_type', post_type),
                'platform': platform
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Social media post generation error: {error_msg}")

            # Provide helpful error messages
            if "quota" in error_msg.lower() or "429" in error_msg:
                error_msg = "API quota exceeded. Try again later or upgrade to paid tier."
            elif "api key" in error_msg.lower() or "403" in error_msg:
                error_msg = "Invalid API key. Check your GOOGLE_API_KEY in .env file."

            return {
                'success': False,
                'error': error_msg
            }

    def optimize_image_prompt(
        self,
        image_concept: str,
        platform: str,
        profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        PHASE 2: Convert basic image concept into optimized visual generation prompt

        This is the KEY to better image generation - transforms text concepts into
        rich visual descriptions with composition, lighting, style, and mood details.

        Args:
            image_concept: Basic concept from Phase 1 (e.g., "AI innovation in healthcare")
            platform: 'linkedin' or 'instagram'
            profile: Marketing profile for style preferences

        Returns:
            Optimized visual prompt string
        """
        try:
            platform_config = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG['linkedin'])
            platform_image_style = platform_config['image_style']

            # Get profile preferences
            profile_image_style = profile.get('image_style_preference', '') if profile else ''
            industry = profile.get('industry', '') if profile else ''

            # Build optimization prompt
            optimization_prompt = f"""You are an expert visual image generation prompt engineer.

Your task is to transform a basic image concept into a HIGHLY DETAILED, OPTIMIZED prompt for AI image generation.

**BASIC CONCEPT:** {image_concept}

**PLATFORM:** {platform.title()}
**PLATFORM VISUAL STYLE:** {platform_image_style}
{f'**INDUSTRY:** {industry}' if industry else ''}
{f'**PREFERRED STYLE:** {profile_image_style}' if profile_image_style else ''}

Transform this concept into a detailed visual prompt that includes:

1. **Main Subject**: What is the primary focus?
2. **Composition**: How is the scene arranged? (rule of thirds, centered, etc.)
3. **Lighting**: What kind of lighting? (soft, dramatic, natural, golden hour, etc.)
4. **Color Palette**: Dominant colors and mood
5. **Style**: Photography style (photorealistic, minimalist, vibrant, etc.)
6. **Mood/Atmosphere**: Overall feeling (professional, energetic, calm, futuristic, etc.)
7. **Quality Keywords**: (high quality, 4K, professional, detailed, etc.)
8. **Platform-Specific**: Optimize for {platform} aesthetic

**OUTPUT FORMAT:**
Return ONLY the optimized visual prompt as a single paragraph (no JSON, no explanation, just the prompt).
Make it 2-3 sentences, rich with visual details, ready for image generation.

**EXAMPLES:**

Input: "Team collaboration"
Output: "Modern collaborative workspace with diverse professionals gathered around a sleek table, natural light streaming through floor-to-ceiling windows, warm color palette with teal and coral accents, shallow depth of field focusing on hands gesturing over documents, professional photography style, energetic yet focused atmosphere, high quality 4K, corporate aesthetic"

Input: "AI technology"
Output: "Futuristic holographic AI interface floating in modern minimalist space, soft blue and purple neon lighting, clean geometric patterns, sleek dark background with subtle gradients, photorealistic rendering, innovative and cutting-edge mood, professional photography, 4K ultra detailed, tech-forward aesthetic"

Now optimize this concept: {image_concept}
"""

            # Call Gemini for optimization
            response = self.model.generate_content(optimization_prompt)
            optimized_prompt = response.text.strip()

            print(f"🎨 Image prompt optimized:")
            print(f"   Concept: {image_concept[:80]}...")
            print(f"   Optimized: {optimized_prompt[:100]}...")

            return optimized_prompt

        except Exception as e:
            print(f"⚠️ Image prompt optimization failed: {e}")
            # Fallback to basic concept with platform style
            fallback = f"{image_concept}. {platform_config['image_style']}, high quality, professional"
            print(f"   Using fallback: {fallback}")
            return fallback

    def generate_complete_post(
        self,
        topic: str,
        platform: str = 'linkedin',
        post_type: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None,
        generate_image: bool = True,
        reference_images: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Generate complete social media post with text AND image using 3-phase approach

        PHASE 1: Generate post text + basic image concept
        PHASE 2: Optimize image concept into detailed visual prompt
        PHASE 3: Generate image with optimized prompt + reference images

        Args:
            topic: What to post about
            platform: 'linkedin' or 'instagram'
            post_type: Type of post
            profile: Marketing profile context
            additional_context: Extra context
            generate_image: Whether to generate an image (default True)
            reference_images: Optional list of PIL Image objects to guide image style

        Returns:
            Dictionary with:
            - success: bool
            - post_text: str
            - hashtags: List[str]
            - image_bytes: bytes (if generate_image=True)
            - image_prompt: str (optimized)
            - reasoning: str
            - platform: str
            - error: str (if failed)
        """
        # PHASE 1: Generate post text and basic image concept
        print(f"\n📝 PHASE 1: Generating {platform} post text and image concept...")
        post_result = self.generate_post(topic, platform, post_type, profile, additional_context)

        if not post_result['success']:
            return post_result

        # PHASE 2 & 3: Image generation (if requested)
        if generate_image and post_result.get('image_concept'):
            # PHASE 2: Optimize image prompt
            print(f"\n🎨 PHASE 2: Optimizing image prompt for visual generation...")
            optimized_image_prompt = self.optimize_image_prompt(
                post_result['image_concept'],
                platform,
                profile
            )

            # Store optimized prompt
            post_result['image_prompt'] = optimized_image_prompt

            # Get platform-specific settings
            platform_config = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG['linkedin'])
            aspect_ratio = platform_config['image_aspect']

            # Determine negative prompt based on platform
            negative_prompt = self._get_platform_negative_prompt(platform)

            # PHASE 3: Generate image with optimized prompt
            print(f"\n🖼️ PHASE 3: Generating {aspect_ratio} image for {platform}...")
            image_result = generate_image_from_prompt(
                prompt=optimized_image_prompt,
                aspect_ratio=aspect_ratio,
                number_of_images=1,
                reference_images=reference_images if reference_images else None,
                negative_prompt=negative_prompt
            )

            if image_result['success']:
                post_result['image_bytes'] = image_result['image_bytes']
                post_result['image_generation_success'] = True
                print(f"   ✅ Image generated successfully ({aspect_ratio})")
            else:
                post_result['image_generation_success'] = False
                post_result['image_error'] = image_result.get('error', 'Unknown error')
                print(f"   ⚠️ Image generation failed: {post_result['image_error']}")
        else:
            post_result['image_prompt'] = post_result.get('image_concept', '')

        return post_result

    def _build_context_prompt(
        self,
        topic: str,
        platform: str,
        post_type: Optional[str],
        profile: Optional[Dict[str, Any]],
        additional_context: Optional[str]
    ) -> str:
        """Build platform-specific context prompt for Gemini"""

        platform_config = PLATFORM_CONFIG[platform]

        # Base system prompt
        base_prompt = f"""You are an expert {platform.title()} content strategist with deep knowledge of what makes posts successful on {platform.title()}.

**PLATFORM: {platform.upper()}**

Your task is to create a compelling {platform.title()} post that:
1. **Hook**: Grabs attention in the first line (critical for feed visibility)
2. **Value**: Provides genuine value to the reader
3. **Brand Voice**: Matches the brand voice and target audience
4. **Platform Best Practices**: Follows {platform.title()}-specific engagement strategies
5. **CTA**: Ends with a {platform_config['cta_style']}

**{platform.upper()} SPECIFICATIONS:**
- Tone: {platform_config['tone']}
- Length: {platform_config['length_words']} ({platform_config['length_chars']})
- Writing Style: {platform_config['writing_style']}
- Emoji Usage: {platform_config['emoji_usage']}
- Paragraph Style: {platform_config['paragraph_style']}
- Target Audience: {platform_config['audience']}
- Hashtags: {platform_config['hashtag_count']} {platform_config['hashtag_style']}

IMPORTANT: Return your response as valid JSON with this exact structure:
{{
  "post_text": "The full {platform} post text with line breaks (\\n) for readability",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
  "image_concept": "BASIC concept for image (e.g., 'team collaboration', 'AI technology dashboard', 'modern office space')",
  "reasoning": "Brief explanation of why this approach works for this audience on {platform}",
  "post_type": "detected type: announcement/thought_leadership/tips/story/culture"
}}

**CRITICAL FOR IMAGE_CONCEPT:**
- Keep it SIMPLE and CONCEPTUAL (NOT a detailed prompt)
- Focus on the SUBJECT/SCENE only
- Example: "healthcare professional using AI" NOT "modern hospital with holographic interface..."
- The concept will be optimized for image generation in a separate step
"""

        # Add profile context if available
        if profile:
            profile_context = self._format_profile_context(profile, platform)
            base_prompt += f"\n{profile_context}\n"
        else:
            base_prompt += f"\nNo specific profile context provided. Use general {platform.title()} best practices.\n"

        # Add post type guidance
        if post_type:
            post_type_guidance = self._get_post_type_guidance(post_type, platform)
            base_prompt += f"\n{post_type_guidance}\n"
        else:
            base_prompt += "\nPost Type: Determine the best type based on the topic.\n"

        # Add the actual request
        base_prompt += f"\n**TOPIC/REQUEST:**\n{topic}\n"

        if additional_context:
            base_prompt += f"\n**ADDITIONAL CONTEXT:**\n{additional_context}\n"

        # Final instructions
        base_prompt += f"""
**FORMATTING GUIDELINES FOR {platform.upper()}:**
- Use line breaks (\\n\\n) between paragraphs for readability
- Keep it concise: {platform_config['length_words']}
- Emojis: {platform_config['emoji_usage']}
- Make the first line compelling (people see it in their feed)
- End with: {platform_config['cta_style']}

**HASHTAGS FOR {platform.upper()}:**
- Include {platform_config['hashtag_count']} hashtags
- Style: {platform_config['hashtag_style']}
- Relevant to the topic and {platform} audience

**IMAGE CONCEPT (KEEP SIMPLE):**
- Describe the BASIC subject/scene only
- Will be optimized for visual generation separately
- Example: "team meeting", "AI dashboard", "sunset landscape"

Now generate the {platform.title()} post as JSON:
"""

        return base_prompt

    def _format_profile_context(self, profile: Dict[str, Any], platform: str) -> str:
        """Format profile information into context string"""
        context_parts = []

        context_parts.append(f"**PROFILE CONTEXT FOR {platform.upper()}:**")
        context_parts.append(f"- Profile Name: {profile.get('profile_name', 'N/A')}")
        context_parts.append(f"- Type: {profile.get('profile_type', 'N/A').title()}")

        if profile.get('brand_voice'):
            context_parts.append(f"- Brand Voice: {profile['brand_voice']}")

        if profile.get('industry'):
            context_parts.append(f"- Industry: {profile['industry']}")

        if profile.get('target_audience'):
            context_parts.append(f"- Target Audience: {profile['target_audience']}")

        if profile.get('content_themes'):
            themes = ', '.join(profile['content_themes'])
            context_parts.append(f"- Content Themes: {themes}")

        if profile.get('typical_post_style'):
            context_parts.append(f"- Typical Style: {profile['typical_post_style']}")

        if profile.get('default_tone'):
            context_parts.append(f"- Preferred Tone: {profile['default_tone']}")

        # Add role/expertise for personal profiles
        if profile.get('profile_type') == 'personal':
            if profile.get('role_title'):
                context_parts.append(f"- Role: {profile['role_title']}")
            if profile.get('expertise_areas'):
                expertise = ', '.join(profile['expertise_areas'])
                context_parts.append(f"- Expertise: {expertise}")
            if profile.get('personal_bio'):
                context_parts.append(f"- Bio: {profile['personal_bio']}")

        # Add company info for company profiles
        if profile.get('profile_type') == 'company':
            if profile.get('company_size'):
                context_parts.append(f"- Company Size: {profile['company_size']}")

        # Add example posts if available
        if profile.get('example_posts') and len(profile['example_posts']) > 0:
            context_parts.append(f"\n**STYLE EXAMPLES (for {platform} reference):**")
            for i, example in enumerate(profile['example_posts'][:2], 1):
                if isinstance(example, dict):
                    context_parts.append(f"\nExample {i}:")
                    context_parts.append(f"```\n{example.get('text', 'N/A')}\n```")
                    if example.get('performance_note'):
                        context_parts.append(f"Performance: {example['performance_note']}")

        # Add topics to avoid
        if profile.get('avoid_topics'):
            topics = ', '.join(profile['avoid_topics'])
            context_parts.append(f"\n**AVOID THESE TOPICS:** {topics}")

        return '\n'.join(context_parts)

    def _get_post_type_guidance(self, post_type: str, platform: str) -> str:
        """Get specific guidance for different post types adapted to platform"""

        # Base guidance (platform-agnostic)
        base_guidance_map = {
            'announcement': {
                'description': 'Announcement',
                'guidelines': [
                    'Clear, direct communication of news',
                    'Lead with the main announcement',
                    'Explain why it matters to your audience',
                    'Include specific details (dates, links, etc.)',
                    'Express excitement without being overly promotional'
                ]
            },
            'thought_leadership': {
                'description': 'Thought Leadership',
                'guidelines': [
                    'Share a unique perspective or insight',
                    'Back it up with data, examples, or personal experience',
                    'Challenge conventional thinking (if appropriate)',
                    'Demonstrate expertise without being preachy',
                    'End with a provocative question to spark discussion'
                ]
            },
            'tips': {
                'description': 'Tips & Advice',
                'guidelines': [
                    'Lead with the value proposition ("3 ways to...")',
                    'Make it actionable and specific',
                    'Use numbered lists or clear structure',
                    'Share from personal experience when possible',
                    'End with "What would you add?" to drive engagement'
                ]
            },
            'company_culture': {
                'description': 'Company Culture',
                'guidelines': [
                    'Humanize your brand with behind-the-scenes content',
                    'Highlight people, not just achievements',
                    'Show authentic moments',
                    'Connect culture to values or mission',
                    'Make it relatable to your audience'
                ]
            },
            'personal_story': {
                'description': 'Personal Story',
                'guidelines': [
                    'Start with a compelling hook',
                    'Share vulnerability or lessons learned',
                    'Connect to a broader insight or takeaway',
                    'Make it relevant to your audience\'s challenges',
                    'End with reflection or call-to-action'
                ]
            },
        }

        guidance = base_guidance_map.get(post_type.lower(), {
            'description': 'General',
            'guidelines': ['Adapt to best fit the topic and platform']
        })

        # Platform-specific adjustments
        platform_adjustment = ""
        if platform == 'instagram':
            platform_adjustment = "\n**Instagram-Specific:** Make it more visual, use line breaks frequently, add relevant emojis, and focus on storytelling."
        elif platform == 'linkedin':
            platform_adjustment = "\n**LinkedIn-Specific:** Professional tone, data-driven insights, and thought-provoking questions work best."

        guidelines_text = '\n'.join([f"- {g}" for g in guidance['guidelines']])

        return f"""
**POST TYPE: {guidance['description']}**
{guidelines_text}{platform_adjustment}
"""

    def _get_platform_negative_prompt(self, platform: str) -> str:
        """Get negative prompt for image generation based on platform"""
        negative_prompts = {
            'linkedin': 'casual, cartoon, unprofessional, cluttered, busy, messy, amateur, low quality, blurry, distorted',
            'instagram': 'boring, corporate, stiff, formal, dull colors, uninteresting, plain, generic, low quality, blurry'
        }
        return negative_prompts.get(platform, 'low quality, blurry, distorted')

    def _parse_gemini_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse Gemini's JSON response, handling markdown code blocks"""
        try:
            # Remove markdown code blocks if present
            cleaned = response_text.strip()

            # Handle ```json ... ``` blocks
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]  # Remove ```json
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]  # Remove ```

            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]  # Remove closing ```

            cleaned = cleaned.strip()

            # Parse JSON
            result = json.loads(cleaned)

            # Validate required fields
            required_fields = ['post_text', 'hashtags', 'image_concept']
            for field in required_fields:
                if field not in result:
                    print(f"⚠️ Missing required field in response: {field}")
                    return None

            return result

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"   Response text: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Unexpected error parsing response: {e}")
            return None


# ==================== Convenience Functions ====================

def generate_social_post(
    topic: str,
    platform: str = 'linkedin',
    profile: Optional[Dict[str, Any]] = None,
    post_type: Optional[str] = None,
    generate_image: bool = True,
    reference_images: Optional[List] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a complete social media post

    Args:
        topic: What to post about
        platform: 'linkedin' or 'instagram'
        profile: Marketing profile dictionary
        post_type: Optional post type
        generate_image: Whether to generate image (default True)
        reference_images: Optional list of PIL Image objects to guide image style

    Returns:
        Complete post result dictionary
    """
    generator = SocialMediaPostGenerator()
    return generator.generate_complete_post(
        topic=topic,
        platform=platform,
        post_type=post_type,
        profile=profile,
        generate_image=generate_image,
        reference_images=reference_images
    )
