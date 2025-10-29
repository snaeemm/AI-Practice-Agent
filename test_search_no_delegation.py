"""
Test that the search tool works without trying to use transfer_to_agent
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment and configure API
load_dotenv(dotenv_path="streamlit_app/agent/.env")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Add streamlit_app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'streamlit_app')))

from agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def test_search_as_tool():
    """Test that search works as a tool (not delegation)"""
    print("=" * 80)
    print("TEST: Search Tool (No Delegation)")
    print("=" * 80)

    try:
        runner = Runner(
            agent=root_agent,
            app_name="search_tool_test",
            session_service=InMemorySessionService()
        )

        user_id = "test_user"
        session = await runner.session_service.create_session(user_id=user_id, app_name="search_tool_test")
        session_id = session.id

        # Explicit instruction to use the tool, not delegate
        query = "Use the web_search_specialist tool to find information about the latest AI breakthroughs in January 2025"
        print(f"\nQuery: {query}")
        print("\nAgent response:")
        print("-" * 80)

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        response_text = ""
        has_error = False
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            # Check for errors
            if hasattr(event, 'error') and event.error:
                print(f"❌ ERROR: {event.error}")
                has_error = True

            if event.is_final_response() and hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text

        if has_error:
            print("❌ FAILED: Error occurred during execution")
            return False

        if response_text:
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            print("-" * 80)
            print("✅ SUCCESS: Search tool works without delegation!")
            return True
        else:
            print("❌ FAILED: No response received")
            return False

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🚀 TESTING SEARCH AS TOOL (NOT DELEGATION)\n")
    test_passed = await test_search_as_tool()
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Search Tool Test: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
