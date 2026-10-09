# TechBook RAG

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-1f1e1d?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-1f1e1d?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-1f1e1d?style=flat-square&logoColor=white)](https://qdrant.tech)
[![Embeddings](https://img.shields.io/badge/Embeddings-BGE_Small_384d-1f1e1d?style=flat-square&logo=huggingface&logoColor=white)](https://huggingface.co/BAAI/bge-small-en-v1.5)
[![LLM](https://img.shields.io/badge/LLM-gpt--4o--mini-1f1e1d?style=flat-square&logo=openai&logoColor=white)](https://openai.com)

**Intelligent Technical Knowledge Assistant** — Production-grade RAG over 11 technical books (2,810 chunks) using hybrid Dense + BM25 search with Reciprocal Rank Fusion.

🔗 **Quick Links:** [Live Interactive Architecture Showcase](https://rudra-p11.github.io/techbook-rag/) · [RRF k=60 Forensic Case Study](https://rudra-p11.github.io/techbook-rag/case_study_rrf_retrieval.html)

---


<br>

## Overview

TechBook RAG is a **production-grade, interview-ready** Retrieval-Augmented Generation system built over a curated library of **11 technical textbooks** spanning SQL, Python, Machine Learning, Deep Learning, Linear Algebra, and Software Engineering.

Every answer is grounded in real textbook passages with **verifiable page-level citations** — no hallucinations, no ungrounded claims.

<br>

> [!TIP]
> **Explore the full system interactively in your browser:**
> - [**Live Architecture Blueprint & Pipeline Simulator**](https://rudra-p11.github.io/techbook-rag/) — Interactive neural tokenizer, draggable 2D vector nebula, RRF physics sandbox, and 8-stage pipeline simulator
> - [**Empirical Case Study: RRF k=60 Retrieval Analysis**](https://rudra-p11.github.io/techbook-rag/case_study_rrf_retrieval.html) — Forensic analysis of hybrid retrieval for *"What is a forward pass in a neural network?"*

<br>

---

## Architecture & System Pipeline

```mermaid
graph LR
    Q[Query] --> G[Guardrails] --> E[BGE-Small Vectorizer]
    E --> H[Hybrid Search<br/>Dense + BM25] --> RRF[RRF k=60<br/>Re-Ranking]
    RRF --> Ctx[Context Builder<br/>Evidence E1..E6] --> LLM[gpt-4o-mini] --> V[Citation Verification]
```

<details>
<summary><b>🔍 System Specifications & Specifications Grid</b></summary>

| Component | Technical Details | Performance / SLA |
| :--- | :--- | :--- |
| **Embeddings** | `BAAI/bge-small-en-v1.5` (384d, 33M params) | Local CPU (15–25 ms inference, 0 API cost) |
| **Vector Store** | Qdrant (HNSW Cosine, 2,810 chunks) | Sub-ms graph traversal (Docker / embedded fallback) |
| **Lexical Search** | BM25 Okapi term frequencies | Exact keyword match rescue |
| **Re-Ranking** | Reciprocal Rank Fusion ($k=60$) | $1/(60 + \text{Rank}_{\text{dense}}) + 1/(60 + \text{Rank}_{\text{lexical}})$ |
| **Chunking** | 700 tokens, 15% overlap (105 tokens) | Sentence & code block boundary snapping |
| **LLM & Grounding** | OpenAI `gpt-4o-mini` (temp 0.1) | Grounded evidence `$E1..E6$` + citation validation |
| **Latency SLA** | Retrieval: $<80\text{ ms}$ | End-to-end: $1.2\text{s} - 2.8\text{s}$ |

</details>

---


<br>

## The 11-Book Corpus

<br>

| &nbsp; | Book | Domain | Publisher |
|:---:|:---|:---|:---|
| 📕 | **Deep Learning from Scratch** | Deep Learning & Neural Networks | O'Reilly |
| 📗 | **SQL Query Design Patterns and Best Practices** | SQL & Relational Databases | Packt |
| 📘 | **Boost.Asio C++ Network Programming Cookbook** | Systems Programming & C++ | Packt |
| 📙 | **Financial Theory with Python** | Python & Quantitative Finance | O'Reilly |
| 📕 | **Hands-On Machine Learning with C++** | Systems & Machine Learning | Packt |
| 📗 | **Linear Algebra for Data Science** | Mathematics & Vector Calculus | — |
| 📘 | **AI as a Service: Serverless ML on AWS** | Cloud Architecture | Manning |
| 📙 | **Data Science: A First Introduction with Python** | Data Science & Statistics | CRC Press |
| 📕 | **Cryptography and Embedded Systems Security** | Cryptography & Security | Springer |
| 📗 | **Graph-Powered Analytics and Machine Learning** | Graph Databases & GNNs | Manning |
| 📘 | **Python in Finance: Numerical Algorithms** | Python & Algorithmic Trading | O'Reilly |

<br>

---

<br>

## Quick Start

<br>

<details open>
<summary><kbd>&nbsp; 1 &nbsp;</kbd> &nbsp; <b>Prerequisites</b></summary>

<br>

- Python **3.11** or **3.12**
- Git
- Node.js **18+** (for the React frontend)

</details>

<br>

<details open>
<summary><kbd>&nbsp; 2 &nbsp;</kbd> &nbsp; <b>Setup Virtual Environment & Install Dependencies</b></summary>

<br>

```bash
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

</details>

<br>

<details open>
<summary><kbd>&nbsp; 3 &nbsp;</kbd> &nbsp; <b>Configure Environment Variables</b></summary>

<br>

Copy `.env.example` → `.env` and provide your OpenAI API key:

```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

</details>

<br>

<details open>
<summary><kbd>&nbsp; 4 &nbsp;</kbd> &nbsp; <b>Ingest Books from the Corpus Directory</b></summary>

<br>

```bash
python scripts/ingest_directory.py --dir ./Corpus
```

</details>

<br>

<details open>
<summary><kbd>&nbsp; 5 &nbsp;</kbd> &nbsp; <b>Launch Application</b></summary>

<br>

**Option A — React + Vite Frontend** <sup>(Recommended)</sup>

```bash
# Terminal 1 — FastAPI REST server:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — React Web App:
cd frontend && npm run dev
```

Open **`http://localhost:3000`** in your browser.

<br>

**Option B — Streamlit Python UI**

```bash
streamlit run app/ui/streamlit_app.py
```

Open **`http://localhost:8501`** in your browser.

<br>

> [!NOTE]
> Interactive Swagger API docs are always available at **`http://localhost:8000/docs`**

</details>

<br>

---

<br>

## Testing & Evaluation

<br>

<table>
  <tr>
    <td align="center" width="48">🧪</td>
    <td><b>Unit Tests</b></td>
    <td><code>python -m pytest tests/unit -v</code></td>
  </tr>
  <tr>
    <td align="center">📊</td>
    <td><b>Retrieval Benchmarks</b></td>
    <td><code>python scripts/evaluate_retrieval.py</code><br><sub>Results saved to <code>evaluation/reports/retrieval_report.json</code></sub></td>
  </tr>
</table>

<br>

---

<br>

## Docker Deployment

<br>

```bash
docker-compose up --build
```

<table>
  <tr>
    <td><kbd>Web UI</kbd></td>
    <td><code>http://localhost:8501</code></td>
  </tr>
  <tr>
    <td><kbd>REST API</kbd></td>
    <td><code>http://localhost:8000</code></td>
  </tr>
  <tr>
    <td><kbd>Qdrant Dashboard</kbd></td>
    <td><code>http://localhost:6333/dashboard</code></td>
  </tr>
</table>

<br>

---

<br>

<div align="center">

<sub>Built with precision · Every answer grounded in real textbook evidence</sub>

<br><br>

<a href="https://rudra-p11.github.io/techbook-rag/">
  <img src="https://img.shields.io/badge/Explore_the_Interactive_Showcase_%E2%86%97-c2593f?style=for-the-badge" alt="Explore">
</a>

<br><br>

</div>
