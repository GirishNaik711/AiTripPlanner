# CLAUDE.md

FastAPI + LangGraph backend (`main.py`) and Streamlit UI (`app.py`). Dependencies live in `pyproject.toml`; `requirements.txt` is generated from it.

## Commands

```
uv venv
uv pip install -r requirements.txt -r requirements_streamlit.txt pytest httpx pip-audit
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
.venv\Scripts\streamlit.exe run app.py
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m tests.redteam_live
.venv\Scripts\python.exe -m pip_audit
uv pip compile pyproject.toml --universal --python-version 3.12 -o requirements.txt
```

## Notes

- Needs `GROQ_API_KEY` and `API_AUTH_TOKEN` in `.env`. Other keys are optional and a tool is left out when its key is missing. See the README table.
- Port 8000 may be taken on the owner's machine by another project. Use another port and set `BACKEND_URL`.
- All external HTTP goes through `utils/http.py:get_json`, which drops the request URL from errors because it contains API keys. Keep it that way.
- Tool argument types live in `utils/validation.py`.
- `.env*` files are deny-listed for Claude in the user's permissions, so `.env.example` has to be created by the user.
- Streamlit pins `pillow<13` and pillow 12 has advisories. Revisit when Streamlit allows 13.
