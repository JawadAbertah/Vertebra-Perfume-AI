"""
frontend.py — AAA Luxury Perfume Bot | SaaS Demo UI v3.0
Dark luxury Arabic RTL chat interface powered by Streamlit.
Layout: st.columns([3, 1]) — no st.sidebar.
Connects to FastAPI backend at http://127.0.0.1:8000/chat
"""

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config — no sidebar
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AAA Perfume | نور",
    page_icon="🌹",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
API_URL     = "http://127.0.0.1:8000/chat"
API_TIMEOUT = 30
GOLD        = "#D4AF37"

SUGGESTIONS = [
    "ما هي العطور المتاحة لديكم؟",
    "ما سعر عطر نفحة الذهب؟",
    "ما هي مكونات عطر مسك الجنة؟",
    "كم يستغرق التوصيل إلى الرياض؟",
    "هل الشحن مجاني عند الطلب؟",
    "ما مدة ثبات عطر عود الملكي؟",
]

# ─────────────────────────────────────────────────────────────────────────────
# CSS — RTL fix, Tajawal, dark luxury, hide ALL sidebar artifacts
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Font: Tajawal ─────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap');

    /* ── RTL Fix ──────────────────────────────────────────────────────────── */
    html, body, [class*="css"], .stApp {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    p, span, div, label, button, h1, h2, h3, h4, h5, h6, li, a {
        writing-mode: horizontal-tb !important;
        text-orientation: mixed !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
    }
    textarea, input {
        writing-mode: horizontal-tb !important;
        unicode-bidi: embed !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
    }

    /* ── Page & block background ──────────────────────────────────────────── */
    .stApp {
        background-color: #0d0d0d !important;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }

    /* ── NUKE the sidebar and its collapsed toggle line completely ─────────── */
    section[data-testid="stSidebar"]              { display: none !important; }
    [data-testid="stSidebarCollapsedControl"]      { display: none !important; }
    [data-testid="collapsedControl"]               { display: none !important; }
    button[kind="header"]                          { display: none !important; }

    /* ── Column gap & borders ─────────────────────────────────────────────── */
    [data-testid="stColumns"] {
        gap: 1rem !important;
        align-items: flex-start !important;
    }
    /* Remove any default column dividers */
    [data-testid="stColumns"] > div::before,
    [data-testid="stColumns"] > div::after {
        display: none !important;
    }

    /* ── Suggestions panel (right column) ────────────────────────────────── */
    .suggestions-panel {
        background: #111111;
        border: 1px solid #D4AF3722;
        border-radius: 14px;
        padding: 1rem 0.75rem 1.2rem;
        position: sticky;
        top: 1rem;
    }
    .suggestions-title {
        color: #D4AF37;
        font-family: 'Tajawal', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        text-align: right;
        margin-bottom: 0.2rem;
    }
    .suggestions-hint {
        color: #555;
        font-family: 'Tajawal', sans-serif;
        font-size: 0.8rem;
        text-align: right;
        margin-bottom: 0.8rem;
        border-bottom: 1px solid #D4AF3718;
        padding-bottom: 0.6rem;
    }

    /* ── Suggestion buttons ───────────────────────────────────────────────── */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #1a1500 0%, #252000 100%) !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF3745 !important;
        border-radius: 10px !important;
        padding: 0.55rem 0.9rem !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        text-align: right !important;
        direction: rtl !important;
        writing-mode: horizontal-tb !important;
        transition: all 0.2s ease !important;
        margin-bottom: 0.45rem !important;
        cursor: pointer !important;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.5 !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2a2200 0%, #3a3000 100%) !important;
        border-color: #D4AF37 !important;
        box-shadow: 0 0 12px #D4AF3735 !important;
        color: #f0d060 !important;
        transform: translateX(3px) !important;
    }
    .stButton > button:active {
        transform: translateX(1px) scale(0.98) !important;
    }

    /* ── Chat bubbles ─────────────────────────────────────────────────────── */
    [data-testid="stChatMessageContent"] {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        writing-mode: horizontal-tb !important;
        unicode-bidi: embed !important;
        border-radius: 14px !important;
        padding: 0.85rem 1.1rem !important;
        font-size: 1.03rem !important;
        line-height: 1.85 !important;
    }

    /* User bubble */
    [data-testid="stChatMessage"][data-message-author-role="user"]
    [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #1e1a00 0%, #2c2500 100%) !important;
        color: #f5e6c8 !important;
        border: 1px solid #D4AF3760 !important;
        box-shadow: inset 0 1px 0 #D4AF3720, 0 2px 8px #00000080 !important;
    }

    /* Assistant bubble */
    [data-testid="stChatMessage"][data-message-author-role="assistant"]
    [data-testid="stChatMessageContent"] {
        background: #161616 !important;
        color: #e8e0d0 !important;
        border: 1px solid #2a2a2a !important;
        box-shadow: 0 2px 8px #00000060 !important;
    }

    /* Avatars */
    [data-testid="chatAvatarIcon-user"] {
        background-color: #D4AF37 !important;
        border-radius: 50% !important;
    }
    [data-testid="chatAvatarIcon-user"] svg { fill: #0d0d0d !important; }
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #1a1a1a !important;
        border: 1px solid #D4AF3740 !important;
        border-radius: 50% !important;
    }

    /* ── Chat input ───────────────────────────────────────────────────────── */
    [data-testid="stChatInputTextArea"] textarea {
        direction: rtl !important;
        text-align: right !important;
        writing-mode: horizontal-tb !important;
        unicode-bidi: embed !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 1rem !important;
        background: #141414 !important;
        color: #f0ead8 !important;
        border: 1px solid #D4AF3755 !important;
        border-radius: 12px !important;
        caret-color: #D4AF37 !important;
    }
    [data-testid="stChatInputTextArea"] textarea::placeholder {
        color: #555 !important;
        font-family: 'Tajawal', sans-serif !important;
    }
    [data-testid="stChatInputTextArea"] textarea:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 10px #D4AF3740 !important;
        outline: none !important;
    }
    [data-testid="stChatInputSubmitButton"] button {
        background-color: #D4AF37 !important;
        border-radius: 8px !important;
        border: none !important;
    }
    [data-testid="stChatInputSubmitButton"] button:hover {
        background-color: #f0d060 !important;
    }

    /* ── Alerts ───────────────────────────────────────────────────────────── */
    .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
        border-radius: 10px !important;
    }

    /* ── Spinner ──────────────────────────────────────────────────────────── */
    .stSpinner > div { border-top-color: #D4AF37 !important; }

    /* ── Dividers ─────────────────────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid #D4AF3725 !important;
        margin: 0.6rem 0 !important;
    }

    /* ── HIDE ALL Streamlit chrome ────────────────────────────────────────── */
    #MainMenu                       { display: none !important; }
    header                          { display: none !important; }
    footer                          { display: none !important; }
    [data-testid="stToolbar"]       { display: none !important; }
    [data-testid="stDecoration"]    { display: none !important; }
    [data-testid="stStatusWidget"]  { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "أهلاً وسهلاً! 🌹 أنا **نور**، مساعدتك الشخصية في متجر **AAA** للعطور الفاخرة.  \n"
                "كيف يمكنني خدمتك اليوم؟"
            ),
        }
    ]

