import streamlit as st
import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
from supabase import create_client
import google.generativeai as genai
import edge_tts
import asyncio
from datetime import datetime

# --- CONFIGURATION (သင့်အချက်အလက်များကို ထည့်သွင်းထားသည်) ---
SUPABASE_URL = "https://mflfazgkhpxgkejjmckq.supabase.co"
SUPABASE_KEY = "sb_publishable_GuLum9W9d3wyDL-s6BsN7w_I1fnHCUg"
GEMINI_API_KEY = "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Burmese Movie Recap AI", layout="wide")

# --- FUNCTIONS ---

def adjust_video_sync(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path).without_audio()
    audio_clip = AudioFileClip(audio_path)
    speed_factor = video_clip.duration / audio_clip.duration
    final_video = video_clip.fx(vfx.speedx, speed_factor).set_audio(audio_clip)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path

def apply_blur_to_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width, height = int(cap.get(3)), int(cap.get(4))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        logo_zone = frame[20:120, width-220:width-20]
        frame[20:120, width-220:width-20] = cv2.GaussianBlur(logo_zone, (51, 51), 0)
        sub_zone = frame[height-150:height-20, 100:width-100]
        frame[height-150:height-20, 100:width-100] = cv2.GaussianBlur(sub_zone, (51, 51), 0)
        out.write(frame)
    cap.release(); out.release()
    return output_path

async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

def get_gemini_script(video_desc):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Write a dramatic movie recap narration in Burmese: {video_desc}"
    return model.generate_content(prompt).text

# --- UI ---
st.title("🎬 Burmese Movie Recap AI")
uploaded_file = st.file_uploader("ဗီဒီယိုတင်ပါ", type=['mp4'])

if uploaded_file:
    with open("temp.mp4", "wb") as f: f.write(uploaded_file.read())
    video_desc = st.text_area("ဇာတ်လမ်းအကျဉ်း")
    if st.button("Recap ပြုလုပ်ပါ"):
        with st.status("Processing..."):
            script = get_gemini_script(video_desc)
            asyncio.run(generate_voice(script, "voice.mp3"))
            blurred = apply_blur_to_video("temp.mp4", "blurred.mp4")
            final = adjust_video_sync(blurred, "voice.mp3", "final.mp4")
        st.video(final)
        with open(final, "rb") as f:
            st.download_button("Download Video", f, "recap.mp4")

