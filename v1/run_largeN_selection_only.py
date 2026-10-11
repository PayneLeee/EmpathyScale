"""
run_largeN_selection_only.py — 复用已落盘的 large-N 双组评估数据，只跑 EFA→CFA 选题。

evaluate_items 那一步（80 persona × 117 题，耗时约 3h）已完成并落盘在：
    data/runs/<RUN>/evaluation_agent_group/selection/combined/{participant_level_evaluations.json, evaluation_summary.json}
这里直接读取 combined 的 summary + participant 数据，调用与流水线完全一致的
ItemSelectionAgent.select_items，避免重跑昂贵的 GLM 评分。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for p in (str(ROOT), str(ROOT / "agents"), str(ROOT / "utils")):
    if p not in sys.path:
        sys.path.insert(0, p)

from agents.item_selection_agent import ItemSelectionAgent
from agents.evaluation_agent_group import EvaluationAgentGroup

OLD_RUN = "2026-10-07_012327"
LARGEN_RUN = "largeN_2026-10-08_153234"


def _load_config():
    return json.load(open(ROOT / "config.json", encoding="utf-8"))


def main():
    _cfg = _load_config()
    api_key = _cfg["openai_api_key"]
    model = _cfg.get("model_name", "glm-4-flash")

    run_path = ROOT / "data" / "runs" / LARGEN_RUN
    combined_dir = run_path / "evaluation_agent_group" / "selection" / "combined"
    csp = combined_dir / "evaluation_summary.json"
    ppl_path = combined_dir / "participant_level_evaluations.json"

    combined_summary = json.load(open(csp, encoding="utf-8"))
    combined = json.load(open(ppl_path, encoding="utf-8"))

    # 从旧 run 取条目池（117 题 / 4 维）
    old_eval_dir = ROOT / "data" / "runs" / OLD_RUN / "evaluation_agent_group" / "selection" / "combined"
    old_pp = json.load(open(old_eval_dir / "participant_level_evaluations.json", encoding="utf-8"))
    items = []
    for p in old_pp:
        for r in p.get("ratings", []):
            if "item_id" in r and "item_text" in r:
                items.append({"item_id": r["item_id"], "item_text": r["item_text"],
                              "dimension": r.get("dimension", "")})
    seen = set(); uniq = []
    for it in items:
        if it["item_id"] not in seen:
            seen.add(it["item_id"]); uniq.append(it)
    items = uniq

    print(f"[sel] 读取 large-N 合并数据：{len(combined)} persona × {len(items)} 题")
    # 重新 summarize 以保证 item_statistics 与落盘 participant 数据严格对应
    eval_agent = EvaluationAgentGroup(api_key=api_key, model_name=model)
    combined_summary = eval_agent._summarize(combined, items)
    combined_summary["evaluation_groups"] = {
        "empathic": {"n_participants": len(combined) // 2},
        "non_empathic": {"n_participants": len(combined) // 2},
    }
    csp.write_text(json.dumps(combined_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    sel = ItemSelectionAgent(api_key=api_key, model_name=model)
    result = sel.select_items(items, combined_summary, target_min=10, target_max=20,
                              selection_config=None, evaluation_summary_path=csp)
    sel.save_selection_results(LARGEN_RUN, result)

    efa = result.get("efa_cfa_results", {})
    cfa_fit = efa.get("cfa_results", {}).get("fit_indices", {})
    print(f"[sel] 选题：selected={efa.get('selected_items')} factors={efa.get('factor_structure')}")
    print(f"[sel] CFA 拟合：{json.dumps(cfa_fit, ensure_ascii=False)}")

    out = run_path / "largeN_summary.json"
    out.write_text(json.dumps({
        "run_id": LARGEN_RUN, "n_total": len(combined), "n_items": len(items),
        "selected_items": efa.get("selected_items"),
        "factor_structure": efa.get("factor_structure"),
        "fit_indices": cfa_fit,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[sel] DONE -> {out}")


if __name__ == "__main__":
    main()
