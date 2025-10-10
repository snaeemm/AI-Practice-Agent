import json
import time
import re
import difflib
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from pydantic import BaseModel, Field
import google.generativeai as genai
import os

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env")
genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025"))

# Constants
FILES_DIR = Path(os.getenv("FILES_DIR", "/mnt/c/Users/Shahzeb/Granite Media/Granite MENA - Operations/2. Practices/AI/Agentic AI for Bid Process/Related Files")).resolve()
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "/mnt/c/Users/Shahzeb/Granite Media/Granite MENA - Operations/2. Practices/AI/Agentic AI for Bid Process/Bid Files")).resolve()
CAPABILITIES_JSON = FILES_DIR / "capabilities.json"
QUALIFICATION_JSON = FILES_DIR / "qualification_matrix.json"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ DATA MODELS ------------------ #
class Contact(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None

class Capability(BaseModel):
    name: str
    category: Optional[str] = None
    capabilities: List[str]
    industry_focus: List[str] = Field(default_factory=list)
    contact: Optional[Contact] = None

class CapabilitiesData(BaseModel):
    granite_mena: List[Capability]
    partners: List[Capability]

class Deliverable(BaseModel):
    section: Optional[str] = None
    requirement: Optional[str] = None

class DeliverablesData(BaseModel):
    client_and_opportunity: Optional[str] = None
    technical_deliverables: List[Deliverable] = Field(default_factory=list)
    commercial_deliverables: List[Deliverable] = Field(default_factory=list)

class EstimatedValue(BaseModel):
    value: Optional[str] = None
    confidence_level: Optional[str] = None  # "High", "Medium", "Low"
    reasoning: Optional[str] = None
    source: Optional[str] = None  # "Extracted", "Estimated", "User_Provided"

class RFPData(BaseModel):
    client_and_opportunity: Optional[EstimatedValue] = Field(None, description="Client name and opportunity description")
    estimated_contract_value: Optional[EstimatedValue] = Field(None, description="Contract value or budget if specified")
    project_objectives: Optional[EstimatedValue] = Field(None, description="Main objectives and goals of the project")
    scope_of_work: Optional[EstimatedValue] = Field(None, description="Detailed scope of work and requirements")
    timeline: Optional[EstimatedValue] = Field(None, description="Project timeline, deadlines, or duration")
    submission_deadline: Optional[EstimatedValue] = Field(None, description="RFP submission deadline")
    client_type: Optional[EstimatedValue] = Field(None, description="Government, private sector, NGO, etc.")
    industry_sector: Optional[EstimatedValue] = Field(None, description="Industry sector (healthcare, finance, government, etc.)")
    region: Optional[EstimatedValue] = Field(None, description="Geographic region or country")
    rfp_type: Optional[EstimatedValue] = Field(None, description="Creative, technology, service, consulting, etc.")
    complexity_indicators: Optional[EstimatedValue] = Field(None, description="Technical complexity, team size, integration requirements")
    additional_notes: Optional[EstimatedValue] = Field(None, description="Any other relevant notes or requirements")

class QualificationCriterion(BaseModel):
    name: str
    options: List[str]
    scores: List[int]
    weight: float

class QualificationMatrix(BaseModel):
    criteria: List[QualificationCriterion]
    average_weight: float

class QualificationAnalysis(BaseModel):
    criterion: str
    selected_option: str
    score: int
    weighted_score: float
    reasoning: str
    missing_data_justification: Optional[str] = Field(None, description="Justification for how missing RFP data was estimated using real-world factors")

class QualificationContext(BaseModel):
    estimated_budget: Optional[EstimatedValue] = None
    estimated_timeline: Optional[EstimatedValue] = None
    complexity_assessment: Optional[str] = None
    strategic_fit_notes: Optional[str] = None
    capability_gaps: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    opportunity_factors: List[str] = Field(default_factory=list)

class UserContext(BaseModel):
    rfp_content: Optional[str] = Field(None, description="Full RFP text content if no PDF provided")
    additional_info: Optional[str] = Field(None, description="Any additional context, hints, or supplementary information")

class QualificationReport(BaseModel):
    client_and_opportunity: str
    analysis_date: str
    total_score: float
    qualifies: bool
    threshold: float
    analyses: List[QualificationAnalysis]
    qualification_context: Optional[QualificationContext] = None
    rfp_classification: Optional[str] = None  # "Creative-Government-High", "Tech-Private-Medium"
    executive_summary: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)

# ------------------ HELPERS ------------------ #
def load_json_file(file_path: Path, model_class: BaseModel) -> Optional[BaseModel]:
    if not file_path.exists():
        print(f"⚠️ File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return model_class(**data)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None

def extract_first_json_object(text: str) -> Optional[str]:
    """Extract the first balanced JSON object from text."""
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1].strip()
    return None

def format_excel_text(text: str) -> str:
    """Format text for clean, readable Excel output with proper bullets and spacing."""
    if not text:
        return text

    # Remove markdown formatting first
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', text)  # *italic*
    text = re.sub(r'(?<!_)_(?!_)([^_]+)_(?!_)', r'\1', text)       # _italic_
    text = re.sub(r'`([^`]+)`', r'\1', text)      # `code`
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # # headers
    text = re.sub(r'~~(.*?)~~', r'\1', text)      # ~~strikethrough~~

    # Handle missing data justification format
    if "MISSING FROM RFP:" in text or "Missing:" in text:
        text = text.replace("MISSING FROM RFP:", "Missing:")
        text = text.replace("ESTIMATION BASIS:", "Basis:")
        text = text.replace("CONFIDENCE:", "Confidence:")
        # Just clean up spacing
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    # For reasoning and other text - keep existing structure but clean up
    # Just preserve the existing bullet structure from the AI
    return text.strip()

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

