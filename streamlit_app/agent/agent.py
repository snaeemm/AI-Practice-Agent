import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import AgentTool

load_dotenv()

from agent.tools import (
    tool_qualify_rfp,
    tool_plan_bid_sections,
    tool_generate_client_brief
)
from agent.prompts import SYSTEM_PROMPT
from agent.database.database_agent import database_agent
from agent.ppt_agent.ppt_agent import ppt_agent
from agent.marketing_agent.marketing_agent import marketing_agent
from agent.search_agent.search_agent import search_agent

# def list_available_rfps() -> dict:
#     """
#     List all available RFP PDF files in the configured directory.
#
#     Returns a numbered list of RFP files with just filenames (not full paths).
#     The agent should present this to the user and let them select by number or name.
#     """
#     try:
#         files_dir = Path(os.getenv("FILES_DIR"))
#         if not files_dir.exists():
#             return {
#                 'success': False,
#                 'error': 'Files directory not found',
#                 'files': [],
#                 'count': 0,
#                 'message': f"Directory not found: {files_dir}"
#             }
#
#         pdf_files = sorted(list(files_dir.glob("*.pdf")))
#
#         files_info = []
#         for idx, pdf_file in enumerate(pdf_files, 1):
#             size_mb = round(pdf_file.stat().st_size / (1024*1024), 2)
#             files_info.append({
#                 'number': idx,
#                 'filename': pdf_file.name,
#                 'full_path': str(pdf_file),
#                 'size_mb': size_mb
#             })
#
#         return {
#             'success': True,
#             'files': files_info,
#             'count': len(files_info),
#             'message': f"Found {len(files_info)} RFP documents. Present to user with numbers for easy selection."
#         }
#     except Exception as e:
#         return {
#             'success': False,
#             'error': str(e),
#             'files': [],
#             'count': 0,
#             'message': f"Error accessing RFP files: {str(e)}"
#         }

# Wrap search agent as a tool using AgentTool pattern
search_tool = AgentTool(agent=search_agent)

root_agent = LlmAgent(
    name="bid_planner",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    instruction=SYSTEM_PROMPT,
    tools=[
        tool_qualify_rfp,
        tool_plan_bid_sections,
        tool_generate_client_brief,
        search_tool  # Web search specialist with Google Search grounding (wrapped as tool)
        # Note: tool_generate_image has been moved to marketing_agent for direct access
    ],
    sub_agents=[
        database_agent,
        ppt_agent,
        marketing_agent
    ]
)
