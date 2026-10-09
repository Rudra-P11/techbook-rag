# Product Requirements Document (PRD)

# Technical Books RAG Chatbot

**Project Name:** TechBook RAG — Intelligent Technical Knowledge Assistant\
**Document Version:** 1.0\
**Status:** Ready for Implementation\
**Product Type:** AI-powered Retrieval-Augmented Generation (RAG) Web Application\
**Primary Domains:** SQL, Python, Machine Learning, Deep Learning, Data Science, Software Engineering\
**Target Users:** Developers, students, data analysts, ML engineers, and technical interview candidates

---

## 1. Executive Summary

TechBook RAG is an intelligent question-answering system that allows users to query a private collection of technical books and receive accurate, context-aware answers grounded in the contents of those books.

The system will ingest a corpus of at least 10 PDF books, with each book containing at least 200 pages. The corpus will primarily cover SQL, Python, Machine Learning, Deep Learning, Data Science, and related technical subjects.

The application will implement an end-to-end Retrieval-Augmented Generation pipeline:

1. PDF ingestion and document validation.
2. Native text extraction and OCR for scanned pages.
3. Text cleaning, normalization, and metadata extraction.
4. Deterministic, token-aware text chunking.
5. Local, open-source embedding generation.
6. Persistent storage in an open-source vector database.
7. Hybrid retrieval using semantic and lexical search.
8. Optional reranking and relevance filtering.
9. LLM-based answer generation using retrieved evidence.
10. Citation generation and verification.
11. Response safety checks and prompt-injection protection.
12. Evaluation, latency monitoring, and retrieval visualization.

The initial implementation will use an open-source embedding model and self-hosted Qdrant for vector storage. OpenAI's API will be used for answer generation through a configurable model selection.

The system must remain functional when the embedding pipeline is run offline after model download. Answer generation will require an active connection to the configured LLM provider unless a local generation model is added.

### Primary objective

Build a working RAG application that answers questions from a large technical PDF corpus, provides traceable citations to the source books and page numbers, and achieves a typical query-to-answer latency of 2–5 seconds under a documented hardware and workload configuration.

The latency objective is a performance target, not a guarantee independent of hardware, network conditions, corpus size, or LLM provider response times.

---

## 2. Problem Statement

Technical knowledge is distributed across long books, reference manuals, and specialized textbooks. Finding a precise explanation in a collection of large PDFs is time-consuming.

Traditional keyword search has several limitations:

- It may miss semantically relevant passages.
- It requires users to know the terminology used in the source document.
- It does not synthesize information across multiple books.
- It does not naturally provide conversational follow-up questions.
- It does not explain answers in a conversational format.
- It may struggle with scanned pages, tables, code examples, and technical notation.

General-purpose LLMs introduce additional risks:

- They may answer using knowledge outside the supplied books.
- They may fabricate technical details or citations.
- They may confuse similar SQL dialects, Python versions, or ML algorithms.
- They may confidently answer questions for which the corpus contains insufficient evidence.

TechBook RAG addresses these problems by retrieving relevant source passages and conditioning answer generation on those passages.

---

## 3. Product Goals

### 3.1 Functional goals

- Ingest at least 10 PDF books, each containing at least 200 pages.
- Support native PDF text extraction and OCR for scanned pages.
- Preserve document identity, page numbers, and available layout information.
- Generate and persist vector embeddings.
- Retrieve relevant chunks using semantic and lexical search.
- Generate answers grounded in retrieved content.
- Include source citations in every substantive factual answer.
- Provide a web-based chat interface.
- Display retrieved passages, similarity scores, and source metadata.
- Support multi-turn conversations with explicit context management.
- Evaluate retrieval quality, citation accuracy, hallucinations, and latency.
- Provide document-management and ingestion-status functionality.

### 3.2 Non-functional goals

- Use free/open-source embedding models by default.
- Use a free/open-source vector database.
- Avoid re-embedding unchanged documents unnecessarily.
- Support reproducible ingestion and indexing.
- Protect API credentials and private documents.
- Resist prompt injection originating from user input or document content.
- Support incremental document ingestion and deletion.
- Expose measurable performance and evaluation metrics.
- Provide a documented local deployment process.

### 3.3 Out of scope for the initial release

- Training a foundation model from scratch.
- Fine-tuning an LLM.
- Guaranteed mathematical correctness for arbitrary calculations.
- Automatic execution of SQL queries against production databases.
- Arbitrary execution of Python code extracted from books.
- Automatic crawling of copyrighted books from unauthorized sources.
- Enterprise-grade multi-tenant isolation unless explicitly implemented.
- Guaranteed extraction of every complex chart or diagram.
- Guaranteed 2-second responses on all hardware and networks.

---

## 4. Target Users and User Stories

### 4.1 Students

As a student, I want to ask questions about SQL, Python, or machine learning so that I can understand concepts without manually searching through entire books.

### 4.2 Developers

As a developer, I want explanations and code examples grounded in technical references so that I can verify implementation details.

### 4.3 Interview candidates

As an interview candidate, I want to compare concepts such as supervised and unsupervised learning, SQL joins, or Python data structures so that I can prepare using my own reference material.

### 4.4 Researchers and technical readers

As a technical reader, I want answers synthesized from multiple books, with citations to each supporting source.

### 4.5 Administrators

As an administrator, I want to upload, inspect, index, and remove books so that the searchable knowledge base remains current and manageable.

---

## 5. Dataset and Corpus Requirements

### 5.1 Minimum corpus

The initial corpus must contain:

- At least 10 PDF documents.
- At least 200 pages per PDF.
- At least 2,000 pages in total.
- A mix of technical subjects, including SQL, Python, and Machine Learning.
- Stable document identifiers and original filenames.
- Metadata recording ingestion status and processing errors.

The ingestion system must not assume that every PDF contains selectable text.

### 5.2 Recommended corpus categories

- SQL fundamentals, joins, indexing, query optimization, and database design.
- Python syntax, standard libraries, data structures, and object-oriented programming.
- Machine Learning algorithms, evaluation, feature engineering, and model selection.
- Deep Learning, neural networks, and optimization.
- Statistics, probability, and data analysis.
- Data engineering and software engineering, where appropriate.

### 5.3 Document acquisition

Documents must be obtained from sources for which the project has appropriate access and reuse rights.

Possible sources include open textbooks, public technical manuals, publisher-authorized resources, and legitimately obtained personal reference material.

The application must not bypass document access restrictions or assume that a publicly accessible PDF is automatically licensed for redistribution.

### 5.4 Document metadata

Each document record must contain:

- `document_id`: stable unique identifier.
- `filename`: original filename.
- `display_name`: human-readable title.
- `file_hash`: SHA-256 checksum of the original file.
- `file_size_bytes`: original file size.
- `page_count`: detected page count.
- `subject`: inferred or user-specified category.
- `author`: optional.
- `publication_year`: optional.
- `language`: detected primary language.
- `source_uri`: optional origin or provenance.
- `license`: optional usage/license information.
- `ingestion_status`: pending, processing, indexed, failed, or deleted.
- `created_at` and `updated_at`.
- `processing_version`: ingestion pipeline version.
- `embedding_model`: model identifier used for indexing.
- `index_version`: collection/index configuration version.

---

## 6. Functional Requirements

## FR-01: PDF Upload and Document Management

The application must allow authorized users to upload PDF files through the web interface or an administrative API.

### Requirements

- Validate file type and PDF structure.
- Reject unsupported or corrupted files with a clear error.
- Enforce configurable upload-size and page-count limits.
- Generate a stable document identifier.
- Calculate a SHA-256 file hash.
- Detect duplicate files using their hashes.
- Record the ingestion status.
- Display document processing progress.
- Allow document metadata to be inspected.
- Support deletion of a document and its associated chunks and vectors.
- Support incremental ingestion without rebuilding the entire corpus.
- Avoid duplicate indexing when the same file is uploaded again.
- Isolate each document's processing errors so that one failed PDF does not stop the entire batch.

