"""
Quick test to verify the search agent fix works in the actual app context
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

async def test_search_integration():
    """Test that search works in the root agent"""
    print("=" * 80)
    print("TEST: Search Integration in Root Agent")
    print("=" * 80)

    try:
        runner = Runner(
            agent=root_agent,
            app_name="search_fix_test",
            session_service=InMemorySessionService()
        )

        user_id = "test_user"
        session = await runner.session_service.create_session(user_id=user_id, app_name="search_fix_test")
        session_id = session.id

        query = "What are the latest AI developments in January 2025?"
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
            print("✅ SUCCESS: Search functionality works!")
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
    print("\n🚀 TESTING SEARCH FIX\n")
    test_passed = await test_search_integration()
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Search Integration Test: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
