import streamlit as st
from agent.agent import root_agent
from agent.file_processor import extract_document_text, cleanup_gemini_file, extract_document_metadata, detect_document_type
from agent.database.db_manager import DatabaseManager
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
import os
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Import caching components
from agent.database.session_cache import SessionCache
from agent.database.background_sync import create_background_sync
from agent.database.db_singleton import get_db
import agent.database.cached_database_tools as cached_db_tools

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

@st.cache_resource
def get_cache_and_sync():
    """
    Create singleton cache and background sync thread.
    Returns (SessionCache, BackgroundSyncThread)
    """
    print("🚀 Initializing performance cache and background sync...")

    # Create cache instance
    cache = SessionCache(default_ttl_seconds=300)  # 5 min TTL for RFP data

    # Initialize cached database tools
    cached_db_tools.set_global_cache(cache)

    # Create and start background sync thread
    db_manager = get_db()
    sync_thread = create_background_sync(
        cache=cache,
        db_manager=db_manager,
        flush_interval_seconds=2.0  # Flush every 2 seconds
    )

    print("✅ Cache and background sync initialized!")
    return cache, sync_thread

session_service = get_session_service()
cache, sync_thread = get_cache_and_sync()

# Initialize SessionContext with cache
from agent.session_wrapper import SessionContext
SessionContext.set_cache(cache)

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
    """
    Ensure ADK session exists in the ADK database.

    CRITICAL: ADK Runner requires session to exist in its own tables.
    This explicitly creates the session if it doesn't exist.
    """
    # ALWAYS check the ADK database, don't trust the in-memory cache
    # The _synced_sessions set can be stale after Streamlit restarts
    try:
        import asyncio

        # Check if session exists in ADK database
        print(f"🔍 Checking ADK session: user={user_id}, session={session_id}", flush=True)

        # Run async function synchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        existing_session = loop.run_until_complete(
            session_service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
        )

        if existing_session is None:
            # Session not found - create it
            print(f"🆕 Creating ADK session for user={user_id}, session={session_id}", flush=True)
            loop.run_until_complete(
                session_service.create_session(
                    app_name=APP_NAME,
                    user_id=user_id,
                    session_id=session_id
                )
            )
            print(f"✅ ADK session created successfully", flush=True)
        else:
            print(f"✅ ADK session already exists", flush=True)

        _synced_sessions.add(session_id)
        return True
    except Exception as e:
        print(f"❌ CRITICAL ERROR syncing ADK session: {e}", flush=True)
        import traceback
        traceback.print_exc()
        # Don't add to _synced_sessions if failed - will retry next time
        return False


