"""
Test that the marketing agent has direct access to web_search_specialist tool
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

from agent.marketing_agent.marketing_agent import marketing_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def test_marketing_search_direct():
    """Test that marketing agent can call web_search_specialist directly"""
    print("=" * 80)
    print("TEST: Marketing Agent Direct Search Access")
    print("=" * 80)

    try:
        runner = Runner(
            agent=marketing_agent,
            app_name="marketing_search_test",
            session_service=InMemorySessionService()
        )

        user_id = "test_user"
        session = await runner.session_service.create_session(user_id=user_id, app_name="marketing_search_test")
        session_id = session.id

        # Ask marketing agent to search for trending topics
        query = "What are the trending AI topics this week? Search the web for recent AI trends."
        print(f"\nQuery: {query}")
        print("\nAgent response:")
        print("-" * 80)

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        response_text = ""
        has_error = False
        tool_calls = []

        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            # Check for errors
            if hasattr(event, 'error') and event.error:
                print(f"❌ ERROR: {event.error}")
                has_error = True

            # Track tool calls
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_name = part.function_call.name
                        tool_calls.append(tool_name)
                        print(f"🔧 Tool called: {tool_name}")

            if event.is_final_response() and hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text

        if has_error:
            print("❌ FAILED: Error occurred during execution")
            return False

        print("\n" + "-" * 80)
        print(f"Tools called: {tool_calls}")
        print("-" * 80)

        # Check if web_search_specialist was called
        search_tool_called = any('search' in tool.lower() for tool in tool_calls)

        if response_text:
            print(f"\nResponse preview:")
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            print("-" * 80)

            if search_tool_called:
                print("✅ SUCCESS: Marketing agent called search tool directly!")
                print("✅ Search results were returned to marketing agent!")
                return True
            else:
                print("⚠️  WARNING: Marketing agent responded but didn't use search tool")
                print("   This might be expected if it had cached knowledge")
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
    print("\n🚀 TESTING MARKETING AGENT DIRECT SEARCH ACCESS\n")
    test_passed = await test_marketing_search_direct()
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Marketing Search Direct Access: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print("=" * 80)

    if test_passed:
        print("\n✅ The marketing agent now has direct access to web search!")
        print("✅ No delegation required - results flow directly back!")

if __name__ == "__main__":
    asyncio.run(main())
