import streamlit as st
import os
import google.generativeai as genai
import edge_tts
import asyncio
import tempfile
import time
from moviepy.editor import VideoFileClip, AudioFileClip, vfx

# --- INITIAL SETUP ---
st.set_page_config(page_title="Burmese Movie Recap AI", layout="wide")
st.title("🎬 Burmese Movie Recap AI")

# API Key - Secrets ထဲမှာ မရှိရင် အောက်က Key ကို သုံးမယ်
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4")

# ပြဿနာအရှိဆုံးဖြစ်တဲ့ API Version ကို Stable ဖြစ်တဲ့ v1 သို့ ပြောင်းလဲခြင်း
os.environ["GOOGLE_GENERATIVE_AI_API_VERSION"] = "v1"
genai.configure(api_key=GEMINI_API_KEY)

def analyze_video(video_path):
    try:
        # Model Name ကို အတိအကျ ပြောင်းလဲထားပါသည်
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
        
        with st.spinner("AI က ဗီဒီယိုကို စစ်ဆေးနေပါသည်..."):
            video_file = genai.upload_file(path=video_path)
            
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                return "Video processing failed."

            prompt = "ဇာတ်လမ်းစစချင်းမှာ... ဆိုတဲ့ စကားလုံးနဲ့ စတင်ပြီး ဒီဗီဒီယိုကို စိတ်ဝင်စားစရာကောင်းအောင် မြန်မာလို Movie Recap ဇာတ်ညွှန်း ရေးပေးပါ။"
            response = model.generate_content([video_file, prompt])
            return response.text
    except Exception as e:
        return f"Error: {str(e)}"

async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

# --- UI ---
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm', 'mov'])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
        tfile.write(uploaded_file.read())
        input_path = tfile.name

    if st.button("Recap လုပ်မည်"):
        # 1. Script
        script_text = analyze_video(input_path)
        
        if "Error" in script_text:
            st.error(f"AI က အဆင်မပြေဖြစ်နေပါသည်: {script_text}")
        else:
            st.subheader("📝 Recap Script (Burmese)")
            st.write(script_text)

            # 2. Voice
            with st.spinner("အသံဖိုင် ပြောင်းလဲနေသည်..."):
                asyncio.run(generate_voice(script_text, "voice.mp3"))
            
            # 3. Final Video
            try:
                with st.spinner("ဗီဒီယို ပေါင်းစပ်နေသည်..."):
                    v_clip = VideoFileClip(input_path).without_audio()
                    a_clip = AudioFileClip("voice.mp3")
                    # Speed adjustment
                    speed = v_clip.duration / a_clip.duration
                    final_video = v_clip.fx(vfx.speedx, speed).set_audio(a_clip)
                    final_video.write_videofile("recap_done.mp4", codec="libx264")
                    st.video("recap_done.mp4")
            except Exception as e:
                st.error(f"Video Merge Error: {e}")
