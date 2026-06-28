import os
import re
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Load environment variables
load_dotenv()

# NVIDIA API key
API_KEY = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY")

# Streamlit configuration
st.set_page_config(
    page_title="Aether AI",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom styles
st.markdown("""
<style>
/* ... */
</style>
""", unsafe_allow_html=True)

# Guard
if not API_KEY:
    st.error("")
    st.stop()

# Session state
SYSTEM_PROMPT = (
    "You are Aether, an elite AI intelligence engine powered by NVIDIA. "
    "Be concise and precise. Use markdown for structure: bold key terms, "
    "use bullet points for lists, and fenced code blocks for code. "
    "Never pad responses with filler phrases."
)
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Header
st.markdown("""
<div class="aether-header">
    <div class="aether-brand">
        <div class="aether-logo"></div>
        <div class="aether-title">Aether</div>
    </div>
    <div class="aether-badge">Online</div>
</div>
""", unsafe_allow_html=True)

# Render message
def render_message(role: str, content: str):
    if role == "user":
        safe = (content
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        safe = re.sub(r'\*(.+?)\*', r'<em>\1</em>', safe)
        safe = re.sub(r'`(.+?)`', r'<code>\1</code>', safe)
        safe = safe.replace("\n", "<br>")
        st.markdown(f"""
<div class="chat-row user-row">
    <div class="bubble user-bubble">{safe}</div>
</div>
""", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([0.04, 0.96])
        with col1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            st.markdown(content, unsafe_allow_html=False)
            st.markdown('</div>', unsafe_allow_html=True)

# Stream response
def stream_response(messages: list, input_type: str) -> str:
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=API_KEY,
    )
    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
    with col2:
        stream_placeholder = st.empty()
        accumulated = ""
        if input_type == "audio":
            audio_file = messages[-1]["content"]
            response = client.audio.analyze(audio_file)
        elif input_type == "image":
            image_file = messages[-1]["content"]
            response = client.image.analyze(image_file)
        elif input_type == "text":
            text_input = messages[-1]["content"]
            response = client.text.analyze(text_input)
        elif input_type == "video":
            video_file = messages[-1]["content"]
            response = client.video.analyze(video_file)
        if response.status_code == 200:
            return response.json()
        else:
            return None

# Audio input
audio_file = st.file_uploader("Upload audio file")
if audio_file:
    audio = AudioSegment.from_file(audio_file)
    st.audio(audio)

# Image input
image_file = st.file_uploader("Upload image file")
if image_file:
    image = Image.open(image_file)
    st.image(image)

# Reasoning task
reasoning_task = st.selectbox("Select reasoning task", ["Task 1", "Task 2"])
if reasoning_task:
    model = AutoModelForSeq2SeqLM.from_pretrained("t5-base")
    tokenizer = AutoTokenizer.from_pretrained("t5-base")
    input_text = st.text_input("Enter input text")
    if input_text:
        inputs = tokenizer.encode(input_text, return_tensors="pt")
        outputs = model.generate(inputs)
        st.write(tokenizer.decode(outputs[0]))

# Text input
text_input = st.text_input("Enter text input")
if text_input:
    api_response = stream_response(st.session_state.messages + [{"role": "user", "content": text_input}], "text")
    st.write(api_response)

# Video input
video_file = st.file_uploader("Upload video file")
if video_file:
    video = VideoFileClip(video_file)
    st.video(video)

# Chat interface
if st.session_state.messages:
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"])

# Input & inference
if user_input := st.chat_input("Message Aether…"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    render_message("user", user_input)
    try:
        ai_text = stream_response(st.session_state.messages, "text")
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
    except Exception as exc:
        render_message("assistant", f"**Error:** {exc}")
