import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

# --- UI SETTINGS ---
st.set_page_config(page_title="Movie Recap AI", layout="wide")

# CSS for Neon Dark Mode
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { background: linear-gradient(45deg, #6a11cb 0%, #2575fc 100%); color: white; border-radius: 10px; border: none; padding: 10px; }
    .stTextArea textarea { background-color: #1a1c24; color: #00ffcc; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

async def generate_recap_script(video_path):
    """Gemini 3 ကိုသုံးပြီး ဗီဒီယိုကို တကယ်စစ်ဆေးပြီး Script ရေးသားခြင်း"""
    with open(video_path, "rb") as f:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                "Analyze this video and write a detailed, dramatic Burmese movie recap script. Use a storytelling tone. Start with 'ဇာတ်လမ်းစစချင်းမှာတော့...'. Burmese language only.",
                genai.types.Part.from_bytes(data=f.read(), mime_type="video/mp4")
            ]
        )
    return response.text

async def generate_ai_voice(text, voice_name, output_path):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)

# --- MAIN UI ---
st.markdown("<h1 style='text-align: center; color: #00ffcc;'>🎬 MOVIE RECAP BOT</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 1. Media Upload")
    video_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ (MP4 or WEBM)", type=['mp4', 'webm'])
    
    st.subheader("🎙️ 2. AI Voice Settings")
    voice_option = st.radio("အသံရွေးချယ်ပါ", ["Male (Thiha)", "Female (Nilar)"])
    selected_voice = "my-MM-ThihaNeural" if "Male" in voice_option else "my-MM-NilarNeural"

with col2:
    st.subheader("🤖 3. AI Script Output")
    
    # Script ထုတ်ပေးမည့် Button
    if st.button("Generate Script Now"):
        if video_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_file.read())
                temp_video_path = tmp.name
            
            with st.spinner("AI က ဗီဒီယိုကို လေ့လာပြီး ဇာတ်ညွှန်းရေးနေသည်... ခဏစောင့်ပါ"):
                try:
                    full_script = asyncio.run(generate_recap_script(temp_video_path))
                    st.session_state.script = full_script
                    st.success("ဇာတ်ညွှန်း ရရှိပါပြီ!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.error("ဗီဒီယို အရင်တင်ပေးပါ။")

    # ရလာတဲ့ Script ကို ဒီမှာပြမယ် (Edit လုပ်လို့ရတယ်)
    recap_script = st.text_area("Edit your script here:", value=st.session_state.get('script', ""), height=300)

# --- FINAL STEP ---
if st.button("Generate Final Video & Voice"):
    if recap_script:
        # Ad Loading Simulation
        progress_bar = st.progress(0)
        for percent in range(100):
            time.sleep(0.05)
            progress_bar.progress(percent + 1)
        
        audio_path = "final_voice.mp3"
        with st.spinner("AI အသံသွင်းနေသည်..."):
            asyncio.run(generate_ai_voice(recap_script, selected_voice, audio_path))
        
        st.subheader("🔊 Preview AI Voice")
        st.audio(audio_path)
        
        st.success("ဗီဒီယိုတည်းဖြတ်မှုအပိုင်းကို Render ဆွဲနေပါသည်။ (MoviePy လုပ်ဆောင်ချက်)")
    else:
        st.error("ဇာတ်ညွှန်း မရှိသေးပါ။ အပေါ်က Generate Script ကို အရင်နှိပ်ပါ။")
