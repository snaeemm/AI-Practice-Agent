import os
from pathlib import Path
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv
from docx import Document
from pptx import Presentation

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.doc', '.xls', '.ppt']
MAX_FILE_SIZE_MB = 500

def detect_document_type(text: str) -> str:
    """
    Detect document type from extracted text using Gemini.

    Args:
        text: Extracted document text

    Returns:
        Document type: "RFP", "Meeting Notes", or "Other"
    """
    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        prompt = """You must classify this document into EXACTLY ONE of these three categories:

1. RFP - Request for Proposal, tender, RFQ, business opportunity, procurement document
2. Meeting Notes - Meeting minutes, call notes, discussion summary, stakeholder notes
3. Other - Any other type of document

Respond with ONLY the exact category name from above, nothing else. No explanation.

Document text (first 2000 characters):
{text}"""

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt.format(text=text[:2000])]  # Use first 2000 chars for quick classification
        )

        raw_response = response.text.strip() if response and hasattr(response, 'text') else "Other"

        # More flexible parsing - look for keywords in the response
        if "RFP" in raw_response and "Meeting" not in raw_response:
            doc_type = "RFP"
        elif "Meeting" in raw_response:
            doc_type = "Meeting Notes"
        elif "Other" in raw_response:
            doc_type = "Other"
        else:
            # Last resort: check first word
            first_word = raw_response.split()[0] if raw_response.split() else ""
            if first_word in ["RFP", "Meeting", "Other"]:
                doc_type = first_word if first_word != "Meeting" else "Meeting Notes"
            else:
                print(f"⚠️ Unexpected response from document type detection: '{raw_response}'")
                doc_type = "Other"

        print(f"📋 Detected document type: {doc_type}")
        return doc_type

    except Exception as e:
        print(f"⚠️ Failed to detect document type: {e}")
        return "Other"


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file using python-docx library.

    Args:
        file_path: Path to the DOCX file

    Returns:
        Extracted text content
    """
    try:
        doc = Document(file_path)
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    row_text.append(cell.text)
                if any(row_text):
                    text_parts.append(" | ".join(row_text))

        return "\n".join(text_parts)
    except Exception as e:
        raise Exception(f"Failed to extract DOCX: {str(e)}")


def extract_text_from_pptx(file_path: str) -> str:
    """
    Extract text from a PPTX file using python-pptx library.

    Args:
        file_path: Path to the PPTX file

    Returns:
        Extracted text content
    """
    try:
        prs = Presentation(file_path)
        text_parts = []

        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = []

            # Extract text from all shapes in the slide
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

                # Also check for tables in the slide
                if shape.has_table:
                    table = shape.table
                    for row in table.rows:
                        row_text = []
                        for cell in row.cells:
                            if cell.text.strip():
                                row_text.append(cell.text)
                        if row_text:
                            slide_text.append(" | ".join(row_text))

            # Add slide content with a separator
            if slide_text:
                text_parts.append(f"--- Slide {slide_num} ---")
                text_parts.extend(slide_text)
                text_parts.append("")  # Empty line between slides

        return "\n".join(text_parts)
    except Exception as e:
        raise Exception(f"Failed to extract PPTX: {str(e)}")


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using pdfplumber library.
    Handles tables and preserves document structure.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text content with tables formatted as pipe-separated text
    """
    try:
        import pdfplumber

        text_parts = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract regular text from page
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text)

                # Extract tables and format as text
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table:
                            # Format each row with pipe separators
                            for row in table:
                                if row:
                                    # Convert None to empty string and join
                                    row_text = " | ".join(str(cell) if cell is not None else "" for cell in row)
                                    if row_text.strip():
                                        text_parts.append(row_text)

        return "\n".join(text_parts)
    except Exception as e:
        raise Exception(f"Failed to extract PDF: {str(e)}")


