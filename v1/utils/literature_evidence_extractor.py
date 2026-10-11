"""
Utilities for turning downloaded literature into compact evidence records.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from pdf_reader import extract_sections, read_pdf_text


SECTION_KEYWORDS = [
    "abstract",
    "introduction",
    "method",
    "methods",
    "results",
    "discussion",
    "conclusion",
    "limitations",
]

MECHANISM_HINTS = {
    "shared_workspace": [
        "shared workspace", "shared space", "turn-taking", "yield", "waiting",
        "resource conflict", "coordination", "fluency", "blocking",
    ],
    "collision_contact": [
        "collision", "contact", "physical interaction", "safety", "comfort",
        "proximity", "near miss", "touch", "bump",
    ],
    "implicit_coordination": [
        "action observation", "implicit", "motion cue", "gaze", "trajectory",
        "timing", "anticipat", "body language", "hesitation",
    ],
    "communication_repair": [
        "communication", "repair", "misunderstanding", "clarif", "verbal",
        "speech", "vocal", "multimodal", "common ground",
    ],
    "embodiment": [
        "embodiment", "anthropomorphism", "body", "morphology", "soft",
        "compliance", "humanoid", "musculoskeletal", "limitation",
    ],
}


def load_pdf_evidence_source(paper: Dict[str, Any], max_chars: int = 24000) -> Dict[str, Any]:
    """
    Load compact text snippets from a downloaded PDF, with abstract fallback.
    """
    pdf_path = paper.get("local_pdf_path")
    if pdf_path:
        try:
            sections = extract_sections(pdf_path, SECTION_KEYWORDS)
            preferred_keys = [
                "abstract", "introduction", "method", "methods",
                "results", "discussion", "conclusion", "limitations",
            ]
            ordered_parts: List[str] = []
            for key in preferred_keys:
                value = sections.get(key)
                if value:
                    ordered_parts.append(f"[{key}]\n{value.strip()}")
            if not ordered_parts:
                full_text = read_pdf_text(pdf_path)
                ordered_parts = [full_text]
            combined = "\n\n".join(ordered_parts)
            return {
                "source_type": "full_text",
                "text": combined[:max_chars],
                "available_sections": [k for k, v in sections.items() if v],
            }
        except Exception:
            pass

    abstract = str(paper.get("abstract", "") or "")
    return {
        "source_type": "abstract",
        "text": abstract[:max_chars],
        "available_sections": ["abstract"] if abstract else [],
    }


def detect_mechanism_hints(text: str) -> List[str]:
    """
    Infer likely mechanism buckets from paper text using broad keyword hints.
    """
    lowered = (text or "").lower()
    matched = []
    for mechanism, keywords in MECHANISM_HINTS.items():
        if any(keyword in lowered for keyword in keywords):
            matched.append(mechanism)
    return matched


def compact_text_excerpt(text: str, max_chars: int = 2200) -> str:
    """
    Lightly normalize extracted paper text before prompting an LLM.
    """
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    return cleaned[:max_chars]
