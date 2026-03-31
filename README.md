<div align="center">
  <h1>RAGnition — Your Personal AI Study Companion</h1>
  <p><strong>A full-stack, AI-powered platform that transforms your study materials into interactive intelligent learning experiences.</strong></p>
  
  <p>
    <img src="https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB" alt="React" />
    <img src="https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
    <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Llama_3-0466C8?style=for-the-badge&logo=meta&logoColor=white" alt="Llama 3" />
    <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain" />
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  </p>
</div>

---

<div align="center">
  <img src="Screenshots/1.PNG" alt="RAGnition Interface" style="border-radius: 12px; max-width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2);" />
</div>

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
├── Screenshots/              # Application Interface Previews
├── Streamlit Prototype/      # Legacy V1 Python Application
├── .env                      # API Configuration
└── package.json              # Frontend Dependencies
```

---

> **Note:** The original Streamlit prototype of RAGnition is perfectly preserved and available for reference inside the `Streamlit Prototype/` folder!

<div align="center">
  <br>
  <p>Engineered with ❤️ by <b><a href="https://github.com/Manwikkk">Manvik Siddhpura</a></b>.</p>
</div>
