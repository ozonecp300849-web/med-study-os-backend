# -*- coding: utf-8 -*-
"""AI-powered classification for UNCLASSIFIED exam questions.

Uses OpenRouter (free models) to classify questions that rule-based system
couldn't handle. Returns classifications with confidence scores.
"""
import json
import os
import sys
import urllib.request
from typing import Any

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BACKEND_DIR)
EXAM_DIR = os.path.join(ROOT, "Exam classifier")
sys.path.insert(0, os.path.join(EXAM_DIR, "tool"))

from lectures import LECTURE_TITLE, LECTURE_ORDER  # type: ignore

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "google/gemma-4-26b-a4b-it:free"

SYSTEM_PROMPT = """You are a medical exam classifier for Thai medical students.

Classify this exam question into one of the lecture topics below.
Medical terms should stay in English as taught in Thai medical schools.

Available lecture topics:
{topics}

Question: {stem}

Options:
{options}

Return ONLY valid JSON in this exact format:
{{"lecture": "L#", "confidence": 0.0-1.0, "reasoning": "brief explanation in 1-2 sentences"}}

confidence guidelines:
- 0.9+: Very clear match, question directly about this topic
- 0.7-0.9: Good match, question likely about this topic
- 0.5-0.7: Uncertain, could be multiple topics
- Below 0.5: Do not classify, return UNCLASSIFIED"""


def _build_topics_list() -> str:
    lines = []
    for key, title in sorted(LECTURE_TITLE.items(), key=lambda x: LECTURE_ORDER.get(x[0], 99)):
        if key != "UNCLASSIFIED":
            lines.append(f"- {key}: {title}")
    return "\n".join(lines)


def classify_with_ai(questions: list[dict[str, Any]], api_key: str) -> dict[str, Any]:
    topics_list = _build_topics_list()
    classifications = []

    for q in questions:
        qid = q.get("id", "")
        stem = q.get("stem", "")
        options = q.get("options", {})

        options_text = "\n".join(f"{k}: {v}" for k, v in sorted(options.items()))

        prompt = SYSTEM_PROMPT.format(
            topics=topics_list,
            stem=stem,
            options=options_text
        )

        try:
            payload = json.dumps({
                "model": FREE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
            }).encode("utf-8")

            req = urllib.request.Request(
                OPENROUTER_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://med-study-os.local",
                    "X-Title": "Med Study OS",
                },
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            text = data["choices"][0]["message"]["content"].strip()

            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)

            lecture = result.get("lecture", "UNCLASSIFIED")
            if lecture not in LECTURE_TITLE:
                lecture = "UNCLASSIFIED"

            classifications.append({
                "questionId": qid,
                "suggestedLecture": lecture,
                "confidence": min(1.0, max(0.0, float(result.get("confidence", 0)))),
                "reasoning": result.get("reasoning", "")
            })

        except Exception as e:
            classifications.append({
                "questionId": qid,
                "suggestedLecture": "UNCLASSIFIED",
                "confidence": 0.0,
                "reasoning": f"AI classification failed: {str(e)[:100]}"
            })

    return {
        "classifications": classifications,
        "model": FREE_MODEL
    }
