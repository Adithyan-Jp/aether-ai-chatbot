"""
Aether AI — Multimodal Chatbot
Supports: Text · Image · Audio · Video · Reasoning
Powered by NVIDIA NIM APIs
"""

import os
import re
import io
import base64
import tempfile
import requests as http_requests

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────

try:
    API_KEY = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
except Exception:
    API_KEY = os.getenv("NVIDIA_API_KEY", "")
NIM_BASE = "https://integrate.api.nvidia.com/v1"
IMG_GEN_URL = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl"

MODELS = {
    "text": "meta/llama-3.1-70b-instruct",
    "vision": "meta/llama-3.2-11b-vision-instruct",
    "reasoning": "deepseek-ai/deepseek-r1",
}

MODES = {
    "💬 Text": {"key": "text", "desc": "Standard AI conversation"},
    "🖼️ Image": {"key": "image", "desc": "Analyze or generate images"},
    "🎤 Audio": {"key": "audio", "desc": "Voice input & spoken responses"},
    "🎬 Video": {"key": "video", "desc": "Upload & analyze video content"},
    "🧠 Reasoning": {"key": "reasoning", "desc": "Deep chain-of-thought reasoning"},
}

MAX_VIDEO_MB = 25
MAX_FRAMES = 6

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Aether AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Massive CSS block ────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Base ── */
.stApp, html, body, [data-testid="stAppViewContainer"] {
    background: #07080D !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.main .block-container {
    max-width: 760px !important;
    padding-top: 0 !important;
    padding-bottom: 8rem !important;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0A0C14 !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
}

/* ── Header ── */
.aether-header {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0;
    margin-bottom: 1.5rem;
    background: #07080D;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.aether-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.aether-logo {
    width: 32px;
    height: 32px;
    border-radius: 10px;
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15));
    border: 1px solid rgba(99,102,241,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}
.aether-title {
    font-size: 16px;
    font-weight: 700;
    color: #E0E4F0;
    letter-spacing: -0.3px;
}
.aether-badge {
    font-size: 9px;
    font-weight: 600;
    color: #38A169;
    background: rgba(56,161,105,0.08);
    border: 1px solid rgba(56,161,105,0.18);
    border-radius: 20px;
    padding: 2px 8px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* ── Mode badge ── */
.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.3px;
    margin-bottom: 1.2rem;
}
.mode-badge.text { background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.18); color: #818CF8; }
.mode-badge.image { background: rgba(236,72,153,0.08); border: 1px solid rgba(236,72,153,0.18); color: #EC4899; }
.mode-badge.audio { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.18); color: #10B981; }
.mode-badge.video { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.18); color: #F59E0B; }
.mode-badge.reasoning { background: rgba(139,92,246,0.08); border: 1px solid rgba(139,92,246,0.18); color: #8B5CF6; }

/* ── Chat rows ── */
.chat-row {
    display: flex;
    width: 100%;
    margin-bottom: 1.5rem;
    gap: 10px;
    align-items: flex-start;
}
.chat-row.user-row    { justify-content: flex-end; }
.chat-row.assistant-row { justify-content: flex-start; }

/* ── Avatars ── */
.avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 11px;
    font-weight: 600;
    margin-top: 3px;
}
.avatar.ai {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15));
    border: 1px solid rgba(99,102,241,0.25);
    color: #818CF8;
}
.avatar.user {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: #606880;
}

