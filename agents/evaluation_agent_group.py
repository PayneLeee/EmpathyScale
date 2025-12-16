"""
Evaluation Agent Group: LLM-simulated participant pretest (PETS-style).
Rates items on clarity, relevance, scenario_sensitivity (1-5) with brief reasons.
"""

import json
import re
import statistics
from pathlib import Path
from typing import Dict, List, Any

from langchain_openai import ChatOpenAI
from openai import APIConnectionError

from utils.prompt_manager import PromptManager
from agents.scale_generation_agents import retry_llm_call

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class EvaluationAgentGroup:
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", prompts_dir: str = None):
        self.llm = ChatOpenAI(api_key=api_key, model_name=model_name, temperature=0.7)
        self.prompt_manager = PromptManager(prompts_dir)

    # ---------- Public API ----------
    def evaluate_items(self, run_id: str, items: List[Dict[str, str]], scenario_context: Dict[str, Any],
                       n_participants: int = 25, out_dir: Path = None) -> Dict[str, Any]:
        if out_dir is None:
            out_dir = PROJECT_ROOT / f"data/runs/{run_id}/evaluation_agent_group"
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"      Evaluating {len(items)} items with {n_participants} simulated participants...")
        all_evals = []
        for idx, item in enumerate(items, 1):
            item_text_short = item.get("item_text", "")[:50] + "..." if len(item.get("item_text", "")) > 50 else item.get("item_text", "")
            print(f"      [{idx}/{len(items)}] Evaluating item: {item_text_short}")
            evals = []
            for pid in range(1, n_participants + 1):
                evals.append(self._simulate_one(item, scenario_context, pid))
                if pid % 5 == 0 or pid == n_participants:
                    print(f"        Participant {pid}/{n_participants} completed", end="\r")
            print()  # New line after progress
            all_evals.append({"item": item, "evaluations": evals})

        print("      [Summarizing] Computing statistics...")
        summary = self._summarize(all_evals)

        with open(out_dir / "item_level_evaluations.json", "w", encoding="utf-8") as f:
            json.dump(all_evals, f, indent=2, ensure_ascii=False)
        with open(out_dir / "evaluation_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return {
            "status": "completed",
            "n_items": len(items),
            "n_participants": n_participants,
            "summary": summary,
            "summary_path": str(out_dir / "evaluation_summary.json"),
        }

    def evaluate_baseline_txt(self, run_id: str, txt_path: Path, scenario_context: Dict[str, Any],
                              n_participants: int = 25, label: str = "baseline") -> Dict[str, Any]:
        print(f"      [Baseline] Loading {label} items from {txt_path.name}...")
        items = self._items_from_plain_text(txt_path)
        print(f"      [Baseline] Found {len(items)} items for {label}")
        out_dir = PROJECT_ROOT / f"data/runs/{run_id}/evaluation_agent_group/baselines/{label}"
        return self.evaluate_items(run_id, items, scenario_context, n_participants, out_dir)

    # ---------- Helpers ----------
    def _simulate_one(self, item: Dict[str, str], scenario_context: Dict[str, Any], participant_id: int) -> Dict[str, Any]:
        prompt_template = self.prompt_manager.get_agent_group_prompt("evaluation_agent_group", "participant_evaluation_prompt")
        prompt = prompt_template.format(
            assessment_context=scenario_context.get("assessment_context", ""),
            robot_platform=scenario_context.get("robot_platform", ""),
            interaction_modalities=scenario_context.get("interaction_modalities", ""),
            collaboration_pattern=scenario_context.get("collaboration_pattern", ""),
            environmental_setting=scenario_context.get("environmental_setting", ""),
            dimension=item.get("dimension", "Unknown"),
            item_text=item.get("item_text", ""),
        )
        try:
            resp = retry_llm_call(lambda: self.llm.invoke(prompt).content.strip())
            data = self._parse_json_like(resp)
            data["participant_id"] = participant_id
            data["raw"] = resp[:200]
            return data
        except Exception as e:
            return {
                "participant_id": participant_id,
                "clarity": None,
                "relevance": None,
                "scenario_sensitivity": None,
                "reason": f"error: {e}",
            }

    def _parse_json_like(self, text: str) -> Dict[str, Any]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        # fallback heuristic
        def grab(key):
            m = re.search(rf"{key}[^0-9]*([1-5])", text, re.IGNORECASE)
            return int(m.group(1)) if m else None
        return {
            "clarity": grab("clarity"),
            "relevance": grab("relevance"),
            "scenario_sensitivity": grab("scenario"),
            "reason": text[:200],
        }

    def _summarize(self, all_evals: List[Dict[str, Any]]) -> Dict[str, Any]:
        item_stats = []
        for row in all_evals:
            ratings = {"clarity": [], "relevance": [], "scenario_sensitivity": []}
            for ev in row["evaluations"]:
                for k in ratings:
                    if isinstance(ev.get(k), (int, float)):
                        ratings[k].append(float(ev[k]))

            def stats(vals):
                if not vals:
                    return {"mean": None, "std": None, "min": None, "max": None, "n": 0}
                return {
                    "mean": round(statistics.mean(vals), 2),
                    "std": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
                    "min": min(vals),
                    "max": max(vals),
                    "n": len(vals),
                }

            c_stats = stats(ratings["clarity"])
            r_stats = stats(ratings["relevance"])
            s_stats = stats(ratings["scenario_sensitivity"])
            overall_mean = None
            if all(v["mean"] is not None for v in [c_stats, r_stats, s_stats]):
                overall_mean = round((c_stats["mean"] + r_stats["mean"] + s_stats["mean"]) / 3, 2)

            item_stats.append({
                "dimension": row["item"].get("dimension"),
                "item_text": row["item"].get("item_text"),
                "clarity": c_stats,
                "relevance": r_stats,
                "scenario_sensitivity": s_stats,
                "overall_mean": overall_mean,
            })

        low_items = [
            it for it in item_stats
            if any(
                (it[m]["mean"] is not None and it[m]["mean"] < 3.5)
                for m in ["clarity", "relevance", "scenario_sensitivity"]
            )
        ]

        return {
            "n_items": len(item_stats),
            "item_statistics": item_stats,
            "low_performing_items": low_items,
            "threshold": 3.5,
        }

    def _items_from_plain_text(self, txt_path: Path) -> List[Dict[str, str]]:
        if not txt_path.exists():
            return []
        text = txt_path.read_text(encoding="utf-8", errors="replace")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        items = []
        for ln in lines:
            # naive: treat every non-empty line as potential item
            if len(ln) > 3:
                items.append({"dimension": "Baseline", "item_text": ln})
        return items

