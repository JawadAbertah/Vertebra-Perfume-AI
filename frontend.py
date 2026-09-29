"""
frontend.py — Streamlit Arabic RTL Chat UI for AAA Luxury Perfume Bot
Connects to the FastAPI backend at http://127.0.0.1:8000/chat
"""

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AAA عطور | مساعد الذكاء الاصطناعي",
    page_icon="🌹",
    layout="centered",
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000/chat"
API_TIMEOUT = 30  # seconds

# ─────────────────────────────────────────────────────────────────────────────
# RTL + Arabic styling
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* ── Global RTL & font ───────────────────────────────────────── */
        html, body, [class*="css"] {
            direction: rtl;
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }

        /* ── Page background ─────────────────────────────────────────── */
        .stApp {
            background: linear-gradient(135deg, #1a0a00 0%, #2d1200 60%, #1a0a00 100%);
        }

        /* ── Header banner ───────────────────────────────────────────── */
        .aaa-header {
            text-align: center;
            padding: 2rem 1rem 1rem;
            color: #f5c842;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 2px;
            text-shadow: 0 0 18px rgba(245, 200, 66, 0.5);
        }
        .aaa-sub {
            text-align: center;
            color: #c9a96e;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        /* ── Chat message bubbles ────────────────────────────────────── */
        [data-testid="stChatMessageContent"] {
            direction: rtl;
            text-align: right;
            border-radius: 16px;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            line-height: 1.7;
        }

        /* User bubble */
        [data-testid="stChatMessage"][data-message-author-role="user"]
        [data-testid="stChatMessageContent"] {
            background: linear-gradient(135deg, #7b3f00, #5c2d00);
            color: #fff8f0;
            border: 1px solid #c9a96e55;
        }

        /* Assistant bubble */
        [data-testid="stChatMessage"][data-message-author-role="assistant"]
        [data-testid="stChatMessageContent"] {
            background: linear-gradient(135deg, #1f1000, #2e1800);
            color: #f5e6cc;
            border: 1px solid #c9a96e33;
        }

        /* ── Chat input box ──────────────────────────────────────────── */
        [data-testid="stChatInputTextArea"] textarea {
            direction: rtl;
            text-align: right;
            background: #1f1000;
            color: #f5e6cc;
            border: 1px solid #c9a96e;
            border-radius: 12px;
            font-size: 1rem;
        }

        /* ── Error / info boxes ──────────────────────────────────────── */
        .stAlert {
            direction: rtl;
            text-align: right;
            border-radius: 12px;
        }

        /* ── Divider ─────────────────────────────────────────────────── */
        hr { border-color: #c9a96e33; }

        /* ── Hide Streamlit branding ─────────────────────────────────── */
        #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="aaa-header">🌹 AAA للعطور الفاخرة</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="aaa-sub">مساعدك الذكي لاختيار أرقى العطور الخليجية</div>',
    unsafe_allow_html=True,
)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Session state — chat history
# ─────────────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "أهلاً وسهلاً! 🌹 أنا نور، مساعدتك في متجر AAA للعطور الفاخرة. "
                "كيف يمكنني مساعدتك اليوم؟"
            ),
        }
    ]

# ─────────────────────────────────────────────────────────────────────────────
# Render chat history
# ─────────────────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────────────────────────────────────
# Chat input & API call
# ─────────────────────────────────────────────────────────────────────────────
if user_input := st.chat_input("اكتب رسالتك هنا... ✍️"):

    # 1. Show & store user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Call FastAPI backend
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
                    "⚠️ تعذّر الاتصال بالخادم. "
                    "يرجى التأكد من تشغيل خادم FastAPI على المنفذ 8000."
                )

            except requests.exceptions.Timeout:
                reply = None
                st.error("⏱️ انتهت مهلة الانتظار. الخادم يستغرق وقتاً أطول من المعتاد.")

            except requests.exceptions.HTTPError as exc:
                reply = None
                st.error(f"❌ خطأ من الخادم: {exc.response.status_code} — {exc.response.text}")

            except Exception as exc:
                reply = None
                st.error(f"❌ خطأ غير متوقع: {exc}")

        if reply:
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — quick tips
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💡 أسئلة مقترحة")
    suggestions = [
        "ما هي العطور المتاحة؟",
        "ما سعر عطر نفحة الذهب؟",
        "كم يستغرق التوصيل إلى الرياض؟",
        "ما هي مكونات مسك الجنة؟",
        "هل الشحن مجاني؟",
    ]
    for tip in suggestions:
        st.markdown(f"- *{tip}*")

    st.divider()
    st.markdown(
        "<div style='text-align:center; color:#c9a96e; font-size:0.8rem;'>"
        "AAA Perfume Bot v1.0<br>مدعوم بالذكاء الاصطناعي 🤖"
        "</div>",
        unsafe_allow_html=True,
    )
