# 🤖 Project_Agent — Adaptive RAG with Multi-Agent Query System

A production-ready **Adaptive RAG (Retrieval-Augmented Generation)** system powered by **LangGraph** multi-agent orchestration. Features intelligent query routing, document grading, hallucination detection, and automatic query transformation — with a sleek dark-themed web UI.

[![Deploy to GCP](https://img.shields.io/badge/Deploy-GCP%20Cloud%20Run-4285F4?logo=google-cloud)](https://cloud.google.com/run)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B6B)](https://github.com/langchain-ai/langgraph)

---

## 🎯 What It Does

This system uses a **multi-agent graph** to intelligently answer questions by:

1. **Routing** — Decides whether to search your vector DB or the web
2. **Retrieving** — Pulls relevant documents from FAISS vector store
3. **Grading** — Filters out irrelevant documents using LLM scoring
4. **Generating** — Produces answers grounded in retrieved context
5. **Validating** — Checks for hallucinations and answer quality
6. **Transforming** — Rewrites queries if initial retrieval fails

**Live Demo:** [https://multi-agent-query-with-rag-xxx.run.app/ui](https://multi-agent-query-with-rag-257612295763.us-central1.run.app/ui)

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Route Question (LLM-based Router)                          │
│  ├─ "web_search"    → Web Search Tool                       │
│  └─ "vectorstore"   → FAISS Retriever                       │
└─────────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
  Web Search                      Retrieve Documents
        │                               │
        │                               ▼
        │                        Grade Documents
        │                               │
        │                   ┌───────────┴──────────┐
        │                   ▼                      ▼
        │            All Relevant           Not Relevant
        │                   │                      │
        │                   │                      ▼
        │                   │              Transform Query
        │                   │                      │
        │                   │                      └─────┐
        └───────────────────┼────────────────────────────┤
                            ▼                            │
                    Generate Answer ◄────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Grade Answer Quality         │
            ├─ Grounded? (Hallucination)   │
            ├─ Useful? (Answers question)  │
            └───────────────────────────────┘
                    │
        ┌───────────┼──────────────┐
        ▼           ▼              ▼
   Not Grounded   Useful      Not Useful
        │           │              │
     Regenerate     END      Transform Query
```

---

## 📁 Project Structure

```
Project_Agent/
│
├── .github/                        # Optional: Add for CI/CD auto-deploy
│   └── workflows/
│       └── deploy.yml              # GitHub Actions pipeline
│
├── src/
│   ├── db/
│   │   ├── __init__.py
│   │   ├── doc_vectordb.py         # SaveDocDB: embed & persist docs in FAISS
│   │   └── fiass_index/            # Vector DB storage (ephemeral on Cloud Run)
│   │
│   ├── graphs/
│   │   ├── __init__.py
│   │   └── graph_builder.py        # GraphBuilder: assembles LangGraph
│   │
│   ├── llms/
│   │   ├── __init__.py
│   │   └── llm.py                  # LLM: OpenAI + Groq model wrappers
│   │
│   ├── nodes/
│   │   ├── __init__.py
│   │   └── node.py                 # AgentNode: all graph node logic
│   │       ├── route_question()
│   │       ├── retriever()
│   │       ├── grade_documents()
│   │       ├── decide_to_generate()
│   │       ├── transform_query()
│   │       ├── generate()
│   │       └── grade_generation_v_documents_and_question()
│   │
│   ├── states/
│   │   ├── __init__.py
│   │   └── state.py                # GraphState + Pydantic schemas
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   └── tool.py                 # Tools: Tavily web search
│   │
│   ├── ui/                         # Frontend (vanilla JS, no build)
│   │   ├── app.js                  # API calls, trace rendering
│   │   ├── index.html              # 3 tabs: Ingest, Query, Logs
│   │   └── styles.css              # Dark industrial theme
│   │
│   ├── logger.py                   # Logging configuration
│   └── main.py                     # FastAPI app + routes
│
├── .dockerignore                   # Docker build exclusions
├── .env                            # API keys (local only, never committed)
├── .gitignore                      # Git exclusions
├── .python-version                 # Python version spec
├── app.py                          # Uvicorn entrypoint
├── Dockerfile                      # Container build instructions
├── notebook.ipynb                  # Jupyter notebook (experiments/testing)
├── pyproject.toml                  # Python project metadata
├── README.md                       # This file
├── request.json                    # Sample API request payloads
├── requirements.txt                # Python dependencies
└── uv.lock                         # UV package manager lock file
```

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/project-agent.git
cd project-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create `.env` file in project root:

```env
LANGCHAIN_API_KEY=your_langchain_key
LANGSMITH_API_KEY=your_langsmith_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
tavily_search_api=your_tavily_key
```

### 3. Run the Server

```bash
python app.py
```

Open browser: **http://localhost:8000/ui**

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/ui` | GET | Web interface (3 tabs: Ingest, Query, Logs) |
| `/health` | GET | Health check for monitoring |
| `/save-data-vectordb` | POST | Ingest URLs → embed → store in FAISS |
| `/agentic-query` | POST | Run multi-agent graph and return answer |

### Example: Ingest Documents

```bash
curl -X POST http://localhost:8000/save-data-vectordb \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/doc1", "https://example.com/doc2"],
    "chunk_size": 500,
    "chunk_overlap": 50
  }'
```

### Example: Query

```bash
curl -X POST http://localhost:8000/agentic-query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is LangGraph?"}'
```

---

## 🎛️ Frontend Features

The UI (`/ui`) provides a complete interface for the RAG pipeline:

### **Ingest Tab**
- Add multiple URLs dynamically
- Configure chunk size, overlap, and DB path
- Watch a 4-stage animated pipeline: Fetch → Split → Embed → Index
- Real-time success/error states per step

### **Query Tab**
- Natural language question input
- Live **Agent Trace** timeline showing graph execution:
  - `retrieve` → `grade_documents` → `transform_query` → `generate`
- **State Inspector** with syntax-highlighted JSON of full graph state
- Answer with source document chips
- Keyboard shortcut: `Ctrl+Enter` / `⌘+Enter` to submit

### **Logs Tab**
- Timestamped event feed (INFO / SUCCESS / ERROR)
- Filterable by log level
- Real-time updates from both ingest and query pipelines

---

## 🧠 How the Agent Graph Works

### Node Descriptions

| Node | Purpose | Logic |
|---|---|---|
| **route_question** | Decides retrieval strategy | LLM classifies query → `"web_search"` or `"vectorstore"` |
| **retriever** | Fetches from FAISS | Embeds query → retrieves top-k similar docs |
| **grade_documents** | Filters irrelevant docs | LLM scores each doc: `"yes"` (keep) or `"no"` (discard) |
| **decide_to_generate** | Checks if docs are sufficient | If all docs filtered → transform query; else → generate |
| **transform_query** | Rewrites query for better retrieval | LLM rephrases question to improve semantic match |
| **generate** | Produces answer | RAG chain: context + question → LLM → answer |
| **grade_generation** | Validates answer quality | 2-step check: (1) Grounded in docs? (2) Answers question? |
| **web_search** | Fallback for out-of-domain queries | Tavily API → fetches web results → formats as context |

### Edge Conditions

```python
# START → route_question
if route == "web_search":    → web_search → generate
if route == "vectorstore":   → retrieve → grade_documents

# grade_documents → decide_to_generate
if all_docs_filtered:        → transform_query → retrieve (loop)
else:                        → generate

# generate → grade_generation
if not_grounded:             → generate (retry)
if not_useful:               → transform_query → retrieve (loop)
if useful:                   → END
```

### Adaptive Behavior Examples

**Query:** "What are the latest iPhone features?"
```
route_question → "web_search" (not in vectorstore docs)
  → web_search (Tavily API)
  → generate
  → grade_generation: "useful" → END
```

**Query:** "Explain LangGraph conditional edges" (in docs)
```
route_question → "vectorstore"
  → retrieve (5 docs)
  → grade_documents (3 relevant, 2 filtered)
  → decide_to_generate: "generate"
  → generate
  → grade_generation:
      ├─ grounded? "yes"
      └─ useful? "yes" → END
```

**Query:** "What is XYZ?" (vague, retrieval fails)
```
route_question → "vectorstore"
  → retrieve (0 relevant docs after grading)
  → decide_to_generate: "transform_query"
  → transform_query ("What is XYZ?" → "Explain XYZ concept in detail")
  → retrieve (now finds relevant docs)
  → grade_documents → generate → END
```

---

## ☁️ Deployment (GCP Cloud Run)

### Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed
- Docker installed

### One-Time Setup

```bash
# 1. Login & set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable services
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# 3. Build & push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/project-agent

# 4. Deploy
gcloud run deploy project-agent \
  --image gcr.io/YOUR_PROJECT_ID/project-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "LANGCHAIN_API_KEY=xxx,LANGSMITH_API_KEY=xxx,GROQ_API_KEY=xxx,OPENAI_API_KEY=xxx,tavily_search_api=xxx"
```

### CI/CD with GitHub Actions

Every push to `main` auto-deploys via `.github/workflows/deploy.yml`.

**Setup once:**
1. Create GCP service account with Cloud Run Admin role
2. Download JSON key
3. Add to GitHub Secrets:
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY` (entire JSON key)
   - All API keys

**Then just:**
```bash
git add .
git commit -m "update"
git push origin main
# → Auto-builds & deploys to Cloud Run ✅
```

---

## 🔧 Configuration

### Models Used

| Component | Model | Provider | Purpose |
|---|---|---|
| Routing | `qwen/qwen3-32b` | Groq | Fast structured output for query classification |
| Grading | `qwen/qwen3-32b` | Groq | Document relevance scoring |
| Generation | `qwen/qwen3-32b` | Groq | Answer synthesis (can swap to `gpt-4o-mini`) |
| Embeddings | `text-embedding-3-large` | OpenAI | 1024-dim vector embeddings |

### Customization Points

**Change LLM models** — edit `src/nodes/node.py`:
```python
self.agent_node = AgentNode(
    model_openai="gpt-4o",      # for generation
    model_groq="llama-3.1-70b"  # for routing/grading
)
```

**Adjust chunk size** — in frontend or API:
```python
# src/main.py
doc_splits = savedocdb.doc_splits(
    chunk_size=1000,      # default: 500
    chunk_overlap=100     # default: 50
)
```

**Change vector DB path**:
```python
db_path = "./src/db/fiass_index"  # local or GCS bucket path
```

---

## 🐛 Known Limitations & Roadmap

### Current Limitations

| Issue | Workaround |
|---|---|
| **FAISS index is ephemeral on Cloud Run** | Each deploy resets vector DB. Use GCS bucket for persistence. |
| **No user authentication** | Add OAuth via FastAPI middleware |
| **No query history** | Store queries in Cloud SQL or Firestore |
| **Single FAISS index** | No multi-tenancy support yet |

### Roadmap

- [ ] Persistent vector DB via GCS or Pinecone
- [ ] User authentication & query history
- [ ] Streaming LLM responses (SSE)
- [ ] Multi-index support for different document collections
- [ ] Agent trace export (JSON/CSV)
- [ ] Fine-tuned embeddings for domain-specific docs

---

## 📊 Monitoring & Logs

### Local Logs

```bash
# Tail logs in real-time
tail -f logs/app.log
```

### Cloud Run Logs

```bash
# View live logs
gcloud run logs tail project-agent --region us-central1

# Filter by severity
gcloud run logs read project-agent --region us-central1 --filter="severity=ERROR"
```

### LangSmith Tracing

Every graph execution is traced in LangSmith (if `LANGSMITH_API_KEY` is set):
- View graph execution flow
- Debug node inputs/outputs
- Measure latency per node
- Track token usage

Access: https://smith.langchain.com

---

## 🛠️ Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Linting & Formatting

```bash
pip install black ruff

# Format code
black src/

# Lint
ruff check src/
```

### Adding New Nodes

1. Add node function to `src/nodes/node.py`:
```python
def my_new_node(self, state: GraphState):
    # Your logic here
    return {"new_key": "value"}
```

2. Register in `src/graphs/graph_builder.py`:
```python
self.graph.add_node("my_node", self.agent_node.my_new_node)
self.graph.add_edge("previous_node", "my_node")
```

3. Update `GraphState` in `src/states/state.py` if adding new state keys

---

## 📚 Tech Stack

| Category | Technology |
|---|---|
| **Framework** | FastAPI, Uvicorn |
| **Agent Orchestration** | LangGraph (StateGraph) |
| **LLMs** | OpenAI GPT-4o-mini, Groq (Qwen3-32B) |
| **Embeddings** | OpenAI `text-embedding-3-large` |
| **Vector DB** | FAISS (local) |
| **Web Search** | Tavily API |
| **Frontend** | Vanilla JS, CSS, HTML (zero build) |
| **Deployment** | GCP Cloud Run, Docker |
| **CI/CD** | GitHub Actions |
| **Monitoring** | LangSmith, Cloud Logging |

---


## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com) for LangGraph framework
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [Tavily](https://tavily.com) for web search API
- [Groq](https://groq.com) for blazing-fast LLM inference