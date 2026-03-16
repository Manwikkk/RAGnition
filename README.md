<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Streamlit-1.32+-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/Groq-Cloud_Inference-orange.svg" alt="Groq">
  <img src="https://img.shields.io/badge/FAISS-Vector_DB-green.svg" alt="FAISS">
  
  <h1>🎓 RAGnition</h1>
  <p><b>Hybrid RAG · AI Powered Exam Preparation System</b></p>
</div>

---

**RAGnition** is an advanced AI-powered educational tool designed to help students and educators interact with study materials like never before. By seamlessly combining local embeddings (SentenceTransformers + FAISS) for privacy and offline document retrieval with the **Groq API** for lighting-fast cloud inference, RAGnition transforms static PDFs into interactive study sessions, quizzes, and full mock exams.

## ✨ Key Features

- 📄 **Upload & Index PDFs Local-First**: Extracts text via PyMuPDF, chunks it, and creates local embeddings using `all-MiniLM-L6-v2`. Your vector index stays on your machine using FAISS.
- 💬 **Interactive Document Assistant**: Chat seamlessly with your documents. Ask complex questions, request summaries, or extract key formulas with instant, streaming responses.
- ❓ **Dynamic Question Generation**: Instantly generate MCQ, True/False, Short, Long, and Case-based questions from any topic at customizable difficulty levels. Participate in interactive, auto-graded quizzes directly in the app.
- 📋 **Automated Mock Tests**: Assemble comprehensive exam papers with multiple sections, custom mark distributions, and complete answer keys. Downloadable as PDF and TXT.
- 📥 **Export to PDF**: Generate beautiful, clean PDFs of isolated questions, user quiz results with explanations, and full mock test papers.

---

## 🚀 Getting Started

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/Manwikkk/RAGnition.git
cd RAGnition
pip install -r requirements.txt
```

### 2. Configure the Groq API Key

To power the AI responses dynamically, RAGnition relies on Groq for inference. Get a free API key at [console.groq.com](https://console.groq.com).

**Windows:**
```cmd
set GROQ_API_KEY=your_api_key_here
```
**Mac / Linux:**
```bash
export GROQ_API_KEY=your_api_key_here
```
*(Alternatively, you can place it entirely in a `.env` file in the root directory).*

### 3. Run the Application

```bash
streamlit run app.py
```

---

## 🧠 Models & Architecture

RAGnition is built on a "Hybrid RAG" architecture to maximize both privacy and speed. 

```text
1. PDF Upload → PyMuPDF extraction → Chunking (500 chars) → SentenceTransformer Embeddings (all-MiniLM-L6-v2) → FAISS Index (Local)
2. User Query → Embed query → Retrieve top-K chunks → Groq API (Llama 3) → Streaming Answer
```

### Model Stack
| Role | Model | Deployment |
|---|---|---|
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Local, Offline |
| **Primary LLM** | `llama-3.1-8b-instant` | Groq API (Cloud LPU™) |
| **Fallback LLM** | `llama-3.3-70b-versatile` | Groq API (Cloud LPU™) |

---

## ⚡ Why Groq Instead of Local LLMs?

While running a fully local pipeline is great for absolute privacy, inference for massive context windows often becomes a bottleneck on standard consumer hardware. 

We explicitly chose **Groq's LPU™ (Language Processing Unit)** infrastructure for this project because:
1. **Unmatched Speed:** Groq delivers ~300-500 tokens per second compared to ~5-30 tokens/sec on local CPUs/GPUs, enabling near-instantaneous streaming of complex, case-based questions and expansive mock exams. 
2. **Zero Hardware Constraints:** Users without dedicated NVIDIA GPUs can experience state-of-the-art open-source LLMs seamlessly.
3. **No Setup Friction:** Simply plugging in an API key avoids massive multi-gigabyte model downloads (like a 4.7GB `llama3-8b` `.gguf` file) and prevents memory `OOM` crashes during intensive batch generation.

### 🧪 Local LLM Support (Testing)

Despite being heavily optimized for Groq, **RAGnition contains the foundational code to run entirely locally**! 

Inside `utils/local_llm.py`, you will find a fully functioning local LLM interface utilizing **Ollama**. This allows developers to point generation functions toward models like `llama3.1:8b` or `mistral` running locally on their own machines. 
*Note: This is currently maintained for development and testing purposes and is isolated from the main `app.py` UI unless explicitly wired up.*

---

## 📁 Repository Structure

```
RAGnition/
├── app.py                      # Main Streamlit application
├── config.py                   # System configurations and parameters
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
└── utils/
    ├── chunker.py              # Semantic text chunking routines
    ├── embedder.py             # Local SentenceTransformer embeddings
    ├── vector_store.py         # FAISS vector database management 
    ├── retriever.py            # Top-K semantic retrieval logic
    ├── pdf_loader.py           # PyMuPDF document extraction
    ├── pdf_exporter.py         # ReportLab PDF building engine
    ├── question_engine.py      # LLM question generation logic
    ├── mock_test_generator.py  # Exam paper assembly engine
    ├── groq_llm.py             # Groq cloud inference client (Active)
    └── local_llm.py            # Ollama local inference client (Testing)
```

---

<div align="center">
  Crafted with ❤️ for students and educators. 
</div>