def extract_document_text(file_path: str) -> Dict[str, Any]:
    """
    Extract text from PDF, DOCX, XLSX, PPTX, or TXT files.

    Extraction methods:
    - PDF: Uses pdfplumber (local, fast, supports tables)
    - DOCX: Uses python-docx (local, fast, supports tables)
    - PPTX: Uses python-pptx (local, fast)
    - TXT: Direct file read (local, instant)
    - XLSX: Uses Gemini File API (slower, but necessary for complex formats)

    Args:
        file_path: Path to the document file

    Returns:
        Dictionary with:
        - status: 'success' or 'failed'
        - text: Extracted text content (if success)
        - file_uri: Gemini File API URI (if XLSX) or None (for local extraction)
        - error: Error message (if failed)
        - filename: Original filename
        - document_type: "RFP", "Meeting Notes", or "Other" (if detected)
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

        # Handle DOCX files directly using python-docx
        if file_ext == '.docx':
            print(f"📄 Extracting text from {path.name} using python-docx...")
            try:
                text_content = extract_text_from_docx(file_path)
                if not text_content.strip():
                    return {
                        'status': 'failed',
                        'error': 'No text could be extracted from the document',
                        'filename': path.name
                    }

                print(f"✅ Extracted {len(text_content)} characters from {path.name}")
                return {
                    'status': 'success',
                    'text': text_content,
                    'file_uri': None,
                    'filename': path.name
                }
            except Exception as e:
                return {
                    'status': 'failed',
                    'error': f'DOCX extraction error: {str(e)}',
                    'filename': path.name
                }

        # Handle PPTX files directly using python-pptx
        if file_ext == '.pptx' or file_ext == '.ppt':
            print(f"📊 Extracting text from {path.name} using python-pptx...")
            try:
                text_content = extract_text_from_pptx(file_path)
                if not text_content.strip():
                    return {
                        'status': 'failed',
                        'error': 'No text could be extracted from the presentation',
                        'filename': path.name
                    }

                print(f"✅ Extracted {len(text_content)} characters from {path.name}")

                # Detect document type from extracted text
                document_type = detect_document_type(text_content)

                return {
                    'status': 'success',
                    'text': text_content,
                    'file_uri': None,
                    'filename': path.name,
                    'document_type': document_type
                }
            except Exception as e:
                return {
                    'status': 'failed',
                    'error': f'PPTX extraction error: {str(e)}',
                    'filename': path.name
                }

        # Handle PDF files directly using pdfplumber
        if file_ext == '.pdf':
            print(f"📄 Extracting text from {path.name} using pdfplumber...")
            try:
                text_content = extract_text_from_pdf(file_path)
                if not text_content.strip():
                    return {
                        'status': 'failed',
                        'error': 'No text could be extracted from the PDF',
                        'filename': path.name
                    }

                print(f"✅ Extracted {len(text_content)} characters from {path.name}")

                # Detect document type from extracted text
                document_type = detect_document_type(text_content)

                return {
                    'status': 'success',
                    'text': text_content,
                    'file_uri': None,  # No Gemini upload needed
                    'filename': path.name,
                    'document_type': document_type
                }
            except Exception as e:
                return {
                    'status': 'failed',
                    'error': f'PDF extraction error: {str(e)}',
                    'filename': path.name
                }

        # For XLSX and other formats, use Gemini File API
        print(f"📤 Uploading {path.name} to Gemini File API...")
        uploaded_file = client.files.upload(file=str(path))

        print(f"🤖 Extracting text from {path.name}...")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        prompt = """Extract ALL text content from this document AND classify its type.

Instructions for extraction:
- Extract all readable text, preserving structure where possible
- Include headings, paragraphs, lists, and table content
- Maintain logical flow and organization
- Do not add commentary or interpretation

Classification:
- Classify document as ONE of: "RFP" (Request for Proposal/tender), "Meeting Notes" (discussion/call notes), or "Other"

Output format:
[DOCUMENT_TYPE]
<type: RFP, Meeting Notes, or Other>
[/DOCUMENT_TYPE]

