"""
app.py — RAGnition Streamlit interface.
Tabs: Upload PDFs | Chat | Generate Questions | Mock Test
"""

import json as _json
import logging
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from config import config
from utils.pdf_loader import PDFLoader
from utils.chunker import Chunker
from utils.embedder import Embedder
from utils.vector_store import VectorStore
from utils.retriever import Retriever
from utils.question_engine import QuestionEngine
from utils.mock_test_generator import MockTestGenerator
from utils.groq_llm import generate_streaming, get_system_status
from utils.pdf_exporter import (
    generate_questions_pdf,
    generate_quiz_result_pdf,
    generate_mock_paper_pdf,
    generate_mock_answerkey_pdf,
)

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="RAGnition — AI Exam Prep",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Tab bar ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: rgba(255,255,255,0.04);
    border-radius: 14px; padding: 6px;
    display: flex; justify-content: center;
    width: fit-content; margin: 0 auto;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px; color: #94a3b8;
    font-weight: 600; padding: 8px 22px; font-size: 0.9rem;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#667eea,#764ba2) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(102,126,234,0.4);
}

/* ── Cards & result blocks ── */
.rag-card {
    background: linear-gradient(135deg,rgba(102,126,234,0.08),rgba(118,75,162,0.06));
    border: 1px solid rgba(102,126,234,0.18);
    border-radius: 16px; padding: 20px; margin: 10px 0;
}
.result-correct {
    background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.28);
    border-radius: 12px; padding: 16px; margin: 8px 0;
}
.result-incorrect {
    background: rgba(239,68,68,0.07); border: 1px solid rgba(239,68,68,0.25);
    border-radius: 12px; padding: 16px; margin: 8px 0;
}
.result-pending {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px; padding: 16px; margin: 8px 0;
}
.score-box {
    background: linear-gradient(135deg,#667eea,#764ba2);
    border-radius: 16px; padding: 24px; text-align: center;
    box-shadow: 0 8px 30px rgba(102,126,234,0.35); margin: 16px 0;
}

/* ── Buttons ── */
.stButton>button {
    background: linear-gradient(135deg,#667eea,#764ba2);
    color: white; border: none; border-radius: 10px;
    font-weight: 600; padding: 0.5rem 1.5rem;
    transition: all 0.2s; box-shadow: 0 2px 10px rgba(102,126,234,0.28);
}
.stButton>button:hover {
    opacity: 0.88; transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(102,126,234,0.4);
}

/* ── Sidebar status cards ── */
.status-card {
    background: #111827;
    border: 1px solid rgba(102,126,234,0.2);
    border-radius: 10px; padding: 10px 14px;
    margin-bottom: 8px; font-size: 0.83rem; color: #d1d5db;
    line-height: 1.6;
}

/* ── Hero badges ── */
.hero-badges span {
    background: #111827;
    border: 1px solid rgba(102,126,234,0.25); color: #c4b5fd;
    padding: 5px 14px; border-radius: 8px;
    font-size: 0.82rem; font-weight: 500;
    margin: 0 3px; display: inline-block;
}

/* ── Footer ── */
.rag-footer {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: linear-gradient(90deg,rgba(15,12,41,0.97),rgba(48,43,99,0.97));
    border-top: 1px solid rgba(102,126,234,0.18);
    padding: 7px 24px; text-align: center; font-size: 0.74rem;
    color: #64748b; z-index: 999;
    display: flex; justify-content: center; align-items: center; gap: 16px;
}
.rag-footer b { color: #667eea; }
.divider-grad {
    height: 2px;
    background: linear-gradient(90deg,#667eea,#764ba2,transparent);
    border-radius: 2px; margin: 16px 0;
}
.main .block-container { padding-bottom: 60px; }
</style>
""", unsafe_allow_html=True)

# ── Singletons ────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading embedding model …")
def _get_embedder(): return Embedder()

@st.cache_resource(show_spinner=False)
def _get_vector_store():
    vs = VectorStore(dimension=_get_embedder().dimension)
    vs.load(); return vs

@st.cache_resource(show_spinner=False)
def _get_retriever():
    return Retriever(vector_store=_get_vector_store(), embedder=_get_embedder())

@st.cache_resource(show_spinner=False)
def _get_question_engine(): return QuestionEngine()

def _get_mock_generator(): return MockTestGenerator(_get_question_engine())

# ── Sidebar ───────────────────────────────────────────────────────────────────
def _status_card(text: str):
    st.sidebar.markdown(
        f"<div class='status-card'>{text}</div>",
        unsafe_allow_html=True
    )

with st.sidebar:
    st.markdown("""
<div style='text-align:center;padding:4px 0 8px'>
  <h2 style='color:#8b5cf6;margin:0;font-size:2.2rem;font-weight:800'>RAGnition</h2>
  <p style='color:#9ca3af;margin:2px 0 0;font-size:0.78rem;letter-spacing:0.05em'>AI EXAM INTELLIGENCE</p>
</div>
<hr style='border-color:rgba(139,92,246,0.2);margin:8px 0;'>
""", unsafe_allow_html=True)

    _status  = get_system_status()
    vs_sb    = _get_vector_store()

    st.markdown("**System Status**")
    if _status["api_key_set"]:
        _status_card("✅ &nbsp;<b>Groq API</b> connected")
    else:
        _status_card("❌ &nbsp;<b>GROQ_API_KEY</b> not set")
        st.code("set GROQ_API_KEY=your_key", language="bash")

    if vs_sb.total_vectors > 0:
        _status_card(f"🧠 &nbsp;<b>Embeddings</b> loaded")
        _status_card(f"📄 &nbsp;<b>{vs_sb.total_vectors}</b> chunks indexed")
    else:
        _status_card("📂 &nbsp;No index — upload PDFs first")

    st.divider()
    st.markdown(f"""
<div style='font-size:0.79rem;color:#6b7280;line-height:2'>
  <b style='color:#94a3b8'>Model:</b> {_status['primary_model']}<br>
  <b style='color:#94a3b8'>Fallback:</b> {_status['fallback_model']}<br>
  <b style='color:#94a3b8'>Embedder:</b> bge-base-en-v1.5<br>
  <b style='color:#94a3b8'>Retrieval:</b> FAISS + BM25<br>
  <b style='color:#94a3b8'>Top-K:</b> {config.TOP_K}
</div>""", unsafe_allow_html=True)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='text-align:center; font-size:64px; font-weight:800; margin-bottom:6px;
  background:linear-gradient(135deg,#667eea,#764ba2);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
  RAGnition
</h1>
<p style='text-align:center; font-size:20px; color:#9ca3af; margin-bottom:4px;'>
  AI-Powered Document Intelligence for Smart Exam Preparation
</p>
<p style='text-align:center; font-size:14px; color:#6b7280; margin-bottom:18px;'>
  Hybrid RAG &nbsp;•&nbsp; Semantic Search &nbsp;•&nbsp; Fast LLM Inference
</p>
<div class='hero-badges' style='text-align:center; margin-bottom:22px;'>
  <span>📄 PDF Chat</span>
  <span>🧠 Hybrid RAG</span>
  <span>⚡ Groq Speed</span>
  <span>📝 Exam Generator</span>
</div>
<div class='divider-grad'></div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_upload, tab_chat, tab_questions, tab_mock = st.tabs([
    "📄 Upload PDFs", "💬 Chat", "❓ Generate Questions", "📋 Mock Test"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Upload PDFs
# ═══════════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.subheader("📄 Upload & Index PDFs")
    st.markdown("Upload your study material PDFs. They will be parsed, chunked, embedded with **BGE-base-en-v1.5**, and indexed locally using FAISS.")
    st.markdown("---")

    uploaded_files = st.file_uploader("Choose PDF files", type=["pdf"],
                                      accept_multiple_files=True, key="pdf_uploader")
    clear_existing = st.checkbox("Clear existing index before building", value=False)

    if uploaded_files and st.button("🔨 Build Index", key="build_index_btn"):
        vs = _get_vector_store()
        if clear_existing: vs.clear()
        loader, chunker, embedder = PDFLoader(), Chunker(), _get_embedder()
        all_chunks: list = []
        progress = st.progress(0, text="Processing …")
        tmp_dir = config.DATA_DIR
        tmp_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for uf in uploaded_files:
            dest = tmp_dir / uf.name
            dest.write_bytes(uf.read())
            saved.append(dest)
        for i, path in enumerate(saved):
            progress.progress(i / len(saved), text=f"Loading {path.name} …")
            try:
                all_chunks.extend(chunker.chunk_documents(loader.load(path)))
            except Exception as e:
                st.warning(f"⚠️ {path.name}: {e}")
        if all_chunks:
            progress.progress(0.85, text="Creating BGE embeddings …")
            vs.add(embedder.embed_chunks(all_chunks), all_chunks)
            vs.save()
            progress.progress(1.0, text="Done!")
            st.session_state["all_chunks"] = all_chunks
            st.success(f"✅ Indexed **{len(all_chunks)} chunks** from **{len(uploaded_files)} PDF(s)**. Total: **{vs.total_vectors}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pages Loaded", sum(1 for c in all_chunks if c.get("page")))
            c2.metric("Chunks Created", len(all_chunks))
            c3.metric("Total Indexed", vs.total_vectors)
        else:
            st.error("No text extracted from the uploaded PDFs.")
        progress.empty()

    vs_up = _get_vector_store()
    if vs_up.total_vectors > 0:
        st.info(f"ℹ️ Index ready — **{vs_up.total_vectors}** vectors available.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Chat
# ═══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.subheader("💬 Chat with Your Documents")
    st.caption("Ask questions, generate summaries, extract insights, create notes — Hybrid RAG retrieval powered by Groq.")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask questions, generate summaries, extract insights from your PDFs...")
    if user_input:
        vs = _get_vector_store()
        if vs.total_vectors == 0:
            st.warning("⚠️ Please upload and index PDFs first.")
        else:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.markdown(user_input)
            with st.chat_message("assistant"):
                chunks  = _get_retriever().retrieve_top_k(user_input, k=config.TOP_K)
                context = "\n\n---\n\n".join(c["text"] for c in chunks)[:2000]
                prompt  = f"Context:\n{context}\n\nUser instruction:\n{user_input}"
                try:
                    ph, full = st.empty(), ""
                    with st.spinner(""):
                        for token in generate_streaming(prompt):
                            full += token
                            ph.markdown(full + "▌")
                    ph.markdown(full)
                    answer = full
                except Exception as exc:
                    answer = f"⚠️ Groq API error: `{exc}`"
                    st.markdown(answer)
                st.session_state["chat_history"].append({"role": "assistant", "content": answer})
                with st.expander("📚 Source chunks"):
                    for i, c in enumerate(chunks, 1):
                        st.caption(
                            f"**Chunk {i}** — {c.get('source','?')} p.{c.get('page','?')} | "
                            f"Hybrid: {c.get('score',0):.3f}"
                        )
                        st.text(c["text"][:280] + "…" if len(c["text"]) > 280 else c["text"])

    if st.session_state["chat_history"] and st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state["chat_history"] = []; st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Generate Questions
# ═══════════════════════════════════════════════════════════════════════════════
with tab_questions:
    st.subheader("❓ Generate Exam Questions")

    vs = _get_vector_store()
    if vs.total_vectors == 0:
        st.warning("⚠️ Please upload and index PDFs first.")
    else:
        col_l, col_r = st.columns([1, 3])
        with col_l:
            with st.container():
                q_topic = st.text_input("Topic (optional)", placeholder="e.g. Knowledge Based Systems")
                q_type  = st.selectbox("Question Type",
                    ["MCQ", "True/False", "Short", "Long", "Case-based"], key="q_type_select")
                q_diff  = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"],
                    index=1, key="q_diff_select")
                q_count = st.slider("Number of questions", 1, 10, 3, key="q_count_slider")
                gen_btn = st.button("⚡ Generate", key="gen_q_btn")

        with col_r:
            if gen_btn:
                query  = q_topic or "exam questions about the main topics"
                chunks = _get_retriever().retrieve_top_k(query, k=config.TOP_K)
                ctx    = "\n\n---\n\n".join(c["text"] for c in chunks)[:2000]
                with st.spinner(f"Generating {q_count} {q_type} question(s) …"):
                    try:
                        qs = _get_question_engine().generate(
                            context=ctx, question_type=q_type,
                            difficulty=q_diff, num_questions=q_count,
                        )
                        st.session_state["last_questions"] = qs
                        st.session_state["q_type_last"]    = q_type
                        st.session_state["q_diff_last"]    = q_diff
                        st.session_state.pop("quiz_submitted", None)
                        st.session_state.pop("quiz_answers",  None)
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

            questions   = st.session_state.get("last_questions", [])
            q_type_last = st.session_state.get("q_type_last", "MCQ")
            q_diff_last = st.session_state.get("q_diff_last", "Medium")

            if questions:
                st.markdown(f"### {len(questions)} {q_type_last} Question(s)")
                st.markdown("---")

                # ── MCQ / True/False Interactive Quiz ─────────────────────────
                if q_type_last in ("MCQ", "True/False"):
                    submitted    = st.session_state.get("quiz_submitted", False)
                    user_answers = st.session_state.get("quiz_answers", {})

                    if not submitted:
                        temp_answers = {}
                        for i, q in enumerate(questions):
                            raw_opts = q.get("options") or {}
                            if isinstance(raw_opts, dict):
                                radio_opts = [f"{k}. {v}" for k, v in sorted(raw_opts.items())]
                            else:
                                radio_opts = list(raw_opts) if raw_opts else ["True", "False"]

                            st.markdown(f"<div class='result-pending'>", unsafe_allow_html=True)
                            st.markdown(f"**Q{i+1}.** {q.get('question','')}")
                            sel = st.radio(
                                f"q{i}_radio", radio_opts,
                                key=f"quiz_radio_{i}", label_visibility="collapsed"
                            )
                            temp_answers[i] = sel
                            st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("---")
                        if st.button("✅ Submit Answers", key="submit_quiz"):
                            st.session_state["quiz_answers"]  = temp_answers
                            st.session_state["quiz_submitted"] = True
                            st.rerun()

                    else:
                        score = 0
                        for i, q in enumerate(questions):
                            correct  = str(q.get("correct_answer", q.get("answer",""))).strip().upper()
                            raw_opts = q.get("options") or {}
                            user_sel = str(user_answers.get(i, "")).strip()
                            user_letter = user_sel[0].upper() if user_sel else ""
                            is_correct  = (user_letter == correct[:1])
                            if is_correct: score += 1

                            cls   = "result-correct" if is_correct else "result-incorrect"
                            badge = "✅ **CORRECT**" if is_correct else "❌ **INCORRECT**"
                            st.markdown(f"<div class='{cls}'>", unsafe_allow_html=True)
                            st.markdown(f"**Q{i+1}.** {q.get('question','')}  —  {badge}")

                            if isinstance(raw_opts, dict):
                                for letter, text in sorted(raw_opts.items()):
                                    is_ans  = (letter.upper() == correct[:1])
                                    is_user = (letter.upper() == user_letter)
                                    label   = f"{letter}. {text}"
                                    if is_ans:
                                        st.markdown(f"✅ **{label}** ← Correct Answer")
                                    elif is_user and not is_ans:
                                        st.markdown(f"❌ ~~{label}~~ ← Your Answer")
                                    else:
                                        st.markdown(f"&nbsp;&nbsp;&nbsp;{label}")
                            else:
                                for opt in (raw_opts or ["True", "False"]):
                                    is_ans  = str(opt).strip().upper() == correct
                                    is_user = str(opt).strip() == user_sel
                                    if is_ans:
                                        st.markdown(f"✅ **{opt}** ← Correct Answer")
                                    elif is_user and not is_ans:
                                        st.markdown(f"❌ ~~{opt}~~ ← Your Answer")
                                    else:
                                        st.markdown(f"&nbsp;&nbsp;&nbsp;{opt}")

                            expl = q.get("explanation", "")
                            if is_correct:
                                st.success(f"💡 **Why correct:** {expl}")
                            else:
                                st.error(f"💡 **Why wrong & why the correct answer is right:** {expl}")
                            st.markdown("</div>", unsafe_allow_html=True)

                        pct   = int(score / len(questions) * 100)
                        color = "#10b981" if pct >= 70 else "#f59e0b" if pct >= 40 else "#ef4444"
                        st.markdown(f"""
<div class='score-box'>
  <div style='color:rgba(255,255,255,0.7);font-size:0.9rem;margin-bottom:4px'>Quiz Score</div>
  <div style='color:{color};font-size:3rem;font-weight:800'>{score}/{len(questions)}</div>
  <div style='color:rgba(255,255,255,0.75);font-size:1rem'>{pct}% Correct</div>
</div>""", unsafe_allow_html=True)

                        st.markdown("---")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            letter_answers = {i: str(user_answers.get(i,""))[0].upper()
                                              for i in range(len(questions))}
                            pdf_q = generate_questions_pdf(questions, q_type_last, q_diff_last)
                            st.download_button("⬇️ Questions PDF", data=pdf_q,
                                file_name="questions.pdf", mime="application/pdf", key="dl_q_pdf")
                        with c2:
                            pdf_r = generate_quiz_result_pdf(questions, letter_answers, score, len(questions))
                            st.download_button("⬇️ My Results PDF", data=pdf_r,
                                file_name="quiz_results.pdf", mime="application/pdf", key="dl_result_pdf")
                        with c3:
                            if st.button("🔄 Retry Quiz", key="retry_quiz"):
                                st.session_state.pop("quiz_submitted", None)
                                st.session_state.pop("quiz_answers",  None)
                                st.rerun()

                # ── Short / Long / Case-based ─────────────────────────────────
                else:
                    for i, q in enumerate(questions, 1):
                        st.markdown("<div class='rag-card'>", unsafe_allow_html=True)
                        st.markdown(f"**Q{i}.** {q.get('question','')}")
                        with st.expander("Show Answer & Explanation"):
                            st.markdown(f"✅ **Answer:** {q.get('answer','')}")
                            st.markdown(f"**Explanation:** {q.get('explanation','')}")
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("---")
                    col_pdf, col_json = st.columns(2)
                    with col_pdf:
                        pdf_q = generate_questions_pdf(questions, q_type_last, q_diff_last)
                        st.download_button("⬇️ Download PDF", data=pdf_q,
                            file_name="questions.pdf", mime="application/pdf", key="dl_q_pdf_other")
                    with col_json:
                        st.download_button("⬇️ Download JSON",
                            data=_json.dumps(questions, indent=2),
                            file_name="questions.json", mime="application/json", key="dl_questions_json")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Mock Test
# ═══════════════════════════════════════════════════════════════════════════════
with tab_mock:
    st.subheader("📋 Generate Mock Test Paper")

    vs = _get_vector_store()
    if vs.total_vectors == 0:
        st.warning("⚠️ Please upload and index PDFs first.")
    else:
        col_ml, col_mr = st.columns([1, 2])
        with col_ml:
            with st.container():
                exam_title      = st.text_input("Exam Title", value="Mock Examination Paper", key="exam_title")
                total_marks     = st.number_input("Total Marks", min_value=10, max_value=200, value=30, step=5)
                mock_difficulty = st.selectbox("Difficulty", ["Easy","Medium","Hard"], index=1, key="mock_diff")

                st.markdown("**Section Distribution**")
                use_custom   = st.checkbox("Customise distribution", value=False)
                distribution = None
                if use_custom:
                    mcq_c   = st.number_input("MCQ (1 mark)",    min_value=0, max_value=30, value=5)
                    short_c = st.number_input("Short (3 marks)", min_value=0, max_value=20, value=3)
                    long_c  = st.number_input("Long (5 marks)",  min_value=0, max_value=10, value=2)
                    case_c  = st.number_input("Case (10 marks)", min_value=0, max_value=5,  value=1)
                    distribution = {}
                    if mcq_c:   distribution["MCQ"]        = {"count": mcq_c,   "marks_each": 1}
                    if short_c: distribution["Short"]      = {"count": short_c, "marks_each": 3}
                    if long_c:  distribution["Long"]       = {"count": long_c,  "marks_each": 5}
                    if case_c:  distribution["Case-based"] = {"count": case_c,  "marks_each": 10}

                gen_mock_btn = st.button("📋 Generate Paper", key="gen_mock_btn")

        with col_mr:
            if gen_mock_btn:
                chunks  = _get_retriever().retrieve_top_k("exam questions key topics", k=config.TOP_K)
                context = "\n\n---\n\n".join(c["text"] for c in chunks)[:2000]
                with st.spinner("Generating exam paper … (may take a minute)"):
                    try:
                        exam = _get_mock_generator().generate(
                            context=context, total_marks=total_marks,
                            distribution=distribution, difficulty=mock_difficulty, title=exam_title,
                        )
                        st.session_state["last_exam"] = exam
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

            exam = st.session_state.get("last_exam")
            if exam:
                mg = _get_mock_generator()
                paper_text  = mg.format_as_text(exam)
                answer_text = mg.format_answer_key(exam)

                st.markdown("#### 📄 Exam Paper Preview")
                st.text_area("", value=paper_text, height=380, key="paper_display",
                             label_visibility="collapsed")
                st.markdown("---")

                with st.expander("🔑 View Answer Key"):
                    st.text(answer_text)

                st.markdown("**Download**")
                col_p, col_k, col_pt, col_kt = st.columns(4)
                with col_p:
                    paper_pdf = generate_mock_paper_pdf(exam)
                    st.download_button("⬇️ Paper (PDF)", data=paper_pdf,
                        file_name="exam_paper.pdf", mime="application/pdf", key="dl_paper_pdf")
                with col_k:
                    key_pdf = generate_mock_answerkey_pdf(exam)
                    st.download_button("⬇️ Answer Key (PDF)", data=key_pdf,
                        file_name="answer_key.pdf", mime="application/pdf", key="dl_key_pdf")
                with col_pt:
                    st.download_button("⬇️ Paper (TXT)", data=paper_text,
                        file_name="exam_paper.txt", key="dl_paper_txt")
                with col_kt:
                    st.download_button("⬇️ Key (TXT)", data=answer_text,
                        file_name="answer_key.txt", key="dl_key_txt")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='rag-footer'>
  <b>RAGnition</b>
  <span style='color:#334155'>·</span>
  <span>AI Powered Exam Preparation</span>
  <span style='color:#334155'>·</span>
  <span>Hybrid RAG — FAISS + BM25 + Groq</span>
  <span style='color:#334155'>·</span>
  <span>Built with Streamlit</span>
</div>
""", unsafe_allow_html=True)
