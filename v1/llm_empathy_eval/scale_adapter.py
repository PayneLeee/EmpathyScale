"""
scale_adapter.py — 从 EmpathyScale 的 run 产物加载已验证的共情量表

读取 data/runs/<run_id> 的 selection 评分产物 + EFA 因子结构，
输出统一格式的量表：[{item_id, text, dimension, factor}]
"""
from __future__ import annotations

import json
from pathlib import Path

RUNS = Path(__file__).resolve().parent.parent / "EmpathyScale-main" / "data" / "runs"


def load_scale(run_id: str = "2026-10-07_012327") -> list[dict]:
    run_dir = RUNS / run_id
    part = json.load(open(
        run_dir / "evaluation_agent_group/selection/combined/participant_level_evaluations.json",
        encoding="utf-8"))
    efa = json.load(open(
        run_dir / "statistical_selection/efa_cfa_results.json", encoding="utf-8"))
    factor = {int(k): int(v) for k, v in efa["factor_structure"].items()}
    selected = {int(x) for x in efa["selected_items"]}

    meta: dict[int, dict] = {}
    for p in part:
        for rt in p.get("ratings", []):
            iid = int(rt["item_id"])
            if iid in selected and iid not in meta:
                meta[iid] = {
                    "item_id": iid,
                    "text": rt.get("item_text", ""),
                    "dimension": rt.get("dimension", ""),
                    "factor": factor.get(iid, -1),
                }
    return [meta[i] for i in sorted(meta)]
