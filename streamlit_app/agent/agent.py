import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent

load_dotenv()

from agent.tools import (
    tool_qualify_rfp,
    tool_plan_bid_sections,
    tool_query_database,
    tool_save_bid_insight,
    tool_get_bid_plan_data,
    tool_get_qualification_data,
    tool_update_qualification,
    tool_update_deliverable,
    tool_update_assignment,
    tool_add_deliverable,
    tool_remove_deliverable,
    tool_generate_report,
    tool_download_qualification_report,
    tool_download_bid_plan_report,
    tool_requalify_rfp
)
from agent.prompts import SYSTEM_PROMPT

def list_available_rfps() -> dict:
    """
    List all available RFP PDF files in the configured directory.

    Returns a numbered list of RFP files with just filenames (not full paths).
    The agent should present this to the user and let them select by number or name.
    """
    try:
        files_dir = Path(os.getenv("FILES_DIR"))
        if not files_dir.exists():
            return {
                'success': False,
                'error': 'Files directory not found',
                'files': [],
                'count': 0,
                'message': f"Directory not found: {files_dir}"
            }

        pdf_files = sorted(list(files_dir.glob("*.pdf")))

        files_info = []
        for idx, pdf_file in enumerate(pdf_files, 1):
            size_mb = round(pdf_file.stat().st_size / (1024*1024), 2)
            files_info.append({
                'number': idx,
                'filename': pdf_file.name,
                'full_path': str(pdf_file),
                'size_mb': size_mb
            })

        return {
            'success': True,
            'files': files_info,
            'count': len(files_info),
            'message': f"Found {len(files_info)} RFP documents. Present to user with numbers for easy selection."
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'files': [],
            'count': 0,
            'message': f"Error accessing RFP files: {str(e)}"
        }

root_agent = LlmAgent(
    name="bid_planner",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    instruction=SYSTEM_PROMPT,
    tools=[
        list_available_rfps,
        tool_qualify_rfp,
        tool_plan_bid_sections,
        tool_query_database,
        tool_save_bid_insight,
        tool_get_bid_plan_data,
        tool_get_qualification_data,
        tool_update_qualification,
        tool_update_deliverable,
        tool_update_assignment,
        tool_add_deliverable,
        tool_remove_deliverable,
        tool_generate_report,
        tool_download_qualification_report,
        tool_download_bid_plan_report,
        tool_requalify_rfp
    ]
)
