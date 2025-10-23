"""
Simple microphone test for Streamlit
Run with: streamlit run test_microphone.py
"""
import streamlit as st

st.title("🎤 Microphone Test")
st.write("Access this app at: http://localhost:8501")

audio = st.audio_input("Click to record")

if audio:
    st.success("✅ Audio recorded!")
    st.audio(audio)
    st.write(f"Audio size: {len(audio.getbuffer())} bytes")
else:
    st.info("👆 Click the button above and allow microphone access when prompted")
