"""
Research Intelligence Agent
Specialized subagent for web search and market intelligence using Google Custom Search API
"""

import os
from google.adk.agents.llm_agent import LlmAgent
from dotenv import load_dotenv

load_dotenv()

from .research_tools import (
    tool_search_trending_topics,
    tool_search_company_info,
    tool_search_topic_data,
    tool_search_industry_standards
)
from .research_prompts import RESEARCH_AGENT_PROMPT


research_agent = LlmAgent(
    name="research_intelligence",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    instruction=RESEARCH_AGENT_PROMPT,
    tools=[
        tool_search_trending_topics,
        tool_search_company_info,
        tool_search_topic_data,
        tool_search_industry_standards
    ]
)