[EXTRACTED_TEXT]
<complete text content here>
[/EXTRACTED_TEXT]"""

        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, uploaded_file]
        )

        response_text = response.text if response and hasattr(response, 'text') else ""

        # Parse document type from response
        document_type = "Other"
        extracted_text = ""

        try:
            # Extract document type
            if "[DOCUMENT_TYPE]" in response_text and "[/DOCUMENT_TYPE]" in response_text:
                type_section = response_text.split("[DOCUMENT_TYPE]")[1].split("[/DOCUMENT_TYPE]")[0].strip()
                # More flexible parsing - check if any of the types are mentioned
                if "RFP" in type_section and "Meeting" not in type_section:
                    document_type = "RFP"
                elif "Meeting Notes" in type_section or "Meeting" in type_section:
                    document_type = "Meeting Notes"
                elif "Other" in type_section:
                    document_type = "Other"
                else:
                    # Fallback: try exact match
                    if type_section in ["RFP", "Meeting Notes", "Other"]:
                        document_type = type_section
                    else:
                        print(f"⚠️ Could not parse document type: '{type_section}', will auto-detect from text")
                        document_type = None  # Mark for auto-detection below

            # Extract text
            if "[EXTRACTED_TEXT]" in response_text and "[/EXTRACTED_TEXT]" in response_text:
                extracted_text = response_text.split("[EXTRACTED_TEXT]")[1].split("[/EXTRACTED_TEXT]")[0].strip()
            else:
                # If no tagged sections, assume the whole response is text
                extracted_text = response_text

        except Exception as e:
            print(f"⚠️ Error parsing response: {e}")
            print(f"Response text: {response_text[:500]}")
            extracted_text = response_text
            document_type = None  # Mark for auto-detection below

        # If document type detection failed from structured format, use auto-detection
        if document_type is None and extracted_text:
            print(f"🔍 Auto-detecting document type from extracted text...")
            document_type = detect_document_type(extracted_text)

        if not extracted_text.strip():
            client.files.delete(name=uploaded_file.name)
            return {
                'status': 'failed',
                'error': 'No text could be extracted from the document',
                'filename': path.name
            }

        print(f"✅ Extracted {len(extracted_text)} characters from {path.name}")
        print(f"📋 Document type: {document_type}")

        return {
            'status': 'success',
            'text': extracted_text,
            'file_uri': uploaded_file.name,
            'filename': path.name,
            'document_type': document_type
        }

    except Exception as e:
        return {
            'status': 'failed',
            'error': f'Extraction error: {str(e)}',
            'filename': Path(file_path).name if file_path else 'unknown'
        }


def extract_document_metadata(text: str, document_type: str, db=None, existing_rfps: list = None, existing_briefs: list = None) -> Dict[str, Any]:
    """
    Extract metadata from document text based on its type using Gemini, and check for duplicates.

    Args:
        text: The document text
        document_type: "RFP", "Meeting Notes", or "Other"
        db: DatabaseManager instance (OPTIMIZED - preferred method for duplicate detection)
        existing_rfps: DEPRECATED - Use db parameter instead for better performance
        existing_briefs: DEPRECATED - Use db parameter instead for better performance

    Returns:
        Dictionary with:
        - document_type: Type of document
        - title: Extracted title/subject string
        - matching_id: RFP ID or brief ID if duplicate found, else None
        - entity_type: "rfp" or "brief" (indicates what matching_id refers to)
        - has_qualification: Boolean (for RFPs only)
        - has_bid_plan: Boolean (for RFPs only)
    """
    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        if document_type == "RFP":
            # Optimized: Extract title first, then use database lookup
            prompt = f"""Extract the RFP/project title from this document.

Instructions:
- Look for the main project title, RFP name, or opportunity name
- If there's a client name and project, format as: "Client Name - Project Title"
- Keep it concise (under 100 characters)

Document text:
{{text}}

