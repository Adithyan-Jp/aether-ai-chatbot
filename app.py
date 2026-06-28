import os
import re
import base64
import io
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# Update your .env or Streamlit secrets with your OpenRouter API key (starts with sk-or-)
API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

st.set_page_config(
    page_title="Aether AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Base ── */
.stApp, html, body, [data-testid="stAppViewContainer"] {
    background: #07080D !important;
}
.main .block-container {
    max-width: 720px !important;
    padding-top: 0 !important;
    padding-bottom: 8rem !important;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Header ── */
.aether-header {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0;
    margin-bottom: 2rem;
    background: #07080D;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.aether-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.aether-logo {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}
.aether-title {
    font-size: 15px;
    font-weight: 600;
    color: #D0D4E0;
    letter-spacing: -0.2px;
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

/* ── Mode selector ── */
.mode-pill {
    display: inline-flex;
    gap: 6px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 1.5rem;
}
.mode-btn {
    font-size: 12px;
    font-weight: 500;
    color: #606880;
    background: transparent;
    border: none;
    border-radius: 7px;
    padding: 5px 12px;
    cursor: pointer;
    transition: all 0.15s;
}
.mode-btn:hover { color: #A0AEC0; }
.mode-btn.active {
    background: rgba(99,102,241,0.12);
    color: #818CF8;
    border: 1px solid rgba(99,102,241,0.18);
}

/* ── Upload area ── */
.upload-area {
    background: rgba(255,255,255,0.02);
    border: 1px dashed rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.upload-area p {
    color: #4A5568;
    font-size: 12px;
    margin: 0;
}
.upload-preview {
    border-radius: 10px;
    max-width: 100%;
    margin-top: 0.5rem;
}

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
    width: 26px;
    height: 26px;
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
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.2);
    color: #818CF8;
}
.avatar.user {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: #606880;
}

/* ── Bubbles ── */
.bubble {
    max-width: 80%;
    font-size: 14.5px;
    line-height: 1.75;
    word-wrap: break-word;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.bubble.user-bubble {
    background: #111420;
    border: 1px solid rgba(255,255,255,0.055);
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
}

/* ── Clear button ── */
div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    color: #4A5568 !important;
    font-size: 11px !important;
    border-radius: 8px !important;
    padding: 3px 12px !important;
    letter-spacing: 0.3px;
    transition: all 0.15s !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: rgba(255,255,255,0.09) !important;
    color: #A0AEC0 !important;
}

/* ── Divider ── */
.msg-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.03);
    margin: 0.25rem 0 1.75rem;
}

/* ── Sidebar tweaks ── */
[data-testid="stSidebar"] {
    background: #0A0C14 !important;
}
[data-testid="stSidebar"] .stMarkdown { color: #8A95A3; }
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────

if not API_KEY:
    st.error("🔑 OpenRouter API key not found. Check your environment variables.")
    st.stop()

# ── Model registry ───────────────────────────────────────────────────────────
# OpenRouter model IDs (from build.nvidia.com via OpenRouter)
# Format: developer/model-name (as shown on OpenRouter model pages)

MODELS = {
    "text": {
        "id": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "name": "Nemotron 3 Ultra 550B",
        "desc": "General-purpose text chat & code",
    },
    "reasoning": {
        "id": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "name": "Nemotron 3 Ultra 550B",
        "desc": "Chain-of-thought reasoning & math",
    },
    "image": {
        "id": "google/gemini-2.0-flash-001",
        "name": "Gemini 2.0 Flash",
        "desc": "Vision-language: images + text",
    },
    "video": {
        "id": "google/gemini-2.0-flash-001",
        "name": "Gemini 2.0 Flash",
        "desc": "Video + image + audio + text understanding",
    },
    "audio": {
        "id": "google/gemini-2.0-flash-001",
        "name": "Gemini 2.0 Flash",
        "desc": "Audio + speech + text understanding",
    },
    "coding": {
        "id": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "name": "Nemotron 3 Ultra 550B",
        "desc": "Fast coding, functions, bug fixes",
    },
}

# ── Session state ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Aether, an elite AI intelligence engine powered by NVIDIA Nemotron 3 Ultra via OpenRouter. "
    "Be concise and precise. Use markdown for structure: bold key terms, "
    "use bullet points for lists, and fenced code blocks for code. "
    "Never pad responses with filler phrases."
)

CODING_SYSTEM_PROMPT = (
    "You are Aether Code, an expert programming assistant powered by NVIDIA Nemotron 3 Ultra via OpenRouter. "
    "Write clean, well-documented code. Always include type hints and docstrings. "
    "Explain your reasoning briefly before showing code. "
    "Use best practices and modern language features."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "mode" not in st.session_state:
    st.session_state.mode = "text"
if "uploaded_media" not in st.session_state:
    st.session_state.uploaded_media = None   # dict: {type, mime, data, ext}

# ── Helpers ───────────────────────────────────────────────────────────────────

def file_to_base64(file_bytes: bytes, mime: str) -> str:
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def build_content(text: str, media: dict | None) -> list | str:
    """Build OpenAI-compatible content array for multimodal messages."""
    if not media:
        return text

    content = []
    if text:
        content.append({"type": "text", "text": text})

    mtype = media["type"]
    mime = media["mime"]
    b64_url = media["data"]

    if mtype == "image":
        content.append({"type": "image_url", "image_url": {"url": b64_url}})
    elif mtype == "audio":
        # OpenRouter accepts audio via input_audio content type
        content.append({"type": "input_audio", "input_audio": {"data": b64_url.split(",")[1], "format": media["ext"]}})
    elif mtype == "video":
        # OpenRouter accepts video via video_url content type
        content.append({"type": "video_url", "video_url": {"url": b64_url}})
    return content


def get_model_for_mode(mode: str) -> str:
    return MODELS[mode]["id"]


def get_system_prompt(mode: str) -> str:
    if mode == "coding":
        return CODING_SYSTEM_PROMPT
    return SYSTEM_PROMPT


def reset_media():
    st.session_state.uploaded_media = None

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="aether-header">
    <div class="aether-brand">
        <div class="aether-logo">✨</div>
        <div class="aether-title">Aether</div>
    </div>
    <div class="aether-badge">Online</div>
</div>
""", unsafe_allow_html=True)

# ── Mode selector ─────────────────────────────────────────────────────────────

modes = ["text", "image", "audio", "video", "reasoning", "coding"]
mode_labels = {
    "text": "💬 Text",
    "image": "🖼️ Image",
    "audio": "🎙️ Audio",
    "video": "🎬 Video",
    "reasoning": "🧠 Reasoning",
    "coding": "💻 Coding",
}

cols = st.columns(len(modes))
for i, m in enumerate(modes):
    active = st.session_state.mode == m
    cls = "mode-btn active" if active else "mode-btn"
    if cols[i].button(mode_labels[m], key=f"mode_{m}", use_container_width=True):
        st.session_state.mode = m
        # Update system prompt when switching modes
        st.session_state.messages[0] = {
            "role": "system",
            "content": get_system_prompt(m)
        }
        reset_media()
        st.rerun()

# ── File uploaders per mode ─────────────────────────────────────────────────

mode = st.session_state.mode
uploaded = None

if mode == "image":
    uploaded = st.file_uploader(
        "Upload an image (PNG, JPG, WEBP)",
        type=["png", "jpg", "jpeg", "webp"],
        key="img_uploader",
    )
elif mode == "audio":
    uploaded = st.file_uploader(
        "Upload audio (MP3, WAV, OGG, M4A)",
        type=["mp3", "wav", "ogg", "m4a", "flac"],
        key="audio_uploader",
    )
elif mode == "video":
    uploaded = st.file_uploader(
        "Upload video (MP4, MOV, WEBM, AVI)",
        type=["mp4", "mov", "webm", "avi", "mkv"],
        key="video_uploader",
    )

if uploaded is not None:
    bytes_data = uploaded.read()
    mime = uploaded.type
    ext = uploaded.name.split(".")[-1].lower()
    b64_url = file_to_base64(bytes_data, mime)
    st.session_state.uploaded_media = {
        "type": mode,
        "mime": mime,
        "data": b64_url,
        "ext": ext,
        "name": uploaded.name,
    }

# Show preview of uploaded media
media = st.session_state.uploaded_media
if media:
    if media["type"] == "image":
        st.markdown(f'<img src="{media["data"]}" class="upload-preview" style="max-height:260px;">', unsafe_allow_html=True)
    elif media["type"] == "audio":
        st.audio(media["data"])
    elif media["type"] == "video":
        st.video(media["data"])
    if st.button("✕ Remove attachment", key="remove_media"):
        reset_media()
        st.rerun()

# ── Render message ───────────────────────────────────────────────────────────

def render_message(role: str, content):
    if role == "user":
        # Extract text from multimodal content
        if isinstance(content, list):
            text_parts = [c["text"] for c in content if c.get("type") == "text"]
            display_text = " ".join(text_parts) if text_parts else "[multimodal]"
        else:
            display_text = content

        safe = (display_text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        safe = re.sub(r'\*(.+?)\*', r'<em>\1</em>', safe)
        safe = re.sub(r'`(.+?)`', r'<code>\1</code>', safe)
        safe = safe.replace("\\n", "<br>")
        st.markdown(f"""
        <div class="chat-row user-row">
            <div class="bubble user-bubble">{safe}</div>
        </div>""", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([0.04, 0.96])
        with col1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            st.markdown(content, unsafe_allow_html=False)
            st.markdown('</div>', unsafe_allow_html=True)


def stream_response(messages: list, model_id: str) -> str:
    """Stream directly from OpenRouter and return the full text."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
        default_headers={
            "HTTP-Referer": "https://aether-ai.app",
            "X-Title": "Aether AI",
        },
    )

    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)

    with col2:
        stream_placeholder = st.empty()
        accumulated = ""

        with client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=True,
        ) as stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    accumulated += delta
                    stream_placeholder.markdown(accumulated + "▋")

        stream_placeholder.markdown(accumulated)

    return accumulated

