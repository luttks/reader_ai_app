# Reader AI App

Dưới đây là **README chuẩn chỉnh (HR-friendly + technical)** cho project của bạn.
Viết theo hướng: **AI Engineer project + có chiều sâu + dễ hiểu cho non-tech**.

---

# 📚 Document Reader AI

## 🚀 Tổng quan

**Document Reader AI** là một hệ thống xử lý tài liệu thông minh, cho phép người dùng:

- 📂 Upload file (TXT, PDF, DOCX)
- 📖 Tự động phân tích cấu trúc tài liệu (chapter, section, paragraph)
- 🧠 Tóm tắt nội dung theo nhiều mức:
  - Short
  - Medium
  - Long

- 📊 Đánh giá chất lượng summary (compression, sentence count, time)

👉 Mục tiêu: giúp người dùng **đọc nhanh – hiểu sâu – chọn đúng nội dung quan trọng**

---

## 🎯 Bài toán giải quyết

Trong thực tế:

- Tài liệu dài → khó đọc hết
- PDF → mất cấu trúc khi parse
- Không biết nên đọc phần nào quan trọng

➡️ Hệ thống này giải quyết bằng cách:

1. **Hiểu cấu trúc tài liệu**
2. **Tách chương – đoạn – nội dung**
3. **Tóm tắt thông minh**
4. **Cho phép người dùng chọn nội dung cần đọc**

---

## 🧠 Điểm nổi bật (KHÔNG dùng pretrained model)

🔥 **Không sử dụng model pretrained (BERT, GPT, etc.)**

Thay vào đó:

- Xây dựng pipeline NLP từ đầu
- Rule-based + statistical methods
- (Định hướng) Deep Learning tự train

👉 Điều này thể hiện:

- Hiểu sâu NLP
- Làm chủ pipeline end-to-end
- Phù hợp môi trường nghiên cứu / học thuật

---

## 🏗️ Kiến trúc hệ thống

```
Upload File
     ↓
File Parser (TXT / PDF / DOCX)
     ↓
Text Cleaning
     ↓
Structure Detection
 (Chapter / Section / Paragraph)
     ↓
Summarization Engine
     ↓
Evaluation + Logging
     ↓
Frontend Reader UI
```

---

## ⚙️ Công nghệ sử dụng

### Backend

- FastAPI (REST API)
- Python
- Pydantic (data validation)

### NLP / AI

- Rule-based NLP
- Text ranking
- Sentence scoring
- (Planned) Deep Learning (RNN / Transformer from scratch)

### Frontend

- React + Vite
- Fetch API

### Database (optional)

- PostgreSQL / SQLite

---

## 📂 Cấu trúc project

```
reader_ai/
│
├── backend/
│   ├── app/
│   │   ├── api/          # endpoints
│   │   ├── services/     # business logic
│   │   ├── models/       # data models
│   │   ├── schemas/      # request/response
│   │   ├── core/         # config
│   │   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── api.js
│
├── logs/
│   └── evaluation_logs.jsonl
│
└── README.md
```

---

## 🔍 Core Features

### 1. 📥 Upload Document

- Hỗ trợ:
  - `.txt`
  - `.pdf`
  - `.docx`

---

### 2. 🧩 Structure Detection (QUAN TRỌNG NHẤT)

Hệ thống tự động:

- Tách **chapter**
- Tách **section**
- Tách **paragraph**

👉 Không làm mất bố cục gốc của sách

---

### 3. ✂️ Summarization

API:

```bash
POST /summarize
```

Input:

```json
{
  "document_id": 1,
  "chapter_id": 1,
  "level": "medium"
}
```

Output:

```json
{
  "summary_text": "...",
  "level": "medium"
}
```

---

### 4. 📊 Evaluation System

API:

```bash
POST /evaluate/summary
```

Output gồm:

- ⏱ processing time
- 📄 số câu gốc
- ✂️ số câu summary
- 📉 compression ratio

Ví dụ:

```json
{
  "level": "short",
  "compression_ratio": 0.24
}
```

---

## 🧪 Ví dụ thực tế

### Input (chapter)

- 8 sentences
- 124 words

### Output

| Level  | Sentences | Words | Compression |
| ------ | --------- | ----- | ----------- |
| Short  | 2         | 30    | 0.24        |
| Medium | 3         | 44    | 0.35        |
| Long   | 4         | 60    | 0.48        |

👉 Cho thấy hệ thống có thể:

- điều chỉnh độ dài summary
- giữ nội dung quan trọng

---

## 🧠 Kỹ thuật cốt lõi

### 1. Sentence Scoring

- Tần suất từ khóa
- Vị trí câu (câu đầu thường quan trọng)
- Độ dài câu

---

### 2. Paragraph-aware Summarization

- Không cắt giữa câu
- Giữ mạch nội dung

---

### 3. Structure-aware Processing

- Tóm tắt theo **chapter**
- Không trộn nội dung giữa các phần

---

### 4. Evaluation Metrics

- Compression Ratio
- Sentence Reduction
- Processing Time

---

## 🔥 Thách thức kỹ thuật

### 1. PDF Parsing

- mất format
- text bị split sai
- header/footer gây nhiễu

### 2. Chapter Detection

- không phải lúc nào cũng có "CHAPTER"
- cần heuristic nâng cao

### 3. OCR (định hướng)

- PDF scan không có text layer

---

## 🚧 Roadmap phát triển

### Phase 1 (Done ✅)

- Upload + parsing
- Basic summarization
- Evaluation
- Frontend reader

---

### Phase 2 (In progress 🔄)

- Advanced structure detection
- PDF layout parsing
- OCR support

---

### Phase 3 (Coming 🚀)

- Deep Learning summarization:
  - Sentence encoder
  - BiLSTM / GRU
  - Transformer (from scratch)

---

### Phase 4

- Chatbot Q&A (RAG)
- Multilingual support
- Deploy production

---

## 🖥️ Demo

Frontend:

```
http://localhost:5173
```

Backend:

```
http://127.0.0.1:8000/docs
```

---

## 🧑‍💻 Cách chạy project

### Backend

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 💡 Điểm mạnh của project

✅ Xây dựng từ đầu (no pretrained)
✅ Full pipeline NLP
✅ Có evaluation rõ ràng
✅ Có frontend demo
✅ Có thể mở rộng thành sản phẩm

---

## 👨‍💼 Phù hợp vị trí

- AI Engineer (Fresher/Junior)
- NLP Engineer
- Backend AI Developer
