"""
Marketing Strategy Agent
A specialized subagent for developing marketing strategies, planning content calendars,
and coordinating multi-profile campaigns.
"""

import os
from google.adk.agents.llm_agent import LlmAgent
from dotenv import load_dotenv

load_dotenv()

from .marketing_tools import (
    tool_search_profile_by_name,
    tool_create_marketing_strategy,
    tool_get_marketing_strategy,
    tool_update_marketing_strategy,
    tool_create_marketing_profile,
    tool_link_employee_to_company,
    tool_plan_content_calendar,
    tool_suggest_next_post,
    tool_create_cross_profile_campaign
)
from .marketing_prompts import MARKETING_AGENT_PROMPT

# Import image generation tool from parent agent
from agent.tools import tool_generate_image


marketing_agent = LlmAgent(
    name="marketing_strategist",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    instruction=MARKETING_AGENT_PROMPT,
    tools=[
        tool_search_profile_by_name,
        tool_create_marketing_strategy,
        tool_get_marketing_strategy,
        tool_update_marketing_strategy,
        tool_create_marketing_profile,
        tool_link_employee_to_company,
        tool_plan_content_calendar,
        tool_suggest_next_post,
        tool_create_cross_profile_campaign,
        tool_generate_image  # Direct access to image generation
    ]
)