def get_qualification_extraction_prompt() -> str:
    """Extract RFP data with clear source tracking."""
    return f"""
You are an expert bid manager extracting data from an RFP. For each field, clearly distinguish between what was EXTRACTED vs ESTIMATED.

For each field, return an object with:
- "value": the actual content
- "source": "Extracted" (explicitly stated in RFP) or "Estimated" (your professional judgment)
- "confidence_level": "High", "Medium", "Low"
- "reasoning": explain your source/estimation method

CRITICAL: Only use "Extracted" if information is EXPLICITLY stated in the RFP. Everything else is "Estimated".

MANDATORY ESTIMATION RULES:
- ALWAYS provide estimated values for budget and timeline - these are required for qualification scoring
- BUDGET: If not specified, estimate range based on client type, project scope, and complexity from RFP
- TIMELINE: If not specified, estimate range based on project scope, stakeholder complexity, and deliverables from RFP
- Base ALL estimations on actual RFP content indicators - cite specific RFP text that supports your estimation

BUSINESS INTELLIGENCE ESTIMATION FACTORS:
When RFP lacks business potential information, consider these factors for intelligent estimation:

PROFIT MARGIN POTENTIAL:
- Government clients: Typically 8-15% margins due to structured pricing, compliance overhead
- Private sector: 15-25% margins, higher for specialized services
- Technology projects: 20-30% margins for innovation/IP development
- Consulting services: 25-40% margins for expertise-based work
- Factor in: project complexity, competition level, relationship value, repeat business potential

FUTURE BUSINESS OPPORTUNITIES:
- Long-term contracts: Assess renewal likelihood (government 60-80%, private 40-70%)
- Client portfolio expansion: Large enterprises offer 2-5x follow-on opportunities
- Technology platforms: Assess scalability to other departments/subsidiaries
- Strategic partnerships: Evaluate potential for ongoing collaboration
- Market positioning: Consider industry leadership and reference value

STRATEGIC VALUE INDICATORS:
- New market entry: Premium for market expansion opportunities
- Technology innovation: Value IP development and competitive advantages
- Client relationship tier: Fortune 500 vs SME strategic importance
- Geographic expansion: Assess regional growth potential
- Capability building: Evaluate internal team development value

CRITICAL FOR QUALIFICATION: The qualification scoring process requires actual values for budget and timeline. When these are missing from the RFP, you MUST provide estimated ranges that can be used for scoring (not null values).

Return ONLY valid JSON:
{{
  "client_and_opportunity": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "estimated_contract_value": {{"value": "Provide estimated range like '$200K-400K' based on RFP scope and client type", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "project_objectives": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "scope_of_work": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "timeline": {{"value": "Provide estimated range like '6-12 months' based on RFP scope and complexity", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "submission_deadline": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "client_type": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "industry_sector": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "region": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "rfp_type": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "complexity_indicators": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}},
  "additional_notes": {{"value": "...", "source": "Extracted/Estimated", "confidence_level": "High/Medium/Low", "reasoning": "..."}}
}}

Use null for entire field if no information can be determined.
"""

def extract_rfp_data(pdf_path: Optional[Path] = None, user_context: Optional[UserContext] = None) -> tuple[Optional[RFPData], Optional[DeliverablesData]]:
    """
    Extract RFP data from PDF or user context.

    Supports 3 modes:
    1. PDF only: Extract from PDF file
    2. PDF + context: Extract from PDF, supplement with context
    3. Context only: Extract from user_context.rfp_content
    """
    pdf_text = ""
    context_note = ""

    # PRIORITY 1: Use context if provided (pre-extracted from UI)
    if user_context and user_context.rfp_content:
        print(f"📄 Using pre-extracted RFP content from context...")
        pdf_text = user_context.rfp_content

        # Add additional_info as supplementary context if provided
        if user_context.additional_info:
            context_note = f"\n\nADDITIONAL CONTEXT:\n{user_context.additional_info}"
    else:
        print("❌ No RFP content available from context")
        return None, None, None

    # Validate we have some content to work with
    if not pdf_text.strip():
        print("❌ No RFP content available from PDF or context")
        return None, None, None
    try:

        prompt = f"""
{get_qualification_extraction_prompt()}

RFP CONTENT:
{pdf_text}{context_note}
"""

        result = safe_generate_content(
            gemini_model,
            [prompt],
            generation_config={"temperature": 0.1, "max_output_tokens": 16384}
        )

        if not result:
            print("❌ Failed to extract RFP data")
            return None, None

        # Parse JSON string to dict
        try:
            result_dict = json.loads(result)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            return None, None

        # Convert nested dicts to EstimatedValue objects only for RFPData fields
        rfp_field_names = set(RFPData.model_fields.keys())
        for field_name, field_data in result_dict.items():
            if field_name in rfp_field_names and isinstance(field_data, dict) and field_data is not None:
                try:
                    result_dict[field_name] = EstimatedValue(**field_data)
                except Exception as e:
                    print(f"❌ Failed to convert {field_name}: {e}")
                    result_dict[field_name] = None

        # Create simplified deliverables data (qualification doesn't need detailed deliverables)
        rfp_data = RFPData(**result_dict)
        deliv_data = DeliverablesData(
            client_and_opportunity=rfp_data.client_and_opportunity.value if rfp_data.client_and_opportunity else None,
            technical_deliverables=[],
            commercial_deliverables=[]
        )
        print(f"✅ Extracted RFP data: {rfp_data.client_and_opportunity.value if rfp_data.client_and_opportunity else 'Unknown'}")
        print(f"📊 Classification: {rfp_data.rfp_type.value if rfp_data.rfp_type else 'Unknown'} | Budget: {rfp_data.estimated_contract_value.value if rfp_data.estimated_contract_value else 'TBD'}")
        return rfp_data, deliv_data, pdf_text
    except Exception as e:
        print(f"❌ Error processing RFP: {e}")
        return None, None, None

