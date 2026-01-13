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

# --- CONFIGURATION ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4")
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Auto Burmese Movie Recap AI", layout="wide")

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
        st.error(f"Video Processing Error: {e}")
        return None

def apply_blur_to_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        out.write(frame)
    cap.release(); out.release()
    return output_path

async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

def analyze_and_recap(video_file_path):
    # Model နာမည်ကို နည်းနည်းပြောင်းပြီး စမ်းကြည့်ပါမည်
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Flash နောက်ဆုံးထွက်
    except:
        model = genai.GenerativeModel('gemini-1.5-pro') # Flash မရရင် Pro ကိုသုံးမယ်
    
    with st.spinner("AI က ဗီဒီယိုကို ဖတ်ရှုနေသည် (မိနစ်အနည်းငယ် ကြာနိုင်ပါသည်)..."):
        video_file = genai.upload_file(path=video_file_path)
        
        # Processing state ကို စောင့်ခြင်း
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            raise ValueError("Video processing failed.")

    prompt = "Listen to the audio, translate to Burmese and write a dramatic movie recap script. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Burmese only."
    
    # API Version Error တက်ရင် နောက်တစ်မျိုး ပြောင်းစမ်းမယ့် logic
    try:
        response = model.generate_content([video_file, prompt])
    except Exception as e:
        st.warning(f"Flash model error: {e}. Switching to Pro model...")
        model_pro = genai.GenerativeModel('gemini-1.5-pro')
        response = model_pro.generate_content([video_file, prompt])

    return response.text

# --- UI ---
st.title("🎬 Burmese Movie Recap AI")
st.caption("Using Gemini 1.5 Flash/Pro")

uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm', 'mov', 'avi'])

if uploaded_file:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
        tfile.write(uploaded_file.read())
        temp_path = tfile.name
    
    if st.button("Recap လုပ်မည်"):
        try:
            # 1. Script
            script = analyze_and_recap(temp_path)
            st.success("ဇာတ်ညွှန်းရရှိပါပြီ!")
            st.write(script)
            
            # 2. Voice
            asyncio.run(generate_voice(script, "voice.mp3"))
            
            # 3. Video
            with st.spinner("ဗီဒီယိုကို ပေါင်းစပ်နေသည်..."):
                final_path = "final_recap.mp4"
                # ရိုးရှင်းအောင် Blur မလုပ်ဘဲ တိုက်ရိုက်ပေါင်းစပ်ကြည့်မည် (Error လျော့နည်းအောင်)
                adjust_video_sync(temp_path, "voice.mp3", final_path)
                
            st.video(final_path)
            
        except Exception as e:
            st.error(f"Error ဖြစ်ပွားပါသည်: {e}")
            if os.path.exists(temp_path): os.remove(temp_path)
