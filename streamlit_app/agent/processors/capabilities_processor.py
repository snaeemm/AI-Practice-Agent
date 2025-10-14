import json
import os
import time
import sys
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv
from docx import Document
import pandas as pd
import google.generativeai as genai
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Import centralized settings
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import settings

# Debug: List files in directory
print(f"📁 Checking directory: {settings.FILES_DIR}")
if settings.FILES_DIR.exists():
    print(f"📄 Available files: {[f.name for f in settings.FILES_DIR.iterdir() if f.is_file()]}")
else:
    print(f"❌ Directory not found: {settings.FILES_DIR}")

api_key = settings.GOOGLE_API_KEY
if not api_key:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env")
genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)

# ------------------ DATA MODELS ------------------ #
class Contact(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    internal_poc: Optional[str] = None

class Capability(BaseModel):
    name: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    capabilities: List[str]
    industry_focus: List[str] = Field(default_factory=list)
    contact: Optional[Contact] = None
    website: Optional[str] = None
    use_cases: Optional[str] = None
    strategic_fit: Optional[str] = None
    past_projects: Optional[str] = None
    reliability_score: Optional[int] = None
    agreement_status: Optional[str] = None
    agreement_type: Optional[str] = None
    notes: Optional[str] = None

class CapabilitiesData(BaseModel):
    granite_mena: List[Capability]
    partners: List[Capability]

# ------------------ HELPERS ------------------ #
def load_company_docx() -> str:
    if not settings.FILES_DIR / "Granite_MENA_Capabilities.docx".exists():
        print(f"⚠️ Company file not found: {settings.FILES_DIR / "Granite_MENA_Capabilities.docx"}")
        return ""
    doc = Document(settings.FILES_DIR / "Granite_MENA_Capabilities.docx")
    text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    print(f"✅ Loaded company text ({len(text)} chars)")
    return text

def load_partner_excel() -> pd.DataFrame:
    file_to_try = settings.FILES_DIR / "Partner Matrix.xlsx"
    if not file_to_try.exists():
        # Try with (1)
        file_to_try = FILES_DIR / "Partner Matrix (1).xlsx"
    if not file_to_try.exists():
        print(f"⚠️ Partner file not found: {settings.FILES_DIR / "Partner Matrix.xlsx"} or alternative")
        return pd.DataFrame()
    df = pd.read_excel(file_to_try, sheet_name="Partners", header=0)
    df = df.fillna("")  # Replace NaN with empty string
    print(f"✅ Loaded {len(df)} partner rows from {file_to_try}")
    return df

def safe_generate_content(model, prompt, max_retries: int = 2, **kwargs) -> Optional[str]:
    """Direct synchronous API call with retry logic."""
    for retry in range(max_retries):
        try:
            response = model.generate_content(prompt, **kwargs)
            if response and response.candidates:
                candidate = response.candidates[0]
                if candidate.content.parts:
                    return candidate.content.parts[0].text.strip()
            print(f"⚠️ No valid text (attempt {retry+1})")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ API error (attempt {retry+1}): {e}")
            time.sleep(0.5)
    return None

def clean_json_str(text: str) -> str:
    """Clean and extract JSON from LLM response, removing control characters."""
    import re

    text = text.strip()
    if text.startswith("```json"):
        text = text[7:].lstrip()
    if text.endswith("```"):
        text = text[:-3].rstrip()

    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith("```"):
            continue
        # Remove control characters (except newlines, tabs, carriage returns)
        line = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', line)
        cleaned_lines.append(line.rstrip())

    text = "\n".join(cleaned_lines).strip()

    # Additional cleaning for common problematic characters
    text = text.replace('\u2013', '-')  # en dash
    text = text.replace('\u2014', '-')  # em dash
    text = text.replace('\u2018', "'")  # left single quote
    text = text.replace('\u2019', "'")  # right single quote
    text = text.replace('\u201C', '"')  # left double quote
    text = text.replace('\u201D', '"')  # right double quote
    text = text.replace('\u2022', '*')  # bullet point

    # Attempt to fix unterminated strings by adding closing quote if missing at end
    if text.count('"') % 2 != 0:
        text += '"'
    return text

def process_partner_chunk(chunk_data: tuple, max_retries: int = 3) -> List[Capability]:
    """Process a single chunk of partner data with automatic retries."""
    i, chunk = chunk_data
    chunk_size = len(chunk)
    def clean_cell_data(x):
        if isinstance(x, str):
            import re
            # Replace newlines and carriage returns with spaces
            x = x.replace("\n", " ").replace("\r", " ")
            # Escape quotes for CSV
            x = x.replace('"', '""')
            # Remove control characters that cause JSON parsing issues
            x = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', x)
            # Replace problematic Unicode characters
            x = x.replace('\u2013', '-').replace('\u2014', '-')
            x = x.replace('\u2018', "'").replace('\u2019', "'")
            x = x.replace('\u201C', '"').replace('\u201D', '"')
            x = x.replace('\u2022', '*')
        return x

    chunk = chunk.map(clean_cell_data)
    table = chunk.to_csv(index=False)

    prompt = f"""
You are an AI knowledge extractor.

SOURCE: Partner Matrix CSV:
{table}

TASK:
- Extract each partner as JSON object.
- 'name' = Name or Partner Name column
- 'website' = Website column
- 'category' = Category column
- 'sub_category' = Sub-Category column
- 'capabilities' = Core Offering / Capability column as array
- 'industry_focus' = Industry Focus column split by ',' or ';'
- 'use_cases' = Potential Use Cases column
- 'strategic_fit' = Strategic Fit column
- 'past_projects' = Past or ongoing projects column
- 'reliability_score' = Reliability score (1 -5) column as an integer
- 'agreement_status' = Agreement in place? column
- 'agreement_type' = Agreement Type column
- 'notes' = Notes column
- 'contact' = {{ "email": Key Partner Contact column, "internal_poc": Internal PoC column }}

Output ONLY valid JSON array
"""

    for attempt in range(max_retries):
        attempt_num = attempt + 1
        print(f"📤 Processing chunk {i}-{i+chunk_size} ({chunk_size} partners) - Attempt {attempt_num}")

        json_str = safe_generate_content(
            gemini_model,
            [prompt],
            generation_config={"temperature": 0.1}
        )

        if not json_str:
            print(f"⚠️ Chunk {i}-{i+chunk_size} failed API call - Attempt {attempt_num}")
            if attempt_num < max_retries:
                print(f"🔄 Retrying chunk {i}-{i+chunk_size}...")
                time.sleep(1)  # Brief pause before retry
                continue
            else:
                print(f"❌ Chunk {i}-{i+chunk_size} failed after {max_retries} attempts")
                return []

        json_str = clean_json_str(json_str)
        try:
            chunk_data = json.loads(json_str)
            caps = []
            for p in chunk_data:
                # Ensure `capabilities` is a list
                if 'capabilities' in p and isinstance(p['capabilities'], str):
                    p['capabilities'] = [p['capabilities']]
                # Ensure `industry_focus` is a list
                if 'industry_focus' in p:
                    if isinstance(p['industry_focus'], str):
                        p['industry_focus'] = [s.strip() for s in p['industry_focus'].split(',')]
                    elif p['industry_focus'] is None:
                        p['industry_focus'] = []
                # Ensure `use_cases` is a string
                if 'use_cases' in p and isinstance(p['use_cases'], list):
                    p['use_cases'] = ", ".join(p['use_cases'])
                # Ensure `past_projects` is a string
                if 'past_projects' in p and isinstance(p['past_projects'], list):
                    p['past_projects'] = ", ".join(p['past_projects'])
                # Ensure `notes` is a string
                if 'notes' in p and isinstance(p['notes'], list):
                    p['notes'] = ", ".join(p['notes'])
                # Ensure `reliability_score` is an integer
                if 'reliability_score' in p and p['reliability_score'] is not None:
                    try:
                        p['reliability_score'] = int(p['reliability_score'])
                    except (ValueError, TypeError):
                        p['reliability_score'] = None
                caps.append(Capability(**p))
            print(f"✅ Chunk {i}-{i+chunk_size} processed successfully ({len(caps)} partners)")
            return caps

        except json.JSONDecodeError as e:
            print(f"❌ Chunk {i}-{i+chunk_size} JSON parse error (Attempt {attempt_num}): {e}")
            if attempt_num < max_retries:
                print(f"🔄 Retrying chunk {i}-{i+chunk_size} due to JSON error...")
                time.sleep(1)  # Brief pause before retry
                continue
            else:
                print(f"❌ Chunk {i}-{i+chunk_size} failed JSON parsing after {max_retries} attempts")
                return []

    return []  # Fallback (should never reach here)

def chunked_partner_json(df: pd.DataFrame, chunk_size: int = 15, max_workers: int = 3) -> List[Capability]:
    """Process partner data in parallel chunks."""
    print(f"🚀 Processing {len(df)} partners in chunks of {chunk_size} with {max_workers} concurrent workers")

    # Create chunks
    chunks = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size].copy()
        chunks.append((i, chunk))

    all_caps = []

    # Process chunks concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(process_partner_chunk, chunk): chunk for chunk in chunks}

        for future in as_completed(future_to_chunk):
            chunk_caps = future.result()
            all_caps.extend(chunk_caps)

    print(f"✅ Processed all chunks: {len(all_caps)} total partners extracted")
    return all_caps


