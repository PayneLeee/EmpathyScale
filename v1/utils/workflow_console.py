"""
Terminal reporting aligned with Boateng et al. (2018) nine-step scale development.
Optimised for video recording / fast-forward playback:
  - 任何时候暂停，进度条一眼定位当前步骤
  - 每步只展示：标题 + 一句话做什么 + 一句话总结结果
  - 裁剪所有中间 JSON、文件路径、内部保存提示
"""

import json
import shutil
from typing import Any, List, Optional

WIDTH = 72

# ---------------------------------------------------------------------------
# Step metadata
# ---------------------------------------------------------------------------
BOATENG_STEPS = [
    {
        "step": 1,
        "phase": 1,
        "phase_en": "Item Development",
        "name_cn": "领域识别与项目生成",
        "name_en": "Domain identification & item generation",
        "system_map": "结构化访谈（领域/场景）→ 文献检索与证据整合（支撑题项与构念）",
        "oneliner": "通过访谈收集场景信息，检索文献寻找理论依据",
    },
    {
        "step": 2,
        "phase": 1,
        "phase_en": "Item Development",
        "name_cn": "内容效度评估",
        "name_en": "Content validity",
        "system_map": "构念界定 → 多生成器题项池 → 内容评估与语义去重",
        "oneliner": "根据文献和场景界定概念，生成初始题项并去重",
    },
    {
        "step": 3,
        "phase": 2,
        "phase_en": "Scale Development",
        "name_cn": "预测试（认知访谈类）",
        "name_en": "Pretest / cognitive interview",
        "system_map": "LLM 模拟参与者 + Persona：对题项反应与理解（预测试/认知反应）",
        "oneliner": "用 empathic 组 Persona 模拟被试对全部题项打分",
    },
    {
        "step": 4,
        "phase": 2,
        "phase_en": "Scale Development",
        "name_cn": "调查实施与样本",
        "name_en": "Survey administration & sample",
        "system_map": "同上：批量 Persona 完成整份量表打分（0–100）",
        "oneliner": "用 non-empathic 组 Persona 打分，合并两组数据",
    },
    {
        "step": 5,
        "phase": 2,
        "phase_en": "Scale Development",
        "name_cn": "项目精简",
        "name_en": "Item reduction",
        "system_map": "ItemSelectionAgent：EFA 链上统计删减 → statistical_selection/",
        "in_default_main": True,
        "oneliner": "对合并数据做 EFA 探索性因子分析，删除不合格题项",
    },
    {
        "step": 6,
        "phase": 2,
        "phase_en": "Scale Development",
        "name_cn": "因子提取",
        "name_en": "Factor extraction",
        "system_map": "含于 select_items_by_efa_cfa（与 Step 5–7 同一管线）",
        "in_default_main": True,
        "oneliner": "确定因子数量，提取各因子对应的题项分组",
    },
    {
        "step": 7,
        "phase": 3,
        "phase_en": "Scale Evaluation",
        "name_cn": "维度性检验",
        "name_en": "Dimensionality (CFA)",
        "system_map": "同上管线中的 CFA；定稿后 Phase 2 见 validation/",
        "in_default_main": True,
        "oneliner": "对 EFA 确定的因子结构做 CFA 验证性检验",
    },
    {
        "step": 8,
        "phase": 3,
        "phase_en": "Scale Evaluation",
        "name_cn": "信度检验",
        "name_en": "Reliability",
        "system_map": "评估汇总中的内部一致性等（如 Cronbach's α，视汇总配置）",
        "oneliner": "在独立验证集上检验量表的内部一致性（Cronbach's α）",
    },
    {
        "step": 9,
        "phase": 3,
        "phase_en": "Scale Evaluation",
        "name_cn": "效度检验",
        "name_en": "Validity",
        "system_map": "区分效度等（评估管线支持时写入 evaluation_summary）",
        "oneliner": "在独立验证集上检验区分效度，确认终版量表质量",
    },
]

TOTAL_STEPS = len(BOATENG_STEPS)

_completed_steps: set[int] = set()
_current_step: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _line(char: str = "─") -> str:
    return char * WIDTH


def _terminal_width() -> int:
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return WIDTH


def _step_meta(step: int):
    for s in BOATENG_STEPS:
        if s["step"] == step:
            return s
    return None


# ---------------------------------------------------------------------------
# Progress bar  (the single most important visual for fast-forward)
#
# Example:
#   进度 [1✓] [2✓] [3✓] [4▶] [5·] [6·] [7·] [8·] [9·]  Phase 2 · Scale Development
# ---------------------------------------------------------------------------
def render_progress_bar(current_step: int = 0, highlight_oneline: bool = True) -> None:
    """Print a compact 9-step progress bar."""
    parts = []
    for s in BOATENG_STEPS:
        n = s["step"]
        if n in _completed_steps:
            parts.append(f"[{n}✓]")
        elif n == current_step:
            parts.append(f"[{n}▶]")
        else:
            parts.append(f"[{n}·]")

    bar = " ".join(parts)

    meta = _step_meta(current_step)
    phase_tag = ""
    if meta:
        phase_tag = f"  Phase {meta['phase']} · {meta['phase_en']}"

    tw = _terminal_width()
    full = f"进度 {bar}{phase_tag}"
    if len(full) > tw:
        full = full[:tw]

    print()
    print(full)

    if highlight_oneline and meta:
        print(f"     → {meta['oneliner']}")

    print(flush=True)


