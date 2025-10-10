import json
import os
import time
import asyncio
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import google.generativeai as genai
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Constants
FILES_DIR = Path(os.getenv("FILES_DIR", "/mnt/c/Users/Shahzeb/Granite Media/Granite MENA - Operations/2. Practices/AI/Agentic AI for Bid Process/Related Files")).resolve()
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", str(FILES_DIR))).resolve()
RESULTS_DIR.mkdir(exist_ok=True)

QUALIFICATION_MATRIX_FILE = FILES_DIR / "Qualification Matrix [Client  Opp Name]_LL_170125.xlsx"
QUALIFICATION_JSON = FILES_DIR / "qualification_matrix.json"

# Debug: List files in directory
print(f"📁 Checking directory: {FILES_DIR}")
if FILES_DIR.exists():
    print(f"📄 Available files: {[f.name for f in FILES_DIR.iterdir() if f.is_file()]}")
else:
    print(f"❌ Directory not found: {FILES_DIR}")

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env")
genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025"))

# ------------------ DATA MODELS ------------------ #
class QualificationCriterion(BaseModel):
    name: str = Field(..., description="Name of the qualification criterion")
    options: List[str] = Field(..., description="List of scoring options for the criterion")
    scores: List[int] = Field(..., description="Scores corresponding to each option (1-4)")
    weight: float = Field(..., description="Weight for the criterion")

class QualificationMatrix(BaseModel):
    criteria: List[QualificationCriterion] = Field(..., description="List of qualification criteria")
    average_weight: float = Field(..., description="Average weight from the matrix")

# ------------------ HELPERS ------------------ #
def load_qualification_excel() -> pd.DataFrame:
    """Load the Qualification Matrix Excel file."""
    if not QUALIFICATION_MATRIX_FILE.exists():
        print(f"⚠️ Qualification Matrix file not found: {QUALIFICATION_MATRIX_FILE}")
        return pd.DataFrame()
    try:
        df = pd.read_excel(QUALIFICATION_MATRIX_FILE, sheet_name="Qualification Matrix", header=None)
        df = df.fillna("")  # Replace NaN with empty string
        print(f"✅ Loaded {len(df)} rows from {QUALIFICATION_MATRIX_FILE}")
        return df
    except Exception as e:
        print(f"❌ Error loading Qualification Matrix: {e}")
        return pd.DataFrame()

async def try_generate(model, prompt, **kwargs):
    """Generate content with retry logic."""
    max_retries = 2
    for retry in range(max_retries):
        try:
            response = model.generate_content(prompt, **kwargs)
            if response and response.candidates:
                candidate = response.candidates[0]
                if candidate.content.parts:
                    return candidate.content.parts[0].text.strip()
            print(f"⚠️ No valid text (attempt {retry+1})")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ API error (attempt {retry+1}): {e}")
            await asyncio.sleep(0.5)
    return None

def safe_generate_content(model, prompt, timeout: int = 20, **kwargs) -> Optional[str]:
    """Generate content with timeout handling."""
    try:
        return asyncio.run(asyncio.wait_for(try_generate(model, prompt, **kwargs), timeout=timeout))
    except asyncio.TimeoutError:
        print(f"❌ LLM call timed out after {timeout}s")
        return None

def extract_json_from_response(text: str) -> str:
    """Extract and clean JSON from LLM response with better parsing."""
    if not text:
        raise ValueError("Empty response from LLM")

    text = text.strip()

    # Remove markdown code blocks
    if text.startswith("```json"):
        text = text[7:].lstrip()
    elif text.startswith("```"):
        text = text[3:].lstrip()

    if text.endswith("```"):
        text = text[:-3].rstrip()

    # Find JSON object boundaries
    start_idx = text.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in response")

    # Find the matching closing brace
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break

    if end_idx == -1:
        raise ValueError("Incomplete JSON object in response")

    json_str = text[start_idx:end_idx + 1]

    # Basic validation
    if json_str.count('{') != json_str.count('}'):
        raise ValueError("Mismatched braces in JSON")

    return json_str