### Acceptance criteria

- A user can upload a valid PDF and observe its processing status.
- A duplicate upload is detected or handled according to the configured duplicate policy.
- A failed document produces an actionable error.
- Deleting a document removes its vectors and associated metadata from active retrieval.

## FR-02: PDF Text Extraction

The system must extract text from PDFs using native PDF parsing before deciding whether OCR is required.

### Recommended libraries

- PyMuPDF (`fitz`) as the primary PDF extraction library.
- `pypdf` as an optional secondary utility.
- Tesseract OCR through `pytesseract` for scanned content.
- OpenCV for optional image preprocessing.

### Requirements

- Extract text page by page.
- Preserve original PDF page numbering.
- Capture page dimensions and text bounding boxes where available.
- Detect pages with little or no extractable text.
- Detect likely scanned pages using configurable heuristics.
- Avoid OCR when native text is already sufficiently complete.
- Perform OCR selectively on pages that need it.
- Support OCR languages through configurable Tesseract language packs.
- Store extraction quality indicators.
- Record extraction errors without silently discarding pages.
- Preserve code blocks, punctuation, operators, and technical symbols as accurately as possible.
- Retain tables and layout information when supported by the extraction library.

### Page-level metadata

Each extracted page should record:

- `document_id`
- `page_number`
- `extracted_text`
- `extraction_method`: native, OCR, or mixed
- `ocr_confidence`: optional, if available
- `page_width`
- `page_height`
- `extraction_status`
- `warnings`
- `processing_duration_ms`

PDF page numbers are one-based in the user interface. The implementation must document any internal zero-based indexing and convert it consistently.

### Acceptance criteria

- Text-based pages are processed without unnecessary OCR.
- Scanned pages are routed to OCR.
- Page numbers remain accurate after extraction.
- Extraction failures are observable.
- Code snippets and technical symbols are preserved to the extent supported by the parser and OCR engine.

## FR-03: Text Cleaning and Normalization

The system must clean extracted text without destroying technical meaning.

### Cleaning operations

- Normalize line endings and whitespace.
- Remove redundant blank lines.
- Join words broken by line-wrap hyphenation when safe.
- Detect repeated headers and footers.
- Remove page artifacts only when confidence is sufficient.
- Normalize Unicode text carefully.
- Preserve meaningful indentation in code examples.
- Preserve punctuation in SQL, Python, mathematical expressions, and formulas.
- Retain section headings and chapter boundaries.
- Detect language and record the result.
- Mark empty or low-quality pages.
- Maintain a mapping from cleaned text to the original page and layout region.

### Important constraints

- Do not blindly remove repeated strings that might be meaningful content.
- Do not strip underscores, brackets, operators, quotation marks, or semicolons from code.
- Do not merge unrelated paragraphs.
- Do not merge text across page boundaries without retaining page provenance.
- Do not treat OCR confidence as a definitive measure of semantic correctness.

### Acceptance criteria

- Normal prose is normalized.
- Code indentation and essential symbols remain intact.
- Page-level provenance remains available after cleaning.
- Cleaning operations are deterministic for a fixed pipeline version.

## FR-04: Chunking and Metadata

The system must divide extracted text into searchable passages optimized for semantic retrieval.

### Initial chunking configuration

- Target chunk size: 700 tokens.
- Minimum chunk size: 150 tokens where practical.
- Maximum chunk size: 1,000 tokens.
- Overlap: approximately 15%, subject to structural boundaries.
- Chunking unit: tokens rather than raw character count.
- Token counter: one compatible with the selected embedding model.
- Chunk boundaries: paragraph, heading, sentence, and code-block aware.

These are starting values, not universal optima. The final configuration must be validated against retrieval benchmarks.

### Chunking rules

- Prefer section boundaries when possible.
- Keep headings with their associated content.
- Avoid splitting code blocks unnecessarily.
- Avoid splitting tables in the middle when a meaningful row-based split is possible.
- Preserve page boundaries in provenance metadata.
- Allow a chunk to reference multiple pages when it legitimately spans them.
- Apply overlap only when useful; avoid excessive duplication.
- Skip chunks containing only whitespace or irrelevant artifacts.
- Keep chunk generation deterministic.
- Record the chunking configuration and version.

### Chunk metadata schema

Each chunk must contain:

- `chunk_id`
- `document_id`
- `filename`
- `title`
- `subject`
- `start_page`
- `end_page`
- `page_numbers`
- `section_title`, if available
- `chunk_index`
- `chunk_text`
- `token_count`
- `bounding_boxes`, when available
- `extraction_method`
- `language`
- `file_hash`
- `chunker_version`
- `embedding_model`
- `created_at`

### Stable identifiers

Chunk identifiers should be derived from stable document identity, chunking version, and chunk position or content hash.

Changing the chunking configuration must trigger an explicit re-indexing process rather than silently mixing incompatible chunks.

### Acceptance criteria

- Chunks remain within configured token limits, except for documented edge cases.
- Page citations remain traceable to the original PDF.
- Re-running ingestion with identical inputs and configuration produces equivalent chunk boundaries and identifiers.
- Chunk metadata can be filtered by document, subject, and page.

## FR-05: Embedding Generation

The system must convert text chunks into dense vector representations.

### Default embedding model

`BAAI/bge-small-en-v1.5`

Implementation: Sentence Transformers.

Model weights will be downloaded from an appropriate model repository and cached locally. Runtime inference should not require a paid embedding API.

### Alternatives

- `sentence-transformers/all-MiniLM-L6-v2`
- `BAAI/bge-base-en-v1.5`
- OpenAI `text-embedding-3-small`, as an optional API-based embedding provider.

The model must be selected based on retrieval quality, latency, memory usage, language requirements, and licensing.

### Requirements

- Generate one embedding per indexed chunk.
- Normalize vectors consistently when required by the selected similarity metric.
- Use batching for efficient processing.
- Support CPU execution.
- Support optional GPU acceleration.
- Persist embeddings to the vector database.
- Avoid embedding unchanged chunks unnecessarily.
- Cache or reuse embeddings when safe and appropriate.
- Record the embedding model name and version.
- Record the vector dimension.
- Handle batch failures with retries and error reporting.
- Reject incompatible vectors during index writes.
- Ensure query embeddings use the same compatible embedding model as indexed documents.

### Re-indexing rules

A full or partial re-index must be triggered when any relevant component changes:

- Embedding model or model revision.
- Vector dimension.
- Chunking configuration.
- Text normalization behavior that changes chunk content.
- Distance metric or incompatible index schema.

### Acceptance criteria

- Embeddings are generated successfully for all eligible chunks.
- Embeddings persist across application restarts.
- Duplicate unchanged chunks do not require unnecessary recomputation.
- Model identity and index compatibility are verifiable.

## FR-06: Vector Database and Indexing

The system must use an open-source vector database.

### Default choice

Qdrant, self-hosted through Docker.

### Requirements

- Store dense vectors and chunk metadata.
- Support approximate nearest-neighbor retrieval.
- Support metadata filtering.
- Support persistent storage.
- Support collection configuration and indexing.
- Support deletion by document identifier.
- Support retrieval of chunk IDs, scores, and metadata.
- Support index rebuilds and backups.
- Expose health status and collection statistics.
- Avoid keeping the only copy of the corpus in volatile memory.

### Index configuration

The system should begin with HNSW-based approximate nearest-neighbor search.

The following settings must be configurable:

- Vector distance metric.
- HNSW construction parameters.
- HNSW search parameters.
- Payload indexing settings.
- Search result limit.
- Optional quantization settings.

Quantization and more complex ANN configurations should be introduced only when measurements justify them.

### Storage design

A Qdrant collection should store:

- Vector embedding.
- `chunk_id`.
- `document_id`.
- Filename and title.
- Page metadata.
- Subject.
- Section title.
- Other required retrieval filters.

A relational database such as SQLite may be used initially for document registry, ingestion jobs, and administrative state. Qdrant remains the vector store.

