"""
Offline test for the REAL LiteratureSearchAgentGroup (no stubs, no network).

Drives the real agent's `search_and_download` end-to-end with:
  - ResearchAPIClient.search_all  -> canned papers (no network)
  - research_api.download_pdf     -> False (papers have no `url`, so no download attempted)
  - create_llm (patched)          -> FakeChatModel returning text each sub-method's parser expects

This exercises the agent's own orchestration + every LLM parser
(generate_queries, _screen_relevance, compute_scenario_relevance_score,
coverage_check, extract_findings, query_expansion_loop) and is the real test of
whether the literature_search_agent_group prompt templates survive `.format(...)`
without crashing on unescaped JSON braces (the same class of bug fixed earlier in
CVI / pretest prompts).
"""

import os
import sys
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "agents"))
sys.path.insert(0, str(REPO / "utils"))

# Flat-import convention (matches main.py) so we patch the SAME module objects.
from literature_search_agent_group import LiteratureSearchAgentGroup
import literature_search_agent_group as lit_mod
import research_api as research_mod


class _Resp:
    def __init__(self, content):
        self.content = content


CANNED_PAPERS = [
    {"title": "Cognitive empathy in human-robot collaboration", "abstract": "A study of cognitive empathy.", "source": "arxiv", "year": 2023},
    {"title": "Emotional empathy signals for assistive robots", "abstract": "Affective signals.", "source": "arxiv", "year": 2022},
    {"title": "Behavioral adaptation in cobot assistance", "abstract": "Adaptive behaviors.", "source": "semantic_scholar", "year": 2024},
    {"title": "Empathy scale design for HRI", "abstract": "Scale construction.", "source": "arxiv", "year": 2021},
    {"title": "Measuring perceived empathy in robots", "abstract": "Measurement methods.", "source": "semantic_scholar", "year": 2023},
]


class FakeChatModel:
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, prompt, *args, **kwargs):
        if isinstance(prompt, list):
            prompt = "\n".join(getattr(m, "content", str(m)) for m in prompt)
        text = prompt if isinstance(prompt, str) else str(prompt)
        return _Resp(self._respond(text))

    def _respond(self, prompt: str) -> str:
        if "SCENARIO_SCORE" in prompt:
            return "SCENARIO_SCORE: 5\nDIMENSIONS: [Cognitive Empathy, Emotional Empathy, Behavioral Empathy]\nREASON: highly relevant to this scenario"
        if "SCORE:" in prompt:
            return "SCORE: 5\nREASON: relevant to robot empathy"
        if "behaviors_identified" in prompt or "empathy_definition" in prompt:
            return json.dumps({
                "empathy_definition": "Empathy is the robot's capacity to understand the user's state.",
                "behaviors_identified": ["verbal acknowledgment", "adaptive pacing"],
                "measurement_methods": "5-point Likert scale",
            }, ensure_ascii=False)
        if "paper_summaries" in prompt or "coverage" in prompt.lower():
            return json.dumps({
                "coverage_score": 1.0, "gaps": [],
                "modality_coverage": True, "user_group_coverage": True,
                "measurement_coverage": True, "context_coverage": True,
            }, ensure_ascii=False)
        # query generation (generate_queries / generate_expansion_queries)
        return "\n".join([
            "1. robot empathy scale construction methods",
            "2. empathic robot behaviors in human-robot interaction",
            "3. measuring perceived empathy in collaborative robots",
            "4. affective computing for assistive robotics",
            "5. human-robot trust and empathy frameworks",
            "6. empathy questionnaire validation HRI",
        ])


def main():
    # Patch the same module-level names the real agent uses.
    lit_mod.create_llm = FakeChatModel
    research_mod.ResearchAPIClient.search_all = staticmethod(
        lambda query, sources=None, max_per_source=5: CANNED_PAPERS)
    research_mod.download_pdf = staticmethod(lambda *a, **k: False)

    interview_summary = {
        "assessment_context": "Collaborative assembly between a human and a robotic arm.",
        "robot_platform": "Collaborative robotic arm",
        "interaction_modalities": ["voice", "gesture"],
        "assessment_goals": ["measure perceived empathy"],
    }
    scenario_brief = {
        "is_ready": True,
        "assessment_context": interview_summary["assessment_context"],
        "robot_platform": interview_summary["robot_platform"],
        "interaction_modalities": interview_summary["interaction_modalities"],
        "collaboration_pattern": "joint task execution",
        "environmental_setting": "factory floor",
        "missing_slots": [],
    }

    agent = LiteratureSearchAgentGroup(api_key="offline", model_name="offline")
    results = agent.search_and_download("lit_offline_test", interview_summary,
                                        scenario_brief=scenario_brief)

    checks = []
    checks.append(("high_relevance_papers >= 3",
                   len(results.get("high_relevance_papers", [])) >= 3))
    checks.append(("relevance_scored_papers present",
                   bool(results.get("relevance_scored_papers"))))
    gate = results.get("gate_report", {})
    checks.append(("gate_passed True", gate.get("gate_passed") is True))
    checks.append(("coverage_report has score",
                   results.get("coverage_report", {}).get("coverage_score") is not None))
    checks.append(("organized_findings present",
                   bool(results.get("organized_findings"))))

    print("=" * 60)
    print("OFFLINE LITERATURE AGENT TEST")
    print("=" * 60)
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    n_fail = sum(1 for _, ok in checks if not ok)
    print(f"\nhigh_rel={len(results.get('high_relevance_papers', []))} "
          f"scored={len(results.get('relevance_scored_papers', []))} "
          f"gate_passed={gate.get('gate_passed')}")
    print("RESULT:", "PASS" if n_fail == 0 else f"FAIL ({n_fail})")
    return n_fail == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
