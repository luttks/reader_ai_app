import { useState } from "react";

export default function SummaryPanel({
  document,
  chapter,
  onSummarizeDocument,
  onSummarizeChapter,
  summary,
  loading,
}) {
  const [level, setLevel] = useState("medium");

  async function handleChapterSummary() {
    if (!document || !chapter) return;
    await onSummarizeChapter(document.id, chapter.id, level);
  }

  async function handleDocumentSummary() {
    if (!document) return;
    await onSummarizeDocument(document.id, level);
  }

  return (
    <div className="card">
      <h2>Summary</h2>

      <div className="summary-controls">
        <label>
          Level
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="short">Short</option>
            <option value="medium">Medium</option>
            <option value="long">Long</option>
          </select>
        </label>

        <div className="button-group">
          <button onClick={handleChapterSummary} disabled={!document || !chapter || loading}>
            {loading ? "Summarizing..." : "Summarize Chapter"}
          </button>

          <button onClick={handleDocumentSummary} disabled={!document || loading}>
            {loading ? "Summarizing..." : "Summarize Document"}
          </button>
        </div>
      </div>

      <div className="summary-box">
        {summary ? summary.summary_text : <span className="muted">No summary yet.</span>}
      </div>
    </div>
  );
}