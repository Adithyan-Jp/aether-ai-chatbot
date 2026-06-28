import os
import re
import base64
import io
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Force load latest environment modifications
load_dotenv(override=True)

# Fetch API Key from OS Environment or Streamlit Secrets
API_KEY = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY")

st.set_page_config(
    page_title="Aether AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",  # Opened by default to check debugging setup
)

# ── Custom Theme CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base App Aesthetics ── */
.stApp, html, body, [data-testid="stAppViewContainer"] {
    background: #07080D !important;
}
.main .block-container {
    max-width: 720px !important;
    padding-top: 0 !important;
    padding-bottom: 8rem !important;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── App Sticky Header ── */
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

/* ── Chat Layout & Bubbles ── */
.chat-row {
    display: flex;
    width: 100%;
    margin-bottom: 1.5rem;
    gap: 10px;
    align-items: flex-start;
}
.chat-row.user-row { justify-content: flex-end; }
.chat-row.assistant-row { justify-content: flex-start; }

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
    white-space: pre-wrap;
}
.bubble.assistant-bubble {
    background: transparent;
    color: #7E8A99;
    padding: 0.1rem 0;
    width: 100%;
}
.bubble.assistant-bubble p { margin: 0 0 0.5rem; color: #8A95A3; }
.bubble.assistant-bubble strong { color: #C0C8D8; font-weight: 600; }
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

/* ── Sticky Chat Input Container ── */
.stChatInputContainer {
    background: #0C0E17 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 0 1px rgba(99,102,241,0.04) !important;
}
.stChatInputContainer textarea {
    color: #C8CEDB !important;
    font-size: 14px !important;
}

/* ── Sidebar Custom Look ── */
[data-testid="stSidebar"] {
    background: #0A0C14 !important;
    border-right: 1px solid rgba(255,255,255,0.04);
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Debugging Tools ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Engine Diagnostics")
    if not API_KEY:
        st.error("❌ Key Status: Missing Environment Values")
        st.info("💡 To fix this, create an ecosystem file named `.env` in this directory containing:\n`NVIDIA_API_KEY=nvapi-yourKey`")
    else:
        # Diagnostic structural assertion to identify OpenRouter leakage paths
        if API_KEY.startswith("sk-or-"):
            st.error("⚠️ Token Issue: Found OpenRouter Token (`sk-or-`) in NVIDIA environment context. Authentications will fail.")
        elif not API_KEY.startswith("nvapi-"):
            st.warning("⚠️ Formatting Warning: API key token does not match standard `nvapi-` header configuration format.")
        else:
            st.success("🔒 System Context: Key Value Found")
            
        # Display safe snippet to prove exactly what string Streamlit is feeding out
        masked_key = f"{API_KEY[:9]}...{API_KEY[-4:]}" if len(API_KEY) > 12 else "Malformed"
        st.text_input("Active Runtime Key Vector:", value=masked_key, disabled=True)

if not API_KEY:
    st.error("🔑 NVIDIA NIM Authentication context missing. Set 'NVIDIA_API_KEY' environment value to unlock runtime execution steps.")
    st.stop()

# ── Model Registry for Production NVIDIA Gateways ─────────────────────────────
MODELS = {
    "text": {
        "id": "nvidia/nemotron-3-ultra-550b-a55b",
        "name": "Nemotron 3 Ultra 550B",
        "desc": "General-purpose MoE chat engine",
    },
    "image": {
        "id": "nvidia/nemotron-parse",
        "name": "Nemotron Parse Vision",
        "desc": "Multimodal visual reasoning engine",
    },
    "reasoning": {
        "id": "nvidia/nemotron-3-ultra-550b-a55b",
        "name": "Nemotron 3 Ultra MoE",
        "desc": "Deep planning, instruction scaling & tasks",
    },
    "coding": {
        "id": "nvidia/nemotron-3-ultra-550b-a55b",
        "name": "Nemotron 3 Ultra 550B",
        "desc": "Agentic codebase engineering, synthesis, & review",
    },
}

# ── Global Architectural Instructions ─────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Aether, an elite AI intelligence engine powered by native NVIDIA NIM architecture. "
    "Be concise and precise. Always use markdown for clean structural rendering: bold critical items, "
    "leverage cleanly organized tables or lists, and use fenced code blocks for syntax outputs."
)

CODING_SYSTEM_PROMPT = (
    "You are Aether Code, a specialized programming pipeline optimized for software generation. "
    "Write structural, production-ready code with comprehensive type hints and descriptive docstrings. "
    "Provide a brief engineering rationale before code blocks. Adhere strictly to clean architecture principles."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "mode" not in st.session_state:
    st.session_state.mode = "text"
if "uploaded_media" not in st.session_state:
    st.session_state.uploaded_media = None

# ── Functional Architecture Subsystems ───────────────────────────────────────
def file_to_base64(file_bytes: bytes, mime: str) -> str:
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def build_content(text: str, media: dict | None) -> list | str:
    if not media:
        return text
    content = []
    if text:
        content.append({"type": "text", "text": text})
    if media["type"] == "image":
        content.append({"type": "image_url", "image_url": {"url": media["data"]}})
    return content

def get_model_for_mode(mode: str) -> str:
    return MODELS[mode]["id"]

def get_system_prompt(mode: str) -> str:
    return CODING_SYSTEM_PROMPT if mode == "coding" else SYSTEM_PROMPT

def reset_media():
    st.session_state.uploaded_media = None

# ── Rendering Interface Elements ─────────────────────────────────────────────
st.markdown("""
<div class="aether-header">
    <div class="aether-brand">
        <div class="aether-logo">✨</div>
        <div class="aether-title">Aether Engine</div>
    </div>
    <div class="aether-badge">NVIDIA NIM</div>
</div>
""", unsafe_allow_html=True)

# ── Context Mode Switcher ──
modes = ["text", "image", "reasoning", "coding"]
mode_labels = {
    "text": "💬 Text",
    "image": "🖼️ Vision",
    "reasoning": "🧠 Reasoning",
    "coding": "💻 Coding",
}

cols = st.columns(len(modes))
for i, m in enumerate(modes):
    active = (st.session_state.mode == m)
    btn_type = "primary" if active else "secondary"
    if cols[i].button(mode_labels[m], key=f"mode_{m}", use_container_width=True, type=btn_type):
        st.session_state.mode = m
        st.session_state.messages[0] = {"role": "system", "content": get_system_prompt(m)}
        reset_media()
        st.rerun()

# ── Multimodal Media Pipeline Upload targets ──
mode = st.session_state.mode
uploaded = None

if mode == "image":
    uploaded = st.file_uploader(
        "Ingest Image Blueprint (PNG, JPG, WEBP)",
        type=["png", "jpg", "jpeg", "webp"],
        key="img_uploader",
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

# Render attached file preview frames
media = st.session_state.uploaded_media
if media:
    if media["type"] == "image":
        st.markdown(f'<img src="{media["data"]}" class="upload-preview" style="max-height:200px; border-radius: 8px; margin-bottom: 1rem;">', unsafe_allow_html=True)
    if st.button("✕ Remove Attachment", key="remove_media"):
        reset_media()
        st.rerun()

# ── Message Parsing & Stream Blocks ──────────────────────────────────────────
def render_message(role: str, content):
    if role == "user":
        if isinstance(content, list):
            text_parts = [c["text"] for c in content if c.get("type") == "text"]
            display_text = " ".join(text_parts) if text_parts else "[Image Object Attached]"
        else:
            display_text = content

        safe = display_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f"""
        <div class="chat-row user-row">
            <div class="bubble user-bubble">{safe}</div>
        </div>""", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            st.markdown(content)
            st.markdown('</div>', unsafe_allow_html=True)

def stream_response(messages: list, model_id: str) -> str:
    """Orchestrates stream processing loops with the native NVIDIA endpoint gateways."""
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=API_KEY
    )

    col1, col2 = st.columns([0.05, 0.95])
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

# ── Structural History Management Loop ───────────────────────────────────────
non_system = [m for m in st.session_state.messages if m["role"] != "system"]

if non_system:
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if st.button("✕ Reset Architecture", key="clear_chat", use_container_width=True):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt(mode)}]
            reset_media()
            st.rerun()

    for msg in non_system:
        render_message(msg["role"], msg["content"])

# ── Conversational Capture Layer ──────────────────────────────────────────────
placeholder_text = {
    "text": "Query Nemotron 3 Ultra...",
    "image": "Deconstruct or analyze this input canvas...",
    "reasoning": "Submit complex computational, code-logic, or architectural algorithms...",
    "coding": "Request optimizations, structural modules, or debugging sequences...",
}

if user_input := st.chat_input(placeholder_text[mode]):
    model_id = get_model_for_mode(mode)
    content = build_content(user_input, media)

    st.session_state.messages.append({"role": "user", "content": content})
    render_message("user", content)

    try:
        ai_text = stream_response(st.session_state.messages, model_id)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
    except Exception as exc:
        render_message("assistant", f"⚡ **NVIDIA NIM Gateway Exception Alert:** `{exc}`")
