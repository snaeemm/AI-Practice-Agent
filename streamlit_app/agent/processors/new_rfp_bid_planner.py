import os
import json
import re
import time
import sys
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from pydantic import BaseModel, Field
import google.generativeai as genai
import pandas as pd
from docx import Document

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Import centralized settings
from agent.config.settings import settings

# Configure Gemini API
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

class Deliverable(BaseModel):
    section: Optional[str] = Field(None, description="Name of the deliverable section")
    requirement: Optional[str] = Field(None, description="Specific content requirements")
    evaluation_criteria: Optional[str] = Field(None, description="Evaluation criteria if mentioned")
    format: Optional[str] = Field(None, description="Exact format if specified")
    page_limit: Optional[str] = Field(None, description="Exact page/word limit if specified")
    owner: Optional[str] = Field(None, description="Owner or responsible person if specified")

class DeliverablesData(BaseModel):
    client_and_opportunity: Optional[str] = Field(None, description="Client name and opportunity title, inferred if not explicit")
    technical_deliverables: List[Deliverable] = Field(..., description="List of technical deliverables")
    commercial_deliverables: List[Deliverable] = Field(..., description="List of commercial deliverables")

class RFPData(BaseModel):
    client_and_opportunity: Optional[str] = Field(None, description="Client name and opportunity/project title, inferred if not explicit")
    location: Optional[str] = Field(None, description="Project or client location")
    tender_validity: Optional[str] = Field(None, description="Duration proposals must remain valid")
    confirmation_intent_deadline: Optional[str] = Field(None, description="Date and time for confirming intent to participate")
    site_visit_meeting: Optional[str] = Field(None, description="Site visit details if mentioned")
    client_contact_email: Optional[str] = Field(None, description="Primary client contact email address")
    tender_queries_deadline: Optional[str] = Field(None, description="Date and time for submitting questions")
    tender_query_recipient: Optional[str] = Field(None, description="Contact for sending tender queries")
    submission_deadline: Optional[str] = Field(None, description="Date and time for final proposal submission")
    submission_format: Optional[str] = Field(None, description="Submission method")
    submission_email: Optional[str] = Field(None, description="Email for proposal submission")
    submission_requirements: Optional[str] = Field(None, description="Technical and commercial proposal requirements, ideally as bullet points")
    delivery_address: Optional[str] = Field(None, description="Address for submission")
    estimated_contract_value: Optional[str] = Field(None, description="Contract value if mentioned")
    governance_level: Optional[str] = Field(None, description="Governance or approval requirements")
    advance_payment_terms: Optional[str] = Field(None, description="Advance payment or bank guarantee requirements")
    payment_terms: Optional[str] = Field(None, description="Payment terms and timeline")
    additional_notes: Optional[str] = Field(None, description="Important procurement notes")
    project_objectives: Optional[str] = Field(None, description="Main project objectives")
    scope_of_work: Optional[str] = Field(None, description="Brief summary of project scope")

class TemplateField(BaseModel):
    label: str = Field(..., description="Field label from Excel template")
    cell_address: str = Field(..., description="Excel cell address (e.g., 'B3')")
    original_value: Optional[str] = Field(None, description="Original value in the cell, if any")

class AssignmentAnalysis(BaseModel):
    deliverable_section: str
    deliverable_requirement: str
    assigned_owner: str
    reasoning: str
    alternative_partners: List[str] = Field(default_factory=list)

class AssignmentReport(BaseModel):
    client_and_opportunity: str
    analysis_date: str
    total_deliverables: int
    granite_assigned: int
    partner_assigned: int
    assignments: List[AssignmentAnalysis]

# ** NEW PYDANTIC MODELS FOR AI RESPONSE **
class ProposedAssignment(BaseModel):
    assigned_owner: str = Field(..., description="The most suitable owner (either 'Granite MENA' or a partner's name).")
    reasoning: str = Field(..., description="The detailed, professional reasoning for this assignment based on skills, experience, and strategic alignment.")
    alternative_partners: List[str] = Field(..., description="List of 2-3 alternative partners with brief notes on their relevance, in order of suitability.")

class AssignmentData(BaseModel):
    assignments: List[ProposedAssignment]

# ------------------ CAPABILITIES HELPERS ------------------ #
def load_capabilities_json() -> Optional[CapabilitiesData]:
    """Load capabilities JSON from file."""
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

# ** OLD assign_owner function is removed and replaced by AI logic in generate_assignment_report **

# ------------------ EXTRACTION HELPERS ------------------ #
def safe_generate_content(model, content, **kwargs):
    """Generate content with retry logic and truncation handling"""
    max_retries = 3
    for retry in range(max_retries):
        try:
            response = model.generate_content(content, **kwargs)
            if not response or not response.candidates:
                print(f"⚠️ No candidates in response (attempt {retry + 1})")
                time.sleep(1)
                continue
            candidate = response.candidates[0]
            if candidate.finish_reason == 2:  # MAX_TOKENS - Truncated
                print(f"⚠️ Truncated response (MAX_TOKENS, attempt {retry + 1})")
                if candidate.content and candidate.content.parts:
                    partial_text = candidate.content.parts[0].text.strip() if candidate.content.parts[0].text else ""
                    if partial_text and "{" in partial_text:  # Check for JSON start
                        try:
                            token_usage = getattr(response, 'usage_metadata', {}).get('candidates_token_count', 'N/A')
                        except Exception as e:
                            print(f"⚠️ Failed to get token usage: {e}, using N/A")
                            token_usage = 'N/A'
                        print(f"✅ Using partial content (length: {len(partial_text)} chars, tokens used: {token_usage})")
                        return partial_text
                time.sleep(1)
                continue
            if response.text:
                json_str = response.text.strip()
                # Remove markdown code block wrappers
                if json_str.startswith("```json"):
                    json_str = json_str.lstrip("```json").strip()
                if json_str.endswith("```"):
                    json_str = json_str.rstrip("```").strip()
                try:
                    token_usage = getattr(response, 'usage_metadata', {}).get('candidates_token_count', 'N/A')
                except Exception as e:
                    print(f"⚠️ Failed to get token usage: {e}, using N/A")
                    token_usage = 'N/A'
                print(f"✅ Full content generated (tokens used: {token_usage})")
                return json_str
        except Exception as e:
            print(f"⚠️ API error (attempt {retry + 1}): {e}")
            time.sleep(1)
    print(f"❌ Failed after {max_retries} attempts")
    return None