# ------------------ MAIN EXTRACTION ------------------ #
def extract_capabilities_to_json() -> CapabilitiesData:
    print("🚀 Extracting capabilities...")
    start = time.time()
    company_text = load_company_docx()
    partner_df = load_partner_excel()
    if not company_text and partner_df.empty:
        print("❌ Nothing to process")
        return CapabilitiesData(granite_mena=[], partners=[])

    # Granite MENA extraction
    prompt_company = f"""
You are an AI knowledge extractor.

SOURCE: Company Capabilities docx:
{company_text}

TASK:
- Extract each service as a JSON object.
- 'name' = heading
- 'category' = inferred from the service heading
- 'capabilities' = bullet points or core offerings
- 'industry_focus' = inferred from context or keywords.
- 'website' = null
- 'sub_category' = null
- 'use_cases' = null
- 'strategic_fit' = null
- 'past_projects' = null
- 'reliability_score' = null
- 'agreement_status' = null
- 'agreement_type' = null
- 'notes' = null
- 'contact' = null

Output ONLY a valid JSON array of services.
"""
    json_company = safe_generate_content(
        gemini_model,
        [prompt_company],
        generation_config={"temperature": 0.1}
    )
    granite_services = []
    if json_company:
        json_company = clean_json_str(json_company)
        try:
            granite_services_raw = json.loads(json_company)
            for s in granite_services_raw:
                if 'industry_focus' in s and isinstance(s['industry_focus'], str):
                    s['industry_focus'] = [s['industry_focus']]
                if 'industry_focus' in s and s['industry_focus'] is None:
                    s['industry_focus'] = []
                granite_services.append(Capability(**s))
        except json.JSONDecodeError as e:
            print(f"❌ Granite JSON parse error: {e}. Skipping extraction for company capabilities.")
            
    # Partners extraction (chunked)
    partners_list = chunked_partner_json(partner_df)

    # Final JSON
    capabilities = CapabilitiesData(granite_mena=granite_services, partners=partners_list)
    with open(settings.CAPABILITIES_JSON, 'w', encoding='utf-8') as f:
        json.dump(capabilities.model_dump(), f, indent=4)
    print(f"✅ Saved final JSON → {settings.CAPABILITIES_JSON} in {time.time()-start:.2f}s")
    return capabilities

def load_capabilities_json() -> Optional[CapabilitiesData]:
    """Load capabilities from existing JSON file."""
    if not settings.CAPABILITIES_JSON.exists():
        print(f"⚠️ Capabilities JSON not found: {settings.CAPABILITIES_JSON}")
        return None
    try:
        with open(settings.CAPABILITIES_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return CapabilitiesData(**data)
    except Exception as e:
        print(f"❌ Error loading capabilities JSON: {e}")
        return None

if __name__ == "__main__":
    extract_capabilities_to_json()