const API_BASE = "http://127.0.0.1:8000";

async function handleResponse(response) {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.detail || "Request failed";
    throw new Error(message);
  }

  return data;
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
}

export async function getDocuments() {
  const response = await fetch(`${API_BASE}/documents`);
  return handleResponse(response);
}

export async function getDocumentDetail(documentId) {
  const response = await fetch(`${API_BASE}/documents/${documentId}`);
  return handleResponse(response);
}

export async function getDocumentChapters(documentId) {
  const response = await fetch(`${API_BASE}/documents/${documentId}/chapters`);
  return handleResponse(response);
}

export async function getChapter(chapterId) {
  const response = await fetch(`${API_BASE}/chapters/${chapterId}`);
  return handleResponse(response);
}

export async function summarizeDocument(documentId, level) {
  const response = await fetch(`${API_BASE}/summarize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_id: documentId,
      level,
    }),
  });

  return handleResponse(response);
}

export async function summarizeChapter(documentId, chapterId, level) {
  const response = await fetch(`${API_BASE}/summarize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_id: documentId,
      chapter_id: chapterId,
      level,
    }),
  });

  return handleResponse(response);
}