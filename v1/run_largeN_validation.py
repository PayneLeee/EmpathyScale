"""
run_largeN_validation.py — 大规模测试（文献无关）：
复用旧 run 已生成的 117 题 / 4 维条目池 + 同一场景，
在 N=40/组（共 80 名 persona）下重新做双组模拟评估 → EFA→CFA 选题，
验证"更大样本量是否改善 CFA 拟合"（旧 run n=30 时 CFA 全面不达标）。

不依赖脆弱的文献检索阶段（该阶段在本环境多次挂起），直接回答用户的
核心问题：CFA 拟合是否随样本量增大而改善。

产物：data/runs/largeN_<ts>/ 下 evaluation + statistical_selection（含 efa_cfa_results.json）
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 让 agents / utils 可被导入（与 main.py 一致：repo 根 + agents/ + utils/）
ROOT = Path(__file__).resolve().parent
for _p in (ROOT, ROOT / "agents", ROOT / "utils"):
    sys.path.insert(0, str(_p))

from evaluation_agent_group import EvaluationAgentGroup
from item_selection_agent import ItemSelectionAgent
from persona_generation_agent import PersonaGenerationAgent
from prompt_manager import PromptManager
from utils.llm_client import create_llm  # noqa: F401  (确保 client 可用)

OLD_RUN = "2026-10-07_012327"
N_PER_GROUP = 40
NEW_RUN_ID = "largeN_" + datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _load_config():
    cfg = json.load(open(ROOT / "config.json", encoding="utf-8"))
    return cfg


def _extract_items_and_scenario():
    """从旧 run 提取条目池（item_id/item_text/dimension）与场景上下文。"""
    old_run = ROOT / "data" / "runs" / OLD_RUN
    # 条目：来自 combined participant_level_evaluations
    pp = old_run / "evaluation_agent_group" / "selection" / "combined" / "participant_level_evaluations.json"
    data = json.load(open(pp, encoding="utf-8"))
    items_map = {}
    for part in data:
        for rt in part.get("ratings", []):
            iid = int(rt["item_id"])
            if iid not in items_map:
                items_map[iid] = {
                    "item_id": iid,
                    "item_text": rt.get("item_text", ""),
                    "dimension": rt.get("dimension", "Unknown"),
                }
    items = [items_map[k] for k in sorted(items_map)]
    # 场景上下文：复用旧 run 的访谈摘要
    iv = old_run / "interview_agent_group" / "summary.json"
    scenario = json.load(open(iv, encoding="utf-8")) if iv.exists() else {}
    if not isinstance(scenario, dict):
        scenario = {}
    return items, scenario


def main():
    cfg = _load_config()
    api_key = cfg["openai_api_key"]
    model = cfg.get("model_name") or "glm-4-flash"
    pm = PromptManager()

    items, scenario = _extract_items_and_scenario()
    scenario_id = (scenario.get("name") or "").strip() or f"run_{NEW_RUN_ID}"
    print(f"[largeN] 条目池={len(items)} 题 / 场景={scenario_id} / N={N_PER_GROUP}/组")

    run_path = ROOT / "data" / "runs" / NEW_RUN_ID
    (run_path / "evaluation_agent_group" / "selection").mkdir(parents=True, exist_ok=True)

    eval_agent = EvaluationAgentGroup(api_key=api_key, model_name=model, prompts_dir=pm.prompts_dir)
    persona_agent = PersonaGenerationAgent(api_key=api_key, model_name=model, prompts_dir=pm.prompts_dir)

    # 生成 empathic / non_empathic 双组 persona（各 N_PER_GROUP 名）
    print("[largeN] 生成双组 persona ...")
    base = persona_agent.generate_personas(scenario, n_personas=N_PER_GROUP)
    personas_emp = persona_agent.add_interaction_experiences(base.copy(), scenario, interaction_type="empathic")
    personas_nemp = persona_agent.add_interaction_experiences(base.copy(), scenario, interaction_type="non_empathic")
    personas_emp = personas_emp[:N_PER_GROUP]
    personas_nemp = personas_nemp[:N_PER_GROUP]

    # 双组评估
    print("[largeN] empathic 组评估 ...")
    res_e = eval_agent.evaluate_items(NEW_RUN_ID, items, scenario, n_participants=N_PER_GROUP,
                                      scenario_id=scenario_id, phase="selection",
                                      personas=personas_emp,
                                      out_dir=run_path / "evaluation_agent_group" / "selection" / "empathic")
    print("[largeN] non-empathic 组评估 ...")
    res_ne = eval_agent.evaluate_items(NEW_RUN_ID, items, scenario, n_participants=N_PER_GROUP,
                                       scenario_id=scenario_id, phase="selection",
                                       personas=personas_nemp,
                                       out_dir=run_path / "evaluation_agent_group" / "selection" / "non_empathic")

    # 合并双组
    combined_dir = run_path / "evaluation_agent_group" / "selection" / "combined"
    combined_dir.mkdir(parents=True, exist_ok=True)
    e_pp = json.load(open(Path(res_e["summary_path"]).parent / "participant_level_evaluations.json", encoding="utf-8"))
    ne_pp = json.load(open(Path(res_ne["summary_path"]).parent / "participant_level_evaluations.json", encoding="utf-8"))
    combined = e_pp + ne_pp
    (combined_dir / "participant_level_evaluations.json").write_text(
        json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
    combined_summary = eval_agent._summarize(combined, items)
    combined_summary["evaluation_groups"] = {
        "empathic": {"n_participants": len(e_pp)},
        "non_empathic": {"n_participants": len(ne_pp)},
    }
    csp = combined_dir / "evaluation_summary.json"
    csp.write_text(json.dumps(combined_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[largeN] 合并完成：共 {len(combined)} 名 persona × {len(items)} 题")

    # 统计选题（EFA→CFA），复用与流水线完全一致的 select_items
    print("[largeN] EFA→CFA 选题 ...")
    selection_agent = ItemSelectionAgent(api_key=api_key, model_name=model)
    selection_result = selection_agent.select_items(
        items, combined_summary, target_min=10, target_max=20,
        selection_config=None, evaluation_summary_path=str(csp))
    selection_agent.save_selection_results(NEW_RUN_ID, selection_result)
    efa = selection_result.get("efa_cfa_results", {})
    cfa_fit = efa.get("cfa_results", {}).get("fit_indices", {})
    print(f"[largeN] 选题结果：selected={efa.get('selected_items')} factors={efa.get('factor_structure')}")
    print(f"[largeN] CFA 拟合：{json.dumps(cfa_fit, ensure_ascii=False)}")

    # 落盘一份汇总
    summary_out = run_path / "largeN_summary.json"
    summary_out.write_text(json.dumps({
        "run_id": NEW_RUN_ID, "n_per_group": N_PER_GROUP, "n_total": len(combined),
        "n_items": len(items),         "selected_items": efa.get("selected_items"),
        "factor_structure": efa.get("factor_structure"),
        "fit_indices": cfa_fit,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[largeN] DONE -> {summary_out}")


if __name__ == "__main__":
    main()
