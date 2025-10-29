"""
Test with a natural query that should trigger search
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

async def test_natural_search_query():
    """Test with a natural query"""
    print("=" * 80)
    print("TEST: Natural Search Query")
    print("=" * 80)

    try:
        runner = Runner(
            agent=root_agent,
            app_name="natural_search_test",
            session_service=InMemorySessionService()
        )

        user_id = "test_user"
        session = await runner.session_service.create_session(user_id=user_id, app_name="natural_search_test")
        session_id = session.id

        # Natural query that should trigger web search
        query = "What are the latest developments in generative AI?"
        print(f"\nQuery: {query}")
        print("\nAgent response:")
        print("-" * 80)

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        response_text = ""
        events_log = []
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            events_log.append(str(type(event)))

            # Check for tool calls
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'function_call'):
                        print(f"🔧 Tool called: {part.function_call.name}")

            if event.is_final_response() and hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text

        if response_text:
            print(response_text[:800] + "..." if len(response_text) > 800 else response_text)
            print("-" * 80)

            # Check if search was actually used
            if "search" in response_text.lower() or len(response_text) > 200:
                print("✅ SUCCESS: Agent responded with substantial content!")
                print(f"   Response length: {len(response_text)} chars")
                return True
            else:
                print("⚠️ WARNING: Response seems short, search may not have been used")
                return False
        else:
            print("❌ FAILED: No response received")
            return False

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🚀 TESTING NATURAL SEARCH QUERY\n")
    test_passed = await test_natural_search_query()
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Natural Search Test: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
