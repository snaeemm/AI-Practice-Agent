"""
Image generation using Gemini 2.5 Flash Image (free tier available!)
Uses the conversational image generation model that works with regular Gemini API
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import io
import base64

load_dotenv()


def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: str = "1:1",
    number_of_images: int = 1,
    reference_images: list = None,
    negative_prompt: str = None
) -> Dict[str, Any]:
    """
    Generate an image using Gemini 2.5 Flash Image (Nano Banana)

    This uses Google's conversational image generation model that's available
    on the free tier of the Gemini API (no Vertex AI required!)

    Args:
        prompt: Text description of the image to generate
        aspect_ratio: Image aspect ratio (supports: "1:1", "16:9", "9:16", "4:5")
        number_of_images: Number of images to generate (note: may generate multiple in one call)
        reference_images: List of PIL Image objects to use as visual reference (optional)
        negative_prompt: What NOT to include in the image (optional)

    Returns:
        Dictionary with:
        - success: bool
        - image_bytes: bytes (if successful, first image)
        - all_images: list of bytes (if multiple images)
        - error: str (if failed)
        - prompt: str (the original prompt)
    """
    try:
        import google.generativeai as genai
        from PIL import Image

        # Configure API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {
                'success': False,
                'error': 'GOOGLE_API_KEY not found in environment variables'
            }

        genai.configure(api_key=api_key)

        print(f"🎨 Generating image with Gemini 2.5 Flash Image...")
        print(f"   Prompt: {prompt[:100]}...")
        if reference_images:
            print(f"   Reference images: {len(reference_images)}")
        if negative_prompt:
            print(f"   Negative prompt: {negative_prompt[:50]}...")

        # Use Gemini 2.5 Flash Image (conversational image generation)
        # Model: gemini-2.5-flash-image-preview (aka "Nano Banana")
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')

        # Create a generation prompt that requests image output
        generation_prompt = f"Generate an image: {prompt}"

        if aspect_ratio and aspect_ratio != "1:1":
            generation_prompt += f"\nAspect ratio: {aspect_ratio}"

        if negative_prompt:
            generation_prompt += f"\nAvoid: {negative_prompt}"

        # Build content parts for multimodal input
        content_parts = []

        # Add reference images first if provided
        if reference_images and len(reference_images) > 0:
            generation_prompt = f"Using the reference image(s) as inspiration for style and composition, {generation_prompt}"
            for img in reference_images:
                content_parts.append(img)

        # Add the text prompt
        content_parts.append(generation_prompt)

        # Generate content (multimodal if reference images provided)
        response = model.generate_content(content_parts)

        print(f"✅ Gemini API call successful")

        # Extract images from response
        all_image_bytes = []

        if hasattr(response, 'parts'):
            for part in response.parts:
                # Check if this part contains image data
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_bytes = part.inline_data.data
                    all_image_bytes.append(img_bytes)
                    print(f"   ✓ Found image: {len(img_bytes)} bytes")

        # Fallback: Check candidates
        if not all_image_bytes and hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            img_bytes = part.inline_data.data
                            all_image_bytes.append(img_bytes)
                            print(f"   ✓ Found image in candidate: {len(img_bytes)} bytes")

        if not all_image_bytes:
            # Check if there's text response explaining why no image
            text_response = response.text if hasattr(response, 'text') else "Unknown error"
            return {
                'success': False,
                'error': f'No images generated. Model response: {text_response[:200]}',
                'prompt': prompt
            }

        print(f"📸 Successfully extracted {len(all_image_bytes)} image(s)")

        return {
            'success': True,
            'image_bytes': all_image_bytes[0],  # First image
            'all_images': all_image_bytes,  # All images
            'prompt': prompt,
            'count': len(all_image_bytes)
        }

    except ImportError as e:
        return {
            'success': False,
            'error': f'Missing required library: {str(e)}. Run: uv pip install google-generativeai'
        }
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Image generation error: {error_msg}")

        # Provide helpful error messages
        if "quota" in error_msg.lower() or "429" in error_msg or "resource_exhausted" in error_msg.lower():
            error_msg = "API quota exceeded. Free tier has ~10-20 images/day. Upgrade to paid tier for more."
        elif "api key" in error_msg.lower() or "403" in error_msg or "permission" in error_msg.lower():
            error_msg = "Invalid API key or insufficient permissions. Check your GOOGLE_API_KEY in .env file."
        elif "safety" in error_msg.lower() or "blocked" in error_msg.lower():
            error_msg = "Image generation blocked by safety filters. Try a different, less controversial prompt."
        elif "not found" in error_msg.lower() or "404" in error_msg:
            error_msg = "Model not found. The gemini-2.5-flash-image-preview model may not be available yet. Try again later."
        elif "unavailable" in error_msg.lower() or "503" in error_msg:
            error_msg = "Service temporarily unavailable. Try again in a few moments."

        return {
            'success': False,
            'error': error_msg,
            'prompt': prompt
        }


def generate_image_with_style(
    prompt: str,
    style: str = "photorealistic",
    aspect_ratio: str = "1:1",
    reference_images: list = None,
    negative_prompt: str = None
) -> Dict[str, Any]:
    """
    Generate an image with a specific style applied to the prompt

    Args:
        prompt: Base text description
        style: Style to apply (photorealistic, minimalist, illustration, abstract, etc.)
        aspect_ratio: Image aspect ratio
        reference_images: List of PIL Image objects to use as visual reference (optional)
        negative_prompt: What NOT to include in the image (optional)

    Returns:
        Same as generate_image_from_prompt
    """
    style_prompts = {
        "photorealistic": "photorealistic, high quality, detailed, professional photography",
        "minimalist": "minimalist design, clean, simple, modern aesthetic",
        "illustration": "digital illustration, artistic, hand-drawn style",
        "abstract": "abstract art, creative, artistic interpretation",
        "corporate": "professional, corporate style, clean design, business aesthetic",
        "vibrant": "vibrant colors, energetic, bold and colorful",
        "monochrome": "black and white, monochrome, high contrast"
    }

    style_suffix = style_prompts.get(style.lower(), "")
    enhanced_prompt = f"{prompt}. Style: {style_suffix}" if style_suffix else prompt

    return generate_image_from_prompt(
        enhanced_prompt,
        aspect_ratio,
        reference_images=reference_images,
        negative_prompt=negative_prompt
    )
