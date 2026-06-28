import os
import re
import base64
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY")

st.set_page_config(
    page_title="Aether Multimodal AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Custom Styling ────────────────────────────────────────────────────────────
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

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0C0E17 !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
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

/* Thinking Box wrapper */
.thinking-box {
    border-left: 2px solid #4F46E5;
    background: rgba(79, 70, 229, 0.03);
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.75rem;
    border-radius: 0 6px 6px 0;
    color: #6366F1 !important;
    font-family: monospace;
    font-size: 13.5px;
}

/* ── Input ── */
.stChatInputContainer {
    background: #0C0E17 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
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
    transition: all 0.15s !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: rgba(255,255,255,0.09) !important;
    color: #A0AEC0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if not API_KEY:
    st.error("🔑 NVIDIA API key not found. Check your environment configuration.")
    st.stop()

# ── Helper Functions ──────────────────────────────────────────────────────────
def get_nvidia_client():
    return OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY)

def encode_image(uploaded_file):
    """Encode an uploaded Streamlit file to a Base64 string."""
    return base64.b64encode(uploaded_file.read()).decode("utf-8")

def parse_reasoning_content(text: str):
    """Extract <think> tags dynamically for reasoning architectures."""
    think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    if think_match:
        thinking = think_match.group(1).strip()
        answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return thinking, answer
    return None, text

# ── Sidebar Controls (Modality Configurations) ────────────────────────────────
with st.sidebar:
    st.markdown("<h3 style='color:#D0D4E0;'>🎛️ Engine Configuration</h3>", unsafe_allow_html=True)
    
    # Model Router
    model_choice = st.selectbox(
        "Select Active NIM Architecture",
        options=[
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "meta/llama-3.1-70b-instruct",
            "deepseek/deepseek-r1",
            "nvidia/cosmos-1.0-vision-70b"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("<h4 style='color:#D0D4E0;'>🖼️ Vision Layer</h4>", unsafe_allow_html=True)
    uploaded_image = st.file_uploader("Attach Image to Next Turn", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Staged Visual Asset", use_container_width=True)
        
    st.markdown("---")
    st.markdown("<h4 style='color:#D0D4E0;'>🔊 Audio Layer</h4>", unsafe_allow_html=True)
    enable_voice = st.checkbox("Enable Text-To-Speech Playback", value=False)

# ── Initialization ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Aether, an elite physical and cognitive multimodal engine powered by NVIDIA NIMs. "
    "Be precise and computationally direct. Use markdown: bold key expressions, bullet points for listings, "
    "and proper syntax formatting on code blocks. Do not produce boilerplate greetings or filler language."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="aether-header">
    <div class="aether-brand">
        <div class="aether-logo">✨</div>
        <div class="aether-title">Aether Multimodal</div>
    </div>
    <div class="aether-badge">NVIDIA NIM Active</div>
</div>
""", unsafe_allow_html=True)

# ── Custom Renderer ───────────────────────────────────────────────────────────
def render_message(role: str, content):
    if role == "user":
        # Check if content is standard text or multimodal structure
        text_display = ""
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "text":
                    text_display += item.get("text", "")
                elif item.get("type") == "image_url":
                    text_display += "<br>🖼️ *[Attached Base64 Inline Image]*"
        else:
            text_display = content

        safe = (text_display.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        safe = safe.replace("\n", "<br>")
        st.markdown(f'<div class="chat-row user-row"><div class="bubble user-bubble">{safe}</div></div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([0.04, 0.96])
        with col1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            
            # Check for thinking profiles (Reasoning models like DeepSeek-R1)
            thinking, structural_answer = parse_reasoning_content(content)
            if thinking:
                st.markdown(f'<div class="thinking-box">💭 <b>Thinking Process:</b><br>{thinking}</div>', unsafe_allow_html=True)
            
            st.markdown(structural_answer, unsafe_allow_html=False)
            st.markdown('</div>', unsafe_allow_html=True)

# ── Inference Pipeline ────────────────────────────────────────────────────────
def stream_response(messages: list, active_model: str) -> str:
    client = get_nvidia_client()
    col1, col2 = st.columns([0.04, 0.96])
    
    with col1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
    with col2:
        stream_placeholder = st.empty()
        accumulated = ""
        
        with client.chat.completions.create(
            model=active_model,
            messages=messages,
            stream=True,
        ) as stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    accumulated += chunk.choices[0].delta.content
                    
                    # Live rendering structure mapping code tokens and formatting
                    thinking, display_text = parse_reasoning_content(accumulated)
                    if thinking:
                        stream_placeholder.markdown(
                            f'<div class="thinking-box">💭 <b>Thinking Process...</b><br>{thinking}</div>\n\n{display_text}▋', 
                            unsafe_allow_html=True
                        )
                    else:
                        stream_placeholder.markdown(accumulated + "▋")
                        
        thinking, final_display = parse_reasoning_content(accumulated)
        if thinking:
            stream_placeholder.markdown(f'<div class="thinking-box">💭 <b>Thinking Process:</b><br>{thinking}</div>\n\n{final_display}', unsafe_allow_html=True)
        else:
            stream_placeholder.markdown(accumulated)
            
    return accumulated

def generate_voice_feedback(text_payload: str):
    """Utilizes Riva/NVIDIA TTS endpoints to convert generation to audio."""
    try:
        client = get_nvidia_client()
        _, clean_text = parse_reasoning_content(text_payload)
        # Stripping out markdown tags for cleaner speech synth
        clean_text = re.sub(r'[*`#_]', '', clean_text)[:250] 
        
        response = client.audio.speech.create(
            model="nvidia/riva-tts",
            voice="English-US-Male-1",
            input=clean_text
        )
        st.audio(response.content, format="audio/wav")
    except Exception as e:
        st.sidebar.error(f"Audio stream error: {e}")

# ── View Loop ─────────────────────────────────────────────────────────────────
non_system = [m for m in st.session_state.messages if m["role"] != "system"]

if non_system:
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if st.button("✕  Clear Canvas", key="clear_chat"):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.rerun()

    for msg in non_system:
        render_message(msg["role"], msg["content"])

# ── User Action Trigger ───────────────────────────────────────────────────────
if user_input := st.chat_input("Message Aether…"):
    
    # Process Multimodal payload structure if image asset is present
    if uploaded_image:
        base64_str = encode_image(uploaded_image)
        mime_type = uploaded_image.type
        current_turn_content = [
            {"type": "text", "text": user_input},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_str}"}
            }
        ]
        # Force switch to vision model if user uploaded an image but forgot to switch models
        if "vision" not in model_choice:
            model_choice = "nvidia/cosmos-1.0-vision-70b"
    else:
        current_turn_content = user_input

    st.session_state.messages.append({"role": "user", "content": current_turn_content})
    render_message("user", current_turn_content)

    try:
        ai_output = stream_response(st.session_state.messages, model_choice)
        st.session_state.messages.append({"role": "assistant", "content": ai_output})
        
        if enable_voice:
            generate_voice_feedback(ai_output)
            
    except Exception as exc:
        render_message("assistant", f"**Inference Exception Error:** {exc}")
