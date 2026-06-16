import os
import re
import flask import Flask, request, jsonify, render_template_string
from openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

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

/* ── Typing animation ── */
.typing-dots {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 8px 0;
}
.typing-dots span {
    width: 5px; height: 5px;
    background: #2D3748;
    border-radius: 50%;
    animation: blink 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes blink {
    0%, 80%, 100% { transform: scale(0.45); opacity: 0.2; }
    40%            { transform: scale(1);    opacity: 0.85; }
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
}

/* ── Clear button ── */
div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    color: #2D3748 !important;
    font-size: 11px !important;
    border-radius: 8px !important;
    padding: 3px 12px !important;
    letter-spacing: 0.3px;
    transition: all 0.15s !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: rgba(255,255,255,0.09) !important;
    color: #404A5A !important;
}

/* ── Divider ── */
.msg-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.03);
    margin: 0.25rem 0 1.75rem;
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

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

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

# ── Render message ────────────────────────────────────────────────────────────
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
        </div>""", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([0.04, 0.96])
        with col1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            st.markdown(content)
            st.markdown('</div>', unsafe_allow_html=True)

# ── History ───────────────────────────────────────────────────────────────────
non_system = [m for m in st.session_state.messages if m["role"] != "system"]

if non_system:
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if st.button("✕  Clear"):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.rerun()

    for msg in non_system:
        render_message(msg["role"], msg["content"])

# ── Input & inference ─────────────────────────────────────────────────────────
if user_input := st.chat_input("Message Aether…"):

    render_message("user", user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    placeholder = st.empty()
    placeholder.markdown("""
    <div class="chat-row assistant-row">
        <div class="avatar ai">✦</div>
        <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        with OpenRouter(api_key=API_KEY) as client:
            response = client.chat.send(
                model="openai/gpt-oss-120b:free",
                messages=st.session_state.messages,
            )
        ai_text = response.choices[0].message.content
        placeholder.empty()
        render_message("assistant", ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})

    except Exception as exc:
        placeholder.empty()
        render_message("assistant", f"**Error:** {exc}")