def extract_json_from_context(prompt: str, model_class, user_context=None) -> Optional[BaseModel]:
    """Extract structured JSON from user context (pre-extracted RFP content).

    Args:
        prompt: Extraction prompt
        model_class: Pydantic model class to parse into
        user_context: Optional UserContext with rfp_content or additional_info
    """
    content = []

    if user_context and user_context.rfp_content:
        print("📄 Using pre-extracted RFP content from context...")
        content.append(user_context.rfp_content)

        # Add additional_info as supplementary context if provided
        if user_context.additional_info:
            content.append(f"\n\nADDITIONAL CONTEXT:\n{user_context.additional_info}")
    else:
        raise ValueError("user_context with rfp_content must be provided for extraction.")

    try:
        json_str = safe_generate_content(
            gemini_model,
            content + [prompt],
            generation_config={'temperature': 0.1, 'max_output_tokens': 16384}
        )
        if not json_str:
            print(f"⚠️ No content generated from context.")
            return None

        try:
            data = json.loads(json_str)
            # Filter out empty deliverables
            if 'technical_deliverables' in data:
                data['technical_deliverables'] = [d for d in data['technical_deliverables'] if d.get('section') or d.get('requirement')]
            if 'commercial_deliverables' in data:
                data['commercial_deliverables'] = [d for d in data['commercial_deliverables'] if d.get('section') or d.get('requirement')]
            return model_class(**data)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed from context: {e}")
            print(f"Problematic JSON: {json_str[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Pydantic validation failed from context: {e}")
            return None
    finally:
        # No uploaded_file to delete since we are not processing PDFs directly
        pass

def to_bullet_points(text: Optional[str]) -> str:
    """Convert paragraph text to clean bullet points, handling varied content appropriately"""
    if not text or not isinstance(text, str):
        return ""
    
    text = text.strip()
    
    # Already has bullets - handle both newline-separated and same-line bullets
    if "•" in text:
        parts = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                bullet_parts = line.split('•')
                for i, part in enumerate(bullet_parts):
                    part = part.strip()
                    if part:  # Skip empty parts
                        if i == 0 and not line.startswith('•'):
                            if len(part) > 3:
                                parts.append(f"• {part}")
                        else:
                            parts.append(f"• {part}")
        clean_lines = [line.strip() for line in parts if line.strip() and len(line.strip()) > 2]
        return "\n".join(clean_lines)
    
    # Has dash bullets, convert to proper bullets
    if "- " in text and text.count("- ") > 1:
        lines = text.replace("- ", "• ").split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]
        return "\n".join(clean_lines)
    
    # Has multiple lines that could be bullet points
    if '\n' in text and text.count('\n') >= 2:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) > 1:
            return "\n".join(f"• {line}" for line in lines)
    
    # Split into natural bullet points based on content
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    bullets = [sentence.strip() for sentence in sentences if sentence.strip() and len(sentence.strip()) > 10]
    
    if len(bullets) > 1:
        return "\n".join(f"• {bullet}" for bullet in bullets)
    
    return text

def detect_rfp_type(content_preview: str) -> str:
    """Detect RFP complexity/type for adaptive extraction"""
    content_lower = content_preview.lower()
    if any(word in content_lower for word in ['website', 'software', 'platform', 'api', 'database', 'kentico', 'wcag', 'compliance']):
        return "technical"
    if any(word in content_lower for word in ['campaign', 'creative', 'marketing', 'brand', 'social media', 'content', 'awareness']):
        return "creative"
    if any(word in content_lower for word in ['security', 'cleaning', 'maintenance', 'guard', 'patrol', 'basic service']):
        return "simple"
    return "standard"

