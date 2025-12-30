import streamlit as st
import requests
import io
import time

st.set_page_config(page_title="Chatterbox Turbo", page_icon="🎙️", layout="wide")

API_URL = "http://localhost:8000"

st.title("🎙️ Chatterbox Turbo TTS")
st.markdown("Upload a voice sample, then generate speech!")

with st.sidebar:
    st.header("Settings")
    st.markdown("---")

    st.subheader("1. Load Voice")
    voice_input = st.radio(
        "Voice Input Method", ["Upload File", "Local Path"], horizontal=True
    )

    if voice_input == "Upload File":
        uploaded_voice = st.file_uploader(
            "Upload voice sample (WAV/MP3, 5-10s)", type=["wav", "mp3", "flac"]
        )
        exaggeration = st.slider("Exaggeration", 0.25, 2.0, 0.5, 0.1)

        if st.button("Load Voice") and uploaded_voice:
            try:
                files = {
                    "voice_file": (
                        uploaded_voice.name,
                        uploaded_voice,
                        uploaded_voice.type,
                    )
                }
                data = {"exaggeration": exaggeration}
                response = requests.post(
                    f"{API_URL}/load_voice_upload", files=files, data=data
                )

                if response.status_code == 200:
                    st.success("Voice loaded successfully!")
                    st.session_state.voice_loaded = True
                else:
                    st.error(f"Failed to load voice: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        voice_path = st.text_input("Path to voice file", value="reference.wav")
        exaggeration = st.slider("Exaggeration", 0.25, 2.0, 0.5, 0.1)

        if st.button("Load Voice"):
            try:
                response = requests.post(
                    f"{API_URL}/load_voice",
                    json={"voice_path": voice_path, "exaggeration": exaggeration},
                )

                if response.status_code == 200:
                    st.success("Voice loaded successfully!")
                    st.session_state.voice_loaded = True
                else:
                    st.error(f"Failed to load voice: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("---")

    st.subheader("API Status")
    try:
        health = requests.get(f"{API_URL}/health").json()
        st.write(f"Status: {health.get('status')}")
        st.write(f"Device: {health.get('device')}")
        st.write(f"Voice Loaded: {health.get('current_voice')}")
    except:
        st.error("API not reachable. Make sure backend is running.")

st.markdown("---")

st.header("2. Generate Speech")
text_input = st.text_area(
    "Enter text to synthesize",
    value="Hello! This is Chatterbox Turbo speaking.",
    height=100,
)

st.markdown("### Supported Tags")
with st.expander("View available tags"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Actions:**")
        for tag in [
            "[chuckle]",
            "[clear throat]",
            "[cough]",
            "[gasp]",
            "[laugh]",
            "[shush]",
            "[sigh]",
            "[sniff]",
        ]:
            st.markdown(f"- {tag}")
    with col2:
        st.markdown("**Emotions:**")
        for tag in [
            "[angry]",
            "[crying]",
            "[dramatic]",
            "[fear]",
            "[happy]",
            "[narration]",
            "[sarcastic]",
            "[surprised]",
            "[whispering]",
        ]:
            st.markdown(f"- {tag}")
    with col3:
        st.markdown("**Example:**")
        st.code("[laugh] I can't believe it! [sigh] So relieved.", language="text")

if st.button("🎵 Generate Speech", type="primary", use_container_width=True):
    if not st.session_state.get("voice_loaded", False):
        st.error("Please load a voice first!")
    elif not text_input.strip():
        st.error("Please enter some text!")
    else:
        with st.spinner("Generating speech..."):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{API_URL}/generate", json={"text": text_input}, stream=True
                )

                if response.status_code == 200:
                    gen_time = float(response.headers.get("X-Generation-Time", 0))

                    st.success(f"Generated in {gen_time:.2f}s!")

                    audio_bytes = response.content
                    st.audio(audio_bytes, format="audio/wav")

                    st.download_button(
                        "📥 Download Audio",
                        audio_bytes,
                        "chatterbox_output.wav",
                        "audio/wav",
                    )
                else:
                    st.error(f"Generation failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown("### Tips")
st.markdown("- Use 5-10 seconds of clear speech for best voice cloning")
st.markdown("- Lower exaggeration (0.3-0.5) for professional tone")
st.markdown("- Higher exaggeration (0.7-1.0+) for more expressive speech")
st.markdown("- Tags can be used anywhere in the text for emotions and sounds")
