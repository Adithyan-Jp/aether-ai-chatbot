import os
import re
import base64
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")

MODELS = {
    "GPT-OSS 120B (free)":     "openai/gpt-oss-120b:free",
    "GPT-4o Mini":             "openai/gpt-4o-mini",
    "GPT-4o":                  "openai/gpt-4o",
    "Claude 3.5 Haiku":        "anthropic/claude-3-5-haiku",
    "Claude 3.7 Sonnet":       "anthropic/claude-3-7-sonnet",
    "Gemini 2.0 Flash (free)": "google/gemini-2.0-flash-exp:free",
    "Llama 3.3 70B (free)":    "meta-llama/llama-3.3-70b-instruct:free",
}
VISION_MODELS = {"GPT-4o Mini","GPT-4o","Claude 3.5 Haiku","Claude 3.7 Sonnet","Gemini 2.0 Flash (free)"}

st.set_page_config(page_title="Aether AI", page_icon="✨", layout="centered",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* ── Base ── */
.stApp, html, body, [data-testid="stAppViewContainer"] { background: #07080D !important; }
.main .block-container {
    max-width: 720px !important;
    padding-top: 0 !important;
    padding-bottom: 7rem !important;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Header ── */
.aether-header {
    position: sticky; top: 0; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0; margin-bottom: 2rem;
    background: #07080D;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.aether-brand  { display: flex; align-items: center; gap: 10px; }
.aether-logo   {
    width: 30px; height: 30px; border-radius: 8px;
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.18);
    display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.aether-title  { font-size: 15px; font-weight: 600; color: #D0D4E0; letter-spacing: -0.2px; }
.aether-badge  {
    font-size: 9px; font-weight: 600; color: #38A169;
    background: rgba(56,161,105,0.08); border: 1px solid rgba(56,161,105,0.18);
    border-radius: 20px; padding: 2px 8px; letter-spacing: 0.8px; text-transform: uppercase;
}
.model-chip {
    font-size: 10px; color: #404A5A;
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px; padding: 2px 10px; letter-spacing: 0.2px;
}

/* ── Chat rows ── */
.chat-row { display: flex; width: 100%; margin-bottom: 1.5rem; gap: 10px; align-items: flex-start; }
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
    max-width: 80%; font-size: 14.5px; line-height: 1.75; word-wrap: break-word;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.bubble.user-bubble {
    background: #111420; border: 1px solid rgba(255,255,255,0.055);
    color: #BFC6D6; border-radius: 16px 16px 3px 16px; padding: 0.65rem 1rem;
}
.bubble.assistant-bubble { background: transparent; color: #7E8A99; padding: 0.1rem 0; }
.bubble.assistant-bubble p            { margin: 0 0 0.5rem; color: #8A95A3; }
.bubble.assistant-bubble p:last-child { margin-bottom: 0; }
.bubble.assistant-bubble strong { color: #C0C8D8; font-weight: 600; }
.bubble.assistant-bubble em     { color: #6E7D8C; font-style: italic; }
.bubble.assistant-bubble ul, .bubble.assistant-bubble ol { margin: 0.35rem 0 0.35rem 1.15rem; padding: 0; }
.bubble.assistant-bubble li  { margin-bottom: 4px; color: #8A95A3; }
.bubble.assistant-bubble h1, .bubble.assistant-bubble h2, .bubble.assistant-bubble h3
    { color: #C0C8D8; font-weight: 600; margin: 0.8rem 0 0.35rem; }
.bubble.assistant-bubble h1 { font-size: 17px; }
.bubble.assistant-bubble h2 { font-size: 15px; }
.bubble.assistant-bubble h3 { font-size: 14px; }
.bubble.assistant-bubble code {
    background: #0D0F18; border: 1px solid rgba(255,255,255,0.07);
    padding: 2px 6px; border-radius: 5px;
    font-family: "Fira Code","JetBrains Mono",monospace; font-size: 12.5px; color: #7EB8D4;
}
.bubble.assistant-bubble pre {
    background: #0A0C14; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 0.9rem 1.1rem; overflow-x: auto; margin: 0.75rem 0;
}
.bubble.assistant-bubble pre code { background: none; border: none; padding: 0; color: #9BAFC0; font-size: 12.5px; }
.bubble.assistant-bubble blockquote {
    border-left: 2px solid rgba(99,102,241,0.3); margin: 0.5rem 0; padding-left: 0.9rem; color: #6E7D8C;
}
.bubble.assistant-bubble hr    { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 0.75rem 0; }
.bubble.assistant-bubble table { border-collapse: collapse; width: 100%; font-size: 13px; margin: 0.5rem 0; }
.bubble.assistant-bubble th, .bubble.assistant-bubble td
    { border: 1px solid rgba(255,255,255,0.07); padding: 6px 10px; text-align: left; }
.bubble.assistant-bubble th { color: #C0C8D8; background: rgba(255,255,255,0.03); }

/* ── Attached image in user bubble ── */
.attached-img {
    max-width: 240px; max-height: 160px; border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.07); margin-bottom: 6px; display: block;
}
.file-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.15);
    border-radius: 20px; padding: 3px 10px; font-size: 11.5px; color: #818CF8; margin-bottom: 6px;
}

/* ── Custom input box ── */
.input-wrap {
    position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
    width: min(720px, 100vw); padding: 0 1rem 1.2rem; background: #07080D; z-index: 200;
}
.input-box {
    display: flex; align-items: flex-end; gap: 0;
    background: #0C0E17; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; overflow: hidden;
    transition: border-color 0.2s;
}
.input-box:focus-within { border-color: rgba(99,102,241,0.25); }

#user-textarea {
    flex: 1; background: transparent; border: none; outline: none;
    color: #C8CEDB; font-size: 14px; line-height: 1.5;
    padding: 12px 14px; resize: none; min-height: 46px; max-height: 160px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    overflow-y: auto;
}
#user-textarea::placeholder { color: #2D3748; }

/* paperclip btn */
.attach-btn {
    flex-shrink: 0; width: 38px; height: 46px;
    display: flex; align-items: center; justify-content: center;
    background: transparent; border: none; cursor: pointer;
    color: #2D3748; font-size: 16px;
    transition: color 0.15s;
}
.attach-btn:hover { color: #818CF8; }

/* send btn */
.send-btn {
    flex-shrink: 0; width: 38px; height: 38px; margin: 4px 6px 4px 0;
    display: flex; align-items: center; justify-content: center;
    background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.2);
    border-radius: 9px; cursor: pointer; color: #818CF8; font-size: 14px;
    transition: background 0.15s;
}
.send-btn:hover { background: rgba(99,102,241,0.28); }

/* preview strip above input */
.preview-strip {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 4px 8px;
}
.preview-thumb {
    position: relative; display: inline-flex;
}
.preview-thumb img {
    width: 48px; height: 48px; object-fit: cover; border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.08);
}
.preview-thumb .remove-x {
    position: absolute; top: -5px; right: -5px;
    width: 16px; height: 16px; border-radius: 50%;
    background: #1A1D2A; border: 1px solid rgba(255,255,255,0.1);
    color: #606880; font-size: 9px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
}
.preview-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.15);
    border-radius: 20px; padding: 4px 10px; font-size: 11.5px; color: #818CF8; cursor: default;
}
.preview-pill .remove-x {
    cursor: pointer; color: #606880; font-size: 10px; margin-left: 2px;
}

/* model selector inside input wrap */
.model-select-row {
    display: flex; align-items: center; gap: 6px; padding: 6px 2px 0;
}
.model-label { font-size: 10px; color: #2D3748; }
#model-select {
    background: transparent; border: none; outline: none;
    color: #404A5A; font-size: 10px; cursor: pointer;
}
#model-select option { background: #0C0E17; color: #C8CEDB; }

/* hide default streamlit chat input */
[data-testid="stChatInput"] { display: none !important; }

/* clear btn */
div[data-testid="stButton"] > button {
    background: transparent !important; border: 1px solid rgba(255,255,255,0.05) !important;
    color: #2D3748 !important; font-size: 11px !important;
    border-radius: 8px !important; padding: 3px 12px !important;
    letter-spacing: 0.3px; transition: all 0.15s !important;
}
div[data-testid="stButton"] > button:hover
    { border-color: rgba(255,255,255,0.09) !important; color: #404A5A !important; }

/* typing */
.typing-dots { display: inline-flex; align-items: center; gap: 5px; padding: 8px 0; }
.typing-dots span {
    width: 5px; height: 5px; background: #2D3748; border-radius: 50%;
    animation: blink 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes blink {
    0%,80%,100% { transform: scale(0.45); opacity: 0.2; }
    40%          { transform: scale(1);    opacity: 0.85; }
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
for key, val in [
    ("messages",       [{"role": "system", "content": SYSTEM_PROMPT}]),
    ("selected_model", "GPT-OSS 120B (free)"),
    ("pending_file",   None),
    ("user_input",     ""),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Header ────────────────────────────────────────────────────────────────────
model_display = st.session_state.selected_model
st.markdown(f"""
<div class="aether-header">
    <div class="aether-brand">
        <div class="aether-logo">✨</div>
        <div class="aether-title">Aether</div>
    </div>
    <div style="display:flex;align-items:center;gap:8px">
        <div class="model-chip">{model_display}</div>
        <div class="aether-badge">Online</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Render helpers ────────────────────────────────────────────────────────────
def render_message(role, content, file_meta=None):
    if role == "user":
        text = content if isinstance(content, str) else \
               " ".join(p["text"] for p in content if p.get("type") == "text")
        safe = (text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        safe = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         safe)
        safe = re.sub(r'`(.+?)`',       r'<code>\1</code>',      safe)
        safe = safe.replace("\n","<br>")
        inner = ""
        if file_meta:
            if file_meta["is_image"]:
                inner += (f'<img class="attached-img" '
                          f'src="data:{file_meta["type"]};base64,{file_meta["b64"]}" '
                          f'alt="{file_meta["name"]}">')
            else:
                inner += (f'<div class="file-pill">📄 {file_meta["name"]}</div>')
        inner += safe
        st.markdown(f'<div class="chat-row user-row"><div class="bubble user-bubble">{inner}</div></div>',
                    unsafe_allow_html=True)
    else:
        c1, c2 = st.columns([0.04, 0.96])
        with c1:
            st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="bubble assistant-bubble">', unsafe_allow_html=True)
            st.markdown(content if isinstance(content, str) else str(content))
            st.markdown('</div>', unsafe_allow_html=True)


def build_content(text, file_meta):
    if not file_meta:
        return text
    if file_meta["is_image"]:
        return [
            {"type": "image_url",
             "image_url": {"url": f"data:{file_meta['type']};base64,{file_meta['b64']}"}},
            {"type": "text", "text": text},
        ]
    return (f"[File: {file_meta['name']}]\n```\n{file_meta['raw_text']}\n```\n\n{text}")


def stream_response(messages):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)
    c1, c2 = st.columns([0.04, 0.96])
    with c1:
        st.markdown('<div class="avatar ai" style="margin-top:6px">✦</div>', unsafe_allow_html=True)
    with c2:
        ph = st.empty(); acc = ""
        with client.chat.completions.create(
            model=MODELS[st.session_state.selected_model],
            messages=messages, stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    acc += delta
                    ph.markdown(acc + "▋")
        ph.markdown(acc)
    return acc


# ── History ───────────────────────────────────────────────────────────────────
non_sys = [m for m in st.session_state.messages if m["role"] != "system"]
if non_sys:
    c1, c2, c3 = st.columns([4, 2, 4])
    with c2:
        if st.button("✕  Clear"):
            st.session_state.messages    = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.session_state.pending_file = None
            st.rerun()
    for m in non_sys:
        render_message(m["role"], m["content"], m.get("_file_meta"))

# ── Custom input component ────────────────────────────────────────────────────
model_opts_js = ", ".join(f'"{k}"' for k in MODELS.keys())

# Build preview HTML for pending file
pf = st.session_state.pending_file
preview_html = ""
if pf:
    if pf["is_image"]:
        preview_html = (
            f'<div class="preview-strip">'
            f'<div class="preview-thumb">'
            f'<img src="data:{pf["type"]};base64,{pf["b64"]}" alt="{pf["name"]}">'
            f'<div class="remove-x" onclick="removeFile()">✕</div>'
            f'</div></div>'
        )
    else:
        preview_html = (
            f'<div class="preview-strip">'
            f'<div class="preview-pill">📄 {pf["name"]}'
            f'<span class="remove-x" onclick="removeFile()">✕</span>'
            f'</div></div>'
        )

current_model = st.session_state.selected_model
model_options_html = "".join(
    f'<option value="{k}" {"selected" if k == current_model else ""}>{k}</option>'
    for k in MODELS.keys()
)

component_html = f"""
<div class="input-wrap">
  <div id="preview-area">{preview_html}</div>
  <div class="input-box" id="inputBox">
    <button class="attach-btn" onclick="document.getElementById('file-input').click()" title="Attach file">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
      </svg>
    </button>
    <textarea id="user-textarea" placeholder="Message Aether…" rows="1"
      onInput="autoResize(this)" onKeyDown="handleKey(event)"></textarea>
    <button class="send-btn" onclick="submitMsg()" title="Send">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
           stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
      </svg>
    </button>
  </div>
  <div class="model-select-row">
    <span class="model-label">Model:</span>
    <select id="model-select" onchange="changeModel(this.value)">{model_options_html}</select>
  </div>
</div>

<!-- hidden file input -->
<input type="file" id="file-input" style="display:none"
  accept="image/png,image/jpeg,image/gif,image/webp,text/plain,text/markdown,
          application/json,.py,.js,.ts,.html,.css,.xml,.yaml,.yml,.csv,.md"
  onchange="handleFile(this)">

<script>
// ── file state ──
let pendingFile = null;

function autoResize(el) {{
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}}

function handleKey(e) {{
  if (e.key === "Enter" && !e.shiftKey) {{ e.preventDefault(); submitMsg(); }}
}}

function handleFile(input) {{
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {{
    const b64 = e.target.result.split(",")[1];
    const isImage = file.type.startsWith("image/");
    pendingFile = {{ name: file.name, type: file.type, b64: b64, isImage: isImage }};
    renderPreview();
  }};
  reader.readAsDataURL(file);
  input.value = "";
}}

function renderPreview() {{
  const area = document.getElementById("preview-area");
  if (!pendingFile) {{ area.innerHTML = ""; return; }}
  if (pendingFile.isImage) {{
    area.innerHTML = `
      <div class="preview-strip">
        <div class="preview-thumb">
          <img src="data:${{pendingFile.type}};base64,${{pendingFile.b64}}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;border:1px solid rgba(255,255,255,0.08)">
          <div class="remove-x" onclick="removeFile()" style="position:absolute;top:-5px;right:-5px;width:16px;height:16px;border-radius:50%;background:#1A1D2A;border:1px solid rgba(255,255,255,0.1);color:#606880;font-size:9px;cursor:pointer;display:flex;align-items:center;justify-content:center;">✕</div>
        </div>
      </div>`;
  }} else {{
    area.innerHTML = `
      <div class="preview-strip">
        <div class="preview-pill">📄 ${{pendingFile.name}}
          <span class="remove-x" onclick="removeFile()" style="cursor:pointer;color:#606880;font-size:10px;margin-left:4px;">✕</span>
        </div>
      </div>`;
  }}
}}

function removeFile() {{
  pendingFile = null;
  renderPreview();
  // Tell Streamlit to clear pending file
  window.parent.postMessage({{type:"streamlit:setComponentValue", key:"remove_file", value: true}}, "*");
  sendToStreamlit("__REMOVE_FILE__", null);
}}

function changeModel(val) {{
  sendToStreamlit("__MODEL__:" + val, null);
}}

function submitMsg() {{
  const ta = document.getElementById("user-textarea");
  const text = ta.value.trim();
  if (!text && !pendingFile) return;
  const payload = JSON.stringify({{ text: text, file: pendingFile }});
  ta.value = "";
  ta.style.height = "auto";
  pendingFile = null;
  renderPreview();
  sendToStreamlit(payload, null);
}}

function sendToStreamlit(val, _) {{
  // Use the hidden st.chat_input trick: set value on the actual textarea
  const stInputs = window.parent.document.querySelectorAll('textarea[data-testid="stChatInputTextArea"]');
  if (stInputs.length > 0) {{
    const nativeInput = stInputs[0];
    const nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, 'value').set;
    nativeSetter.call(nativeInput, val);
    nativeInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
    setTimeout(() => {{
      const form = nativeInput.closest('form');
      if (form) {{
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.click();
      }}
    }}, 50);
  }}
}}
</script>
"""

st.components.v1.html(component_html, height=140, scrolling=False)

# ── Hidden st.chat_input to receive messages ──────────────────────────────────
raw = st.chat_input("Message Aether…")

if raw:
    # Parse payload
    file_meta = None
    user_text = raw

    if raw.startswith("__REMOVE_FILE__"):
        st.session_state.pending_file = None
        st.rerun()
    elif raw.startswith("__MODEL__:"):
        model_name = raw[len("__MODEL__:"):]
        if model_name in MODELS:
            st.session_state.selected_model = model_name
        st.rerun()
    else:
        try:
            import json
            payload   = json.loads(raw)
            user_text = payload.get("text", "").strip()
            file_data = payload.get("file")

            if file_data:
                is_image = file_data.get("isImage", False)
                file_meta = {
                    "name":     file_data["name"],
                    "type":     file_data["type"],
                    "b64":      file_data["b64"],
                    "is_image": is_image,
                    "raw_text": None if is_image else
                                base64.b64decode(file_data["b64"]).decode("utf-8", errors="replace"),
                }
        except Exception:
            user_text = raw  # plain text fallback

        if not user_text and not file_meta:
            st.stop()

        content = build_content(user_text, file_meta)
        st.session_state.messages.append({"role": "user", "content": content, "_file_meta": file_meta})
        render_message("user", content, file_meta)

        try:
            api_msgs = [{k: v for k, v in m.items() if not k.startswith("_")}
                        for m in st.session_state.messages]
            ai_text = stream_response(api_msgs)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as exc:
            render_message("assistant", f"**Error:** {exc}")
