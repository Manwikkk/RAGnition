<div align="center">
  <img src="public/favicon.png" alt="RAGnition Logo" width="120" />
  <h1>RAGnition V2 — Ultimate AI Study Companion</h1>
  <p><strong>A full-stack, AI-powered platform that transforms your study materials into interactive intelligent learning experiences.</strong></p>
  
  <p>
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
    <img src="https://img.shields.io/badge/GROQ-Llama_3-purple?style=for-the-badge" />
    <img src="https://img.shields.io/badge/LangChain-gray?style=for-the-badge" />
    <img src="https://img.shields.io/badge/FAISS-VectorDB-blue?style=for-the-badge" />
  </p>
</div>

---

> **Note:** The original Streamlit prototype of RAGnition is still available for reference inside the `Streamlit Prototype/` folder.

## ✨ Features

- **🧠 Intelligent Document Chat:** Ask questions, get explanations, and converse naturally with your uploaded PDFs. Powered by local FAISS vector search and Llama-3.
- **📝 Bulk MCQ Generator:** Generate up to **50 custom Multiple Choice Questions** with instant scoring and detailed AI explanations for every answer.
- **🎓 Smart Mock Tests:** Generate full-scale exam papers (capped at 100 marks) with an intelligent auto-division algorithm that perfectly balances short, medium, and long-form essay questions based on total marks.
- **⚡ Auto-Flashcards:** Auto-generate revision flashcards featuring a stunning flip animation, known/unknown tracking, and a progress bar.
- **📑 Smart Summaries:** Extract key takeaways, core concepts, and actionable study tips instantly. Downloadable directly as PDF.
- **💅 Premium UI/UX:** Built with beautiful glassmorphism design, custom Framer Motion hover animations (light sweeps, tilt cards, dynamic glows), and a fully responsive layout.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Node.js** v18+ (for frontend)
- **Python** 3.10+ (for backend vector database + API)
- **Groq API Key** (Get it free at [console.groq.com](https://console.groq.com))

### 2. Environment Setup
Create a `.env` file in the root of the project with your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
VITE_API_BASE_URL=
```

### 3. Start the Python Backend
The backend parses your PDFs, chunks them, creates vector embeddings using `BAAI/bge-base-en-v1.5`, and handles RAG generation.

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*(Wait until the terminal reads `Model loaded. CORS configured.`)*

### 4. Start the React Frontend
In a **new terminal tab**, from the root of the project:

```bash
npm install
npm run dev
```

Open [http://localhost:8080](http://localhost:8080) to access the platform!

---

## 📁 Project Architecture

```plaintext
RAGnition/
├── backend/                  # Python FastAPI Backend
│   ├── main.py               # RAG logic, FAISS indexing, Groq LLM chains
│   └── requirements.txt      # Python dependencies
├── src/                      # React Frontend
│   ├── components/           # UI Components (Upload, Chat, MCQs, Mock Tests)
│   ├── context/              # PDF File State Management
│   ├── lib/                  # Backend API Client
│   ├── pages/                # Dashboard Layout
│   └── index.css             # Tailwind & Glassmorphism Keyframes
├── Streamlit Prototype/      # Legacy V1 Python Application
├── .env                      # API Configuration
└── package.json              # Frontend Dependencies
```

---

## 🔧 Troubleshooting

- **Server Connection Error:** Ensure the Python server is actively running on port 8000.
- **"No text found in PDF":** Ensure you upload text-based PDFs. Image-based scans without OCR are not supported by the current PyPDF loader.
- **First-time Slow Startup:** The backend downloads the BAAI embedding model (~440MB) on the very first run. All subsequent startups will be instantaneous.

<div align="center">
  <br>
  <p>Engineered with ❤️ by <b><a href="https://github.com/Manwikkk">Manvik Siddhpura</a></b>.</p>
</div>
