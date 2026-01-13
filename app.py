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

# Get API Key from Secrets
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    # ဤစာကြောင်းသည် v1beta error ကို ကျော်ဖြတ်ရန် အဓိကဖြစ်သည်
    os.environ["GOOGLE_GENERATIVE_AI_API_VERSION"] = "v1"
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("Secrets ထဲမှာ GEMINI_API_KEY မရှိသေးပါ။")
    st.stop()

# --- FUNCTIONS ---
def analyze_video_v1(video_path):
    try:
        # v1 stable လမ်းကြောင်းမှ ခေါ်ယူခြင်း
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.spinner("AI က ဗီဒီယိုကို စတင်စစ်ဆေးနေပါသည်..."):
            video_file = genai.upload_file(path=video_path)
            
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                return "AI Error: Video upload failed."

            prompt = "Write a dramatic Burmese movie recap script for this video. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Burmese language only."
            response = model.generate_content([video_file, prompt])
            return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

async def text_to_speech(text, output_audio):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_audio)

# --- UI ---
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm'])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
        tfile.write(uploaded_file.read())
        input_path = tfile.name

    if st.button("Recap လုပ်မည်"):
        # 1. AI Analysis
        script = analyze_video_v1(input_path)
        
        if "AI Error" in script:
            st.error(f"Error တက်နေပါသည်: {script}")
            st.info("အကယ်၍ 404 ပြနေသေးပါက Streamlit Cloud တွင် App ကို Delete လုပ်ပြီး ပြန်တင်ကြည့်ပါ။")
        else:
            st.subheader("📝 Script")
            st.write(script)

            # 2. TTS
            with st.spinner("အသံသွင်းနေပါသည်..."):
                audio_path = "voice.mp3"
                asyncio.run(text_to_speech(script, audio_path))

            # 3. Merge
            try:
                with st.spinner("ဗီဒီယို ထုတ်လုပ်နေပါသည်..."):
                    v_clip = VideoFileClip(input_path).without_audio()
                    a_clip = AudioFileClip(audio_path)
                    speed = v_clip.duration / a_clip.duration
                    final = v_clip.fx(vfx.speedx, speed).set_audio(a_clip)
                    final.write_videofile("recap_done.mp4", codec="libx264")
                    st.video("recap_done.mp4")
            except Exception as e:
                st.error(f"Render Error: {e}")

    if os.path.exists(input_path):
        os.remove(input_path)
