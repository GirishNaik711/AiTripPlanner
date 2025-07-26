from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.agentic_workflow import GraphBuilder
from starlette.responses import JSONResponse
from pydantic import BaseModel
from collections import deque
from dotenv import load_dotenv
import os
import random
from openai import OpenAI
import re
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq


load_dotenv()

app = FastAPI()

MAX_MEMORY_WINDOW = 5
session_memory = {}

class QueryRequest(BaseModel):
    question: str
    session_id: str

POLITE_WORDS = {
    "thanks", "thank", "thx", "appreciate", "ok", "okay", "cool",
    "noted", "alright", "hi", "hello", "yo", "fine", "great", "nice",
    "welcome", "sure", "well", "yup", "yeah"
}

def is_trip_related(user_input: str) -> bool:
    cleaned = user_input.lower().strip()

    # 🔒 Fast check: Blocklisted soft/polite responses
    words = set(re.findall(r"\w+", cleaned))

    if cleaned in POLITE_WORDS:
        print(f"[Classifier] Blocklisted: {cleaned}")
        return False

    # 🧠 Smart fallback: LLM classifier
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """
You are a strict binary classifier. Respond ONLY with 'Yes' or 'No'.

Say 'Yes' ONLY if the message is a clear, respectful, and meaningful request related to **trip planning**, such as:
- Asking about destinations, itineraries, flights, hotels, restaurants, or transportation
- Questions about sightseeing, weather, local activities, or budgeting for a trip

Say 'No' if the message:
- Is a greeting ("hi", "hello")
- Is a polite response like "thanks", "thank you", "okay", "cool", "noted"
- Contains profanity or insults
- Is vague, irrelevant, or not a travel-related request

Only say 'Yes' or 'No'. No explanation.
"""
            },
            {"role": "user", "content": user_input}
        ]
    )

    result = response.choices[0].message.content.strip().lower()
    print(f"[Classifier] Input: {user_input} → Output: {result}")
    return result == "yes"


@app.get("/")
async def root():
    return {"message": "🧠 FastAPI Agentic Backend is up and running."}


@app.post("/query")
async def query_travel_agent(query: QueryRequest):
    try:
        user_input = query.question.strip()
        session_id = query.session_id.strip()

        # 🔐 Smart intent & toxicity filtering
        if not is_trip_related(user_input):
            rude_responses = [
                "Wow. You kiss your vacation goodbye with that mouth?",
                "Try saying something useful, genius.",
                "Did your brain short-circuit, or was that on purpose?",
                "Fascinating. Now say something that resembles a travel query."
            ]
            return {"answer": random.choice(rude_responses)}

        # 💾 Use memory window per session
        if session_id not in session_memory:
            session_memory[session_id] = deque(maxlen=MAX_MEMORY_WINDOW)

        session_memory[session_id].append(user_input)
        full_context = "\n".join(session_memory[session_id])

        # 🧠 Invoke rude agent via Groq LangGraph
        graph = GraphBuilder(model_provider="groq")
        react_app = graph()
        png_graph = react_app.get_graph().draw_mermaid_png()

        with open("my_graph.png", "wb") as f:
            f.write(png_graph)

        messages = {"messages": [full_context]}
        output = react_app.invoke(messages)

        if isinstance(output, dict) and "messages" in output:
            final_output = output["messages"][-1].content
        else:
            final_output = str(output)

        return {"answer": final_output}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