def validate_matrix_data(matrix_data: dict) -> dict:
    """Validate and clean matrix data before Pydantic validation."""
    if 'criteria' not in matrix_data:
        raise ValueError("Missing 'criteria' field in matrix data")

    if 'average_weight' not in matrix_data:
        raise ValueError("Missing 'average_weight' field in matrix data")

    # Validate criteria structure
    criteria = matrix_data['criteria']
    if not isinstance(criteria, list):
        raise ValueError("'criteria' must be a list")

    if len(criteria) != 9:
        raise ValueError(f"Expected exactly 9 criteria, got {len(criteria)}")

    # Clean and validate each criterion
    for i, criterion in enumerate(criteria):
        if not isinstance(criterion, dict):
            raise ValueError(f"Criterion {i} must be a dictionary")

        # Validate required fields
        required_fields = ['name', 'options', 'scores', 'weight']
        for field in required_fields:
            if field not in criterion:
                raise ValueError(f"Criterion {i} missing required field: {field}")

        # Validate options
        if not isinstance(criterion['options'], list) or len(criterion['options']) != 4:
            raise ValueError(f"Criterion {i} must have exactly 4 options")

        # Validate scores
        if not isinstance(criterion['scores'], list) or criterion['scores'] != [1, 2, 3, 4]:
            criterion['scores'] = [1, 2, 3, 4]  # Fix scores

        # Validate weight
        try:
            criterion['weight'] = float(criterion['weight'])
        except (ValueError, TypeError):
            raise ValueError(f"Criterion {i} weight must be a number")

    # Validate average_weight
    try:
        matrix_data['average_weight'] = float(matrix_data['average_weight'])
    except (ValueError, TypeError):
        raise ValueError("average_weight must be a number")

    return matrix_data

def extract_qualification_matrix_to_json() -> QualificationMatrix:
    """Extract Qualification Matrix from Excel to JSON using LLM with robust validation."""
    print("🚀 Extracting Qualification Matrix...")
    start = time.time()

    df = load_qualification_excel()
    if df.empty:
        raise RuntimeError("❌ Cannot load Excel file - extraction impossible")

    # Convert DataFrame to CSV for LLM processing with better data cleaning
    df_clean = df.iloc[:13].copy()  # Include row 12 (AVERAGE WEIGHTED SCORE)
    df_clean = df_clean.map(lambda x: str(x).replace("\n", " ").replace("\r", " ").replace('"', '""') if isinstance(x, str) else x)
    table = df_clean.to_csv(index=False, header=None)
    print(f"📤 Sending qualification matrix data to LLM:\n{table[:300]}...\n")

    prompt = f"""Extract qualification criteria from this CSV table. Return ONLY valid JSON.

CSV DATA:
{table}

You must extract exactly 9 criteria from rows 3-11. Each criterion has:
- name (column 0)
- options (columns 1-4, exactly 4 options each)
- weight (column 6)
- scores are always [1, 2, 3, 4]

Row 12 contains average_weight value (column 6).

REQUIRED JSON FORMAT (return this exact structure):
{{
  "criteria": [
    {{
      "name": "Revenue Value",
      "options": ["< $500,000", "$500,000 - $999,999", "$999,999 - $5,000,000", "$5,000,000 +"],
      "scores": [1, 2, 3, 4],
      "weight": 1.5
    }}
  ],
  "average_weight": 1.25
}}

Return ONLY the JSON object. No explanations."""

    # Multiple attempts with retry logic
    for attempt in range(3):
        print(f"🔄 LLM attempt {attempt + 1}/3")

        json_str = safe_generate_content(
            gemini_model,
            [prompt],
            generation_config={"temperature": 0.0, "max_output_tokens": 6000},
            timeout=45
        )

        if not json_str:
            print(f"⚠️ Attempt {attempt + 1} failed: No response from LLM")
            continue

        try:
            # Extract JSON from response
            clean_json = extract_json_from_response(json_str)
            print(f"📋 Extracted JSON (attempt {attempt + 1}):\n{clean_json[:200]}...")

            # Parse JSON
            matrix_data = json.loads(clean_json)
            print(f"✅ JSON parsed successfully")

            # Validate structure
            validated_data = validate_matrix_data(matrix_data)
            print(f"✅ Data validation passed")

            # Create Pydantic model
            matrix = QualificationMatrix.model_validate(validated_data)
            print(f"✅ Pydantic validation passed - {len(matrix.criteria)} criteria extracted")

            # Save JSON
            with open(QUALIFICATION_JSON, 'w', encoding='utf-8') as f:
                json.dump(matrix.model_dump(), f, indent=4)

            print(f"✅ Saved Qualification Matrix JSON → {QUALIFICATION_JSON} in {time.time()-start:.2f}s")
            return matrix

        except json.JSONDecodeError as e:
            print(f"❌ Attempt {attempt + 1} - JSON parse error: {e}")
            if attempt < 2:
                print(f"🔄 Retrying with adjusted prompt...")
                time.sleep(1)
            continue
        except ValueError as e:
            print(f"❌ Attempt {attempt + 1} - Validation error: {e}")
            if attempt < 2:
                print(f"🔄 Retrying with adjusted prompt...")
                time.sleep(1)
            continue
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} - Unexpected error: {e}")
            if attempt < 2:
                print(f"🔄 Retrying...")
                time.sleep(1)
            continue

    # If all attempts failed
    raise RuntimeError("❌ Failed to extract qualification matrix after 3 attempts - LLM extraction unsuccessful")

if __name__ == "__main__":
    extract_qualification_matrix_to_json()