def get_comprehensive_evaluation_prompt(rfp_data: RFPData, capabilities_data: CapabilitiesData, matrix: QualificationMatrix) -> str:
    """Generate comprehensive prompt for evaluating ALL criteria in one API call using rich JSON context."""

    # --- Build rich capability context (Simplified for response, assume logic is correct) ---
    granite_capabilities = []
    for c in capabilities_data.granite_mena:
        cap_str = f"- {c.name}"
        if c.category:
            cap_str += f" (Category: {c.category})"
        if c.capabilities:
            cap_str += f"\n  Capabilities: {', '.join(c.capabilities)}"
        if c.industry_focus:
            cap_str += f"\n  Industry Focus: {', '.join(c.industry_focus)}"
        granite_capabilities.append(cap_str)

    partner_capabilities = []
    for p in capabilities_data.partners:
        partner_str = f"- {p.name}"
        if p.category:
            partner_str += f" (Category: {p.category})"
        if p.capabilities:
            partner_str += f"\n  Capabilities: {', '.join(p.capabilities)}"
        partner_capabilities.append(partner_str) # Simplified other partner attributes for brevity here

    criteria_context = []
    for criterion in matrix.criteria:
        criteria_context.append(f"""
Criterion: {criterion.name}
Options: {criterion.options}
Scores: {criterion.scores} (1=Poor, 2=Fair, 3=Good, 4=Excellent)
Weight: {criterion.weight}""")
    # -----------------------------------

    # Use a large multi-line string for the prompt content, ensuring no accidental continuation characters.
    return f"""
You are an expert bid manager with 15+ years experience evaluating RFPs for strategic qualification decisions.

RFP DETAILS (with source information in brackets [Source]):
- Client & Opportunity: {rfp_data.client_and_opportunity.value if rfp_data.client_and_opportunity else 'Not specified'} [{rfp_data.client_and_opportunity.source if rfp_data.client_and_opportunity else 'N/A'}]
- Contract Value: {rfp_data.estimated_contract_value.value if rfp_data.estimated_contract_value else 'Not specified'} [{rfp_data.estimated_contract_value.source if rfp_data.estimated_contract_value else 'N/A'}]
- Project Type: {rfp_data.rfp_type.value if rfp_data.rfp_type else 'Not specified'} [{rfp_data.rfp_type.source if rfp_data.rfp_type else 'N/A'}]
- Client Type: {rfp_data.client_type.value if rfp_data.client_type else 'Not specified'} [{rfp_data.client_type.source if rfp_data.client_type else 'N/A'}]
- Region: {rfp_data.region.value if rfp_data.region else 'Not specified'} [{rfp_data.region.source if rfp_data.region else 'N/A'}]
- Timeline: {rfp_data.timeline.value if rfp_data.timeline else 'Not specified'} [{rfp_data.timeline.source if rfp_data.timeline else 'N/A'}]
- Scope: {rfp_data.scope_of_work.value if rfp_data.scope_of_work else 'Not specified'} [{rfp_data.scope_of_work.source if rfp_data.scope_of_work else 'N/A'}]
- Complexity: {rfp_data.complexity_indicators.value if rfp_data.complexity_indicators else 'Not specified'} [{rfp_data.complexity_indicators.source if rfp_data.complexity_indicators else 'N/A'}]
- Industry: {rfp_data.industry_sector.value if rfp_data.industry_sector else 'Not specified'} [{rfp_data.industry_sector.source if rfp_data.industry_sector else 'N/A'}]

GRANITE MENA CAPABILITIES:
{chr(10).join(granite_capabilities)}

PARTNER NETWORK:
{chr(10).join(partner_capabilities)}

QUALIFICATION CRITERIA TO EVALUATE:
{chr(10).join(criteria_context)}

***

## CRITICAL ANTI-HALLUCINATION RULES

**NEVER INVENT SPECIFIC DETAILS NOT IN THE RFP**

When RFP data is marked as **[Estimated]**, you may ONLY:
- Acknowledge what information is missing
- Provide broad category assessments based on what IS in the RFP
- Use general approximation ranges

You ABSOLUTELY MUST NOT:
- Invent specific numbers, dates, or timelines not in the RFP
- Add details from your training data or assumptions
- Create precise specifications that weren't mentioned
- Fabricate client requirements or project phases

**ACCEPTABLE ESTIMATION EXAMPLES:**
- "Budget range appears mid-market based on scope complexity mentioned in RFP"
- "Timeline likely extended given multi-stakeholder references in RFP"
- "Government client type inferred from procurement language used"
- "Competitive environment likely moderate based on specialized requirements mentioned in RFP"
- "Standard government procurement suggests 3-5 bidders typical for this scope"
- "Technology specialization requirements may limit competitor pool"

**UNACCEPTABLE FABRICATIONS:**
- "12+ months timeline" (when no timeline mentioned)
- "$100K-250K budget" (when no budget indicators exist)
- "Multi-phase delivery" (when phases not described)
- Specific regulatory requirements not mentioned in RFP

**ESTIMATION MUST CITE RFP CONTENT:**
Every estimation must reference specific text, requirements, or indicators actually present in the RFP document.

## ENHANCED ESTIMATION GUIDANCE FOR MISSING RFP DATA

**When data is missing, use these comprehensive factors based on RFP content:**

**BUDGET ESTIMATION FACTORS:**
- Government: $50K-200K (simple), $200K-1M (complex), $1M+ (enterprise systems)
- Private SME: $25K-150K (consulting), $150K-500K (technology implementation)
- Enterprise: $100K-500K (departmental), $500K-2M+ (enterprise-wide)
- Technology complexity: +50% for integration, +100% for custom development
- Stakeholder complexity: +25% per additional department/external entity mentioned

**TIMELINE ESTIMATION FACTORS:**
- Government: Add 50% to standard timelines for compliance/approvals
- Simple projects: 3-6 months, Complex: 6-18 months, Enterprise: 12-24 months
- Multi-stakeholder: +3 months per external stakeholder group
- Technology integration: +6 months for legacy system integration

**BUSINESS POTENTIAL ESTIMATION:**
- Client size (Fortune 500): High future business potential (3-5x follow-on)
- Government long-term: Medium-High renewal potential (60-80% for 3+ years)
- New market entry: High strategic value for market positioning
- Technology platform projects: High scalability potential across organization

**PROFIT MARGIN FACTORS:**
- Government: 8-15% (structured pricing, compliance overhead)
- Private sector consulting: 20-35% (expertise premium)
- Technology/Innovation: 25-40% (IP development value)
- Long-term partnerships: +5-10% margin improvement over time

**STRATEGIC VALUE INDICATORS:**
- New geographic market: High strategic importance
- Fortune 500 client: High reference value and portfolio enhancement
- Emerging technology: High capability building and competitive advantage
- Partnership opportunities: Medium-High for ecosystem expansion

**COMPETITIVE ENVIRONMENT FACTORS:**
- Government procurement: Typically 3-7 bidders based on specialization requirements
- Technology specialization: Reduces competitor pool (fewer qualified bidders)
- Geographic requirements: Local presence requirements limit international competition
- Established relationships: Incumbent advantages in existing client relationships
- Entry barriers: Certification/compliance requirements reduce competitive field

***

EVALUATION TASK:

**MANDATORY PRE-CHECK:** Before generating any responses, verify that you are using ONLY information from:
1. The RFP content provided above
2. The capabilities data provided above
3. The qualification criteria provided above

DO NOT use external knowledge, training data assumptions, or invented details.

Evaluate ALL {len(matrix.criteria)} criteria using this CLEAR THREE-PHASE PROCESS:

PHASE 1 - DATA ANALYSIS:
- Review all RFP data provided above (marked as [Extracted] or [Estimated])
- Review capabilities and qualification criteria
- Identify which RFP data points were marked as [Estimated] (meaning they had to be approximated due to missing information in the original RFP)

PHASE 2 - MISSING DATA HANDLING:
- For criteria that require RFP data marked as [Estimated], document how that missing data was originally estimated
- Use the Enhanced Estimation Guidance factors to justify the approximation
- This justification goes in the "missing_data_justification" field

PHASE 3 - QUALIFICATION SCORING:
- Treat ALL data (both [Extracted] and [Estimated]) as input information for scoring
- Score each criterion using ALL available information
- Provide strategic reasoning for each score in the "reasoning" field

Return ONLY JSON with this exact structure:
{{
  "evaluations": [
    {{
      "criterion": "{matrix.criteria[0].name}",
      "selected_option_index": <int 0-3>,
      "selected_option": "<exact string from options>",
      "score": <int 1-4>,
      "reasoning": "Strategic rationale for this score using all available data. Key factors from RFP, capabilities, and criteria that led to this decision. Why this option was selected over others.",
      "missing_data_justification": "MISSING FROM RFP: [what wasn't specified] ESTIMATION BASIS: [RFP indicators used + market factors] CONFIDENCE: [level with reasoning]" OR null if only [Extracted] data was used
    }},
    // ... continue for all {len(matrix.criteria)} criteria
  ]
}}

IMPORTANT GUIDELINES:
- Use partner reliability scores and strategic fit data for "Ability to Deliver" assessments
- **ALWAYS NAME SPECIFIC PARTNERS** when discussing partner capabilities (e.g., "Accenture's cloud expertise" not "partner network capabilities")
- **ALWAYS NAME SPECIFIC CAPABILITIES** when referencing capabilities (e.g., "Digital Transformation and Cloud Migration" not "our capabilities")
- Reference specific partner agreement status and reliability scores where relevant
- Consider contract value and complexity when evaluating revenue and margin potential
- Provide strategic, actionable reasoning for each score with concrete examples

FIELD USAGE INSTRUCTIONS:

**"reasoning" field (ALWAYS required):**
- Explain why this qualification score was assigned using bullet points for clarity
- Use all available information (both extracted from RFP and estimated data)
- Focus on strategic rationale and key decision factors
- **Name specific capabilities and partners** when referencing them (never use generic terms like "our capabilities" or "partner network")
- Reference specific RFP requirements and qualification criteria
- Provide concrete examples and evidence for your scoring decision
- **FORMAT**: Use bullet points (•) for each key reasoning point to improve readability

**"missing_data_justification" field (ONLY when needed):**
- Fill ONLY if the scoring used RFP data marked as [Estimated]
- Use this 3-part format: MISSING FROM RFP → ESTIMATION BASIS → CONFIDENCE

**Simple Template:**
```
MISSING FROM RFP: [what wasn't specified]
ESTIMATION BASIS: [specific RFP indicators used + market factors applied]
CONFIDENCE: [High/Medium/Low with brief reasoning]
```

ENHANCED EXAMPLES:

"reasoning": "• Strong capability match with RFP requirements through Granite MENA's Digital Transformation and Cloud Migration capabilities\n• Accenture and Microsoft partners provide proven coverage in Middle East regions with cloud infrastructure expertise\n• Estimated 20-25% profit margin based on technology consulting nature and government client stability\n• High strategic value for regional expansion and technology portfolio development"

"missing_data_justification":
```
- Missing: Budget, timeline, and future business potential not specified
- Basis:
• Government client + system integration scope suggests $200K-400K range
• Complex integration typically 12-18 months for government projects based on compliance requirements mentioned in RFP
• Government contracts typically offer 60-80% renewal likelihood with 15% margin potential due to structured pricing
- Confidence: Medium due to clear government indicators but unclear scope specifics
```

**BUSINESS POTENTIAL EXAMPLE:**
"missing_data_justification":
```
- Missing: Profit margin potential and strategic value not specified
- Basis:
• Fortune 500 client mentioned suggests high future business potential (3-5x follow-on opportunities)
• Technology platform project indicates 25-35% margin potential due to IP development value
• New geographic market entry provides high strategic positioning value for Middle East expansion
- Confidence: High due to clear client tier and technology scope indicators in RFP
```

**VALIDATION:**
- missing_data_justification must use 3-part format: MISSING FROM RFP → ESTIMATION BASIS → CONFIDENCE
- All estimations must cite specific RFP content
- Never reference qualification scores in missing_data_justification field

Return ONLY the JSON structure specified above. No additional text or explanations.
"""

