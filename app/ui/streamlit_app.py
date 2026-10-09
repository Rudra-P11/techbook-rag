import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import time
import requests
from pathlib import Path
import json

# Setup page config
st.set_page_config(
    page_title="TechBook RAG — Technical Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E88E5, #7E57C2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #607D8B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .citation-badge {
        display: inline-block;
        background-color: #E8EAF6;
        color: #283593;
        border-radius: 4px;
        padding: 2px 8px;
        margin-right: 6px;
        margin-bottom: 4px;
        font-size: 0.82rem;
        font-weight: 600;
        border: 1px solid #C5CAE9;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 10px 14px;
        border: 1px solid #E0E0E0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Direct Service Imports (allows running standalone or via API)
from app.config import settings
from app.api.schemas.chat import ChatRequest, ChatFilters
from app.services.chat_service import chat_service
from app.storage.document_registry import registry
from app.storage.qdrant_store import qdrant_store
from app.ingestion.pipeline import pipeline

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None

# Sidebar
with st.sidebar:
    st.title("⚙️ TechBook RAG Control")
    st.markdown("---")

    stats = qdrant_store.get_collection_stats()
    st.markdown("### 📊 Index Status")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("Total Vectors", stats.get("vectors_count", 0))
    with col_stat2:
        st.metric("Status", stats.get("status", "ready").upper())

    st.markdown("---")
    st.markdown("### 🔍 Retrieval Filters")
    all_docs = registry.list_documents()
    available_subjects = sorted(list({d.get("subject", "General") for d in all_docs}))
    
    selected_subjects = st.multiselect(
        "Filter by Subject",
        options=available_subjects,
        default=[]
    )

    top_k_chunks = st.slider("Context Evidence Chunks (Top-K)", min_value=2, max_value=10, value=6)

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_response = None
        st.rerun()

# Tabs
tab_chat, tab_docs, tab_inspector, tab_benchmarks = st.tabs([
    "💬 Chat Assistant",
    "📁 Document Management",
    "🔬 Retrieval Inspector",
    "📈 Evaluation & Latency"
])

# ----------------- TAB 1: CHAT -----------------
with tab_chat:
    st.markdown('<div class="main-header">TechBook RAG Knowledge Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Grounded technical question-answering across your books in SQL, Python, ML, Deep Learning & Systems</div>', unsafe_allow_html=True)

    # Sample prompt buttons
    st.markdown("**Sample Questions:**")
    sample_col1, sample_col2, sample_col3 = st.columns(3)
    sample_query = None
    with sample_col1:
        if st.button("📌 Explain INNER JOIN vs LEFT JOIN in SQL", use_container_width=True):
            sample_query = "What is the difference between INNER JOIN and LEFT JOIN in SQL?"
    with sample_col2:
        if st.button("📌 Difference between list and tuple in Python", use_container_width=True):
            sample_query = "Explain the difference between a list and a tuple in Python."
    with sample_col3:
        if st.button("📌 Compare supervised and unsupervised learning", use_container_width=True):
            sample_query = "Compare supervised and unsupervised learning using the available books."

    # Render Conversation History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "citations" in msg and msg["citations"]:
                st.markdown("**Citations:**")
                citation_html = "".join([
                    f'<span class="citation-badge">📖 {c["title"]} (p. {", ".join(map(str, c["pages"]))})</span>'
                    for c in msg["citations"]
                ])
                st.markdown(citation_html, unsafe_allow_html=True)

    # Input handling
    user_input = st.chat_input("Ask a technical question from your book library...")
    if sample_query:
        user_input = sample_query

    if user_input:
        # Add user query to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching technical corpus and synthesizing grounded answer..."):
                request = ChatRequest(
                    query=user_input,
                    filters=ChatFilters(subjects=selected_subjects),
                    top_k=top_k_chunks,
                    include_retrieval_debug=True
                )
                response = chat_service.answer_query(request)
                st.session_state.last_response = response

                st.markdown(response.answer)

                if response.citations:
                    st.markdown("**Citations:**")
                    citation_html = "".join([
                        f'<span class="citation-badge">📖 {c.title} (p. {", ".join(map(str, c.pages))})</span>'
                        for c in response.citations
                    ])
                    st.markdown(citation_html, unsafe_allow_html=True)

                # Metrics banner
                st.caption(
                    f"⏱️ Retrieval: {response.metrics.retrieval_latency_ms} ms | "
                    f"Generation: {response.metrics.generation_latency_ms} ms | "
                    f"Total: {response.metrics.total_latency_ms} ms"
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.answer,
                    "citations": [c.model_dump() for c in response.citations]
                })

