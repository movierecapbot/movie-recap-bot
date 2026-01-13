import streamlit as st
import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4"
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Auto Burmese Movie Recap AI", layout="wide")

# --- FUNCTIONS ---

def adjust_video_sync(video_path, audio_path, output_path):
    """ဗီဒီယိုကို အသံနဲ့ ကိုက်အောင် ညှိခြင်း"""
    video_clip = VideoFileClip(video_path).without_audio()
    audio_clip = AudioFileClip(audio_path)
    speed_factor = video_clip.duration / audio_clip.duration
    final_video = video_clip.fx(vfx.speedx, speed_factor).set_audio(audio_clip)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
    return output_path

def apply_blur_to_video(video_path, output_path):
    """Logo နဲ့ Subtitle Blur လုပ်ခြင်း"""
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        # Top Right Logo Blur
        logo = frame[10:110, width-210:width-10]
        if logo.size > 0: frame[10:110, width-210:width-10] = cv2.GaussianBlur(logo, (51, 51), 0)
        # Bottom Subtitle Blur
        sub = frame[height-140:height-10, 50:width-50]
        if sub.size > 0: frame[height-140:height-10, 50:width-50] = cv2.GaussianBlur(sub, (51, 51), 0)
        out.write(frame)
    cap.release(); out.release()
    return output_path

async def generate_voice(text, output_path):
    """ဗမာအသံ ထုတ်ပေးခြင်း"""
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

def analyze_and_recap(video_file_path):
    """ဗီဒီယိုကို နားထောင်ပြီး ဗမာလို ဇာတ်ညွှန်းရေးခြင်း"""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    # ဗီဒီယိုဖိုင်ကို Gemini ဆီ တင်ပို့ခြင်း
    video_upload = genai.upload_file(path=video_file_path)
    
    prompt = "Listen to the audio and watch this video. Translate it and rewrite into a dramatic movie recap narration in Burmese language. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Do not use English."
    response = model.generate_content([prompt, video_upload])
    return response.text

# --- UI ---
st.title("🎬 Auto Movie Recap AI (Burmese)")
st.info("ဗီဒီယိုတင်လိုက်ရုံနဲ့ AI က ဘာသာပြန်ပြီး ဇာတ်ညွှန်းရေးပေးပါလိမ့်မယ်။")

uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm', 'mov', 'avi'])

if uploaded_file:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    
    if st.button("အလိုအလျောက် Recap လုပ်ပါ"):
        with st.status("AI အလုပ်လုပ်နေသည်...", expanded=True) as status:
            # 1. AI Video Analysis & Script
            st.write("🕵️ ဗီဒီယိုကို နားထောင်ပြီး ဇာတ်ညွှန်းရေးနေသည် (ဒါက ခဏကြာနိုင်ပါတယ်)...")
            script = analyze_and_recap(tfile.name)
            st.success("ဇာတ်ညွှန်း ရရှိပါပြီ!")
            st.write(f"📝 **AI Script:** {script[:100]}...")
            
            # 2. Voice Generation
            st.write("🎙️ ဗမာအသံသွင်းနေသည်...")
            asyncio.run(generate_voice(script, "voice.mp3"))
            
            # 3. Processing Video
            st.write("🌫️ Blur ပြုလုပ်ပြီး Final ဗီဒီယို ထုတ်နေသည်...")
            blurred = apply_blur_to_video(tfile.name, "blurred.mp4")
            final = adjust_video_sync(blurred, "voice.mp3", "final.mp4")
            
            status.update(label="✅ အားလုံး ပြီးပါပြီ!", state="complete")
            
        st.video(final)
        with open(final, "rb") as f:
            st.download_button("📥 Download Video", f, "recap_burmese.mp4")