def generate_qualification_context(rfp_data: RFPData, capabilities_data: CapabilitiesData = None, user_context: Optional[UserContext] = None) -> QualificationContext:
    """Generate intelligent qualification context with estimation and analysis."""

    # Use budget information from RFP data
    estimated_budget = rfp_data.estimated_contract_value if rfp_data.estimated_contract_value else EstimatedValue(
        value="No budget information available",
        confidence_level="Low",
        reasoning="No budget data found in RFP",
        source="Missing"
    )

    # Use timeline information from RFP data
    estimated_timeline = rfp_data.timeline if rfp_data.timeline else EstimatedValue(
        value="No timeline information available",
        confidence_level="Low",
        reasoning="No timeline data found in RFP",
        source="Missing"
    )

    return QualificationContext(
        estimated_budget=estimated_budget,
        estimated_timeline=estimated_timeline,
        complexity_assessment=rfp_data.complexity_indicators.value if rfp_data.complexity_indicators else "Requires detailed technical analysis",
        strategic_fit_notes=f"RFP Type: {rfp_data.rfp_type.value if rfp_data.rfp_type else 'TBD'}, Client: {rfp_data.client_type.value if rfp_data.client_type else 'TBD'}",
        capability_gaps=[],  # Will be populated during evaluation
        competitive_advantages=[],  # Will be populated during evaluation
        risk_factors=[],
        opportunity_factors=[]
    )