# ── History ───────────────────────────────────────────────────────────────────

non_system = [m for m in st.session_state.messages if m["role"] != "system"]

if non_system:
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if st.button("✕  Clear", key="clear_chat"):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt(mode)}]
            reset_media()
            st.rerun()

    for msg in non_system:
        render_message(msg["role"], msg["content"])

# ── Input & inference ─────────────────────────────────────────────────────────

placeholder_text = {
    "text": "Message Aether…",
    "image": "Ask about this image…",
    "audio": "Ask about this audio…",
    "video": "Ask about this video…",
    "reasoning": "Ask a reasoning question…",
    "coding": "Write code, debug, or explain…",
}

if user_input := st.chat_input(placeholder_text[mode]):
    model_id = get_model_for_mode(mode)
    content = build_content(user_input, media)

    st.session_state.messages.append({"role": "user", "content": content})
    render_message("user", content)

    # For non-text modes, inject a brief system hint about the modality
    messages = list(st.session_state.messages)
    if mode in ("image", "audio", "video"):
        # Prepend a temporary context hint (not stored in session)
        hint = f"The user has uploaded a {mode} file. Analyze it carefully."
        messages = [{"role": "system", "content": get_system_prompt(mode) + " " + hint}] + messages[1:]

    try:
        ai_text = stream_response(messages, model_id)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
    except Exception as exc:
        render_message("assistant", f"**Error:** {exc}")
