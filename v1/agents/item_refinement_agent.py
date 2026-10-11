"""
ItemRefinementAgent — 自激励回路中的"题项重写"agent

输入：弱题列表 + 逐题心理测量诊断（低载荷/低题总相关）+ 场景 + 维度定义
激励框架（PPT 共享激励段的延伸）：把"提高因子载荷与 α"明确写进目标，
    即 agent 的奖励 = 心理测量指标的改善。
输出：与被替换题项一一对应的新题（JSON 列表），不改变题数。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from utils.llm_client import create_llm
from agents.scale_generation_agents import retry_llm_call
from utils.prompt_manager import PromptManager

SYSTEM_TMPL = (
    "You are the Item Refinement Agent in a self-improving scale-development loop. "
    "Your REWARD is the psychometric quality of the scale: items you write must load "
    "cleanly onto their intended factor (target |loading| >= 0.5), raise Cronbach's alpha "
    "(target >= 0.8), and preserve discriminant validity between empathic and "
    "non-empathic perceptions. Weak items and their diagnostics are provided; rewrite "
    "each weak item so it measures the SAME dimension but with a single, concrete, "
    "non-double-barrelled statement tied to the scenario.\n\n"
    "{incentive}\n\n"
    "Output STRICT JSON: a list of objects "
    '[{{"item_id": <int>, "dimension": "<dim>", "item_text": "<new item>", '
    '"change_note": "<why this should load better>"}}]. No markdown fences.'
)


class ItemRefinementAgent:
    def __init__(self, api_key: str, model_name: str = None, prompts_dir: str = None,
                 temperature: float = 0.6):
        self.llm = create_llm(api_key=api_key, model_name=model_name,
                              temperature=temperature, timeout=240.0)
        self.prompt_manager = PromptManager(prompts_dir)

    def refine_items(self, weak_items: List[Dict[str, Any]],
                     diagnostics: List[Dict[str, Any]],
                     scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """weak_items: [{item_id, item_text, dimension}], diagnostics: 诊断行列表。"""
        inc = self.prompt_manager.get_shared_incentive() or ""
        system = SYSTEM_TMPL.replace("{incentive}", inc)

        diag_by_id = {int(d["item_id"]): d for d in diagnostics
                      if str(d.get("item_id", "")).lstrip("-").isdigit()}
        weak_lines = []
        for it in weak_items:
            iid = int(it["item_id"])
            d = diag_by_id.get(iid, {})
            weak_lines.append(
                f'- item_id={iid} | dimension={it.get("dimension","")}\n'
                f'  text: {it.get("item_text","")}\n'
                f'  diagnostics: loading={d.get("max_loading")}, '
                f'item_total_r={d.get("item_total_r")}, '
                f'alpha_if_deleted={d.get("alpha_if_deleted")}'
            )
        scenario_text = "\n".join(
            f"{k}: {scenario.get(k, '')}" for k in
            ("assessment_context", "robot_platform", "interaction_modalities",
             "collaboration_pattern", "environmental_setting"))
        prompt = (f"Scenario:\n{scenario_text}\n\nWeak items to rewrite "
                  f"({len(weak_items)}):\n" + "\n".join(weak_lines))

        resp = retry_llm_call(lambda: self.llm.invoke(
            f"{system}\n\n{prompt}").content.strip())
        return self._parse(resp, weak_items)

    @staticmethod
    def _parse(resp: str, weak_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        m = re.search(r"\[.*\]", resp, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group())
        except json.JSONDecodeError:
            return []
        valid_ids = {int(it["item_id"]) for it in weak_items}
        out = []
        for row in data:
            try:
                iid = int(row.get("item_id"))
                text = str(row.get("item_text", "")).strip()
                if iid in valid_ids and text:
                    out.append({"item_id": iid,
                                "dimension": row.get("dimension",
                                                     next((w["dimension"] for w in weak_items
                                                           if int(w["item_id"]) == iid), "")),
                                "item_text": text,
                                "change_note": row.get("change_note", "")})
            except (TypeError, ValueError):
                continue
        return out
