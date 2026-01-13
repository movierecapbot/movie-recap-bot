import streamlit as st
import os
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import time
from moviepy.editor import VideoFileClip, AudioFileClip, vfx

# --- CONFIG ---
st.set_page_config(page_title="Burmese Movie Recap AI", layout="wide")
st.title("🎬 Burmese Movie Recap AI")

# API Setup
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4")
genai.configure(api_key=GEMINI_API_KEY)

# --- FUNCTIONS ---
def get_ai_recap(video_path):
    try:
        # Model နာမည်ကို models/ မပါဘဲ တိုက်ရိုက်ခေါ်ကြည့်ခြင်း
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.spinner("AI က ဗီဒီယိုကို ဖတ်နေသည်..."):
            myfile = genai.upload_file(video_path)
            
            # စောင့်ဆိုင်းခြင်း
            while myfile.state.name == "PROCESSING":
                time.sleep(2)
                myfile = genai.get_file(myfile.name)
            
            prompt = "Translate this video content into a dramatic Burmese movie recap script. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Output only Burmese text."
            response = model.generate_content([myfile, prompt])
            return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

async def make_voice(text, path):
    tts = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await tts.save(path)

# --- UI ---
up_file = st.file_uploader("ဗီဒီယိုတင်ပါ", type=['mp4', 'webm'])

if up_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(up_file.read())
        video_in = tmp.name

    if st.button("Recap လုပ်မည်"):
        # 1. Script
        script = get_ai_recap(video_in)
        
        if "AI Error" in script:
            st.error(f"နည်းပညာအခက်အခဲရှိနေပါသည်- {script}")
            st.info("အကြံပြုချက်- API Key အသစ်တစ်ခုဖြင့် စမ်းသပ်ကြည့်ပါ။")
        else:
            st.subheader("📝 Script")
            st.write(script)

            # 2. Voice & Merge
            with st.spinner("အသံသွင်းပြီး ဗီဒီယိုထုတ်လုပ်နေသည်..."):
                asyncio.run(make_voice(script, "audio.mp3"))
                
                v_clip = VideoFileClip(video_in).without_audio()
                a_clip = AudioFileClip("audio.mp3")
                speed = v_clip.duration / a_clip.duration
                final = v_clip.fx(vfx.speedx, speed).set_audio(a_clip)
                final.write_videofile("done.mp4", codec="libx264")
                st.video("done.mp4")