### Acceptance criteria

- Vectors remain available after service restart.
- A query returns relevant chunks with scores and metadata.
- Filtering by document or subject works correctly.
- Document deletion removes associated vector points.
- Collection and index settings are documented.

## FR-07: Retrieval Pipeline

The system must retrieve the most relevant chunks for a user query.

### Default retrieval workflow

1. Validate the user query.
2. Normalize the query without changing its intent.
3. Apply any requested subject or document filters.
4. Generate a query embedding.
5. Perform dense vector search.
6. Perform lexical search using a BM25-compatible implementation.
7. Merge candidates using Reciprocal Rank Fusion or another measured fusion method.
8. Optionally rerank candidates.
9. Apply relevance and diversity filtering.
10. Return the final evidence set with source metadata.

### Initial retrieval configuration

- Dense retrieval candidates: 20.
- Lexical retrieval candidates: 20.
- Fused candidate pool: up to 30–40 unique chunks.
- Optional reranker input: up to 20 chunks.
- Final context: typically 4–8 chunks.
- Final context token budget: configurable, initially approximately 5,000 tokens.

These values must be tuned using the evaluation dataset and the generation model's context requirements.

### Hybrid retrieval

Dense retrieval helps identify semantically related passages even when the wording differs.

Lexical retrieval helps identify exact technical terms such as:

- SQL function names.
- Python exception names.
- API identifiers.
- Algorithm names.
- Mathematical notation.
- Error messages.
- Version numbers.

The initial implementation may use a local BM25 index through a suitable open-source library, such as `rank-bm25`, or another suitable search component.

### Optional reranking

The system may use an open-source cross-encoder reranker, such as a suitable BGE reranker, to improve the ordering of candidate passages.

Reranking must be configurable because it adds inference latency and memory requirements.

A lightweight lexical or score-based filter may be used when strict latency is more important than a small potential relevance improvement.

### Diversity and redundancy

The retrieval layer should avoid returning many nearly identical overlapping chunks from the same passage.

Where appropriate, it should prefer evidence from multiple sections or books when the question asks for a comparison.

### Relevance threshold

The system must support configurable relevance thresholds or calibrated filtering rules.

A raw cosine similarity score is not a universal confidence score. Thresholds must be calibrated against actual retrieval results.

### Acceptance criteria

- Relevant passages are returned for benchmark queries.
- Metadata and scores are included with each retrieved chunk.
- Retrieval supports exact technical terms and semantic paraphrases.
- Unrelated or low-confidence evidence can be filtered.
- Retrieval latency is measured independently from generation latency.

## FR-08: LLM Answer Generation

The system must synthesize answers from retrieved evidence.

### Default provider

OpenAI API, using a configurable generation model available to the project's API account.

The exact model identifier must be stored in environment configuration rather than hardcoded throughout the application.

### Requirements

- Pass the user query and retrieved evidence to the LLM.
- Include source identifiers in the evidence supplied to the model.
- Instruct the model to prioritize retrieved evidence over prior knowledge.
- Require citations for factual claims grounded in the books.
- Avoid unsupported citations.
- Avoid inventing page numbers or document names.
- Allow the system to state that evidence is insufficient.
- Support multi-document synthesis.
- Support concise answers by default.
- Support optional detailed explanations.
- Preserve important technical terminology and code formatting.
- Distinguish direct source claims from reasonable inferences.
- Avoid claiming that a statement appears in a book when the retrieved text does not support it.

### Answer structure

The standard answer should contain:

1. Direct answer.
2. Explanation or step-by-step reasoning summary, where appropriate.
3. Code example or comparison, if requested and supported by evidence.
4. Inline citations linked to source references.
5. A source list containing the document title, filename, and page number or range.
6. An uncertainty statement when the evidence is incomplete or conflicting.

### Technical correctness

For questions involving SQL, Python, or machine learning:

- Preserve SQL dialect differences.
- Avoid presenting version-specific behavior as universal.
- Identify version constraints when the source provides them.
- Do not execute generated code automatically.
- Clearly label illustrative examples that are not direct source quotations.
- Avoid modifying retrieved code snippets in ways that change their semantics without explaining the changes.

### OpenAI API integration

- Use the official OpenAI SDK.
- Keep the API key on the server.
- Use configurable request timeouts.
- Retry transient failures with bounded exponential backoff.
- Avoid retrying non-recoverable errors indefinitely.
- Set a maximum output token budget.
- Use streaming responses when supported and appropriate.
- Record provider latency, status, and token usage.
- Avoid logging API keys or sensitive prompt contents.
- Handle rate limits and quota exhaustion gracefully.

### Acceptance criteria

- Answers are generated from the selected evidence.
- Citations refer to actual retrieved chunks.
- The system refuses to invent source references.
- API errors result in a controlled error response.
- Model and generation settings are recorded for reproducibility.

## FR-09: Citation Generation and Verification

Citations are a mandatory product requirement.

### Citation format

The default citation format is:

`[Book Title, p. 123]`

For a passage spanning multiple pages:

`[Book Title, pp. 123–125]`

For a chunk that maps to non-contiguous pages, cite the relevant page numbers separately rather than implying a continuous range.

### Citation requirements

- Every substantive factual answer must include source references.
- Each cited source must correspond to retrieved evidence.
- The citation must use page metadata from the ingestion pipeline.
- The source must include the filename or human-readable book title.
- The interface must allow users to inspect the cited passage.
- The system must not trust page numbers generated by the LLM without verification.
- The backend must validate citations against the evidence actually supplied to the model.
- Unsupported citations must be removed or cause the answer to be regenerated or rejected.
- A claim supported by multiple sources may cite multiple references.

### Citation verification approach

The preferred implementation is to assign a stable evidence ID to every context passage.

For example:

- `E1`: Python book, page 72.
- `E2`: SQL book, pages 155–156.
- `E3`: Machine Learning book, page 310.

The LLM returns citations referencing these evidence IDs. The backend maps each evidence ID to the stored document metadata and formats the citation.

This approach is more reliable than asking the model to invent filenames and page numbers directly.

The implementation should validate citation identifiers and ensure that every displayed source exists in the retrieved evidence set.

### Acceptance criteria

- Every displayed citation resolves to a known document and page.
- A user can inspect the cited passage.
- Fabricated or unknown evidence identifiers are rejected.
- Citation accuracy is measured during evaluation.

## FR-10: Multi-Turn Conversation

The application must support follow-up questions.

Examples:

- "Explain supervised learning."
- "How is it different from unsupervised learning?"
- "Give me an example in Python."

### Requirements

- Maintain conversation history within a session.
- Support configurable history length or token budget.
- Resolve follow-up references into a standalone retrieval query.
- Retrieve fresh evidence for each substantive question.
- Do not assume earlier retrieved passages are sufficient for every follow-up.
- Preserve citations from the current answer.
- Avoid mixing unrelated conversations.
- Support a clear-chat action.
- Do not store conversation history permanently unless explicitly configured.

Conversation history must not be treated as authoritative evidence. Retrieved document passages remain the source of truth for corpus-grounded answers.

## FR-11: Web User Interface

The application must provide a responsive web interface.

### Recommended frontend

- Streamlit for the initial demo.
- React or Next.js as an optional production-oriented frontend.

Streamlit is recommended for the first implementation because it enables rapid development of the chat interface and retrieval visualization.

### Required screens and components

#### A. Chat interface

- User message input.
- Conversation history.
- Assistant answer display.
- Streaming answer display when supported.
- Inline citations.
- Source inspection controls.
- Clear conversation action.
- Loading state.
- Error messages and retry controls.

#### B. Document management

- Upload PDF control.
- List of ingested documents.
- Filename and title.
- Page count.
- Subject/category.
- Ingestion status.
- Chunk count.
- Last ingestion time.
- Error details.
- Delete action.

#### C. Retrieval inspector

Display the passages used for the answer.

For each passage, show:

