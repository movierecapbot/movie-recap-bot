import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ImageClip
import moviepy.video.fx.all as vfx

# --- ၁။ UI Styling (Neon Dark Theme) ---
st.set_page_config(page_title="Movie Recap AI Bot", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #ffffff; }
    .stButton>button {
        background: linear-gradient(90deg, #00dbde 0%, #fc00ff 100%);
        color: white; border: none; border-radius: 8px; font-weight: bold; width: 100%;
    }
    .stTextArea textarea { background-color: #161b22; color: #00ffcc; border: 1px solid #30363d; font-size: 16px; }
    h1, h2, h3 { color: #00ffcc; text-shadow: 0 0 10px #00ffcc; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- ၂။ Backend Functions ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

async def get_clean_script(video_path):
    """ဗီဒီယိုကိုကြည့်ပြီး AI Voice ဖတ်ရန် သင့်တော်သော Storyteller Script သီးသန့်ထုတ်ပေးခြင်း"""
    with open(video_path, "rb") as f:
        # Prompt ကို အပိုစာသားမပါရန် သေချာညွှန်ကြားထားသည်
        prompt = "Analyze this video and write a clean Burmese movie recap script in a dramatic storyteller style. Output ONLY the story narration text that will be read by an AI voice. Do not include timecodes, headers, or any English text. Start with 'ဇာတ်လမ်းစစချင်းမှာတော့...'"
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[prompt, genai.types.Part.from_bytes(data=f.read(), mime_type="video/mp4")]
        )
    return response.text

async def generate_voice(text, voice_name, output_path):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)

# --- ၃။ Main Interface (All in One Page) ---
st.markdown("<h1 style='text-align: center;'>🎬 MOVIE RECAP BOT - AI AUTOMATION</h1>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns([1, 1], gap="large")

# --- Left Column: Input & Controls ---
with col1:
    st.subheader("📁 1. Media Upload")
    video_input = st.file_uploader("ဗီဒီယိုဖိုင်တင်ပါ", type=['mp4', 'webm'])
    
    st.subheader("🎙️ 2. Voice Settings")
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        voice_option = st.radio("အသံရွေးပါ", ["Male (Thiha)", "Female (Nilar)"])
        selected_voice = "my-MM-ThihaNeural" if "Male" in voice_option else "my-MM-NilarNeural"
    with v_col2:
        audio_upload = st.file_uploader("ကိုယ်ပိုင်အသံတင်ရန် (Optional)", type=['mp3', 'wav'])

    st.subheader("🖼️ 3. Logo & Branding")
    logo_input = st.file_uploader("Logo တင်ပါ", type=['png', 'jpg'])
    logo_pos = st.selectbox("Logo Position", ["top-right", "top-left", "bottom-right", "bottom-left"])

# --- Right Column: Script & Preview ---
with col2:
    st.subheader("🤖 4. AI Script Output")
    
    # Script Generate Button
    if st.button("Generate Clean Script"):
        if video_input:
            with st.spinner("AI က ဗီဒီယိုကို လေ့လာပြီး ဇာတ်ညွှန်းရေးနေသည်..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(video_input.read())
                    st.session_state.video_path = tmp.name
                    st.session_state.raw_script = asyncio.run(get_clean_script(tmp.name))
        else:
            st.error("ဗီဒီယို အရင်တင်ပေးပါ။")

    # Script Area (Edit လုပ်လို့ရသည်)
    final_script = st.text_area("Edit Narration:", value=st.session_state.get('raw_script', ""), height=250)
    
    # Audio Preview
    if st.button("Generate/Preview Voice"):
        if final_script:
            with st.spinner("AI အသံသွင်းနေသည်..."):
                audio_path = "final_audio.mp3"
                asyncio.run(generate_voice(final_script, selected_voice, audio_path))
                st.session_state.final_audio = audio_path
                st.audio(audio_path)
        else:
            st.warning("Script အရင်ထုတ်ပေးပါ။")

st.divider()

# --- ၄။ Final Processing Section (Bottom) ---
st.subheader("🚀 5. Final Rendering")
if st.button("Generate & Download Final Video"):
    if video_input and (st.session_state.get('final_audio') or audio_upload):
        with st.status("ဗီဒီယို အချောသတ်နေသည်... (Ads)", expanded=True) as status:
            try:
                # Path သတ်မှတ်ခြင်း
                v_path = st.session_state.video_path
                a_path = audio_upload if audio_upload else st.session_state.final_audio
                
                # MoviePy Processing
                st.write("ဗီဒီယိုနှင့် အသံကို ညှိနေသည်...")
                video_clip = VideoFileClip(v_path).without_audio()
                audio_clip = AudioFileClip(a_path if isinstance(a_path, str) else a_path.name)
                
                # Speed Sync
                final_v = video_clip.fx(vfx.speedx, video_clip.duration / audio_clip.duration).set_audio(audio_clip)
                
                # Logo Overlay
                if logo_input:
                    st.write("Logo ထည့်သွင်းနေသည်...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as ltmp:
                        ltmp.write(logo_input.read())
                        logo = ImageClip(ltmp.name).set_duration(final_v.duration).resize(height=50).margin(right=10, top=10, opacity=0).set_pos(logo_pos.split('-'))
                        final_v = CompositeVideoClip([final_v, logo])

                output_name = "recap_final.mp4"
                final_v.write_videofile(output_name, codec="libx264", audio_codec="aac")
                
                st.video(output_name) # Preview ပေါ်စေရန်
                with open(output_name, "rb") as f:
                    st.download_button("📥 Download Recap Video", f, file_name="movie_recap.mp4")
                
                status.update(label="အားလုံး ပြီးပါပြီ!", state="complete", expanded=False)
            except Exception as e:
                st.error(f"Render Error: {e}")
    else:
        st.error("ဗီဒီယိုနှင့် အသံဖိုင် (Generate Voice) အရင်လုပ်ဆောင်ပေးပါ။")