def send_message(session, user_input: str, display_message: str = None):
    """Process user message and get agent response"""
    # Save display version to history (shortened if provided)
    display_msg = display_message if display_message is not None else user_input
    session.save_user_message(display_msg)

    try:
        user_id = str(session.session['user_id'])
        print(f"\n{'='*80}")
        print(f"📨 SENDING MESSAGE")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session.session_id}")
        print(f"Message: {user_input[:100]}...")
        print(f"{'='*80}\n")

        # CRITICAL: Ensure ADK session exists before sending message
        adk_sync_success = ensure_adk_session_sync(user_id, session.session_id)
        if not adk_sync_success:
            raise Exception("Failed to sync ADK session - cannot send message")

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )

        all_parts = []
        response_text = ""
        event_count = 0

        print(f"🔄 Starting runner.run() event loop...")
        for event in runner.run(
            user_id=user_id,
            session_id=session.session_id,
            new_message=content
        ):
            event_count += 1
            print(f"📍 Event #{event_count}: is_final={event.is_final_response()}, type={type(event).__name__}")

            if event.is_final_response():
                print(f"✅ FINAL RESPONSE RECEIVED")
                if event.content and hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text = part.text
                            print(f"📝 Response text: {response_text[:100]}...")
                            break
                break

            if event.content and hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"💭 Thinking: {part.text[:50]}...")
                        all_parts.append({"type": "thinking", "content": part.text.strip()})

                    if hasattr(part, 'function_call') and part.function_call:
                        func_name = part.function_call.name if hasattr(part.function_call, 'name') else 'function'
                        print(f"🔧 Tool call: {func_name}")
                        all_parts.append({"type": "tool_call", "content": func_name})

        print(f"🏁 Event loop finished. Total events: {event_count}")
        print(f"Response text length: {len(response_text)}")

        if all_parts:
            all_parts.append({"type": "response", "content": response_text})
            import json
            session.save_assistant_message(json.dumps(all_parts))
        else:
            session.save_assistant_message(response_text)

        # Generate TTS if last message was voice
        if st.session_state.get('last_message_was_voice', False) and response_text:
            try:
                from gtts import gTTS
                import tempfile
                import re

                # Clean markdown formatting from text for TTS
                clean_text = response_text

                # Remove markdown bold/italic (** or __)
                clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)
                clean_text = re.sub(r'__(.+?)__', r'\1', clean_text)
                clean_text = re.sub(r'\*(.+?)\*', r'\1', clean_text)
                clean_text = re.sub(r'_(.+?)_', r'\1', clean_text)

                # Remove markdown links [text](url)
                clean_text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean_text)

                # Remove code blocks and inline code
                clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)
                clean_text = re.sub(r'`(.+?)`', r'\1', clean_text)

                # Remove markdown headers (#)
                clean_text = re.sub(r'^#+\s+', '', clean_text, flags=re.MULTILINE)

                # Replace markdown lists (-, *, +) with nothing
                clean_text = re.sub(r'^\s*[-*+]\s+', '', clean_text, flags=re.MULTILINE)

                # Remove horizontal rules (---, ___)
                clean_text = re.sub(r'^[-_*]{3,}$', '', clean_text, flags=re.MULTILINE)

                # Clean up extra whitespace
                clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
                clean_text = clean_text.strip()

                print(f"🎤 TTS Clean Text: {clean_text[:100]}...")

                # Generate speech audio using Google TTS
                tts = gTTS(text=clean_text, lang='en', slow=False)

                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                    tts.save(tmp_audio.name)
                    # Store audio path in session state for playback
                    st.session_state.tts_audio_path = tmp_audio.name
                    print(f"✅ TTS audio generated: {tmp_audio.name}")

            except Exception as tts_error:
                print(f"⚠️ TTS Error: {tts_error}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole response if TTS fails

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

    # Auto-play TTS if available
    if 'tts_audio_path' in st.session_state:
        print(f"🔊 Playing TTS audio from: {st.session_state.tts_audio_path}")
        try:
            with open(st.session_state.tts_audio_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                print(f"🔊 Audio file size: {len(audio_bytes)} bytes")

                # Display audio player with autoplay
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)
                st.caption("🔊 Agent is speaking...")

            # Clean up
            import os as os_module
            os_module.unlink(st.session_state.tts_audio_path)
            del st.session_state.tts_audio_path
            print("✅ TTS audio played and cleaned up")

        except Exception as e:
            print(f"⚠️ Error playing TTS audio: {e}")
            import traceback
            traceback.print_exc()
            if 'tts_audio_path' in st.session_state:
                del st.session_state.tts_audio_path

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

    # CSS to make upload/voice more compact and equal height
    st.markdown("""
    <style>
    /* Make file uploader compact and same height as audio */
    [data-testid="stFileUploader"] {
        padding: 0 !important;
        margin-bottom: 5px !important;
    }
    [data-testid="stFileUploader"] > div {
        padding: 0 !important;
    }
    [data-testid="stFileUploader"] section {
        padding: 8px !important;
        min-height: 45px !important;
        max-height: 45px !important;
    }
    /* Hide all text in uploader */
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploader"] span {
        display: none !important;
    }
    /* Replace with simple text */
    [data-testid="stFileUploader"] section::before {
        content: "📎 Upload" !important;
        font-size: 14px !important;
        display: block !important;
        text-align: center !important;
        color: #1f77b4 !important;
    }
    /* Make audio input compact */
    [data-testid="stAudioInput"] {
        padding: 0 !important;
        margin-bottom: 5px !important;
    }
    [data-testid="stAudioInput"] > div {
        min-height: 45px !important;
        max-height: 45px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Upload and Voice side by side
    col_upload, col_voice = st.columns(2)

    with col_upload:
        uploader_key = st.session_state.get('uploader_key', 0)
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'docx', 'xlsx', 'txt', 'pptx'],
            key=f"file_uploader_{uploader_key}",
            label_visibility="collapsed"
        )

    with col_voice:
        audio_key = st.session_state.get('audio_key', 0)
        audio_file = st.audio_input("Record Audio", key=f"audio_input_{audio_key}", label_visibility="collapsed")

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
            # Detect document type and extract metadata
            with st.spinner("🔍 Analyzing document..."):
                db = DatabaseManager()

                # Get document type (from PDF extraction or detect from text)
                document_type = extraction_result.get('document_type')
                if not document_type:
                    document_type = detect_document_type(extraction_result['text'])

                # Optimized: No longer fetch all records for duplicate detection
                # The new database methods handle this directly
                # Extract metadata with duplicate checking
                metadata = extract_document_metadata(
                    extraction_result['text'],
                    document_type,
                    db=db  # Pass db instance for optimized lookups
                )

                title = metadata['title']
                matching_id = metadata['matching_id']
                entity_type = metadata['entity_type']
                has_qualification = metadata['has_qualification']
                has_bid_plan = metadata['has_bid_plan']

                print(f"🔍 Document type: {document_type}")
                print(f"🔍 Extracted title: {title}")
                print(f"🔄 Matching {entity_type} ID: {matching_id}")

                # Get status using the matched ID or by title
                status = {
                    'exists': False,
                    'matching_id': None,
                    'entity_type': entity_type,
                    'title': None,
                    'has_qualification': False,
                    'has_bid_plan': False
                }

                if matching_id and document_type == "RFP":
                    # Optimized: Single query with LEFT JOINs instead of 3 separate queries
                    rfp_data = db.get_rfp_upload_status(matching_id)

                    status = {
                        'exists': True,
                        'matching_id': matching_id,
                        'entity_type': 'rfp',
                        'title': rfp_data.get('project_title') if rfp_data else title,
                        'client_name': rfp_data.get('client_name') if rfp_data else None,
                        'has_qualification': rfp_data.get('has_qualification', False) if rfp_data else False,
                        'has_bid_plan': rfp_data.get('has_bid_plan', False) if rfp_data else False
                    }
                elif matching_id and document_type == "Meeting Notes":
                    brief_doc = db.get_client_brief(matching_id)
                    status = {
                        'exists': True,
                        'matching_id': matching_id,
                        'entity_type': 'brief',
                        'title': brief_doc.get('client_name') if brief_doc else title,
                        'has_qualification': False,
                        'has_bid_plan': False
                    }

                print(f"📊 Database status: {status}")

            st.session_state.pending_extraction = {
                'filename': extraction_result['filename'],
                'text': extraction_result['text'],
                'file_uri': extraction_result.get('file_uri'),
                'document_type': document_type,
                'title': title,
                'matching_id': status.get('matching_id'),
                'entity_type': entity_type,
                'has_qualification': status.get('has_qualification', False),
                'has_bid_plan': status.get('has_bid_plan', False)
            }

            print(f"💾 Pending extraction data: doc_type={document_type}, title={title}, matching_id={status.get('matching_id')}, entity_type={entity_type}")

            st.success(f"✅ Document processed: {extraction_result['filename']}")

            # Show status based on document type
            if status.get('exists'):
                if entity_type == 'rfp':
                    st.warning(f"⚠️ This RFP already exists: **{title}**")
                    status_parts = []
                    if status.get('has_qualification'):
                        status_parts.append("✓ Qualification")
                    if status.get('has_bid_plan'):
                        status_parts.append("✓ Bid Plan")
                    if status_parts:
                        st.info(f"Status: {', '.join(status_parts)}")
                elif entity_type == 'brief':
                    st.warning(f"⚠️ Client brief already exists for: **{title}**")

            st.info(f"📋 Document type: {document_type} | 💬 Add your instructions below and send")
        else:
            error_msg = extraction_result.get('error', 'Unknown error') if extraction_result else 'Unknown error'
            st.error(f"⚠️ Extraction failed after {max_retries} attempts: {error_msg}")
            if 'pending_file' in st.session_state:
                del st.session_state.pending_file
                        

    # Audio transcription (audio_file is from the column above)
    # Check if this is a NEW audio file (different from last processed)
    is_new_audio = (audio_file is not None and
                    st.session_state.get('last_transcribed_audio') != audio_file)

    if is_new_audio:
        with st.spinner("🎯 Transcribing audio..."):
            try:
                from vosk import Model, KaldiRecognizer
                import wave
                import json
                import tempfile
                import os as os_module
                import urllib.request
                import zipfile

                # Download and cache Vosk model
                @st.cache_resource
                def load_vosk_model():
                    model_path = "/tmp/vosk-model-small-en-us-0.15"

                    # Download model if not exists
                    if not os.path.exists(model_path):
                        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
                        zip_path = "/tmp/vosk-model.zip"

                        st.info("📥 Downloading speech recognition model (one-time, ~40MB)...")
                        urllib.request.urlretrieve(model_url, zip_path)

                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall("/tmp/")

                        os_module.unlink(zip_path)

                    return Model(model_path)

                model = load_vosk_model()

                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_file.getbuffer())
                    tmp_audio_path = tmp_file.name

                # Open WAV file and transcribe
                wf = wave.open(tmp_audio_path, "rb")

                # Check audio format
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                    st.warning("⚠️ Audio format should be mono, 16-bit. Attempting transcription anyway...")

                recognizer = KaldiRecognizer(model, wf.getframerate())
                recognizer.SetWords(True)

                # Transcribe
                full_text = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        if 'text' in result and result['text']:
                            full_text.append(result['text'])

                # Get final result
                final_result = json.loads(recognizer.FinalResult())
                if 'text' in final_result and final_result['text']:
                    full_text.append(final_result['text'])

                transcribed_text = " ".join(full_text).strip()

                # Clean up
                wf.close()
                os_module.unlink(tmp_audio_path)

                if not transcribed_text:
                    st.warning("⚠️ No speech detected. Please try speaking more clearly.")
                    # Mark this audio as processed to prevent re-processing
                    st.session_state.last_transcribed_audio = audio_file
                else:
                    # AUTO-SEND: Immediately queue transcribed text to be sent
                    st.success("✅ Transcribed successfully - sending to agent...")
                    st.session_state.voice_message_to_send = transcribed_text
                    # Mark as processed
                    st.session_state.last_transcribed_audio = audio_file
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Transcription failed: {str(e)}")
                st.info("💡 Make sure `vosk` is installed: `pip install vosk`")
                import traceback
                st.code(traceback.format_exc())

    # Check if we have a voice message to send (auto-sent after transcription)
    user_input = None
    if 'voice_message_to_send' in st.session_state:
        user_input = st.session_state.voice_message_to_send
        del st.session_state.voice_message_to_send
        # Mark that this was a voice message so we can enable TTS response
        st.session_state.last_message_was_voice = True
        # Note: We keep last_transcribed_audio so we don't re-process the same audio
    else:
        user_input = st.chat_input("Type your message here...", key="chat_input")
        # Regular text input, disable TTS
        st.session_state.last_message_was_voice = False

    if user_input:
        # Prevent accidental empty submits
        if not user_input.strip():
            st.rerun()  # Just rerun without processing

        # Clear audio widget if this was a voice message
        if st.session_state.get('last_message_was_voice', False):
            audio_key = st.session_state.get('audio_key', 0)
            st.session_state.audio_key = audio_key + 1
            # Clear the transcribed audio reference so new recordings can be processed
            if 'last_transcribed_audio' in st.session_state:
                del st.session_state.last_transcribed_audio

        with st.spinner("🤔 Agent is thinking..."):
            if st.session_state.get('pending_extraction'):
                extraction = st.session_state.pending_extraction
                st.session_state.show_uploader = False

                # Build metadata section based on document type
                document_type = extraction.get('document_type', 'Other')
                entity_type = extraction.get('entity_type', 'other')

                if document_type == "RFP" or entity_type == "rfp":
                    metadata = f"""[RFP_METADATA]
document_type: RFP
rfp_title: {extraction.get('title', 'Unknown')}
existing_rfp_id: {extraction.get('matching_id', 'null')}
has_qualification: {extraction.get('has_qualification', False)}
has_bid_plan: {extraction.get('has_bid_plan', False)}
[/RFP_METADATA]"""
                elif document_type == "Meeting Notes" or entity_type == "brief":
                    metadata = f"""[RFP_METADATA]
document_type: Meeting Notes
rfp_title: {extraction.get('title', 'Unknown')}
existing_rfp_id: {extraction.get('matching_id', 'null')}
has_qualification: false
has_bid_plan: false
[/RFP_METADATA]"""
                else:  # Other
                    metadata = f"""[RFP_METADATA]
document_type: Other
rfp_title: {extraction.get('title', 'Unknown')}
existing_rfp_id: null
has_qualification: false
has_bid_plan: false
[/RFP_METADATA]"""

                # Debug: Print metadata being sent
                print("\n" + "="*80)
                print("📋 METADATA BEING SENT TO AGENT:")
                print(metadata)
                print("="*80 + "\n")

                # Full merged for agent (private, not shown in chat)
                merged_message = f"""📎 Document: {extraction['filename']}

{metadata}

[FULL_DOCUMENT]
{extraction['text']}
[/FULL_DOCUMENT]

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