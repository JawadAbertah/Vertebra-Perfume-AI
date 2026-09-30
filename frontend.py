"""
frontend.py — Vertebra AI | Sendbird-Style Floating Chat Widget v5.0
Exact replication of Sendbird compact widget UI.
Connects to FastAPI backend at http://127.0.0.1:8000/chat
"""

import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 1. Page Config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vertebra AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Brand Constants  (exact purple from Vertebra.jfif: #B021B1)
# ─────────────────────────────────────────────────────────────────────────────
API_URL     = "http://127.0.0.1:8000/chat"
API_TIMEOUT = 30
PURPLE      = "#B021B1"
PURPLE_DARK = "#99189A"
LOGO_PATH   = Path("Vertebra.jfif")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Base64 Image Loader — standard library only, zero Streamlit internals
# ─────────────────────────────────────────────────────────────────────────────
def get_base64_image(path: Path) -> str:
    """Read image bytes and return a data:image/jpeg;base64,... URI string."""
    if path.exists():
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
    return ""

LOGO_URI: str = get_base64_image(LOGO_PATH)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Global CSS — Floating Widget, Sendbird Reference
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    /* ── Tajawal Arabic Font ──────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;600;700;800&display=swap');

    /* 1. Force the main app background to grey */
    .stApp {{ background-color: #E5E5E5 !important; }}

    /* 2. The Main Widget Card */
    .block-container {{
        max-width: 420px !important;
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        margin-top: 40px !important;
        padding: 20px 20px 0px 20px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
    }}

    /* 3. Rip the Input Container from the Viewport Bottom and Dock It */
    [data-testid="stBottom"] {{
        position: static !important; 
        width: 100% !important;
        max-width: 420px !important; 
        margin: 0 auto !important;
        background-color: #FFFFFF !important;
        padding: 0px 20px 20px 20px !important;
        border-bottom-left-radius: 16px !important;
        border-bottom-right-radius: 16px !important;
    }}

    /* 4. Annihilate the Dark Mode Input Box */
    [data-testid="stChatInput"] {{ background-color: #FFFFFF !important; border: 1px solid #E0E0E0 !important; border-radius: 24px !important; padding: 0 !important; }}
    [data-testid="stChatInput"] * {{ background-color: transparent !important; color: #333333 !important; }}
    div[data-baseweb="input"] {{ background-color: #FFFFFF !important; border: none !important; }}

    /* 5. Hide Streamlit Header & Annoying Defaults */
    [data-testid="stHeader"], #MainMenu, footer,
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    section[data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none !important; }}

    /* ── RTL: prevent vertical text stacking ─────────────────────────────── */
    p, span, div, label, button, h1, h2, h3, h4, h5, h6 {{
        writing-mode: horizontal-tb !important;
        text-orientation: mixed !important;
        direction: rtl !important;
        font-family: 'Tajawal', sans-serif !important;
    }}

    /* ─── HEADER ─────────────────────────────────────────────────────────── */
    /* Header brand column: white bg, bottom border */
    .st-key-btn_refresh,
    .st-key-btn_exit {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding-top: 0 !important;
    }}

    /* ↻ Refresh button */
    .st-key-btn_refresh button {{
        width: 28px !important;
        height: 28px !important;
        min-height: 28px !important;
        border-radius: 50% !important;
        background: transparent !important;
        border: none !important;
        color: #888888 !important;
        font-size: 1rem !important;
        padding: 0 !important;
        box-shadow: none !important;
        margin-top: 16px !important;
        transition: all 0.25s ease !important;
    }}
    .st-key-btn_refresh button:hover {{
        background: #F5F0FF !important;
        color: {PURPLE} !important;
        transform: rotate(180deg) !important;
    }}

    /* ✕ Exit button */
    .st-key-btn_exit button {{
        width: 28px !important;
        height: 28px !important;
        min-height: 28px !important;
        border-radius: 50% !important;
        background: transparent !important;
        border: none !important;
        color: #888888 !important;
        font-size: 0.85rem !important;
        padding: 0 !important;
        box-shadow: none !important;
        margin-top: 16px !important;
        transition: all 0.2s ease !important;
    }}
    .st-key-btn_exit button:hover {{
        background: #FEF2F2 !important;
        color: #EF4444 !important;
    }}

    /* ─── MESSAGE BUBBLES ────────────────────────────────────────────────── */
    /* Bot bubble: light grey bg, dark grey text (high contrast) */
    .bot-row {{
        display: flex;
        align-items: flex-end;
        gap: 7px;
        justify-content: flex-start;
        margin-bottom: 10px;
        padding: 0 14px;
        direction: rtl;
    }}
    .bot-avt {{
        width: 26px;
        height: 26px;
        border-radius: 50%;
        object-fit: cover;
        flex-shrink: 0;
        border: 1px solid #F0ABFC;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .bot-avt-fallback {{
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #F3F3F5;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        flex-shrink: 0;
    }}
    .bot-bubble {{
        background: #F3F3F5 !important;
        color: #333333 !important;
        border-radius: 16px 16px 16px 4px !important;
        padding: 9px 13px !important;
        max-width: 286px !important;
        font-size: 0.87rem !important;
        line-height: 1.65 !important;
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 500 !important;
        text-align: right !important;
        direction: rtl !important;
        word-wrap: break-word !important;
    }}
    .bot-ts {{
        font-size: 0.62rem !important;
        color: #9CA3AF !important;
        margin-top: 3px !important;
        direction: ltr !important;
        text-align: left !important;
        font-family: -apple-system, sans-serif !important;
        padding-right: 2px;
    }}

    /* User bubble: solid Vertebra purple, pure white text */
    .user-row {{
        display: flex;
        align-items: flex-end;
        justify-content: flex-end;
        margin-bottom: 10px;
        padding: 0 14px;
        direction: rtl;
    }}
    .user-bubble {{
        background: {PURPLE} !important;
        color: #FFFFFF !important;
        border-radius: 16px 16px 4px 16px !important;
        padding: 9px 13px !important;
        max-width: 286px !important;
        font-size: 0.87rem !important;
        line-height: 1.55 !important;
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 500 !important;
        text-align: right !important;
        direction: rtl !important;
        box-shadow: 0 2px 8px rgba(176,33,177,0.22) !important;
        word-wrap: break-word !important;
    }}
    .user-ts {{
        font-size: 0.62rem !important;
        color: rgba(255,255,255,0.72) !important;
        margin-top: 3px !important;
        direction: ltr !important;
        text-align: right !important;
        font-family: -apple-system, sans-serif !important;
    }}

    /* Chat messages wrapper — extra bottom pad prevents last bubble cramping */
    .chat-area {{
        padding: 14px 0 20px;
        background: #FFFFFF;
    }}

    /* ─── QUICK REPLIES ──────────────────────────────────────────────────── */
    .qr-label {{
        font-size: 0.72rem;
        color: #AAAAAA;
        font-weight: 600;
        text-align: right !important;
        direction: rtl !important;
        padding: 6px 16px 4px;
        font-family: 'Tajawal', sans-serif;
    }}
    .qr-row-wrapper {{
        padding: 2px 10px;
    }}

    /* Primary quick reply — solid Vertebra purple, white text */
    .st-key-qr_yes button {{
        background: {PURPLE} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 9999px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        padding: 6px 10px !important;
        box-shadow: 0 2px 6px rgba(176,33,177,0.18) !important;
        transition: all 0.18s ease !important;
        font-family: 'Tajawal', sans-serif !important;
        width: 100% !important;
        min-height: 34px !important;
        height: auto !important;
        line-height: 1.3 !important;
        white-space: normal !important;
    }}
    .st-key-qr_yes button:hover {{
        background: {PURPLE_DARK} !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(176,33,177,0.28) !important;
    }}

    /* Secondary quick reply — white bg, purple border, purple text */
    .st-key-qr_no button {{
        background: #FFFFFF !important;
        color: {PURPLE} !important;
        border: 1.5px solid {PURPLE} !important;
        border-radius: 9999px !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        padding: 6px 10px !important;
        font-family: 'Tajawal', sans-serif !important;
        width: 100% !important;
        min-height: 34px !important;
        height: auto !important;
        line-height: 1.3 !important;
        white-space: normal !important;
        transition: all 0.18s ease !important;
    }}
    .st-key-qr_no button:hover {{
        background: #F9F5FF !important;
        border-color: {PURPLE_DARK} !important;
    }}

    /* Suggested full-width reply — white bg, purple border, purple text */
    .st-key-qr_suggest button {{
        background: #FFFFFF !important;
        color: {PURPLE} !important;
        border: 1.5px solid {PURPLE} !important;
        border-radius: 9999px !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        padding: 7px 16px !important;
        font-family: 'Tajawal', sans-serif !important;
        width: 100% !important;
        min-height: 34px !important;
        height: auto !important;
        line-height: 1.3 !important;
        white-space: normal !important;
        transition: all 0.18s ease !important;
        margin-top: 4px !important;
    }}
    .st-key-qr_suggest button:hover {{
        background: #F9F5FF !important;
    }}

    /* ─── CHAT INPUT (Text Direction & Cursor overrides only) ───────────── */
    [data-testid="stChatInput"]:focus-within {{
        border-color: {PURPLE} !important;
        box-shadow: 0 0 0 3px rgba(176,33,177,0.08) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 0.87rem !important;
        caret-color: {PURPLE} !important;
    }}
    [data-testid="stChatInputTextArea"] textarea::placeholder {{
        color: #BBBBBB !important;
        font-family: 'Tajawal', sans-serif !important;
    }}

    /* Send arrow button — Vertebra purple circle */
    [data-testid="stChatInputSubmitButton"] button {{
        background: #9B26B6 !important;
        border: none !important;
        border-radius: 50% !important;
        transition: all 0.2s ease !important;
    }}
    [data-testid="stChatInputSubmitButton"] button:hover {{
        background: {PURPLE_DARK} !important;
        transform: scale(1.08) !important;
    }}
    [data-testid="stChatInputSubmitButton"] button svg {{
        fill: #FFFFFF !important;
    }}

    /* ─── ALERTS & SPINNER ───────────────────────────────────────────────── */
    .stAlert {{
        direction: rtl !important;
        text-align: right !important;
        border-radius: 10px !important;
        margin: 0 14px 8px !important;
        font-family: 'Tajawal', sans-serif !important;
    }}
    .stSpinner > div {{
        border-top-color: {PURPLE} !important;
    }}

    /* ─── FOOTER ─────────────────────────────────────────────────────────── */
    .widget-footer {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        padding: 8px 0 10px;
        margin-bottom: 5px !important;
        font-size: 0.65rem;
        color: #AAAAAA;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        direction: ltr;
        letter-spacing: 0.2px;
    }}
    .footer-logo {{
        width: 12px;
        height: 12px;
        border-radius: 50%;
        object-fit: cover;
        opacity: 0.75;
        vertical-align: middle;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Session State
# ─────────────────────────────────────────────────────────────────────────────
WELCOME_MSG: dict = {
    "role": "assistant",
    "content": "مرحباً بك! 👋 أنا **Vertebra AI**، مستشارك الذكي لاختيار أرقى العطور الخليجية.",
    "ts": datetime.now().strftime("%I:%M %p"),
}
if "messages" not in st.session_state:
    st.session_state.messages = [WELCOME_MSG]

# ─────────────────────────────────────────────────────────────────────────────
# 6. Header Row — brand (left) + ↻ and ✕ (right)
#    Uses st.columns so the buttons are real clickable Streamlit widgets
# ─────────────────────────────────────────────────────────────────────────────
col_brand, col_ref, col_ex = st.columns([8, 1, 1])

with col_brand:
    logo_img = (
        f'<img src="{LOGO_URI}" style="width:38px;height:38px;border-radius:50%;'
        f'object-fit:cover;border:1.5px solid #F0ABFC;" alt="Logo" />'
        if LOGO_URI
        else '<div style="width:38px;height:38px;border-radius:50%;background:#F3F3F5;'
             'display:flex;align-items:center;justify-content:center;font-size:1.2rem;">✨</div>'
    )
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;padding:12px 0 12px 14px;
                    background:#FFFFFF;direction:rtl;border-bottom:1px solid #F0F0F0;">
            <div style="position:relative;width:38px;height:38px;flex-shrink:0;">
                {logo_img}
                <span style="position:absolute;bottom:1px;right:1px;width:10px;height:10px;
                             background:#22C55E;border:2px solid #fff;border-radius:50%;"></span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.95rem;font-weight:800;color:#1F2937;
                            font-family:'Tajawal',sans-serif;line-height:1.2;">Vertebra AI</div>
                <div style="font-size:0.72rem;color:#22C55E;font-weight:600;
                            font-family:-apple-system,sans-serif;margin-top:1px;">We're online...</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_ref:
    if st.button("↻", key="btn_refresh", help="إعادة تعيين المحادثة / Reset"):
        st.session_state.messages = [
            dict(WELCOME_MSG, ts=datetime.now().strftime("%I:%M %p"))
        ]
        st.session_state.pop("pending_message", None)
        st.rerun()

with col_ex:
    if st.button("✕", key="btn_exit", help="مسح المحادثة / Clear"):
        st.session_state.messages = [
            dict(WELCOME_MSG, ts=datetime.now().strftime("%I:%M %p"))
        ]
        st.session_state.pop("pending_message", None)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 7. Message Renderer — custom HTML bubbles, no st.chat_message()
# ─────────────────────────────────────────────────────────────────────────────
def _safe_html(text: str) -> str:
    """Escape HTML entities and convert markdown bold + newlines."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br>")
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    return text


def render_messages(messages: list[dict]) -> str:
    bot_avatar = (
        f'<img src="{LOGO_URI}" class="bot-avt" alt="Vertebra AI" />'
        if LOGO_URI
        else '<div class="bot-avt-fallback">✨</div>'
    )
    parts = ['<div class="chat-area">']
    for msg in messages:
        ts = msg.get("ts", datetime.now().strftime("%I:%M %p"))
        body = _safe_html(msg["content"])
        if msg["role"] == "assistant":
            parts.append(
                f'<div class="bot-row">'
                f'  {bot_avatar}'
                f'  <div>'
                f'    <div class="bot-bubble">{body}</div>'
                f'    <div class="bot-ts">{ts}</div>'
                f'  </div>'
                f'</div>'
            )
        else:
            parts.append(
                f'<div class="user-row">'
                f'  <div>'
                f'    <div class="user-bubble">{body}</div>'
                f'    <div class="user-ts">{ts}</div>'
                f'  </div>'
                f'</div>'
            )
    parts.append("</div>")
    return "".join(parts)


st.markdown(render_messages(st.session_state.messages), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 8. Quick Replies — Primary (solid purple), Secondary (white border),
#    Suggested (full-width white border)
#    Clicking fires pending_message → st.rerun() → processed below
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="qr-label">ردود سريعة:</div>', unsafe_allow_html=True)

qr1, qr2 = st.columns([1, 1])
with qr1:
    if st.button("نعم، بالتأكيد", key="qr_yes", use_container_width=True):
        st.session_state.pending_message = "نعم، أريد المساعدة في اختيار عطر فاخر لديكم"
        st.rerun()
with qr2:
    if st.button("لا، شكراً لك", key="qr_no", use_container_width=True):
        st.session_state.pending_message = "شكراً، لا أحتاج مساعدة الآن"
        st.rerun()

if st.button("ما هي أشهر منتجاتكم؟", key="qr_suggest", use_container_width=True):
    st.session_state.pending_message = "ما هي العطور الأكثر مبيعاً وشعبيةً لديكم؟"
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 9. Chat Input (styled via CSS above — light grey bar, ☺ 📎 on left)
# ─────────────────────────────────────────────────────────────────────────────
chat_input = st.chat_input("اكتب رسالتك...")

# ─────────────────────────────────────────────────────────────────────────────
# 10. Resolve user input — quick-reply button or typed message
# ─────────────────────────────────────────────────────────────────────────────
pending = st.session_state.pop("pending_message", None)
user_input: Optional[str] = pending or (chat_input if chat_input else None)

# ─────────────────────────────────────────────────────────────────────────────
# 11. Process → FastAPI → store → rerun
# ─────────────────────────────────────────────────────────────────────────────
if user_input:
    ts_now = datetime.now().strftime("%I:%M %p")
    st.session_state.messages.append({"role": "user", "content": user_input, "ts": ts_now})

    with st.spinner("Vertebra AI يكتب..."):
        try:
            res = requests.post(
                API_URL,
                json={"message": user_input},
                timeout=API_TIMEOUT,
            )
            res.raise_for_status()
            reply: Optional[str] = res.json().get("reply", "عذراً، لم أتلقَّ رداً.")
        except requests.exceptions.ConnectionError:
            reply = None
            st.error("⚠️ تعذّر الاتصال بالخادم — تأكد من تشغيل FastAPI على المنفذ 8000.")
        except requests.exceptions.Timeout:
            reply = None
            st.error("⏱️ انتهت مهلة الانتظار. الخادم بطيء.")
        except requests.exceptions.HTTPError as exc:
            reply = None
            st.error(f"❌ خطأ {exc.response.status_code}: {exc.response.text}")
        except Exception as exc:
            reply = None
            st.error(f"❌ خطأ غير متوقع: {exc}")

    if reply:
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "ts": datetime.now().strftime("%I:%M %p"),
        })
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 12. Footer — muted, minimal, absolute bottom of widget
# ─────────────────────────────────────────────────────────────────────────────
footer_logo_tag = (
    f'<img src="{LOGO_URI}" class="footer-logo" alt="Vertebra" />'
    if LOGO_URI else ""
)
st.markdown(
    f'<div class="widget-footer">'
    f'Powered by <strong style="color:#8E8E93;margin-left:2px;">Vertebra</strong>'
    f'{footer_logo_tag}'
    f'</div>',
    unsafe_allow_html=True,
)
