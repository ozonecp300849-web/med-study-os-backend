# -*- coding: utf-8 -*-
"""
Med Study OS — local API bridge
================================
Wraps the two existing Python tools and serves their REAL results to the
Next.js frontend in the exact JSON shape the UI expects.

  • Exam classifier  ->  POST /api/quiz-master          -> { result: QuizMasterResult }
  • reslide          ->  POST /api/lecture-synthesizer  -> { result: LectureResult }

Run it:
    pip install -r requirements.txt          # fastapi + uvicorn (already installed)
    python backend/main.py                   # serves http://localhost:8000

Then in med-study-os/.env.local put:
    NEXT_PUBLIC_API_BASE=http://localhost:8000
and restart `npm run dev`. The two agents will now show your real data.
"""
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from ai_classify import classify_with_ai
from lectures import LECTURE_TITLE, LECTURE_ORDER, UNCLASSIFIED

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BACKEND_DIR)  # ...\Med guide

EXAM_DIR = os.path.join(ROOT, "Exam classifier")
EXAM_WORK = os.path.join(EXAM_DIR, "work")
RESLIDE_PROJECTS = os.path.join(ROOT, "concluder", "projects")

PHARMA_START = LECTURE_ORDER.get("L18", 16)
ACCENTS = ["teal", "emerald", "sky", "amber", "rose"]

