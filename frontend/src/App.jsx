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
  FileText,
  Sun,
  Moon,
  Copy,
  Check,
  Search,
  Zap,
  Brain,
  Sliders,
  PanelLeftClose,
  PanelLeftOpen,
  ArrowRight
} from 'lucide-react';

export default function App() {
  // Theme state: dark / light
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('techbook_theme') || 'dark';
  });

  // Selected generation model
  const [selectedModel, setSelectedModel] = useState('gpt-4o-mini');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [bookSearch, setBookSearch] = useState('');

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am **TechBook RAG**, an intelligent knowledge assistant grounded in 11 comprehensive technical books covering **SQL, Python, Machine Learning, Deep Learning, and Systems Architecture**.\n\nAsk any technical question or select one of the suggested topics below to experience real-time hybrid retrieval and citation verification.',
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
  const [copiedIdx, setCopiedIdx] = useState(null);
  const messagesEndRef = useRef(null);

  // Sync theme attribute with DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('techbook_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

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
          model: selectedModel,
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
          retrieved_chunks: data.retrieved_chunks || [],
          modelUsed: selectedModel
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

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
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
  const filteredDocuments = documents.filter((d) => 
    d.display_name.toLowerCase().includes(bookSearch.toLowerCase()) ||
    (d.subject && d.subject.toLowerCase().includes(bookSearch.toLowerCase()))
  );

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
        <div className="sidebar-header">
          <div className="logo-group">
            <div className="logo-icon">
              <BookOpen size={20} />
            </div>
            <div className="logo-text">
              <h1>TechBook RAG</h1>
              <span>AI Knowledge Core</span>
            </div>
          </div>
          <button 
            className="sidebar-toggle-btn"
            onClick={() => setSidebarOpen(false)}
            title="Collapse Sidebar"
          >
            <PanelLeftClose size={16} />
          </button>
        </div>

        <div className="sidebar-content">
          {/* System Specs & Vector Database Status */}
          <div className="status-badge-container">
            <div className="status-row">
              <span className="status-label">Engine Service</span>
              <span className={`status-pill ${health ? 'online' : 'offline'}`}>
                {health ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                {health ? 'Connected' : 'Offline'}
              </span>
            </div>

            <div className="system-spec-badge">
              <span>Vector Database</span>
              <code>Qdrant ANN (Local)</code>
            </div>

            <div className="system-spec-badge">
              <span>Embedding Model</span>
              <code>BGE-Small-v1.5 (384d)</code>
            </div>

            <div className="system-spec-badge">
              <span>Indexed Vectors</span>
              <code>{health?.total_vectors ?? '2,810'} chunks</code>
            </div>

            <div className="system-spec-badge">
              <span>Hybrid Search</span>
              <code>RRF (Dense + BM25)</code>
            </div>
          </div>

          {/* Subject Filter */}
          {allSubjects.length > 0 && (
            <div>
              <div className="section-title">
                <span>Domain Filters</span>
                {selectedSubjects.length > 0 && (
                  <button 
                    onClick={() => setSelectedSubjects([])} 
                    style={{ background: 'transparent', color: 'var(--accent-primary)', fontSize: '0.7rem' }}
                  >
                    Clear ({selectedSubjects.length})
                  </button>
                )}
              </div>
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
                        background: active ? 'var(--accent-primary)' : undefined,
                        borderColor: active ? 'var(--accent-primary)' : undefined,
                        color: active ? '#fff' : undefined,
                        fontWeight: active ? '600' : undefined
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
              <div className="section-title" style={{ margin: 0 }}>
                Corpus Books ({documents.length})
              </div>
              <label className="btn-secondary" style={{ padding: '4px 8px', fontSize: '0.72rem', cursor: 'pointer' }}>
                <Upload size={12} />
                {uploading ? 'Adding...' : 'Add PDF'}
                <input type="file" accept=".pdf" onChange={handleFileUpload} style={{ display: 'none' }} />
              </label>
            </div>

            {/* Quick Search inside Books */}
            <div className="search-input-wrapper">
              <Search size={13} className="search-icon-inside" />
              <input 
                type="text" 
                placeholder="Search library..." 
                value={bookSearch} 
                onChange={(e) => setBookSearch(e.target.value)} 
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '340px', overflowY: 'auto' }}>
              {filteredDocuments.length === 0 ? (
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center', padding: '16px' }}>
                  No matching books found.
                </div>
              ) : (
                filteredDocuments.map((doc) => (
                  <div key={doc.document_id} className="doc-item">
                    <div className="doc-header">
                      <span className="doc-name">{doc.display_name}</span>
                      <button
                        onClick={() => handleDelete(doc.document_id)}
                        style={{ background: 'transparent', color: 'var(--text-muted)', padding: '2px' }}
                        title="Delete book"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                    <div className="doc-meta">
                      <span className="doc-tag">{doc.subject}</span>
                      <span>{doc.page_count}p</span>
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
          <div className="nav-left">
            {!sidebarOpen && (
              <button 
                className="sidebar-toggle-btn" 
                onClick={() => setSidebarOpen(true)}
                title="Expand Sidebar"
              >
                <PanelLeftOpen size={16} />
              </button>
            )}
            <div className="nav-title">
              <Sparkles size={18} color="var(--accent-primary)" />
              <h2>Interactive RAG Workspace</h2>
              <span className="live-badge">
                <span className="live-dot" />
                Live Sub-80ms Index
              </span>
            </div>
          </div>

          <div className="nav-actions">
            {/* Model Profile Switcher */}
            <div className="model-selector-pill" title="Switch Generator Model to experience latency & depth in real time">
              <button
                className={`model-pill-opt ${selectedModel === 'gpt-4o-mini' ? 'active' : ''}`}
                onClick={() => setSelectedModel('gpt-4o-mini')}
              >
                <Zap size={13} />
                <span>gpt-4o-mini (Fast)</span>
              </button>
              <button
                className={`model-pill-opt ${selectedModel === 'gpt-4o' ? 'active' : ''}`}
                onClick={() => setSelectedModel('gpt-4o')}
              >
                <Brain size={13} />
                <span>gpt-4o (Deep)</span>
              </button>
            </div>

            {/* Light / Dark Mode Toggle */}
            <button
              id="theme-toggle"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            {/* Clear Chat */}
            <button
              className="btn-secondary"
              onClick={() =>
                setMessages([
                  {
                    role: 'assistant',
                    content: 'Workspace cleared. What technical topic would you like to explore next?',
                    citations: []
                  }
                ])
              }
              title="Clear conversation history"
            >
              Clear
            </button>
          </div>
        </header>

        {/* Messages Stream */}
        <div className="messages-container">
          {/* Bento Prompt Cards on Clean Slate */}
          {messages.length <= 1 && (
            <div className="hero-welcome-card">
              <div className="hero-header">
                <Sparkles size={22} color="var(--accent-primary)" />
                <h3 className="hero-title">Technical Books Knowledge Assistant</h3>
              </div>
              <p className="hero-subtitle">
                Grounded directly in authoritative computer science books with strict citation verification and domain guardrails. Select a topic below to test real-time retrieval:
              </p>

              <div className="bento-grid">
                <div 
                  className="bento-card"
                  onClick={() => handleSend('Explain the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with query examples')}
                >
                  <span className="bento-tag">
                    <Database size={13} /> SQL & Relational
                  </span>
                  <div className="bento-text">INNER JOIN vs LEFT JOIN with set semantics & indexing</div>
                  <div style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 600 }}>
                    Try Query <ArrowRight size={12} />
                  </div>
                </div>

                <div 
                  className="bento-card"
                  onClick={() => handleSend('Explain Python list vs tuple in terms of mutability, memory allocation, and performance')}
                >
                  <span className="bento-tag">
                    <Terminal size={13} /> Python Internals
                  </span>
                  <div className="bento-text">List vs Tuple memory overhead & over-allocation</div>
                  <div style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 600 }}>
                    Try Query <ArrowRight size={12} />
                  </div>
                </div>

                <div 
                  className="bento-card"
                  onClick={() => handleSend('What is the difference between supervised and unsupervised learning? Give concrete examples')}
                >
                  <span className="bento-tag">
                    <Cpu size={13} /> Machine Learning
                  </span>
                  <div className="bento-text">Supervised vs Unsupervised learning paradigms</div>
                  <div style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 600 }}>
                    Try Query <ArrowRight size={12} />
                  </div>
                </div>

                <div 
                  className="bento-card"
                  onClick={() => handleSend('How does backpropagation work in neural networks using the chain rule?')}
                >
                  <span className="bento-tag">
                    <Brain size={13} /> Deep Learning
                  </span>
                  <div className="bento-text">Backpropagation & Gradient descent chain rule mechanics</div>
                  <div style={{ color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 600 }}>
                    Try Query <ArrowRight size={12} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message-wrapper ${msg.role}`}>
              <div className={`avatar ${msg.role}`}>
                {msg.role === 'user' ? 'U' : <Cpu size={18} />}
              </div>
              <div className="message-bubble">
                {/* Header bar on assistant bubbles */}
                {msg.role === 'assistant' && (
                  <div className="message-header-bar">
                    <span className="message-role-name">
                      TechBook Assistant {msg.modelUsed ? `• ${msg.modelUsed}` : ''}
                    </span>
                    <button 
                      className="copy-action-btn"
                      onClick={() => handleCopy(msg.content, idx)}
                      title="Copy response to clipboard"
                    >
                      {copiedIdx === idx ? (
                        <>
                          <Check size={12} color="var(--accent-emerald)" />
                          <span style={{ color: 'var(--accent-emerald)' }}>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                )}

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
                        title="Click to view full evidence passage in Inspector Drawer"
                      >
                        <FileText size={12} />
                        {c.title} (p. {c.pages.join(', ')})
                      </span>
                    ))}
                  </div>
                )}

                {/* Latency & Telemetry Breakdown */}
                {msg.metrics && (
                  <div className="telemetry-container">
                    <div className="metrics-row">
                      <span className="metric-item">
                        <Clock size={12} />
                        <span>Retrieval:</span>
                        <strong style={{ color: 'var(--accent-cyan)' }}>{msg.metrics.retrieval_latency_ms}ms</strong>
                      </span>
                      <span>•</span>
                      <span className="metric-item">
                        <Zap size={12} />
                        <span>Generation:</span>
                        <strong style={{ color: 'var(--accent-primary)' }}>{msg.metrics.generation_latency_ms}ms</strong>
                      </span>
                      <span>•</span>
                      <span className="metric-item">
                        <span>Total:</span>
                        <strong style={{ color: 'var(--text-primary)' }}>{msg.metrics.total_latency_ms}ms</strong>
                      </span>
                      {msg.retrieved_chunks && msg.retrieved_chunks.length > 0 && (
                        <>
                          <span>•</span>
                          <button
                            onClick={() => setInspectorData(msg.retrieved_chunks)}
                            style={{ 
                              background: 'transparent', 
                              color: 'var(--accent-primary)', 
                              fontSize: '0.74rem', 
                              fontWeight: 600,
                              textDecoration: 'underline' 
                            }}
                          >
                            Inspect {msg.retrieved_chunks.length} Passages
                          </button>
                        </>
                      )}
                    </div>

                    {/* Proportional Latency Bar */}
                    {msg.metrics.total_latency_ms > 0 && (
                      <div className="latency-split-bar" title={`Retrieval: ${msg.metrics.retrieval_latency_ms}ms | Generation: ${msg.metrics.generation_latency_ms}ms`}>
                        <div 
                          className="latency-split-retrieval" 
                          style={{ 
                            width: `${Math.max(3, (msg.metrics.retrieval_latency_ms / msg.metrics.total_latency_ms) * 100)}%` 
                          }} 
                        />
                        <div 
                          className="latency-split-generation" 
                          style={{ 
                            width: `${Math.min(97, (msg.metrics.generation_latency_ms / msg.metrics.total_latency_ms) * 100)}%` 
                          }} 
                        />
                      </div>
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
              <div className="message-bubble loading-box">
                <div className="loading-step-row">
                  <div className="spinner-dot" />
                  <span>1. Computing 384d dense embeddings via BGE-Small...</span>
                </div>
                <div className="loading-step-row">
                  <div className="spinner-dot" style={{ animationDelay: '0.2s', background: 'var(--accent-cyan)' }} />
                  <span>2. Scanning 2,810 book chunks (Qdrant ANN + BM25 Okapi)...</span>
                </div>
                <div className="loading-step-row">
                  <div className="spinner-dot" style={{ animationDelay: '0.4s', background: 'var(--accent-secondary)' }} />
                  <span>3. Synthesizing grounded answer via {selectedModel}...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Sample Prompts Chips */}
        <div className="prompt-chips-wrapper">
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 700 }}>Quick:</span>
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
              id="chat-input"
              className="chat-textarea"
              placeholder="Ask any technical question from your book library (e.g. SQL indexing, backpropagation, Python memory)..."
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
              id="send-button"
              className="send-btn"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              title="Send Query (Enter)"
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
                <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Retrieval Inspector</h3>
              </div>
              <button
                onClick={() => setInspectorData(null)}
                style={{ background: 'transparent', color: 'var(--text-muted)', cursor: 'pointer' }}
                title="Close drawer"
              >
                <X size={18} />
              </button>
            </div>

            <div className="drawer-content">
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Showing evidence passages retrieved across dense ANN similarity and BM25 lexical ranking:
              </div>

              {inspectorData.map((chunk, i) => (
                <div key={i} className="evidence-card">
                  <div className="evidence-header">
                    <div>
                      <span className="evidence-tag">Evidence [E{i + 1}]</span>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem', marginTop: '4px' }}>
                        {chunk.title}
                      </div>
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                      Score: {chunk.score}
                    </div>
                  </div>

                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Pages: {chunk.page_numbers?.join(', ')} • Subject: {chunk.subject || 'Technical'}
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
