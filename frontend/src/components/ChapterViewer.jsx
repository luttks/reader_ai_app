export default function ChapterViewer({ document, chapter }) {
    return (
      <div className="card viewer-card">
        <h2>Reader</h2>
  
        {!document ? (
          <p className="muted">Select a document.</p>
        ) : !chapter ? (
          <p className="muted">Select a chapter.</p>
        ) : (
          <>
            <div className="document-header">
              <div className="document-title">{document.title}</div>
              <div className="document-subtitle">
                {chapter.chapter_index}. {chapter.title}
              </div>
            </div>
  
            <div className="reader-content">
              {chapter.raw_text.split("\n").map((line, index) => (
                <p key={index}>
                  {line.trim() === "" ? "\u00A0" : line}
                </p>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }