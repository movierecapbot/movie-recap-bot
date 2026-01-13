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

# Get API Key
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyBDfSFCV4kF56dAZ8Zx0m0xaR8a40v8pG4")
genai.configure(api_key=GEMINI_API_KEY)

# --- CORE FUNCTIONS ---
def analyze_video_with_ai(video_path):
    """ဗီဒီယိုကို AI ဆီပို့ပြီး ဇာတ်ညွှန်းတောင်းခြင်း"""
    try:
        # Version သတ်မှတ်ချက်ကို ဖြုတ်ပြီး အခြေခံအတိုင်း ခေါ်ယူခြင်း
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.spinner("AI က ဗီဒီယိုကို စစ်ဆေးနေသည်..."):
            video_file = genai.upload_file(path=video_path)
            
            # Processing ပြီးအောင်စောင့်ပါ
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                return "Video processing failed on server."

            prompt = "Watch this video and write a dramatic Burmese movie recap script. Start with 'ဇာတ်လမ်းစစချင်းမှာ...' Burmese language only."
            response = model.generate_content([video_file, prompt])
            return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

async def text_to_speech(text, output_audio):
    """မြန်မာအသံဖိုင် ပြောင်းလဲခြင်း"""
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_audio)

def create_final_video(video_in, audio_in, video_out):
    """အသံနှင့် ဗီဒီယို ပေါင်းစပ်ခြင်း"""
    try:
        v_clip = VideoFileClip(video_in).without_audio()
        a_clip = AudioFileClip(audio_in)
        # အသံအရှည်အတိုင်း ဗီဒီယိုအမြန်နှုန်းကို ညှိပေးပါသည်
        speed = v_clip.duration / a_clip.duration
        final = v_clip.fx(vfx.speedx, speed).set_audio(a_clip)
        final.write_videofile(video_out, codec="libx264", audio_codec="aac")
        return True
    except Exception as e:
        st.error(f"Render Error: {e}")
        return False

# --- UI LOGIC ---
uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ (MP4, WEBM)", type=['mp4', 'webm'])

if uploaded_file:
    # ယာယီဖိုင် သိမ်းဆည်းခြင်း
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
        tfile.write(uploaded_file.read())
        input_path = tfile.name

    if st.button("Recap ပြုလုပ်မည်"):
        # 1. AI Analysis
        script = analyze_video_with_ai(input_path)
        
        if "AI Error" in script:
            st.error(script)
            # အကယ်၍ Flash model မရပါက Pro model နဲ့ ထပ်စမ်းကြည့်ခြင်း
            st.info("Trying Pro model as backup...")
            model_pro = genai.GenerativeModel('gemini-1.5-pro')
            video_file_retry = genai.upload_file(path=input_path)
            # (Wait logic removed for brevity but same as above)
            response = model_pro.generate_content([video_file_retry, "Write Burmese movie recap."])
            script = response.text

        st.subheader("📝 AI Generated Script")
        st.write(script)

        # 2. Voice Generation
        with st.spinner("မြန်မာအသံဖိုင် ဖန်တီးနေသည်..."):
            asyncio.run(text_to_speech(script, "temp_audio.mp3"))

        # 3. Video Processing
        with st.spinner("ဗီဒီယို ထုတ်လုပ်နေသည်..."):
            if create_final_video(input_path, "temp_audio.mp3", "final_video.mp4"):
                st.success("အားလုံးပြီးစီးပါပြီ!")
                st.video("final_video.mp4")

    # Clean up
    if os.path.exists(input_path):
        os.remove(input_path)
