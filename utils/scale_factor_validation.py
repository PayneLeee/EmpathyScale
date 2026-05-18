"""Validate whether generated scale content structurally covers scenario factors."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

try:
    from scenario_factors import flatten_factor_labels
except ImportError:  # pragma: no cover - package import path
    from .scenario_factors import flatten_factor_labels


DEMO_REQUIRED_GROUPS = {
    "collision/contact": ["physical contact/collision", "safety concern", "contact-risk", "collision", "contact"],
    "shared workspace": ["shared", "contention", "shared-space interference", "resource coordination", "workspace"],
    "implicit coordination": ["action observation", "implicit coordination", "side-by-side", "motion", "observe"],
}

BEHAVIOR_TERMS = [
    "tool", "rack", "part", "assembly", "reach", "wait", "yield", "take", "handover",
    "collision", "contact", "observe", "gesture", "motion", "pause", "space", "yield",
    "\u5de5\u5177", "\u5de5\u5177\u67b6", "\u96f6\u4ef6", "\u88c5\u914d", "\u7b49\u5f85",
    "\u8ba9\u4f4d", "\u78b0\u649e", "\u63a5\u89e6", "\u89c2\u5bdf", "\u52a8\u4f5c",
]


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(_as_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_as_text(v) for v in value)
    return str(value)


def normalize_item(item: Any, dimension: str = "Unknown") -> Dict[str, Any]:
    if isinstance(item, dict):
        out = dict(item)
        out.setdefault("dimension", dimension)
        out.setdefault("item_text", out.get("text", ""))
        out.setdefault("related_factors", [])
        out.setdefault("scenario_mechanism", "")
        out.setdefault("source_basis", {})
        out.setdefault("generation_reason", "")
        out.setdefault("literature_basis_status", "fallback_reasoning")
        return out
    return {
        "dimension": dimension,
        "item_text": str(item),
        "related_factors": [],
        "scenario_mechanism": "",
        "source_basis": {},
        "generation_reason": "",
        "literature_basis_status": "fallback_reasoning",
    }


def flatten_items(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for block in blocks or []:
        dim = block.get("dimension") or block.get("construct") or block.get("name") or "Unknown"
        for item in block.get("items", []):
            items.append(normalize_item(item, dim))
    return items


def validate_scale_against_factors(
    factors: Dict[str, Any],
    constructs: List[Dict[str, Any]] | None,
    item_blocks: List[Dict[str, Any]] | None,
    demo_mode: bool = False,
) -> Dict[str, Any]:
    labels = flatten_factor_labels(factors or {})
    constructs = constructs or []
    items = flatten_items(item_blocks or [])

    factor_coverage: Dict[str, Dict[str, List[str]]] = {
        label: {"constructs": [], "items": []} for label in labels
    }

    for construct in constructs:
        ctext = _as_text(construct).lower()
        cname = construct.get("construct") or construct.get("name") or "Unnamed construct"
        for label in labels:
            if label.lower() in ctext or label in construct.get("related_factors", []):
                factor_coverage[label]["constructs"].append(cname)

    for idx, item in enumerate(items, 1):
        itext = _as_text(item).lower()
        iname = f"Item {idx}"
        for label in labels:
            if label.lower() in itext or label in item.get("related_factors", []):
                factor_coverage[label]["items"].append(iname)

    missing_factor_coverage = [
        label for label, cov in factor_coverage.items()
        if not cov["constructs"] and not cov["items"]
    ]
    construct_issues = [
        (c.get("construct") or c.get("name") or "Unnamed construct")
        for c in constructs
        if not c.get("related_factors") or not c.get("scenario_mechanism")
    ]

    n_items = len(items) or 1
    items_with_factors = sum(1 for i in items if i.get("related_factors"))
    items_with_reason = sum(1 for i in items if i.get("generation_reason"))
    behavior_specific = sum(
        1 for i in items
        if any(term.lower() in str(i.get("item_text", "")).lower() for term in BEHAVIOR_TERMS)
    )

    demo_groups = {}
    if demo_mode:
        all_text = _as_text({"constructs": constructs, "items": items, "factors": factors}).lower()
        for group, terms in DEMO_REQUIRED_GROUPS.items():
            demo_groups[group] = any(term.lower() in all_text for term in terms)

    result = {
        "n_constructs": len(constructs),
        "n_items": len(items),
        "factor_coverage": factor_coverage,
        "missing_factor_coverage": missing_factor_coverage,
        "constructs_missing_required_metadata": construct_issues,
        "items_with_related_factors_ratio": round(items_with_factors / n_items, 2),
        "items_with_generation_reason_ratio": round(items_with_reason / n_items, 2),
        "behavior_specific_item_ratio": round(behavior_specific / n_items, 2),
        "demo_required_groups": demo_groups,
        "passed": (
            not construct_issues
            and not missing_factor_coverage
            and (items_with_factors / n_items) >= 0.8
            and (items_with_reason / n_items) >= 0.8
            and (not demo_mode or (all(demo_groups.values()) and (behavior_specific / n_items) >= 0.3))
        ),
    }
    return result


def save_validation_report(report: Dict[str, Any], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