Response format:
Title: [extracted title]"""

            response = client.models.generate_content(
                model=model_name,
                contents=[prompt.format(text=text[:3000])]
            )

            response_text = response.text.strip() if response and hasattr(response, 'text') else ""

            # Parse response
            title = "Untitled RFP"
            for line in response_text.split('\n'):
                if line.startswith('Title:'):
                    title = line.replace('Title:', '').strip().replace('"', '').replace("'", "")
                    break

            print(f"📋 Extracted RFP title: {title}")

            # Optimized duplicate detection using database-level normalized lookup
            matching_id = None
            has_qualification = False
            has_bid_plan = False

            if db:
                # Use optimized database method (much faster than loading all RFPs)
                matching_id = db.find_rfp_by_normalized_title(title)
                if matching_id:
                    print(f"🔄 Found duplicate RFP: {matching_id}")
                    # Get status using optimized single-query method
                    rfp_data = db.get_rfp_upload_status(matching_id)
                    if rfp_data:
                        has_qualification = rfp_data.get('has_qualification', False)
                        has_bid_plan = rfp_data.get('has_bid_plan', False)

            return {
                'document_type': document_type,
                'title': title,
                'matching_id': matching_id,
                'entity_type': 'rfp',
                'has_qualification': has_qualification,
                'has_bid_plan': has_bid_plan
            }

        elif document_type == "Meeting Notes":
            # Optimized: Extract client name first, then use database lookup
            prompt = f"""Extract the client name and meeting subject from these meeting notes.

Instructions:
- Extract the client/organization name
- Extract the meeting subject or main topic
- Format as: "Client Name - Meeting Subject"
- Keep it concise (under 100 characters)

Meeting notes text:
{{text}}

Response format:
Title: [client name - meeting subject]
Client Name: [just the client/organization name]"""

            response = client.models.generate_content(
                model=model_name,
                contents=[prompt.format(text=text[:3000])]
            )

            response_text = response.text.strip() if response and hasattr(response, 'text') else ""

            # Parse response
            title = "Untitled Meeting Notes"
            client_name = None

            for line in response_text.split('\n'):
                if line.startswith('Title:'):
                    title = line.replace('Title:', '').strip().replace('"', '').replace("'", "")
                elif line.startswith('Client Name:'):
                    client_name = line.replace('Client Name:', '').strip().replace('"', '').replace("'", "")

            print(f"📝 Extracted meeting subject: {title}")

            # Optimized duplicate detection using database-level normalized lookup
            matching_id = None
            if db and client_name:
                # Use optimized database method (much faster than loading all briefs)
                matching_id = db.find_brief_by_normalized_title(client_name)
                if matching_id:
                    print(f"🔄 Found duplicate brief: {matching_id}")

            return {
                'document_type': document_type,
                'title': title,
                'matching_id': matching_id,
                'entity_type': 'brief',
                'has_qualification': False,
                'has_bid_plan': False
            }

        else:  # "Other"
            # Extract general title
            prompt = f"""Extract a concise title or description for this document.

Instructions:
- Identify the main topic or title of the document
- Keep it concise (under 100 characters)
- Do not include any duplicate checking information

Document text:
{{text}}

Response format:
Title: [document title or subject]"""

            response = client.models.generate_content(
                model=model_name,
                contents=[prompt.format(text=text[:2000])]
            )

            response_text = response.text.strip() if response and hasattr(response, 'text') else ""

            # Parse response
            title = "Untitled Document"
            for line in response_text.split('\n'):
                if line.startswith('Title:'):
                    title = line.replace('Title:', '').strip().replace('"', '').replace("'", "")
                    break

            print(f"📄 Extracted document title: {title}")

            return {
                'document_type': document_type,
                'title': title,
                'matching_id': None,
                'entity_type': 'other',
                'has_qualification': False,
                'has_bid_plan': False
            }

    except Exception as e:
        print(f"⚠️ Failed to extract metadata: {e}")
        return {
            'document_type': document_type,
            'title': "Untitled Document",
            'matching_id': None,
            'entity_type': 'other',
            'has_qualification': False,
            'has_bid_plan': False
        }


def extract_rfp_title(text: str, existing_rfps: list = None) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility. Use extract_document_metadata() instead.

    Deprecated: This function is kept for backward compatibility only.
    Use extract_document_metadata(text, "RFP", existing_rfps) instead.
    """
    result = extract_document_metadata(text, "RFP", existing_rfps=existing_rfps)
    return {
        'title': result['title'],
        'matching_rfp_id': result['matching_id']
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
