import streamlit as st
import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
from supabase import create_client
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile

# --- CONFIGURATION ---
SUPABASE_URL = "https://mflfazgkhpxgkejjmckq.supabase.co"
SUPABASE_KEY = "sb_publishable_GuLum9W9d3wyDL-s6BsN7w_I1fnHCUg"
GEMINI_API_KEY = "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Burmese Movie Recap AI", layout="wide")

# --- FUNCTIONS ---

def adjust_video_sync(video_path, audio_path, output_path):
    """ဗီဒီယိုအရှည်ကို အသံနဲ့ကိုက်အောင် ညှိပြီး Output ထုတ်ပေးခြင်း"""
    video_clip = VideoFileClip(video_path).without_audio()
    audio_clip = AudioFileClip(audio_path)
    
    # Duration ညှိနှိုင်းခြင်း
    speed_factor = video_clip.duration / audio_clip.duration
    final_video = video_clip.fx(vfx.speedx, speed_factor).set_audio(audio_clip)
    
    # အကုန်လုံး အဆင်ပြေမယ့် mp4 format နဲ့ ထုတ်ပေးခြင်း
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
    return output_path

def apply_blur_to_video(video_path, output_path):
    """Logo နဲ့ Subtitle နေရာများကို Blur လုပ်ခြင်း"""
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None: fps = 24
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # Logo Blur (Top Right)
        logo_zone = frame[10:110, width-210:width-10]
        if logo_zone.size > 0:
            frame[10:110, width-210:width-10] = cv2.GaussianBlur(logo_zone, (51, 51), 0)
        
        # Subtitle Blur (Bottom)
        sub_zone = frame[height-140:height-10, 50:width-50]
        if sub_zone.size > 0:
            frame[height-140:height-10, 50:width-50] = cv2.GaussianBlur(sub_zone, (51, 51), 0)
        
        out.write(frame)
    
    cap.release()
    out.release()
    return output_path

async def generate_voice(text, output_path):
    """ဗမာအသံ ထုတ်ပေးခြင်း"""
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

def get_gemini_script(video_desc):
    """Gemini AI နဲ့ ဇာတ်ညွှန်းရေးခြင်း"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Write a dramatic movie recap narration in Burmese based on this: {video_desc}. Start with 'ဇာတ်လမ်းစစချင်းမှာ...'"
    response = model.generate_content(prompt)
    return response.text

# --- UI ---
st.title("🎬 Burmese Movie Recap AI (All Formats Support)")

# File uploader မှာ webm, mov, avi တို့ပါ ထည့်ထားပါတယ်
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ (MP4, WEBM, MOV, AVI)", type=['mp4', 'webm', 'mov', 'avi', 'mkv'])

if uploaded_file:
    # ယာယီဖိုင်အဖြစ် သိမ်းဆည်းခြင်း
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    st.info(f"တင်လိုက်သောဖိုင်: {uploaded_file.name}")
    video_desc = st.text_area("ဒီဗီဒီယိုအကြောင်း ဘာပြောမလဲ? (AI ဇာတ်ညွှန်းရေးရန်)")
    
    if st.button("Recap ဗီဒီယို စတင်ထုတ်လုပ်ပါ"):
        if not video_desc:
            st.warning("ဇာတ်လမ်းအကျဉ်းလေး အရင်ရေးပေးပါဦး။")
        else:
            with st.status("ဗီဒီယို ပြုပြင်နေပါပြီ... ခေတ္တစောင့်ပါ", expanded=True) as status:
                # 1. AI Script
                st.write("📝 AI က ဇာတ်ညွှန်းရေးနေသည်...")
                script = get_gemini_script(video_desc)
                
                # 2. AI Voice
                st.write("🎙️ ဗမာအသံသွင်းနေသည်...")
                asyncio.run(generate_voice(script, "voice.mp3"))
                
                # 3. Blur Process
                st.write("🌫️ Logo နဲ့ Subtitle များကို Blur လုပ်နေသည်...")
                blurred_vid = apply_blur_to_video(tfile.name, "blurred.mp4")
                
                # 4. Final Sync
                st.write("⚡ အသံနဲ့ ဗီဒီယိုကို Speed ညှိပြီး ပေါင်းစပ်နေသည်...")
                final_output = adjust_video_sync(blurred_vid, "voice.mp3", "final_recap.mp4")
                
                status.update(label="✅ အားလုံး ပြီးပါပြီ!", state="complete")
            
            st.video(final_output)
            with open(final_output, "rb") as f:
                st.download_button("📥 Download Recap Video", f, file_name="myanmar_recap.mp4")

st.divider()
st.caption("Developed for Burmese Movie Recappers | Supported formats: MP4, WEBM, MOV, AVI")
