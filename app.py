import os
import re
import base64
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

# ── Models available ───────────────────────────────────────────────────────────
MODELS = {
    "GPT-4o Mini (free)":      "openai/gpt-4o-mini",
    "GPT-4o":                  "openai/gpt-4o",
    "Claude 3.5 Haiku":        "anthropic/claude-3-5-haiku",
    "Claude 3.7 Sonnet":       "anthropic/claude-3-7-sonnet",
    "Gemini 2.0 Flash (free)": "google/gemini-2.0-flash-exp:free",
    "Llama 3.3 70B (free)":    "meta-llama/llama-3.3-70b-instruct:free",
    "GPT-OSS 120B (free)":     "openai/gpt-oss-120b:free",
}

VISION_MODELS = {
    "GPT-4o Mini (free)",
    "GPT-4o",
    "Claude 3.5 Haiku",
    "Claude 3.7 Sonnet",
    "Gemini 2.0 Flash (free)",
}

st.set_page_config(
    page_title="Aether AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
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
    padding-bottom: 9rem !important;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0A0C15 !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
}
[data-testid="stSidebar"] * { color: #8A95A3 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #C0C8D8 !important; font-size: 12px !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #0D0F18 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    color: #C8CEDB !important;
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
    margin-bottom: 2rem;
    background: #07080D;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.aether-brand { display: flex; align-items: center; gap: 10px; }
.aether-logo {
    width: 30px; height: 30px; border-radius: 8px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.18);
    display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.aether-title { font-size: 15px; font-weight: 600; color: #D0D4E0; letter-spacing: -0.2px; }
.aether-badge {
    font-size: 9px; font-weight: 600; color: #38A169;
    background: rgba(56,161,105,0.08); border: 1px solid rgba(56,161,105,0.18);
    border-radius: 20px; padding: 2px 8px; letter-spacing: 0.8px; text-transform: uppercase;
}

/* ── Chat rows ── */
.chat-row {
    display: flex; width: 100%; margin-bottom: 1.5rem;
    gap: 10px; align-items: flex-start;
}
.chat-row.user-row      { justify-content: flex-end; }
.chat-row.assistant-row { justify-content: flex-start; }

/* ── Avatars ── */
.avatar {
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 11px; font-weight: 600; margin-top: 3px;
}
.avatar.ai   { background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.2); color: #818CF8; }
.avatar.user { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); color: #606880; }

/* ── Bubbles ── */
.bubble {
    max-width: 80%; font-size: 14.5px; line-height: 1.75;
    word-wrap: break-word;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.bubble.user-bubble {
    background: #111420; border: 1px solid rgba(255,255,255,0.055);
    color: #BFC6D6; border-radius: 16px 16px 3px 16px; padding: 0.65rem 1rem;
}
.bubble.assistant-bubble { background: transparent; color: #7E8A99; padding: 0.1rem 0; }
.bubble.assistant-bubble p  { margin: 0 0 0.5rem; color: #8A95A3; }
.bubble.assistant-bubble p:last-child { margin-bottom: 0; }
.bubble.assistant-bubble strong { color: #C0C8D8; font-weight: 600; }
.bubble.assistant-bubble em     { color: #6E7D8C; font-style: italic; }
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
    background: #0D0F18; border: 1px solid rgba(255,255,255,0.07);
    padding: 2px 6px; border-radius: 5px;
    font-family: "Fira Code", "JetBrains Mono", monospace;
    font-size: 12.5px; color: #7EB8D4;
}
.bubble.assistant-bubble pre {
    background: #0A0C14; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 0.9rem 1.1rem; overflow-x: auto; margin: 0.75rem 0;
}
.bubble.assistant-bubble pre code { background: none; border: none; padding: 0; color: #9BAFC0; font-size: 12.5px; }
.bubble.assistant-bubble blockquote {
    border-left: 2px solid rgba(99,102,241,0.3);
    margin: 0.5rem 0; padding-left: 0.9rem; color: #6E7D8C;
}
.bubble.assistant-bubble hr { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 0.75rem 0; }
.bubble.assistant-bubble table { border-collapse: collapse; width: 100%; font-size: 13px; margin: 0.5rem 0; }
.bubble.assistant-bubble th, .bubble.assistant-bubble td {
    border: 1px solid rgba(255,255,255,0.07); padding: 6px 10px; text-align: left;
}
.bubble.assistant-bubble th { color: #C0C8D8; background: rgba(255,255,255,0.03); }

/* ── File attachment pill ── */
.file-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.15);
    border-radius: 20px; padding: 3px 10px; font-size: 11.5px; color: #818CF8;
    margin-bottom: 6px;
}
.file-pill-icon { font-size: 13px; }

/* ── Attached image preview in user bubble ── */
.attached-img {
    max-width: 260px; max-height: 180px; border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.07); margin-bottom: 6px; display: block;
}

/* ── Typing animation ── */
.typing-dots { display: inline-flex; align-items: center; gap: 5px; padding: 8px 0; }
.typing-dots span {
    width: 5px; height: 5px; background: #2D3748; border-radius: 50%;
    animation: blink 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes blink {
    0%, 80%, 100% { transform: scale(0.45); opacity: 0.2; }
    40%            { transform: scale(1);    opacity: 0.85; }
}

/* ── Input area ── */
.stChatInputContainer {
    background: #0C0E17 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    transition: border-color 0.2s !important;
}
.stChatInputContainer:focus-within {
    border-color: rgba(99,102,241,0.2) !important;
    box-shadow: none !important;
}
.stChatInputContainer textarea {
    color: #C8CEDB !important; font-size: 14px !important; background: transparent !important;
}
textarea:focus { outline: none !important; box-shadow: none !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: transparent !important;
}
[data-testid="stFileUploader"] section {
    background: #0C0E17 !important;
    border: 1px dashed rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: rgba(99,102,241,0.4) !important;
}
[data-testid="stFileUploader"] label { color: #606880 !important; font-size: 12px !important; }
[data-testid="stFileUploader"] button {
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    color: #818CF8 !important; font-size: 11px !important; border-radius: 6px !important;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    color: #2D3748 !important; font-size: 11px !important;
    border-radius: 8px !important; padding: 3px 12px !important;
    letter-spacing: 0.3px; transition: all 0.15s !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: rgba(255,255,255,0.09) !important; color: #404A5A !important;
}

/* ── Pending file banner ── */
.pending-file {
    display: flex; align-items: center; gap: 8px;
    background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.12);
    border-radius: 8px; padding: 6px 12px; margin-bottom: 0.5rem;
    font-size: 12px; color: #818CF8;
}

/* ── Streaming cursor ── */
@keyframes cursor-blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
}

/* ── Divider ── */
.msg-divider {
    border: none; border-top: 1px solid rgba(255,255,255,0.03); margin: 0.25rem 0 1.75rem;
}
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if not API_KEY:
    st.error("🔑 API key not found. Check your `.env` file.")
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Aether, an elite AI intelligence engine. "
    "Be concise and precise. Use markdown for structure: bold key terms, "
    "use bullet points for lists, and fenced code blocks for code. "
    "Never pad responses with filler phrases."
)

if "messages"      not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "GPT-OSS 120B (free)"
if "pending_file"  not in st.session_state:
    st.session_state.pending_file = None   # dict: {name, type, b64, is_image}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.session_state.selected_model = st.selectbox(
        "Model",
        list(MODELS.keys()),
        index=list(MODELS.keys()).index(st.session_state.selected_model),
    )
    model_id = MODELS[st.session_state.selected_model]
    supports_vision = st.session_state.selected_model in VISION_MODELS

    st.markdown("---")
    st.markdown("### 📎 Attach a file")
    uploaded = st.file_uploader(
        "Image or text file",
        type=["png", "jpg", "jpeg", "gif", "webp", "txt", "md", "py", "js", "ts",
              "json", "csv", "html", "css", "xml", "yaml", "yml"],
        label_visibility="collapsed",
    )
    if uploaded:
        raw = uploaded.read()
        is_image = uploaded.type.startswith("image/")
        if is_image and not supports_vision:
            st.warning("⚠️ Current model doesn't support images. Switch to a vision model.")
        else:
            b64 = base64.b64encode(raw).decode()
            st.session_state.pending_file = {
                "name":     uploaded.name,
                "type":     uploaded.type,
                "b64":      b64,
                "is_image": is_image,
                "raw_text": None if is_image else raw.decode("utf-8", errors="replace"),
            }
            st.success(f"✓ Ready to send: **{uploaded.name}**")

    if st.session_state.pending_file:
        if st.button("✕ Remove file"):
            st.session_state.pending_file = None
            st.rerun()

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:10px;color:#2D3748'>Model: {model_id}</div>",
        unsafe_allow_html=True,
    )

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


# ── Helpers ───────────────────────────────────────────────────────────────────
def file_pill(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].upper() if "." in name else "FILE"
    icon = "🖼️" if ext in {"PNG","JPG","JPEG","GIF","WEBP"} else "📄"
    return f'<div class="file-pill"><span class="file-pill-icon">{icon}</span>{name}</div>'


def render_message(role: str, content, file_meta: dict | None = None):
    """Render a chat message. content may be str or list (vision payload)."""
    if role == "user":
        # Extract display text
        if isinstance(content, list):
            text_parts = [p["text"] for p in content if p.get("type") == "text"]
            display_text = " ".join(text_parts)
        else:
            display_text = content

        safe = (display_text
                .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        safe = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         safe)
        safe = re.sub(r'`(.+?)`',       r'<code>\1</code>',      safe)
        safe = safe.replace("\n", "<br>")

        inner = ""
        if file_meta:
            if file_meta["is_image"]:
                inner += (f'<img class="attached-img" '
                          f'src="data:{file_meta["type"]};base64,{file_meta["b64"]}" '
                          f'alt="{file_meta["name"]}">')
            else:
                inner += file_pill(file_meta["name"])
        inner += safe

        st.markdown(f"""
        <div class="chat-row user-row">
            <div class="bubble user-bubble">{inner}</div>
        </div>""", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([0.04, 0.96])
        with col1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>',
                        unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            st.markdown(content if isinstance(content, str) else str(content),
                        unsafe_allow_html=False)
            st.markdown('</div>', unsafe_allow_html=True)


def build_user_content(text: str, file_meta: dict | None) -> list | str:
    """Build the message content — plain string or multipart list."""
    if not file_meta:
        return text

    if file_meta["is_image"]:
        return [
            {"type": "image_url",
             "image_url": {"url": f"data:{file_meta['type']};base64,{file_meta['b64']}"}},
            {"type": "text", "text": text},
        ]
    else:
        # Prepend file text as context
        combined = (f"[File: {file_meta['name']}]\n"
                    f"```\n{file_meta['raw_text']}\n```\n\n"
                    f"{text}")
        return combined


def stream_response(messages: list) -> str:
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

    col1, col2 = st.columns([0.04, 0.96])
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>',
                    unsafe_allow_html=True)
    with col2:
        placeholder = st.empty()
        accumulated = ""

        with client.chat.completions.create(
            model=MODELS[st.session_state.selected_model],
            messages=messages,
            stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    accumulated += delta
                    placeholder.markdown(accumulated + "▋")

        placeholder.markdown(accumulated)

    return accumulated


# ── History ───────────────────────────────────────────────────────────────────
non_system = [m for m in st.session_state.messages if m["role"] != "system"]

if non_system:
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if st.button("✕  Clear", key="clear_chat"):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.session_state.pending_file = None
            st.rerun()

    for msg in non_system:
        render_message(msg["role"], msg["content"],
                       file_meta=msg.get("_file_meta"))

# ── Pending file indicator above input ────────────────────────────────────────
if st.session_state.pending_file:
    pf = st.session_state.pending_file
    icon = "🖼️" if pf["is_image"] else "📄"
    st.markdown(
        f'<div class="pending-file">{icon} <strong>{pf["name"]}</strong>'
        f'<span style="color:#404A5A;margin-left:4px">— will be sent with your next message</span></div>',
        unsafe_allow_html=True,
    )

# ── Input & inference ─────────────────────────────────────────────────────────
if user_input := st.chat_input("Message Aether…"):
    file_meta = st.session_state.pending_file
    content   = build_user_content(user_input, file_meta)

    # Store with optional _file_meta for re-rendering history
    st.session_state.messages.append({
        "role":       "user",
        "content":    content,
        "_file_meta": file_meta,
    })
    render_message("user", content, file_meta=file_meta)

    # Clear pending file after send
    st.session_state.pending_file = None

    try:
        # Strip private keys before sending to API
        api_messages = [
            {k: v for k, v in m.items() if not k.startswith("_")}
            for m in st.session_state.messages
        ]
        ai_text = stream_response(api_messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
    except Exception as exc:
        render_message("assistant", f"**Error:** {exc}")
