import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

from agent.config.settings import settings
from agent.database.db_singleton import get_db

genai.configure(api_key=settings.GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)

db = get_db()


class Stakeholder(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    influence: Optional[str] = None
    relationship_with_granite: Optional[str] = None


class BusinessGoal(BaseModel):
    category: str
    goals: List[str]


class Challenge(BaseModel):
    category: str
    challenges: List[str]


class KPI(BaseModel):
    kpi_name: str
    target: Optional[str] = None


class CompetitiveLandscape(BaseModel):
    industry_leaders: List[str] = Field(default_factory=list)
    vendors_in_play: List[str] = Field(default_factory=list)
    client_perception: Optional[str] = None


class BudgetInfo(BaseModel):
    budget_owners: List[str] = Field(default_factory=list)
    indicative_budget: Optional[str] = None
    procurement_process: Optional[str] = None
    budget_approvers: List[str] = Field(default_factory=list)


class RisksBlockers(BaseModel):
    potential_blockers: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_strategy: Optional[str] = None
    champions: List[str] = Field(default_factory=list)


class ClientOverview(BaseModel):
    context: Optional[str] = None
    organization_overview: Optional[str] = None
    size_of_business: Optional[str] = None
    industry: Optional[str] = None
    region_focus: Optional[str] = None
    digital_maturity: Optional[str] = None
    business_model: Optional[str] = None
    recent_news: Optional[str] = None
    stakeholders: List[Stakeholder] = Field(default_factory=list)
    business_goals: List[BusinessGoal] = Field(default_factory=list)
    challenges: List[Challenge] = Field(default_factory=list)
    kpis: List[KPI] = Field(default_factory=list)
    competitive_landscape: Optional[CompetitiveLandscape] = None
    budget_info: Optional[BudgetInfo] = None
    risks_blockers: Optional[RisksBlockers] = None


class ValueMapping(BaseModel):
    client_goal: str
    granite_capability: str
    partners_suggested: List[str] = Field(default_factory=list)
    high_level_solution: Optional[str] = None


class QuickWin(BaseModel):
    title: str
    description: str
    target_stakeholder: Optional[str] = None
    short_term_goal_alignment: Optional[str] = None


class LongTermOpportunity(BaseModel):
    title: str
    description: str
    business_potential: Optional[str] = None


class Differentiator(BaseModel):
    title: str
    description: str


class GraniteOpportunity(BaseModel):
    value_mappings: List[ValueMapping] = Field(default_factory=list)
    quick_wins: List[QuickWin] = Field(default_factory=list)
    long_term_opportunities: List[LongTermOpportunity] = Field(default_factory=list)
    differentiators: List[Differentiator] = Field(default_factory=list)
    bid_win_strategy_notes: Optional[str] = None


class ClientBrief(BaseModel):
    client_overview: ClientOverview
    granite_opportunity: GraniteOpportunity


def extract_client_brief_from_notes(
    meeting_notes: str,
    granite_capabilities: Optional[List[Dict]] = None,
    partners_data: Optional[List[Dict]] = None,
    past_rfps: Optional[List[Dict]] = None
) -> ClientBrief:
    context_info = ""

    if granite_capabilities:
        context_info += "\n\n### GRANITE MENA CAPABILITIES:\n"
        for cap in granite_capabilities[:20]:
            context_info += f"- {cap.get('name')}: {', '.join(cap.get('capabilities', []))}\n"

    if partners_data:
        context_info += "\n\n### AVAILABLE PARTNERS:\n"
        for partner in partners_data[:30]:
            context_info += f"- {partner.get('name')} ({partner.get('category')}): {', '.join(partner.get('capabilities', []))}\n"

    if past_rfps:
        context_info += "\n\n### PAST ENGAGEMENT HISTORY:\n"
        for rfp in past_rfps[:5]:
            title = rfp.get('project_title', 'Unknown')
            status = rfp.get('status', 'Unknown')
            qualifies = rfp.get('qualifies', False)
            score = rfp.get('qualification_score', 0)
            budget = rfp.get('estimated_budget', 'Unknown')
            requirements = rfp.get('key_requirements', '')

            # Build summary line
            summary = f"- {title} | Status: {status} | Won: {qualifies}"
            if score > 0:
                summary += f" | Score: {score}"
            if budget != 'Unknown':
                summary += f" | Budget: {budget}"
            if requirements:
                # Limit requirements to first few items
                req_list = [r.strip() for r in requirements.split(',')[:3]]
                summary += f" | Key needs: {', '.join(req_list)}"

            context_info += summary + "\n"

    prompt = f"""You are an expert business analyst. Extract structured client brief information from meeting notes.

MEETING NOTES:
{meeting_notes}

AVAILABLE CONTEXT:
{context_info}

Extract the following information in valid JSON format:

{{
  "client_overview": {{
    "context": "Brief overview of the organization",
    "organization_overview": "Description",
    "size_of_business": "Size/scale",
    "industry": "Industry sector",
    "region_focus": "Geographic focus",
    "digital_maturity": "Digital/Data/AI maturity level",
    "business_model": "B2B, B2C, etc.",
    "recent_news": "Recent partnerships, expansions, leadership changes",
    "stakeholders": [
      {{"name": "Name", "role": "Title", "influence": "Decision/Influence/User", "relationship_with_granite": "Existing relationship status"}}
    ],
    "business_goals": [
      {{"category": "Strategic/Short-term/Long-term", "goals": ["goal1", "goal2"]}}
    ],
    "challenges": [
      {{"category": "Business/Technology/Process", "challenges": ["challenge1", "challenge2"]}}
    ],
    "kpis": [
      {{"kpi_name": "KPI name", "target": "Target value"}}
    ],
    "competitive_landscape": {{
      "industry_leaders": ["company1", "company2"],
      "vendors_in_play": ["vendor1", "vendor2"],
      "client_perception": "How client views competitors/vendors"
    }},
    "budget_info": {{
      "budget_owners": ["name1"],
      "indicative_budget": "Budget range/amount",
      "procurement_process": "RFP-driven, partner referrals, etc.",
      "budget_approvers": ["name1"]
    }},
    "risks_blockers": {{
      "potential_blockers": ["blocker1"],
      "risk_factors": ["risk1"],
      "mitigation_strategy": "How to mitigate",
      "champions": ["Champions who can influence"]
    }}
  }},
  "granite_opportunity": {{
    "value_mappings": [
      {{
        "client_goal": "Client's goal",
        "granite_capability": "Matching Granite capability",
        "partners_suggested": ["partner1", "partner2"],
        "high_level_solution": "Brief solution description"
      }}
    ],
    "quick_wins": [
      {{
        "title": "Quick win title",
        "description": "Description",
        "target_stakeholder": "Who to target",
        "short_term_goal_alignment": "Which short-term goal this addresses"
      }}
    ],
    "long_term_opportunities": [
      {{
        "title": "Opportunity title",
        "description": "Description",
        "business_potential": "Revenue/strategic potential"
      }}
    ],
    "differentiators": [
      {{
        "title": "Differentiator title",
        "description": "Why Granite stands out"
      }}
    ],
    "bid_win_strategy_notes": "Strategic notes for winning bids with this client"
  }}
}}

INSTRUCTIONS:
- Extract all available information from the meeting notes
- Use the AVAILABLE CONTEXT to suggest relevant Granite capabilities and partners
- If information is missing, use null or empty arrays
- Ensure valid JSON output
- Be specific and actionable

Output ONLY valid JSON:"""

    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config={"temperature": 0.2}
        )

        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        brief_data = json.loads(response_text)

        client_brief = ClientBrief(**brief_data)

        return client_brief

    except Exception as e:
        print(f"❌ Error extracting client brief: {e}")
        raise


def save_client_brief_to_db(
    client_name: str,
    meeting_notes: str,
    brief_data: ClientBrief,
    meeting_date: Optional[datetime] = None,
    created_by: Optional[str] = None
) -> int:
    from agent.database.db_manager import DatabaseManager

    db_manager = DatabaseManager()

    brief_id = db_manager.save_client_brief(
        client_name=client_name,
        meeting_notes=meeting_notes,
        brief_data=brief_data.model_dump(),
        meeting_date=meeting_date,
        created_by=created_by
    )

    return brief_id
