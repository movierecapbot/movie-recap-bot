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

# Streamlit Secrets ကနေ Key ကို ယူခြင်း
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        st.error("Secrets ထဲမှာ GEMINI_API_KEY ကို ရှာမတွေ့ပါ။")
        st.stop()
except Exception as e:
    st.error(f"Config Error: {e}")
    st.stop()

# --- FUNCTIONS ---
def analyze_video_ai(video_path):
    try:
        # Model နာမည်ကို အခြေခံအကျဆုံးပုံစံဖြင့် ခေါ်ဆိုခြင်း
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.spinner("AI က ဗီဒီယိုကို လေ့လာနေသည်..."):
            video_file = genai.upload_file(path=video_path)
            
            # Processing ပြီးအောင် စောင့်ပါ
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                return "AI Error: ဗီဒီယိုကို ဖတ်လို့မရပါ။"

            prompt = "Translate this video content and write a dramatic Burmese movie recap script. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Output only Burmese text."
            response = model.generate_content([video_file, prompt])
            return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

async def generate_burmese_voice(text, output_audio):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_audio)

# --- UI ---
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ (MP4 or WEBM)", type=['mp4', 'webm'])

if uploaded_file:
    # ယာယီဖိုင်အဖြစ် သိမ်းဆည်းခြင်း
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
        tfile.write(uploaded_file.read())
        temp_input_path = tfile.name

    if st.button("Recap ပြုလုပ်မည်"):
        # 1. AI ဇာတ်ညွှန်း ရယူခြင်း
        script = analyze_video_ai(temp_input_path)
        
        if "AI Error" in script:
            st.error(script)
        else:
            st.subheader("📝 AI ရေးပေးသော ဇာတ်ညွှန်း")
            st.info(script)

            # 2. အသံဖိုင် ဖန်တီးခြင်း
            with st.spinner("မြန်မာအသံဖိုင် ပြုလုပ်နေသည်..."):
                audio_path = "recap_audio.mp3"
                asyncio.run(generate_burmese_voice(script, audio_path))

            # 3. ဗီဒီယိုနှင့် အသံကို ပေါင်းစပ်ခြင်း
            with st.spinner("ဗီဒီယိုနှင့် အသံကို ညှိနေသည်..."):
                try:
                    video_clip = VideoFileClip(temp_input_path).without_audio()
                    audio_clip = AudioFileClip(audio_path)
                    
                    # အသံအရှည်အတိုင်း ဗီဒီယိုမြန်နှုန်းကို ညှိပေးသည်
                    speed_factor = video_clip.duration / audio_clip.duration
                    final_clip = video_clip.fx(vfx.speedx, speed_factor).set_audio(audio_clip)
                    
                    final_video_name = "final_movie_recap.mp4"
                    final_clip.write_videofile(final_video_name, codec="libx264", audio_codec="aac")
                    
                    st.success("အားလုံးပြီးပါပြီ။ အောက်မှာ ကြည့်နိုင်ပါတယ်။")
                    st.video(final_video_name)
                except Exception as ve:
                    st.error(f"Render Error: {ve}")

    # File Cleanup
    if os.path.exists(temp_input_path):
        os.remove(temp_input_path)
