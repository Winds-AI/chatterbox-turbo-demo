import streamlit as st
import requests
import io
import time
import os

st.set_page_config(page_title="Chatterbox Turbo TTS", page_icon="🎙️", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .voice-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: #4CAF50;
        color: white;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
    .no-voice-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: #FF5722;
        color: white;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
    .tips-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .stButton button {
        width: 100%;
    }
    .audio-player {
        margin: 1rem 0;
    }
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .status-healthy { background: #4CAF50; }
    .status-error { background: #F44336; }
    .status-starting { background: #FF9800; }
</style>
""",
    unsafe_allow_html=True,
)

if "voice_loaded" not in st.session_state:
    st.session_state.voice_loaded = False
if "generated_count" not in st.session_state:
    st.session_state.generated_count = 0
if "audio_history" not in st.session_state:
    st.session_state.audio_history = []


def check_api_status():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except:
        return None


def load_voice(voice_path, exaggeration):
    response = requests.post(
        f"{API_URL}/load_voice",
        json={"voice_path": voice_path, "exaggeration": exaggeration},
    )
    return response


def load_voice_upload(voice_file, exaggeration):
    files = {"voice_file": (voice_file.name, voice_file, voice_file.type)}
    data = {"exaggeration": exaggeration}
    response = requests.post(f"{API_URL}/load_voice_upload", files=files, data=data)
    return response


def generate_speech(text):
    response = requests.post(f"{API_URL}/generate", json={"text": text}, stream=True)
    return response


def get_status_indicator(status):
    status_map = {
        "healthy": ("status-healthy", "Ready"),
        "initializing": ("status-starting", "Initializing..."),
        "starting": ("status-starting", "Starting..."),
        "error": ("status-error", "Error"),
    }
    css_class, text = status_map.get(status, ("status-error", status))
    return f'<span class="status-dot {css_class}"></span> {text}'


st.markdown('<div class="main-header">', unsafe_allow_html=True)
col_header1, col_header2, col_header3 = st.columns([1, 2, 1])
with col_header2:
    st.title("🎙️ Chatterbox Turbo")
    st.caption("AI Text-to-Speech with Voice Cloning")
st.markdown("</div>", unsafe_allow_html=True)

health = check_api_status()

with st.sidebar:
    st.header("⚙️ Settings")

    st.markdown("---")
    st.subheader("🔊 Voice Settings")

    voice_source = st.radio(
        "Voice Source",
        ["Upload File", "Use Sample"],
        horizontal=True,
        help="Upload your own voice or use the sample voice",
    )

    exaggeration = st.slider(
        "🎭 Exaggeration",
        min_value=0.25,
        max_value=2.0,
        value=0.5,
        step=0.1,
        help="Higher = more expressive, Lower = more natural",
    )

    st.markdown("---")
    st.subheader("📊 API Status")

    if health:
        status_html = get_status_indicator(health.get("status"))
        st.markdown(
            f"""
        <div class="status-indicator">
            {status_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

        device = health.get("device", "N/A")
        st.info(f"**Device:** {device}")

        current_voice = health.get("current_voice")
        if current_voice:
            voice_name = os.path.basename(current_voice)
            st.success(f"**Loaded Voice:** {voice_name}")
        else:
            st.warning("**No voice loaded**")
    else:
        st.error("⚠️ API Unreachable")
        st.caption(
            "Make sure the backend is running: `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`"
        )

    st.markdown("---")
    st.subheader("📖 Quick Help")
    with st.expander("How to use"):
        st.markdown("""
        1. **Load a voice** - Upload a WAV/MP3 file (5-10s of clear speech)
        2. **Enter text** - Type or paste your text
        3. **Generate** - Click the generate button
        4. **Download** - Save your audio file
        """)

    with st.expander("🎭 Emotion Tags"):
        st.markdown("""
        **Actions:** `[chuckle]`, `[laugh]`, `[sigh]`, `[cough]`, `[gasp]`
        
        **Emotions:** `[angry]`, `[happy]`, `[sad]`, `[whispering]`, `[dramatic]`
        
        **Example:** `[laugh] That's amazing! [sigh] I can't believe it.`
        """)

    with st.expander("💡 Tips"):
        st.markdown("""
        - Use 5-10 seconds of **clear speech** for best results
        - **No background noise** improves quality
        - **Consistent tone** helps voice cloning
        - Lower exaggeration (0.3-0.5) for **professional tone**
        - Higher exaggeration (0.7-1.0+) for **expressive speech**
        """)

col_main1, col_main2 = st.columns([2, 1])

with col_main1:
    st.subheader("🎤 Load Your Voice")

    if voice_source == "Upload File":
        uploaded_voice = st.file_uploader(
            "Upload voice sample (WAV, MP3, FLAC)",
            type=["wav", "mp3", "flac"],
            help="5-10 seconds of clear speech works best",
        )

        if uploaded_voice:
            st.audio(
                uploaded_voice, format=f"audio/{uploaded_voice.type.split('/')[-1]}"
            )

            col_load1, col_load2 = st.columns(2)
            with col_load1:
                load_btn = st.button(
                    "✅ Load Voice", type="primary", use_container_width=True
                )
            with col_load2:
                st.caption(f"File: {uploaded_voice.name}")

            if load_btn:
                with st.spinner("Loading voice..."):
                    try:
                        response = load_voice_upload(uploaded_voice, exaggeration)
                        if response.status_code == 200:
                            st.session_state.voice_loaded = True
                            st.success("✅ Voice loaded successfully!")
                        else:
                            st.error(
                                f"❌ Failed: {response.json().get('detail', 'Unknown error')}"
                            )
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    else:
        voice_files = (
            [f for f in os.listdir("audio") if f.endswith((".wav", ".mp3", ".flac"))]
            if os.path.exists("audio")
            else []
        )
        if voice_files:
            selected_voice = st.selectbox("Select voice sample", voice_files)
            col_load1, col_load2 = st.columns(2)
            with col_load1:
                load_btn = st.button(
                    "✅ Load Voice", type="primary", use_container_width=True
                )
            with col_load2:
                st.caption(f"Selected: {selected_voice}")

            if load_btn:
                with st.spinner("Loading voice..."):
                    try:
                        response = load_voice(f"audio/{selected_voice}", exaggeration)
                        if response.status_code == 200:
                            st.session_state.voice_loaded = True
                            st.success("✅ Voice loaded successfully!")
                        else:
                            st.error(
                                f"❌ Failed: {response.json().get('detail', 'Unknown error')}"
                            )
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("📁 No voice files found in 'audio/' folder")
            st.info("💡 Add WAV/MP3 files to the 'audio/' folder to use this option")

with col_main2:
    st.subheader("📋 Current Status")

    if st.session_state.voice_loaded:
        st.markdown(
            '<span class="voice-badge">🎤 Voice Loaded</span>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span class="no-voice-badge">⚠️ No Voice</span>', unsafe_allow_html=True
        )

    st.markdown("---")

    st.metric("Generations", st.session_state.generated_count)

    if st.session_state.audio_history:
        st.markdown("### 📜 Recent Audio")
        for i, (text, timestamp) in enumerate(st.session_state.audio_history[-3:]):
            st.caption(f"{text[:30]}... ({timestamp})")

st.markdown("---")

st.subheader("📝 Generate Speech")

col_text1, col_text2 = st.columns([3, 1])
with col_text1:
    text_input = st.text_area(
        "Enter your text",
        value="Hello! This is Chatterbox Turbo speaking. I can clone any voice with just a few seconds of audio.",
        height=120,
        placeholder="Type something here...",
    )
    char_count = len(text_input)
    st.caption(f"Characters: {char_count}")
with col_text2:
    st.markdown("### ⚡ Quick Templates")
    if st.button("👋 Greeting", use_container_width=True):
        st.session_state.quick_text = "Hello! How are you doing today?"
    if st.button("🎉 Celebration", use_container_width=True):
        st.session_state.quick_text = "[laugh] This is amazing! I can't believe it!"
    if st.button("📢 Announcement", use_container_width=True):
        st.session_state.quick_text = (
            "Attention everyone! We have an important announcement to make."
        )
    if st.button("📞 Phone", use_container_width=True):
        st.session_state.quick_text = (
            "Hello, this is [name] calling. Could you please give me a call back?"
        )

if "quick_text" in st.session_state:
    text_input = st.session_state.quick_text
    del st.session_state.quick_text
    st.rerun()

st.markdown("### 🎭 Add Emotions (Optional)")
st.caption("Insert these tags anywhere in your text for expressive speech:")
col_tag1, col_tag2, col_tag3, col_tag4 = st.columns(4)
with col_tag1:
    if st.button("[laugh]", use_container_width=True):
        st.session_state.tag_text = "[laugh] " + text_input
with col_tag2:
    if st.button("[sigh]", use_container_width=True):
        st.session_state.tag_text = text_input + " [sigh]"
with col_tag3:
    if st.button("[chuckle]", use_container_width=True):
        st.session_state.tag_text = "[chuckle] " + text_input
with col_tag4:
    if st.button("[dramatic]", use_container_width=True):
        st.session_state.tag_text = "[dramatic] " + text_input

if "tag_text" in st.session_state:
    text_input = st.session_state.tag_text
    del st.session_state.tag_text
    st.rerun()

col_gen1, col_gen2 = st.columns([3, 1])
with col_gen1:
    generate_btn = st.button(
        "🎵 Generate Speech", type="primary", use_container_width=True
    )
with col_gen2:
    st.caption("⬆️ Upload voice first")

if generate_btn:
    if not st.session_state.voice_loaded:
        st.error("⚠️ Please load a voice first!")
    elif not text_input.strip():
        st.error("⚠️ Please enter some text!")
    else:
        with st.spinner("🎨 Generating speech... This may take a few seconds..."):
            try:
                start_time = time.time()
                response = generate_speech(text_input)

                if response.status_code == 200:
                    gen_time = float(response.headers.get("X-Generation-Time", 0))
                    audio_bytes = response.content

                    st.session_state.generated_count += 1
                    timestamp = time.strftime("%H:%M")
                    st.session_state.audio_history.append((text_input[:40], timestamp))

                    st.success(f"✅ Generated in {gen_time:.2f}s!")

                    st.markdown("### 🔊 Your Audio")
                    st.audio(audio_bytes, format="audio/wav")

                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "📥 Download Audio",
                            audio_bytes,
                            "chatterbox_output.wav",
                            "audio/wav",
                            type="primary",
                            use_container_width=True,
                        )
                    with col_dl2:
                        st.caption("Right-click → Save link as...")
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"❌ Generation failed: {error_detail}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

st.markdown("---")
st.caption(
    "🎙️ Chatterbox Turbo - Open Source Text-to-Speech | [GitHub](https://github.com/resemble-ai/chatterbox)"
)
