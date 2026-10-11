"""
Offline test for the REAL EmpathyScaleGenerationAgentGroup (no stubs).

The main pipeline smoke test replaces the generation agent with a stub, so its
internal orchestration (construct -> item pool -> content assessment -> evidence
coverage -> markdown assembly + file writes) is never actually executed. This test
drives the REAL agent group with a FakeChatModel that returns valid JSON for each of
the three sub-agents, verifying the agent's own code path end-to-end without any API.

Dispatch heuristic (based on the composed prompt the real agent builds):
  - prompt contains "Candidates:"   -> ContentAssessmentAgent.refine  -> list of item blocks
  - prompt contains "Dimensions:"   -> ItemGenerationAgent.generate_items -> list of item blocks
  - otherwise                       -> ConstructDefinitionAgent.define_constructs -> {"dimensions": [...]}
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "agents"))
sys.path.insert(0, str(REPO / "utils"))

# Use the SAME flat-import convention as main.py (agents/ is on sys.path), so that
# the module objects we patch ARE the ones the real code uses at call time.
from empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
import empathy_scale_generation_agent_group as gen_mod
import scale_generation_agents as sga_mod


class _Resp:
    def __init__(self, content):
        self.content = content


class FakeChatModel:
    """Returns canned valid JSON depending on which sub-agent is calling."""

    DIMS = [
        {"name": "Cognitive Empathy", "description": "The robot understands the user's task state and intent."},
        {"name": "Emotional Empathy", "description": "The robot recognizes and responds to the user's emotional state."},
        {"name": "Behavioral Empathy", "description": "The robot adapts its actions to support the user."},
    ]

    ITEM_BLOCKS = [
        {"dimension": "Cognitive Empathy",
         "items": ["The robot identifies my emotional state from my tone of voice.",
                   "The robot notices when I hesitate and offers clarification proactively.",
                   "The robot tracks my understanding level during multi-step instructions."]},
        {"dimension": "Emotional Empathy",
         "items": ["The robot provides encouraging feedback when I am stressed.",
                   "The robot acknowledges my concerns before continuing the task.",
                   "The robot responds warmly when I am anxious about the procedure."]},
        {"dimension": "Behavioral Empathy",
         "items": ["The robot adjusts its pace to match my working tempo.",
                   "The robot adapts its behavior when I struggle with a step.",
                   "The robot offers help proactively when I seem overwhelmed."]},
    ]

    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt, *args, **kwargs):
        if isinstance(prompt, list):
            prompt = "\n".join(getattr(m, "content", str(m)) for m in prompt)
        text = prompt if isinstance(prompt, str) else str(prompt)
        if "Candidates:" in text:
            return _Resp(json.dumps(self.ITEM_BLOCKS, ensure_ascii=False))
        if "Dimensions:" in text:
            return _Resp(json.dumps(self.ITEM_BLOCKS, ensure_ascii=False))
        return _Resp(json.dumps({"dimensions": self.DIMS}, ensure_ascii=False))


def _write_summaries(run_dir: Path):
    (run_dir / "interview_agent_group").mkdir(parents=True, exist_ok=True)
    (run_dir / "literature_search_agent_group").mkdir(parents=True, exist_ok=True)

    interview = {
        "assessment_context": "Collaborative assembly between a human worker and a robotic arm in a smart factory.",
        "robot_platform": "Collaborative robotic arm",
        "interaction_modalities": ["voice", "gesture", "screen"],
        "collaboration_pattern": "joint task execution",
        "environmental_setting": "factory floor",
        "assessment_goals": ["measure perceived empathy"],
        "expected_empathy_forms": ["cognitive", "emotional", "behavioral"],
    }
    (run_dir / "interview_agent_group" / "summary.json").write_text(
        json.dumps(interview, ensure_ascii=False, indent=2), encoding="utf-8")

    papers = [
        {"title": "Cognitive empathy in human-robot collaboration", "abstract": "..."},
        {"title": "Emotional empathy signals for assistive robots", "abstract": "..."},
        {"title": "Behavioral adaptation in cobot assistance", "abstract": "..."},
    ]
    for p in papers:
        p["scenario_relevance_score"] = 5
    (run_dir / "literature_search_agent_group" / "summary.json").write_text(
        json.dumps({"relevance_scored_papers": papers, "high_relevance_papers": papers},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "literature_search_agent_group" / "relevance_scored_papers.json").write_text(
        json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    # Patch create_llm in BOTH modules that import it at top level.
    gen_mod.create_llm = FakeChatModel
    sga_mod.create_llm = FakeChatModel

    run_root = REPO / "data" / "runs"
    run_root.mkdir(parents=True, exist_ok=True)
    run_id = "gen_offline_test"
    run_dir = run_root / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_summaries(run_dir)

    group = EmpathyScaleGenerationAgentGroup(api_key="offline", model_name="offline",
                                              num_item_generators=2)
    result = group.generate_scale(run_id)

    draft = run_dir / "empathy_scale_generation_agent_group" / "scale_draft.md"
    summary = run_dir / "empathy_scale_generation_agent_group" / "summary.json"

    checks = []
    checks.append(("draft exists", draft.exists()))
    checks.append(("summary exists", summary.exists()))

    items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(
        draft.read_text(encoding="utf-8")) if draft.exists() else []
    checks.append(("draft has >=6 items", len(items) >= 6))
    checks.append(("evidence_coverage computed",
                   bool(result.get("evidence_coverage"))))
    cov = result.get("evidence_coverage", {}).get("evidence_coverage_score")
    checks.append(("evidence_coverage_score > 0", (cov or 0) > 0))

    print("=" * 60)
    print("OFFLINE GENERATION AGENT TEST")
    print("=" * 60)
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    n_fail = sum(1 for _, ok in checks if not ok)
    print(f"\nn_items={len(items)} evidence_coverage_score={cov}")
    print("RESULT:", "PASS" if n_fail == 0 else f"FAIL ({n_fail})")

    # Clean up the test run so it doesn't pollute data/runs.
    try:
        shutil.rmtree(run_dir)
    except Exception:
        pass
    return n_fail == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
