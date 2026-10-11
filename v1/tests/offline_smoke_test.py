"""
Offline end-to-end smoke test for the multi-agent empathy-scale pipeline.

Purpose: prove main.py's orchestration runs end-to-end with ZERO real API calls.

Strategy:
  1. Replace the LLM with a deterministic FakeChatModel, patched into every agent
     module that imported `create_llm` by name. CVI / Pretest / Evaluation / Persona
     agents then run *for real* against the fake LLM (exercising their real parsers).
  2. Stub the three agents that depend on external tools or langchain executors:
       - InterviewAgentGroup  (builds a langchain AgentExecutor)
       - LiteratureSearchAgentGroup (calls search/PDF APIs)
       - the generation-agent *instance* (complex multi-file writer)
     Each stub emits the same on-disk artifacts the real agents would, so main.py's
     real orchestration code (gates, phases, EFA/CFA, validation) executes unchanged.

This is a WIRING / ORCHESTRATION proof, not a statistical-validity proof.
"""

import os
import re
import sys
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # tests/.. -> repo root
for _p in (str(ROOT), str(ROOT / "agents"), str(ROOT / "utils")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# 1. Fake LLM
# ---------------------------------------------------------------------------
class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChatModel:
    def __init__(self, *args, **kwargs):
        self.model_name = kwargs.get("model_name", "fake")
        self.temperature = kwargs.get("temperature", 0.7)
        self._counter = 0  # increments per LLM call -> distinct ratings per participant

    def invoke(self, prompt, *args, **kwargs):
        self._counter += 1
        return FakeMessage(self._dispatch(prompt))

    def _dispatch(self, prompt):
        if not isinstance(prompt, str):
            prompt = str(prompt)
        p = prompt.lower()
        # CVI expert rating: output example in the template contains "score"/"comment"
        if '"score"' in p or '"comment"' in p:
            return '{"score": 4, "comment": "Highly relevant to the dimension."}'
        # Pretest ambiguity check
        if "has_ambiguity" in p or "ambiguity" in p:
            return ('{"has_ambiguity": false, "reason": "wording is clear", '
                    '"suggested_revision": "", '
                    '"simulated_understanding": "I would understand this as describing the robot behavior."}')
        # Evaluation ratings (default)
        return self._eval_ratings(prompt)

    def _eval_ratings(self, prompt):
        p = prompt.lower()
        non_emph = ("non_empathic" in p) or ("purely functional" in p) or ("fixed pace" in p)
        # parse per-item dimensions from the items_list embedded in the prompt
        dims = re.findall(r"^\s*\d+\.\s*\[([^\]]+)\]", prompt, re.MULTILINE)
        # Per-call seed -> each simulated participant gets a distinct rating vector.
        rng = random.Random(12345 + self._counter)
        # Latent-factor model so EFA/CFA have recoverable structure:
        #   rating = mu + common_method + dim_latent[dim] + noise
        # within-dim items share dim_latent (corr ~0.75, under the 0.8 inter-cap);
        # between-dim items share only weak common method variance (corr ~0.06).
        mu = 66 if not non_emph else 46
        common = rng.gauss(0, 3.0)            # small common-method variance
        dim_to_idx = {}
        for d in dims:
            if d not in dim_to_idx:
                dim_to_idx[d] = len(dim_to_idx)
        dim_lat = [rng.gauss(0, 10.0) for _ in range(max(1, len(dim_to_idx)))]
        ratings = []
        for d in dims:
            di = dim_to_idx[d]
            val = mu + common + dim_lat[di] + rng.gauss(0, 6.0)
            val = max(1, min(100, round(val)))
            ratings.append(int(val))
        # safety padding so the parser can truncate to the expected item count
        while len(ratings) < 40:
            ratings.append(int(max(1, min(100, round(mu + rng.gauss(0, 12.0))))))
        return json.dumps({"ratings": ratings, "summary": "Simulated smoke-test ratings."})


def fake_create_llm(*args, **kwargs):
    return FakeChatModel(*args, **kwargs)


# ---------------------------------------------------------------------------
# 2. Patch every agent module's `create_llm` reference (they imported by name)
# ---------------------------------------------------------------------------
import utils.llm_client as llm_client_mod
llm_client_mod.create_llm = fake_create_llm

import agents.content_validity_agent as cvi_mod
import agents.pretest_agent as pretest_mod
import agents.persona_generation_agent as persona_mod
import agents.evaluation_agent_group as eval_mod
cvi_mod.create_llm = fake_create_llm
pretest_mod.create_llm = fake_create_llm
persona_mod.create_llm = fake_create_llm
eval_mod.create_llm = fake_create_llm


# ---------------------------------------------------------------------------
# 3. Stub the three external-dependency agents
# ---------------------------------------------------------------------------
SCENARIO = {
    "name": "smoke_test_robot",
    "assessment_context": "工厂装配协作",
    "robot_platform": "协作机械臂",
    "interaction_modalities": "语音 + 状态显示屏",
    "environmental_setting": "结构化车间",
    "collaboration_pattern": "人机并肩装配",
}
REQUIRED_SLOTS = ["assessment_context", "robot_platform", "interaction_modalities",
                  "environmental_setting", "collaboration_pattern"]


class StubInterview:
    def __init__(self, api_key=None, model_name="fake", prompts_dir=None, **kwargs):
        self.run_id = None

    def set_scenario_run_id(self, run_id):
        self.run_id = run_id

    def start_interview(self):
        return "[STUB] 访谈开始"

    def process_response(self, user_input):
        return "[STUB] 已记录您的回答"

    def is_interview_complete(self):
        return True

    def get_scenario_brief(self):
        return {
            "is_ready": True,
            "readiness_score": 1.0,
            "missing_slots": [],
            **{k: SCENARIO[k] for k in REQUIRED_SLOTS},
            "name": SCENARIO["name"],
        }

    def get_interview_summary(self):
        return {k: SCENARIO[k] for k in (["name"] + REQUIRED_SLOTS)}

    def get_conversation_history(self):
        return []


class StubLiterature:
    def __init__(self, api_key=None, model_name="fake", prompts_dir=None, **kwargs):
        pass

    def search_and_download(self, run_id, interview_summary, scenario_brief=None):
        return {
            "total_papers_found": 5,
            "screened_papers": 5,
            "pdfs_downloaded": 3,
            "high_relevance_papers": [{"title": f"paper {i}"} for i in range(3)],
            "gate_report": {"high_relevance_count": 3, "expansion_trace": []},
            "coverage_report": {"coverage_score": 0.8},
        }


SYNTHETIC_MD = """# Empathy Scale Draft (smoke test)

### Cognitive Empathy
- Item 1: The robot recognizes when I am confused and slows down its explanation.
- Item 2: The robot identifies my emotional state from my tone of voice.
- Item 3: The robot notices when I hesitate and offers clarification proactively.
- Item 4: The robot tracks my understanding level during multi-step instructions.

### Emotional Empathy
- Item 5: The robot expresses understanding when I feel frustrated.
- Item 6: The robot provides encouraging feedback when I am stressed.
- Item 7: The robot acknowledges my concerns before continuing the task.
- Item 8: The robot responds warmly when I am anxious about the procedure.

### Behavioral Empathy
- Item 9: The robot adjusts its pace to match my working tempo.
- Item 10: The robot adapts its behavior when I struggle with a step.
- Item 11: The robot offers help proactively when I seem overwhelmed.
- Item 12: The robot modifies its actions based on my nonverbal cues.
"""


class StubGeneration:
    def __init__(self, api_key=None, num_item_generators=5, enable_content_assessment=True,
                 model_name="fake", prompts_dir=None, **kwargs):
        pass

    def generate_scale(self, run_id):
        from data_manager import DataManager
        dm = DataManager()
        run_path = dm.get_run_path(run_id)
        scale_dir = run_path / "empathy_scale_generation_agent_group"
        scale_dir.mkdir(parents=True, exist_ok=True)
        draft = scale_dir / "scale_draft.md"
        draft.write_text(SYNTHETIC_MD, encoding="utf-8")
        return {
            "scale_draft_path": str(draft),
            "evidence_coverage": {"evidence_coverage_score": 0.9},
            "needs_more_research": False,
            "error": None,
        }


# ---------------------------------------------------------------------------
# 4. Wire stubs into main and shrink the sample size for speed
# ---------------------------------------------------------------------------
import main
main.InterviewAgentGroup = StubInterview
main.LiteratureSearchAgentGroup = StubLiterature
main.SELECTION_N_PER_GROUP = 40   # smaller than default 100 for a fast smoke test


# ---------------------------------------------------------------------------
# 5. Run
# ---------------------------------------------------------------------------
def fake_user(last_agent_message):
    return ("我们有一台协作机械臂，用于工厂装配，通过语音和状态显示屏交互，"
            "在结构化车间里与人类并肩协作。")


def run_smoke_test():
    wf = main.MultiAgentWorkflow()
    wf.agents["scale_generation"] = StubGeneration()
    wf.run_interview_session(user_input_factory=fake_user, max_automated_turns=5)
    run_id = wf.run_id
    run_dir = wf.data_manager.get_run_path(run_id)

    print("\n" + "=" * 70)
    print("OFFLINE SMOKE TEST — ARTIFACT CHECK")
    print("=" * 70)
    checks = []
    root = Path(run_dir)

    def check(label, path):
        ok = Path(path).exists()
        checks.append((label, ok))
        print(f"  [{'OK' if ok else 'MISSING'}] {label}")

    check("interview summary", root / "interview_agent_group" / "summary.json")
    check("scale draft", root / "empathy_scale_generation_agent_group" / "scale_draft.md")
    check("CVI summary", root / "content_validity_agent" / "content_validity_summary.json")
    check("CVI report", root / "content_validity_agent" / "content_validity_report.txt")
    check("pretest result", root / "pretest_agent" / "pretest_result.json")
    check("pretest report", root / "pretest_agent" / "pretest_report.txt")
    check("Phase1 empathic eval", root / "evaluation_agent_group" / "selection" / "empathic" / "evaluation_summary.json")
    check("Phase1 non-empathic eval", root / "evaluation_agent_group" / "selection" / "non_empathic" / "evaluation_summary.json")
    check("Phase1 combined", root / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json")
    check("statistical selection", root / "statistical_selection" / "selection_config.json")
    check("filtered draft", root / "empathy_scale_generation_agent_group" / "filtered_scale_draft.md")
    check("Phase2 validation", root / "evaluation_agent_group" / "validation" / "evaluation_summary.json")
    check("run README", root / "README.md")

    n_ok = sum(1 for _, ok in checks if ok)
    print(f"\nSUMMARY: {n_ok}/{len(checks)} artifact checks present. run_id={run_id}")

    cvi_path = root / "content_validity_agent" / "content_validity_summary.json"
    if cvi_path.exists():
        cvi = json.loads(cvi_path.read_text(encoding="utf-8"))
        print(f"  S-CVI = {cvi.get('scale_cvi')}, kept = {len(cvi.get('items_kept', []))}, "
              f"removed = {len(cvi.get('items_removed', []))}")

    if (root / "statistical_selection" / "selection_config.json").exists():
        print("  EFA/CFA selection: produced a filtered scale.")
    else:
        print("  EFA/CFA selection: not produced (CFA may not have converged on synthetic "
              "data — pipeline still ran end-to-end).")

    return n_ok, len(checks), run_id


if __name__ == "__main__":
    run_smoke_test()