- Document title.
- Filename.
- Page number or range.
- Section heading, if available.
- Retrieval score.
- Retrieval method or rank.
- A text preview.
- Final inclusion status.
- Reranker score, when applicable.

#### D. Ingestion pipeline dashboard

Visualize:

`PDF Upload → Extraction/OCR → Cleaning → Chunking → Embedding → Vector Indexing → Ready`

The UI must show processing stages and failures. Progress must be based on actual backend job status rather than simulated progress.

#### E. Evaluation dashboard

Display:

- Corpus size.
- Total indexed chunks.
- Failed ingestion jobs.
- Retrieval latency.
- Generation latency.
- End-to-end latency.
- p50, p95, and p99 latency where sufficient samples exist.
- Recall@k.
- Mean Reciprocal Rank.
- Citation accuracy.
- Answer groundedness metrics.
- Evaluation run history.

### Acceptance criteria

- Users can ask questions without interacting with the terminal.
- Citations and retrieved passages are visible.
- Ingestion progress reflects actual job state.
- The interface works at typical desktop and mobile widths.

## FR-12: REST API

The backend must expose an API for ingestion, querying, and document management.

### Required endpoints

#### Health

`GET /health`

Returns service health and dependency status.

#### Readiness

`GET /ready`

Indicates whether required dependencies are ready to serve requests.

#### Upload document

`POST /api/v1/documents`

Accepts a PDF upload and creates an ingestion job.

#### List documents

`GET /api/v1/documents`

Returns document metadata and processing status.

#### Get document details

`GET /api/v1/documents/{document_id}`

Returns document metadata, ingestion state, and processing statistics.

#### Delete document

`DELETE /api/v1/documents/{document_id}`

Deletes the document from the active corpus and removes associated vector data.

#### Get ingestion job

`GET /api/v1/jobs/{job_id}`

Returns job status, stage, progress, warnings, and errors.

#### Query

`POST /api/v1/chat`

Accepts a query and optional conversation context.

Example request:

```json
{
  "query": "Explain the difference between a clustered and non-clustered index.",
  "conversation_id": "optional-session-id",
  "filters": {
    "subjects": ["SQL"],
    "document_ids": []
  },
  "top_k": 5,
  "include_retrieval_debug": true
}
```

Example response:

```json
{
  "answer": "A clustered index determines the organization of table data in systems that implement this model...",
  "citations": [
    {
      "evidence_id": "E1",
      "document_id": "doc_123",
      "filename": "database_systems.pdf",
      "title": "Database Systems",
      "pages": [142, 143]
    }
  ],
  "retrieved_chunks": [
    {
      "chunk_id": "chunk_456",
      "document_id": "doc_123",
      "page_numbers": [142, 143],
      "score": 0.82,
      "text_preview": "..."
    }
  ],
  "metrics": {
    "retrieval_latency_ms": 120,
    "generation_latency_ms": 1800,
    "total_latency_ms": 2050
  }
}
```

All values above are illustrative schema examples, not measured results.

The implementation must define stable response models and avoid exposing private internal fields unnecessarily.

### API requirements

- Validate all request parameters.
- Enforce query and upload size limits.
- Use appropriate HTTP status codes.
- Return structured error messages.
- Support request IDs for tracing.
- Apply authentication to administrative endpoints.
- Avoid returning internal exception traces to users.
- Document endpoints with OpenAPI.
- Add rate limiting where appropriate.
- Do not expose arbitrary file paths or secrets.

## FR-13: Ingestion Job Management

Long-running ingestion must not block interactive chat requests.

### Requirements

- Run ingestion asynchronously.
- Maintain explicit job states.
- Support bounded retries.
- Record job duration and stage-level progress.
- Support cancellation where safe.
- Avoid concurrent ingestion jobs exhausting system resources.
- Make failed jobs inspectable and retryable.
- Ensure that partially ingested documents are not incorrectly marked as ready.
- Make indexing operations idempotent.
- Track the pipeline version for each document.

A simple local deployment may use a database-backed job table and a separate worker process. A distributed task queue may be introduced if the workload requires it.

---

## 7. System Architecture

### 7.1 High-level architecture

```
                    USER
                     |
                     v
             Streamlit Web UI
                     |
                     v
              FastAPI Backend
                     |
          +----------+----------+
          |                     |
          v                     v
   Query Orchestrator     Document API
          |                     |
          v                     v
    Query Validation       Ingestion Queue
          |                     |
          v                     v
    Query Embedding       PDF Extraction
          |                     |
          v                     v
    Dense Retrieval       OCR / Cleaning
          |                     |
          v                     v
    Lexical Retrieval      Token Chunking
          |                     |
          v                     v
     Rank Fusion           Local Embeddings
          |                     |
          v                     v
       Reranking           Qdrant Index
          |                     |
          v                     v
     Context Builder      Document Registry
          |
          v
      OpenAI API
          |
          v
   Citation Validation
          |
          v
     Safety Checks
          |
          v
   Final Chat Response
```

### 7.2 Query-time flow

1. Receive and validate the user query.
2. Identify the conversation context.
3. Apply permitted metadata filters.
4. Generate the query embedding.
5. Execute dense and lexical retrieval.
6. Fuse and optionally rerank candidates.
7. Select a context within the token budget.
8. Call the configured generation model.
9. Validate evidence references and citations.
10. Apply response safety and output validation.
11. Return the answer, citations, and optional debug data.
12. Record latency and usage metrics.

### 7.3 Ingestion-time flow

1. Accept the uploaded PDF.
2. Validate its structure and metadata.
3. Compute the file hash.
4. Create a document record and ingestion job.
5. Extract text page by page.
6. Run OCR where required.
7. Clean and normalize the extracted text.
8. Detect sections and preserve page provenance.
9. Chunk the content deterministically.
10. Generate embeddings in batches.
11. Write vectors and metadata to Qdrant.
12. Verify indexed counts and metadata.
13. Mark the document as indexed.
14. Record the ingestion summary.

### 7.4 Architectural principles

- Separate ingestion from query serving.
- Keep model and database clients behind well-defined interfaces.
- Make embedding and generation providers configurable.
- Treat source metadata as authoritative for citations.
- Make ingestion idempotent.
- Keep all credentials server-side.
- Make the retrieval pipeline observable.
- Ensure that documents are treated as untrusted input.
- Make every performance claim measurable.

---

## 8. Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Programming language | Python 3.11 or compatible supported version | Application logic |
| Frontend | Streamlit | Chat and demo UI |
| API backend | FastAPI | REST endpoints |
| PDF extraction | PyMuPDF | Native text and layout extraction |
| OCR | Tesseract + pytesseract | Scanned pages |
| Image preprocessing | OpenCV, optional | Improve OCR quality |
| Text tokenization | Model-compatible tokenizer | Chunk sizing |
| Embeddings | BAAI/bge-small-en-v1.5 | Local dense vectors |
| Embedding framework | Sentence Transformers | Local embedding inference |
| Vector database | Qdrant | Persistent vector storage |
| Lexical retrieval | BM25-compatible library | Keyword retrieval |
| Reranking | Optional open-source cross-encoder | Candidate refinement |
| LLM generation | OpenAI API | Answer synthesis |
| Configuration | Environment variables and Pydantic settings | Configuration management |
| Document registry | SQLite initially | Document/job metadata |
| Data validation | Pydantic | Request/response schemas |
| Logging | Python logging with structured output | Application logs |
| Metrics | Prometheus-compatible instrumentation, optional | Monitoring |
| Testing | pytest | Automated testing |
| API documentation | FastAPI OpenAPI | API specification |
| Containerization | Docker and Docker Compose | Reproducible deployment |

All dependencies must be pinned to tested versions for a reproducible release.

Before selecting a package version, verify compatibility with the chosen Python runtime and deployment environment.

---

## 9. Configuration and Environment Variables

Secrets and runtime settings must be externalized.

Example `.env.example`:

