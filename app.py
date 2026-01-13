import streamlit as st
import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import time

# --- DEBUG & CONFIG ---
st.set_page_config(page_title="Auto Burmese Movie Recap AI", layout="wide")
st.title("🎬 Burmese Movie Recap AI")

# Library Version ကို စစ်ဆေးခြင်း (မျက်နှာပြင်မှာ ပြပါလိမ့်မယ်)
st.info(f"System Check: Google GenAI Version = {genai.__version__}")

if genai.__version__ < "0.8.3":
    st.error("⚠️ Library Version နိမ့်နေပါသည်။ App ကို Delete လုပ်ပြီး ပြန်တင်ရန် လိုအပ်ပါသည်။")
    st.stop()

# API Key Setup
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4"

# Force API Version to v1
os.environ["GOOGLE_GENERATIVE_AI_API_VERSION"] = "v1"
genai.configure(api_key=GEMINI_API_KEY)

# --- FUNCTIONS ---
def adjust_video_sync(video_path, audio_path, output_path):
    try:
        video_clip = VideoFileClip(video_path).without_audio()
        audio_clip = AudioFileClip(audio_path)
        speed_factor = video_clip.duration / audio_clip.duration
        final_video = video_clip.fx(vfx.speedx, speed_factor).set_audio(audio_clip)
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
        return output_path
    except Exception as e:
        st.error(f"Video Error: {e}")
        return None

async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

def analyze_and_recap(video_file_path):
    # အသစ်ဆုံး Model ကို သုံးပါမယ်
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.spinner("AI က ဗီဒီယိုကို ကြည့်ရှုနေသည် (ခေတ္တစောင့်ပါ)..."):
        video_file = genai.upload_file(path=video_file_path)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            raise ValueError("Video processing failed.")

    prompt = "Listen to the audio, translate to Burmese and write a dramatic movie recap script. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Output Burmese only."
    response = model.generate_content([video_file, prompt])
    return response.text

# --- UI ---
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm', 'mov'])

if uploaded_file:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
        tfile.write(uploaded_file.read())
        temp_path = tfile.name
    
    if st.button("Recap လုပ်မည်"):
        try:
            # 1. Script
            script = analyze_and_recap(temp_path)
            st.success("✅ ဇာတ်ညွှန်း ရရှိပါပြီ!")
            st.text_area("Script", script, height=150)
            
            # 2. Voice
            asyncio.run(generate_voice(script, "voice.mp3"))
            
            # 3. Video (Simple Merge)
            with st.spinner("ဗီဒီယို ပြုလုပ်နေသည်..."):
                final_path = "final_recap.mp4"
                adjust_video_sync(temp_path, "voice.mp3", final_path)
                
            st.video(final_path)
            
        except Exception as e:
            st.error(f"Error: {e}")
