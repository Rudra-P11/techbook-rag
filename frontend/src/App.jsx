import React, { useState, useEffect, useRef } from 'react';
import { 
  BookOpen, 
  Send, 
  Clock, 
  Layers, 
  CheckCircle2, 
  AlertCircle, 
  Upload, 
  Trash2, 
  ExternalLink, 
  X, 
  Database,
  Cpu,
  Sparkles,
  Terminal,
  FileText
} from 'lucide-react';

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am **TechBook RAG**, your intelligent knowledge assistant for technical books.\n\nAsk me anything about **SQL, Python, Machine Learning, Deep Learning, or Systems** grounded directly in your ingested library.',
      citations: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedSubjects, setSelectedSubjects] = useState([]);
  const [inspectorData, setInspectorData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef(null);

  // Poll health and document library
  const fetchData = async () => {
    try {
      const hRes = await fetch('/health');
      if (hRes.ok) {
        const hData = await hRes.json();
        setHealth(hData);
      }
      const dRes = await fetch('/api/v1/documents');
      if (dRes.ok) {
        const dData = await dRes.json();
        setDocuments(dData);
      }
    } catch (e) {
      console.warn('API unreachable:', e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (queryText) => {
    const q = queryText || input;
    if (!q.trim() || loading) return;

    const userMsg = { role: 'user', content: q.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q.trim(),
          filters: {
            subjects: selectedSubjects.length > 0 ? selectedSubjects : []
          },
          top_k: 6,
          include_retrieval_debug: true
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          citations: data.citations || [],
          metrics: data.metrics,
          retrieved_chunks: data.retrieved_chunks || []
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error communicating with TechBook RAG backend: ${err.message}`,
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/v1/documents', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        await fetchData();
      }
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document and its vector embeddings?')) return;
    try {
      await fetch(`/api/v1/documents/${docId}`, { method: 'DELETE' });
      await fetchData();
    } catch (e) {
      alert(`Failed to delete: ${e.message}`);
    }
  };

  const allSubjects = Array.from(new Set(documents.map((d) => d.subject).filter(Boolean)));

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-group">
            <div className="logo-icon">
              <BookOpen size={20} />
            </div>
            <div className="logo-text">
              <h1>TechBook RAG</h1>
              <span>Knowledge Assistant</span>
            </div>
          </div>
        </div>

        <div className="sidebar-content">
          {/* Status Box */}
          <div className="status-badge-container">
            <div className="status-row">
              <span className="status-label">Backend Service</span>
              <span className={`status-pill ${health ? 'online' : 'offline'}`}>
                {health ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                {health ? 'Connected' : 'Offline'}
              </span>
            </div>
            <div className="status-row">
              <span className="status-label">Total Indexed Vectors</span>
              <span className="status-pill online" style={{ background: 'rgba(99, 102, 241, 0.1)', color: '#a5b4fc', borderColor: 'rgba(99, 102, 241, 0.25)' }}>
                <Database size={12} />
                {health?.total_vectors ?? '—'}
              </span>
            </div>
            <div className="status-row">
              <span className="status-label">Embedding Model</span>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                bge-small-en-v1.5
              </span>
            </div>
          </div>

          {/* Subject Filter */}
          {allSubjects.length > 0 && (
            <div>
              <div className="section-title">Filter By Subject</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {allSubjects.map((sub) => {
                  const active = selectedSubjects.includes(sub);
                  return (
                    <button
                      key={sub}
                      onClick={() =>
                        setSelectedSubjects((prev) =>
                          active ? prev.filter((s) => s !== sub) : [...prev, sub]
                        )
                      }
                      className="prompt-chip"
                      style={{
                        background: active ? 'rgba(99, 102, 241, 0.25)' : undefined,
                        borderColor: active ? 'var(--accent-primary)' : undefined,
                        color: active ? '#fff' : undefined
                      }}
                    >
                      {sub}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Document Ingestion & List */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div className="section-title" style={{ margin: 0 }}>Corpus Library ({documents.length})</div>
              <label className="btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', cursor: 'pointer' }}>
                <Upload size={12} />
                {uploading ? 'Uploading...' : 'Add PDF'}
                <input type="file" accept=".pdf" onChange={handleFileUpload} style={{ display: 'none' }} />
              </label>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {documents.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: '#64748b', textAlign: 'center', padding: '16px' }}>
                  No books indexed yet.
                </div>
              ) : (
                documents.map((doc) => (
                  <div key={doc.document_id} className="doc-item">
                    <div className="doc-header">
                      <span className="doc-name">{doc.display_name}</span>
                      <button
                        onClick={() => handleDelete(doc.document_id)}
                        style={{ background: 'transparent', color: '#64748b', padding: '2px' }}
                        title="Delete book"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                    <div className="doc-meta">
                      <span className="doc-tag">{doc.subject}</span>
                      <span>{doc.page_count} pages</span>
                      <span>•</span>
                      <span>{doc.chunk_count} chunks</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="main-chat-area">
        {/* Top Navbar */}
        <header className="top-navbar">
          <div className="nav-title">
            <Sparkles size={18} color="var(--accent-primary)" />
            <h2>Interactive RAG Chat Workspace</h2>
          </div>
          <div className="nav-actions">
            <button
              className="btn-secondary"
              onClick={() =>
                setMessages([
                  {
                    role: 'assistant',
                    content: 'Conversation cleared. What technical topic would you like to explore?',
                    citations: []
                  }
                ])
              }
            >
              Clear Chat
            </button>
          </div>
        </header>

        {/* Messages Stream */}
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-wrapper ${msg.role}`}>
              <div className={`avatar ${msg.role}`}>
                {msg.role === 'user' ? 'U' : <Cpu size={18} />}
              </div>
              <div className="message-bubble">
                <div className="message-text">{msg.content}</div>

                {/* Inline Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="citations-container">
                    <span className="citations-label">Sources:</span>
                    {msg.citations.map((c, cIdx) => (
                      <span
                        key={cIdx}
                        className="citation-chip"
                        onClick={() => setInspectorData(msg.retrieved_chunks || [])}
                        title="Click to view full evidence passage"
                      >
                        <FileText size={12} />
                        {c.title} (p. {c.pages.join(', ')})
                      </span>
                    ))}
                  </div>
                )}

                {/* Latency & Telemetry */}
                {msg.metrics && (
                  <div className="metrics-pill">
                    <span className="metric-item">
                      <Clock size={12} />
                      Retrieval: <span className="metric-value">{msg.metrics.retrieval_latency_ms}ms</span>
                    </span>
                    <span>•</span>
                    <span className="metric-item">
                      Generation: <span className="metric-value">{msg.metrics.generation_latency_ms}ms</span>
                    </span>
                    <span>•</span>
                    <span className="metric-item">
                      Total: <span className="metric-value">{msg.metrics.total_latency_ms}ms</span>
                    </span>
                    {msg.retrieved_chunks && msg.retrieved_chunks.length > 0 && (
                      <>
                        <span>•</span>
                        <button
                          onClick={() => setInspectorData(msg.retrieved_chunks)}
                          style={{ background: 'transparent', color: 'var(--accent-primary)', fontSize: '0.74rem', textDecoration: 'underline' }}
                        >
                          Inspect {msg.retrieved_chunks.length} Passages
                        </button>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-wrapper assistant">
              <div className="avatar assistant">
                <Cpu size={18} />
              </div>
              <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>
                  Retrieving passages & synthesizing grounded answer...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Sample Prompts */}
        <div className="prompt-chips-wrapper">
          <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Try:</span>
          {[
            'Explain INNER JOIN vs LEFT JOIN in SQL',
            'What is the difference between list and tuple in Python?',
            'Compare supervised and unsupervised learning',
            'What is a forward pass in a neural network?'
          ].map((promptText) => (
            <button
              key={promptText}
              className="prompt-chip"
              onClick={() => handleSend(promptText)}
            >
              {promptText}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="input-dock">
          <div className="input-container">
            <textarea
              className="chat-textarea"
              placeholder="Ask a technical question grounded in your PDF books (e.g. SQL joins, backprop, data structures)..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              rows={1}
            />
            <button
              className="send-btn"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </main>

      {/* Slide-out Retrieval Inspector Drawer */}
      {inspectorData && (
        <div className="drawer-backdrop" onClick={() => setInspectorData(null)}>
          <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="var(--accent-primary)" />
                <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Retrieval Inspector</h3>
              </div>
              <button
                onClick={() => setInspectorData(null)}
                style={{ background: 'transparent', color: '#94a3b8' }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="drawer-content">
              <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                Showing evidence passages retrieved across dense ANN similarity and BM25 lexical ranking:
              </div>

              {inspectorData.map((chunk, i) => (
                <div key={i} className="evidence-card">
                  <div className="evidence-header">
                    <div>
                      <span className="evidence-tag">Evidence [E{i + 1}]</span>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', marginTop: '4px' }}>
                        {chunk.title}
                      </div>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#06b6d4', fontFamily: 'monospace' }}>
                      Score: {chunk.score}
                    </div>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    Pages: {chunk.page_numbers?.join(', ')} • Subject: {chunk.subject || 'General'}
                  </div>

                  <div className="evidence-snippet">{chunk.text_preview}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
