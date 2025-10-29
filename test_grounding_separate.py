"""
Test Google Search grounding separately to understand the limitation
"""
import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import google_search

load_dotenv(dotenv_path="streamlit_app/agent/.env")


async def test_search_only():
    """Test Google Search tool alone"""
    search_only_agent = LlmAgent(
        name="search_test",
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        instruction="You are a search assistant. Use Google Search to find information.",
        tools=[google_search]
    )

    print("Testing Google Search tool alone...")
    try:
        # Collect all events
        events = []
        async for event in search_only_agent.run_async("What were the major AI announcements in January 2025?"):
            events.append(event)

        print("✅ SUCCESS: Google Search works alone")
        print(f"Total events: {len(events)}")
        # Print the final text response
        for event in events:
            if hasattr(event, 'text') and event.text:
                print(f"Response: {event.text[:200]}...")
                break
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()


async def test_mixed_tools():
    """Test Google Search with custom function tool"""
    def dummy_tool() -> str:
        """A dummy custom tool"""
        return "dummy"

    print("\n" + "="*50)
    print("Testing Google Search with custom function tool...")
    try:
        mixed_agent = LlmAgent(
            name="mixed_test",
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            instruction="You are a test assistant.",
            tools=[google_search, dummy_tool]
        )

        events = []
        async for event in mixed_agent.run_async("What is 2+2?"):
            events.append(event)

        print("✅ SUCCESS: Mixed tools work!")
        print(f"Total events: {len(events)}")
    except Exception as e:
        print(f"❌ FAILED (Expected): {str(e)[:200]}")


async def main():
    await test_search_only()
    await test_mixed_tools()


if __name__ == "__main__":
    asyncio.run(main())
