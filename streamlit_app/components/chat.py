import streamlit as st
from agent.agent import root_agent
from agent.file_processor import extract_document_text, cleanup_gemini_file
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
import os
import traceback
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "bid_planner_app"

@st.cache_resource
def get_session_service():
    """Create singleton session service with connection pool settings"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL must be set in .env file")

    return DatabaseSessionService(
        db_url=db_url,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        pool_pre_ping=True
    )

session_service = get_session_service()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

_synced_sessions = set()

def get_mime_type(file_path: str) -> str:
    """Get MIME type based on file extension"""
    ext = file_path.lower().split('.')[-1]
    mime_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain',
        'csv': 'text/csv',
        'json': 'application/json'
    }
    return mime_types.get(ext, 'application/octet-stream')

def ensure_adk_session_sync(user_id: str, session_id: str):
    """Ensure ADK session exists using direct database insert (with caching)"""

    if session_id in _synced_sessions:
        return True

    import psycopg2

    conn = None
    cursor = None
    try:
        db_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM sessions
            WHERE app_name = %s AND user_id = %s AND id = %s
        """, (APP_NAME, user_id, session_id))

        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO sessions (app_name, user_id, id, state, create_time, update_time)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (APP_NAME, user_id, session_id, '{}'))
            conn.commit()

        _synced_sessions.add(session_id)
        return True
    except Exception as e:
        print(f"⚠️ Error ensuring ADK session: {e}")
        print(traceback.format_exc())
        return False
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


