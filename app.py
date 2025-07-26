import streamlit as st
import requests
import datetime
import uuid
from streamlit_lottie import st_lottie
import json

BASE_URL = "https://aitripplanner-m8cm.onrender.com"

st.set_page_config(
    page_title="RUDE Agentic Travel Planner",
    page_icon="🛸",
    layout="centered",
)

# SCIFI CSS + Footer Animation
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    html, body, [class*="css"] {
        background-color: #0a0f1c;
        color: #33ffcc;
        font-family: 'Share Tech Mono', monospace;
    }

    .stTextInput input {
        background-color: #111827;
        color: #33ffcc;
        border: 1px solid #33ffcc;
    }

    .stButton button {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        color: #33ffcc;
        border-radius: 8px;
        border: 1px solid #33ffcc;
        font-weight: bold;
        transition: 0.3s ease;
    }

    .stButton button:hover {
        background-color: #33ffcc;
        color: #0a0f1c;
    }

    .chat-bubble {
        padding: 12px 18px;
        margin: 10px 0;
        border-radius: 15px;
        max-width: 85%;
        font-size: 16px;
        border: 1px solid #33ffcc;
        box-shadow: 0 0 10px #33ffcc50;
    }
    .user-bubble {
        background-color: #0f172a;
        color: #33ffcc;
        margin-left: auto;
        text-align: right;
    }
    .ai-bubble {
        background-color: #1a1a2e;
        color: #ff33a8;
        margin-right: auto;
        text-align: left;
    }
    .timestamp {
        font-size: 11px;
        color: #8899a6;
        text-align: center;
        margin-top: -5px;
        margin-bottom: 10px;
    }

    .terminal-title {
        font-size: 26px;
        color: #33ffcc;
        text-align: center;
        margin-bottom: 0;
        text-shadow: 0 0 5px #33ffcc;
        letter-spacing: 2px;
    }

    .terminal-sub {
        font-size: 14px;
        text-align: center;
        color: #ff33a8;
        margin-top: -10px;
    }

    .cursor {
        display: inline-block;
        width: 10px;
        height: 20px;
        background-color: #33ffcc;
        animation: blink 1s infinite;
        margin-left: 2px;
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }

    .footer {
        text-align: center;
        font-size: 14px;
        color: #8899a6;
        padding: 20px 10px 40px;
        animation: fadeUp 1.5s ease-out;
    }

    @keyframes fadeUp {
        0% {
            opacity: 0;
            transform: translateY(20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='terminal-title'>RUDE AGENTIC TRAVEL CONSOLE 🛸</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>‘Cos apparently your species can’t plan vacations without me <span class='cursor'></span></div>", unsafe_allow_html=True)

# Initialize session_id and history
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat input
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Command Input", placeholder="e.g., Plan my Goa trip with zero effort.", label_visibility="collapsed")
    send_button = st.form_submit_button("Launch")

# Handle submission
if send_button and user_input.strip():
    st.session_state.chat_history.append({
        "sender": "user",
        "message": user_input,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    try:
        with st.spinner("Compiling your lazy request..."):
            response = requests.post(f"{BASE_URL}/query", json={
                "question": user_input,
                "session_id": st.session_state.session_id
            })

        if response.status_code == 200:
            ai_response = response.json().get("answer", "Ugh. Here's what I found. You're welcome.")
        else:
            ai_response = f"Backend error ({response.status_code}): {response.text}"

    except Exception as e:
        ai_response = f"System Fault: Your error broke my circuits ({e})"

    st.session_state.chat_history.append({
        "sender": "ai",
        "message": ai_response,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })

# Display chat history
for msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if msg["sender"] == "user" else "ai-bubble"
    st.markdown(f"""
        <div class='chat-bubble {bubble_class}'>{msg['message']}</div>
        <div class='timestamp'>{msg['time']}</div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
    <hr style="border: 1px solid #33ffcc; margin-top: 40px;"/>
    <div class='footer'>
        made by <span style='color:#33ffcc;'>Girish</span> to impress hiring managers.<br>
        <span style='font-size:12px;'>© 2025 RUDE Labs | All bugs are features.</span>
    </div>
""", unsafe_allow_html=True)
