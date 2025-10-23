"""
Smart Profile Extractor
Extracts professional profile information from resumes, CVs, and bios using Gemini AI
"""

import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
import tempfile
from pathlib import Path

from agent.file_processor import extract_document_text, extract_text_from_docx

load_dotenv()


def extract_profile_from_document(
    file_bytes: bytes,
    filename: str,
    file_type: str
) -> Dict[str, Any]:
    """
    Extract professional profile information from uploaded resume/bio document

    Args:
        file_bytes: Raw file bytes
        filename: Original filename
        file_type: File extension (pdf, docx, txt)

    Returns:
        Dictionary with:
        - success: bool
        - extracted_data: Dict with profile fields (if successful)
        - error: str (if failed)
        - suggestions: List of detected elements for user review
    """
    try:
        print(f"📄 Starting smart profile extraction from {filename}...")

        # Step 1: Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            # Step 2: Extract text from document
            print(f"📤 Extracting text from {file_type} file...")

            if file_type == 'txt':
                # Direct text read
                text_content = file_bytes.decode('utf-8', errors='ignore')
                extraction_result = {
                    'status': 'success',
                    'text': text_content,
                    'filename': filename
                }
            else:
                # Use existing file processor
                extraction_result = extract_document_text(tmp_path)

            if extraction_result['status'] != 'success':
                return {
                    'success': False,
                    'error': f"Failed to extract text: {extraction_result.get('error', 'Unknown error')}"
                }

            extracted_text = extraction_result['text']

            if not extracted_text or len(extracted_text.strip()) < 50:
                return {
                    'success': False,
                    'error': 'Document contains too little text to extract meaningful information'
                }

            print(f"✅ Extracted {len(extracted_text)} characters of text")

            # Step 3: Use Gemini to extract structured profile data
            print(f"🤖 Analyzing document with Gemini AI...")

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return {
                    'success': False,
                    'error': 'GOOGLE_API_KEY not found in environment variables'
                }

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash-preview-0514')

            prompt = f"""Analyze this resume/professional bio and extract structured information for a LinkedIn marketing profile.

DOCUMENT TEXT:
{extracted_text[:4000]}

Extract the following information and return as valid JSON:

{{
  "full_name": "Person's full name (string or null)",
  "role_title": "Current job title or professional role (string or null)",
  "industry": "Primary industry/sector (Technology, Finance, Healthcare, etc.) (string or null)",
  "expertise_areas": ["List of 3-7 key skills/expertise areas (array of strings)"],
  "personal_bio": "Concise professional bio in 150-300 characters (string or null)",
  "target_audience": "Inferred target audience based on role (e.g., 'Tech executives', 'Startup founders') (string or null)",
  "content_themes": ["3-5 content themes based on expertise (array of strings)"],
  "brand_voice": "Inferred communication style from tone (Professional/Conversational/Innovative/etc.) (string or null)",
  "company_info": "Current company name if mentioned (string or null)",
  "confidence_score": 0.0-1.0,
  "suggestions": ["List of notable achievements or themes to consider for content strategy"]
}}

EXTRACTION GUIDELINES:
- Be accurate - only extract what's clearly stated
- Use null for fields you cannot determine
- Infer target_audience and content_themes intelligently from role/expertise
- confidence_score: How confident you are in the extraction (0.0 = very uncertain, 1.0 = very confident)
- personal_bio: Craft a concise, third-person professional bio (150-300 chars)
- brand_voice: Analyze writing style if present, otherwise infer from role (e.g., CEO = "Inspirational, Authoritative")

Return ONLY valid JSON, no markdown code blocks."""

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print(f"✅ Received Gemini response ({len(response_text)} chars)")

            # Step 4: Parse JSON response
            extracted_data = _parse_gemini_profile_response(response_text)

            if not extracted_data:
                return {
                    'success': False,
                    'error': 'Failed to parse AI response. Please fill profile manually.'
                }

            # Validate extraction quality
            confidence = extracted_data.get('confidence_score', 0.0)

            if confidence < 0.3:
                return {
                    'success': False,
                    'error': 'Low confidence extraction. Document may not be a resume/bio. Please fill manually.'
                }

            print(f"🎯 Extraction successful (confidence: {confidence:.2f})")
            print(f"   Found: {extracted_data.get('full_name', 'N/A')}, {extracted_data.get('role_title', 'N/A')}")

            return {
                'success': True,
                'extracted_data': extracted_data,
                'confidence_score': confidence,
                'suggestions': extracted_data.get('suggestions', [])
            }

        finally:
            # Cleanup temp file
            try:
                Path(tmp_path).unlink()
            except:
                pass

    except Exception as e:
        print(f"❌ Smart profile extraction error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': f'Extraction failed: {str(e)}'
        }


def _parse_gemini_profile_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse Gemini's JSON response for profile extraction

    Args:
        response_text: Raw response from Gemini

    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        # Remove markdown code blocks if present
        cleaned = response_text.strip()

        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]

        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Parse JSON
        result = json.loads(cleaned)

        # Validate required structure
        if not isinstance(result, dict):
            print("⚠️ Response is not a dictionary")
            return None

        # Ensure confidence_score exists
        if 'confidence_score' not in result:
            result['confidence_score'] = 0.5

        return result

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"   Response text: {response_text[:300]}...")
        return None
    except Exception as e:
        print(f"❌ Unexpected error parsing response: {e}")
        return None


def apply_extracted_data_to_session(
    extracted_data: Dict[str, Any],
    session_data: Dict[str, Any],
    profile_type: str = 'personal'
) -> Dict[str, Any]:
    """
    Apply extracted data to onboarding session state

    Args:
        extracted_data: Data extracted from document
        session_data: Current session_state.onboarding_data
        profile_type: 'personal' or 'company'

    Returns:
        Updated session_data dictionary
    """
    updated_data = session_data.copy()

    # Map extracted fields to session fields
    field_mapping = {
        'role_title': 'role_title',
        'industry': 'industry',
        'expertise_areas': 'expertise_areas',
        'personal_bio': 'personal_bio',
        'target_audience': 'target_audience',
        'content_themes': 'content_themes',
        'brand_voice': 'brand_voice'
    }

    for extracted_key, session_key in field_mapping.items():
        if extracted_key in extracted_data and extracted_data[extracted_key]:
            # Only update if not already set or if extracted value is better
            if session_key not in updated_data or not updated_data[session_key]:
                updated_data[session_key] = extracted_data[extracted_key]

    # Generate profile name from extracted data if not set
    if 'profile_name' not in updated_data or not updated_data['profile_name']:
        name = extracted_data.get('full_name', '')
        if name:
            if profile_type == 'personal':
                updated_data['profile_name'] = f"{name} - Personal"
            else:
                company = extracted_data.get('company_info', '')
                if company:
                    updated_data['profile_name'] = f"{company} Marketing"
                else:
                    updated_data['profile_name'] = f"{name} - {profile_type.title()}"

    return updated_data