def send_message(session, user_input: str, display_message: str = None):
    """Process user message and get agent response"""
    # Save display version to history (shortened if provided)
    display_msg = display_message if display_message is not None else user_input
    session.save_user_message(display_msg)

    try:
        user_id = str(session.session['user_id'])
        ensure_adk_session_sync(user_id, session.session_id)

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )

        all_parts = []
        response_text = ""

        for event in runner.run(
            user_id=user_id,
            session_id=session.session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text = part.text
                            break
                break

            if event.content and hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        all_parts.append({"type": "thinking", "content": part.text.strip()})

                    if hasattr(part, 'function_call') and part.function_call:
                        func_name = part.function_call.name if hasattr(part.function_call, 'name') else 'function'
                        all_parts.append({"type": "tool_call", "content": func_name})

        if all_parts:
            all_parts.append({"type": "response", "content": response_text})
            import json
            session.save_assistant_message(json.dumps(all_parts))
        else:
            session.save_assistant_message(response_text)

    except Exception as e:
        error_msg = str(e)
        full_trace = traceback.format_exc()

        print("\n" + "="*80)
        print("ERROR IN AGENT PROCESSING:")
        print("="*80)
        print(full_trace)
        print("="*80 + "\n")

        if "No address associated with hostname" in error_msg or "ConnectError" in error_msg:
            error_response = "⚠️ **Network Error**: Cannot connect to Gemini API. Please check your internet connection."
        elif "GOOGLE_API_KEY" in error_msg:
            error_response = "⚠️ **API Key Error**: Please check your GOOGLE_API_KEY in .env file."
        else:
            error_response = f"⚠️ **Error**: {error_msg}\n\n```\n{full_trace}\n```"

        session.save_assistant_message(error_response)


def render_chat(session):
    st.markdown("### 💬 Chat")

    messages = session.get_history()

    if not messages:
        st.info("👋 Welcome! Start a conversation by typing a message below.")
        st.markdown("<div style='min-height: 30vh;'></div>", unsafe_allow_html=True)

    for msg in messages:
        role = msg.get('role')
        content = msg.get('content')

        if role == 'user':
            with st.chat_message("user"):
                st.markdown(content)
        elif role == 'assistant':
            with st.chat_message("assistant"):
                try:
                    import json
                    parts = json.loads(content)

                    for part in parts:
                        if part["type"] == "thinking":
                            st.markdown(f"**💭 Thinking:** {part['content']}")
                        elif part["type"] == "tool_call":
                            st.markdown(f"⚡ {part['content']}")
                        elif part["type"] == "response":
                            st.markdown(part["content"])
                except (json.JSONDecodeError, KeyError):
                    st.markdown(content)
        elif role == 'tool':
            with st.expander(f"🔧 {msg.get('tool_name', 'Tool Call')}"):
                st.json(msg.get('tool_result', {}))

    if st.session_state.get('show_uploader', False):
        with st.expander("📤 Upload Document", expanded=True):

            # Inject CSS to make uploader label white
            st.markdown(
                """
                <style>
                    /* Make file uploader label white */
                    div[data-testid="stFileUploader"] label {
                        color: white !important;
                    }
                </style>
                """,
                unsafe_allow_html=True
            )

            uploader_key = st.session_state.get('uploader_key', 0)

            uploaded_file = st.file_uploader(
                "Choose a file (PDF, DOCX, XLSX, etc.)",
                type=['pdf', 'docx', 'xlsx', 'txt', 'pptx'],
                key=f"file_uploader_{uploader_key}"
            )


            if uploaded_file:
                st.session_state.pending_file = uploaded_file
                st.session_state.uploading_in_progress = True  # NEW: Gate chat during processing

                max_retries = 3
                extraction_result = None
                for attempt in range(max_retries):
                    with st.spinner(f"📄 Processing {uploaded_file.name}... (Attempt {attempt + 1}/{max_retries})"):
                        file_path = os.path.join("/tmp", uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        extraction_result = extract_document_text(file_path)
                        if extraction_result['status'] == 'success':
                            break
                        else:
                            if attempt < max_retries - 1:
                                import time
                                time.sleep(2)  # Brief pause before retry
                            else:
                                # All retries failed
                                pass

                # Clear selection after process (success or error) by incrementing key
                st.session_state.uploader_key = uploader_key + 1
                st.session_state.uploading_in_progress = False  # NEW: Unlock chat

                if extraction_result and extraction_result['status'] == 'success':
                    st.session_state.pending_extraction = {
                        'filename': extraction_result['filename'],
                        'text': extraction_result['text'],
                        'file_uri': extraction_result.get('file_uri')
                    }
                    st.success(f"✅ Document processed: {extraction_result['filename']}")
                    st.info("💬 Add your instructions below and send")
                else:
                    error_msg = extraction_result.get('error', 'Unknown error') if extraction_result else 'Unknown error'
                    st.error(f"⚠️ Extraction failed after {max_retries} attempts: {error_msg}")
                    if 'pending_file' in st.session_state:
                        del st.session_state.pending_file
                        
    st.markdown("---")

    current_show_uploader = st.session_state.get('show_uploader', False)
    if st.button("📎 Upload Document", help="Upload RFP or documents", key="upload_btn", use_container_width=True):
        st.session_state.show_uploader = not current_show_uploader
        st.rerun()

    user_input = st.chat_input("Type your message here...", key="chat_input")

    if user_input:
        # Prevent accidental empty submits
        if not user_input.strip():
            st.rerun()  # Just rerun without processing
        
        with st.spinner("🤔 Agent is thinking..."):
            if st.session_state.get('pending_extraction'):
                extraction = st.session_state.pending_extraction
                st.session_state.show_uploader = False

                # Full merged for agent (private, not shown in chat)
                merged_message = f"""📎 Document: {extraction['filename']}

DOCUMENT CONTENT:
{extraction['text']}

---
USER REQUEST:
{user_input}
"""
                
                # Just the raw user input for chat history display
                display_message = user_input
                
                # Send full to agent with display version for history
                send_message(session, merged_message, display_message)

                if extraction.get('file_uri'):
                    cleanup_gemini_file(extraction['file_uri'])

                del st.session_state.pending_extraction
                if 'pending_file' in st.session_state:
                    del st.session_state.pending_file
            else:
                send_message(session, user_input)
        st.rerun()