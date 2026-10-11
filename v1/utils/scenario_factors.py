"""
Scenario-factor extraction and factor-driven query planning.

This module is generic: it extracts collaboration mechanisms from any HRI
scenario text and turns them into research intents and queries. Demo-specific
seed queries may be supplied by a scenario config, but global logic never
depends on a demo name.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


FACTOR_GROUPS = {
    "interaction_modes": {
        "side-by-side": ["side-by-side", "side by side", "parallel", "\u5e76\u6392"],
        "face-to-face": ["face-to-face", "face to face", "\u9762\u5bf9\u9762"],
        "remote": ["remote", "online", "text chat", "\u8fdc\u7a0b", "\u7ebf\u4e0a"],
        "turn-taking": ["turn-taking", "turn taking", "\u8f6e\u6d41", "\u4ea4\u66ff"],
    },
    "resource_relations": {
        "shared": ["shared", "same workspace", "shared workspace", "tool rack", "\u5171\u4eab", "\u5de5\u5177\u67b6"],
        "contention": ["conflict", "competition", "compete", "contention", "\u51b2\u7a81", "\u7ade\u4e89"],
        "role-constrained division": ["division", "role constraint", "only human", "only robot", "\u5206\u5de5", "\u53ea\u80fd\u7531"],
    },
    "communication_modes": {
        "language": ["voice", "speech", "language", "verbal", "\u8bed\u8a00", "\u8bed\u97f3", "\u8bf4\u8bdd"],
        "action observation": ["gesture", "motion", "action observation", "implicit", "gaze", "\u52a8\u4f5c", "\u89c2\u5bdf", "\u9ed8\u5951"],
        "visual cues": ["display", "screen", "visual", "light", "led", "\u5c4f\u5e55", "\u706f"],
        "haptic/contact": ["haptic", "touch", "contact", "force", "\u89e6\u89c9", "\u63a5\u89e6"],
    },
    "robot_type": {
        "musculoskeletal": ["musculoskeletal", "\u808c\u8089\u9aa8\u9abc"],
        "humanoid": ["humanoid", "human-like", "anthropomorphic", "\u7c7b\u4eba"],
        "collaborative arm": ["collaborative arm", "cobot", "robot arm", "\u673a\u68b0\u81c2"],
        "mobile": ["mobile", "\u79fb\u52a8"],
        "chatbot": ["chatbot", "text-based", "\u804a\u5929"],
    },
    "risk_factors": {
        "physical contact/collision": ["collision", "contact", "touch", "\u78b0\u649e", "\u63a5\u89e6", "\u8eab\u4f53\u63a5\u89e6"],
        "shared-space interference": ["shared workspace", "shared space", "\u5171\u4eab\u5de5\u4f5c\u7a7a\u95f4", "\u5171\u4eab\u7a7a\u95f4"],
        "safety concern": ["safety", "injury", "risk", "\u5b89\u5168", "\u5371\u9669", "\u98ce\u9669"],
    },
    "embodied_cues": {
        "embodied motion": ["embodiment", "body", "limb", "torso", "arm", "\u8eab\u4f53\u6027", "\u8eab\u4f53"],
        "visible bodily limitation": ["constraint", "difficulty", "cannot reach", "range limit", "access limit", "\u9650\u5236", "\u56f0\u96be", "\u62ff\u4e0d\u5230"],
        "human-like morphology": ["human-like", "humanoid", "musculoskeletal", "\u7c7b\u4eba", "\u808c\u8089\u9aa8\u9abc"],
    },
    "task_context_terms": {
        "assembly": ["assembly", "\u88c5\u914d"],
        "tool rack": ["tool rack", "\u5de5\u5177\u67b6"],
        "parts": ["parts", "component", "\u96f6\u4ef6"],
        "factory": ["factory", "workstation", "\u5de5\u5382", "\u5de5\u4f4d"],
        "home": ["home", "\u5bb6\u5ead"],
        "counseling": ["counseling", "\u54a8\u8be2"],
    },
}


MECHANISM_TO_FACTORS = {
    "collision/contact adaptation": ["physical contact/collision", "safety concern", "embodied motion"],
    "shared workspace coordination": ["shared", "contention", "shared-space interference"],
    "implicit coordination through action observation": ["action observation", "side-by-side", "embodied motion"],
    "role-constrained task allocation": ["role-constrained division", "human-only actions/items", "robot-only actions/items"],
    "explicit communication and repair": ["language", "visual cues"],
    "bodily limitation understanding": ["visible bodily limitation", "musculoskeletal", "humanoid"],
}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_as_text(v) for v in value.values())
    return str(value)


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        item = str(item).strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _contains(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def scenario_to_text(scenario: Dict[str, Any] | str) -> str:
    if isinstance(scenario, str):
        return scenario
    fields = [
        "name",
        "description",
        "assessment_context",
        "robot_platform",
        "interaction_modalities",
        "collaboration_pattern",
        "environmental_setting",
        "assessment_goals",
        "expected_empathy_forms",
        "assessment_challenges",
        "measurement_requirements",
        "contrast_points",
        "failure_modes",
        "role_constraints",
        "shared_resources",
        "seed_queries",
    ]
    return "\n".join(_as_text(scenario.get(field, "")) for field in fields)


def extract_scenario_specific_factors(
    scene_description: str,
    scenario: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    text = f"{scene_description or ''}\n{scenario_to_text(scenario or {})}".lower()

    factors: Dict[str, Any] = {}
    for group_name, options in FACTOR_GROUPS.items():
        hits = [label for label, keywords in options.items() if _contains(text, keywords)]
        factors[group_name] = _dedupe(hits) or ["unspecified"]

    role_constraints = []
    if re.search(r"(human|person|operator|user).{0,20}(only|exclusive)", text) or "\u53ea\u80fd\u7531\u4eba" in text:
        role_constraints.append("human-only actions/items")
    if re.search(r"(robot|machine).{0,20}(only|exclusive)", text) or "\u53ea\u80fd\u7531\u673a\u5668\u4eba" in text:
        role_constraints.append("robot-only actions/items")
    if any(k in text for k in ["both can", "both may", "\u53cc\u65b9\u90fd", "\u90fd\u53ef\u4ee5"]):
        role_constraints.append("shared-capability actions/items")
    factors["role_constraints"] = _dedupe(role_constraints) or []

    factors["physical_contact_risk"] = any(
        x in factors.get("risk_factors", [])
        for x in ["physical contact/collision", "safety concern"]
    )

    mechanisms = []
    for mechanism, related in MECHANISM_TO_FACTORS.items():
        flat = set()
        for key in ["interaction_modes", "resource_relations", "communication_modes", "robot_type", "risk_factors", "embodied_cues", "role_constraints"]:
            flat.update(factors.get(key, []))
        if any(r in flat for r in related):
            mechanisms.append(mechanism)
    factors["empathy_mechanisms"] = _dedupe(mechanisms)
    factors["all_factor_labels"] = flatten_factor_labels(factors)
    return factors


def flatten_factor_labels(factors: Dict[str, Any]) -> List[str]:
    labels: List[str] = []
    for key, value in factors.items():
        if key in {"physical_contact_risk", "all_factor_labels"}:
            continue
        if isinstance(value, list):
            labels.extend(v for v in value if v and v != "unspecified")
    return _dedupe(labels)


def format_scenario_factors(factors: Dict[str, Any]) -> str:
    lines = []
    for key, value in factors.items():
        if isinstance(value, list):
            rendered = ", ".join(str(v) for v in value) if value else "none"
        else:
            rendered = str(value)
        lines.append(f"{key}: {rendered}")
    return "\n".join(lines)


def build_factor_intents(factors: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert factors into research intents before query construction."""
    labels = set(flatten_factor_labels(factors))
    intents: List[Dict[str, Any]] = []

    def add(intent: str, related: List[str], rationale: str) -> None:
        if any(r in labels for r in related):
            intents.append({"intent": intent, "related_factors": [r for r in related if r in labels], "rationale": rationale})

    add(
        "Find work on physical HRI safety, contact, collision, and comfort",
        ["physical contact/collision", "safety concern", "embodied motion"],
        "Contact risk changes empathy judgments through comfort, tension, and perceived care.",
    )
    add(
        "Find work on shared workspace coordination, resource conflict, and fluency",
        ["shared", "contention", "shared-space interference"],
        "Shared resources create waiting, yielding, and conflict-management mechanisms.",
    )
    add(
        "Find work on implicit coordination through motion, gaze, and action observation",
        ["action observation", "side-by-side", "embodied motion"],
        "Implicit coordination can make the robot seem considerate without explicit speech.",
    )
    add(
        "Find work on explicit communication, repair, and common ground in HRI",
        ["language", "visual cues"],
        "Explicit channels shape perceived understanding during errors or uncertainty.",
    )
    add(
        "Find work on robot embodiment, anthropomorphism, and bodily limitation perception",
        ["musculoskeletal", "humanoid", "visible bodily limitation", "human-like morphology"],
        "Robot body form and limitations shape perspective-taking and empathy attribution.",
    )
    add(
        "Find work on task allocation and role constraints in human-robot teams",
        ["role-constrained division", "human-only actions/items", "robot-only actions/items", "shared-capability actions/items"],
        "Role constraints shape whether help, delay, and accommodation feel fair.",
    )

    if not intents:
        intents.append({
            "intent": "Find general perceived robot empathy, trust, comfort, and HRI scale validation work",
            "related_factors": [],
            "rationale": "Fallback when scenario factors are sparse.",
        })
    return intents


