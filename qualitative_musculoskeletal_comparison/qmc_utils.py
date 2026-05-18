"""Shared helpers for qualitative comparison package."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

PKG_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_ROOT.parent

MECHANISM_KEYWORDS = {
    "shared_workspace": [
        "tool rack", "shared", "workspace", "turn", "yield", "wait", "space",
        "side by side", "simultaneous", "reach", "pick", "工位", "轮流", "让",
    ],
    "collision_recovery": [
        "bump", "collision", "contact", "brush", "retract", "cautious", "physical",
        "碰撞", "接触", "碰",
    ],
    "verbal_repair": [
        "said", "speak", "verbal", "phrase", "words", "你先", "我来", "apolog",
        "口头", "说",
    ],
    "mind_reading_risk": [
        "mental state", "emotionally intelligent", "anticipated when", "seemed to know",
        "sympath", "coping with an emotional", "read my mind", "猜",
    ],
    "generic_trust": [
        "trusted", "understood my goals", "understood my needs", "understood my intentions",
        "goals", "needs",
    ],
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_scale_markdown(md_text: str) -> List[Dict[str, str]]:
    """Extract items from scale markdown (### dimension + several list styles)."""
    items: List[Dict[str, str]] = []
    current_dim: Optional[str] = None
    in_items_section = False

    def add_item(text: str) -> None:
        text = text.strip()
        if len(text) < 18:
            return
        if text.lower().startswith(("## ", "# ")):
            return
        items.append({"dimension": current_dim or "Unknown", "item_text": text})

    for line in md_text.splitlines():
        stripped = line.strip()
        if re.match(r"^##\s+Items\b", stripped, re.IGNORECASE):
            in_items_section = True
            current_dim = "Items"
            continue
        if re.match(r"^##\s+", stripped) and not re.match(r"^###", stripped):
            if in_items_section and stripped.lower().startswith("## ") and "item" not in stripped.lower():
                pass
        dim_match = re.match(r"^###\s+(.+)$", stripped)
        if dim_match:
            current_dim = dim_match.group(1).strip()
            in_items_section = True
            continue
        if not in_items_section and not current_dim:
            continue

        for pattern in (
            r"^[-*]\s*Item\s+\d+:\s*(.+)$",
            r"^\d+\.\s+(.+)$",
            r"^[-*]\s+(.+)$",
        ):
            m = re.match(pattern, stripped, re.IGNORECASE)
            if m:
                add_item(m.group(1))
                break
    return items


def scenario_text_from_interview(summary: Dict[str, Any]) -> str:
    parts = [
        f"Assessment context: {summary.get('assessment_context', '')}",
        f"Robot platform: {summary.get('robot_platform', '')}",
        f"Interaction: {summary.get('interaction_modalities', '')}",
        f"Collaboration: {summary.get('collaboration_pattern', '')}",
        f"Environment: {summary.get('environmental_setting', '')}",
    ]
    for label, key in [
        ("Expected empathy forms", "expected_empathy_forms"),
        ("Failure modes", "failure_modes"),
        ("Assessment challenges", "assessment_challenges"),
        ("Contrast vs rigid arm", "contrast_points"),
    ]:
        val = summary.get(key) or []
        if val:
            parts.append(f"{label}: {'; '.join(val) if isinstance(val, list) else val}")
    return "\n".join(p for p in parts if p.strip())


def score_scene_fit(items: List[Dict[str, str]]) -> Dict[str, Any]:
    """Heuristic scene-fit score for ranking direct-LLM runs (higher = more on-scenario)."""
    text_blob = " ".join(i["item_text"].lower() for i in items)
    hits = {k: sum(1 for w in words if w.lower() in text_blob) for k, words in MECHANISM_KEYWORDS.items()}
    mind = hits.get("mind_reading_risk", 0)
    generic = hits.get("generic_trust", 0)
    scene = (
        hits.get("shared_workspace", 0)
        + hits.get("collision_recovery", 0) * 1.2
        + hits.get("verbal_repair", 0) * 1.1
    )
    penalty = mind * 2.0 + max(0, generic - 2) * 0.8
    total = scene - penalty + min(len(items), 20) * 0.05
    return {
        "score": round(total, 3),
        "hits": hits,
        "n_items": len(items),
        "n_dimensions": len({i["dimension"] for i in items}),
    }