/* ── Bubbles ── */
.bubble {
    max-width: 82%;
    font-size: 14.5px;
    line-height: 1.75;
    word-wrap: break-word;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.bubble.user-bubble {
    background: #111420;
    border: 1px solid rgba(255,255,255,0.06);
    color: #BFC6D6;
    border-radius: 16px 16px 3px 16px;
    padding: 0.65rem 1rem;
}
.bubble.assistant-bubble {
    background: transparent;
    color: #7E8A99;
    padding: 0.1rem 0;
}
.bubble.assistant-bubble p  { margin: 0 0 0.5rem; color: #8A95A3; }
.bubble.assistant-bubble p:last-child { margin-bottom: 0; }
.bubble.assistant-bubble strong { color: #C0C8D8; font-weight: 600; }
.bubble.assistant-bubble em      { color: #6E7D8C; font-style: italic; }
.bubble.assistant-bubble ul, .bubble.assistant-bubble ol {
    margin: 0.35rem 0 0.35rem 1.15rem; padding: 0;
}
.bubble.assistant-bubble li { margin-bottom: 4px; color: #8A95A3; }
.bubble.assistant-bubble h1, .bubble.assistant-bubble h2, .bubble.assistant-bubble h3 {
    color: #C0C8D8; font-weight: 600; margin: 0.8rem 0 0.35rem;
}
.bubble.assistant-bubble h1 { font-size: 17px; }
.bubble.assistant-bubble h2 { font-size: 15px; }
.bubble.assistant-bubble h3 { font-size: 14px; }
.bubble.assistant-bubble code {
    background: #0D0F18;
    border: 1px solid rgba(255,255,255,0.07);
    padding: 2px 6px;
    border-radius: 5px;
    font-family: "Fira Code", "JetBrains Mono", monospace;
    font-size: 12.5px;
    color: #7EB8D4;
}
.bubble.assistant-bubble pre {
    background: #0A0C14;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    overflow-x: auto;
    margin: 0.75rem 0;
}
.bubble.assistant-bubble pre code {
    background: none; border: none; padding: 0;
    color: #9BAFC0; font-size: 12.5px;
}
.bubble.assistant-bubble blockquote {
    border-left: 2px solid rgba(99,102,241,0.3);
    margin: 0.5rem 0;
    padding-left: 0.9rem;
    color: #6E7D8C;
}
.bubble.assistant-bubble hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 0.75rem 0;
}
.bubble.assistant-bubble table {
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
    margin: 0.5rem 0;
}
.bubble.assistant-bubble th, .bubble.assistant-bubble td {
    border: 1px solid rgba(255,255,255,0.07);
    padding: 6px 10px;
    text-align: left;
}
.bubble.assistant-bubble th { color: #C0C8D8; background: rgba(255,255,255,0.03); }

/* ── Thinking block ── */
.thinking-block {
    background: rgba(139,92,246,0.04);
    border: 1px solid rgba(139,92,246,0.12);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    font-size: 13px;
    color: #7E7D99;
    line-height: 1.7;
}
.thinking-header {
    font-size: 11px;
    font-weight: 600;
    color: #8B5CF6;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Upload area ── */
.upload-zone {
    border: 1px dashed rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    color: #4A5568;
    font-size: 13px;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.upload-zone:hover {
    border-color: rgba(99,102,241,0.3);
}

/* ── Input ── */
.stChatInputContainer {
    background: #0C0E17 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 0 1px rgba(99,102,241,0.04) !important;
    transition: border-color 0.2s !important;
}
.stChatInputContainer:focus-within {
    border-color: rgba(99,102,241,0.2) !important;
}
.stChatInputContainer textarea {
    color: #C8CEDB !important;
    font-size: 14px !important;
    background: transparent !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    color: #4A5568 !important;
    font-size: 11px !important;
    border-radius: 8px !important;
    padding: 4px 14px !important;
    letter-spacing: 0.3px;
    transition: all 0.2s !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: rgba(99,102,241,0.25) !important;
    color: #A0AEC0 !important;
    background: rgba(99,102,241,0.04) !important;
}

/* ── Sidebar mode buttons ── */
.mode-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 4px;
    border: 1px solid transparent;
    text-decoration: none;
}
.mode-btn:hover {
    background: rgba(255,255,255,0.03);
}
.mode-btn.active {
    background: rgba(99,102,241,0.06);
    border-color: rgba(99,102,241,0.15);
}
.mode-btn .mode-icon {
    font-size: 18px;
    width: 32px;
    text-align: center;
}
.mode-btn .mode-label {
    font-size: 13px;
    font-weight: 500;
    color: #C0C8D8;
}
.mode-btn .mode-desc {
    font-size: 10px;
    color: #4A5568;
    margin-top: 1px;
}

/* ── Image display ── */
.gen-image-container {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06);
    margin: 0.75rem 0;
}
.gen-image-container img {
    width: 100%;
    display: block;
}

/* ── Audio player ── */
.stAudio > audio {
    border-radius: 8px !important;
}

/* ── Expander tweaks ── */
.streamlit-expanderHeader {
    font-size: 13px !important;
    color: #8B5CF6 !important;
    font-weight: 600 !important;
    background: rgba(139,92,246,0.04) !important;
    border-radius: 8px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 1px dashed rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"] label {
    color: #606880 !important;
    font-size: 13px !important;
}

/* ── Radio buttons ── */
.stRadio > div {
    gap: 0.5rem !important;
}
.stRadio label {
    color: #8A95A3 !important;
    font-size: 13px !important;
}

/* ── Divider ── */
.msg-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.03);
    margin: 0.25rem 0 1.75rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.12); }

/* ── Spinner ── */
.stSpinner > div { border-color: #818CF8 transparent transparent transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────

if not API_KEY:
    st.error("🔑 **NVIDIA API key not found.** Set `NVIDIA_API_KEY` in your `.env` file.")
    st.stop()

# ── OpenAI client ─────────────────────────────────────────────────────────────

client = OpenAI(base_url=NIM_BASE, api_key=API_KEY)

# ── Session state ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Aether, an elite AI intelligence engine powered by NVIDIA. "
    "Be concise and precise. Use markdown for structure: bold key terms, "
    "use bullet points for lists, and fenced code blocks for code. "
    "Never pad responses with filler phrases."
)

if "mode" not in st.session_state:
    st.session_state.mode = "text"

# Separate message histories per mode
for mode_key in ["text", "image", "audio", "video", "reasoning"]:
    state_key = f"messages_{mode_key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

if "generated_images" not in st.session_state:
    st.session_state.generated_images = []


def get_messages():
    """Get message list for the current mode."""
    return st.session_state[f"messages_{st.session_state.mode}"]


def add_message(role, content, **extra):
    """Add a message to the current mode's history."""
    msg = {"role": role, "content": content, **extra}
    st.session_state[f"messages_{st.session_state.mode}"].append(msg)
    return msg


def clear_messages():
    """Clear messages for the current mode."""
    st.session_state[f"messages_{st.session_state.mode}"] = []


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1.5rem;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="font-size:18px;">✨</span>
            <span style="font-size:15px; font-weight:700; color:#E0E4F0; letter-spacing:-0.3px;">Aether AI</span>
        </div>
        <span style="font-size:10px; color:#4A5568; letter-spacing:0.5px; text-transform:uppercase;">Multimodal Assistant</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style="font-size:10px; font-weight:600; color:#4A5568;
        letter-spacing:1px; text-transform:uppercase; margin-bottom:8px; padding-left:4px;">
        Mode</div>""", unsafe_allow_html=True)

    for label, info in MODES.items():
        key = info["key"]
        is_active = st.session_state.mode == key
        if st.button(
            label,
            key=f"mode_{key}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.mode = key
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Clear chat button
    if get_messages():
        if st.button("🗑️ Clear Chat", key="clear_chat", use_container_width=True):
            clear_messages()
            st.rerun()

    st.markdown("""
    <div style="position:fixed; bottom:1rem; padding:0 1rem;">
        <div style="font-size:10px; color:#2D3748; line-height:1.6;">
            Powered by NVIDIA NIM<br>
            Text · Image · Audio · Video · Reasoning
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

mode = st.session_state.mode
mode_colors = {
    "text": "#818CF8", "image": "#EC4899", "audio": "#10B981",
    "video": "#F59E0B", "reasoning": "#8B5CF6",
}
mode_icons = {
    "text": "💬", "image": "🖼️", "audio": "🎤",
    "video": "🎬", "reasoning": "🧠",
}
mode_labels = {
    "text": "Text", "image": "Image", "audio": "Audio",
    "video": "Video", "reasoning": "Reasoning",
}

st.markdown(f"""
<div class="aether-header">
    <div class="aether-brand">
        <div class="aether-logo">✨</div>
        <div class="aether-title">Aether</div>
    </div>
    <div class="aether-badge">Online</div>
</div>
<div class="mode-badge {mode}">
    {mode_icons[mode]} {mode_labels[mode]} Mode
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# RENDERING HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def render_user_message(content):
    """Render a user chat bubble."""
    safe = (content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
    safe = re.sub(r'\*(.+?)\*', r'<em>\1</em>', safe)
    safe = re.sub(r'`(.+?)`', r'<code>\1</code>', safe)
    safe = safe.replace("\n", "<br>")
    st.markdown(f"""
    <div class="chat-row user-row">
        <div class="bubble user-bubble">{safe}</div>
        <div class="avatar user">U</div>
    </div>""", unsafe_allow_html=True)


def render_assistant_message(content):
    """Render an assistant chat bubble with markdown."""
    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(content, unsafe_allow_html=False)


def render_thinking(thinking_text):
    """Render a reasoning thinking block."""
    with st.expander("🧠 Reasoning Process", expanded=False):
        st.markdown(f"""<div class="thinking-block">
            <div class="thinking-header">⚡ Chain of Thought</div>
            {thinking_text}
        </div>""", unsafe_allow_html=True)


def render_image_in_chat(image_b64, caption="Generated Image"):
    """Render a base64 image inline in chat."""
    st.markdown(f"""<div class="gen-image-container">
        <img src="data:image/png;base64,{image_b64}" alt="{caption}" />
    </div>""", unsafe_allow_html=True)


def render_message(msg):
    """Render any message from history."""
    role = msg["role"]
    content = msg["content"]

    if role == "user":
        # Show image thumbnail if present
        if msg.get("image_b64"):
            render_user_message(content)
            st.image(
                base64.b64decode(msg["image_b64"]),
                caption="Uploaded image",
                use_container_width=True,
            )
        elif msg.get("video_frames"):
            render_user_message(content)
            cols = st.columns(min(len(msg["video_frames"]), 3))
            for i, frame_b64 in enumerate(msg["video_frames"][:3]):
                with cols[i]:
                    st.image(base64.b64decode(frame_b64), caption=f"Frame {i+1}", use_container_width=True)
        else:
            render_user_message(content)

    elif role == "assistant":
        if msg.get("thinking"):
            render_thinking(msg["thinking"])
        if msg.get("gen_image_b64"):
            col1, col2 = st.columns([0.04, 0.96])
            with col1:
                st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(content, unsafe_allow_html=False)
                render_image_in_chat(msg["gen_image_b64"])
        elif msg.get("audio_bytes"):
            render_assistant_message(content)
            st.audio(msg["audio_bytes"], format="audio/mp3")
        else:
            render_assistant_message(content)


# ══════════════════════════════════════════════════════════════════════════════
# STREAMING
# ══════════════════════════════════════════════════════════════════════════════

def stream_text(messages, model=None):
    """Stream a text response from the NIM API and return the full text."""
    if model is None:
        model = MODELS["text"]

    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
    with col2:
        placeholder = st.empty()
        accumulated = ""
        with client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            max_tokens=4096,
            temperature=0.7,
            top_p=0.9,
        ) as stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    accumulated += chunk.choices[0].delta.content
                    placeholder.markdown(accumulated + "▋")
        placeholder.markdown(accumulated)
    return accumulated


def stream_reasoning(messages):
    """Stream a reasoning response, parsing <think> tags."""
    model = MODELS["reasoning"]

    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)

    with col2:
        thinking_placeholder = st.empty()
        answer_placeholder = st.empty()
        accumulated = ""
        in_think = False
        thinking_text = ""
        answer_text = ""

        with client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            max_tokens=8192,
            temperature=0.6,
        ) as stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    accumulated += delta

                    # Parse <think> blocks
                    if "<think>" in accumulated and not in_think:
                        in_think = True
                    if "</think>" in accumulated and in_think:
                        in_think = False

                    # Split thinking vs answer
                    think_match = re.search(r"<think>(.*?)</think>", accumulated, re.DOTALL)
                    if think_match:
                        thinking_text = think_match.group(1).strip()
                        answer_text = accumulated[think_match.end():].strip()
                    elif in_think:
                        start = accumulated.find("<think>") + len("<think>")
                        thinking_text = accumulated[start:].strip()
                        answer_text = ""
                    else:
                        answer_text = accumulated.strip()

                    # Update displays
                    if thinking_text:
                        with thinking_placeholder.container():
                            with st.expander("🧠 Reasoning Process", expanded=in_think):
                                st.markdown(thinking_text + ("▋" if in_think else ""))
                    if answer_text:
                        answer_placeholder.markdown(answer_text + ("▋" if not in_think or answer_text else ""))

        # Final render
        if thinking_text:
            with thinking_placeholder.container():
                with st.expander("🧠 Reasoning Process", expanded=False):
                    st.markdown(thinking_text)
        if answer_text:
            answer_placeholder.markdown(answer_text)

    return thinking_text, answer_text


# ══════════════════════════════════════════════════════════════════════════════
# IMAGE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def analyze_image(image_b64, prompt, mime_type="image/jpeg"):
    """Send an image to the vision model for analysis."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                },
            ],
        },
    ]

    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
    with col2:
        placeholder = st.empty()
        accumulated = ""
        with client.chat.completions.create(
            model=MODELS["vision"],
            messages=messages,
            stream=True,
            max_tokens=2048,
            temperature=0.5,
        ) as stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    accumulated += chunk.choices[0].delta.content
                    placeholder.markdown(accumulated + "▋")
        placeholder.markdown(accumulated)
    return accumulated