def build_factor_based_queries(
    scenario: Dict[str, Any],
    factors: Dict[str, Any] | None = None,
    max_queries: int = 16,
) -> List[str]:
    """Build queries only through factors -> intents -> queries."""
    factors = factors or extract_scenario_specific_factors(scenario_to_text(scenario), scenario)
    intents = build_factor_intents(factors)
    task_terms = [t for t in factors.get("task_context_terms", []) if t != "unspecified"]
    robot_terms = [r for r in factors.get("robot_type", []) if r != "unspecified"]

    queries: List[str] = []
    for item in intents:
        intent = item["intent"].lower()
        if "physical hri" in intent:
            queries.append("human robot physical interaction collision contact comfort")
            queries.append("human robot shared workspace safety proxemics contact avoidance")
            queries.append("physical human robot interaction safety comfort questionnaire perceived collision risk")
        elif "shared workspace" in intent:
            queries.append("human robot collaboration shared workspace coordination fluency")
            queries.append("side by side assembly human robot yielding waiting turn taking")
            queries.append("shared workspace human robot coordination fluency measurement collaborative assembly")
        elif "implicit coordination" in intent:
            queries.append("human robot collaboration implicit coordination action observation")
            queries.append("human robot team fluency anticipation motion cues collaborative assembly")
            queries.append("human robot action observation intention legibility motion cues questionnaire")
        elif "explicit communication" in intent:
            queries.append("human robot collaboration verbal communication repair common ground")
            queries.append("human robot multimodal communication repair clarification collaborative task")
            queries.append("robot intent communication verbal cues common ground perceived understanding scale")
        elif "embodiment" in intent:
            queries.append("human robot interaction embodiment anthropomorphism bodily limitations empathy")
            queries.append("musculoskeletal humanoid robot embodiment physical human robot interaction")
            queries.append("humanoid musculoskeletal robot embodiment anthropomorphism user perception questionnaire")
        elif "task allocation" in intent:
            queries.append("human robot collaboration task allocation role constraints shared resources")
            queries.append("human robot collaborative assembly division of labor handover shared tools")
            queries.append("human robot role allocation fairness shared resource coordination questionnaire")
        else:
            queries.append("perceived robot empathy trust comfort scale validation HRI")
            queries.append("human robot collaboration empathy trust fluency perceived understanding")
            queries.append("human robot empathy questionnaire item development psychometrics")

    if task_terms:
        queries.append("human robot collaboration " + " ".join(task_terms[:3]) + " empathy trust")
        queries.append("shared workspace " + " ".join(task_terms[:3]) + " coordination fluency hri")
        queries.append(" ".join(task_terms[:3]) + " human robot questionnaire perceived understanding comfort")
    if robot_terms:
        queries.append("human robot interaction " + " ".join(robot_terms[:3]) + " empathy embodiment")
        queries.append("physical human robot interaction " + " ".join(robot_terms[:3]) + " collaboration")
        queries.append(" ".join(robot_terms[:3]) + " user perception scale trust comfort coordination")

    for seed in scenario.get("seed_queries", []) if isinstance(scenario, dict) else []:
        queries.append(str(seed))

    return _dedupe(q for q in queries if len(q.split()) >= 4)[:max_queries]
