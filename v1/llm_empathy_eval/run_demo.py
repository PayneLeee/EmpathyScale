"""
run_demo.py — LLM 共情评估流水线 demo 入口

用法（在 llm_empathy_eval/venv 环境下）：
    venv/Scripts/python.exe run_demo.py --model stub  --iters 2 --k 2
    venv/Scripts/python.exe run_demo.py --model qwen --iters 2 --k 2

流程：
    共情量表（复用 EmpathyScale 已验证的 18 题）
      → 被评模型（本地超小模型）按 system prompt 生成回应
      → GLM 评审按量表逐题打分 → reward
      → 激励回路：变异 system prompt → 再评 → 爬山保留
"""
from __future__ import annotations

import argparse
from pathlib import Path

from scale_adapter import load_scale
from judge import GLMJudge
from subject_model import make_subject
from incentive_loop import PromptIncentiveLoop

SCENARIOS = [
    "我今天去医院复查，医生说我的腿恢复得不太好，可能还要再动一次手术……唉。",
    "老伴走了以后，家里就剩我一个人，下午的时候特别安静，心里空落落的。",
    "儿子工作忙，已经三个星期没回来看我了。我知道他忙，可我还是很想他。",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["stub", "qwen", "llamacpp", "glm"], default="stub")
    ap.add_argument("--iters", type=int, default=2)
    ap.add_argument("--k", type=int, default=2, help="每轮 prompt 变异数")
    ap.add_argument("--run-id", default="2026-10-07_012327")
    args = ap.parse_args()

    scale = load_scale(args.run_id)
    print(f"[demo] 量表加载：{len(scale)} 题 / "
          f"{len({s['factor'] for s in scale})} 因子（run {args.run_id}）")

    subject = make_subject(args.model)
    judge = GLMJudge()
    out_dir = Path(__file__).resolve().parent / "results" / args.model

    loop = PromptIncentiveLoop(judge, scale, SCENARIOS, subject,
                               out_dir, iters=args.iters, k_mutants=args.k)
    best = loop.run()
    print(f"\n[demo] 最优 reward = {best['reward']}（{best['tag']}）")
    print(f"[demo] 轨迹落盘 -> {out_dir}")


if __name__ == "__main__":
    main()