def generate_image(prompt):
    """Generate an image using Pollinations AI (free, reliable fallback for retired SDXL)."""
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&private=true"
    response = http_requests.get(url, timeout=120)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def extract_frames(video_bytes, max_frames=MAX_FRAMES):
    """Extract evenly-spaced keyframes from a video."""
    import cv2
    import numpy as np

    # Write video bytes to a temp file
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames <= 0:
            cap.release()
            return []

        # Pick evenly spaced frame indices
        indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)
        frames_b64 = []

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                # Resize to max 512px on longest side for API limits
                h, w = frame.shape[:2]
                scale = 512 / max(h, w)
                if scale < 1:
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frames_b64.append(base64.b64encode(buffer).decode("utf-8"))

        cap.release()
        return frames_b64
    finally:
        os.unlink(tmp_path)


def analyze_video_frames(frames_b64, prompt):
    """Send multiple frames to the vision model for video understanding."""
    # Build content with all frames
    content = [{"type": "text", "text": f"{prompt}\n\nThese are frames extracted from a video at regular intervals. Analyze the video content based on these frames."}]
    for i, frame in enumerate(frames_b64):
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{frame}"},
        })

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + " You are analyzing a video through its keyframes. Describe what happens across the frames as a coherent video narrative."},
        {"role": "user", "content": content},
    ]

    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
    with col2:
        placeholder = st.empty()
        accumulated = ""
        with client.chat.completions.create(
            model=MODELS["vision"],
            messages=messages,
            stream=True,
            max_tokens=2048,
            temperature=0.5,
        ) as stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    accumulated += chunk.choices[0].delta.content
                    placeholder.markdown(accumulated + "▋")
        placeholder.markdown(accumulated)
    return accumulated


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def text_to_speech(text):
    """Convert text to speech using gTTS and return audio bytes."""
    from gtts import gTTS
    tts = gTTS(text=text, lang="en", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════════════════════
# RENDER HISTORY
# ══════════════════════════════════════════════════════════════════════════════

messages = get_messages()
for msg in messages:
    render_message(msg)


# ══════════════════════════════════════════════════════════════════════════════
# MODE: TEXT
# ══════════════════════════════════════════════════════════════════════════════

if mode == "text":
    if user_input := st.chat_input("Message Aether…"):
        add_message("user", user_input)
        render_user_message(user_input)

        try:
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in get_messages():
                if m["role"] in ("user", "assistant"):
                    api_messages.append({"role": m["role"], "content": m["content"]})

            ai_text = stream_text(api_messages)
            add_message("assistant", ai_text)
        except Exception as exc:
            err = f"**Error:** {exc}"
            render_assistant_message(err)
            add_message("assistant", err)


# ══════════════════════════════════════════════════════════════════════════════
# MODE: IMAGE
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "image":
    img_mode = st.radio(
        "Choose action",
        ["🔍 Analyze Image", "🎨 Generate Image"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if img_mode == "🔍 Analyze Image":
        uploaded = st.file_uploader(
            "Upload an image to analyze",
            type=["jpg", "jpeg", "png", "webp"],
            key="img_upload",
        )

        if uploaded:
            # Show preview
            st.image(uploaded, caption="Uploaded Image", use_container_width=True)

            prompt = st.chat_input("Ask about this image…")
            if prompt:
                img_bytes = uploaded.getvalue()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                # Detect MIME
                mime = "image/jpeg"
                if uploaded.name.lower().endswith(".png"):
                    mime = "image/png"
                elif uploaded.name.lower().endswith(".webp"):
                    mime = "image/webp"

                add_message("user", prompt, image_b64=img_b64)
                render_user_message(prompt)

                try:
                    ai_text = analyze_image(img_b64, prompt, mime)
                    add_message("assistant", ai_text)
                except Exception as exc:
                    err = f"**Error:** {exc}"
                    render_assistant_message(err)
                    add_message("assistant", err)
        else:
            st.markdown("""<div class="upload-zone">
                📷 Upload an image (JPG, PNG, WebP) and ask Aether to analyze it
            </div>""", unsafe_allow_html=True)

    else:  # Generate Image
        prompt = st.chat_input("Describe the image you want to generate…")
        if prompt:
            add_message("user", f"🎨 Generate: {prompt}")
            render_user_message(f"🎨 Generate: {prompt}")

            try:
                with st.spinner("🎨 Generating image with Stable Diffusion XL…"):
                    img_b64 = generate_image(prompt)

                response_text = f"Here's your generated image for: **{prompt}**"
                col1, col2 = st.columns([0.04, 0.96])
                with col1:
                    st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(response_text)
                    render_image_in_chat(img_b64)

                add_message("assistant", response_text, gen_image_b64=img_b64)

            except Exception as exc:
                err = f"**Error generating image:** {exc}"
                render_assistant_message(err)
                add_message("assistant", err)


# ══════════════════════════════════════════════════════════════════════════════
# MODE: AUDIO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "audio":
    try:
        from audio_recorder_streamlit import audio_recorder
    except ImportError:
        st.error("📦 `audio-recorder-streamlit` not installed. Run: `pip install audio-recorder-streamlit`")
        st.stop()

    st.markdown("""<div style="font-size:12px; color:#4A5568; margin-bottom:1rem;">
        🎙️ Click the microphone to record, then Aether will respond with voice.
    </div>""", unsafe_allow_html=True)

    audio_bytes = audio_recorder(
        text="",
        recording_color="#818CF8",
        neutral_color="#2D3748",
        icon_size="2x",
        pause_threshold=2.0,
        key="audio_recorder",
    )

    # Also allow text input as fallback
    text_fallback = st.chat_input("Or type your message…")

    user_text = None

    if audio_bytes:
        # Transcribe using Whisper-compatible endpoint
        st.audio(audio_bytes, format="audio/wav")

        with st.spinner("🎤 Transcribing audio…"):
            try:
                # Try NVIDIA's whisper endpoint
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "recording.wav"
                transcription = client.audio.transcriptions.create(
                    model="nvidia/parakeet-ctc-1.1b-asr",
                    file=audio_file,
                    response_format="text",
                )
                user_text = transcription if isinstance(transcription, str) else transcription.text
            except Exception:
                # Fallback: Use speech_recognition if available
                try:
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    audio_io = io.BytesIO(audio_bytes)
                    with sr.AudioFile(audio_io) as source:
                        audio_data = recognizer.record(source)
                    user_text = recognizer.recognize_google(audio_data)
                except Exception:
                    user_text = None
                    st.warning("⚠️ Could not transcribe audio. Please try typing instead.")

    if text_fallback:
        user_text = text_fallback

    if user_text:
        add_message("user", f"🎤 {user_text}")
        render_user_message(f"🎤 {user_text}")

        try:
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT + " Keep responses concise (2-3 sentences) since they will be read aloud."}]
            for m in get_messages():
                if m["role"] in ("user", "assistant"):
                    api_messages.append({"role": m["role"], "content": m["content"]})

            ai_text = stream_text(api_messages)

            # Generate TTS
            with st.spinner("🔊 Generating speech…"):
                try:
                    audio_response = text_to_speech(ai_text)
                    st.audio(audio_response, format="audio/mp3", autoplay=True)
                    add_message("assistant", ai_text, audio_bytes=audio_response)
                except Exception:
                    add_message("assistant", ai_text)

        except Exception as exc:
            err = f"**Error:** {exc}"
            render_assistant_message(err)
            add_message("assistant", err)


# ══════════════════════════════════════════════════════════════════════════════
# MODE: VIDEO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "video":
    uploaded = st.file_uploader(
        "Upload a video to analyze",
        type=["mp4", "mov", "avi", "mkv"],
        key="vid_upload",
    )

    if uploaded:
        file_size_mb = len(uploaded.getvalue()) / (1024 * 1024)
        if file_size_mb > MAX_VIDEO_MB:
            st.error(f"⚠️ Video too large ({file_size_mb:.1f} MB). Maximum is {MAX_VIDEO_MB} MB.")
        else:
            st.video(uploaded)
            st.markdown(f"""<div style="font-size:11px; color:#4A5568; margin:0.5rem 0;">
                📁 {uploaded.name} · {file_size_mb:.1f} MB
            </div>""", unsafe_allow_html=True)

            prompt = st.chat_input("Ask about this video…")
            if prompt:
                add_message("user", prompt)
                render_user_message(prompt)

                with st.spinner(f"🎬 Extracting {MAX_FRAMES} keyframes…"):
                    try:
                        frames = extract_frames(uploaded.getvalue(), MAX_FRAMES)
                    except Exception as exc:
                        st.error(f"Error extracting frames: {exc}")
                        frames = []

                if frames:
                    # Show extracted frames
                    with st.expander(f"📸 Extracted {len(frames)} keyframes", expanded=False):
                        cols = st.columns(min(len(frames), 3))
                        for i, frame_b64 in enumerate(frames):
                            with cols[i % 3]:
                                st.image(base64.b64decode(frame_b64), caption=f"Frame {i+1}", use_container_width=True)

                    # Update user message with frames
                    get_messages()[-1]["video_frames"] = frames[:3]

                    try:
                        ai_text = analyze_video_frames(frames, prompt)
                        add_message("assistant", ai_text)
                    except Exception as exc:
                        err = f"**Error analyzing video:** {exc}"
                        render_assistant_message(err)
                        add_message("assistant", err)
                else:
                    st.error("Could not extract frames from the video.")
    else:
        st.markdown("""<div class="upload-zone">
            🎬 Upload a video (MP4, MOV, AVI, MKV — max 25 MB) and ask Aether to analyze it
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MODE: REASONING
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "reasoning":
    st.markdown("""<div style="font-size:12px; color:#4A5568; margin-bottom:1rem; line-height:1.6;">
        🧠 Reasoning mode uses DeepSeek-R1 for deep chain-of-thought analysis.<br>
        You'll see the AI's thinking process before the final answer.
    </div>""", unsafe_allow_html=True)

    if user_input := st.chat_input("Ask a complex question…"):
        add_message("user", user_input)
        render_user_message(user_input)

        try:
            api_messages = [
                {"role": "system", "content": "You are Aether, an elite reasoning AI. Think deeply and show your work. Use <think> tags to enclose your reasoning process, then provide a clear final answer."},
            ]
            for m in get_messages():
                if m["role"] in ("user", "assistant"):
                    api_messages.append({"role": m["role"], "content": m["content"]})

            thinking, answer = stream_reasoning(api_messages)
            add_message("assistant", answer, thinking=thinking)

        except Exception as exc:
            err = f"**Error:** {exc}"
            render_assistant_message(err)
            add_message("assistant", err)