def get_deliverables_prompt() -> str:
    """Smart bid management prompt that combines RFP extraction with practical bid requirements"""
    return """
You are an experienced bid manager creating a winning proposal structure. Think strategically about what wins bids, not just what's requested. Build a professional bid framework that demonstrates comprehension, capability, and value. Return ONLY valid JSON:

{
  "client_and_opportunity": "Client name and opportunity title from document",
  "technical_deliverables": [
    {
      "section": "Professional deliverable name",
      "requirement": "Strategic requirements that demonstrate value and understanding. Use bullet format with • symbols.",
      "evaluation_criteria": "What evaluators will assess. Use bullet format with • symbols.", 
      "format": "Format if specified",
      "page_limit": "Limit if specified",
      "owner": "Owner or responsible person if identified from original task assignments, otherwise null"
    }
  ],
  "commercial_deliverables": [
    {
      "section": "Commercial section name",
      "requirement": "Clean commercial requirements. Use bullet format with • symbols.",
      "evaluation_criteria": "Commercial evaluation criteria. Use bullet format with • symbols.",
      "format": "Format if specified", 
      "page_limit": "Limit if specified",
      "owner": "Owner or responsible person if identified from original task assignments, otherwise null"
    }
  ]
}

BID MANAGER APPROACH:
1. ALWAYS START WITH CORE BID COMPONENTS:
    Technical: Cover Letter, Executive Summary, Company Profile, [domain-specific sections], Team Structure & Profiles, Project Management & Execution
    Commercial: Cover Letter, Pricing Model/Costs, Assumptions and Exclusions

2. CREATE STRATEGIC VALUE-FOCUSED SECTIONS:
    - "Comprehension of Client Objectives" (shows you understand their real needs)
    - "Proposed Strategic & Creative Approach" (for creative RFPs) 
    - "Technical Solution Architecture" (for tech RFPs)
    - "Risk Management & Mitigation" (addresses concerns)
    - "Brand Consistency Approach" (for brand/creative work)
    - "Information Security" (for tech projects)
    - "Project Methodology and Schedule" (shows delivery capability)

3. SECTION NAMING - PROFESSIONAL NOT LITERAL:
    ❌ "Appendix A Requirements" → ✅ "Strategic Creative Approach"
    ❌ "Section 5.2 Technical Specs" → ✅ "Technical Solution Design"  
    ❌ "Part 2 Commercial" → ✅ "Investment Proposal"

Rules:
1. Extract and infer all sections and details from the RFP content, maximizing actionable detail.
2. Use imperative language (e.g., "Provide", "Include") for clarity and actionability.
3. Set 'format' and 'page_limit' to null unless specified.
4. For 'owner': When extracting deliverables, analyze the original RFP text for any assigned names or responsibility indicators (e.g., "@Paul Darmas", "Assigned to Paul", "Paul - Task"). When creating new strategic deliverables, attempt to reassign owners based on the original assignments where relevant skills or roles match. Use null only if no owner can be determined.
5. Ensure valid JSON with no trailing commas or unclosed strings.

CONTEXT-AWARE COMPLEXITY:
    - Creative RFPs: Focus on strategy, concepts, brand alignment, asset production
    - Tech RFPs: Architecture, security, methodology, team expertise
    - Service RFPs: Approach, experience, team, delivery process

PROFESSIONAL BID STRUCTURE EXAMPLES:
Creative/Marketing: Cover Letter, Executive Summary, Company Profile, Comprehension of Client Objectives, Proposed Creative Strategy, Brand Consistency Approach, Project Management & Execution, Team Structure & Profiles, Flexibility & Risk Management
Technology: Cover Letter, Executive Summary, Company Profile, Technical Solution Architecture, Project Methodology, Information Security, Risk Matrix, Team Expertise, Warranty & Maintenance
Service: Cover Letter, Executive Summary, Company Profile, Service Approach & Methodology, Client References, Project Team Staffing, Risk Management, Quality Assurance
"""

def get_overview_prompt() -> str:
    """Flexible prompt for extracting all possible RFP overview details, adaptable to any RFP"""
    fields = ', '.join(f'"{k}": "{v.description}"' for k, v in RFPData.model_fields.items())
    return f"""
Extract all possible RFP details from the document, inferring where necessary. Return ONLY valid JSON: {{ {fields} }}
Use null for missing fields. For 'scope_of_work' and 'submission_requirements', use a single string summarizing all elements or join multiple items with newlines. Ensure valid JSON with no unclosed strings.
"""

# ** NEW PROMPT FOR ASSIGNMENTS **
def get_assignment_prompt(deliverables: List[Deliverable], capabilities: CapabilitiesData) -> str:
    """Prompt for assigning deliverables to owners using Gemini's reasoning."""
    deliverables_text = "\n".join([
        f"- Section: {d.section}\n  Requirement: {d.requirement}\n" for d in deliverables
    ])
    
    granite_capabilities = "\n".join([
        f"  - {c.name}" +
        (f" (Category: {c.category}" if c.category else "") +
        (f", Industries: {', '.join(c.industry_focus)}" if c.industry_focus else "") +
        (")" if c.category or c.industry_focus else "")
        for c in capabilities.granite_mena
    ])
    partners = "\n".join([
        f"- Partner Name: {p.name}" +
        f"\n  Category: {p.category}" +
        f"\n  Capabilities: {', '.join(p.capabilities)}" +
        f"\n  Industry Focus: {', '.join(p.industry_focus)}" +
        (f"\n  Reliability Score: {p.reliability_score}/5" if p.reliability_score else "") +
        (f"\n  Agreement Status: {p.agreement_status}" if p.agreement_status else "") +
        (f"\n  Agreement Type: {p.agreement_type}" if p.agreement_type else "") +
        (f"\n  Strategic Fit: {p.strategic_fit}" if p.strategic_fit else "") +
        (f"\n  Past Projects: {p.past_projects}" if p.past_projects else "") +
        (f"\n  Contact: {p.contact.email if p.contact and p.contact.email else 'N/A'}" if p.contact else "") +
        (f" (Internal PoC: {p.contact.internal_poc})" if p.contact and p.contact.internal_poc else "") +
        (f"\n  Notes: {p.notes}" if p.notes else "")
        for p in capabilities.partners
    ])

    return f"""
As an expert bid manager, your task is to assign each deliverable to the most suitable owner: either 'Granite MENA' or a specific partner from the list (Granite Ireland is must NOT be considered for anything). Your reasoning must be professional, strategic, and concise.

Deliverables to Assign:
{deliverables_text}

Our Capabilities:
Granite MENA: {granite_capabilities}

Partner Network:
{partners}

Assignment Guidelines:
1. STRATEGIC ASSIGNMENTS:
   - Assign to "Granite MENA" for strategic, high-level, or overall project management deliverables
   - Consider Granite MENA's category and industry focus when making assignments

2. PARTNER ASSIGNMENTS:
   - For specialized deliverables (e.g., website development, creative campaigns), find the best partner match
   - PRIORITIZE partners with higher reliability scores (4-5/5) for critical deliverables
   - PREFER partners with existing agreements (agreement_status = "Yes" or "Active") for faster project initiation
   - Consider strategic_fit ratings when choosing between similar capability partners
   - Reference past_projects as evidence of successful delivery capability
   - Factor in any important notes that might affect project success

3. DECISION CRITERIA PRIORITY:
   - Capability match (essential)
   - Reliability score (critical for project success)
   - Agreement status (affects timeline and ease of engagement)
   - Strategic fit (long-term partnership value)
   - Past project success (proven track record)

4. OUTPUT REQUIREMENTS:
   - Your reasoning MUST reference specific data points (reliability scores, agreement status, strategic fit, etc.)
   - Your output must be a valid JSON list of assignments.

Return ONLY valid JSON:
{{
  "assignments": [
    {{
      "assigned_owner": "Name of the assigned owner (e.g., 'Granite MENA' or 'Partner Name')",
      "reasoning": "Explain the strategic reason for the assignment. MUST reference specific data: reliability scores, agreement status, strategic fit, past projects, or other relevant factors from the partner profiles.",
      "alternative_partners": ["Partner A: [brief note on capability and why they're alternative]", "Partner B: [brief note on capability and reliability]"]
    }}
  ]
}}
"""

