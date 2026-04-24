import { useEffect, useRef, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";
const CHUNK_SIZE = 10;

function App() {
  const [documents, setDocuments] = useState([]);
  const [chapters, setChapters] = useState([]);

  const [selectedDoc, setSelectedDoc] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);

  const [chunks, setChunks] = useState([]);
  const [chunkPage, setChunkPage] = useState(1);
  const [hasMoreChunks, setHasMoreChunks] = useState(false);
  const [totalChunks, setTotalChunks] = useState(0);

  const [summary, setSummary] = useState("");
  const [level, setLevel] = useState("medium");

  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [error, setError] = useState("");

  const loaderRef = useRef(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    if (!loaderRef.current || !selectedDoc || !hasMoreChunks) return;

    const observer = new IntersectionObserver((entries) => {
      const first = entries[0];

      if (first.isIntersecting && !loadingChunks && hasMoreChunks) {
        loadMoreChunks();
      }
    });

    observer.observe(loaderRef.current);

    return () => observer.disconnect();
  }, [selectedDoc, chunkPage, hasMoreChunks, loadingChunks]);

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

      const form = new FormData();
      form.append("file", file);

      const res = await fetch(`${API}/upload`, {
        method: "POST",
        body: form,
      });

      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Upload failed");
      }

      await loadDocuments();
      await openDocument(data.id);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function openDocument(documentId) {
    try {
      setError("");
      setSummary("");
      setChunks([]);
      setChunkPage(1);
      setHasMoreChunks(false);
      setTotalChunks(0);
      setSelectedChapter(null);

      const docRes = await fetch(`${API}/documents/${documentId}`);
      const doc = await safeJson(docRes);

      if (!docRes.ok) {
        throw new Error(doc?.detail || "Failed to load document");
      }

      setSelectedDoc(doc);

      await Promise.all([
        loadChapters(documentId),
        loadInitialChunks(documentId),
      ]);
    } catch (err) {
      setError(err.message || "Failed to open document");
    }
  }

  async function loadChapters(documentId) {
    try {
      setLoadingChapters(true);

      const res = await fetch(`${API}/documents/${documentId}/chapters`);
      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to load chapters");
      }

      setChapters(data);
    } catch (err) {
      setError(err.message || "Failed to load chapters");
    } finally {
      setLoadingChapters(false);
    }
  }

  async function loadInitialChunks(documentId) {
    try {
      setLoadingChunks(true);

      const res = await fetch(
        `${API}/documents/${documentId}/chunks?page=1&size=${CHUNK_SIZE}`
      );
      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to load document chunks");
      }

      setChunks(data.chunks || []);
      setChunkPage(1);
      setHasMoreChunks(data.has_more);
      setTotalChunks(data.total);
    } catch (err) {
      setError(err.message || "Failed to load document chunks");
    } finally {
      setLoadingChunks(false);
    }
  }

  async function loadMoreChunks() {
    if (!selectedDoc || loadingChunks || !hasMoreChunks) return;

    try {
      setLoadingChunks(true);

      const nextPage = chunkPage + 1;

      const res = await fetch(
        `${API}/documents/${selectedDoc.id}/chunks?page=${nextPage}&size=${CHUNK_SIZE}`
      );
      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to load more chunks");
      }

      setChunks((prev) => [...prev, ...(data.chunks || [])]);
      setChunkPage(nextPage);
      setHasMoreChunks(data.has_more);
      setTotalChunks(data.total);
    } catch (err) {
      setError(err.message || "Failed to load more chunks");
    } finally {
      setLoadingChunks(false);
    }
  }

  async function selectChapter(chapterId) {
    try {
      setError("");
      setSummary("");

      const res = await fetch(`${API}/chapters/${chapterId}`);
      const data = await safeJson(res);

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to load chapter");
      }

      setSelectedChapter(data);
      setChunks([data.raw_text]);
      setHasMoreChunks(false);
      setTotalChunks(1);
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

  function showFullDocumentAgain() {
    if (!selectedDoc) return;
    setSelectedChapter(null);
    setSummary("");
    setChunks([]);
    setChunkPage(1);
    setHasMoreChunks(false);
    loadInitialChunks(selectedDoc.id);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Document Reader AI</h1>
          <p>Lazy reader: short documents load fully, long books load by chunks.</p>
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

      <div className="reader-layout">
        <aside className="sidebar">
          <div className="panel">
            <div className="panel-header">
              <h2>Documents</h2>
              {loadingDocuments && <span className="badge">Loading</span>}
            </div>

            {documents.length === 0 ? (
              <p className="empty-text">No documents uploaded.</p>
            ) : (
              <div className="list">
                {documents.map((doc) => (
                  <button
                    key={doc.id}
                    className={`list-item ${
                      selectedDoc?.id === doc.id ? "active" : ""
                    }`}
                    onClick={() => openDocument(doc.id)}
                  >
                    <div className="item-title">{doc.title}</div>
                    <div className="item-meta">
                      {doc.file_type.toUpperCase()} • ID {doc.id}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="panel">
            <div className="panel-header">
              <h2>Mục lục</h2>
              {loadingChapters && <span className="badge">Loading</span>}
            </div>

            {selectedDoc && (
              <button className="outline-btn full-width" onClick={showFullDocumentAgain}>
                Xem toàn tài liệu
              </button>
            )}

            {chapters.length === 0 ? (
              <p className="empty-text">Chọn document để xem mục lục.</p>
            ) : (
              <div className="list toc-list">
                {chapters.map((chapter) => (
                  <button
                    key={chapter.id}
                    className={`list-item ${
                      selectedChapter?.id === chapter.id ? "active" : ""
                    }`}
                    onClick={() => selectChapter(chapter.id)}
                  >
                    <div className="item-title">
                      {chapter.chapter_index}. {chapter.title}
                    </div>
                    <div className="item-meta">
                      {chapter.paragraph_count} paragraphs •{" "}
                      {chapter.sentence_count} sentences
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </aside>

        <main className="content-area">
          <section className="panel reader-panel">
            <div className="reader-header">
              <div>
                <h2>{selectedDoc ? selectedDoc.title : "Reader"}</h2>

                {selectedDoc && (
                  <p>
                    {selectedChapter
                      ? `Chapter ${selectedChapter.chapter_index}: ${selectedChapter.title}`
                      : `Loaded ${chunks.length} / ${totalChunks} blocks`}
                  </p>
                )}
              </div>

              {selectedDoc && !selectedChapter && hasMoreChunks && (
                <button className="outline-btn" onClick={loadMoreChunks}>
                  Load thêm 10 blocks
                </button>
              )}
            </div>

            {!selectedDoc ? (
              <p className="empty-text">Chọn hoặc upload tài liệu để đọc.</p>
            ) : chunks.length === 0 && loadingChunks ? (
              <p className="empty-text">Đang load nội dung...</p>
            ) : (
              <div className="document-content">
                {chunks.map((chunk, index) => (
                  <div key={`${chunkPage}-${index}`} className="text-block">
                    {chunk.split("\n").map((line, lineIndex) => (
                      <p key={lineIndex}>{line.trim() || "\u00A0"}</p>
                    ))}
                  </div>
                ))}

                {!selectedChapter && hasMoreChunks && (
                  <div ref={loaderRef} className="load-more-trigger">
                    {loadingChunks ? "Đang load thêm..." : "Cuộn xuống để load thêm"}
                  </div>
                )}

                {!selectedChapter && !hasMoreChunks && chunks.length > 0 && (
                  <div className="end-text">Đã load hết tài liệu.</div>
                )}
              </div>
            )}
          </section>

          <section className="panel summary-panel">
            <div className="panel-header">
              <h2>Summary</h2>
            </div>

            <div className="summary-controls">
              <select value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="short">short</option>
                <option value="medium">medium</option>
                <option value="long">long</option>
              </select>

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

            <div className="summary-box">
              {summary || (
                <span className="empty-text">
                  Chọn chapter hoặc document rồi bấm summarize.
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