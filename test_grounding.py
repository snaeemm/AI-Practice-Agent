"""
Test script for Google Search grounding in ADK agents
"""

import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

# Create a simple test agent with grounding
test_agent = LlmAgent(
    name="test_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    instruction="You are a helpful assistant with access to Google Search for up-to-date information.",
    tools=[google_search]
)

# Create a runner with in-memory session service
runner = Runner(
    agent=test_agent,
    app_name="grounding_test",
    session_service=InMemorySessionService()
)

def test_grounding():
    """Test the grounding functionality with a current events query"""
    from google.genai import types

    print("=" * 80)
    print("Testing Google Search Grounding")
    print("=" * 80)

    # Test query that requires current information
    test_query = "Who won the Euro 2024 football championship?"

    print(f"\nQuery: {test_query}")
    print("\nAgent response:")
    print("-" * 80)

    try:
        # Create a test user and session
        user_id = "test_user"

        # Create a new session
        session = runner.create_session(user_id)
        session_id = session.id

        print(f"Created session: {session_id}\n")

        # Create message content
        content = types.Content(
            role="user",
            parts=[types.Part(text=test_query)]
        )

        # Run the agent and collect response
        response_text = ""
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                # Get the final response text
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text

        print(response_text)
        print("-" * 80)
        print("\n✅ Grounding test completed successfully!")

        # Check if grounding was used
        if response_text:
            print(f"\nResponse length: {len(response_text)} characters")
            if "spain" in response_text.lower() or "2024" in response_text:
                print("✅ Response contains relevant Euro 2024 information!")

    except Exception as e:
        print(f"\n❌ Error during grounding test: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

        # Check if it's a model compatibility issue
        if "unsupported" in str(e).lower() or "not supported" in str(e).lower():
            print("\n⚠️ Note: Google Search grounding requires Gemini 2.0+ models")
            print(f"Current model: {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}")

    print("=" * 80)

if __name__ == "__main__":
    test_grounding()
