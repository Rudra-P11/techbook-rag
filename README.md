# TechBook RAG — Intelligent Technical Knowledge Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-red.svg)](https://streamlit.io)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-orange.svg)](https://qdrant.tech)
[![Live Interactive Showcase](https://img.shields.io/badge/Interactive%20Showcase-Live%20Architecture%20%26%20Simulations-c2593f.svg)](https://rudra-p11.github.io/techbook-rag/)
[![Empirical Case Study](https://img.shields.io/badge/Case%20Study-RRF%20k%3D60%20Forensic%20Analysis-3d7a46.svg)](https://rudra-p11.github.io/techbook-rag/case_study_rrf_retrieval.html)

> 🌟 **Interactive System Showcase & Live Visual Simulations:**
> Experience the animated neural tokenizer, draggable 2D semantic vector nebula, real-time RRF fusion physics sandbox, and 8-stage pipeline simulator directly in your browser:
> - 🌐 **[Live Interactive Architecture Blueprint & Simulator](https://rudra-p11.github.io/techbook-rag/)**
> - 📄 **[Empirical Case Study: Reciprocal Rank Fusion Retrieval Analysis](https://rudra-p11.github.io/techbook-rag/case_study_rrf_retrieval.html)**

TechBook RAG is a production-grade, interview-ready Retrieval-Augmented Generation (RAG) system tailored for a collection of technical books covering **SQL, Python, Machine Learning, Deep Learning, Linear Algebra, and Software Engineering**.

---

## 🏛️ Architecture Overview

```
                      USER
                        |
            +-----------+-----------+
            |                       |
            v                       v
     Streamlit Web UI        FastAPI Backend
    (Interactive App)         (RESTful API)
            |                       |
            +-----------+-----------+
                        |
                        v
              Query Orchestrator
       [Prompt Injection Guardrail Check]
                        |
          +-------------+-------------+
          |                           |
          v                           v
     Dense Search               Lexical Search
  (BGE-Small Embeddings)        (BM25 Okapi)
          |                           |
          +-------------+-------------+
                        |
                        v
             Reciprocal Rank Fusion (RRF)
                        |
                        v
             Context Builder [E1..E6]
                        |
                        v
             OpenAI Answer Synthesis
                        |
                        v
            Citation Verification &
            Fabricated ID Stripping
                        |
                        v
             Final Grounded Response
```

---

## 🚀 Key Features

1. **Zero-API Cost Local Embeddings**: Uses `BAAI/bge-small-en-v1.5` via Sentence Transformers running locally on CPU/GPU.
2. **Resilient Vector Store (Qdrant)**:
   - Connects to remote/Docker Qdrant if `QDRANT_URL` is provided.
   - Automatically falls back to embedded persistent storage (`./data/qdrant_storage`) if Docker is offline.
3. **Hybrid Retrieval**: Dense semantic similarity merged with BM25 Okapi lexical search using Reciprocal Rank Fusion ($k=60$).
4. **Verifiable Citations**: Every substantive fact is tagged with Evidence IDs `[E1]`, `[E2]` and transformed into human-readable citations e.g. `[Deep Learning from Scratch, p. 72]`.
5. **Security Guardrails**: Prompt-injection filtering, input length constraints, untrusted document isolation, and rejection of hallucinated citation tags.
6. **Sub-5-Second Latency**: Measured latency telemetry (retrieval ms, generation ms, total request ms).

---

## 📦 Quick Start Guide

### 1. Prerequisites
- Python 3.11 or 3.12
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and provide your OpenAI API key:
```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 4. Ingest Books from the Corpus Directory
Batch ingest all technical books from `./Corpus`:
```bash
python scripts/ingest_directory.py --dir ./Corpus
```

### 5. Launch Application

#### Option A: React + Node Modern Frontend (Recommended)
```bash
# In one terminal, start the FastAPI REST server:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In second terminal, launch the modern React Web App:
cd frontend
npm run dev
```
Open **`http://localhost:3000`** in your browser.

#### Option B: Streamlit Python UI
```bash
streamlit run app/ui/streamlit_app.py
```
Open **`http://localhost:8501`** in your browser.

Interactive Swagger API docs are available at **`http://localhost:8000/docs`**.

---

## 🧪 Testing and Evaluation

### Run Automated Unit Tests
```bash
python -m pytest tests/unit -v
```

### Run Benchmark Retrieval Evaluation
```bash
python scripts/evaluate_retrieval.py
```
Evaluation metrics are saved to `evaluation/reports/retrieval_report.json`.

---

## 🐳 Docker Deployment

To launch Qdrant and the application via Docker Compose:
```bash
docker-compose up --build
```
- Web UI: `http://localhost:8501`
- REST API: `http://localhost:8000`
- Qdrant Dashboard: `http://localhost:6333/dashboard`
