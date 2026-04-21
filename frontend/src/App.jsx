import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [documents, setDocuments] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [summary, setSummary] = useState("");
  const [level, setLevel] = useState("medium");

  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDocuments();
  }, []);

  async function safeJson(response) {
    const text = await response.text();
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  async function loadDocuments() {
    try {
      setLoadingDocuments(true);
      setError("");

      const res = await fetch(`${API}/documents`);
      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to load documents");
      }

      setDocuments(data);
    } catch (err) {
      setError(err.message || "Failed to load documents");
    } finally {
      setLoadingDocuments(false);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      setError("");
      setSummary("");

      const form = new FormData();
      form.append("file", file);

      const uploadRes = await fetch(`${API}/upload`, {
        method: "POST",
        body: form,
      });

      const uploaded = await safeJson(uploadRes);

      if (!uploadRes.ok) {
        throw new Error(uploaded?.detail || "Upload failed");
      }

      await loadDocuments();
      await selectDocument(uploaded.id);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function selectDocument(id) {
    try {
      setLoadingChapters(true);
      setError("");
      setSummary("");
      setSelectedChapter(null);

      const [docRes, chapRes] = await Promise.all([
        fetch(`${API}/documents/${id}`),
        fetch(`${API}/documents/${id}/chapters`),
      ]);

      const doc = await safeJson(docRes);
      const chapList = await safeJson(chapRes);

      if (!docRes.ok) {
        throw new Error(doc?.detail || "Failed to load document");
      }

      if (!chapRes.ok) {
        throw new Error(chapList?.detail || "Failed to load chapters");
      }

      setSelectedDoc(doc);
      setChapters(chapList);

      if (chapList.length > 0) {
        await selectChapter(chapList[0].id, false);
      }
    } catch (err) {
      setError(err.message || "Failed to load document");
    } finally {
      setLoadingChapters(false);
    }
  }

  async function selectChapter(id, clearSummary = true) {
    try {
      setError("");
      if (clearSummary) setSummary("");

      const res = await fetch(`${API}/chapters/${id}`);
      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to load chapter");
      }

      setSelectedChapter(data);
    } catch (err) {
      setError(err.message || "Failed to load chapter");
    }
  }

  async function summarizeChapter() {
    if (!selectedDoc || !selectedChapter) return;

    try {
      setSummarizing(true);
      setError("");

      const res = await fetch(`${API}/summarize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document_id: selectedDoc.id,
          chapter_id: selectedChapter.id,
          level,
        }),
      });

      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to summarize chapter");
      }

      setSummary(data.summary_text);
    } catch (err) {
      setError(err.message || "Failed to summarize chapter");
    } finally {
      setSummarizing(false);
    }
  }

  async function summarizeDocument() {
    if (!selectedDoc) return;

    try {
      setSummarizing(true);
      setError("");

      const res = await fetch(`${API}/summarize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document_id: selectedDoc.id,
          level,
        }),
      });

      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to summarize document");
      }

      setSummary(data.summary_text);
    } catch (err) {
      setError(err.message || "Failed to summarize document");
    } finally {
      setSummarizing(false);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Document Reader AI</h1>
          <p>Upload, read by chapter, and summarize documents.</p>
        </div>

        <label className="upload-button">
          {uploading ? "Uploading..." : "Upload file"}
          <input
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
      </header>

      {error && <div className="error-box">{error}</div>}

      <div className="grid">
        <aside className="panel">
          <div className="panel-header">
            <h2>Documents</h2>
            {loadingDocuments && <span className="badge">Loading...</span>}
          </div>

          {documents.length === 0 ? (
            <p className="empty-text">No documents uploaded yet.</p>
          ) : (
            <div className="list">
              {documents.map((doc) => (
                <button
                  key={doc.id}
                  className={`list-item ${selectedDoc?.id === doc.id ? "active" : ""}`}
                  onClick={() => selectDocument(doc.id)}
                >
                  <div className="item-title">{doc.title}</div>
                  <div className="item-meta">
                    {doc.file_type.toUpperCase()} • ID {doc.id}
                  </div>
                </button>
              ))}
            </div>
          )}
        </aside>

        <aside className="panel">
          <div className="panel-header">
            <h2>Chapters</h2>
            {loadingChapters && <span className="badge">Loading...</span>}
          </div>

          {chapters.length === 0 ? (
            <p className="empty-text">Select a document to view chapters.</p>
          ) : (
            <div className="list">
              {chapters.map((chapter) => (
                <button
                  key={chapter.id}
                  className={`list-item ${selectedChapter?.id === chapter.id ? "active" : ""}`}
                  onClick={() => selectChapter(chapter.id)}
                >
                  <div className="item-title">
                    {chapter.chapter_index}. {chapter.title}
                  </div>
                  <div className="item-meta">
                    {chapter.paragraph_count} paragraphs • {chapter.sentence_count} sentences
                  </div>
                </button>
              ))}
            </div>
          )}
        </aside>

        <main className="main-panel">
          <section className="panel">
            <div className="panel-header">
              <h2>Reader</h2>
            </div>

            {!selectedDoc ? (
              <p className="empty-text">Choose a document to start reading.</p>
            ) : !selectedChapter ? (
              <p className="empty-text">Choose a chapter to view its content.</p>
            ) : (
              <>
                <div className="reader-meta">
                  <h3>{selectedDoc.title}</h3>
                  <p>
                    Chapter {selectedChapter.chapter_index}: {selectedChapter.title}
                  </p>
                </div>

                <div className="reader-content">
                  {selectedChapter.raw_text.split("\n").map((line, idx) => (
                    <p key={idx}>{line.trim() === "" ? "\u00A0" : line}</p>
                  ))}
                </div>
              </>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Summary</h2>
            </div>

            <div className="summary-controls">
              <select value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="short">short</option>
                <option value="medium">medium</option>
                <option value="long">long</option>
              </select>

              <div className="button-row">
                <button
                  className="primary-btn"
                  onClick={summarizeChapter}
                  disabled={!selectedDoc || !selectedChapter || summarizing}
                >
                  {summarizing ? "Summarizing..." : "Summarize Chapter"}
                </button>

                <button
                  className="secondary-btn"
                  onClick={summarizeDocument}
                  disabled={!selectedDoc || summarizing}
                >
                  {summarizing ? "Summarizing..." : "Summarize Document"}
                </button>
              </div>
            </div>

            <div className="summary-box">
              {summary ? (
                summary
              ) : (
                <span className="empty-text">
                  No summary yet. Choose a level and summarize a chapter or the whole document.
                </span>
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;