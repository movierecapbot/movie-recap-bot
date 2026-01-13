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
        st.error(f"Video Sync Error: {e}")
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
        # Blur logos (Adjust coordinates as needed)
        h, w, _ = frame.shape
        # Top Right
        frame[10:110, w-210:w-10] = cv2.GaussianBlur(frame[10:110, w-210:w-10], (51, 51), 0)
        # Bottom
        frame[h-140:h-10, 50:w-50] = cv2.GaussianBlur(frame[h-140:h-10, 50:w-50], (51, 51), 0)
        out.write(frame)
    cap.release(); out.release()
    return output_path

async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

def analyze_and_recap(video_file_path):
    # Model name 'gemini-1.5-flash' works with google-generativeai>=0.8.3
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.spinner("AI က ဗီဒီယိုကို ဖတ်ရှုနေသည် (ခဏစောင့်ပါ)..."):
        video_file = genai.upload_file(path=video_file_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            raise ValueError("Video processing failed by Google AI.")

    prompt = "Listen to the audio, translate to Burmese and write a dramatic movie recap script. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Burmese only."
    response = model.generate_content([video_file, prompt])
    return response.text

# --- UI ---
st.title("🎬 Burmese Movie Recap AI")
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm', 'mov', 'avi'])

if uploaded_file:
    # Save temp file
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
        tfile.write(uploaded_file.read())
        temp_path = tfile.name
    
    if st.button("Recap လုပ်မည်"):
        try:
            # 1. Generate Script
            script = analyze_and_recap(temp_path)
            st.success("ဇာတ်ညွှန်းရရှိပါပြီ!")
            st.text_area("Script", script, height=200)
            
            # 2. Generate Voice
            asyncio.run(generate_voice(script, "voice.mp3"))
            st.success("အသံဖိုင်ရရှိပါပြီ!")
            
            # 3. Process Video
            with st.spinner("ဗီဒီယိုကို ပေါင်းစပ်နေသည်..."):
                blurred_path = "blurred.mp4"
                final_path = "final_recap.mp4"
                apply_blur_to_video(temp_path, blurred_path)
                adjust_video_sync(blurred_path, "voice.mp3", final_path)
                
            st.video(final_path)
            
        except Exception as e:
            st.error(f"Error ဖြစ်ပွားပါသည်: {e}")
        finally:
            # Cleanup
            if os.path.exists(temp_path): os.remove(temp_path)
