"""
verify_run_cfa.py — 对指定 run 用修正后的 CFA 路径复算真实拟合指数

背景：run 2026-10-07_012327 的原始 CFA 因两处 bug（fit_indices 从
model.inspect() 参数估计里读 + semopy 无 SRMR）输出假的 Inf/0；修正后
真实值为 RMSEA≈0.33（n=30 过小）。本工具在任意 run 上重建评分矩阵并
用修正后的 perform_cfa 复算，验证大样本下 CFA 是否改善。

用法：
    venv/Scripts/python.exe tools/verify_run_cfa.py <run_id>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.factor_analysis import perform_cfa  # noqa: E402  (已修正的 CFA)


def build_matrix(run_dir: Path):
    part = json.load(open(
        run_dir / "evaluation_agent_group/selection/combined/participant_level_evaluations.json",
        encoding="utf-8"))
    ratings = {}
    for pi, persona in enumerate(part):
        for rt in persona.get("ratings", []):
            v = rt.get("rating")
            if v is not None:
                ratings[(pi, int(rt["item_id"]))] = float(v)
    df = pd.Series(ratings).unstack()
    df = df[sorted(df.columns)]
    return df


def main():
    run_id = sys.argv[1] if len(sys.argv) > 1 else sorted(
        (ROOT / "data" / "runs").iterdir())[-1].name
    run_dir = ROOT / "data" / "runs" / run_id
    df = build_matrix(run_dir)
    print(f"[cfa] run={run_id}  n_personas={df.shape[0]}  n_items={df.shape[1]}")

    efa = json.load(open(run_dir / "statistical_selection/efa_cfa_results.json",
                         encoding="utf-8"))
    factor = {int(k): int(v) for k, v in efa["factor_structure"].items()}
    n_factors = efa.get("n_factors", 2)

    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = perform_cfa(df.values.astype(float), factor)
    fit = result.get("fit_indices", {})
    sel = result.get("selected_items", [])
    removed = result.get("removed_items", [])

    print(f"[cfa] n={df.shape[0]}  fit indices (真实计算, 迭代后 {len(sel)} 题):")
    for k in ("RMSEA", "TLI", "CFI", "SRMR"):
        print(f"    {k} = {fit.get(k)}")
    thr = {"RMSEA": ("<", 0.08), "TLI": (">", 0.90), "CFI": (">", 0.90), "SRMR": ("<", 0.08)}
    verdict = []
    for k, (op, t) in thr.items():
        v = fit.get(k)
        ok = (v is not None and pd.notna(v) and
              (v < t if op == "<" else v > t))
        verdict.append(f"{k} {'✓' if ok else '✗'}")
    print(f"[cfa] verdict: {' '.join(verdict)}  | removed={removed}")
    print(f"[cfa] 经验参考：CFA 稳健一般需 n≥200 或 ≥10:1 题例比（当前 n={df.shape[0]}）")

    out = run_dir / "statistical_selection" / "cfa_recheck.json"
    json.dump({"run_id": run_id, "n": int(df.shape[0]),
               "fit_indices": {k: (None if fit.get(k) is None or not pd.notna(fit[k])
                                   else float(fit[k])) for k in ("RMSEA", "TLI", "CFI", "SRMR")},
               "selected_items": [int(x) for x in sel],
               "removed_items": [int(x) for x in removed]},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[cfa] saved -> {out}")


if __name__ == "__main__":
    main()