# ─────────────────────────────────────────────────────────────────────────────
# Full-width header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='text-align:center; padding:1rem 0 0.5rem;'>
        <div style='font-size:2.2rem; font-weight:700; color:{GOLD};
                    font-family:Tajawal,sans-serif; letter-spacing:2px;
                    text-shadow:0 0 24px #D4AF3750;'>
            🌹 &nbsp; AAA للعطور الفاخرة
        </div>
        <div style='font-size:0.95rem; color:#555; font-family:Tajawal,sans-serif;
                    margin-top:0.35rem;'>
            مساعدك الذكي لاختيار أرقى العطور الخليجية
        </div>
    </div>
    <hr style='border:none; border-top:1px solid {GOLD}25; margin:0.6rem 0 0.8rem;'>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Column layout — [chat 75%] | [suggestions 25%]
# ─────────────────────────────────────────────────────────────────────────────
col_chat, col_suggest = st.columns([3, 1])

# ── Right column: Suggestions panel ──────────────────────────────────────────
with col_suggest:
    st.markdown(
        """
        <div class="suggestions-panel">
            <div class="suggestions-title">✨ أسئلة مقترحة</div>
            <div class="suggestions-hint">اضغط على أي سؤال لإرساله مباشرةً</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for question in SUGGESTIONS:
        if st.button(question, key=f"btn_{question}", use_container_width=True):
            st.session_state.pending_message = question
            st.rerun()

    st.markdown(
        f"<div style='text-align:center; margin-top:1rem; font-family:Tajawal,sans-serif;'>"
        f"<span style='color:#333; font-size:0.75rem;'>v3.0 · مدعوم بالذكاء الاصطناعي</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

# ── Left column: Chat history ─────────────────────────────────────────────────
with col_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ─────────────────────────────────────────────────────────────────────────────
# Chat input — always at root level (Streamlit pins it to page bottom)
# ─────────────────────────────────────────────────────────────────────────────
chat_input = st.chat_input("اكتب رسالتك هنا... ✍️")

# ─────────────────────────────────────────────────────────────────────────────
# Resolve user input: sidebar button (pending_message) OR manual chat_input
# ─────────────────────────────────────────────────────────────────────────────
pending = st.session_state.get("pending_message")
if pending:
    del st.session_state["pending_message"]
    user_input = pending
elif chat_input:
    user_input = chat_input
else:
    user_input = None

# ─────────────────────────────────────────────────────────────────────────────
# Process → call FastAPI → display reply (appended to col_chat)
# ─────────────────────────────────────────────────────────────────────────────
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Re-enter col_chat to append new messages below existing history
    with col_chat:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("جارٍ التفكير... 💭"):
                try:
                    response = requests.post(
                        API_URL,
                        json={"message": user_input},
                        timeout=API_TIMEOUT,
                    )
                    response.raise_for_status()
                    reply = response.json().get("reply", "عذراً، لم أتلقَّ رداً من الخادم.")

                except requests.exceptions.ConnectionError:
                    reply = None
                    st.error(
                        "⚠️ **تعذّر الاتصال بالخادم.**  \n"
                        "يرجى التأكد من تشغيل خادم FastAPI على المنفذ 8000."
                    )
                except requests.exceptions.Timeout:
                    reply = None
                    st.error("⏱️ **انتهت مهلة الانتظار.** الخادم يستغرق وقتاً أطول من المعتاد.")
                except requests.exceptions.HTTPError as exc:
                    reply = None
                    st.error(
                        f"❌ **خطأ من الخادم:** {exc.response.status_code}  \n{exc.response.text}"
                    )
                except Exception as exc:
                    reply = None
                    st.error(f"❌ **خطأ غير متوقع:** {exc}")

            if reply:
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
