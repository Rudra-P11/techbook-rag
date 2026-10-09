import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, documents, jobs, chat
from app.retrieval.lexical_search import lexical_search

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("techbook_rag")

app = FastAPI(
    title="TechBook RAG API",
    description="Intelligent Technical Knowledge Assistant for SQL, Python, ML & Deep Learning",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(jobs.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing TechBook RAG application...")
    settings.ensure_directories()
    
    # Pre-warm local embedding model so queries never suffer cold-start latency
    from app.ingestion.embedder import embedder
    logger.info("Pre-warming local SentenceTransformer model in memory...")
    embedder._load_model()
    embedder.embed_query("warmup query")
    
    # Pre-warm BM25 index in memory
    lexical_search.refresh_index()
    logger.info("TechBook RAG API startup complete. Model and indexes fully pre-warmed.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
