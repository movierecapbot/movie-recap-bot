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
GEMINI_API_KEY = "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4"

# ⚠️ အရေးကြီးဆုံးအပိုင်း- v1beta Error ကို ကျော်ရန် API Version ကို v1 အဖြစ် Force လုပ်ခြင်း
os.environ["GOOGLE_GENERATIVE_AI_API_VERSION"] = "v1"
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Auto Burmese Movie Recap AI", layout="wide")

# --- FUNCTIONS ---

def adjust_video_sync(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path).without_audio()
    audio_clip = AudioFileClip(audio_path)
    speed_factor = video_clip.duration / audio_clip.duration
    final_video = video_clip.fx(vfx.speedx, speed_factor).set_audio(audio_clip)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
    return output_path

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
        logo = frame[10:110, width-210:width-10]
        if logo.size > 0: frame[10:110, width-210:width-10] = cv2.GaussianBlur(logo, (51, 51), 0)
        sub = frame[height-140:height-10, 50:width-50]
        if sub.size > 0: frame[height-140:height-10, 50:width-50] = cv2.GaussianBlur(sub, (51, 51), 0)
        out.write(frame)
    cap.release(); out.release()
    return output_path

async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await asyncio.wait_for(communicate.save(output_path), timeout=60)

def analyze_and_recap(video_file_path):
    # Model နာမည်ကို models/ မပါဘဲ တိုက်ရိုက်ခေါ်ကြည့်ခြင်း (Version v1 အတွက်)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    st.write("📤 ဗီဒီယိုဖိုင်ကို AI ဆီ တင်ပို့နေသည်...")
    video_file = genai.upload_file(path=video_file_path)
    
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    prompt = (
        "Watch this video and listen to the audio carefully. "
        "Summarize the story and translate it into a dramatic Burmese movie recap script. "
        "Start with 'ဇာတ်လမ်းစစချင်းမှာ...'. Output Burmese text only."
    )
    
    response = model.generate_content([video_file, prompt])
    return response.text

# --- UI ---
st.title("🎬 Burmese Movie Recap AI")
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm', 'mov', 'avi'])

if uploaded_file:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tfile:
        tfile.write(uploaded_file.read())
        temp_path = tfile.name
    
    if st.button("အလိုအလျောက် Recap ပြုလုပ်ပါ"):
        with st.status("AI အလုပ်လုပ်နေသည်...", expanded=True) as status:
            try:
                # 1. AI Analysis
                st.write("🕵️ AI က ဗီဒီယိုကို နားထောင်နေသည် (ခေတ္တစောင့်ပါ)...")
                script = analyze_and_recap(temp_path)
                st.success("ဇာတ်ညွှန်း ရရှိပါပြီ!")
                
                # 2. Voice
                st.write("🎙️ ဗမာအသံသွင်းနေသည်...")
                asyncio.run(generate_voice(script, "voice.mp3"))
                
                # 3. Processing
                st.write("🌫️ ဗီဒီယိုကို ပြုပြင်နေသည်...")
                blurred = apply_blur_to_video(temp_path, "blurred.mp4")
                final = adjust_video_sync(blurred, "voice.mp3", "final.mp4")
                
                status.update(label="✅ အားလုံး ပြီးပါပြီ!", state="complete")
                st.video(final)
                with open(final, "rb") as f:
                    st.download_button("📥 Download Video", f, "recap.mp4")
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)
