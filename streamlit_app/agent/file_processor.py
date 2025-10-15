import os
from pathlib import Path
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.doc', '.xls', '.ppt']
MAX_FILE_SIZE_MB = 15

def extract_document_text(file_path: str) -> Dict[str, Any]:
    """
    Extract text from PDF, DOCX, XLSX, PPTX, or TXT files using Gemini File API.

    Args:
        file_path: Path to the document file

    Returns:
        Dictionary with:
        - status: 'success' or 'failed'
        - text: Extracted text content (if success)
        - file_uri: Gemini File API URI (if success)
        - error: Error message (if failed)
        - filename: Original filename
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                'status': 'failed',
                'error': f'File not found: {file_path}',
                'filename': path.name
            }

        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return {
                'status': 'failed',
                'error': f'File too large: {file_size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)',
                'filename': path.name
            }

        file_ext = path.suffix.lower()
        if file_ext not in SUPPORTED_EXTENSIONS:
            return {
                'status': 'failed',
                'error': f'Unsupported file type: {file_ext}',
                'filename': path.name
            }

        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()

            return {
                'status': 'success',
                'text': text_content,
                'file_uri': None,
                'filename': path.name
            }

        print(f"📤 Uploading {path.name} to Gemini File API...")
        uploaded_file = client.files.upload(file=str(path))

        print(f"🤖 Extracting text from {path.name}...")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        prompt = """Extract ALL text content from this document.

Instructions:
- Extract all readable text, preserving structure where possible
- Include headings, paragraphs, lists, and table content
- Maintain logical flow and organization
- Do not add commentary or interpretation
- Return only the extracted text

Output the complete text content:"""

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, uploaded_file]
        )

        extracted_text = response.text if response and hasattr(response, 'text') else ""

        if not extracted_text.strip():
            client.files.delete(name=uploaded_file.name)
            return {
                'status': 'failed',
                'error': 'No text could be extracted from the document',
                'filename': path.name
            }

        print(f"✅ Extracted {len(extracted_text)} characters from {path.name}")

        return {
            'status': 'success',
            'text': extracted_text,
            'file_uri': uploaded_file.name,
            'filename': path.name
        }

    except Exception as e:
        return {
            'status': 'failed',
            'error': f'Extraction error: {str(e)}',
            'filename': Path(file_path).name if file_path else 'unknown'
        }


def extract_rfp_title(text: str, existing_rfps: list = None) -> Dict[str, Any]:
    """
    Extract RFP title/name from document text using Gemini, and check for duplicates.

    Args:
        text: The RFP document text
        existing_rfps: List of existing RFPs from database with rfp_id, client_name, project_title

    Returns:
        Dictionary with:
        - title: Extracted title string
        - matching_rfp_id: RFP ID if duplicate found, else None
    """
    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Build existing RFPs list for prompt
        existing_list = ""
        if existing_rfps:
            existing_list = "\n\n### EXISTING RFPs IN DATABASE:\n"
            for rfp in existing_rfps[:50]:  # Limit to 50 most recent
                existing_list += f"- ID: {rfp.get('rfp_id')} | Client: {rfp.get('client_name')} | Project: {rfp.get('project_title')}\n"

        prompt = f"""Extract the RFP/project title from this document and check for duplicates.

Instructions:
- Look for the main project title, RFP name, or opportunity name
- If there's a client name and project, format as: "Client Name - Project Title"
- Keep it concise (under 100 characters)

{existing_list}

**CRITICAL:** If this RFP matches ANY of the existing RFPs above (same client and project), return the matching RFP ID.

Document text:
{{text}}

Response format:
Title: [extracted title]
Matching RFP ID: [rfp_id if duplicate, otherwise "None"]"""

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt.format(text=text[:3000])]
        )

        response_text = response.text.strip() if response and hasattr(response, 'text') else ""

        # Parse response
        title = "Untitled RFP"
        matching_rfp_id = None

        for line in response_text.split('\n'):
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip().replace('"', '').replace("'", "")
            elif line.startswith('Matching RFP ID:'):
                match_value = line.replace('Matching RFP ID:', '').strip()
                if match_value.lower() not in ['none', 'null', '']:
                    matching_rfp_id = match_value

        print(f"📋 Extracted RFP title: {title}")
        if matching_rfp_id:
            print(f"🔄 Found duplicate: {matching_rfp_id}")

        return {
            'title': title,
            'matching_rfp_id': matching_rfp_id
        }

    except Exception as e:
        print(f"⚠️ Failed to extract title: {e}")
        return {
            'title': "Untitled RFP",
            'matching_rfp_id': None
        }


def cleanup_gemini_file(file_uri: str):
    """
    Delete a file from Gemini File API.

    Args:
        file_uri: The Gemini File API URI to delete
    """
    try:
        if file_uri:
            client.files.delete(name=file_uri)
            print(f"🗑️ Cleaned up Gemini file: {file_uri}")
    except Exception as e:
        print(f"⚠️ Failed to cleanup Gemini file {file_uri}: {e}")