```
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2
OPENAI_MAX_OUTPUT_TOKENS=1200

# Embeddings
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_BATCH_SIZE=32
EMBEDDING_DEVICE=cpu

# Optional OpenAI embeddings
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=techbook_chunks

# Document storage
DOCUMENT_STORAGE_DIR=./data/documents
EXTRACTED_TEXT_DIR=./data/extracted
REGISTRY_DB_URL=sqlite:///./data/registry.db

# Chunking
CHUNK_SIZE_TOKENS=700
CHUNK_OVERLAP_TOKENS=105
MIN_CHUNK_SIZE_TOKENS=150
MAX_CHUNK_SIZE_TOKENS=1000

# Retrieval
DENSE_TOP_K=20
LEXICAL_TOP_K=20
FUSION_TOP_K=30
RERANKER_ENABLED=false
FINAL_CONTEXT_CHUNKS=6
MAX_CONTEXT_TOKENS=5000

# Security
ADMIN_API_KEY=
MAX_UPLOAD_SIZE_MB=100
MAX_QUERY_LENGTH=4000

# Observability
METRICS_ENABLED=true
TRACE_RETRIEVAL=true
```

These values are defaults for implementation planning and must be validated against the chosen models, machine, and deployment configuration.

### Configuration requirements

- `.env` must never be committed.
- `.env.example` must contain placeholders only.
- API keys must never be embedded in source code.
- Production secrets should be supplied through the deployment environment or a secrets manager.
- Configuration must be validated during startup.
- Invalid configurations must produce actionable startup errors.
- The application must never print secret values in logs.

---

## 10. Security, Guardrails, and Responsible AI

Guardrails are mandatory because retrieved documents may contain malicious instructions, incorrect claims, sensitive information, or content that the user is not authorized to access.

### 10.1 Prompt-injection defense

A PDF is a data source, not an instruction source.

The system must:

- Treat retrieved document content as untrusted evidence.
- Never follow instructions embedded in a retrieved passage that attempt to change system behavior.
- Ignore document instructions that ask the model to reveal secrets, system prompts, credentials, or internal configuration.
- Never allow retrieved text to override system-level policies.
- Clearly delimit evidence passages in the generation prompt.
- Avoid granting tool access merely because a retrieved passage requests it.
- Include adversarial PDF content in the security test suite.

### 10.2 Grounded-answer policy

The model must be instructed to:

- Answer using relevant retrieved evidence.
- State when evidence is insufficient.
- Avoid inventing book titles, authors, pages, or quotations.
- Distinguish conflicting sources instead of silently choosing one.
- Avoid presenting unsupported outside knowledge as a corpus-derived fact.
- Cite sources for substantive factual claims.
- Identify uncertainty when evidence is ambiguous.

The system should not claim that every answer is guaranteed to be correct merely because citations are present.

### 10.3 Citation guardrail

- Only evidence IDs supplied by the backend may be cited.
- Every citation must map to real metadata.
- Page numbers must come from the ingestion pipeline.
- Unsupported citation IDs must be rejected.
- Missing citations for factual answers must trigger a controlled fallback or regeneration.
- Citation validation must be independent of the LLM's self-reported confidence.

### 10.4 User-input validation

- Enforce maximum query length.
- Validate filters and pagination parameters.
- Reject malformed payloads.
- Limit upload size and supported file types.
- Apply request timeouts.
- Rate-limit expensive operations.
- Restrict administrative operations to authorized users.

### 10.5 File-upload security

- Treat PDFs as untrusted files.
- Validate PDF structure and file size.
- Apply processing time and memory limits.
- Avoid unsafe shell command construction.
- Run OCR and extraction in appropriately restricted processes.
- Do not execute embedded JavaScript, macros, or extracted code.
- Use temporary directories safely.
- Consider malware scanning in deployments that accept files from untrusted users.
- Prevent path traversal and unsafe filename handling.
- Avoid allowing uploads to overwrite arbitrary filesystem paths.

### 10.6 Code execution safety

Technical books may contain Python code, shell commands, and SQL examples.

The initial application must not automatically execute code extracted from documents.

If an execution feature is introduced later, it must use an isolated sandbox with resource limits, restricted networking, controlled filesystem access, and explicit authorization.

### 10.7 API key and data protection

- Keep the OpenAI API key on the server.
- Never return credentials to the frontend.
- Avoid logging raw API keys or authorization headers.
- Minimize the retention of user questions and generated answers.
- Do not transmit entire books to the generation provider; send only selected evidence and necessary instructions.
- Document that selected passages are sent to the configured LLM provider.
- Do not assume that using an API automatically satisfies every organization's privacy or compliance requirements.
- Provide a deletion mechanism for documents and associated index data.

### 10.8 Access control

For a single-user local demo, authentication may be minimal.

For shared or hosted deployment:

- Protect document upload and deletion.
- Restrict administrative APIs.
- Authenticate users.
- Enforce authorization on document retrieval.
- Ensure retrieval filters are applied before evidence reaches the LLM.
- Prevent cross-user access to private document collections.
- Avoid relying solely on frontend checks.

### 10.9 Resource exhaustion protection

- Limit upload size and page count.
- Bound OCR concurrency.
- Bound embedding batch size.
- Bound retrieval candidate count.
- Bound context tokens.
- Bound LLM output tokens.
- Use request timeouts.
- Apply queue backpressure.
- Limit concurrent generation requests.
- Record failures and retry only when appropriate.

### 10.10 Guardrail acceptance criteria

- A malicious instruction embedded in a PDF cannot override system behavior.
- Unknown citation IDs are rejected.
- Missing evidence produces an uncertainty response rather than a fabricated citation.
- Invalid uploads fail safely.
- No secret appears in application logs or API responses.
- Unauthorized users cannot access protected document data.
- The application does not execute retrieved code.

---

## 11. Non-Functional Requirements

## NFR-01: Latency

Target end-to-end query latency:

- Typical queries: 2–5 seconds.
- Retrieval: target approximately 100–500 ms under a documented local benchmark.
- Answer generation: target approximately 1–4 seconds for short answers when supported by the selected provider and model.
- p95 latency: measure and report; set a deployment-specific service-level target after baseline testing.

The latency budget is indicative, not a promise that every request will complete within five seconds.

The benchmark must define:

- Hardware specifications.
- Corpus size.
- Model names and versions.
- Whether model startup and warm-up are excluded.
- Query complexity.
- Context token budget.
- Concurrency.
- Network conditions.
- Whether streaming time-to-first-token or complete-response latency is measured.

Measure the complete request, including query embedding, retrieval, reranking, generation, and citation validation.

### Latency optimization strategies

- Precompute all document embeddings during ingestion.
- Use batched embedding generation.
- Keep the embedding model loaded in memory.
- Keep Qdrant available locally when practical.
- Use asynchronous I/O for API operations.
- Use bounded context sizes.
- Stream generated answers when supported.
- Avoid unnecessary LLM calls for routine retrieval.
- Use reranking only when its quality improvement justifies its latency.
- Cache safe, repeated query results where appropriate.
- Avoid embedding the full conversation history unnecessarily.
- Track provider-side latency separately from internal processing.

## NFR-02: Scalability

The initial release must support the minimum corpus and should be designed to scale beyond it.

Requirements:

- Incremental document ingestion.
- Batch embedding.
- Persistent vector storage.
- Configurable worker concurrency.
- Asynchronous ingestion jobs.
- Metadata filtering.
- Controlled memory use.
- Index rebuild and backup procedures.
- A documented migration path to more scalable registry or queue components.

## NFR-03: Reliability

- A failed PDF must not corrupt unrelated documents.
- A failed LLM request must return a controlled error.
- Database unavailability must be reported.
- Ingestion must be retryable.
- Partial indexing must not be marked complete.
- Repeated ingestion must not create uncontrolled duplicates.
- Application restarts must not erase persisted vectors.
- The system must expose health and readiness checks.

## NFR-04: Reproducibility

- Pin dependencies.
- Version the chunking pipeline.
- Version the embedding model and configuration.
- Record the corpus file hash.
- Record index configuration.
- Record retrieval configuration.
- Keep benchmark queries and expected source references under version control.
- Make ingestion deterministic for identical inputs and settings.
- Document the steps required to rebuild the corpus.

