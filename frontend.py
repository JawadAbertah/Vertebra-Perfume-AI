"""
frontend.py — AAA Luxury Perfume Bot | SaaS Demo UI v2.0
Dark luxury Arabic RTL chat interface powered by Streamlit.
Connects to FastAPI backend at http://127.0.0.1:8000/chat
"""

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config — MUST be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AAA Perfume | نور",
    page_icon="🌹",
    layout="wide",
    initial_sidebar_state="expanded",
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
# CSS — Tajawal font, RTL fix, dark luxury theme, hide Streamlit chrome
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Font: Tajawal ─────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap');

    /* ── RTL Fix: force horizontal text flow, prevent vertical stacking ───── */
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

    /* ── Page background ──────────────────────────────────────────────────── */
    .stApp {
        background-color: #0d0d0d !important;
    }

    /* ── Main content area padding ────────────────────────────────────────── */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px !important;
    }

    /* ── Sidebar ──────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #111111 !important;
        border-left: 1px solid #D4AF3730 !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
    }

    /* ── Sidebar suggestion buttons ───────────────────────────────────────── */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #1a1500 0%, #252000 100%) !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF3755 !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        text-align: right !important;
        direction: rtl !important;
        writing-mode: horizontal-tb !important;
        transition: all 0.2s ease !important;
        margin-bottom: 0.5rem !important;
        cursor: pointer !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #2a2200 0%, #3a3000 100%) !important;
        border-color: #D4AF37 !important;
        box-shadow: 0 0 14px #D4AF3740 !important;
        transform: translateX(-4px) !important;
        color: #f0d060 !important;
    }
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateX(-2px) scale(0.98) !important;
    }

    /* ── Chat bubbles ─────────────────────────────────────────────────────── */
    [data-testid="stChatMessageContent"] {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        writing-mode: horizontal-tb !important;
        unicode-bidi: embed !important;
        border-radius: 14px !important;
        padding: 0.9rem 1.2rem !important;
        font-size: 1.05rem !important;
        line-height: 1.85 !important;
    }

    /* User bubble — dark gold tint */
    [data-testid="stChatMessage"][data-message-author-role="user"]
    [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #1e1a00 0%, #2c2500 100%) !important;
        color: #f5e6c8 !important;
        border: 1px solid #D4AF3760 !important;
        box-shadow: inset 0 1px 0 #D4AF3720, 0 2px 8px #00000080 !important;
    }

    /* Assistant bubble — deep charcoal */
    [data-testid="stChatMessage"][data-message-author-role="assistant"]
    [data-testid="stChatMessageContent"] {
        background: #161616 !important;
        color: #e8e0d0 !important;
        border: 1px solid #2e2e2e !important;
        box-shadow: 0 2px 8px #00000060 !important;
    }

    /* Avatar icons */
    [data-testid="chatAvatarIcon-user"] svg {
        fill: #0d0d0d !important;
    }
    [data-testid="chatAvatarIcon-user"] {
        background-color: #D4AF37 !important;
        border-radius: 50% !important;
    }
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
        font-weight: 400 !important;
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

    /* Chat send button */
    [data-testid="stChatInputSubmitButton"] button {
        background-color: #D4AF37 !important;
        border-radius: 8px !important;
    }
    [data-testid="stChatInputSubmitButton"] button:hover {
        background-color: #f0d060 !important;
    }

    /* ── Alerts / errors ──────────────────────────────────────────────────── */
    .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tajawal', sans-serif !important;
        border-radius: 10px !important;
    }

    /* ── Divider ──────────────────────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid #D4AF3730 !important;
    }

    /* ── Spinner text ─────────────────────────────────────────────────────── */
    .stSpinner > div {
        border-top-color: #D4AF37 !important;
    }

    /* ── HIDE all Streamlit chrome ────────────────────────────────────────── */
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
# Sidebar — clickable suggested questions (st.button → pending_message)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<h2 style='color:{GOLD}; text-align:right; font-family:Tajawal,sans-serif;"
        f" font-size:1.3rem; margin-bottom:0.2rem;'>✨ أسئلة مقترحة</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#666; font-size:0.83rem; text-align:right;"
        " font-family:Tajawal,sans-serif; margin-bottom:0.8rem;'>"
        "اضغط على أي سؤال لإرساله مباشرةً</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    for question in SUGGESTIONS:
        if st.button(question, key=f"btn_{question}", use_container_width=True):
            st.session_state.pending_message = question
            st.rerun()

    st.divider()
    st.markdown(
        f"<div style='text-align:center; font-family:Tajawal,sans-serif;'>"
        f"<span style='color:{GOLD}; font-size:0.85rem;'>AAA Perfume Bot</span>"
        f"<br><span style='color:#444; font-size:0.75rem;'>v2.0 · مدعوم بالذكاء الاصطناعي 🤖</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Main — header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='text-align:center; padding:1.2rem 0 0.4rem;'>
        <div style='font-size:2.4rem; font-weight:700; color:{GOLD};
                    font-family:Tajawal,sans-serif; letter-spacing:2px;
                    text-shadow:0 0 24px #D4AF3750;'>
            🌹 &nbsp; AAA للعطور الفاخرة
        </div>
        <div style='font-size:1rem; color:#666; font-family:Tajawal,sans-serif; margin-top:0.4rem;'>
            مساعدك الذكي لاختيار أرقى العطور الخليجية
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    f"<hr style='border:none; border-top:1px solid {GOLD}30; margin:0.6rem 0 1rem;'>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Render chat history
# ─────────────────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────────────────────────────────────
# Resolve user input — sidebar button (pending_message) OR chat_input
# ─────────────────────────────────────────────────────────────────────────────
chat_input = st.chat_input("اكتب رسالتك هنا... ✍️")

pending = st.session_state.get("pending_message")
if pending:
    del st.session_state["pending_message"]
    user_input = pending
elif chat_input:
    user_input = chat_input
else:
    user_input = None

# ─────────────────────────────────────────────────────────────────────────────
# Process → call FastAPI → display reply
# ─────────────────────────────────────────────────────────────────────────────
if user_input:
    # Store & render user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call backend & render assistant reply
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
