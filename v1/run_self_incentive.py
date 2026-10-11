"""
run_self_incentive.py — 自激励回路驱动器：以心理测量指标为奖励迭代题项

流程（每轮）：
  1. 诊断：对 run 的 selection 评分矩阵计算 α / 因子载荷 / 题总相关 / 区分效度
     → 组合奖励 reward（0-1，见 utils/psychometric_feedback.scale_reward）
  2. 挑选最弱题项（载荷 < 0.40 优先）
  3. ItemRefinementAgent 以"提高载荷与 α"为奖励目标重写这些题
  4. 从原 run 抽样 n-check 个 persona（两组各半），只对新题重新评分
  5. 在同一 check 子样本上对比 reward（旧题 vs 新题，其余题不变）：
     提升则保留（贪心爬坡），否则回滚；连续两轮无提升即收敛
  6. 报告落盘 data/runs/<run_id>/self_incentive/

局限（如实说明）：新题评分只来自 check 子样本；被保留的新题在报告的
final_matrix 中仅替换了 check persona 的行，其余行保留旧题评分。
用法：
    venv/Scripts/python.exe run_self_incentive.py --run 2026-10-07_012327 \
        --rounds 2 --k 4 --n-check 12
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from utils.llm_client import get_api_key, get_default_model_name  # noqa: E402
from utils.psychometric_feedback import (  # noqa: E402
    diagnose_items, pick_weak_items, scale_reward)
from agents.item_refinement_agent import ItemRefinementAgent  # noqa: E402
from agents.evaluation_agent_group import EvaluationAgentGroup  # noqa: E402

REWARD_KEYS = ("reward", "alpha", "mean_max_loading", "discriminant_d")


def load_selection_matrix(run_dir: Path):
    """返回 (评分矩阵 df, group_flags, personas, items_meta, scenario)。"""
    sel = run_dir / "evaluation_agent_group" / "selection"
    emp = json.load(open(sel / "empathic" / "participant_level_evaluations.json", encoding="utf-8"))
    non = json.load(open(sel / "non_empathic" / "participant_level_evaluations.json", encoding="utf-8"))

    rows, flags, personas = [], [], []
    items_meta = {}
    for label, group in ((True, emp), (False, non)):
        for p in group:
            r = {}
            for rt in p.get("ratings", []):
                iid = int(rt["item_id"])
                r[iid] = rt.get("rating")
                items_meta.setdefault(iid, {"item_id": iid,
                                            "item_text": rt.get("item_text", ""),
                                            "dimension": rt.get("dimension", "Unknown")})
            rows.append(r)
            flags.append(label)
            personas.append(p.get("persona", {}))
    df = pd.DataFrame(rows).sort_index(axis=1)
    scenario = next((p.get("scenario") for p in emp if p.get("scenario")), {})
    return df, flags, personas, items_meta, scenario


def rate_new_items(eval_agent: EvaluationAgentGroup, items: list, scenario: dict,
                   personas: list, max_workers: int = 5) -> pd.DataFrame:
    """对给定 items 用一组 persona 评分 → df(persona × 真实item_id)。

    注意：_simulate_participant_with_persona 返回的 item_id 是**位置序号**
    (item_offset + idx + 1)，并非题项自带 id，必须在此映射回真实题号。
    """
    pos2id = {i + 1: int(it["item_id"]) for i, it in enumerate(items)}
    results = [None] * len(personas)

    def one(idx):
        try:
            r = eval_agent._simulate_participant_with_persona(items, scenario, personas[idx])
            row = {}
            for x in r.get("ratings", []):
                try:
                    pos = int(x["item_id"])
                except (TypeError, ValueError):
                    continue
                if pos in pos2id:
                    row[pos2id[pos]] = x.get("rating")
            results[idx] = row
        except Exception as e:
            print(f"    [WARN] persona {idx} 评分失败：{type(e).__name__}: {e}", flush=True)
            results[idx] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        list(ex.map(one, range(len(personas))))
    return pd.DataFrame(results)


def pack_reward(d: dict) -> dict:
    return {k: (None if pd.isna(d[k]) else round(float(d[k]), 4)) for k in REWARD_KEYS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--k", type=int, default=4, help="每轮重写的弱题数")
    ap.add_argument("--n-check", type=int, default=12, help="每轮重测 persona 数（两组各半）")
    args = ap.parse_args()

    run_dir = ROOT / "data" / "runs" / args.run
    df, flags, personas, items_meta, scenario = load_selection_matrix(run_dir)
    n_emp = sum(flags)
    print(f"[self-incentive] run={args.run}  matrix={df.shape}  "
          f"empathic={n_emp} non={len(flags) - n_emp}")

    api_key = get_api_key()
    model_name = get_default_model_name()
    refiner = ItemRefinementAgent(api_key=api_key, model_name=model_name)
    eval_agent = EvaluationAgentGroup(api_key=api_key, model_name=model_name, max_workers=5)

    n_factors = 2
    history = []
    reward_full = scale_reward(df, flags, n_factors=n_factors)
    print(f"[self-incentive] 全样本基线 reward={reward_full['reward']:.3f}  "
          f"α={reward_full['alpha']:.3f}")

    for rnd in range(1, args.rounds + 1):
        print(f"\n===== Round {rnd}/{args.rounds} =====")
        diag = diagnose_items(df, n_factors=n_factors)
        weak_ids = pick_weak_items(diag, k=args.k)
        if not weak_ids:
            print("  无弱题，回路收敛。")
            break
        print(f"  弱题（本轮重写）：{weak_ids}")

        weak_meta = [items_meta[i] for i in weak_ids if i in items_meta]
        t0 = time.time()
        rewrites = refiner.refine_items(weak_meta, diag.to_dict("records"), scenario)
        print(f"  重写完成：{len(rewrites)}/{len(weak_meta)} 题（{time.time() - t0:.0f}s）")
        if not rewrites:
            print("  [WARN] 重写解析失败，本轮跳过。")
            history.append({"round": rnd, "weak_ids": weak_ids, "rewrites": [],
                            "kept": False, "note": "rewrite parse failed"})
            continue

        # 抽样 check persona（两组各半；df/personas/flags 同序：empathic 在前）
        n_half = max(1, args.n_check // 2)
        sample_idx = ([i for i, f in enumerate(flags) if f][:n_half]
                      + [i for i, f in enumerate(flags) if not f][:n_half])
        flags_check = [flags[i] for i in sample_idx]
        check_personas = [personas[i] for i in sample_idx]

        new_items = [{"item_id": r["item_id"], "item_text": r["item_text"],
                      "dimension": r["dimension"]} for r in rewrites]
        t0 = time.time()
        new_scores = rate_new_items(eval_agent, new_items, scenario,
                                    check_personas, max_workers=5)
        print(f"  重测完成：{new_scores.shape[0]} personas × {new_scores.shape[1]} 新题"
              f"（{time.time() - t0:.0f}s）")

        # 公平对比：同一 check 子样本，其余题不变，仅弱题列 旧 vs 新
        df_check_before = df.iloc[sample_idx].copy()
        df_check_after = df.iloc[sample_idx].copy()
        for j in range(len(sample_idx)):
            for r in rewrites:
                iid = int(r["item_id"])
                if iid in new_scores.columns and j < len(new_scores):
                    v = new_scores.iloc[j][iid]
                    df_check_after.loc[df_check_after.index[j], iid] = v

        # 决策指标：LLM persona 数据上全量 reward 会饱和（α/d 门控恒 1.0），
        # 故用被重写题项的"局部未门控指标"：max|loading| 与题总相关的均值。
        diag_b = diagnose_items(df_check_before, n_factors=n_factors).set_index("item_id")
        diag_a = diagnose_items(df_check_after, n_factors=n_factors).set_index("item_id")

        def local_metric(diag):
            vals = []
            for r in rewrites:
                iid = int(r["item_id"])
                if iid in diag.index:
                    row = diag.loc[iid]
                    l = row["max_loading"] if pd.notna(row["max_loading"]) else 0.0
                    t = row["item_total_r"] if pd.notna(row["item_total_r"]) else 0.0
                    vals.append(0.5 * float(l) + 0.5 * float(t))
            return float(np.mean(vals)) if vals else float("nan")

        metric_b, metric_a = local_metric(diag_b), local_metric(diag_a)
        rb = scale_reward(df_check_before, flags_check, n_factors=n_factors)
        ra = scale_reward(df_check_after, flags_check, n_factors=n_factors)
        kept = (not np.isnan(metric_a) and not np.isnan(metric_b)
                and metric_a > metric_b + 1e-4)
        print(f"  局部指标(重写题 0.5*loading+0.5*item_total_r): "
              f"{metric_b:.4f} -> {metric_a:.4f}  → {'KEEP ✓' if kept else 'ROLLBACK ✗'}")
        print(f"  [参考] 全量 reward(check): {rb['reward']:.3f} -> {ra['reward']:.3f}  "
              f"α: {rb['alpha']:.3f} -> {ra['alpha']:.3f}")

        history.append({
            "round": rnd,
            "weak_ids": weak_ids,
            "rewrites": rewrites,
            "local_metric_before": round(metric_b, 4),
            "local_metric_after": round(metric_a, 4),
            "reward_before": pack_reward(rb),
            "reward_after": pack_reward(ra),
            "kept": bool(kept),
            "n_check_personas": len(check_personas),
        })
        if kept:
            for j, idx in enumerate(sample_idx):
                for r in rewrites:
                    iid = int(r["item_id"])
                    if iid in new_scores.columns and j < len(new_scores):
                        v = new_scores.iloc[j][iid]
                        df.loc[df.index[idx], iid] = v
        elif len(history) >= 2 and not history[-2].get("kept", True):
            print("  连续两轮无提升，提前收敛。")
            break

    # ---- 落盘报告 ----
    out_dir = run_dir / "self_incentive"
    out_dir.mkdir(parents=True, exist_ok=True)
    final_reward = scale_reward(df, flags, n_factors=n_factors)
    kept_rounds = [h for h in history if h.get("kept")]
    report = {
        "run_id": args.run,
        "config": {"rounds_planned": args.rounds, "k": args.k,
                   "n_check": args.n_check, "model": model_name,
                   "n_factors": n_factors},
        "reward_full_initial": pack_reward(reward_full),
        "reward_full_final": pack_reward(final_reward),
        "kept_rounds": len(kept_rounds),
        "rounds": history,
    }
    json.dump(report, open(out_dir / "self_incentive_report.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    df.to_csv(out_dir / "final_items_matrix.csv", encoding="utf-8-sig")

    lines = [f"# 自激励回路报告 — run {args.run}", "",
             f"- 模型：`{model_name}`　实际轮数：{len(history)}　"
             f"保留轮数：{len(kept_rounds)}", "",
             f"- 全样本 reward: {report['reward_full_initial']} → "
             f"{report['reward_full_final']}", ""]
    for h in history:
        lines.append(
            f"## Round {h.get('round')}\n"
            f"- 弱题：{h.get('weak_ids')}\n"
            f"- reward(check): {h.get('reward_before')} → {h.get('reward_after')}\n"
            f"- 结论：**{'保留 ✓' if h.get('kept') else '回滚 ✗'}**\n")
    (out_dir / "self_incentive_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[self-incentive] 报告已落盘 -> {out_dir}")


if __name__ == "__main__":
    main()
