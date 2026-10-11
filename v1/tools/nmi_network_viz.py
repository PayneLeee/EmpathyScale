"""
nmi_network_viz.py — 题项网络社区结构可视化（NMI before/after）

对照论文中的 Big-Five NMI 网络图：把量表题项作为节点、题项间 Pearson 相关
（跨 persona 评分）作为边，做社区检测，然后计算社区划分与"参考结构"的
NMI（归一化互信息）：
  - Before：全部候选题项，参考结构 = 生成阶段的原始维度标签
  - After ：统计筛选后的题项，参考结构 = EFA 因子归属

用法：
    venv/Scripts/python.exe tools/nmi_network_viz.py [run_id]
默认使用最新的 run。输出 PNG 写到 data/runs/<run_id>/viz/nmi_item_network.png
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from sklearn.metrics import normalized_mutual_info_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 颜色盘（参考图风格：red / blue / green / orange / yellow / purple）
PALETTE = ["#E4574C", "#6FB3E0", "#A8C97F", "#F2A45C", "#F5D763", "#B07FD8",
           "#7FCDBB", "#F28E9B"]


def load_run(run_id: str):
    run_dir = PROJECT_ROOT / "data" / "runs" / run_id
    part = json.load(open(
        run_dir / "evaluation_agent_group/selection/combined/participant_level_evaluations.json",
        encoding="utf-8"))
    ratings = {}          # {(persona_idx, item_id): rating}
    dims = {}             # item_id -> original dimension label
    texts = {}            # item_id -> item text
    for pi, persona in enumerate(part):
        for rt in persona.get("ratings", []):
            iid = int(rt["item_id"])
            v = rt.get("rating")
            if v is not None:
                ratings[(pi, iid)] = float(v)
            dims.setdefault(iid, rt.get("dimension", "Unknown"))
            texts.setdefault(iid, rt.get("item_text", ""))
    df = pd.Series(ratings).unstack()  # rows=persona, cols=item_id
    df = df[sorted(df.columns)]
    return df, dims, texts, run_dir


def community_labels(G: nx.Graph, nodes: list) -> list:
    """Greedy modularity communities -> label per node (order follows `nodes`)."""
    comms = greedy_modularity_communities(G, weight="weight")
    lab = {}
    for ci, c in enumerate(comms):
        for n in c:
            lab[n] = ci
    # 孤立节点自成一区
    out = []
    nxt = max(lab.values(), default=-1) + 1
    for n in nodes:
        if n not in lab:
            lab[n] = nxt
            nxt += 1
        out.append(lab[n])
    return out


def build_graph(corr: pd.DataFrame, nodes: list, thr: float = 0.0,
                top_k: int = 3) -> nx.Graph:
    """每节点仅保留最强的 top_k 条 |r| 边（稀疏化，接近参考图观感）。"""
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for i, a in enumerate(nodes):
        vals = []
        for b in nodes:
            if b == a:
                continue
            r = corr.loc[a, b]
            if pd.notna(r) and abs(r) >= thr:
                vals.append((abs(float(r)), b))
        vals.sort(reverse=True)
        for w, b in vals[:top_k]:
            if not G.has_edge(a, b) or G[a][b]["weight"] < w:
                G.add_edge(a, b, weight=w)
    return G


def draw_panel(ax, G, nodes, node_labels, title, seed=7):
    pos = nx.spring_layout(G, k=0.45, seed=seed, weight="weight")
    k = len(set(node_labels))
    colors = [PALETTE[l % len(PALETTE)] for l in node_labels]
    edge_colors = ["#3E9B4F" if G.nodes[u]["_c"] == G.nodes[v]["_c"] else "#BBBBBB"
                   for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors,
                           width=[1.6 * G[u][v]["weight"] for u, v in G.edges()],
                           alpha=0.55)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors,
                           node_size=330, edgecolors="white", linewidths=1.2)
    nx.draw_networkx_labels(G, pos, labels={n: str(n) for n in nodes},
                            font_size=5.5, ax=ax)
    ax.set_title(title, fontsize=11)
    ax.axis("off")
    handles = [Line2D([0], [0], marker="o", linestyle="", markersize=9,
                      markerfacecolor=PALETTE[i % len(PALETTE)], markeredgecolor="white",
                      label=f"cluster {i + 1}") for i in range(k)]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.0, 0.5),
              fontsize=8, frameon=False)


def main():
    run_id = sys.argv[1] if len(sys.argv) > 1 else sorted(
        (PROJECT_ROOT / "data" / "runs").iterdir())[-1].name
    df, dims, texts, run_dir = load_run(run_id)
    print(f"[viz] run={run_id}  matrix={df.shape}")

    corr = df.corr(min_periods=8)
    efa = json.load(open(run_dir / "statistical_selection/efa_cfa_results.json",
                         encoding="utf-8"))
    factor = {int(k): int(v) for k, v in efa["factor_structure"].items()}
    selected = [int(x) for x in efa["selected_items"]]
    print(f"[viz] selected={len(selected)} items, factors={sorted(set(factor.values()))}")

    # ---- Before：全部题项 ----
    nodes_b = list(df.columns)
    G_b = build_graph(corr, nodes_b, thr=0.30, top_k=3)
    for n in G_b.nodes:
        G_b.nodes[n]["_c"] = 0  # placeholder（边着色在 before 用不到，统一灰）
    comm_b = community_labels(G_b, nodes_b)
    for n, c in zip(nodes_b, comm_b):
        G_b.nodes[n]["_c"] = c
    ref_b = [dims[n] for n in nodes_b]
    nmi_b = normalized_mutual_info_score(ref_b, comm_b)

    # ---- After：入选题项，参考结构 = EFA 因子 ----
    nodes_a = [n for n in selected if n in df.columns]
    corr_a = corr.loc[nodes_a, nodes_a]
    G_a = build_graph(corr_a, nodes_a, thr=0.30, top_k=3)
    comm_a = community_labels(G_a, nodes_a)
    for n, c in zip(nodes_a, comm_a):
        G_a.nodes[n]["_c"] = c
    ref_a = [factor.get(n, -1) for n in nodes_a]
    nmi_a = normalized_mutual_info_score(ref_a, comm_a)

    print(f"[viz] NMI before = {nmi_b:.2f}  (vs 原始维度标签, {len(set(ref_b))} 维)")
    print(f"[viz] NMI after  = {nmi_a:.2f}  (vs EFA 因子, {len(set(ref_a))} 因子)")

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.4), facecolor="white")
    draw_panel(axes[0], G_b, nodes_b, comm_b,
               f"Before  (NMI: {nmi_b * 100:.2f})\n{len(nodes_b)} items · edges={G_b.number_of_edges()}")
    draw_panel(axes[1], G_a, nodes_a, comm_a,
               f"After  (NMI: {nmi_a * 100:.2f})\n{len(nodes_a)} selected items · edges={G_a.number_of_edges()}")
    fig.suptitle(f"Item network community structure — run {run_id}\n"
                 f"(edges = top-3 strongest |Pearson r| per item across simulated respondents; "
                 f"reference = original dimensions before / EFA factors after)",
                 fontsize=11, y=0.99)
    out_dir = run_dir / "viz"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "nmi_item_network.png"
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    print(f"[viz] saved -> {out}")


if __name__ == "__main__":
    main()
