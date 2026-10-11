"""
Helpers for aggregating literature evidence into scenario-linked mechanism cards.
"""

from __future__ import annotations

from typing import Any, Dict, List


MECHANISM_LABEL_MAP = {
    "shared_workspace": "shared workspace coordination",
    "collision_contact": "collision/contact adaptation",
    "implicit_coordination": "implicit coordination through action observation",
    "communication_repair": "explicit communication and repair",
    "embodiment": "bodily limitation understanding",
}


def mechanism_label(mechanism_type: str) -> str:
    return MECHANISM_LABEL_MAP.get(mechanism_type, mechanism_type.replace("_", " "))


def build_mechanism_cards(
    evidence_cards: List[Dict[str, Any]],
    scenario_factors: Dict[str, Any],
) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for card in evidence_cards or []:
        mechanism_type = card.get("mechanism_type") or "general"
        bucket = grouped.setdefault(
            mechanism_type,
            {
                "mechanism_type": mechanism_type,
                "mechanism": mechanism_label(mechanism_type),
                "supported_by": [],
                "scenario_link": [],
                "measurement_implications": [],
                "related_factors": [],
            },
        )
        title = card.get("paper_title")
        if title and title not in bucket["supported_by"]:
            bucket["supported_by"].append(title)
        scenario_link = card.get("scenario_transfer_note")
        if scenario_link and scenario_link not in bucket["scenario_link"]:
            bucket["scenario_link"].append(scenario_link)
        implication = card.get("measurement_implication")
        if implication and implication not in bucket["measurement_implications"]:
            bucket["measurement_implications"].append(implication)
        for factor in card.get("related_factors", []) or []:
            if factor not in bucket["related_factors"]:
                bucket["related_factors"].append(factor)

    known_factors = set(scenario_factors.get("all_factor_labels") or [])
    results = []
    for bucket in grouped.values():
        related = [f for f in bucket["related_factors"] if f in known_factors]
        bucket["related_factors"] = related
        bucket["supporting_paper_count"] = len(bucket["supported_by"])
        results.append(bucket)
    return sorted(results, key=lambda x: (-x.get("supporting_paper_count", 0), x.get("mechanism", "")))


def build_mechanism_coverage_report(
    mechanism_cards: List[Dict[str, Any]],
    scenario_factors: Dict[str, Any],
) -> Dict[str, Any]:
    scenario_mechanisms = scenario_factors.get("empathy_mechanisms") or []
    normalized_card_names = {card.get("mechanism", "") for card in mechanism_cards or []}
    paper_links = {
        card.get("mechanism", ""): card.get("supported_by", [])
        for card in mechanism_cards or []
    }
    covered = [m for m in scenario_mechanisms if m in normalized_card_names]
    missing = [m for m in scenario_mechanisms if m not in normalized_card_names]
    weakly_covered = [
        card.get("mechanism", "")
        for card in mechanism_cards or []
        if card.get("supporting_paper_count", 0) <= 1
    ]
    return {
        "covered": covered,
        "weakly_covered": weakly_covered,
        "missing": missing,
        "paper_links": paper_links,
    }
