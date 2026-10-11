"""
pipeline_efficiency.py — 流水线 token/调用次数/耗时 估算模型

按代码真实的调用粒度建模（对照 agents/ 实现逐一核实）：
  访谈:        ReAct 多轮（每轮 1-2 次 LLM 调用）
  文献:        初筛 N 篇 + 二筛 N 篇 + 摘要抽取 50 篇（各 1 调用/篇）
  生成:        构念 1 + 题项生成(按维度) + 内容评估(每100题1批) + 语义去重
  CVI:         逐题 × n_experts（最大消耗项，192×5=960 次）
  预测试:      1 次全量调用（192 题单批）
  Phase1 评估: 2*n_per_group personas × ceil(n_items/100) 批
  Phase2 验证: 25 personas × ceil(n_final/100) 批
  统计(EFA/CFA/α/d): 0 次（本地计算）

token 估算：输入≈prompt 字节/2.5（中英混合），输出≈0.15×输入
耗时：glm-4-flash 免费档实测 1.5-10 s/调用（限流时取上限），5 并发。

用法：
    venv/Scripts/python.exe tools/pipeline_efficiency.py \
        --n-items 192 --n-final 18 --n-per-group 15 --n-papers 65 --n-experts 5
"""
from __future__ import annotations

import argparse
import math


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-items", type=int, default=192, help="CVI 阶段题项数")
    ap.add_argument("--n-final", type=int, default=18, help="最终入选题项数")
    ap.add_argument("--n-per-group", type=int, default=15)
    ap.add_argument("--n-papers", type=int, default=65)
    ap.add_argument("--n-experts", type=int, default=5)
    ap.add_argument("--interview-turns", type=int, default=12)
    ap.add_argument("--sec-per-call", type=float, default=4.0)
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    S = 2.5          # 混合文本字节→token
    OUT_RATIO = 0.15

    stages = []      # (名称, 调用数, 平均输入token)

    def add(name, calls, avg_in):
        stages.append((name, calls, avg_in))

    add("访谈(ReAct)", args.interview_turns * 2, 2200)
    add("文献·查询生成", 6, 1500)
    add(f"文献·初筛({args.n_papers}篇)", args.n_papers, 500)
    add(f"文献·二筛({args.n_papers}篇)", args.n_papers, 550)
    add("文献·摘要抽取(50篇)", min(50, args.n_papers), 900)
    add("生成·构念界定", 1, 4500)
    add("生成·题项(按维度)", 4, 5000)
    add(f"生成·内容评估({math.ceil(args.n_items/100)}批)", math.ceil(args.n_items / 100), 6500)
    add("生成·语义去重", 2, 6000)
    add(f"CVI({args.n_items}题×{args.n_experts}专家)", args.n_items * args.n_experts, 700)
    add(f"预测试(1次全量)", 1, 9000)
    add(f"Phase1评估({2*args.n_per_group}人×{math.ceil(args.n_items/100)}批)",
        2 * args.n_per_group * math.ceil(args.n_items / 100), 6000)
    add(f"Phase2验证(25人×{math.ceil(args.n_final/100)}批)", 25 * max(1, math.ceil(args.n_final / 100)), 1600)

    total_calls = sum(c for _, c, _ in stages)
    total_tokens = sum(c * i * (1 + OUT_RATIO) for _, c, i in stages)
    seq_time_h = total_calls * args.sec_per_call / 3600
    par_time_h = seq_time_h / args.workers

    print(f"{'阶段':<38}{'调用':>8}{'≈输入tok/次':>12}{'≈总tok':>12}")
    print("-" * 70)
    for name, calls, avg_in in stages:
        print(f"{name:<38}{calls:>8}{avg_in:>12,}{calls*avg_in:>12,}")
    print("-" * 70)
    print(f"合计调用: {total_calls:,}    合计token≈{total_tokens/1e6:.2f} M")
    print(f"串行耗时≈{seq_time_h:.1f} h   5并发≈{par_time_h:.1f} h（{args.sec_per_call}s/调用）")
    print(f"效率: {total_tokens/1e4/args.n_final:.1f} 万token/最终题  |  "
          f"{total_tokens/1e4/args.n_items:.2f} 万token/候选题  |  "
          f"{total_calls/args.n_final:.0f} 调用/最终题")


if __name__ == "__main__":
    main()