app = FastAPI(title="Med Study OS API bridge", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


# ───────────────────────────── Quiz Master ──────────────────────────────
def _group_for(lecture_key: str) -> str:
    if lecture_key == UNCLASSIFIED[0]:
        return "Other"
    order = LECTURE_ORDER.get(lecture_key, 99)
    return "Patho/Radiology" if order < PHARMA_START else "Pharmacology"


def build_quiz_result() -> dict:
    uniq = _read_json(os.path.join(EXAM_WORK, "unique.json"), [])
    labels = _read_json(os.path.join(EXAM_WORK, "labels.json"), {})
    dupmap = _read_json(os.path.join(EXAM_WORK, "dupmap.json"), {})
    questions_all = _read_json(os.path.join(EXAM_WORK, "questions.json"), [])

    def lecture_of(qid: str) -> str:
        info = labels.get(qid)
        return info["lecture"] if info else UNCLASSIFIED[0]

    # questions
    questions = []
    counts: dict[str, int] = {}
    for q in uniq:
        lec = lecture_of(q["id"])
        counts[lec] = counts.get(lec, 0) + 1
        opts = q.get("options", {})
        questions.append(
            {
                "qid": q["id"],
                "topic": lec,
                "year": q.get("year", ""),
                "number": q.get("qnum", 0),
                "stem": q.get("stem", ""),
                "choices": [opts[k] for k in sorted(opts)],
                "duplicate": len(dupmap.get(q["id"], [])) > 0,
            }
        )

    # topics (ordered like the tool's output)
    topics = []
    for lec in sorted(counts, key=lambda k: LECTURE_ORDER.get(k, 99)):
        title = LECTURE_TITLE.get(lec, lec)
        topics.append(
            {
                "code": lec,
                "name": {"th": title, "en": title},
                "group": _group_for(lec),
                "questionCount": counts[lec],
            }
        )

    total_dups = sum(len(v) for v in dupmap.values() if isinstance(v, list))
    return {
        "fileName": "ExamBank_MD48-52 (real)",
        "totalExtracted": len(questions_all) or (len(uniq) + total_dups),
        "duplicatesRemoved": total_dups,
        "uniqueCount": len(uniq),
        "topics": topics,
        "questions": questions,
    }


# ─────────────────────────── Lecture Synthesizer ─────────────────────────
def _latest_project() -> str | None:
    if not os.path.isdir(RESLIDE_PROJECTS):
        return None
    dirs = [
        d
        for d in os.listdir(RESLIDE_PROJECTS)
        if os.path.isfile(os.path.join(RESLIDE_PROJECTS, d, "outline.json"))
    ]
    if not dirs:
        return None
    dirs.sort(
        key=lambda d: os.path.getmtime(os.path.join(RESLIDE_PROJECTS, d, "outline.json")),
        reverse=True,
    )
    return dirs[0]


def _bullets_from(content: list) -> list[str]:
    out: list[str] = []
    for block in content or []:
        if block.get("type") in ("bullet", "para", "step") and block.get("text"):
            out.append(block["text"])
        for child in block.get("children", []) or []:
            if child.get("text"):
                out.append("– " + child["text"])
    return out


def _high_yield_from(content: list) -> list[str]:
    out: list[str] = []
    for block in content or []:
        if block.get("type") in ("callout", "recap", "pill") and block.get("text"):
            out.append(block["text"])
    return out


def build_lecture_result() -> dict:
    project = _latest_project()
    if not project:
        return {
            "fileName": "—",
            "projectId": "",
            "originalPageCount": 0,
            "slideCount": 0,
            "figureCount": 0,
            "theme": "clinical",
            "summary": ["ยังไม่มีโปรเจกต์ reslide — รัน `python -m reslide all <input.pdf>` ก่อน"],
            "slides": [],
        }

    outline = _read_json(os.path.join(RESLIDE_PROJECTS, project, "outline.json"), {})
    raw_slides = outline.get("slides", [])

    slides = []
    all_pages: set[int] = set()
    fig_count = 0
    for i, s in enumerate(raw_slides):
        pages = s.get("src_pages", []) or []
        all_pages.update(p for p in pages if isinstance(p, int))
        fig_count += len(s.get("figures", []) or [])
        layout = s.get("layout", "bullets")
        allowed = {"title", "bullets", "compare-table", "figure-left", "figure-right", "steps", "recap"}
        slides.append(
            {
                "id": s.get("id", f"s{i}"),
                "kicker": {"th": s.get("kicker", ""), "en": s.get("kicker", "")},
                "titleTh": s.get("title_th", ""),
                "section": {"th": s.get("section", ""), "en": s.get("section", "")},
                "accent": ACCENTS[i % len(ACCENTS)],
                "layout": layout if layout in allowed else "bullets",
                "bullets": _bullets_from(s.get("content", [])),
                "highYield": _high_yield_from(s.get("content", [])),
                "srcPages": pages,
            }
        )

    # summary: objectives bullets from the first multi-bullet slide, else slide titles
    summary: list[str] = []
    for s in slides:
        if len(s["bullets"]) >= 3:
            summary = s["bullets"][:5]
            break
    if not summary:
        summary = [s["titleTh"] for s in slides if s["titleTh"]][:5]

    meta = outline.get("meta", {})
    src_pdf = outline.get("source_pdf", "")
    return {
        "fileName": os.path.basename(src_pdf) if src_pdf else f"{project}.pdf",
        "projectId": project,
        "originalPageCount": max(all_pages) if all_pages else len(slides),
        "slideCount": len(slides),
        "figureCount": fig_count,
        "theme": outline.get("theme", "clinical"),
        "summary": summary or [meta.get("title_th", "")],
        "slides": slides,
    }


# ───────────────────────────── Endpoints ────────────────────────────────
@app.get("/")
def root():
    return {"name": "Med Study OS API bridge", "status": "ok", "endpoints": ["/api/health", "/api/quiz-master", "/api/lecture-synthesizer"]}


@app.get("/api/health")
def health():
    return {"ok": True}


# Both accept POST from the UI (it sends the uploaded file as multipart).
# v1 returns your existing processed results; the file body is accepted and ignored.
@app.post("/api/quiz-master")
@app.get("/api/quiz-master")
def quiz_master():
    return {"result": build_quiz_result()}


@app.post("/api/lecture-synthesizer")
@app.get("/api/lecture-synthesizer")
def lecture_synthesizer():
    return {"result": build_lecture_result()}


@app.post("/api/ai-classify")
def ai_classify_endpoint(payload: dict = Body(...)):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "OPENROUTER_API_KEY not configured. Get free key at https://openrouter.ai/keys", "classifications": []}

    questions = payload.get("questions", [])
    if not questions:
        return {"classifications": []}

    result = classify_with_ai(questions, api_key)
    return result


if __name__ == "__main__":
    import uvicorn

    print("Med Study OS API bridge -> http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
