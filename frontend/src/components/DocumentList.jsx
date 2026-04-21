export default function DocumentList({
    documents,
    selectedDocumentId,
    onSelectDocument,
  }) {
    return (
      <div className="card">
        <h2>Documents</h2>
        {documents.length === 0 ? (
          <p className="muted">No documents yet.</p>
        ) : (
          <ul className="list">
            {documents.map((doc) => (
              <li key={doc.id}>
                <button
                  className={
                    selectedDocumentId === doc.id ? "list-item active" : "list-item"
                  }
                  onClick={() => onSelectDocument(doc.id)}
                >
                  <div className="list-title">{doc.title}</div>
                  <div className="list-meta">
                    {doc.file_type.toUpperCase()} • ID {doc.id}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }