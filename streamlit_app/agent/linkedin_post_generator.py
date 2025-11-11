"""
LinkedIn Post Generator with Context-Aware Gemini Integration
Generates high-quality LinkedIn posts by feeding Gemini rich profile context
"""

import json
from typing import Dict, Any, Optional, List
import google.generativeai as genai
import os
from dotenv import load_dotenv

from agent.image_generator import generate_image_from_prompt

load_dotenv()


class LinkedInPostGenerator:
    """Generates context-aware LinkedIn posts using Gemini"""

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
        post_type: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a LinkedIn post with optional profile context

        Args:
            topic: What the user wants to post about
            post_type: Type of post (announcement, thought_leadership, tips, etc.)
            profile: Marketing profile dictionary with brand context
            additional_context: Any extra context from the user

        Returns:
            Dictionary with:
            - success: bool
            - post_text: str (the LinkedIn caption)
            - hashtags: List[str]
            - image_prompt: str (prompt for image generation)
            - reasoning: str (why Gemini made these choices)
            - error: str (if failed)
        """
        try:
            # Build rich context prompt
            prompt = self._build_context_prompt(topic, post_type, profile, additional_context)

            print(f"🎯 Generating LinkedIn post about: {topic[:100]}...")
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
                'image_prompt': result.get('image_prompt', ''),
                'reasoning': result.get('reasoning', ''),
                'post_type_detected': result.get('post_type', post_type)
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ LinkedIn post generation error: {error_msg}")

            # Provide helpful error messages
            if "quota" in error_msg.lower() or "429" in error_msg:
                error_msg = "API quota exceeded. Try again later or upgrade to paid tier."
            elif "api key" in error_msg.lower() or "403" in error_msg:
                error_msg = "Invalid API key. Check your GOOGLE_API_KEY in .env file."

            return {
                'success': False,
                'error': error_msg
            }

    def generate_complete_post(
        self,
        topic: str,
        post_type: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None,
        generate_image: bool = True,
        reference_images: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Generate complete LinkedIn post with text AND image

        Args:
            topic: What to post about
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
            - image_prompt: str
            - reasoning: str
            - error: str (if failed)
        """
        # Step 1: Generate post text and image prompt
        post_result = self.generate_post(topic, post_type, profile, additional_context)

        if not post_result['success']:
            return post_result

        # Step 2: Generate image if requested
        if generate_image and post_result.get('image_prompt'):
            print(f"🎨 Generating image for post...")

            # Determine aspect ratio from profile or default to 1:1
            aspect_ratio = "1:1"  # LinkedIn posts work well with square images
            image_style = profile.get('image_style_preference', 'professional') if profile else 'professional'

            # Enhance image prompt with style preference
            enhanced_image_prompt = post_result['image_prompt']
            if image_style and image_style != 'professional':
                enhanced_image_prompt = f"{enhanced_image_prompt}. Style: {image_style}"

            # Generate image
            image_result = generate_image_from_prompt(
                prompt=enhanced_image_prompt,
                aspect_ratio=aspect_ratio,
                number_of_images=1,
                reference_images=reference_images if reference_images else None,
                negative_prompt="low quality, blurry, distorted, watermark, text overlay"
            )

            if image_result['success']:
                post_result['image_bytes'] = image_result['image_bytes']
                post_result['image_generation_success'] = True
                print(f"   ✅ Image generated successfully")
            else:
                post_result['image_generation_success'] = False
                post_result['image_error'] = image_result.get('error', 'Unknown error')
                print(f"   ⚠️ Image generation failed: {post_result['image_error']}")

        return post_result

    def _build_context_prompt(
        self,
        topic: str,
        post_type: Optional[str],
        profile: Optional[Dict[str, Any]],
        additional_context: Optional[str]
    ) -> str:
        """Build rich context prompt for Gemini"""

        # Base system prompt
        base_prompt = """You are an expert LinkedIn content strategist with deep knowledge of what makes posts successful on LinkedIn.

Your task is to create a compelling LinkedIn post that:
1. Grabs attention in the first line (the "hook")
2. Provides genuine value to the reader
3. Matches the brand voice and target audience
4. Follows LinkedIn best practices for engagement
5. Ends with a clear call-to-action or thought-provoking question

IMPORTANT: Return your response as valid JSON with this exact structure:
{
  "post_text": "The full LinkedIn post text with line breaks (\\n) for readability",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
  "image_prompt": "Detailed description for image generation that complements the post",
  "reasoning": "Brief explanation of why this approach works for this audience",
  "post_type": "detected type: announcement/thought_leadership/tips/story/culture"
}

"""

        # Add profile context if available
        if profile:
            profile_context = self._format_profile_context(profile)
            base_prompt += f"\n{profile_context}\n"
        else:
            base_prompt += "\nNo specific profile context provided. Use general LinkedIn best practices.\n"

        # Add post type guidance
        if post_type:
            post_type_guidance = self._get_post_type_guidance(post_type)
            base_prompt += f"\n{post_type_guidance}\n"
        else:
            base_prompt += "\nPost Type: Determine the best type based on the topic.\n"

        # Add the actual request
        base_prompt += f"\n**TOPIC/REQUEST:**\n{topic}\n"

        if additional_context:
            base_prompt += f"\n**ADDITIONAL CONTEXT:**\n{additional_context}\n"

        # Final instructions
        base_prompt += """
**FORMATTING GUIDELINES:**
- Use line breaks (\\n\\n) between paragraphs for readability
- Keep it concise: 150-300 words is optimal for LinkedIn engagement
- Use emojis sparingly and only if it fits the brand voice
- Make the first line compelling (people see it in their feed)
- End with a question or CTA to drive comments

**HASHTAGS:**
- Include 3-5 relevant hashtags
- Mix of popular and niche tags
- Relevant to the topic and industry

**IMAGE PROMPT:**
- Describe a professional, eye-catching image
- Should complement the post without being too literal
- Specify colors, mood, composition
- Keep it appropriate for LinkedIn's professional audience

Now generate the LinkedIn post as JSON:
"""

        return base_prompt

    def _format_profile_context(self, profile: Dict[str, Any]) -> str:
        """Format profile information into context string"""
        context_parts = []

        context_parts.append("**PROFILE CONTEXT:**")
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
            context_parts.append("\n**STYLE EXAMPLES (for reference):**")
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

    def _get_post_type_guidance(self, post_type: str) -> str:
        """Get specific guidance for different post types"""
        guidance_map = {
            'announcement': """
**POST TYPE: Announcement**
- Clear, direct communication of news
- Lead with the main announcement
- Explain why it matters to your audience
- Include specific details (dates, links, etc.)
- Express excitement without being overly promotional
""",
            'thought_leadership': """
**POST TYPE: Thought Leadership**
- Share a unique perspective or insight
- Back it up with data, examples, or personal experience
- Challenge conventional thinking (if appropriate)
- Demonstrate expertise without being preachy
- End with a provocative question to spark discussion
""",
            'tips': """
**POST TYPE: Tips & Advice**
- Lead with the value proposition ("3 ways to...")
- Make it actionable and specific
- Use numbered lists or clear structure
- Share from personal experience when possible
- End with "What would you add?" to drive engagement
""",
            'company_culture': """
**POST TYPE: Company Culture**
- Humanize your brand with behind-the-scenes content
- Highlight people, not just achievements
- Show authentic moments
- Connect culture to values or mission
- Make it relatable to your audience
""",
            'personal_story': """
**POST TYPE: Personal Story**
- Start with a compelling hook
- Share vulnerability or lessons learned
- Connect to a broader insight or takeaway
- Make it relevant to your audience's challenges
- End with reflection or call-to-action
""",
        }

        return guidance_map.get(post_type.lower(), "**POST TYPE: General**\nAdapt to best fit the topic.")

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
            required_fields = ['post_text', 'hashtags', 'image_prompt']
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

