import { useState } from "react";

export default function UploadPanel({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) return;

    try {
      setUploading(true);
      await onUploadSuccess(file);
      setFile(null);
      event.target.reset();
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="card">
      <h2>Upload document</h2>
      <form onSubmit={handleSubmit} className="upload-form">
        <input
          type="file"
          accept=".txt,.pdf,.docx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <button type="submit" disabled={!file || uploading}>
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </form>
    </div>
  );
}