"""Single-prompt template used for direct LLM scale baseline runs."""
from __future__ import annotations

DIRECT_PROMPT_TEMPLATE = """Design a perceived-empathy Likert scale for the human–robot collaboration scenario below.

{scenario_text}

Output Markdown only. Format example (illustrative structure only—not instructions on how to organize the scale):

# Empathy Scale

## Purpose

## Items
- ..."""


def build_direct_prompt_payload(scenario_text: str) -> dict:
    filled = DIRECT_PROMPT_TEMPLATE.format(scenario_text=scenario_text.strip())
    return {
        "template": DIRECT_PROMPT_TEMPLATE,
        "filled": filled,
        "temperature": 0.85,
        "n_runs": 5,
        "seeds": [42, 43, 44, 45, 46],
    }
