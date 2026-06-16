import os
import re
from flask import Flask, request, jsonify, render_template_string
from openrouter import OpenRouter
from dotenv import load_dotenv

# ── 1. Environment ────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# ── 2. Flask Config ───────────────────────────────────────────────────────────
app = Flask(__name__)

# ── 3. Unified Layout Sheet & HTML ────────────────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aether AI</title>
    <style>
    /* ── Base ── */
    html, body {
        background: #07080D !important;
        margin: 0;
        padding: 0;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
    .block-container {
        max-width: 720px !important;
        width: 100%;
        margin: 0 auto;
        padding-top: 0 !important;
        padding-bottom: 8rem !important;
        display: flex;
        flex-direction: column;
        flex: 1;
        box-sizing: border-box;
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

    /* ── Chat Canvas ── */
    .chat-area {
        flex: 1;
        overflow-y: auto;
        padding-right: 4px;
    }
    .chat-area::-webkit-scrollbar { width: 4px; }
    .chat-area::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 2px; }

    /* ── Chat rows ── */
    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 1.5rem;
        gap: 10px;
        align-items: flex-start;
        box-sizing: border-box;
    }
    .chat-row.user-row    { justify-content: flex-end; }
    .chat-row.assistant-row { justify-content: flex-start; }

    /* ── Avatars ── */
    .avatar-col {
        width: 5%;
        flex-shrink: 0;
    }
    .bubble-col {
        width: 95%;
    }
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
    .chat-row.user-row .bubble {
        max-width: 80%;
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
        max-width: 100%;
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

    /* ── Input Wrapper ── */
    .input-dock {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: #07080D;
        padding-bottom: 2rem;
        z-index: 90;
    }
    .input-dock-inner {
        max-width: 720px;
        margin: 0 auto;
        padding: 0 20px;
    }

    /* ── Input ── */
    .stChatInputContainer {
        background: #0C0E17 !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 14px !important;
        box-shadow: 0 0 0 1px rgba(99,102,241,0.04) !important;
        transition: border-color 0.2s !important;
        display: flex;
        padding: 10px 14px;
        align-items: center;
    }
    .stChatInputContainer:focus-within {
        border-color: rgba(99,102,241,0.2) !important;
    }
    .stChatInputContainer textarea {
        color: #C8CEDB !important;
        font-size: 14px !important;
        background: transparent !important;
        border: none;
        outline: none;
        resize: none;
        width: 100%;
        font-family: inherit;
        height: 20px;
    }

    /* ── Control Button Layout Row ── */
    .control-row {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }

    /* ── Clear button ── */
    .clear-btn {
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        color: #2D3748 !important;
        font-size: 11px !important;
        border-radius: 8px !important;
        padding: 5px 16px !important;
        letter-spacing: 0.3px;
        transition: all 0.15s !important;
        cursor: pointer;
    }
    .clear-btn:hover {
        border-color: rgba(255,255,255,0.09) !important;
        color: #404A5A !important;
    }
    </style>
</head>
<body>

    <div class="block-container">
        <!-- ── Header ── -->
        <div class="aether-header">
            <div class="aether-brand">
                <div class="aether-logo">✨</div>
                <div class="aether-title">Aether</div>
            </div>
            <div class="aether-badge">Online</div>
        </div>

        <!-- ── Control Row (Clear Button) ── -->
        <div class="control-row" id="controlRow" style="display: none;">
            <button class="clear-btn" onclick="clearChat()">✕  Clear</button>
        </div>

        <!-- ── Chat Area ── -->
        <div class="chat-area" id="chatArea"></div>
    </div>

    <!-- ── Input Dock ── -->
    <div class="input-dock">
        <div class="input-dock-inner">
            <div class="stChatInputContainer">
                <textarea id="chatInput" placeholder="Message Aether…" rows="1" onkeydown="handleKeyPress(event)"></textarea>
            </div>
        </div>
    </div>

    <!-- ── State Pipeline Scripts ── -->
    <script>
        let chatHistory = [];

        function handleKeyPress(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitMessage();
            }
        }

        async function submitMessage() {
            const inputField = document.getElementById('chatInput');
            const userText = inputField.value.trim();
            if (!userText) return;

            inputField.value = '';
            document.getElementById('controlRow').style.display = 'flex';

            // 1. Render User Message
            renderUserMessage(userText);
            chatHistory.push({"role": "user", "content": userText});

            // 2. Render Animated Loading State
            const loader = renderLoadingIndicator();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: chatHistory })
                });
                const data = await response.json();
                
                loader.remove();

                if (data.error) {
                    renderErrorMessage(data.error);
                } else {
                    renderAssistantMessage(data.html_content);
                    chatHistory.push({"role": "assistant", "content": data.raw_content});
                }
            } catch (err) {
                loader.remove();
                renderErrorMessage(err);
            }
        }

        function renderUserMessage(text) {
            const container = document.getElementById('chatArea');
            let safe = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            safe = safe.replace(/\\*\\*(.+?)\\*\\//g, '<strong>$1</strong>');
            safe = safe.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
            safe = safe.replace(/`(.+?)`/g, '<code>$1</code>');
            safe = safe.replace(/\\n/g, '<br>');

            container.innerHTML += `
                <div class="chat-row user-row">
                    <div class="bubble user-bubble">${safe}</div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
        }

        function renderLoadingIndicator() {
            const container = document.getElementById('chatArea');
            const id = 'loader_' + Date.now();
            container.innerHTML += `
                <div class="chat-row assistant-row" id="${id}">
                    <div class="avatar-col"><div class="avatar ai">✦</div></div>
                    <div class="bubble-col">
                        <div class="typing-dots"><span></span><span></span><span></span></div>
                    </div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
            return document.getElementById(id);
        }

        function renderAssistantMessage(htmlContent) {
            const container = document.getElementById('chatArea');
            container.innerHTML += `
                <div class="chat-row assistant-row">
                    <div class="avatar-col"><div class="avatar ai" style="margin-top:6px">✦</div></div>
                    <div class="bubble-col">
                        <div class="bubble assistant-bubble">${htmlContent}</div>
                    </div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
        }

        function renderErrorMessage(err) {
            const container = document.getElementById('chatArea');
            container.innerHTML += `
                <div class="chat-row assistant-row">
                    <div class="avatar-col"><div class="avatar ai" style="margin-top:6px">✦</div></div>
                    <div class="bubble-col">
                        <div class="bubble assistant-bubble" style="color: #FC8181;"><strong>Error:</strong> ${err}</div>
                    </div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
        }

        function clearChat() {
            document.getElementById('chatArea').innerHTML = '';
            document.getElementById('controlRow').style.display = 'none';
            chatHistory = [];
        }
    </script>
</body>
</html>
"""

# ── 4. Guard ──────────────────────────────────────────────────────────────────
if not API_KEY:
    print("🔑 API key not found. Check your `.env` file.")

SYSTEM_PROMPT = (
    "You are Aether, an elite AI intelligence engine. "
    "Be concise and precise. Use markdown for structure: bold key terms, "
    "use bullet points for lists, and fenced code blocks for code. "
    "Never pad responses with filler phrases."
)

# ── 5. Helper Markdown Parsing Pipeline ────────────────────────────────────────
def convert_markdown_to_html(text):
    """
    Parses structural markdown properties down to plain HTML nodes.
    Matches the custom CSS classes targeting structural elements perfectly.
    """
    html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    def parse_table(match):
        lines = match.group(0).strip().split('\n')
        table_html = "<table>"
        for i, line in enumerate(lines):
            if '|---' in line or '| :---' in line:
                continue
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if not cols:
                continue
            tag = "th" if i == 0 else "td"
            table_html += "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cols) + "</tr>"
        table_html += "</table>"
        return table_html
    html = re.sub(r'(\|[^\n]+\|\n\|[ \-.:|]+\|\n(?:\|[^\n]+\|\n*)+)', parse_table, html)

    html = re.sub(r'
