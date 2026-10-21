import os
import re
import time
import uuid
import datetime

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "")
MAX_CHARS = 500
COOLDOWN_SECONDS = 3

EXAMPLES = [
    "Plan my Goa trip with zero effort.",
    "3 days in Lisbon on a tight budget.",
    "What's the weather like in Tokyo in April?",
]

STATUS_MESSAGES = {
    401: "The console has bad credentials for the backend. Whoever runs this needs to fix the API token.",
    403: "The console has bad credentials for the backend. Whoever runs this needs to fix the API token.",
    413: f"That message is too long. Keep it under {MAX_CHARS} characters.",
    422: f"The backend rejected that message. Keep it under {MAX_CHARS} characters and try again.",
    502: "The AI got confused by that. Rephrase it and try again.",
    503: "The AI is overloaded or unreachable right now. Try again in a minute.",
    504: "The AI took too long to answer. Try again, maybe with a simpler request.",
}
DEFAULT_ERROR = "Something broke on the backend. Try again in a moment."
IMAGE_MD = re.compile(r"!\[[^\]]*\]\([^)]*\)|!\[[^\]]*\]\[[^\]]*\]")

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

    [data-testid="stChatMessage"] {
        background-color: #0f172a;
        border: 1px solid #33ffcc;
        border-radius: 15px;
        box-shadow: 0 0 10px #33ffcc50;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #1a1a2e;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) p,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) li {
        color: #ff33a8;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
        overflow-wrap: anywhere;
    }
    [data-testid="stChatMessage"] table { display: block; overflow-x: auto; }

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

    @media (max-width: 640px) {
        .terminal-title { font-size: 20px; letter-spacing: 1px; }
        .terminal-sub { font-size: 12px; margin-top: 6px; }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='terminal-title'>RUDE AGENTIC TRAVEL CONSOLE 🛸</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>‘Cos apparently your species can’t plan vacations without me <span class='cursor'></span></div>", unsafe_allow_html=True)

if not API_AUTH_TOKEN:
    st.error("API_AUTH_TOKEN is not set. Add it to .env (same value the backend uses) and restart.")
    st.stop()


def new_chat():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.pending = None


def stamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def ask_backend(question: str):
    """Returns (text, is_error). Never returns raw backend or exception text."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": question, "session_id": st.session_state.session_id},
            headers={"X-API-Key": API_AUTH_TOKEN},
            timeout=(5, 120),
        )
    except requests.Timeout:
        return "The backend took too long to answer. It may be waking up, so try again in a minute.", True
    except requests.RequestException:
        return "Can't reach the backend. Check that it is running and that BACKEND_URL is right.", True

    if response.status_code == 200:
        try:
            answer = response.json().get("answer")
        except ValueError:
            answer = None
        if isinstance(answer, str) and answer.strip():
            return IMAGE_MD.sub("", answer), False
        return "The backend sent back something unreadable.", True

    if response.status_code == 429:
        wait = response.headers.get("Retry-After", "60")
        wait = wait if wait.isdigit() else "60"
        return f"Too many requests. Wait about {wait} seconds and try again.", True
    return STATUS_MESSAGES.get(response.status_code, DEFAULT_ERROR), True


def queue_question(question: str):
    if time.monotonic() - st.session_state.last_sent < COOLDOWN_SECONDS:
        st.toast("Easy there. One request at a time.")
        return
    st.session_state.last_sent = time.monotonic()
    st.session_state.chat_history.append({"sender": "user", "message": question, "time": stamp(), "error": False})
    st.session_state.pending = question
    st.rerun()


if "session_id" not in st.session_state:
    new_chat()
if "last_sent" not in st.session_state:
    st.session_state.last_sent = 0.0

busy = st.session_state.pending is not None

if st.session_state.chat_history:
    if st.button("New chat", disabled=busy):
        new_chat()
        st.rerun()
else:
    st.caption("Pick one, or type your own below:")
    for example in EXAMPLES:
        if st.button(example, key=f"example-{example}", use_container_width=True, disabled=busy):
            queue_question(example)

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message("user" if msg["sender"] == "user" else "assistant"):
        if msg["sender"] == "user":
            st.text(msg["message"])
        elif msg["error"]:
            st.error(msg["message"])
        else:
            st.markdown(msg["message"])
        st.caption(msg["time"])

if st.session_state.pending:
    with st.chat_message("assistant"):
        with st.spinner("Compiling your lazy request... (a sleeping server can take up to a minute)"):
            text, is_error = ask_backend(st.session_state.pending)
    st.session_state.chat_history.append({"sender": "ai", "message": text, "time": stamp(), "error": is_error})
    st.session_state.pending = None
    st.rerun()

question = st.chat_input("e.g., Plan my Goa trip with zero effort.", max_chars=MAX_CHARS, disabled=busy)
if question and question.strip():
    queue_question(question.strip())

# Footer
st.markdown("""
    <hr style="border: 1px solid #33ffcc; margin-top: 40px;"/>
    <div class='footer'>
        made by <span style='color:#33ffcc;'>Girish</span> to impress hiring managers.<br>
        <span style='font-size:12px;'>© 2025 RUDE Labs | All bugs are features.</span>
    </div>
""", unsafe_allow_html=True)
