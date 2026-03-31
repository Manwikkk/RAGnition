import io
import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pypdf import PdfReader
from rank_bm25 import BM25Okapi
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv


load_dotenv()

app = FastAPI(title="RAGnition Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

EMBEDDER_NAME = os.getenv("EMBEDDER_NAME", "BAAI/bge-base-en-v1.5")
TOP_K = int(os.getenv("TOP_K", "5"))
FUSION_ALPHA = float(os.getenv("FUSION_ALPHA", "0.6"))


print("Loading sentence transformer model...")
embedder = SentenceTransformer(EMBEDDER_NAME)
print("Model loaded.")


@dataclass
class DocIndex:
    file_name: str
    chunks: List[str]
    bm25: BM25Okapi
    vector_index: Any  # faiss index


DOCS: Dict[str, DocIndex] = {}


def extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    parts: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)
    full = "\n\n".join(parts).strip()
    return full


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    text = (text or "").replace("\x00", " ").strip()
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
        if chunk_size - overlap <= 0:
            break
    return chunks


def build_index(chunks: List[str]) -> Tuple[BM25Okapi, Any]:
    tokens = [c.lower().split() for c in chunks]
    bm25 = BM25Okapi(tokens)

    embeddings = embedder.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    embeddings = embeddings.astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return bm25, index


def retrieve(doc: DocIndex, query: str, top_k: int = TOP_K) -> List[str]:
    q = query.strip() or "general"
    q_emb = embedder.encode([q], convert_to_numpy=True, normalize_embeddings=True).astype("float32")

    vec_scores, vec_ids = doc.vector_index.search(q_emb, min(top_k, len(doc.chunks)))
    vec_scores = vec_scores[0]
    vec_ids = vec_ids[0]

    vec_map: Dict[int, float] = {}
    for idx, score in zip(vec_ids.tolist(), vec_scores.tolist()):
        if idx >= 0:
            vec_map[idx] = float(score)

    q_tokens = q.lower().split()
    bm25_scores = doc.bm25.get_scores(q_tokens)
    bm25_top_ids = np.argsort(bm25_scores)[::-1][: min(top_k, len(doc.chunks))]

    bm25_map: Dict[int, float] = {}
    for idx in bm25_top_ids.tolist():
        bm25_map[idx] = float(bm25_scores[idx])

    def norm_map(m: Dict[int, float]) -> Dict[int, float]:
        if not m:
            return {}
        mx = max(m.values()) or 1.0
        return {k: (v / mx) for k, v in m.items()}

    vec_norm = norm_map(vec_map)
    bm25_norm = norm_map(bm25_map)

    candidate_ids = set(vec_map.keys()) | set(bm25_map.keys())
    fused: List[Tuple[int, float]] = []
    for idx in candidate_ids:
        v = vec_norm.get(idx, 0.0)
        b = bm25_norm.get(idx, 0.0)
        score = FUSION_ALPHA * v + (1.0 - FUSION_ALPHA) * b
        fused.append((idx, score))

    fused.sort(key=lambda x: x[1], reverse=True)
    top_ids = [idx for idx, _ in fused[:top_k]]
    return [doc.chunks[i] for i in top_ids]


def retrieve_all_context(doc: DocIndex, top_k: int = 10) -> str:
    """Get a broad context for summary/flashcard generation."""
    # Sample evenly across all chunks for broad coverage
    n = len(doc.chunks)
    if n <= top_k:
        return "\n\n---\n\n".join(doc.chunks)
    step = n // top_k
    sampled = [doc.chunks[i * step] for i in range(top_k)]
    return "\n\n---\n\n".join(sampled)


def groq_chat(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 1200) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set in your .env file.")

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {"model": GROQ_MODEL, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if not r.ok:
            print(f"[Groq ERROR] status={r.status_code} body={r.text[:1000]}")
            r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        raise RuntimeError("Groq API request timed out. Please try again.")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Cannot reach Groq API. Check your internet connection. ({e})")


def parse_json_maybe_markdown(text: str) -> Any:
    if text is None:
        raise ValueError("Empty LLM response")
    t = text.strip()
    # Remove markdown fences
    t = re.sub(r"^```(?:json)?\s*|```\s*$", "", t, flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"(\{.*\}|\[.*\])", t, flags=re.DOTALL)
    if m:
        candidate = m.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            pass
    raise ValueError("Could not parse JSON from LLM response.")


def _strip_markdown(s: str) -> str:
    s = s or ""
    s = re.sub(r"```.*?```", "", s, flags=re.DOTALL)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"^>\s*", "", s, flags=re.MULTILINE)
    return s.strip()


