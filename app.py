import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import concatenate_audioclips
import moviepy.video.fx.all as vfx

# --- UI Styling (Neon Dark Theme) ---
st.set_page_config(page_title="Movie Recap AI Bot", layout="wide")
st.markdown("<h1 style='text-align: center;'>🎬 MOVIE RECAP BOT - AI AUTOMATION</h1>", unsafe_allow_html=True)
st.divider()

# --- Backend Functions ---
async def get_detailed_script(video_path):
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_API_KEY)
    with open(video_path, "rb") as f:
        # နံပါတ် (၂) စတိုင်လ်အတိုင်း အသေးစိတ်ရေးရန် ညွှန်ကြားချက်
        prompt = "Analyze this video and write a detailed, dramatic Burmese movie recap script (Storyteller style). Include actions and emotions. Output ONLY the narration text."
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[prompt, genai.types.Part.from_bytes(data=f.read(), mime_type="video/mp4")]
        )
    return response.text

async def generate_long_voice(text, voice_name, output_path):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)

# --- Main Interface Flow (၁ -> ၂ -> ၃ -> ၄) ---

# အဆင့် (၁): Media Upload
st.subheader("📂 1. Media Upload")
video_input = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ (MP4 or WEBM)", type=['mp4', 'webm'])

st.divider()

# အဆင့် (၂): AI Script Output
st.subheader("🤖 2. AI Script Output")
if st.button("Generate Detailed Script Now"):
    if video_input:
        with st.spinner("အသေးစိတ် ဇာတ်ညွှန်းရေးသားနေသည်..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_input.read())
                st.session_state.v_path = tmp.name
                st.session_state.script = asyncio.run(get_detailed_script(tmp.name))
    else: st.error("ဗီဒီယို အရင်တင်ပေးပါ။")

final_script = st.text_area("Edit your script here (နံပါတ် ၂ စတိုင်လ်):", value=st.session_state.get('script', ""), height=250)

st.divider()

# အဆင့် (၃): Voice Settings
st.subheader("🎙️ 3. Voice Settings")
col_v1, col_v2 = st.columns(2)
with col_v1:
    voice_choice = st.radio("အသံရွေးပါ", ["Male (Thiha)", "Female (Nilar)"])
    selected_voice = "my-MM-ThihaNeural" if "Male" in voice_choice else "my-MM-NilarNeural"
    if st.button("Generate/Preview AI Voice"):
        if final_script:
            with st.spinner("AI အသံသွင်းနေသည်..."):
                a_out = "final_audio.mp3"
                asyncio.run(generate_long_voice(final_script, selected_voice, a_out))
                st.session_state.a_path = a_out
                st.audio(a_out)
        else: st.warning("Script အရင်ထုတ်ပေးပါ။")
with col_v2:
    audio_upload = st.file_uploader("ကိုယ်ပိုင်အသံတင်ရန် (Optional)", type=['mp3', 'wav'])

st.divider()

# အဆင့် (၄): Logo & Branding
st.subheader("🖼️ 4. Logo & Branding")
col_l1, col_l2 = st.columns(2)
with col_l1:
    logo_input = st.file_uploader("Logo တင်ပါ", type=['png', 'jpg'])
with col_l2:
    logo_pos = st.selectbox("Logo Position", ["top-right", "top-left", "bottom-right", "bottom-left"])

st.divider()

# Final Processing
if st.button("🚀 5. Generate & Download Final Video"):
    # Render logic...
    st.info("ဗီဒီယိုကို အသံနှင့်ပေါင်းစပ်ပြီး အချောသတ်နေပါသည်။ ခဏစောင့်ပါ။")