# ---------------------------------------------------------------------------
# Step lifecycle
# ---------------------------------------------------------------------------
def step_start(step: int, subtitle: Optional[str] = None) -> None:
    """Announce entering a Boateng step."""
    global _current_step
    _current_step = step

    meta = _step_meta(step)
    if not meta:
        print(f"\n  >>> Step {step} 开始")
        return

    render_progress_bar(step)
    print()
    print(_line("═"))
    print(f" Step {step}/{TOTAL_STEPS}  {meta['name_cn']}")
    print(f" Phase {meta['phase']} — {meta['phase_en']}")
    if subtitle:
        print(f" └─ {subtitle}")
    print(_line("═"))
    print(flush=True)


def step_complete(step: int, summary: Optional[str] = None) -> None:
    """Mark a step as done and update the bar."""
    _completed_steps.add(step)

    meta = _step_meta(step)
    if meta:
        print()
        banner = f"✓ Step {step}/{TOTAL_STEPS} 完成：{meta['name_cn']}"
        if summary:
            banner += f"  · {summary}"
        print(banner)
        print(flush=True)

    render_progress_bar(0, highlight_oneline=False)


# ---------------------------------------------------------------------------
# Sub-step messages (kept to 1-2 per step for video clarity)
# ---------------------------------------------------------------------------
def sub(msg: str, indent: int = 2) -> None:
    pad = " " * indent
    print(f"{pad}▸ {msg}", flush=True)


def sub_done(msg: str, indent: int = 2) -> None:
    pad = " " * indent
    print(f"{pad}✓ {msg}", flush=True)


def minor_separator(label: Optional[str] = None) -> None:
    if label:
        print(f"  --- {label} ---", flush=True)
    else:
        print(f"  {_line('·')}", flush=True)


# ---------------------------------------------------------------------------
# Quality gates — compact, no detail dump
# ---------------------------------------------------------------------------
def gate_ok(title: str, passed: Optional[bool] = None, detail: Optional[str] = None) -> None:
    """One-line quality gate result."""
    status = "通过" if passed else "未达标（管线继续）"
    msg = f"  ▌质量门控: {title}  → {status}"
    if detail:
        msg += f"  ({detail})"
    print()
    print(msg)
    print(flush=True)


# ---------------------------------------------------------------------------
# Top / bottom wrappers
# ---------------------------------------------------------------------------
def print_workflow_title(run_id: Optional[str] = None) -> None:
    print()
    print(_line("═"))
    print(" EmpathyScale 工作流（对齐 Boateng et al., 2018 三阶段 · 九步法）")
    if run_id:
        print(f" Run ID: {run_id}")
    print(_line("═"))
    print()


def print_boateng_roadmap() -> None:
    """Print all 9 steps once at startup so viewers see the full map."""
    print(_line("─"))
    print(" 九步法总览（与 docs/PETS_WORKFLOW_MAPPING.md 一致）")
    print(_line("─"))
    current_phase = None
    for s in BOATENG_STEPS:
        if s["phase"] != current_phase:
            current_phase = s["phase"]
            ptitle = {1: "Phase 1 — Item Development（项目开发）",
                      2: "Phase 2 — Scale Development（量表构建）",
                      3: "Phase 3 — Scale Evaluation（量表评估）"}.get(current_phase, "")
            print(f"\n  {ptitle}")
        oneline = s.get("oneliner", "")
        print(f"    Step {s['step']}: {s['name_cn']}")
        print(f"            → {oneline}")
    print()
    print(_line("─"))
    print()


def skipped_steps_note(steps: List[int]) -> None:
    if not steps:
        return
    rng = ", ".join(str(x) for x in steps)
    print()
    print(_line("─"))
    print(f"  说明: Boateng Step {rng} 在本入口（main.py）未自动执行。")
    print("        完整 EFA/CFA/精简流程见 agents/item_selection_agent.py 与实验脚本。")
    print(_line("─"))
    print(flush=True)


def final_summary(lines: List[str]) -> None:
    # Final progress bar with all steps marked
    for s in BOATENG_STEPS:
        _completed_steps.add(s["step"])
    render_progress_bar(current_step=0, highlight_oneline=False)

    print()
    print(_line("═"))
    print(" 本次运行结束 · 产出摘要")
    print(_line("═"))
    for ln in lines:
        print(f"  {ln}")
    print(_line("═"))
    print(flush=True)


def print_json_panel(title: str, obj: Any, max_chars: Optional[int] = None) -> None:
    """Only use for short, key JSON snippets — avoid large dumps."""
    try:
        text = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except TypeError:
        text = json.dumps(str(obj), ensure_ascii=False, indent=2)
    truncated = False
    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars] + "\n  ... [终端展示已截断；完整内容已写入 run 目录] ..."
        truncated = True
    print()
    print(_line("━"))
    print(f" 【{title}】")
    if truncated:
        print(f" （展示长度已限制）")
    print(_line("━"))
    for line in text.splitlines():
        print(f"  {line}")
    print(_line("━"))
    print(flush=True)


def print_literature_digest(
    research_results: dict,
    *,
    max_high_rel_list: int = 8,
) -> None:
    """Compact literature outcome — only what judges need to see."""
    high = research_results.get("high_relevance_papers") or []
    stats = {
        "检索论文总数": research_results.get("total_papers_found", 0),
        "筛选后论文": research_results.get("screened_papers", 0),
        "下载 PDF": research_results.get("pdfs_downloaded", 0),
        "高相关论文": len(high),
    }
    print_json_panel("文献检索结果", stats, max_chars=4000)


def print_final_items_preview(items: list) -> None:
    """Show the final scale items — the most important output for judges."""
    if not items:
        return
    print()
    print(_line("━"))
    print(f" 【终版量表题项 · {len(items)} 条】")
    print(_line("━"))
    for i, it in enumerate(items, 1):
        dim = it.get("dimension", "?")
        txt = it.get("item_text", "")
        print(f"  {i:2d}. [{dim}] {txt}")
    print(_line("━"))
    print(flush=True)
