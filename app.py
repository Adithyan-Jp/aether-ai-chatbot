import os
import re
import base64
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

st.set_page_config(
    page_title="Aether AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Paste handler using st.text_area as bridge ────────────────────────────────

# We use a hidden text_area that JavaScript will populate with pasted image data
# The key insight: st.text_area supports paste natively, and we can intercept it

st.markdown("""
<style>
/* ── Base ── */
.stApp, html, body, [data-testid="stAppViewContainer"] {
    background: #07080D !important;
}
.main .block-container {
    max-width: 720px !important;
    padding-top: 0 !important;
    padding-bottom: 6rem !important;
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

/* ── Image in chat ── */
.chat-img {
    max-width: 280px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    margin-top: 4px;
}

/* ── Image preview above input ── */
.img-preview-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    padding: 0 4px;
}
.img-preview-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 12px;
    color: #818CF8;
}
.img-preview-pill img {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    object-fit: cover;
}

/* ── Input ── */
.stChatInputContainer {
    background: #0C0E17 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px !important;
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
    st.error("🔑 OpenRouter API key not found. Check your environment variables or Streamlit secrets.")
    st.stop()

# ── Model registry ───────────────────────────────────────────────────────────

MODELS = {
    "text": {
        "id": "openrouter/owl-alpha",
        "name": "Owl Alpha",
        "desc": "General-purpose text chat & code",
    },
    "reasoning": {
        "id": "openrouter/owl-alpha",
        "name": "Owl Alpha",
        "desc": "Chain-of-thought reasoning & math",
    },
    "coding": {
        "id": "openrouter/owl-alpha",
        "name": "Owl Alpha",
        "desc": "Fast coding, functions, bug fixes",
    },
    "vision": {
        "id": "google/gemini-2.0-flash-exp:free",
        "name": "Gemini Flash",
        "desc": "Vision & image understanding",
    },
}

# ── Session state ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Aether, an elite AI intelligence engine powered by OpenRouter Owl Alpha. "
    "Be concise and precise. Use markdown for structure: bold key terms, "
    "use bullet points for lists, and fenced code blocks for code. "
    "Never pad responses with filler phrases."
)

CODING_SYSTEM_PROMPT = (
    "You are Aether Code, an expert programming assistant powered by OpenRouter Owl Alpha. "
    "Write clean, well-documented code. Always include type hints and docstrings. "
    "Explain your reasoning briefly before showing code. "
    "Use best practices and modern language features."
)

VISION_SYSTEM_PROMPT = (
    "You are Aether Vision, an AI that can see and understand images. "
    "Describe images accurately and concisely. Answer questions about visual content. "
    "Be precise about details you observe."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "mode" not in st.session_state:
    st.session_state.mode = "text"
if "pending_image" not in st.session_state:
    st.session_state.pending_image = None

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_model_for_mode(mode: str, has_image: bool = False) -> str:
    if has_image:
        return MODELS["vision"]["id"]
    return MODELS[mode]["id"]


def get_system_prompt(mode: str, has_image: bool = False) -> str:
    if has_image:
        return VISION_SYSTEM_PROMPT
    if mode == "coding":
        return CODING_SYSTEM_PROMPT
    return SYSTEM_PROMPT


def encode_image(file_bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")


def build_user_message(text: str, image_b64: str = None, mime_type: str = "image/jpeg") -> dict:
    if image_b64:
        return {
            "role": "user",
            "content": [
                {"type": "text", "text": text or "What do you see in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_b64}"
                    },
                },
            ],
        }
    return {"role": "user", "content": text}


def render_message(role: str, content, image_data: dict = None):
    display_text = content
    if isinstance(content, list):
        text_parts = [item["text"] for item in content if item.get("type") == "text"]
        display_text = " ".join(text_parts) if text_parts else "[Image]"

    if role == "user":
        safe = (str(display_text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        safe = re.sub(r'\*(.+?)\*', r'<em>\1</em>', safe)
        safe = re.sub(r'`(.+?)`', r'<code>\1</code>', safe)
        safe = safe.replace("\n", "<br>")
        
        img_html = ""
        if image_data:
            img_html = f'<img src="data:{image_data["mime"]};base64,{image_data["data"]}" class="chat-img">'
        
        st.markdown(f"""
        <div class="chat-row user-row">
            <div class="bubble user-bubble">
                {safe}
                {img_html}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([0.04, 0.96])
        with col1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            st.markdown(display_text, unsafe_allow_html=False)
            st.markdown('</div>', unsafe_allow_html=True)


def stream_response(messages: list, model_id: str) -> str:
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

modes = ["text", "reasoning", "coding"]
mode_labels = {
    "text": "💬 Text",
    "reasoning": "🧠 Reasoning",
    "coding": "💻 Coding",
}

cols = st.columns(len(modes))
for i, m in enumerate(modes):
    active = st.session_state.mode == m
    if cols[i].button(mode_labels[m], key=f"mode_{m}", use_container_width=True):
        st.session_state.mode = m
        st.session_state.messages[0] = {
            "role": "system",
            "content": get_system_prompt(m)
        }
        st.rerun()

mode = st.session_state.mode

# ── History ───────────────────────────────────────────────────────────────────

non_system = [m for m in st.session_state.messages if m["role"] != "system"]

if non_system:
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if st.button("✕  Clear", key="clear_chat"):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt(mode)}]
            st.session_state.pending_image = None
            st.rerun()

    for msg in non_system:
        img_key = f"img_{id(msg)}"
        img_data = st.session_state.get(img_key)
        render_message(msg["role"], msg["content"], image_data=img_data)

# ── Image preview ─────────────────────────────────────────────────────────────

if st.session_state.pending_image:
    st.markdown('<div class="img-preview-bar">', unsafe_allow_html=True)
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        st.markdown(
            f'<div class="img-preview-pill">'
            f'<img src="data:{st.session_state.pending_image["mime"]};base64,{st.session_state.pending_image["data"]}">'
            f'<span>🖼️  {st.session_state.pending_image["name"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("✕ Remove", key="remove_img"):
            st.session_state.pending_image = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Chat input ─────────────────────────────────────────────────────────────────

has_image = st.session_state.pending_image is not None
model_id = get_model_for_mode(mode, has_image=has_image)

placeholder = "Message Aether…" if not has_image else "Ask about this image…"

if user_input := st.chat_input(placeholder):
    if has_image:
        user_msg = build_user_message(
            user_input,
            image_b64=st.session_state.pending_image["data"],
            mime_type=st.session_state.pending_image["mime"],
        )
        st.session_state.messages[0] = {
            "role": "system",
            "content": get_system_prompt(mode, has_image=True)
        }
        img_storage_key = f"img_{id(user_msg)}"
        st.session_state[img_storage_key] = st.session_state.pending_image
    else:
        user_msg = build_user_message(user_input)

    st.session_state.messages.append(user_msg)
    render_message("user", user_msg["content"], image_data=st.session_state.pending_image)
    
    st.session_state.pending_image = None

    try:
        ai_text = stream_response(st.session_state.messages, model_id)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
    except Exception as exc:
        render_message("assistant", f"**Error:** {exc}")
    
    st.rerun()