## NFR-05: Maintainability

- Separate API, ingestion, retrieval, generation, and UI modules.
- Use typed request and response models.
- Centralize configuration.
- Add unit and integration tests.
- Document interfaces and operational procedures.
- Keep provider-specific implementations behind abstractions.

## NFR-06: Accessibility and usability

- Provide clear loading and error states.
- Display readable citations.
- Preserve code formatting.
- Support keyboard navigation where practical.
- Make source inspection straightforward.
- Ensure the UI remains usable on standard laptop displays and smaller screens.

---

## 12. Evaluation and Quality Measurement

Evaluation must use a fixed benchmark dataset rather than subjective impressions alone.

### 12.1 Benchmark dataset

Create a manually reviewed dataset of at least 100 questions, preferably 150–200 as the project matures.

Include:

- Direct factual questions.
- Conceptual questions.
- Multi-document comparison questions.
- Questions requiring exact SQL or Python terminology.
- Questions involving tables or technical notation.
- Questions with multiple supporting passages.
- Ambiguous questions.
- Questions that cannot be answered from the corpus.
- Questions containing misleading assumptions.
- Questions about conflicting source statements.
- Adversarial prompt-injection cases.

Each benchmark item should include:

- `question_id`
- `query`
- `expected_answer_points`
- `relevant_document_ids`
- `relevant_chunk_ids` or page references
- `answerable`
- `expected_citations`
- `category`
- `difficulty`
- `review_notes`

### 12.2 Retrieval metrics

#### Recall@K

Measures whether at least one or more relevant chunks appear in the top K results.

Report Recall@5 and Recall@10, and optionally Recall@20.

#### Mean Reciprocal Rank (MRR)

Measures how highly the first relevant result is ranked.

#### nDCG@K

Measures ranking quality when relevance has graded levels.

#### Retrieval latency

Record p50, p95, and p99 latency where sample sizes support meaningful estimates.

### 12.3 Answer-quality metrics

Evaluate:

- Factual correctness.
- Evidence relevance.
- Answer groundedness.
- Citation precision.
- Citation completeness.
- Citation page accuracy.
- Appropriate abstention.
- Correct handling of conflicting sources.
- Preservation of technical details.

### 12.4 Hallucination evaluation

Measure whether answers contain material factual claims unsupported by retrieved evidence.

Use a manually reviewed sample as the primary quality check. Automated LLM-based evaluators may assist but must not be treated as infallible.

### 12.5 Initial target thresholds

These are proposed targets that must be validated against the actual corpus.

| Metric | Initial target |
| --- | --- |
| Document ingestion success | At least 95% of valid test PDFs |
| Recall@5 | At least 0.80 |
| Recall@10 | At least 0.90 |
| MRR | At least 0.70 |
| Citation page accuracy | At least 0.98 |
| Citation precision | At least 0.95 |
| Answer groundedness | At least 0.90 on the reviewed evaluation set |
| Appropriate abstention on unanswerable questions | At least 0.90 |
| Typical end-to-end latency | 2–5 seconds under the documented benchmark |

Metrics must be reported with sample sizes and evaluation methodology. Targets must not be represented as achieved until they have been measured.

### 12.6 Performance testing

Run tests for:

- Cold start.
- Warm queries.
- Short questions.
- Long questions.
- Large retrieval candidate pools.
- OCR-heavy documents.
- Concurrent queries.
- LLM rate limits.
- Database restarts.
- Slow or failed network requests.
- Large ingestion batches.

### 12.7 Regression testing

Every change to chunking, embeddings, retrieval, prompts, or generation settings must be tested against the benchmark set.

Compare the new metrics with the previous baseline and investigate significant regressions.

---

## 13. Observability and Monitoring

The system must provide enough telemetry to diagnose retrieval failures and latency problems.

### 13.1 Request-level metrics

- Request ID.
- Timestamp.
- Query length.
- Retrieval duration.
- Embedding duration.
- Lexical search duration.
- Reranking duration.
- Context construction duration.
- LLM time-to-first-token, when available.
- LLM total duration.
- Citation validation duration.
- Total request duration.
- Provider status.
- Retry count.
- Input and output token usage, when available.
- Number of retrieved and selected chunks.

### 13.2 Ingestion metrics

- Number of documents received.
- Number of pages processed.
- Number of pages requiring OCR.
- Extraction failure rate.
- OCR duration.
- Number of chunks generated.
- Embedding duration.
- Number of vectors indexed.
- Duplicate count.
- Failed jobs.
- Average and maximum document processing time.

### 13.3 Privacy-aware logging

Logs must not contain:

- API keys.
- Authorization headers.
- Secrets.
- Full private documents by default.
- Unnecessarily retained sensitive user queries.
- Entire prompts or model responses unless explicitly enabled for a controlled debugging environment.

### 13.4 Alerts

Where monitoring infrastructure is available, alert on:

- Repeated ingestion failures.
- Vector database unavailability.
- Elevated LLM error rates.
- Sustained p95 latency regressions.
- API quota exhaustion.
- Abnormally high OCR failure rates.
- Unexpected document deletion or index inconsistency.

---

## 14. Error Handling

The system must handle at least the following cases:

| Error | Expected behavior |
| --- | --- |
| Invalid PDF | Reject and explain the reason |
| Password-protected PDF | Report unsupported encryption or request an authorized unencrypted copy |
| Scanned PDF | Attempt OCR |
| OCR failure | Record page-level failure and continue where safe |
| Empty extracted text | Mark document failed or require manual review |
| Duplicate PDF | Apply configured duplicate policy |
| Embedding model unavailable | Report dependency failure; do not mark ingestion complete |
| Embedding batch failure | Retry safely and record failed batches |
| Qdrant unavailable | Return controlled service error |
| OpenAI rate limit | Apply bounded retry/backoff and return a controlled error if exhausted |
| OpenAI quota exhausted | Report provider configuration or billing issue without exposing secrets |
| LLM timeout | Return a controlled error or safe partial response if the implementation supports it |
| No relevant passages | Explain that the corpus did not provide sufficient evidence |
| Invalid citation ID | Reject or regenerate the answer |
| Malicious PDF instructions | Treat as untrusted document content |
| Oversized query | Reject with a clear validation error |
| Deleted document | Ensure its chunks are no longer eligible for retrieval |
| Corrupt index | Fail readiness checks and provide recovery instructions |

The application must not silently turn infrastructure failures into fabricated answers.

---

## 15. Project Structure

Recommended initial repository layout:

```
techbook-rag/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── documents.py
│   │   │   ├── jobs.py
│   │   │   └── chat.py
│   │   ├── schemas/
│   │   │   ├── document.py
│   │   │   ├── chat.py
│   │   │   └── common.py
│   │   └── middleware.py
│   │
│   ├── ingestion/
│   │   ├── pdf_loader.py
│   │   ├── ocr.py
│   │   ├── cleaner.py
│   │   ├── language.py
│   │   ├── chunker.py
│   │   ├── metadata.py
│   │   ├── embedder.py
│   │   └── pipeline.py
│   │
│   ├── retrieval/
│   │   ├── dense_search.py
│   │   ├── lexical_search.py
│   │   ├── fusion.py
│   │   ├── reranker.py
│   │   ├── filters.py
│   │   └── context_builder.py
│   │
│   ├── generation/
│   │   ├── client.py
│   │   ├── prompts.py
│   │   └── citations.py
│   │
│   ├── guardrails/
│   │   ├── input_validation.py
│   │   ├── prompt_injection.py
│   │   ├── citation_validation.py
│   │   └── output_validation.py
│   │
│   ├── storage/
│   │   ├── qdrant_store.py
│   │   ├── document_registry.py
│   │   └── job_store.py
│   │
│   ├── services/
│   │   ├── ingestion_service.py
│   │   ├── retrieval_service.py
│   │   └── chat_service.py
│   │
│   ├── observability/
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   └── tracing.py
│   │
│   └── ui/
│       └── streamlit_app.py
│
├── scripts/
│   ├── ingest_directory.py
│   ├── rebuild_index.py
│   ├── evaluate_retrieval.py
│   ├── evaluate_answers.py
│   └── inspect_corpus.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   ├── evaluation/
│   └── performance/
│
├── data/
│   ├── documents/
│   ├── extracted/
│   ├── indexes/
│   └── registry.db
│
├── evaluation/
│   ├── questions.jsonl
│   ├── expected_sources.jsonl
│   └── reports/
│
├── docker/
│   └── Dockerfile
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── SECURITY.md
└── prd.md
```

The directory structure is a proposed design. Files should be added as implementation progresses; empty placeholder modules should not be treated as completed functionality.

---

## 16. Testing Strategy

### 16.1 Unit tests

Test:

- PDF page extraction.
- OCR routing decisions.
- Text normalization.
- Chunk boundaries.
- Metadata construction.
- Stable chunk IDs.
- Embedding dimensions.
- Query validation.
- Retrieval filters.
- Citation mapping.
- Citation rejection.
- Prompt construction.
- Error serialization.

### 16.2 Integration tests

Test:

- PDF ingestion into Qdrant.
- Persistence after restart.
- Query embedding and retrieval.
- Hybrid retrieval.
- Reranking integration.
- OpenAI client integration using mocks where appropriate.
- Document deletion.
- Incremental re-ingestion.
- Citation rendering.
- API validation and authorization.

### 16.3 End-to-end tests

Test these complete user flows:

1. Upload a PDF.
2. Observe ingestion status.
3. Confirm indexing is complete.
4. Ask a question answerable from the book.
5. Inspect the retrieved chunks.
6. Verify the answer's citations.
7. Ask a follow-up question.
8. Ask a question outside the corpus.
9. Confirm that the system abstains appropriately.
10. Delete the document and verify that it is no longer retrievable.

### 16.4 Security tests

Test:

- Prompt injection in user input.
- Prompt injection embedded in PDFs.
- Attempts to expose system instructions.
- Attempts to expose API keys.
- Path traversal in uploaded filenames.
- Malformed PDFs.
- Oversized uploads.
- Unauthorized document deletion.
- Forged evidence IDs.
- Cross-user retrieval isolation in shared deployments.
- Resource exhaustion and excessive concurrency.

### 16.5 Regression tests

Maintain fixed benchmark queries and expected source references.

Every significant pipeline change must produce a comparable evaluation report.

---

## 17. Deployment Requirements

### 17.1 Local development

The application should run locally with:

- Python.
- A local embedding model.
- Qdrant.
- FastAPI.
- Streamlit.
- A configured OpenAI API key for generation.

### 17.2 Docker deployment

Docker Compose should define the required services, such as:

- API backend.
- Streamlit frontend.
- Qdrant.
- Optional ingestion worker.

Requirements:

- Persistent Qdrant volume.
- Persistent document storage.
- Environment-based configuration.
- Health checks.
- Restart policies where appropriate.
- No secrets baked into images.
- A documented startup procedure.
- A documented backup and restore procedure.

### 17.3 Production considerations

A public deployment must additionally consider:

- HTTPS.
- Authentication.
- API rate limiting.
- Upload quotas.
- Resource limits.
- Secret management.
- Monitoring.
- Backup retention.
- Access-control boundaries.
- Provider privacy requirements.
- Document retention and deletion policies.

### 17.4 Operational commands

The README must document how to:

- Install dependencies.
- Start Qdrant.
- Configure the OpenAI API key.
- Download the embedding model.
- Ingest the initial corpus.
- Start the backend.
- Start the frontend.
- Run tests.
- Run the evaluation suite.
- Rebuild the index.
- Back up the corpus and metadata.
- Restore a deployment.

---

## 18. Implementation Roadmap

### Phase 1: Project foundation

Tasks:

- Initialize the repository.
- Define configuration and environment handling.
- Set up FastAPI and Streamlit.
- Configure Qdrant.
- Create document and job schemas.
- Add health endpoints.
- Add logging and error handling.

Deliverable: The application starts successfully and all dependencies can be checked.

### Phase 2: PDF ingestion

Tasks:

- Implement PDF validation.
- Extract native text page by page.
- Implement OCR routing.
- Add text normalization.
- Preserve page provenance.
- Implement deterministic chunking.
- Create ingestion jobs and progress tracking.

Deliverable: The system extracts and chunks the initial PDF corpus.

### Phase 3: Embeddings and indexing

Tasks:

- Integrate the local embedding model.
- Implement batched embedding generation.
- Create Qdrant collection configuration.
- Store vectors and metadata.
- Implement duplicate detection.
- Implement incremental ingestion and deletion.
- Verify index persistence.

Deliverable: The minimum corpus is searchable in Qdrant.

### Phase 4: Retrieval

Tasks:

- Implement query embeddings.
- Implement dense retrieval.
- Implement lexical retrieval.
- Implement rank fusion.
- Add optional reranking.
- Add relevance filtering.
- Add retrieval diagnostics.

Deliverable: Queries return ranked passages with accurate provenance.

### Phase 5: Answer generation

Tasks:

- Integrate the OpenAI API.
- Create the grounded-answer prompt.
- Add context budgeting.
- Implement evidence-ID-based citations.
- Validate citation IDs.
- Implement uncertainty handling.
- Add bounded retries and provider error handling.

Deliverable: The chatbot produces evidence-grounded answers with citations.

### Phase 6: UI and visualization

Tasks:

- Build the chat interface.
- Add document management.
- Add ingestion status.
- Add source inspection.
- Display retrieval rankings and scores.
- Add evaluation metrics.
- Add user-friendly errors.

Deliverable: The complete application is usable through a web interface.

### Phase 7: Guardrails and testing

Tasks:

- Add prompt-injection defenses.
- Add upload validation.
- Add citation verification tests.
- Add retrieval benchmarks.
- Add answer-quality evaluation.
- Add latency measurement.
- Test provider failures.
- Test deletion and persistence.

Deliverable: The system has measurable quality and security characteristics.

### Phase 8: Optimization and demo readiness

Tasks:

- Tune chunk size and overlap.
- Compare embedding models.
- Tune hybrid retrieval.
- Evaluate reranking.
- Reduce unnecessary LLM calls.
- Optimize context length.
- Run performance tests.
- Document limitations and measured results.
- Prepare demonstration questions.

Deliverable: A reproducible, evaluated RAG demo.

---

## 19. Acceptance Criteria for Final Delivery

The project is considered ready for demonstration when all mandatory criteria below have been met.

### Corpus and ingestion

- [ ] At least 10 PDF books have been ingested.
- [ ] Every required PDF contains at least 200 pages.
- [ ] The total corpus contains at least 2,000 pages.
- [ ] Native extraction works on text-based PDFs.
- [ ] OCR works on representative scanned pages.
- [ ] Document metadata is stored.
- [ ] Chunk metadata includes accurate source page references.
- [ ] Embeddings are persisted in Qdrant.
- [ ] Re-ingestion and deletion behave correctly.

### Retrieval and generation

- [ ] Dense retrieval returns relevant passages.
- [ ] Lexical retrieval supports exact technical terminology.
- [ ] Hybrid ranking is implemented and evaluated.
- [ ] The LLM answers questions using retrieved evidence.
- [ ] Citations include the correct document and page.
- [ ] Unsupported questions receive an appropriate uncertainty response.
- [ ] Multi-turn follow-up questions work.
- [ ] Retrieved chunks can be inspected in the UI.

### Guardrails

- [ ] Retrieved instructions cannot override system policies.
- [ ] Citation IDs are validated.
- [ ] Invalid uploads fail safely.
- [ ] API keys remain server-side.
- [ ] Retrieved code is not executed automatically.
- [ ] Administrative endpoints are protected appropriately.

### Performance and quality

- [ ] End-to-end latency is measured.
- [ ] p50 and p95 latency are reported.
- [ ] Recall@K and MRR are calculated.
- [ ] Citation accuracy is evaluated.
- [ ] Unanswerable questions are tested.
- [ ] Benchmark results are reproducible.
- [ ] Performance claims match measured results.

### User interface and deployment

- [ ] Users can ask questions through the web UI.
- [ ] The ingestion pipeline is visualized.
- [ ] Retrieved chunks are displayed.
- [ ] Final answers contain citations.
- [ ] Errors are handled gracefully.
- [ ] Setup instructions are documented.
- [ ] The system can be restarted without losing persisted vectors.
- [ ] The project can be demonstrated from a clean environment using documented steps.

---

## 20. Demo Scenarios

The final demo should showcase both successful retrieval and deliberate failure handling.

### Scenario 1: SQL knowledge retrieval

Question:

"What is the difference between INNER JOIN and LEFT JOIN?"

Expected behavior:

- Retrieve relevant SQL passages.
- Explain the difference accurately.
- Include citations to the relevant book pages.
- Display the retrieved evidence.

### Scenario 2: Python technical explanation

Question:

"Explain the difference between a list and a tuple in Python."

Expected behavior:

- Retrieve relevant Python passages.
- Explain mutability and common use cases.
- Include source references.
- Preserve any relevant code examples.

### Scenario 3: Machine Learning comparison

Question:

"Compare supervised and unsupervised learning using the available books."

Expected behavior:

- Retrieve relevant passages from the ML corpus.
- Synthesize a comparison.
- Cite the sources supporting each major point.
- Identify differences in terminology across sources when relevant.

### Scenario 4: Multi-document reasoning

Question:

"How can feature scaling affect K-means clustering, and how does that differ from a tree-based model?"

Expected behavior:

- Retrieve passages about K-means, feature scaling, and tree-based algorithms.
- Synthesize a qualified answer.
- Cite the evidence supporting each comparison.
- Avoid overstating claims not supported by the corpus.

### Scenario 5: Unanswerable question

Question:

"What was the exact internal architecture of a private production system that is not mentioned in these books?"

Expected behavior:

- Search the corpus.
- Determine that sufficient evidence is unavailable.
- State that the provided books do not establish the answer.
- Avoid inventing details or citations.

### Scenario 6: Prompt injection

Place a test passage in a PDF that attempts to instruct the assistant to reveal its system prompt or API key.

Expected behavior:

- Treat the passage as untrusted content.
- Do not reveal secrets.
- Do not follow the malicious instruction.
- Continue to answer legitimate questions using relevant evidence.

### Scenario 7: Citation inspection

Ask a factual question and inspect the source references.

Expected behavior:

- Open the correct book and page reference.
- Display the actual retrieved passage.
- Confirm that the citation is supported by the stored metadata.

### Scenario 8: Performance demonstration

Run a fixed set of representative questions.

Expected behavior:

- Display actual retrieval and generation timings.
- Report p50 and p95 latency.
- Show the retrieval and generation configuration.
- Distinguish warm-query performance from cold-start performance.

---

## 21. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Poor OCR quality | Page-level quality checks, OCR preprocessing, and manual inspection of failures |
| Inaccurate retrieval | Hybrid search, chunk tuning, reranking, and benchmark-based evaluation |
| Incorrect citations | Evidence IDs and backend validation |
| Hallucinated answers | Grounded prompts, abstention, and answer-quality evaluation |
| Prompt injection | Treat document content as untrusted data and test adversarial PDFs |
| High latency | Precomputed embeddings, bounded context, profiling, and optional reranking |
| High LLM costs | Limit context and output tokens, monitor usage, and use local embeddings |
| Embedding model limitations | Benchmark alternative models before changing the default |
| Duplicate vectors | File hashing, stable chunk identifiers, and idempotent indexing |
| Index corruption | Persistent storage, backups, consistency checks, and documented rebuild procedures |
| Model version changes | Pin model revisions and re-evaluate before migration |
| Provider outages | Bounded retries and controlled errors; optional future local generation fallback |
| Large document processing times | Asynchronous workers and bounded concurrency |
| Copyright restrictions | Ingest only documents the project is authorized to use |
| Cross-user data leakage | Authorization-aware retrieval filters and isolation tests |

---

## 22. Cost and Resource Considerations

The application is designed to minimize recurring infrastructure expenses.

### Embeddings

The default local embedding model incurs no per-token embedding API fee. Hardware, electricity, and storage still have costs.

### Vector database

Self-hosted Qdrant avoids hosted vector-database subscription fees, but uses local storage and compute resources.

### OCR and PDF processing

PyMuPDF and Tesseract are open-source components. Processing large or scanned PDFs consumes CPU time and storage.

### Answer generation

OpenAI API usage is billed according to the selected model and applicable pricing.

Costs depend on:

- Input tokens.
- Output tokens.
- Model selection.
- Number of questions.
- Context size.
- Retry frequency.
- Whether query expansion or multiple generation calls are used.

### Cost controls

- Keep the corpus embeddings precomputed.
- Avoid re-embedding unchanged chunks.
- Use local query embeddings by default.
- Limit retrieved context to relevant passages.
- Set output-token limits.
- Track token usage per request.
- Cache appropriate repeated requests.
- Avoid multiple LLM calls unless they improve quality enough to justify the cost.

No fixed monetary total should be promised until the corpus, hardware, model, usage volume, and deployment environment have been specified.

---

## 23. Future Enhancements

After the first release is stable, consider:

- Local LLM generation as an alternative to OpenAI.
- OCR support for additional languages.
- Better table extraction.
- Diagram and figure understanding.
- Page previews in the source inspector.
- Query rewriting for difficult questions.
- Parent-child retrieval for long chapters.
- Contextual compression.
- Advanced reranking.
- Version-aware technical answers.
- User feedback on helpfulness and citation quality.
- Automated regression evaluation in CI.
- Distributed ingestion workers.
- Multi-user authentication and per-user collections.
- Document-level access control.
- Exportable conversation reports.
- More advanced observability and cost dashboards.

Future enhancements must be prioritized based on evaluation results rather than added solely for architectural complexity.

---

## 24. Definition of Done

The project is complete when:

1. The required corpus is ingested and searchable.
2. The application supports native extraction and OCR.
3. Embeddings are persisted in an open-source vector database.
4. The hybrid retrieval pipeline returns relevant source passages.
5. The OpenAI-powered answer generation pipeline produces grounded responses.
6. Citations are validated against stored metadata.
7. Users can inspect retrieved evidence in the web interface.
8. Guardrails are implemented and tested.
9. Retrieval quality and citation accuracy are evaluated.
10. End-to-end latency is measured under a documented configuration.
11. The project can be started from a clean environment using documented instructions.
12. The demo scenarios can be reproduced.
13. Known limitations and measured results are documented.

**Final deliverable:** A reproducible, web-accessible technical-book RAG chatbot with a minimum 10-book, 2,000-page corpus, open-source embeddings, self-hosted Qdrant, OpenAI-based answer generation, evidence-backed citations, retrieval visualization, security guardrails, and a documented evaluation report.

## Before you start implementation

A few important decisions will affect the code generated from this PRD:

- Embedding model: Start with local `BAAI/bge-small-en-v1.5`; switch only if your benchmark demonstrates a meaningful quality improvement.
- Vector database: Run Qdrant locally using Docker, with persistent storage.
- LLM: Use your OpenAI API key exclusively on the backend, never in Streamlit frontend code or browser-side JavaScript.
- Retrieval: Implement dense retrieval first, then add BM25 hybrid search and reranking after establishing a baseline.
- Latency: Measure the full pipeline from query submission through final answer. Do not claim the 2–5-second target has been achieved until you benchmark it.

One particularly important interview point: the quality of a RAG system depends as much on chunking, retrieval, evidence selection, and citation validation as it does on the LLM itself. Your demo should show not just the answer, but why the system retrieved the evidence used to produce it.
