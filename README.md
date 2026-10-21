# AI Trip Planner

A rude travel agent. FastAPI backend running a LangGraph agent (Groq) with weather, place search, currency and expense tools, plus a Streamlit chat UI.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Groq API key

## Install

```
uv venv
uv pip install -r requirements.txt -r requirements_streamlit.txt
```

## Config

Create a `.env` in the project root. Never commit it.

```
GROQ_API_KEY=
API_AUTH_TOKEN=
BACKEND_URL=http://127.0.0.1:8000
TAVILY_API_KEY=
GPLACE_API_KEY=
OPENWEATHERMAP_API_KEY=
EXCHANGE_RATE_API_KEY=
RATE_LIMIT_PER_MIN=10
GLOBAL_LIMIT_PER_HOUR=200
```

| Variable | Needed | Used for |
|---|---|---|
| `GROQ_API_KEY` | yes | The agent and the on-topic check |
| `API_AUTH_TOKEN` | yes | Shared secret (16+ characters) the UI sends to the backend. The backend won't start without it. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `BACKEND_URL` | UI only | Where the UI finds the backend |
| `TAVILY_API_KEY`, `GPLACE_API_KEY` | no | Attractions, restaurants, activities, transport. Skipped if unset |
| `OPENWEATHERMAP_API_KEY` | no | Weather tools. Skipped if unset |
| `EXCHANGE_RATE_API_KEY` | no | Currency conversion (exchangerate-api.com). Skipped if unset |
| `RATE_LIMIT_PER_MIN`, `GLOBAL_LIMIT_PER_HOUR` | no | Per-IP and overall request caps |

Only the Groq key is needed to chat. Without the others the agent has no weather, place or currency data and says so.

## Usage

Backend:

```
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

UI, in a second terminal:

```
.venv\Scripts\streamlit.exe run app.py
```

If port 8000 is taken, pick another and set `BACKEND_URL` to match.

## Tests

```
uv pip install pytest httpx
.venv\Scripts\python.exe -m pytest
```

The tests use stubbed models and tools, so they need no keys or network.

`tests/redteam_live.py` sends about 30 hostile and off-topic prompts to the real model and prints a pass/fail table. It needs the Groq key and the token in `.env`:

```
.venv\Scripts\python.exe -m tests.redteam_live
```

## Security notes

- `/query` needs the `X-API-Key` header, is rate limited, and caps message size and concurrent runs. `/docs` is off.
- Messages are normalized, then checked by a Groq classifier that must answer exactly "yes". Anything else, or a provider error, refuses the message.
- Replies are stripped of HTML, images and `<think>` blocks and checked for system prompt leaks before they leave the API. The UI escapes everything it renders.
- Tool arguments are validated. Upstream error text is never passed on, because it can contain API keys.
- The UI is public if you deploy it, so anyone can spend your Groq credits through it. The rate limits cap that. Set a spend limit with your provider as well.
- Behind a proxy such as Render, uvicorn only trusts forwarded addresses from `127.0.0.1` by default. Pass `--forwarded-allow-ips` with the proxy's address so the per-IP limit sees real clients. Until then, the overall hourly cap is what protects you.
- Streamlit pins `pillow<13`, which has known advisories (`pip-audit`). The UI never decodes images.

## Known gaps

- Tools without a key are not exercised against the real services, so weather, places and currency are tested with mocked responses only.
- The `exception/` and `logger/` packages are empty and unused.
