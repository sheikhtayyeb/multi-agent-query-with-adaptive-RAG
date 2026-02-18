import os
from dotenv import load_dotenv
from src.logger import get_logger
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.db.doc_vectordb import SaveDocDB
from src.graphs.graph_builder import GraphBuilder

load_dotenv()
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")  # ✅ fixed typo
os.environ["GROQ_API_KEY"]      = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["OPENAI_API_KEY"]    = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"]    = os.getenv("tavily_search_api")

app = FastAPI()
logger = get_logger(__name__)
db_path = "./src/db/fiass_index"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return RedirectResponse(url="/ui")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/save-data-vectordb")
async def save_vectordb(request: Request):
    data = await request.json()
    logger.info("Saving_url_data_in_vectordb_started")

    urls = data.get("urls", "")
    savedocdb = SaveDocDB(embd_model="text-embedding-3-large", vector_dimensions=1024)
    doc_list   = savedocdb.doc_list(urls)
    doc_splits = savedocdb.doc_splits(chunk_size=500, chunk_overlap=50, doc_list=doc_list)
    savedocdb.save_vectordb(doc_splits, path=db_path)

    logger.info("Saving_url_data_in_vectordb successfully done")
    return {"status": "success", "message": "Documents vectorised and stored successfully"}  # ✅ added

@app.post("/agentic-query")
async def agentic_query(request: Request):
    data = await request.json()
    question = data.get("question", "")
    graph_builder = GraphBuilder()
    graph = graph_builder.build_graph()
    state = graph.invoke({"question": question})
    return {"data": state}

# ✅ Mount AFTER all routes
app.mount("/ui", StaticFiles(directory="src/ui", html=True), name="ui")