def _option_letter(i: int) -> str:
    return chr(65 + i)


def _make_paragraph(styles, text: str, style_name: str = "BodyText") -> Paragraph:
    safe = _strip_markdown(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\n", "<br/>")
    return Paragraph(safe, styles[style_name])


def render_mcq_pdf_bytes(
    file_name: str,
    topic: Optional[str],
    mcqs: List[Dict[str, Any]],
    with_answers: bool,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
    styles = getSampleStyleSheet()
    heading = ParagraphStyle("Heading", parent=styles["Heading2"], spaceAfter=12)

    story: List[Any] = []
    story.append(Paragraph("RAGnition MCQ Test", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(_make_paragraph(styles, f"Document: {file_name}", "BodyText"))
    if topic:
        story.append(_make_paragraph(styles, f"Topic: {topic}", "BodyText"))
    story.append(_make_paragraph(styles, f"Total Questions: {len(mcqs)}", "BodyText"))
    story.append(Spacer(1, 14))

    for i, mcq in enumerate(mcqs, start=1):
        story.append(Paragraph(f"Q{i}. {mcq.get('question', '')}", heading))
        for j, opt in enumerate(mcq.get("options", [])):
            story.append(_make_paragraph(styles, f"{_option_letter(j)}. {opt}", "BodyText"))

        if with_answers:
            correct_idx = int(mcq.get("correct", 0))
            story.append(Spacer(1, 6))
            story.append(_make_paragraph(styles, f"Correct Answer: {_option_letter(correct_idx)}", "BodyText"))
            explanations = mcq.get("explanations") or []
            if explanations:
                story.append(Spacer(1, 4))
                story.append(_make_paragraph(styles, "Option Explanations:", "BodyText"))
                for j, exp in enumerate(explanations):
                    exp_text = exp or ""
                    story.append(_make_paragraph(styles, f"{_option_letter(j)}: {exp_text}", "BodyText"))

        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def render_mock_pdf_bytes(
    file_name: str,
    topic: Optional[str],
    test: Dict[str, Any],
    with_answers: bool,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
    styles = getSampleStyleSheet()
    heading = ParagraphStyle("Heading", parent=styles["Heading2"], spaceAfter=12)

    story: List[Any] = []
    story.append(Paragraph("RAGnition Mock Test", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(_make_paragraph(styles, f"Document: {file_name}", "BodyText"))
    if topic:
        story.append(_make_paragraph(styles, f"Topic: {topic}", "BodyText"))
    story.append(_make_paragraph(styles, f"Total Marks: {test.get('totalMarks', '')}", "BodyText"))
    story.append(Spacer(1, 14))

    for section in test.get("sections", []):
        story.append(Paragraph(section.get("name", "Section"), heading))
        story.append(_make_paragraph(styles, f"Marks per question: {section.get('marksPerQuestion', '')}", "BodyText"))
        story.append(Spacer(1, 10))

        for idx, q in enumerate(section.get("questions", []), start=1):
            story.append(Paragraph(f"{idx}. {q.get('question', '')}", styles["Heading3"]))
            if with_answers:
                story.append(Spacer(1, 6))
                story.append(_make_paragraph(styles, f"Answer: {q.get('answer', '')}", "BodyText"))
            story.append(Spacer(1, 12))

        story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def render_chat_pdf_bytes(file_name: str, messages: List[Dict[str, str]]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
    styles = getSampleStyleSheet()

    story: List[Any] = []
    story.append(Paragraph("RAGnition Chat History", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(_make_paragraph(styles, f"Document: {file_name}", "BodyText"))
    story.append(Spacer(1, 14))

    for m in messages:
        role = (m.get("role") or "user").capitalize()
        content = m.get("content") or ""
        story.append(Paragraph(f"{role}:", styles["Heading3"]))
        story.append(_make_paragraph(styles, content, "BodyText"))
        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def render_summary_pdf_bytes(file_name: str, summary: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=40)
    styles = getSampleStyleSheet()
    heading = ParagraphStyle("SectionHeading", parent=styles["Heading2"], spaceAfter=8, spaceBefore=14)

    story: List[Any] = []
    story.append(Paragraph("RAGnition Smart Summary", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(_make_paragraph(styles, f"Document: {file_name}", "BodyText"))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Overview", heading))
    story.append(_make_paragraph(styles, summary.get("overview", ""), "BodyText"))
    story.append(Spacer(1, 12))

    if summary.get("keyPoints"):
        story.append(Paragraph("Key Points", heading))
        for i, pt in enumerate(summary["keyPoints"], 1):
            story.append(_make_paragraph(styles, f"{i}. {pt}", "BodyText"))
        story.append(Spacer(1, 12))

    if summary.get("concepts"):
        story.append(Paragraph("Key Concepts", heading))
        for c in summary["concepts"]:
            story.append(_make_paragraph(styles, f"{c.get('term', '')}: {c.get('definition', '')}", "BodyText"))
        story.append(Spacer(1, 12))

    if summary.get("studyTips"):
        story.append(Paragraph("Study Tips", heading))
        for tip in summary["studyTips"]:
            story.append(_make_paragraph(styles, f"• {tip}", "BodyText"))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    # FIX: Accept both .pdf extension AND application/pdf MIME type
    filename = file.filename or ""
    mime = (file.content_type or "").lower()
    if not filename.lower().endswith(".pdf") and mime not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_pdf_text(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text found in PDF. The file may be a scanned image PDF.")

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Failed to chunk document text.")

    bm25, index = build_index(chunks)
    doc_id = uuid.uuid4().hex
    DOCS[doc_id] = DocIndex(file_name=filename, chunks=chunks, bm25=bm25, vector_index=index)
    return {"docId": doc_id, "fileName": filename, "chunks": len(chunks)}


def get_doc(doc_id: str) -> DocIndex:
    doc = DOCS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found. Please upload a PDF first.")
    return doc


def build_context(doc: DocIndex, query: str, max_chars: int = 4000) -> str:
    excerpts = retrieve(doc, query, top_k=TOP_K)
    # Truncate each excerpt and total context to avoid token overflow
    truncated = [e[:600] for e in excerpts]
    context = "\n\n---\n\n".join(truncated)
    return context[:max_chars]


@app.post("/api/chat")
async def chat(payload: Dict[str, Any]) -> Dict[str, str]:
    doc_id = payload.get("docId")
    messages = payload.get("messages") or []
    if not doc_id or not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="Invalid payload for /api/chat.")

    doc = get_doc(doc_id)
    last_user = ""
    for m in messages[::-1]:
        if m.get("role") == "user":
            last_user = m.get("content") or ""
            break
    context = build_context(doc, last_user)

    system_prompt = (
        "You are a helpful study companion named RAGnition. Answer the user's question ONLY using the provided document excerpts.\n"
        "If the answer is not present in the excerpts, respond exactly: I couldn't find that in the uploaded document.\n"
        "Be concise and accurate. Use markdown for lists and structure when helpful.\n\n"
        f"Document excerpts:\n{context}"
    )

    groq_messages = [{"role": "system", "content": system_prompt}]
    for m in messages[-8:]:
        role = m.get("role") or "user"
        content = m.get("content") or ""
        if role not in ("user", "assistant"):
            role = "user"
        groq_messages.append({"role": role, "content": content})

    reply = groq_chat(groq_messages, temperature=0.2, max_tokens=1200)
    return {"reply": reply}


@app.post("/api/generate-mcq")
async def generate_mcq(payload: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = payload.get("docId")
    count = payload.get("count")
    topic = payload.get("topic") or ""
    if not doc_id or not count:
        raise HTTPException(status_code=400, detail="Invalid payload for /api/generate-mcq.")

    doc = get_doc(doc_id)
    query = topic.strip() or "general study"
    context = build_context(doc, query)

    system_prompt = (
        "You generate exam-style multiple choice questions from provided document excerpts.\n"
        "Return ONLY valid JSON (no markdown fences) with this schema:\n"
        "{\n"
        '  "mcqs": [\n'
        "    {\n"
        '      "question": string,\n'
        '      "options": [string, string, string, string],\n'
        '      "correct": integer,  // 0-3 index of the correct option\n'
        '      "explanations": [string, string, string, string]  // explanation for EACH option\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Ground every question, option, and explanation strictly in the excerpts.\n"
        "- Explanations must explain why each option is correct or incorrect.\n"
        "- Do not include any extra keys.\n"
    )

    user_prompt = (
        f"Topic focus (may be empty): {topic or '(none)'}\n"
        f"Number of MCQs to generate: {count}\n\n"
        f"Document excerpts:\n{context}\n\n"
        "Generate the MCQs now."
    )

    raw = groq_chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.2,
        max_tokens=4000,
    )
    parsed = parse_json_maybe_markdown(raw)
    mcqs = parsed.get("mcqs", [])
    return {"mcqs": mcqs}


@app.post("/api/generate-mock-test")
async def generate_mock_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = payload.get("docId")
    total_marks = payload.get("totalMarks")
    topic = payload.get("topic") or ""
    if not doc_id or not total_marks:
        raise HTTPException(status_code=400, detail="Invalid payload for /api/generate-mock-test.")

    # Cap at 100 marks
    total_marks = min(int(total_marks), 100)

    # Smart section division based on total marks
    # Section A: 2 marks each  |  Section B: 5 marks each  |  Section C: 10 marks each (exactly 2 Qs)
    sec_c_marks = 20  # 2 questions * 10 marks each (fixed)
    remaining = total_marks - sec_c_marks
    # Split remaining 40/60 between A and B
    sec_a_marks = max(2, round(remaining * 0.40 / 2) * 2)   # round to nearest even
    sec_b_marks = remaining - sec_a_marks
    sec_a_count = max(1, sec_a_marks // 2)
    sec_b_count = max(1, sec_b_marks // 5)

    doc = get_doc(doc_id)
    query = topic.strip() or "general study"
    context = build_context(doc, query)

    system_prompt = (
        "You generate a complete structured mock exam from provided document excerpts.\n"
        "Return ONLY valid JSON (no markdown fences) with this schema:\n"
        "{\n"
        '  "test": {\n'
        '    "title": string,\n'
        '    "totalMarks": number,\n'
        '    "sections": [\n'
        "      {\n"
        '        "name": string,\n'
        '        "marksPerQuestion": number,\n'
        '        "questions": [\n'
        '          {"question": string, "answer": string}\n'
        "        ]\n"
        "      }\n"
        "    ]\n"
        "  }\n"
        "}\n\n"
        "Rules:\n"
        "- Ground all questions and answers strictly in the excerpts.\n"
        "- Use EXACTLY three sections as specified in the user prompt.\n"
        "- For Section C, the 'answer' must be highly detailed and comprehensive (at least 3-4 paragraphs).\n"
        "- Do not include any extra keys.\n"
    )

    user_prompt = (
        f"Topic focus (may be empty): {topic or '(none)'}\n"
        f"Total marks: {total_marks}\n\n"
        f"Generate EXACTLY these sections:\n"
        f"  Section A (Short Answer) — {sec_a_count} questions × 2 marks each = {sec_a_count * 2} marks\n"
        f"  Section B (Medium Answer) — {sec_b_count} questions × 5 marks each = {sec_b_count * 5} marks\n"
        f"  Section C (Long Answer)  — 2 questions × 10 marks each = 20 marks\n\n"
        f"Document excerpts:\n{context}\n\n"
        "Generate the mock test now with exactly those question counts."
    )

    raw = groq_chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.2,
        max_tokens=5000,
    )
    parsed = parse_json_maybe_markdown(raw)
    return {"test": parsed.get("test")}


@app.post("/api/summarize")
async def summarize(payload: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = payload.get("docId")
    focus = payload.get("focus") or ""
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing docId.")

    doc = get_doc(doc_id)
    context = retrieve_all_context(doc, top_k=10)

    system_prompt = (
        "You are an expert study assistant. Create a comprehensive summary from the document excerpts.\n"
        "Return ONLY valid JSON (no markdown fences) with this schema:\n"
        "{\n"
        '  "summary": {\n'
        '    "overview": string,       // 3-5 sentence overview of the whole document\n'
        '    "keyPoints": [string],    // 5-8 key points/takeaways\n'
        '    "concepts": [{"term": string, "definition": string}],  // 4-8 important terms/concepts\n'
        '    "studyTips": [string]     // 3-5 actionable study tips for this material\n'
        "  }\n"
        "}\n"
        "Return ONLY the JSON, no extra text.\n"
    )

    user_prompt = (
        f"Focus area (if provided): {focus or '(none - full document)'}\n\n"
        f"Document excerpts:\n{context}\n\n"
        "Generate the summary now."
    )

    raw = groq_chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    parsed = parse_json_maybe_markdown(raw)
    return {"summary": parsed.get("summary")}


@app.post("/api/flashcards")
async def flashcards(payload: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = payload.get("docId")
    count = int(payload.get("count", 10))
    topic = payload.get("topic") or ""
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing docId.")

    doc = get_doc(doc_id)
    query = topic.strip() or "key concepts definitions"
    context = build_context(doc, query)

    system_prompt = (
        "You create revision flashcards from document excerpts.\n"
        "Return ONLY valid JSON (no markdown fences) with this schema:\n"
        "{\n"
        '  "flashcards": [\n'
        "    {\n"
        '      "front": string,   // question or term\n'
        '      "back": string,    // answer or definition\n'
        '      "hint": string     // optional short hint (can be empty string)\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- Make cards concise and focused\n"
        "- Mix definitions, key facts, and concept questions\n"
        "- Return ONLY the JSON\n"
    )

    user_prompt = (
        f"Topic focus: {topic or '(general)'}\n"
        f"Number of flashcards: {count}\n\n"
        f"Document excerpts:\n{context}\n\n"
        "Generate the flashcards now."
    )

    raw = groq_chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    parsed = parse_json_maybe_markdown(raw)
    return {"flashcards": parsed.get("flashcards", [])}


@app.post("/api/mcq-pdf")
async def mcq_pdf(payload: Dict[str, Any]) -> Response:
    doc_id = payload.get("docId")
    with_answers = bool(payload.get("withAnswers", False))
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing docId.")
    _ = get_doc(doc_id)
    mcqs = payload.get("mcqs") or []
    file_name = payload.get("fileName") or "document"
    topic = payload.get("topic") or None

    pdf_bytes = render_mcq_pdf_bytes(file_name=file_name, topic=topic, mcqs=mcqs, with_answers=with_answers)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="mcq-{"with-answers" if with_answers else "questions"}.pdf"'},
    )


@app.post("/api/mock-pdf")
async def mock_pdf(payload: Dict[str, Any]) -> Response:
    doc_id = payload.get("docId")
    with_answers = bool(payload.get("withAnswers", False))
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing docId.")
    _ = get_doc(doc_id)
    test = payload.get("test") or {}
    file_name = payload.get("fileName") or "document"
    topic = payload.get("topic") or None

    pdf_bytes = render_mock_pdf_bytes(file_name=file_name, topic=topic, test=test, with_answers=with_answers)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="mock-test-{"with-answers" if with_answers else "questions"}.pdf"'},
    )


@app.post("/api/chat-pdf")
async def chat_pdf(payload: Dict[str, Any]) -> Response:
    doc_id = payload.get("docId")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing docId.")
    _ = get_doc(doc_id)
    file_name = payload.get("fileName") or "document"
    messages = payload.get("messages") or []

    pdf_bytes = render_chat_pdf_bytes(file_name=file_name, messages=messages)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="chat-history.pdf"'},
    )


@app.post("/api/summary-pdf")
async def summary_pdf(payload: Dict[str, Any]) -> Response:
    doc_id = payload.get("docId")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing docId.")
    _ = get_doc(doc_id)
    file_name = payload.get("fileName") or "document"
    summary = payload.get("summary") or {}

    pdf_bytes = render_summary_pdf_bytes(file_name=file_name, summary=summary)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="summary.pdf"'},
    )
