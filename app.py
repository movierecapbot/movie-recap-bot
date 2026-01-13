import streamlit as st
from google import genai
import edge_tts
import asyncio
import tempfile
import os
import time

# --- CONFIG ---
st.set_page_config(page_title="Burmese Movie Recap AI (Gemini 3)", layout="wide")
st.title("🎬 Burmese Movie Recap AI (Gemini 3)")

# Get API Key
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    st.error("Secrets ထဲမှာ GEMINI_API_KEY ထည့်ပေးပါ။")
    st.stop()

# Gemini 3 Client Setup
client = genai.Client(api_key=GEMINI_API_KEY)

async def generate_recap(video_path):
    try:
        # Video Upload
        with st.spinner("AI ဆီ ဗီဒီယို ပေးပို့နေသည်..."):
            with open(video_path, "rb") as f:
                # Gemini 3 တွင် gemini-3-flash-preview ကို သုံးရပါမည်
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=[
                        "Write a dramatic Burmese movie recap script for this video. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Output only Burmese text.",
                        genai.types.Part.from_bytes(data=f.read(), mime_type="video/mp4")
                    ]
                )
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

    if st.button("Recap ပြုလုပ်မည်"):
        # 1. Generate Script
        script = asyncio.run(generate_recap(video_in))
        
        if "AI Error" in script:
            st.error(script)
            st.info("Gemini 3 Flash သည် Preview ဖြစ်သောကြောင့် တစ်ခါတလေ Server ကြာတတ်ပါသည်။ ခဏနေပြန်စမ်းပါ။")
        else:
            st.subheader("📝 AI Recap Script")
            st.write(script)

            # 2. Voice & Merge
            with st.spinner("အသံသွင်းနေသည်..."):
                audio_path = "out.mp3"
                asyncio.run(make_voice(script, audio_path))
                st.audio(audio_path)
                st.success("ဗီဒီယိုဖန်တီးမှုအပိုင်းကို Gemini 3 ဖြင့် အချောသတ်နေပါသည်။")

    if os.path.exists(video_in):
        os.remove(video_in)
