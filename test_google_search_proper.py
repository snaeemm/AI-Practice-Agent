"""
Test for the AgentTool pattern with the CORRECT .env file path.
"""
import os
import sys
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment from the CORRECT location and configure the API
load_dotenv(dotenv_path="streamlit_app/agent/.env")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Add streamlit_app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import google_search, AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def test_agent_as_tool_pattern():
    """Test using a grounded agent as a tool in an orchestrator."""
    print("=" * 80)
    print("TEST: Grounded Agent as a Tool (AgentTool) with CORRECT .env path")
    print("=" * 80)

    try:
        # 1. Create the specialist Search Agent
        # With the environment correctly loaded, this should now work.
        search_agent = LlmAgent(
            name="SearchAgent",
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025"),
            instruction="You are a specialist in web searching. Your only job is to perform a Google Search query and return the findings.",
            tools=[google_search],
        )

        # 2. Wrap the Search Agent in an AgentTool
        search_tool = AgentTool(agent=search_agent)

        # 3. Define a custom tool for the orchestrator
        def get_internal_project_status(project_name: str) -> str:
            """Get the status of an internal project."""
            return f"The status of project '{project_name}' is 'On Track'."

        # 4. Equip the Orchestrator with the AgentTool and other custom tools
        orchestrator_agent = LlmAgent(
            name="Orchestrator",
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025"),
            instruction="You are an orchestrator. Use the 'SearchAgent' tool for current web information and other tools for internal data.",
            tools=[search_tool, get_internal_project_status],
        )

        runner = Runner(
            agent=orchestrator_agent,
            app_name="agent_as_tool_test",
            session_service=InMemorySessionService()
        )

        user_id = "test_user"
        session = await runner.session_service.create_session(user_id=user_id, app_name="agent_as_tool_test")
        session_id = session.id

        query = "What is the latest news about the 'Gemini' project at Google? Also, what is the status of our internal project 'Bluebird'?"
        print(f"\nQuery: {query}")
        print("\nAgent response:")
        print("-" * 80)

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        response_text = ""
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text

        if response_text:
            print(response_text)
            print("-" * 80)
            print("✅ SUCCESS: The AgentTool pattern works!")
            return True
        else:
            print("❌ FAILED: No response received")
            return False

    except Exception as e:
        print(f"❌ FAILED: An exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🚀 TESTING AGENT-AS-TOOL PATTERN WITH GROUNDING\n")
    test_passed = await test_agent_as_tool_pattern()
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Agent-as-Tool Test: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print("=" * 80)
    if test_passed:
        print("\nThis is a breakthrough! This pattern successfully isolates the grounding tool.")
        print("The root cause of the previous failures was an incorrect path to the .env file.")

if __name__ == "__main__":
    asyncio.run(main())