def evaluate_rfp_qualification(pdf_base: str, rfp_data: RFPData, deliv_data: DeliverablesData, capabilities_data: CapabilitiesData, matrix: QualificationMatrix, user_context: Optional[UserContext] = None) -> QualificationReport:
    print(f"🚀 Evaluating RFP qualification for {pdf_base}...")
    print(f"📊 Evaluating ALL {len(matrix.criteria)} criteria in single comprehensive analysis...")

    analyses = []
    total_weighted_score = 0.0

    # Generate qualification context first
    qualification_context = generate_qualification_context(rfp_data, capabilities_data, user_context)

    # Single comprehensive evaluation with full JSON context
    prompt = get_comprehensive_evaluation_prompt(rfp_data, capabilities_data, matrix)

    result = safe_generate_content(
        gemini_model,
        [prompt],
        generation_config={"temperature": 0.1, "max_output_tokens": 16384}
    )

    if not result:
        print("⚠️ No response from comprehensive evaluation, using defaults")
        # Fallback to defaults for all criteria
        for criterion in matrix.criteria:
            selected_option = criterion.options[0]
            score = criterion.scores[0]
            reasoning = f"• No response for comprehensive evaluation\n• Defaulted to lowest for {criterion.name}"
            weighted_score = score * criterion.weight
            total_weighted_score += weighted_score
            analyses.append(QualificationAnalysis(
                criterion=criterion.name,
                selected_option=selected_option,
                score=score,
                weighted_score=weighted_score,
                reasoning=reasoning,
                missing_data_justification=None
            ))
    else:
        try:
            # Parse comprehensive JSON response
            result_dict = json.loads(result)
            evaluations = result_dict.get("evaluations", [])

            # Create lookup for criteria by name
            criteria_lookup = {c.name: c for c in matrix.criteria}

            for eval_data in evaluations:
                criterion_name = eval_data.get("criterion", "")
                criterion = criteria_lookup.get(criterion_name)

                if not criterion:
                    print(f"⚠️ Unknown criterion in response: {criterion_name}")
                    continue

                try:
                    if "selected_option_index" in eval_data:
                        idx = int(eval_data["selected_option_index"])
                        if 0 <= idx < len(criterion.options):
                            selected_option = criterion.options[idx]
                            score = criterion.scores[idx]
                        else:
                            raise ValueError("index out of range")
                    else:
                        raw_option = str(eval_data.get("selected_option", "")).strip()
                        if raw_option in criterion.options:
                            idx = criterion.options.index(raw_option)
                            selected_option = criterion.options[idx]
                            score = criterion.scores[idx]
                        else:
                            matches = difflib.get_close_matches(raw_option, criterion.options, n=1, cutoff=0.6)
                            if matches:
                                selected_option = matches[0]
                                idx = criterion.options.index(selected_option)
                                score = criterion.scores[idx]
                            else:
                                raw_score = eval_data.get("score")
                                if isinstance(raw_score, int) and raw_score in criterion.scores:
                                    idx = criterion.scores.index(raw_score)
                                    selected_option = criterion.options[idx]
                                    score = criterion.scores[idx]
                                else:
                                    selected_option = criterion.options[0]
                                    score = criterion.scores[0]

                    reasoning_raw = eval_data.get("reasoning", "")
                    # Preserve the AI's original reasoning structure instead of forcing bullets
                    reasoning = reasoning_raw.strip() if reasoning_raw.strip() else f"• No reasoning provided for {criterion.name}"

                    # Extract AI estimation reasoning if provided
                    missing_data_justification = eval_data.get("missing_data_justification")
                    if missing_data_justification and missing_data_justification != "null":
                        # Preserve the AI's original justification structure
                        missing_data_justification = missing_data_justification.strip()
                    else:
                        missing_data_justification = None

                except Exception as e:
                    print(f"⚠️ Invalid data for {criterion_name}: {e}")
                    selected_option = criterion.options[0]
                    score = criterion.scores[0]
                    reasoning = f"• Error parsing data for {criterion_name}\n• Defaulted to lowest"
                    missing_data_justification = None

                weighted_score = score * criterion.weight
                total_weighted_score += weighted_score
                analyses.append(QualificationAnalysis(
                    criterion=criterion.name,
                    selected_option=selected_option,
                    score=score,
                    weighted_score=weighted_score,
                    reasoning=reasoning,
                    missing_data_justification=missing_data_justification
                ))

            # Handle any missing criteria
            evaluated_criteria = {a.criterion for a in analyses}
            for criterion in matrix.criteria:
                if criterion.name not in evaluated_criteria:
                    print(f"⚠️ Missing evaluation for {criterion.name}, using default")
                    selected_option = criterion.options[0]
                    score = criterion.scores[0]
                    reasoning = f"• Missing from comprehensive evaluation\n• Defaulted to lowest for {criterion.name}"
                    weighted_score = score * criterion.weight
                    total_weighted_score += weighted_score
                    analyses.append(QualificationAnalysis(
                        criterion=criterion.name,
                        selected_option=selected_option,
                        score=score,
                        weighted_score=weighted_score,
                        reasoning=reasoning,
                        missing_data_justification=None
                    ))

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed for comprehensive evaluation: {e}")
            # Fallback to defaults for all criteria
            for criterion in matrix.criteria:
                selected_option = criterion.options[0]
                score = criterion.scores[0]
                reasoning = f"• JSON parse error for comprehensive evaluation\n• Defaulted to lowest for {criterion.name}"
                weighted_score = score * criterion.weight
                total_weighted_score += weighted_score
                analyses.append(QualificationAnalysis(
                    criterion=criterion.name,
                    selected_option=selected_option,
                    score=score,
                    weighted_score=weighted_score,
                    reasoning=reasoning,
                    missing_data_justification=None
                ))

    # Calculate proper weighted average using sum of weights
    total_weights = sum(criterion.weight for criterion in matrix.criteria) if matrix.criteria else 1.0
    avg_weighted_score = total_weighted_score / total_weights if total_weights > 0 else 0.0
    threshold = 2.5
    qualifies = avg_weighted_score >= threshold

    # Generate executive summary and recommendations
    exec_summary = f"""
RFP Qualification Analysis for {rfp_data.client_and_opportunity.value if rfp_data.client_and_opportunity else 'Unknown Opportunity'}

DECISION: {'PURSUE' if qualifies else 'DECLINE'} (Score: {avg_weighted_score:.2f}/{threshold})
PROJECT TYPE: {rfp_data.rfp_type.value if rfp_data.rfp_type else 'TBD'} | CLIENT: {rfp_data.client_type.value if rfp_data.client_type else 'TBD'}
BUDGET: {qualification_context.estimated_budget.value if qualification_context.estimated_budget else 'TBD'}
TIMELINE: {qualification_context.estimated_timeline.value if qualification_context.estimated_timeline else 'TBD'}
""".strip()

    recommendations = []
    if qualifies:
        recommendations.append("Proceed with bid preparation and resource allocation")
        recommendations.append("Conduct detailed capability assessment for delivery planning")
        if avg_weighted_score < 3.0:
            recommendations.append("Address identified risks before proposal submission")
    else:
        recommendations.append("Do not pursue this opportunity at this time")
        recommendations.append("Consider re-evaluation if RFP terms or scope change")
        recommendations.append("Use learnings for future similar opportunities")

    report = QualificationReport(
        client_and_opportunity=rfp_data.client_and_opportunity.value if rfp_data.client_and_opportunity else "Unknown",
        analysis_date=time.strftime("%Y-%m-%d %H:%M:%S"),
        total_score=avg_weighted_score,
        qualifies=qualifies,
        threshold=threshold,
        analyses=analyses,
        qualification_context=qualification_context,
        rfp_classification=f"{rfp_data.rfp_type.value if rfp_data.rfp_type else 'Unknown'}-{rfp_data.client_type.value if rfp_data.client_type else 'Unknown'}",
        executive_summary=exec_summary,
        recommendations=recommendations
    )

    return report

