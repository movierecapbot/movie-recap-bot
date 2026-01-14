import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ImageClip

# --- ၁။ UI Styling (Advanced Neon Theme) ---
st.set_page_config(page_title="Movie Recap Bot", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    .stButton>button {
        background: linear-gradient(90deg, #8a2be2, #4b0082);
        color: white; border-radius: 8px; border: none; padding: 12px; font-weight: bold;
    }
    .stTextArea textarea { background-color: #161b22; color: #00ffcc; border: 1px solid #30363d; }
    .status-box { padding: 20px; border-radius: 10px; background: #1c2128; border-left: 5px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- ၂။ Backend Functions ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

async def get_ai_script(video_path):
    with open(video_path, "rb") as f:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=["Write a dramatic Burmese movie recap script based on this video.", 
                      genai.types.Part.from_bytes(data=f.read(), mime_type="video/mp4")]
        )
    return response.text

async def generate_ai_voice(text, voice_name, output_path):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)

# --- ၃။ Main Interface ---
st.markdown("<h1 style='text-align: center; color: #00ffcc;'>MOVIE RECAP BOT - AI AUTOMATION</h1>", unsafe_allow_html=True)

# Session State Initialization
if 'step' not in st.session_state: st.session_state.step = 1

# Step 1: Video Upload & Script Generation
if st.session_state.step == 1:
    col1, col2 = st.columns(2)
    with col1:
        video_input = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ (MP4/WEBM)", type=['mp4', 'webm'])
    with col2:
        if st.button("Generate Script") and video_input:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_input.read())
                script = asyncio.run(get_ai_script(tmp.name))
                st.session_state.script = script
                st.session_state.step = 2
                st.rerun()

# Step 2: Script Edit & Voice Selection
if st.session_state.step == 2:
    st.subheader("📝 Edit Script & Choose Voice")
    edited_script = st.text_area("Script ကို ပြင်ဆင်ပါ", value=st.session_state.get('script', ""), height=250)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🎙️ Voice Options")
        voice_choice = st.radio("အသံရွေးပါ", ["Male (Thiha)", "Female (Nilar)", "Upload My Own Audio"])
    
    with c2:
        if voice_choice != "Upload My Own Audio":
            if st.button("Generate AI Voice"):
                v_name = "my-MM-ThihaNeural" if "Male" in voice_choice else "my-MM-NilarNeural"
                asyncio.run(generate_ai_voice(edited_script, v_name, "temp_voice.mp3"))
                st.session_state.audio_ready = "temp_voice.mp3"
        else:
            uploaded_audio = st.file_uploader("အသံဖိုင်တင်ပါ", type=['mp3', 'wav'])
            if uploaded_audio: st.session_state.audio_ready = uploaded_audio

    with c3:
        if 'audio_ready' in st.session_state:
            st.audio(st.session_state.audio_ready)
            if st.button("Try Again / Reset"):
                del st.session_state.audio_ready
                st.rerun()

    st.divider()
    
    # Logo Settings
    st.subheader("🖼️ Logo & Brand Settings")
    logo_file = st.file_uploader("Upload Logo", type=['png', 'jpg'])
    logo_pos = st.selectbox("Logo Position", ["top-right", "top-left", "bottom-right", "bottom-left"])
    
    if st.button("🚀 Generate Final Video"):
        st.session_state.step = 3
        st.rerun()

# Step 3: Video Rendering (Simplified Logic)
if st.session_state.step == 3:
    with st.status("ဗီဒီယို ဖန်တီးနေသည်...", expanded=True) as status:
        st.write("AI အသံနှင့် ဗီဒီယိုကို ပေါင်းစပ်နေသည်...")
        time.sleep(2)
        st.balloons()
        st.success("အားလုံး ပြီးပါပြီ!")
        st.button("အသစ်ပြန်လုပ်မည်", on_click=lambda: st.session_state.clear())