def generate_linkedin_post_with_profile(
    topic: str,
    profile: Dict[str, Any],
    post_type: Optional[str] = None,
    generate_image: bool = True,
    reference_images: Optional[List] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a complete LinkedIn post with profile context

    Args:
        topic: What to post about
        profile: Marketing profile dictionary
        post_type: Optional post type
        generate_image: Whether to generate image (default True)
        reference_images: Optional list of PIL Image objects to guide image style

    Returns:
        Complete post result dictionary
    """
    generator = LinkedInPostGenerator()
    return generator.generate_complete_post(
        topic=topic,
        post_type=post_type,
        profile=profile,
        generate_image=generate_image,
        reference_images=reference_images
    )


def generate_linkedin_post_simple(
    topic: str,
    post_type: Optional[str] = None,
    generate_image: bool = True,
    reference_images: Optional[List] = None
) -> Dict[str, Any]:
    """
    Simple LinkedIn post generation without profile context

    Args:
        topic: What to post about
        post_type: Optional post type
        generate_image: Whether to generate image (default True)
        reference_images: Optional list of PIL Image objects to guide image style

    Returns:
        Complete post result dictionary
    """
    generator = LinkedInPostGenerator()
    return generator.generate_complete_post(
        topic=topic,
        post_type=post_type,
        profile=None,
        generate_image=generate_image,
        reference_images=reference_images
    )