def copy_excel_template(input_path: Path, output_path: Path) -> Path:
    """Copy Excel template preserving formatting"""
    wb = load_workbook(input_path)
    wb_new = Workbook(write_only=False)
    for sheet_name in wb.sheetnames:
        source_sheet = wb[sheet_name]
        target_sheet = wb_new.create_sheet(sheet_name)
        for row in source_sheet.iter_rows():
            for cell in row:
                new_cell = target_sheet.cell(row=cell.row, column=cell.column, value=cell.value)
                if cell.has_style:
                    new_cell.font = Font(name=cell.font.name, size=cell.font.size, bold=cell.font.bold, italic=cell.font.italic, color=cell.font.color)
                    new_cell.border = Border(left=Side(style=cell.border.left.style), right=Side(style=cell.border.right.style), top=Side(style=cell.border.top.style), bottom=Side(style=cell.border.bottom.style))
                    new_cell.fill = PatternFill(fill_type=cell.fill.fill_type, fgColor=cell.fill.fgColor)
                    new_cell.alignment = Alignment(horizontal=cell.alignment.horizontal, vertical=cell.alignment.vertical, wrap_text=cell.alignment.wrap_text)
        for col, dim in source_sheet.column_dimensions.items():
            target_sheet.column_dimensions[col].width = dim.width
        for row, dim in source_sheet.row_dimensions.items():
            target_sheet.row_dimensions[row].height = dim.height
    if 'Sheet' in wb_new.sheetnames:
        del wb_new['Sheet']
    if 'hiddenSheet' in wb_new.sheetnames:
        del wb_new['hiddenSheet']
    # Local file save commented out - data saved to database
    # wb_new.save(output_path)
    return output_path