def create_qualification_excel_report(report: QualificationReport) -> Workbook:
    wb = Workbook()

    # Executive Summary Sheet
    exec_ws = wb.active
    exec_ws.title = "Executive Summary"

    # Header
    header_cell = exec_ws.cell(1, 1, "RFP QUALIFICATION REPORT")
    header_cell.font = Font(bold=True, size=16)
    header_cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")
    header_cell.font = Font(bold=True, size=16, color="FFFFFF")

    # Executive Summary
    exec_ws.cell(3, 1, "EXECUTIVE SUMMARY").font = Font(bold=True, size=12)

    # Format executive summary with proper line breaks and alignment
    summary_cell = exec_ws.cell(4, 1, report.executive_summary or "No summary available")
    summary_cell.alignment = Alignment(wrap_text=True, vertical='top')
    exec_ws.row_dimensions[4].height = 120  # Increase height for multi-line content

    # Key Metrics
    exec_ws.cell(6, 1, "KEY METRICS").font = Font(bold=True, size=12)
    exec_ws.cell(7, 1, f"Overall Score: {report.total_score:.2f} / 4.0")
    exec_ws.cell(8, 1, f"Threshold: {report.threshold:.2f}")
    exec_ws.cell(9, 1, f"Total Criteria: {len(report.analyses)}")
    decision_cell = exec_ws.cell(10, 1, f"DECISION: {'PURSUE' if report.qualifies else 'DECLINE'}")
    decision_cell.font = Font(bold=True, color="008000" if report.qualifies else "FF0000")

    # Recommendations (move up since we removed classification)
    if report.recommendations:
        exec_ws.cell(12, 1, "RECOMMENDATIONS").font = Font(bold=True, size=12)
        for i, rec in enumerate(report.recommendations, 13):
            exec_ws.cell(i, 1, f"• {rec}")

    # Estimated Values (if available)
    if report.qualification_context:
        context = report.qualification_context
        exec_ws.cell(16, 1, "ESTIMATED VALUES").font = Font(bold=True, size=12)

        if context.estimated_budget and context.estimated_budget.value:
            source_indicator = "[AI Estimated]" if context.estimated_budget.source == "Estimated" else "[From RFP]"
            budget_text = f"Budget: {context.estimated_budget.value} {source_indicator}\nConfidence Level: {context.estimated_budget.confidence_level}"
            budget_cell = exec_ws.cell(17, 1, budget_text)
            budget_cell.alignment = Alignment(wrap_text=True, vertical='top')
            exec_ws.row_dimensions[17].height = 40

        if context.estimated_timeline and context.estimated_timeline.value:
            source_indicator = "[AI Estimated]" if context.estimated_timeline.source == "Estimated" else "[From RFP]"
            timeline_text = f"Timeline: {context.estimated_timeline.value} {source_indicator}\nConfidence Level: {context.estimated_timeline.confidence_level}"
            timeline_cell = exec_ws.cell(18, 1, timeline_text)
            timeline_cell.alignment = Alignment(wrap_text=True, vertical='top')
            exec_ws.row_dimensions[18].height = 40

    # Detailed Analysis Sheet
    detail_ws = wb.create_sheet("Detailed Analysis")

    headers = ["Criterion", "Selected Option", "Score", "Weight", "Weighted Score", "Reasoning", "Missing Data Justification"]
    for col, header in enumerate(headers, 1):
        cell = detail_ws.cell(1, col, header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(fill_type="solid", fgColor="E7E6E6")
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    # Create lookup for actual weights from matrix
    weight_lookup = {c.name: c.weight for c in report.analyses} if hasattr(report, 'matrix') else {}

    # Qualification Matrix Data
    for i, analysis in enumerate(report.analyses, 2):
        detail_ws.cell(i, 1, analysis.criterion)
        detail_ws.cell(i, 2, analysis.selected_option)
        detail_ws.cell(i, 3, f"{analysis.score}/4")  # Show as "3/4" format

        # Use the actual weight from the analysis (which comes from matrix)
        weight = analysis.weighted_score / analysis.score if analysis.score > 0 else 0.0
        detail_ws.cell(i, 4, f"{weight:.2f}")
        detail_ws.cell(i, 5, f"{analysis.weighted_score:.2f}")
        detail_ws.cell(i, 6, format_excel_text(analysis.reasoning))

        # Add Missing Data Justification column (column 7)
        missing_data_text = analysis.missing_data_justification if analysis.missing_data_justification else ""
        detail_ws.cell(i, 7, format_excel_text(missing_data_text))

        # Style the rows (now includes column 7)
        for col in range(1, 8):
            cell = detail_ws.cell(i, col)
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            cell.border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )

        # Increase row height for reasoning and justification columns to improve readability
        if analysis.reasoning or analysis.missing_data_justification:
            min_height = 60  # Base height
            # Add height based on content length
            reasoning_lines = len(analysis.reasoning.split('\n')) if analysis.reasoning else 0
            justification_lines = len(analysis.missing_data_justification.split('\n')) if analysis.missing_data_justification else 0
            content_height = max(reasoning_lines, justification_lines) * 15
            detail_ws.row_dimensions[i].height = max(min_height, content_height)

    # Column widths
    detail_ws.column_dimensions['A'].width = 25  # Criterion
    detail_ws.column_dimensions['B'].width = 45  # Selected Option
    detail_ws.column_dimensions['C'].width = 8   # Score
    detail_ws.column_dimensions['D'].width = 10  # Weight
    detail_ws.column_dimensions['E'].width = 12  # Weighted Score
    detail_ws.column_dimensions['F'].width = 55  # Reasoning (reduced to make room)
    detail_ws.column_dimensions['G'].width = 55  # Missing Data Justification

    # Add spacing before summary
    summary_row = len(report.analyses) + 4  # Extra row for spacing
    detail_ws.cell(summary_row, 1, "TOTAL WEIGHTED SCORE").font = Font(bold=True)
    detail_ws.cell(summary_row, 3, f"{report.total_score:.2f}/4.0").font = Font(bold=True)
    detail_ws.cell(summary_row, 5, f"{report.total_score:.2f}").font = Font(bold=True)

    # Add threshold row
    threshold_row = summary_row + 1
    detail_ws.cell(threshold_row, 1, "QUALIFICATION THRESHOLD").font = Font(bold=True)
    detail_ws.cell(threshold_row, 3, f"{report.threshold:.2f}/4.0").font = Font(bold=True)

    # Add qualification result with spacing
    result_row = threshold_row + 2  # Extra spacing
    result_cell = detail_ws.cell(result_row, 1, f"RESULT: {'QUALIFIES' if report.qualifies else 'DOES NOT QUALIFY'}")
    result_cell.font = Font(bold=True, color="008000" if report.qualifies else "FF0000")

    # Executive summary sheet column width
    exec_ws.column_dimensions['A'].width = 80

    return wb

