#!/usr/bin/env python3
"""
Dual-Scenario Empathy Scale Test
Runs the full three-agent pipeline twice with distinct scenarios:
  1) Co-Assembly Situation (embodied robot)
  2) Chat-Based Collaboration (non-embodied chat agent)

Verifies that each run produces a contextually distinct empathy scale draft
with scenario-appropriate modality and embodiment cues, and stores results
as two separate runs for comparison.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
from unittest.mock import patch, MagicMock

# Add project modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from main import MultiAgentWorkflow  # noqa: E402


PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _print_header():
    print("\n" + "=" * 86)
    print(" " * 18 + "DUAL-SCENARIO EMPATHY SCALE GENERATION PIPELINE TEST")
    print("=" * 86)


def _print_step(title: str):
    print("\n" + title)
    print("-" * 86)


def _scenario_dialogue_co_assembly() -> List[str]:
    """Simulated interview responses for embodied co-assembly with a physical robot."""
    return [
        "We need an empathy assessment for a human collaborating with a physical robot during joint assembly tasks in a shared workspace",
        "The robot is an embodied dual-arm manipulator with force feedback and haptic interfaces",
        "Coordination uses gesture cues, eye-gaze alignment, voice prompts, and physical handoffs of tools",
        "The setting is a manufacturing cell with close proximity collaboration and safety interlocks",
        "Goals include evaluating supportive behaviors when the human shows stress or hesitation and how the robot adapts timing",
        "We expect empathic behaviors like gentle haptic guidance, slowed motions, clarifying prompts, and safe distance adjustments",
        "Challenges include measuring trust during near-contact motion and the impact of tool passing latency",
        "We need a scale that captures embodied cues, shared workspace coordination, haptic feedback, and gesture-informed responsiveness",
    ]


def _scenario_dialogue_chat() -> List[str]:
    """Simulated interview responses for non-embodied chat-based collaboration."""
    return [
        "We need an empathy assessment for collaborating with a non-embodied chat agent to co-write a project",
        "The agent is purely software with no physical form; interaction is via chat UI with optional voice dictation",
        "Collaboration includes co-authoring documents, turn-taking in edits, and commenting on drafts via text and voice",
        "The setting is remote, asynchronous and synchronous sessions, version control, and document threads",
        "Goals include evaluating whether the agent acknowledges feelings, clarifies intent, and adapts tone and style",
        "We expect empathic behaviors like reflective summaries, polite tone shifts, timing sensitivity, and content-sensitive suggestions",
        "Challenges include measuring perceived presence, conversational transparency, and avoiding intrusive interventions",
        "We need a scale that focuses on chat modalities, non-embodiment, mixed voice-text dialogue, and co-authoring etiquette",
    ]


def _run_pipeline_with_responses(responses: List[str]) -> str:
    """Run the full pipeline with mocked input; return the run_id."""
    workflow = MultiAgentWorkflow()
    with patch('builtins.input', side_effect=responses + ['exit']):
        with patch('sys.stdin', new=MagicMock()):
            workflow.run_interview_session()
    return workflow.run_id


def _load_file_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return ""


def _verify_run_artifacts(run_id: str) -> Dict[str, Path]:
    """Verify required artifacts exist for a run; return important paths."""
    run_dir = PROJECT_ROOT / 'data' / 'runs' / run_id
    interview_dir = run_dir / 'interview_agent_group'
    literature_dir = run_dir / 'literature_search_agent_group'
    scale_dir = run_dir / 'empathy_scale_generation_agent_group'

    assert interview_dir.exists(), f"Missing interview dir: {interview_dir}"
    assert literature_dir.exists(), f"Missing literature dir: {literature_dir}"
    assert scale_dir.exists(), f"Missing scale dir: {scale_dir}"

    interview_summary = interview_dir / 'summary.json'
    literature_summary = literature_dir / 'summary.json'
    pdfs_dir = literature_dir / 'pdfs'
    scale_draft = scale_dir / 'scale_draft.md'

    assert interview_summary.exists(), "interview summary.json not found"
    assert literature_summary.exists(), "literature summary.json not found"
    assert pdfs_dir.exists(), "literature pdfs/ not found"
    assert scale_draft.exists(), "scale_draft.md not found"

    # Basic JSON load for interview/literature summaries
    with open(interview_summary, 'r', encoding='utf-8', errors='replace') as f:
        json.load(f)
    with open(literature_summary, 'r', encoding='utf-8', errors='replace') as f:
        json.load(f)

    # At least one PDF by design of the pipeline
    pdf_files = list(pdfs_dir.rglob('*.pdf'))
    assert len(pdf_files) > 0, "No PDFs downloaded"

    # Scale draft must be non-empty
    draft_text = _load_file_text(scale_draft)
    assert draft_text.strip(), "scale_draft.md is empty"

    return {
        'run_dir': run_dir,
        'scale_draft': scale_draft,
    }


def _contains_keywords(text: str, keywords: List[str], min_hits: int = 2) -> Tuple[int, List[str]]:
    text_l = text.lower()
    hits = [kw for kw in keywords if kw.lower() in text_l]
    return (len(hits), hits)


def _jaccard_similarity(a: str, b: str) -> float:
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def test_dual_scenarios():
    _print_header()

    # Scenario definitions
    co_assembly_responses = _scenario_dialogue_co_assembly()
    chat_responses = _scenario_dialogue_chat()

    _print_step("[1/5] Running Co-Assembly Scenario (Embodied Robot)")
    co_run_id = _run_pipeline_with_responses(co_assembly_responses)
    print(f"[OK] Co-Assembly run_id: {co_run_id}")

    _print_step("[2/5] Running Chat-Based Collaboration Scenario (Non-Embodied)")
    chat_run_id = _run_pipeline_with_responses(chat_responses)
    print(f"[OK] Chat run_id: {chat_run_id}")

    _print_step("[3/5] Verifying Artifacts for Both Runs")
    co_paths = _verify_run_artifacts(co_run_id)
    chat_paths = _verify_run_artifacts(chat_run_id)
    print("[OK] Artifacts verified for both runs")

    _print_step("[4/5] Validating Scenario-Specific Content in Scale Drafts")
    co_text = _load_file_text(co_paths['scale_draft'])
    chat_text = _load_file_text(chat_paths['scale_draft'])

    co_keywords = [
        "gesture", "shared workspace", "handoff", "haptic", "embodied",
        "proximity", "tool passing", "force feedback", "gaze"
    ]
    chat_keywords = [
        "chat", "text", "voice", "non-embodied", "co-author", "document",
        "asynchronous", "message", "turn-taking", "comment"
    ]

    co_hits, co_matched = _contains_keywords(co_text, co_keywords, min_hits=2)
    chat_hits, chat_matched = _contains_keywords(chat_text, chat_keywords, min_hits=2)

    print(f"[INFO] Co-Assembly keyword matches ({co_hits}): {co_matched}")
    print(f"[INFO] Chat keyword matches ({chat_hits}): {chat_matched}")

    assert co_hits >= 2, "Co-Assembly scale draft lacks embodied/coordination cues"
    assert chat_hits >= 2, "Chat scale draft lacks non-embodied/chat modality cues"

    _print_step("[5/5] Comparing Drafts for Distinctness")
    sim = _jaccard_similarity(co_text, chat_text)
    print(f"[INFO] Draft similarity (Jaccard): {sim:.3f}")

    # Heuristic: drafts should not be nearly identical
    assert sim < 0.8, "Drafts are too similar; expected distinct scenario adaptation"

    # Summary output
    print("\n" + "=" * 86)
    print(" " * 26 + "DUAL-SCENARIO VALIDATION SUMMARY")
    print("=" * 86)
    print(f"Co-Assembly Run: {co_run_id}")
    print(f"Chat Run:       {chat_run_id}")
    print(f"Co hits: {co_hits} => {co_matched}")
    print(f"Chat hits: {chat_hits} => {chat_matched}")
    print(f"Draft similarity (Jaccard): {sim:.3f}")
    print("=" * 86)


if __name__ == "__main__":
    # Allow running as a standalone script
    try:
        test_dual_scenarios()
        sys.exit(0)
    except AssertionError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)