def adjust_row_height(sheet, cell_address: str, text: str) -> None:
    """Adjust row height based on content"""
    if not text:
        return
    row_num = int(''.join([c for c in cell_address if c.isdigit()]))
    col_letter = ''.join([c for c in cell_address if c.isalpha()])
    col_width = sheet.column_dimensions[col_letter].width or 30
    chars_per_line = int(col_width * 1.2)
    lines = text.count('\n') + sum(len(line) // chars_per_line for line in text.split('\n')) + 1
    height = max(15, min(lines * 15, 300))
    sheet.row_dimensions[row_num].height = height

def apply_deliverables_formatting(sheet):
    """Apply formatting to deliverables sheet"""
    column_widths = {'B': 15, 'C': 24, 'D': 13, 'E': 62, 'F': 32, 'G': 20, 'H': 15, 'I': 16, 'J': 15}
    for col, width in column_widths.items():
        sheet.column_dimensions[col].width = width
    header_font = Font(name="Segoe UI", size=10, bold=True)
    header_fill = PatternFill(fill_type="solid", fgColor="E7E6E6")
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    header_border = Border(top=Side('thin'), bottom=Side('thin'), left=Side('thin'), right=Side('thin'))
    headers = ["Client Ref from RFP", "Section Heading", "Sub-Section Heading", "Deliverable Requirement", "Evaluation Criteria", "Client Format? Letterhead? Table?", "Page/ Word Limit", "Owner", "Status"]
    for i, title in enumerate(headers, start=2):
        cell = sheet.cell(8, i, title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = header_border
    sheet['B3'].font = Font("Segoe UI", 14, bold=False)
    sheet['B5'].font = Font("Segoe UI", 14, bold=True)
    sheet['B7'].font = Font("Segoe UI", 10, bold=True)

def add_commercial_section_header(sheet, header_row: int):
    """Add commercial section header at the specified row with proper formatting matching template structure"""
    # Add commercial section title
    commercial_title_cell = sheet.cell(header_row, 2, "Commercial Bid")  # Column B
    commercial_title_cell.font = Font("Segoe UI", 14, bold=True)
    commercial_title_cell.alignment = Alignment(horizontal='left', vertical='center')

    # Add column headers 3 rows below the title (matching template structure)
    header_row_actual = header_row + 3
    header_font = Font(name="Segoe UI", size=10, bold=True)
    header_fill = PatternFill(fill_type="solid", fgColor="E7E6E6")
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    header_border = Border(top=Side('thin'), bottom=Side('thin'), left=Side('thin'), right=Side('thin'))
    headers = ["Client Ref from RFP", "Section Heading", "Sub-Section Heading", "Deliverable Requirement", "Evaluation Criteria", "Client Format? Letterhead? Table?", "Page/ Word Limit", "Owner", "Status"]

    for i, title in enumerate(headers, start=2):
        cell = sheet.cell(header_row_actual, i, title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = header_border

def detect_template_structure(sheet) -> dict:
    """Dynamically detect template structure positions"""
    if not sheet:
        raise ValueError("Sheet is None or invalid")
        
    structure = {
        'client_row': None,
        'tech_header_row': None,
        'tech_start_row': None,
        'comm_header_row': None,  
        'comm_start_row': None,
        'max_row': sheet.max_row
    }
    
    try:
        for row in range(1, min(50, sheet.max_row + 1)):
            for col in range(2, 6):
                cell = sheet.cell(row, col)
                if cell.value and isinstance(cell.value, str):
                    value = cell.value.lower().strip()
                    if ('[client' in value or 'opportunity]' in value) and not structure['client_row']:
                        structure['client_row'] = row
                    elif 'technical' in value and 'bid' in value and not structure['tech_header_row']:
                        structure['tech_header_row'] = row
                        structure['tech_start_row'] = row + 3
                    elif 'commercial' in value and 'bid' in value and not structure['comm_header_row']:
                        structure['comm_header_row'] = row
                        structure['comm_start_row'] = row + 3
    except Exception as e:
        print(f"⚠️ Error scanning template structure: {e}")
    
    if not structure['client_row']:
        structure['client_row'] = 4
        print("⚠️ Client row not found, using fallback row 4")
    if not structure['tech_start_row']:
        structure['tech_start_row'] = 10
        print("⚠️ Technical section not found, using fallback row 10")
    if not structure['comm_start_row']:
        structure['comm_start_row'] = 25
        print("⚠️ Commercial section not found, using fallback row 25")
        
    return structure

# Removed dynamic positioning - using fixed layout instead

def fill_deliverable_row(sheet, row: int, deliv: Deliverable, owner: str, cell_style: dict) -> int:
    """Fill a single deliverable row with proper formatting and borders, including the owner."""
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    filled = 0

    # Section name (Column C)
    if deliv.section:
        cell_value = deliv.section.replace("**", "")
        cell_c = sheet.cell(row, 3, cell_value)
        cell_c.font = cell_style['font']
        cell_c.alignment = cell_style['alignment']
        cell_c.border = border
        adjust_row_height(sheet, f'C{row}', cell_value)
        filled += 1

    # Requirement (Column E) - Ensure full text is included
    if deliv.requirement:
        cell_value = to_bullet_points(deliv.requirement.replace("**", ""))
        cell_e = sheet.cell(row, 5, cell_value)
        cell_e.font = cell_style['font']
        cell_e.alignment = cell_style['alignment']
        cell_e.border = border
        # Increase row height for long requirements
        adjust_row_height(sheet, f'E{row}', cell_value)
        # Ensure minimum height for readability
        row_num = row
        current_height = sheet.row_dimensions[row_num].height or 15
        if len(cell_value) > 200:  # Long text needs more height
            sheet.row_dimensions[row_num].height = max(current_height, 45)
        filled += 1

    # Evaluation criteria (Column F)
    if deliv.evaluation_criteria:
        cell_value = to_bullet_points(deliv.evaluation_criteria.replace("**", ""))
        cell_f = sheet.cell(row, 6, cell_value)
        cell_f.font = cell_style['font']
        cell_f.alignment = cell_style['alignment']
        cell_f.border = border
        adjust_row_height(sheet, f'F{row}', cell_value)
        filled += 1

    # Format (Column G)
    if deliv.format:
        cell_value = deliv.format.replace("**", "")
        cell_g = sheet.cell(row, 7, cell_value)
        cell_g.font = cell_style['font']
        cell_g.alignment = cell_style['alignment']
        cell_g.border = border
        adjust_row_height(sheet, f'G{row}', cell_value)
        filled += 1

    # Page limit (Column H)
    if deliv.page_limit:
        cell_value = deliv.page_limit.replace("**", "")
        cell_h = sheet.cell(row, 8, cell_value)
        cell_h.font = cell_style['font']
        cell_h.alignment = cell_style['alignment']
        cell_h.border = border
        adjust_row_height(sheet, f'H{row}', cell_value)
        filled += 1

    # Owner (Column I) - MODIFIED TO USE AI-ASSIGNED OWNER
    cell_value = owner.replace("**", "")
    cell_i = sheet.cell(row, 9, cell_value)
    cell_i.font = cell_style['font']
    cell_i.alignment = cell_style['alignment']
    cell_i.border = border
    adjust_row_height(sheet, f'I{row}', cell_value)
    filled += 1

    # Add borders to empty cells in the row to maintain table structure
    for col in range(2, 11):  # Columns B through J
        cell = sheet.cell(row, col)
        if not cell.border.left.style:  # Only add if no border exists
            cell.border = border

    return filled

def fill_deliverables_sheet(sheet, data: DeliverablesData, assignments: Optional[List[AssignmentAnalysis]]) -> int:
    """Fill deliverables Excel sheet with dynamic template detection and AI assignments."""
    if not sheet:
        print("❌ Error: Sheet is None or invalid")
        return 0
    if not data:
        print("❌ Error: DeliverablesData is None or invalid")
        return 0
    
    # Create a mapping from deliverable section to assigned owner for quick lookup
    assignment_map = {a.deliverable_section: a.assigned_owner for a in assignments} if assignments else {}
    
    filled = 0
    
    try:
        # Detect template structure
        structure = detect_template_structure(sheet)

        # Fixed layout: Max 20 technical deliverables, fixed commercial position
        tech_deliverables = data.technical_deliverables[:20]  # Cap at 20
        tech_count = len(tech_deliverables)
        comm_count = len(data.commercial_deliverables)
        total_deliverables = tech_count + comm_count

        if total_deliverables == 0:
            print("⚠️ Warning: No deliverables found in data")
            return 0

        if len(data.technical_deliverables) > 20:
            print(f"⚠️ Warning: Truncated technical deliverables from {len(data.technical_deliverables)} to 20")

        # Use existing commercial section in template at row 35
        existing_comm_start_row = 33  # Data starts after existing header at row 35

        print(f"📊 Fixed layout structure:")
        print(f"   Client row: {structure['client_row']}")
        print(f"   Technical: rows {structure['tech_start_row']} - {structure['tech_start_row'] + 19} (max 20, actual: {tech_count})")
        print(f"   Commercial: rows {existing_comm_start_row}+ ({comm_count} deliverables)")
        
        # Fill client/opportunity
        if data.client_and_opportunity and structure['client_row']:
            cell_value = data.client_and_opportunity.replace("**", "")
            cell = sheet.cell(structure['client_row'], 2)  # Column B
            cell.value = cell_value
            cell.font = Font("Segoe UI", 18, bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            adjust_row_height(sheet, f'B{structure["client_row"]}', cell_value)
            filled += 1
        
        # Standard cell style
        cell_style = {
            'font': Font("Segoe UI", 10),
            'alignment': Alignment(wrap_text=True, vertical='top')
        }
        
        # Fill technical deliverables (max 20)
        for i, deliv in enumerate(tech_deliverables):
            row = structure['tech_start_row'] + i
            owner = assignment_map.get(deliv.section, "Granite MENA") # Get AI owner, fallback to Granite
            filled += fill_deliverable_row(sheet, row, deliv, owner, cell_style)

        # Fill commercial deliverables using existing template section (no duplicate headers)
        for i, deliv in enumerate(data.commercial_deliverables):
            row = existing_comm_start_row + i
            owner = assignment_map.get(deliv.section, "Granite MENA") # Get AI owner, fallback to Granite
            filled += fill_deliverable_row(sheet, row, deliv, owner, cell_style)

        # Report success
        print(f"✅ Successfully filled {filled} cells across {total_deliverables} deliverables (tech: {tech_count}/20 max, comm: {comm_count})")
        
    except Exception as e:
        print(f"❌ Error filling deliverables sheet: {e}")
        return 0
    
    return filled

def extract_template_fields(sheet) -> List[TemplateField]:
    """Extract fillable fields from overview template"""
    fields = []
    for row in sheet.iter_rows(min_row=1, max_row=40, min_col=2, max_col=6):
        for cell in row:
            if isinstance(cell.value, str) and cell.value.strip() and len(cell.value.strip()) > 3:
                value_cell = sheet.cell(cell.row, cell.column + 1)
                fields.append(TemplateField(label=cell.value.strip(), cell_address=value_cell.coordinate))
    return fields

def map_rfp_to_excel(data: RFPData) -> List[tuple[str, str]]:
    """Map RFP data to overview fields with bullet points"""
    mappings = [
        ("[Client and Opportunity]", data.client_and_opportunity.replace("**", "") if data.client_and_opportunity else None),
        ("Location", data.location.replace("**", "") if data.location else None),
        ("Tender Validity", data.tender_validity.replace("**", "") if data.tender_validity else None),
        ("Confirmation of Intent to Bid", data.confirmation_intent_deadline.replace("**", "") if data.confirmation_intent_deadline else None),
        ("Tender Queries Deadline", data.tender_queries_deadline.replace("**", "") if data.tender_queries_deadline else None),
        ("Submission Deadline", data.submission_deadline.replace("**", "") if data.submission_deadline else None),
        ("Client Point of Contact", data.client_contact_email.replace("**", "") if data.client_contact_email else None),
        ("Tender Query Recipient and Details", data.tender_query_recipient.replace("**", "") if data.tender_query_recipient else None),
        ("Delivery Address", data.delivery_address.replace("**", "") if data.delivery_address else None),
        ("Submission Format? Hard Copies / Portal / Email", data.submission_format.replace("**", "") if data.submission_format else None),
        ("Submission Requirements", to_bullet_points(data.submission_requirements.replace("**", "")) if data.submission_requirements else None),
        ("Estimated Contract Value", data.estimated_contract_value.replace("**", "") if data.estimated_contract_value else None),
        ("Governance Level Required", data.governance_level.replace("**", "") if data.governance_level else None),
        ("Additional Notes/Requirements", to_bullet_points(f"{data.advance_payment_terms or ''} {data.payment_terms or ''}".strip().replace("**", "")) if data.advance_payment_terms or data.payment_terms else None),
        ("Site Visit/Client Meeting (if applicable)", data.site_visit_meeting.replace("**", "") if data.site_visit_meeting else "N/A"),
        ("If Hard Copy, Specify Details of Submission", "N/A")
    ]
    return [(k, v) for k, v in mappings if v]

def fill_overview_sheet(sheet, fields: List[TemplateField], mappings: List[tuple[str, str]]) -> int:
    """Fill overview Excel sheet"""
    filled = 0
    for field in fields:
        for label, value in mappings:
            if field.label == label:
                cell_value = value.replace("**", "")
                cell = sheet[field.cell_address]
                cell.value = cell_value
                cell.alignment = Alignment(wrap_text=True, vertical='top', horizontal='left')
                adjust_row_height(sheet, field.cell_address, cell_value)
                filled += 1
    return filled

def generate_assignment_report(pdf_base: str, deliv_data: DeliverablesData, capabilities_data: Optional[CapabilitiesData]) -> AssignmentReport:
    """Generate comprehensive assignment analysis report using Gemini for reasoning."""
    if not capabilities_data:
        print("⚠️ No capabilities data found, can't assign to partners.")
        return None

    # Filter out empty deliverables before sending to API
    all_deliverables = [
        d for d in deliv_data.technical_deliverables + deliv_data.commercial_deliverables
        if d.section and d.requirement
    ]
    
    if not all_deliverables:
        print("⚠️ No valid deliverables to assign.")
        return None

    # Get the detailed, AI-driven assignments
    prompt = get_assignment_prompt(all_deliverables, capabilities_data)
    
    try:
        # Use a higher temperature for more creative reasoning
        json_str = safe_generate_content(
            gemini_model, 
            prompt, 
            generation_config={'temperature': 0.7, 'max_output_tokens': 16384}
        )
        if not json_str:
            print("❌ No AI assignments generated.")
            return None
            
        assignments_data = json.loads(json_str)
        assignments = [ProposedAssignment(**item) for item in assignments_data['assignments']]

    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ Failed to parse AI-generated assignment JSON: {e}")
        print(f"Problematic JSON: {json_str[:500]}...")
        return None

    # Map the AI assignments to your final AssignmentAnalysis Pydantic model
    final_assignments = []
    granite_count = 0
    partner_count = 0
    
    for i, assignment in enumerate(assignments):
        # Handle cases where AI might not assign anything
        if i >= len(all_deliverables):
            continue
            
        original_deliv = all_deliverables[i]
        
        final_assignments.append(AssignmentAnalysis(
            deliverable_section=original_deliv.section,
            deliverable_requirement=original_deliv.requirement,  # Keep full requirement text
            assigned_owner=assignment.assigned_owner,
            reasoning=assignment.reasoning,
            alternative_partners=assignment.alternative_partners
        ))

        if "Granite" in assignment.assigned_owner:
            granite_count += 1
        else:
            partner_count += 1
    
    return AssignmentReport(
        client_and_opportunity=deliv_data.client_and_opportunity or "Unknown Client",
        analysis_date=time.strftime("%Y-%m-%d %H:%M:%S"),
        total_deliverables=len(final_assignments),
        granite_assigned=granite_count,
        partner_assigned=partner_count,
        assignments=final_assignments
    )

def create_assignment_excel_report(pdf_base: str, report: AssignmentReport):
    """Create Excel report from assignment analysis with bullet points for Reasoning and Alternative Partners."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Assignment Analysis"
    
    # Headers
    headers = ["Deliverable Section", "Requirement", "Assigned Owner", "Reasoning", "Alternative Partners"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.font = Font(name="Segoe UI", size=10, bold=True)
        cell.fill = PatternFill(fill_type="solid", fgColor="E7E6E6")
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
    
    # Summary section
    ws.cell(2, 1, f"Client: {report.client_and_opportunity}")
    ws.cell(3, 1, f"Analysis Date: {report.analysis_date}")
    ws.cell(4, 1, f"Total Deliverables: {report.total_deliverables}")
    ws.cell(5, 1, f"Granite MENA: {report.granite_assigned}, Partners: {report.partner_assigned}")
    
    # Data rows
    start_row = 7
    for i, assignment in enumerate(report.assignments):
        row = start_row + i
        ws.cell(row, 1, assignment.deliverable_section)

        # Format requirement with proper bullet points and line breaks
        formatted_requirement = to_bullet_points(assignment.deliverable_requirement)
        ws.cell(row, 2, formatted_requirement)

        ws.cell(row, 3, assignment.assigned_owner)

        # Format reasoning with proper bullet points and line breaks
        formatted_reasoning = to_bullet_points(assignment.reasoning)
        ws.cell(row, 4, formatted_reasoning)

        # Format alternative partners with proper bullet points and line breaks
        alt_partners_text = "\n".join([f"• {partner}" for partner in assignment.alternative_partners])
        ws.cell(row, 5, alt_partners_text)

        # Apply formatting to all cells in the row with increased row height for multi-line content
        for col in range(1, 6):
            cell = ws.cell(row, col)
            cell.font = Font(name="Segoe UI", size=10)
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )

        # Set minimum row height for readability of multi-line content
        ws.row_dimensions[row].height = max(30, len(formatted_requirement.split('\n')) * 15)
    
    # Column widths - Increased width for requirement column to prevent truncation
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 60  # Increased for full requirement text
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 45  # Increased for full reasoning text
    ws.column_dimensions['E'].width = 35  # Increased for alternative partners

    # Local file save commented out - data saved to database
    # output_path = RESULTS_DIR / f"{pdf_base}_assignment_report.xlsx"
    # wb.save(output_path)
    # print(f"✅ Saved assignment Excel report: {pdf_base}_assignment_report.xlsx")
    print(f"✅ Assignment report generated in-memory (saved to database)")

# Local JSON file saving function commented out - all data saved to database instead
# def save_json_data(pdf_base: str, deliv_data: Optional[DeliverablesData], rfp_data: Optional[RFPData], assignment_report: Optional[AssignmentReport] = None):
#     """Save extracted data to JSON files"""
#     if deliv_data:
#         with open(RESULTS_DIR / f"{pdf_base}_deliverables.json", 'w', encoding='utf-8') as f:
#             json.dump(deliv_data.model_dump(), f, indent=4)
#         print(f"✅ Saved deliverables JSON: {pdf_base}_deliverables.json")
#     if rfp_data:
#         with open(RESULTS_DIR / f"{pdf_base}_overview.json", 'w', encoding='utf-8') as f:
#             json.dump(rfp_data.model_dump(), f, indent=4)
#         print(f"✅ Saved overview JSON: {pdf_base}_overview.json")
#     if assignment_report:
#         with open(RESULTS_DIR / f"{pdf_base}_assignment_analysis.json", 'w', encoding='utf-8') as f:
#             json.dump(assignment_report.model_dump(), f, indent=4)
#         print(f"✅ Saved assignment analysis JSON: {pdf_base}_assignment_analysis.json")

def process_pdf(pdf_input: Optional[str], template_input: str, output_template: str, user_context=None):
    """Process PDF or context for both deliverables and overview in the same file

    Supports 3 modes:
    1. PDF only: Provide pdf_input, extract from PDF
    2. PDF + context: Provide both, use PDF as primary with context supplement
    3. Context only: Provide user_context with rfp_content, no PDF needed

    Args:
        pdf_input: Optional path to PDF file or filename
        template_input: Excel template filename
        output_template: Output filename template
        user_context: Optional UserContext (imported from new_rfp_qualifier)
    """
    # Determine pdf_base for file naming
    if pdf_input:
        # If pdf_input is provided, use it as the base name
        pdf_base = Path(pdf_input).stem if Path(pdf_input).suffix else str(pdf_input)
    elif user_context and user_context.rfp_content:
        # Context-only mode: generate a name
        import hashlib
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        context_hash = hashlib.md5(user_context.rfp_content[:100].encode()).hexdigest()[:8]
        pdf_base = f"context_rfp_{timestamp}_{context_hash}"
    else:
        raise ValueError("Either pdf_input or user_context.rfp_content must be provided")

    # Local output path commented out - not needed for database-only saving
    # output_path = RESULTS_DIR / output_template.format(pdf_name=pdf_base)

    print(f"\n🚀 Processing {pdf_base} at {time.strftime('%I:%M %p %Z, %B %d, %Y')}")
    print(f"📊 Note: All data will be saved to database (no local files created)")

    # Load capabilities data
    capabilities_data = load_capabilities_json()

    # Extract data using the refined functions with context support
    deliv_data = extract_json_from_context(get_deliverables_prompt(), DeliverablesData, user_context)
    rfp_data = extract_json_from_context(get_overview_prompt(), RFPData, user_context)

    # Generate assignment analysis report
    assignment_report = None
    if deliv_data:
        assignment_report = generate_assignment_report(pdf_base, deliv_data, capabilities_data)

    if not deliv_data and not rfp_data:
        print("❌ Failed to extract any data")
        return

    # Save to database instead of files
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from database.db_manager import DatabaseManager

        db = DatabaseManager()

        rfp_id = pdf_base
        client_name = deliv_data.client_and_opportunity if deliv_data else "Unknown Client"
        project_title = deliv_data.client_and_opportunity if deliv_data else "Unknown Project"

        # Create/update RFP document
        db.create_rfp_document(
            rfp_id=rfp_id,
            client_name=client_name,
            project_title=project_title,
            pdf_path=None # No longer processing PDFs directly
        )

        # Save deliverables data
        if deliv_data:
            db.save_rfp_deliverables(
                rfp_id=rfp_id,
                deliverables_data=deliv_data.model_dump()
            )
            print(f"✅ Saved deliverables to database")

        # Save RFP raw data
        if rfp_data:
            db.save_rfp_raw_data(
                rfp_id=rfp_id,
                rfp_data=rfp_data.model_dump()
            )
            print(f"✅ Saved RFP overview data to database")

        # Save assignment analysis
        if assignment_report:
            db.save_rfp_assignments(
                rfp_id=rfp_id,
                assignment_data=assignment_report.model_dump()
            )
            print(f"✅ Saved assignment analysis to database")

        print(f"\n✅ BID PLAN DATA SAVED TO DATABASE")
        print(f"📊 RFP ID: {rfp_id}")
        print(f"📋 Client: {client_name}")
        if assignment_report:
            print(f"📦 Total Deliverables: {assignment_report.total_deliverables}")
            print(f"🏢 Granite: {assignment_report.granite_assigned}, 🤝 Partners: {assignment_report.partner_assigned}")

    except Exception as e:
        print(f"⚠️ Failed to save to database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Process specified file from command line
        pdf_files = [sys.argv[1]]
    else:
        # Default files if no command line argument
        pdf_files = [
            "Part 1 RFQ-06-2025_Creative Awareness_20250624.pdf",
            # "RFP_gary.pdf",
        ]
    
    template_input = "Bid Plan - [Client Opp Name]_BB_140125.xlsx"
    output_template = "{pdf_name}_bid_plan.xlsx"
    
    for pdf in pdf_files:
        pdf_path = (settings.FILES_DIR / pdf).resolve()
        if pdf_path.exists():
            process_pdf(pdf, template_input, output_template)
        else:
            print(f"⚠️ File not found: {pdf_path}")