# RAGnition

**Hybrid RAG · AI Powered Exam Preparation System**

RAGnition lets you upload PDFs and interact with them using AI — ask questions, generate exam questions, create mock tests, and more. It uses local embeddings (SentenceTransformers + FAISS) for retrieval and **Groq API** for ultra-fast cloud inference.

---

## Features

- 📄 **Upload PDFs** — extract, chunk, embed, and index locally
- 💬 **AI Document Assistant** — ask questions, summarize, extract info, generate notes (streaming responses)
- ❓ **Generate Questions** — MCQ, Short, Long, True/False, Case-based at any difficulty
- 📋 **Mock Test Generator** — auto-assembled exam papers with answer keys

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Groq API key

Get a free API key at [console.groq.com](https://console.groq.com)

**Windows:**
```cmd
set GROQ_API_KEY=your_api_key_here
```

**Mac / Linux:**
```bash
export GROQ_API_KEY=your_api_key_here
```

### 3. Run the application

```bash
streamlit run app.py
```

---

## Why Groq?

Groq provides **extremely fast inference** on cloud hardware (LPU™). Compared to running models locally on CPU:

| | Local (CPU) | Groq API |
|---|---|---|
| Speed | ~5–30 tokens/sec | ~300–500 tokens/sec |
| Setup | Model download required | Just an API key |
| Hardware | Depends on your machine | Dedicated LPU hardware |

---

## Architecture

```
PDF Upload → PyMuPDF extraction → Chunking (500 chars) → SentenceTransformer embeddings → FAISS index
User Query → Embed query → FAISS Top-K (k=3) → Context (≤2000 chars) → Groq API → Streaming response
```

---

## Models

| Role | Model |
|---|---|
| Primary | `llama3-8b-8192` (fast, accurate) |
| Fallback | `mixtral-8x7b-32768` |
| Embeddings | `all-MiniLM-L6-v2` (local, offline) |
