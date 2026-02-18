# ◈ AdaptiveRAG — Multiagent Frontend

A production-grade dark UI for the **Adaptive RAG multiagent pipeline** with two API endpoints:
- `POST /save-data-vectordb` — ingest URLs into the vector store
- `POST /agentic-query`      — run the LangGraph agent graph and return answers

---

## 📁 Folder Structure

```
Project_Agent/
│
├── logs/                           # Runtime log files
│
├── src/                            # All source code
│   ├── db/                         # Vector DB persistence layer
│   │   ├── __init__.py
│   │   └── save_doc_db.py          # SaveDocDB — embed & store docs
│   │
│   ├── graphs/                     # LangGraph graph definitions
│   │   ├── __init__.py
│   │   └── graph_builder.py        # GraphBuilder — assembles the agent graph
│   │
│   ├── llms/                       # LLM client wrappers
│   │   ├── __init__.py
│   │   └── llm_factory.py
│   │
│   ├── nodes/                      # Individual graph nodes
│   │   ├── __init__.py
│   │   ├── retrieve.py             # Vector DB retrieval
│   │   ├── grade_documents.py      # Relevance grader
│   │   ├── generate.py             # Answer generation
│   │   ├── rewrite_query.py        # Query rewriter
│   │   └── web_search.py           # Web search fallback
│   │
│   ├── states/                     # TypedDict state schemas
│   │   ├── __init__.py
│   │   └── graph_state.py
│   │
│   ├── tools/                      # Tool definitions (search, etc.)
│   │   ├── __init__.py
│   │   └── search_tool.py
│   │
│   ├── ui/                         # ← Frontend lives here
│   │   ├── index.html              # Main HTML shell (3 tabs)
│   │   ├── styles.css              # Dark industrial theme
│   │   └── app.js                  # Tab nav, API calls, trace rendering
│   │
│   ├── logger.py                   # Logging configuration
│   └── main.py                     # FastAPI route handlers
│
├── app.py                          # Entrypoint — uvicorn server launch
├── .env                            # API keys, model names, DB path
├── .gitignore
├── .python-version
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── request.json                    # Sample request payloads
└── README.md
```

---

## 🚀 Quick Start

### 1. Configure the API base URL

Open `src/ui/app.js` and set your FastAPI server address:

```js
// src/ui/app.js — line 7
const API_BASE = "http://localhost:8000"; // ← matches uvicorn in app.py
```

### 2. Enable CORS in FastAPI

Add this to `src/main.py` so the browser can reach the API:

```python
# src/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your serve URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Serve the UI as a static mount (recommended)

Mount `src/ui/` directly from FastAPI — no separate server needed:

```python
# src/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/ui", StaticFiles(directory="src/ui", html=True), name="ui")
# Then open: http://localhost:8000/ui
```

Or serve standalone with Python:

```bash
cd src/ui && python -m http.server 3000
# Then open: http://localhost:3000
```

### 4. (Optional) Add a health check endpoint

The status dot in the header pings `/health` every 15 seconds:

```python
# src/main.py
@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 5. Start the backend

```bash
# From project root
python app.py
# or
uvicorn src.main:app --reload --port 8000
```

---

## 🎛 Features

| Feature | Description |
|---|---|
| **Ingest Tab** | Add multiple URLs, configure chunk size / overlap / DB path, watch the 4-stage pipeline animate |
| **Query Tab** | Type a question, run the agent graph, see answer + source chips |
| **Agent Trace** | Real-time timeline of nodes the graph visited (retrieve → grade → rewrite → generate) |
| **State Inspector** | Pretty-printed JSON of the full LangGraph state with syntax highlighting |
| **Logs Tab** | Timestamped event feed, filterable by INFO / SUCCESS / ERROR |
| **API Status** | Live ping dot — green when backend is reachable |
| **Keyboard shortcut** | `Ctrl+Enter` / `⌘+Enter` submits the query |

---

## 🔌 Adapting to Your Graph State

The `inferNodeTrace()` function in `src/ui/app.js` maps LangGraph state keys to trace events.
Update it to match your actual state schema from `src/states/graph_state.py`:

```js
function inferNodeTrace(state) {
  const events = [];
  // Map your graph's node outputs to trace events
  if (state.documents)          events.push({ node: "retrieve",        status: "success", detail: "..." });
  if (state.filtered_docs)      events.push({ node: "grade_documents", status: "success", detail: "..." });
  if (state.rewritten_question) events.push({ node: "rewrite_query",   status: "success", detail: "..." });
  if (state.generation)         events.push({ node: "generate",        status: "success", detail: "..." });
  return events;
}
```

And update `renderAnswer()` to pull from your state's answer key:

```js
const text = state.generation || state.answer || state.output;
```

---

## 📦 Dependencies

**Zero** — pure HTML + CSS + vanilla JS. No build step, no npm, no bundler.
Drop the 3 files into `src/ui/` and you're done.