from typing import List, Optional, Tuple # Added Tuple import

# ... (rest of the imports and classes remain the same)

def process_rfp_qualification(pdf_input: Optional[str] = None, user_context: Optional[UserContext] = None) -> Tuple[Optional[QualificationReport], Optional[str]]:
    """Enhanced RFP qualification processing with intelligent analysis and dual output.

    Supports 3 modes:
    1. PDF only: Provide pdf_input, extract from PDF
    2. PDF + context: Provide both, use PDF as primary with context supplement
    3. Context only: Provide user_context with rfp_content, no PDF needed

    Args:
        pdf_input: Optional path to PDF file or base name
        user_context: Optional user context (can contain full RFP text in rfp_content field)
    """
    pdf_base = None

    # Determine the base name for the report
    if pdf_input:
        # If pdf_input is provided, use it as the base name
        pdf_base = Path(pdf_input).stem if Path(pdf_input).suffix else str(pdf_input)
    elif user_context and user_context.rfp_content:
        # If no pdf_input but context is provided, generate a name
        import hashlib
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        context_hash = hashlib.md5(user_context.rfp_content[:100].encode()).hexdigest()[:8]
        pdf_base = f"context_rfp_{timestamp}_{context_hash}"
        print(f"\n🚀 Processing qualification from context (no PDF) at {time.strftime('%I:%M %p %Z, %B %d, %Y')}")
    else:
        print("❌ No PDF input or context provided")
        return None, None # Return None for both report and pdf_base

    if pdf_base:
        print(f"\n🚀 Processing enhanced qualification for {pdf_base} at {time.strftime('%I:%M %p %Z, %B %d, %Y')}")

    if user_context:
        print("📝 User context provided:")
        if user_context.rfp_content:
            print(f"   RFP content: {len(user_context.rfp_content)} characters")
        if user_context.additional_info:
            print(f"   Additional info: {user_context.additional_info[:100]}...")

    rfp_data, deliv_data, raw_document_text = extract_rfp_data(None, user_context)
    capabilities_data = load_json_file(CAPABILITIES_JSON, CapabilitiesData)
    matrix = load_json_file(QUALIFICATION_JSON, QualificationMatrix)

    if not rfp_data or not capabilities_data or not matrix:
        print("❌ Missing required data; cannot evaluate qualification")
        return None, None # Return None for both report and pdf_base

    report = evaluate_rfp_qualification(pdf_base, rfp_data, deliv_data, capabilities_data, matrix, user_context)

    # Save to database
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from database.db_manager import DatabaseManager

        db = DatabaseManager()

        rfp_id = pdf_base
        client_name = rfp_data.client_and_opportunity.value if rfp_data.client_and_opportunity else "Unknown Client"
        project_title = report.client_and_opportunity

        # Parse submission deadline if available
        submission_deadline = None
        if rfp_data.submission_deadline and rfp_data.submission_deadline.value:
            from dateutil import parser
            try:
                # Try to parse the human-readable date string
                parsed_date = parser.parse(rfp_data.submission_deadline.value, fuzzy=True)
                submission_deadline = parsed_date
                print(f"✅ Parsed submission deadline: {rfp_data.submission_deadline.value} -> {submission_deadline}")
            except Exception as date_error:
                print(f"⚠️  Could not parse submission deadline: {rfp_data.submission_deadline.value}")
                print(f"   Error: {date_error}")
                # Store None instead of unparseable string
                submission_deadline = None

        # Save RFP document metadata
        db.create_rfp_document(
            rfp_id=rfp_id,
            client_name=client_name,
            project_title=project_title,
            pdf_path=None, # No longer processing PDFs directly
            submission_deadline=submission_deadline
        )

        # Save complete RFP raw data as JSONB
        db.save_rfp_raw_data(
            rfp_id=rfp_id,
            rfp_data=rfp_data.model_dump()
        )

        # Save raw document text
        if raw_document_text:
            db.save_raw_document_text(
                rfp_id=rfp_id,
                raw_text=raw_document_text
            )
            print(f"✅ Saved raw document text ({len(raw_document_text)} characters)")

        # Save complete qualification report as JSONB
        try:
            qualification_id = db.save_qualification_results(
                rfp_id=rfp_id,
                qualification_data=report.model_dump()
            )
            print(f"✅ Saved complete qualification data to database (ID: {qualification_id})")
        except Exception as save_error:
            print(f"❌ CRITICAL: Failed to save qualification to database!")
            print(f"   Error: {save_error}")
            import traceback
            traceback.print_exc()
            print(f"⚠️  WARNING: Qualification completed but NOT saved to database!")

    except Exception as e:
        print(f"⚠️ Failed to save RFP metadata to database: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n✅ QUALIFICATION COMPLETE")
    print(f"🎯 Decision: {'PURSUE' if report.qualifies else 'DECLINE'} (Score: {report.total_score:.2f}/{report.threshold})")
    print(f"📊 Classification: {report.rfp_classification}")
    print(f"💰 Budget: {report.qualification_context.estimated_budget.value if report.qualification_context and report.qualification_context.estimated_budget else 'TBD'}")
    print(f"⏰ Timeline: {report.qualification_context.estimated_timeline.value if report.qualification_context and report.qualification_context.estimated_timeline else 'TBD'}")

    if report.recommendations:
        print("📋 Key Recommendations:")
        for rec in report.recommendations[:3]:
            print(f"   • {rec}")

    return report, pdf_base

    # Determine the base name for the report
    if pdf_input:
        # If pdf_input is provided, use it as the base name
        pdf_base = Path(pdf_input).stem if Path(pdf_input).suffix else str(pdf_input)
    elif user_context and user_context.rfp_content:
        # If no pdf_input but context is provided, generate a name
        import hashlib
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        context_hash = hashlib.md5(user_context.rfp_content[:100].encode()).hexdigest()[:8]
        pdf_base = f"context_rfp_{timestamp}_{context_hash}"
        print(f"\n🚀 Processing qualification from context (no PDF) at {time.strftime('%I:%M %p %Z, %B %d, %Y')}")
    else:
        print("❌ No PDF input or context provided")
        return None

    if pdf_base:
        print(f"\n🚀 Processing enhanced qualification for {pdf_base} at {time.strftime('%I:%I %p %Z, %B %d, %Y')}")

    if user_context:
        print("📝 User context provided:")
        if user_context.rfp_content:
            print(f"   RFP content: {len(user_context.rfp_content)} characters")
        if user_context.additional_info:
            print(f"   Additional info: {user_context.additional_info[:100]}...")

    rfp_data, deliv_data, raw_document_text = extract_rfp_data(None, user_context)
    capabilities_data = load_json_file(CAPABILITIES_JSON, CapabilitiesData)
    matrix = load_json_file(QUALIFICATION_JSON, QualificationMatrix)

    if not rfp_data or not capabilities_data or not matrix:
        print("❌ Missing required data; cannot evaluate qualification")
        return None

    report = evaluate_rfp_qualification(pdf_base, rfp_data, deliv_data, capabilities_data, matrix, user_context)

    # Save to database
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from database.db_manager import DatabaseManager

        db = DatabaseManager()

        rfp_id = pdf_base
        client_name = rfp_data.client_and_opportunity.value if rfp_data.client_and_opportunity else "Unknown Client"
        project_title = report.client_and_opportunity

        # Parse submission deadline if available
        submission_deadline = None
        if rfp_data.submission_deadline and rfp_data.submission_deadline.value:
            from dateutil import parser
            try:
                # Try to parse the human-readable date string
                parsed_date = parser.parse(rfp_data.submission_deadline.value, fuzzy=True)
                submission_deadline = parsed_date
                print(f"✅ Parsed submission deadline: {rfp_data.submission_deadline.value} -> {submission_deadline}")
            except Exception as date_error:
                print(f"⚠️  Could not parse submission deadline: {rfp_data.submission_deadline.value}")
                print(f"   Error: {date_error}")
                # Store None instead of unparseable string
                submission_deadline = None

        # Save RFP document metadata
        db.create_rfp_document(
            rfp_id=rfp_id,
            client_name=client_name,
            project_title=project_title,
            pdf_path=None, # No longer processing PDFs directly
            submission_deadline=submission_deadline
        )

        # Save complete RFP raw data as JSONB
        db.save_rfp_raw_data(
            rfp_id=rfp_id,
            rfp_data=rfp_data.model_dump()
        )

        # Save raw document text
        if raw_document_text:
            db.save_raw_document_text(
                rfp_id=rfp_id,
                raw_text=raw_document_text
            )
            print(f"✅ Saved raw document text ({len(raw_document_text)} characters)")

        # Save complete qualification report as JSONB
        try:
            qualification_id = db.save_qualification_results(
                rfp_id=rfp_id,
                qualification_data=report.model_dump()
            )
            print(f"✅ Saved complete qualification data to database (ID: {qualification_id})")
        except Exception as save_error:
            print(f"❌ CRITICAL: Failed to save qualification to database!")
            print(f"   Error: {save_error}")
            import traceback
            traceback.print_exc()
            print(f"⚠️  WARNING: Qualification completed but NOT saved to database!")

    except Exception as e:
        print(f"⚠️ Failed to save RFP metadata to database: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n✅ QUALIFICATION COMPLETE")
    print(f"🎯 Decision: {'PURSUE' if report.qualifies else 'DECLINE'} (Score: {report.total_score:.2f}/{report.threshold})")
    print(f"📊 Classification: {report.rfp_classification}")
    print(f"💰 Budget: {report.qualification_context.estimated_budget.value if report.qualification_context and report.qualification_context.estimated_budget else 'TBD'}")
    print(f"⏰ Timeline: {report.qualification_context.estimated_timeline.value if report.qualification_context and report.qualification_context.estimated_timeline else 'TBD'}")

    if report.recommendations:
        print("📋 Key Recommendations:")
        for rec in report.recommendations[:3]:
            print(f"   • {rec}")

    return report, pdf_base

def process_rfp_with_context(pdf_input: str, budget_hints: str = None, strategic_priorities: str = None,
                           additional_context: str = None) -> Optional[QualificationReport]:
    """Agent-ready function with context parameters.

    Args:
        pdf_input: Can be either a full path to PDF file or just the base name
    """
    user_context = None
    if budget_hints or strategic_priorities or additional_context:
        user_context = UserContext(
            budget_hints=budget_hints,
            strategic_priorities=strategic_priorities,
            additional_context=additional_context
        )

    return process_rfp_qualification(pdf_input, user_context)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_base = sys.argv[1]
        # Support additional context via command line
        budget_hints = sys.argv[2] if len(sys.argv) > 2 else None
        strategic_priorities = sys.argv[3] if len(sys.argv) > 3 else None

        user_context = None
        if budget_hints or strategic_priorities:
            user_context = UserContext(budget_hints=budget_hints, strategic_priorities=strategic_priorities)

        process_rfp_qualification(pdf_base, user_context)
    else:
        # pdf_base = "RFP_gary"
        pdf_base = "interesting"
        # pdf_base = "KHDA_RFP_Website"
        process_rfp_qualification(pdf_base)