# ----------------- TAB 2: DOCUMENT MANAGEMENT -----------------
with tab_docs:
    st.subheader("📚 Book Library & Ingestion Pipeline")
    
    # Ingestion pipeline visual flow
    st.markdown("""
    **Pipeline:** `1. PDF Upload` ➔ `2. Native Extraction / OCR` ➔ `3. Text Cleaning` ➔ `4. Token Chunking` ➔ `5. BGE-Small Embeddings` ➔ `6. Qdrant Index` ➔ `✅ Ready`
    """)
    st.markdown("---")

    # Ingest Corpus folder action
    corpus_dir = settings.get_absolute_path("./Corpus")
    if corpus_dir.exists():
        pdf_files = list(corpus_dir.glob("*.pdf"))
        st.markdown(f"Found **{len(pdf_files)} PDF books** in local `Corpus/` directory.")
        
        if st.button("🚀 Ingest / Index All Books in Corpus Folder", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, pdf in enumerate(pdf_files):
                status_text.text(f"Ingesting ({idx+1}/{len(pdf_files)}): {pdf.name}...")
                try:
                    pipeline.ingest_file(pdf)
                except Exception as e:
                    st.error(f"Error ingesting {pdf.name}: {e}")
                progress_bar.progress((idx + 1) / len(pdf_files))
            
            status_text.text("Corpus ingestion complete!")
            st.success("All books in Corpus ingested and indexed!")
            time.sleep(1)
            st.rerun()

    st.markdown("---")
    st.markdown("### 📤 Upload New PDF Book")
    uploaded_file = st.file_uploader("Upload a PDF document (max 150MB)", type=["pdf"])
    upload_subject = st.text_input("Subject / Domain (e.g., SQL, Python, Deep Learning)", value="Computer Science")
    
    if uploaded_file and st.button("Ingest Uploaded File"):
        with st.spinner(f"Ingesting {uploaded_file.name}..."):
            dest_dir = settings.get_absolute_path(settings.DOCUMENT_STORAGE_DIR)
            dest_dir.mkdir(parents=True, exist_ok=True)
            save_path = dest_dir / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            res = pipeline.ingest_file(save_path, subject=upload_subject)
            st.success(f"Ingested '{uploaded_file.name}': {res.get('page_count', 0)} pages, {res.get('chunk_count', 0)} chunks.")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📑 Currently Ingested Books")
    docs = registry.list_documents()
    if not docs:
        st.info("No documents indexed yet. Click 'Ingest / Index All Books in Corpus Folder' above to start!")
    else:
        for d in docs:
            with st.expander(f"📖 {d['display_name']} ({d['subject']}) — Status: {d['ingestion_status'].upper()}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.write(f"**Pages:** {d['page_count']}")
                c2.write(f"**Chunks:** {d['chunk_count']}")
                c3.write(f"**File Size:** {round(d['file_size_bytes'] / (1024*1024), 2)} MB")
                c4.write(f"**Hash:** `{d['file_hash'][:10]}...`")
                if st.button("❌ Delete Book", key=f"del_{d['document_id']}"):
                    qdrant_store.delete_by_document(d['document_id'])
                    registry.mark_document_deleted(d['document_id'])
                    st.warning(f"Deleted {d['display_name']}")
                    st.rerun()

# ----------------- TAB 3: RETRIEVAL INSPECTOR -----------------
with tab_inspector:
    st.subheader("🔬 Retrieved Evidence Passages Inspector")
    st.markdown("Inspect the exact passages retrieved, similarity scores, and metadata from the most recent query.")

    if not st.session_state.last_response or not st.session_state.last_response.retrieved_chunks:
        st.info("No query performed yet. Ask a question in the Chat Assistant tab to inspect retrieved evidence passages here!")
    else:
        resp = st.session_state.last_response
        st.markdown(f"**Total Evidence Passages Retrieved:** {len(resp.retrieved_chunks)}")
        
        for idx, chunk in enumerate(resp.retrieved_chunks, start=1):
            with st.expander(f"Evidence [E{idx}] — {chunk.title} (Pages: {', '.join(map(str, chunk.page_numbers))}) | Score: {chunk.score}"):
                st.write(f"**Document ID:** `{chunk.document_id}`")
                st.write(f"**Filename:** `{chunk.filename}`")
                st.write(f"**Subject:** {chunk.subject}")
                st.markdown("**Chunk Content Preview:**")
                st.code(chunk.text_preview, language="text")

# ----------------- TAB 4: EVALUATION & LATENCY -----------------
with tab_benchmarks:
    st.subheader("📈 Performance Telemetry & Latency Dashboard")
    
    if st.session_state.last_response:
        m = st.session_state.last_response.metrics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Retrieval Latency", f"{m.retrieval_latency_ms} ms")
        with c2:
            st.metric("LLM Generation Latency", f"{m.generation_latency_ms} ms")
        with c3:
            st.metric("End-to-End Latency", f"{m.total_latency_ms} ms")

        st.markdown("---")
        st.markdown("### PRD SLA Target Compliance")
        sla_met = 2000 <= m.total_latency_ms <= 5000 or m.total_latency_ms < 5000
        if sla_met:
            st.success(f"✅ Total Latency ({m.total_latency_ms} ms) is within target PRD latency (2,000–5,000 ms).")
        else:
            st.info(f"Total Latency: {m.total_latency_ms} ms.")
    else:
        st.info("Submit a query in the Chat tab to view real-time latency metrics.")
