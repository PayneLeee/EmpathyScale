"""
Initialize fixed artifacts and build qualitative_comparison.html.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

PKG_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from run_baseline_comparison import extract_pets_items  # noqa: E402

sys.path.insert(0, str(PKG_ROOT))
from qmc_utils import (  # noqa: E402
    PKG_ROOT,
    PROJECT_ROOT,
    load_json,
    parse_scale_markdown,
    save_json,
    scenario_text_from_interview,
)
from direct_llm_prompt import build_direct_prompt_payload  # noqa: E402
from qmc_translate import (  # noqa: E402
    apply_zh_to_items,
    ensure_bundle_for_texts,
    load_zh_bundle,
    translate_dimension,
    translate_text,
)

STABILITY_QUALITATIVE = [
    "五次直出多为扁平「Items」列表，无稳定维度划分，未经文献检索、模拟评估与统计筛选。",
    "条目数量约 10–15 条/次，随生成波动。",
    "最差样本（run_05）仍含「像人类同事」式整体感受句，难在现场逐项核验。",
]

MECHANISM_ZH = {
    "collision/contact adaptation": "碰撞/接触后的适应",
    "shared workspace coordination": "共享工位协调",
    "implicit coordination through action observation": "通过观察动作的隐性协调",
    "explicit communication and repair": "显式沟通与修复",
    "bodily limitation understanding": "对身体限制的理解",
}

# (pattern, issue, priority) — higher priority wins when multiple match
DIRECT_MISFIT_RULES: List[tuple] = [
    (r"推断|infer", "要求被试「推断」机器人意图，现场难以客观评分。", 90),
    (
        r"人类队友|human teammate|two human teammates|human coworker|像.*同事|coworker would behave",
        "用「像人类同事/队友」的整体感受替代可观察的让行、碰后与口头修复。",
        88,
    ),
    (
        r"feel fluid|feel considerate|indifferent to my presence|cooperative rather than",
        "整体态度/流畅感评价，无法对应「停—让—说明」等行为链。",
        85,
    ),
    (
        r"hinted|without speaking when|does not simply continue",
        "动作含义模糊（暗示、不说话、未继续）— 工人难以一致判断。",
        82,
    ),
    (
        r"showed awareness|seemed aware",
        "要求推断机器人「意识到」协调失误，而非描述可见的暂停/改轨迹/口头说明。",
        80,
    ),
    (
        r"gaze|凝视|视线|personal space during simultaneous",
        "引入个人空间/凝视等场景未强调的构念，偏离短句口语 + 手臂动作。",
        75,
    ),
    (
        r"emotionally intelligent|mental state|sympath|情商|心理状态",
        "情绪/心理特质表述，与本场景协调失败机制无关。",
        70,
    ),
]

PETS_MISFIT_RULES: List[tuple] = [
    (r"mental state|心理状态", "评价「系统」是否考虑心理状态，非工位协作行为。", 90),
    (r"emotionally intelligent|很有情商", "整体「情商」印象，无法区分撞架与顺畅协调。", 88),
    (r"expressed emotions|表达情绪", "情绪表达，与共享料架取放无关。", 86),
    (r"sympathiz|表示同情", "同情/情绪支持，非工厂并肩协调。", 86),
    (r"showed interest|表示兴趣", "社交兴趣，非可观察协调。", 84),
    (r"coping with an emotional|情绪情境", "面向情绪应对情境，非本场景核心。", 84),
    (
        r"understood my (goals|needs|intentions)|理解我的(目标|需求|意图)",
        "抽象「理解」— 撞架与顺畅时都可能同意。",
        82,
    ),
    (r"trusted the system|信任", "抽象信任，不说明协作中发生了什么。", 80),
    (r"^The system", "主语为「系统」，未描述肌肉骨骼机器人在共享料架旁的具体动作。", 50),
]

SCENARIO_ANCHOR_RE = re.compile(
    r"tool|rack|arm|reach|grab|collision|contact|pause|yield|shared|"
    r"你先拿|我来拿|shelf|brush|bump|retract|verbal|spoken|phrase",
    re.IGNORECASE,
)

PETS_GENERIC_ISSUES = [
    "10 条全部以「系统」为主语，无共享工具架、同时伸手、口头让行等场景要素。",
    "ER（6 条）测情绪/心理；UT（4 条）测抽象理解/信任— 均难区分「撞架」与「顺畅协调」。",
    "适合作跨情境基线，不宜作为本装配工位的主测量工具。",
]

NINE_STEP_RUN = "2026-05-11_155408"
INTERVIEW_RUN = "2026-05-11_155408"
_pets_candidates = list((PROJECT_ROOT / "agents/expert_pdfs/txt").glob("*PETS*User.txt"))
PETS_TXT = _pets_candidates[0] if _pets_candidates else PROJECT_ROOT / "agents/expert_pdfs/txt"

# Curated qualitative rows (subjective); direct_llm column filled at build time from worst run
COMPARISON_ROWS: List[Dict[str, str]] = [
    {
        "theme": "共享工位 / 轮流取件",
        "nine_step_good": "When we both reached at the same time, the robot said '你先拿' to let me go first.",
        "contrast_bad": "The system understood my goals.",
        "contrast_source": "PETS-UT",
        "why": "九步骤描述可观察的协作动作；PETS 是抽象目标理解，无法区分「撞架」与「顺畅轮流」。",
    },
    {
        "theme": "口头让行 / 修复",
        "nine_step_good": "The robot's words ('我来拿这个') made its intention obvious.",
        "contrast_bad": "The system sympathized with me.",
        "contrast_source": "PETS-ER",
        "why": "场景里机器人会说「你先拿」；PETS 情绪共情条目与工厂协作机制无关。",
    },
    {
        "theme": "碰撞后恢复",
        "nine_step_good": "I felt the robot communicated effectively when we almost collided.",
        "contrast_bad": "I felt the robot was considerate of my personal space and proximity, similar to how a human coworker would behave.",
        "contrast_source": "单提示直出 (run_05)",
        "why": "九步骤锚定「几乎碰撞」时的沟通修复；直出用「像人类同事」式整体感受替代可观察行为链。",
    },
    {
        "theme": "动作可观察性",
        "nine_step_good": "I could predict when the robot would reach for a tool by watching its arm.",
        "contrast_bad": "The system seemed emotionally intelligent.",
        "contrast_source": "PETS-ER",
        "why": "条目锚定在手臂动作可预测；PETS 评价的是系统「像有情商」的整体印象。",
    },
    {
        "theme": "边界：适度 vs 读心",
        "nine_step_good": "The robot's arm trajectory made it easy to anticipate its next move.",
        "contrast_bad": "Overall, the robot acted as if it understood my physical presence and tried to avoid interfering with my movements.",
        "contrast_source": "单提示直出 (run_02)",
        "why": "九步骤用轨迹/手臂动作表达可预期性；直出要求被试判断机器人「是否理解」在场存在，偏读心式表述。",
    },
    {
        "theme": "信任与协调",
        "nine_step_good": "I appreciated that the robot verbally indicated when it would wait for me.",
        "contrast_bad": "I trusted the system.",
        "contrast_source": "PETS-UT",
        "why": "九步骤把信任建立在言行一致上；PETS 信任条目不说明协作中发生了什么。",
    },
]

SIMILAR_PAIRS: List[Dict[str, Any]] = [
    {
        "title": "理解 vs 协调让行",
        "nine_step": "When we both reached at the same time, the robot said '你先拿' to let me go first.",
        "pets": "The system understood my needs.",
        "direct": "Overall, the robot acted as if it understood my physical presence and tried to avoid interfering with my movements.",
        "note": "同一「体谅」主题：九步骤绑定具体话语与工位动作；直出/PETS 难反映共享料架冲突。",
    },
    {
        "title": "接触后行为",
        "nine_step": "I felt the robot communicated effectively when we almost collided.",
        "pets": "The system considered my mental state.",
        "direct": "I felt the robot was considerate of my personal space and proximity, similar to how a human coworker would behave.",
        "note": "碰撞/接触场景应测行为响应，而非「像同事」式整体感受。",
    },
]

# Subjective display picks (override heuristic ranking for mentor-facing contrast)
SUBJECTIVE_BEST_RUN = "run_02"
SUBJECTIVE_WORST_RUN = "run_05"

EVIDENCE_LINKS = [
    ("访谈摘要", f"data/runs/{INTERVIEW_RUN}/interview_agent_group/summary.json"),
    ("文献检索", f"data/runs/{NINE_STEP_RUN}/literature_search_agent_group/summary.json"),
    ("初始题项", f"data/runs/{NINE_STEP_RUN}/empathy_scale_generation_agent_group/scale_draft.md"),
    ("统计筛选后", f"data/runs/{NINE_STEP_RUN}/empathy_scale_generation_agent_group/filtered_scale_draft.md"),
    ("评估验证", f"data/runs/{NINE_STEP_RUN}/evaluation_agent_group/validation/evaluation_summary.json"),
]


def init_data() -> None:
    data_dir = PKG_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    interview_path = (
        PROJECT_ROOT / "data/runs" / INTERVIEW_RUN / "interview_agent_group/summary.json"
    )
    interview = load_json(interview_path)
    scenario = {
        "source_run": INTERVIEW_RUN,
        "scenario_text": scenario_text_from_interview(interview),
        **{k: interview.get(k) for k in interview if k != "name"},
    }
    save_json(data_dir / "scenario_input.json", scenario)

    filtered_md = (
        PROJECT_ROOT
        / "data/runs"
        / NINE_STEP_RUN
        / "empathy_scale_generation_agent_group/filtered_scale_draft.md"
    )
    md = filtered_md.read_text(encoding="utf-8")
    nine_items = parse_scale_markdown(md)
    save_json(
        data_dir / "nine_step_scale.json",
        {
            "source_run": NINE_STEP_RUN,
            "source_file": str(filtered_md.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "markdown": md,
            "items": nine_items,
        },
    )

    pets_items = extract_pets_items(PETS_TXT)
    save_json(
        data_dir / "pets_items.json",
        {"source": "Schmidmaier et al. 2024 Table 1", "items": pets_items},
    )
    save_json(
        PKG_ROOT / "artifacts_manifest.json",
        {
            "nine_step_run": NINE_STEP_RUN,
            "interview_run": INTERVIEW_RUN,
            "files": {label: path for label, path in EVIDENCE_LINKS},
        },
    )
    print(f"Initialized data/ ({len(nine_items)} nine-step items, {len(pets_items)} PETS items)")


def build_scenario_display(scenario: Dict[str, Any], factors: Dict[str, Any]) -> Dict[str, Any]:
    """Chinese scenario card for report header."""
    mechanisms = [
        MECHANISM_ZH.get(m, m) for m in factors.get("empathy_mechanisms", [])
    ]
    return {
        "title": "当前评价场景设定",
        "source_run": scenario.get("source_run", NINE_STEP_RUN),
        "rows": [
            ("任务情境", "人与肌肉骨骼机器人并肩坐在同一装配工位，共享工具架；人取需判断的精细件，机器人取较重或靠自身的件；时序协调失误会导致同时伸手、挡路或轻微碰撞。"),
            ("机器人平台", "肌肉骨骼机器人（非传统刚性机械臂分区作业）"),
            ("交互方式", "机器人短句口语（如「我来拿这个」「你先拿」）+ 人通过手臂暂停、让路、改轨迹、收回等动作观察意图"),
            ("协作分工", "人负责精细/判断项，机器人负责较重或较近项；靠简短话语与手臂动作线索协调"),
            ("环境", "装配工位，共享工具架"),
            ("期待的共情表现", "；".join([
                "及时表明意图",
                "避让（让路、暂停、收回）",
                "在共享工具架处留出空间",
            ])),
            ("典型失败模式", "；".join([
                "同时伸手拿同一层物料",
                "误以为对方已看到自己的伸手",
                "挡路或擦碰",
                "接触后无暂停、无避让、无解释",
            ])),
            ("与传统机械臂对比", "刚性臂常有清晰工位边界；本场景机器人与人共享同一取放空间，轨迹与上身距离更接近人际并肩协作。"),
        ],
        "mechanisms": mechanisms,
        "risk_flags": ["存在肢体接触/碰撞风险（physical_contact_risk=true）"],
    }


def collect_misfit_examples(
    items: List[Dict[str, str]],
    label_prefix: str,
    rules: List[tuple],
    *,
    pets_scale: bool = False,
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for it in items:
        text = it.get("item_text_en") or it.get("item_text", "")
        issue, pri = _classify_item_with_priority(text, rules, pets_scale=pets_scale)
        if not issue:
            continue
        dim = it.get("dimension", "—")
        out.append({
            "source": label_prefix,
            "label": f"{label_prefix}·{dim}" if dim != "—" else label_prefix,
            "item_text_en": text,
            "item_text": text,
            "issue": issue,
            "priority": pri,
        })
    return out


def _classify_item_with_priority(
    text: str, rules: List[tuple], *, pets_scale: bool = False
) -> tuple[str | None, int]:
    best_issue: str | None = None
    best_pri = -1
    for pattern, issue, pri in rules:
        if re.search(pattern, text, re.IGNORECASE) and pri > best_pri:
            best_issue = issue
            best_pri = pri
    if best_issue:
        return best_issue, best_pri
    if pets_scale:
        return "未出现共享料架、同时伸手、让行用语、碰后行为等本场景要素。", 40
    if not SCENARIO_ANCHOR_RE.search(text):
        return "未锚定共享料架、取放动作或碰后恢复等场景要素，表述过泛。", 30
    return None, -1


def group_examples_by_issue(
    examples: List[Dict[str, str]],
    max_groups: int = 5,
    max_entries_per_group: int = 3,
) -> List[Dict[str, Any]]:
    """Merge cards that share the same issue text; sort by severity."""
    from collections import OrderedDict

    groups: OrderedDict[str, List[Dict[str, str]]] = OrderedDict()
    group_pri: Dict[str, int] = {}
    for ex in examples:
        issue = ex.get("issue", "").strip()
        if not issue:
            continue
        entry = {
            "label": ex.get("label") or ex.get("source", ""),
            "item_text": ex.get("item_text", ""),
            "item_text_en": ex.get("item_text_en") or ex.get("item_text", ""),
        }
        groups.setdefault(issue, [])
        group_pri[issue] = max(group_pri.get(issue, 0), int(ex.get("priority", 0)))
        if entry not in groups[issue] and len(groups[issue]) < max_entries_per_group:
            groups[issue].append(entry)
    ordered = sorted(
        groups.items(),
        key=lambda kv: (-group_pri.get(kv[0], 0), -len(kv[1])),
    )
    return [{"issue": k, "entries": v} for k, v in ordered[:max_groups]]


def _short_paper_title(title: str, max_len: int = 52) -> str:
    t = (title or "").strip()
    return t if len(t) <= max_len else t[: max_len - 1] + "…"


def load_literature_stats() -> Dict[str, Any]:
    path = (
        PROJECT_ROOT
        / "data/runs"
        / NINE_STEP_RUN
        / "literature_search_agent_group/summary.json"
    )
    return load_json(path) if path.exists() else {}


def build_mechanism_literature_refs() -> List[Dict[str, Any]]:
    """Mechanism → literature (from run search) → nine-step themes."""
    lit = load_literature_stats()
    high = {p.get("title", ""): p for p in lit.get("high_relevance_papers", []) if p.get("title")}

    def pick(*title_substrings: str) -> List[str]:
        out: List[str] = []
        for sub in title_substrings:
            for title in high:
                if sub.lower() in title.lower():
                    out.append(_short_paper_title(title))
                    break
        return out

    fallbacks = {
        "共享工位协调": [
            "Human Factors Considerations and Metrics in Shared Space…",
            "Human-Robot Perception in Industrial Environments: A Survey",
        ],
        "显式沟通与修复": [
            "A Virtual Sandbox Approach to Studying the Effect of Aug…",
            "What Can You Say to a Robot? Capability Communication…",
        ],
        "隐性协调（动作可预期）": [
            "Human-robot proxemics",
            "Physical interaction learning: Behavior adaptation…",
        ],
        "碰撞/接触情境": [
            "Generating behavioral protocol for human-robot physical…",
            "The path towards contact-based physical human–robot int…",
        ],
    }
    specs = [
        ("共享工位协调", ("Shared Space", "Industrial"), "共享工位考量维度（伸手位置、同时取物、工位安全感）"),
        ("显式沟通与修复", ("Augmented Communication", "What Can You Say", "small talk"), "「你先拿」「我来拿这个」、误抓后口头修复"),
        ("隐性协调（动作可预期）", ("proxemics", "Physical interaction learning"), "手臂轨迹可预判、观察手臂可知取件时机"),
        ("碰撞/接触情境", ("physical-contact", "contact-based", "Physical Contact"), "几乎相撞时的有效沟通"),
    ]
    out: List[Dict[str, Any]] = []
    for mech, keys, items in specs:
        papers = pick(*keys) or fallbacks.get(mech, [])
        out.append({"mechanism": mech, "papers": papers, "items": items})
    return out


def build_nine_step_highlights(nine_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Pick 3 representative items with brief literature tie-in."""
    by_en = {it.get("item_text_en") or it.get("item_text", ""): it for it in nine_items}
    specs = [
        (
            "显式让行",
            "When we both reached at the same time, the robot said '你先拿' to let me go first.",
            "口语让行与 HRI 中的 augmented communication / common ground 研究一致（如 Arntz et al., 2021）。",
        ),
        (
            "动作可预期",
            "I could predict when the robot would reach for a tool by watching its arm.",
            "对应「通过观察动作的隐性协调」；与共享空间中的 proxemics、动作线索研究相呼应。",
        ),
        (
            "协调修复",
            "I felt the robot communicated effectively when we almost collided.",
            "对齐碰撞/接触情境下的行为适应与沟通修复文献（physical contact / adaptation 类研究）。",
        ),
    ]
    out: List[Dict[str, str]] = []
    for theme, en_key, note in specs:
        it = by_en.get(en_key)
        if it:
            out.append({
                "theme": theme,
                "item_text": it.get("item_text", en_key),
                "note": note,
            })
    return out


def build_deep_analysis(
    nine_count: int,
    pets_count: int,
    direct_worst: Dict[str, Any],
    direct_best: Dict[str, Any],
    all_runs: List[Dict[str, Any]],
    pets_items: List[Dict[str, str]],
    nine_items: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    worst_items = direct_worst.get("items", [])
    best_items = direct_best.get("items", [])
    run_span = ""
    if all_runs:
        counts = [len(r.get("items", [])) for r in all_runs]
        run_span = f"{min(counts)}–{max(counts)} 条/次"

    lit = load_literature_stats()
    screened = lit.get("screened_papers", "—")
    high_rel = lit.get("high_relevance_count", "—")

    pets_misfits = collect_misfit_examples(
        pets_items, "PETS", PETS_MISFIT_RULES, pets_scale=True
    )
    pets_groups = group_examples_by_issue(pets_misfits, max_groups=5, max_entries_per_group=2)

    direct_misfits: List[Dict[str, str]] = []
    for run in all_runs:
        rid = run.get("run_id", "?")
        direct_misfits.extend(
            collect_misfit_examples(
                run.get("items", []),
                f"直出·{rid}",
                DIRECT_MISFIT_RULES,
            )
        )
    # De-duplicate same English text across runs; keep first label
    seen_text: set[str] = set()
    deduped_direct: List[Dict[str, str]] = []
    for ex in direct_misfits:
        key = (ex.get("item_text") or "").strip().lower()
        if key in seen_text:
            continue
        seen_text.add(key)
        deduped_direct.append(ex)
    direct_groups = group_examples_by_issue(
        deduped_direct, max_groups=7, max_entries_per_group=2
    )

    mech_refs = build_mechanism_literature_refs()
    highlights = build_nine_step_highlights(nine_items)
    papers_with_refs = sum(1 for m in mech_refs if m.get("papers"))

    return [
        {
            "heading": "PETS：跨情境通用，对本场景过于笼统",
            "summary": (
                f"正式量表 {pets_count} 条（Schmidmaier et al., 2024）；"
                f"检出 {len(pets_misfits)} 条与装配共享工位场景明显不符或过于抽象。"
            ),
            "points": PETS_GENERIC_ISSUES,
            "example_groups": pets_groups,
        },
        {
            "heading": "单提示直出：主要问题是可核验性与构念漂移",
            "summary": (
                f"五次生成约 {run_span}（最好 {len(best_items)} 条 / 最差 {len(worst_items)} 条）；"
                f"核心问题不在条目数量，而在跨五次检出 {len(deduped_direct)} 条难核验或构念偏移表述（去重后）。"
            ),
            "points": [
                "可核验性问题：不少句子要求被试推断机器人内在状态（如“是否理解我在场”），难以现场一致评分。",
                "构念漂移问题：出现“像人类同事/队友”“流畅感”等整体印象，偏离共享工位中的具体协调行为。",
                "稳定性问题：一次成稿且多为扁平条目列表，缺少文献约束、模拟预试与统计筛选，跨次可比性弱。",
            ],
            "example_groups": direct_groups,
        },
        {
            "heading": "九步骤：好在哪里（机制 + 文献 + 流程）",
            "summary": (
                f"最终 {nine_count} 条（run {NINE_STEP_RUN}）；文献检索 screened {screened} 篇、"
                f"高相关 {high_rel} 篇，其中 {papers_with_refs} 类机制有对应论文支撑。"
            ),
            "points": [
                "流程：访谈 → 文献机制卡片 → 题项生成与双组模拟 → EFA 保留可施测题量。",
                "条目：保留场景内真实话术与手臂可预测性，对应同时伸手、挡路、几乎碰撞等失败模式。",
                "结构：协调沟通（6）+ 共享工位考量（4），比 PETS 更贴场景、比直出更短更稳。",
            ],
            "mechanism_refs": mech_refs,
            "nine_highlights": highlights,
        },
    ]


def pick_direct_runs() -> Dict[str, Any]:
    manifest_path = PKG_ROOT / "direct_llm_runs" / "manifest.json"
    if not manifest_path.exists():
        return {"best": None, "worst": None, "all": []}

    manifest = load_json(manifest_path)
    runs = manifest.get("runs", [])
    if not runs:
        return {"best": None, "worst": None, "all": []}

    def load_run(rid: str) -> Dict[str, Any]:
        d = PKG_ROOT / "direct_llm_runs" / rid
        md = (d / "scale_draft.md").read_text(encoding="utf-8")
        items = parse_scale_markdown(md)
        meta_path = d / "meta.json"
        meta = load_json(meta_path) if meta_path.exists() else {}
        return {
            "run_id": rid,
            "meta": meta,
            "markdown": md,
            "items": items,
        }

    worst_id = SUBJECTIVE_WORST_RUN
    best_id = SUBJECTIVE_BEST_RUN
    worst = load_run(worst_id)
    best = load_run(best_id)

    return {
        "best": best,
        "worst": worst,
        "all": [load_run(r["run_id"]) for r in runs],
        "selection_note": (
            f"主观选定：最差={worst_id}（含「像人类同事」等整体感受句），"
            f"最好={best_id}（条目相对简洁、场景覆盖较完整）。"
        ),
    }


def localize_to_zh(data: Dict[str, Any]) -> Dict[str, Any]:
    """Attach Chinese text for all displayed strings."""
    texts: List[str] = []
    for block in (data["nine_step"]["items"], data["pets"]["items"]):
        for it in block:
            texts.append(it.get("item_text", ""))
            texts.append(it.get("dimension", ""))
    direct = data["direct_llm"]
    for key in ("worst", "best"):
        block = direct.get(key) or {}
        for it in block.get("items", []):
            texts.append(it.get("item_text", ""))
            texts.append(it.get("dimension", ""))
    for row in data["comparison_rows"]:
        texts.extend([row.get("nine_step_good", ""), row.get("contrast_bad", "")])
    for pair in data["similar_pairs"]:
        texts.extend([pair.get("nine_step", ""), pair.get("pets", ""), pair.get("direct", "")])

    data["stability_qualitative"] = STABILITY_QUALITATIVE
    data["deep_analysis"] = build_deep_analysis(
        nine_count=len(data["nine_step"]["items"]),
        pets_count=len(data["pets"]["items"]),
        direct_worst=data["direct_llm"].get("worst") or {},
        direct_best=data["direct_llm"].get("best") or {},
        all_runs=data["direct_llm"].get("all") or [],
        pets_items=data["pets"]["items"],
        nine_items=data["nine_step"]["items"],
    )
    for block in data["deep_analysis"]:
        for grp in block.get("example_groups") or []:
            for ent in grp.get("entries") or []:
                texts.append(ent.get("item_text_en") or ent.get("item_text", ""))
        for h in block.get("nine_highlights") or []:
            texts.append(h.get("item_text_en") or h.get("item_text", ""))
            texts.append(h.get("note", ""))
    for run in direct.get("all") or []:
        for it in run.get("items", []):
            texts.append(it.get("item_text", ""))
            texts.append(it.get("dimension", ""))

    bundle = ensure_bundle_for_texts(texts, use_llm=True)

    data["nine_step"]["items"] = apply_zh_to_items(data["nine_step"]["items"], bundle)
    data["pets"]["items"] = apply_zh_to_items(data["pets"]["items"], bundle)
    if direct.get("worst"):
        direct["worst"]["items"] = apply_zh_to_items(direct["worst"]["items"], bundle)
    if direct.get("best"):
        direct["best"]["items"] = apply_zh_to_items(direct["best"]["items"], bundle)
    for run in direct.get("all") or []:
        run["items"] = apply_zh_to_items(run.get("items", []), bundle)

    for row in data["comparison_rows"]:
        row["nine_step_good"] = translate_text(row["nine_step_good"], bundle)
        row["contrast_bad"] = translate_text(row["contrast_bad"], bundle)
    for pair in data["similar_pairs"]:
        pair["nine_step"] = translate_text(pair["nine_step"], bundle)
        pair["pets"] = translate_text(pair["pets"], bundle)
        pair["direct"] = translate_text(pair["direct"], bundle)

    for block in data["deep_analysis"]:
        for grp in block.get("example_groups") or []:
            for ent in grp.get("entries") or []:
                src = ent.get("item_text_en") or ent.get("item_text", "")
                ent["item_text"] = translate_text(src, bundle)
        for h in block.get("nine_highlights") or []:
            src = h.get("item_text_en") or h.get("item_text", "")
            h["item_text"] = translate_text(src, bundle)

    return data


def build_comparison_data() -> Dict[str, Any]:
    nine = load_json(PKG_ROOT / "data" / "nine_step_scale.json")
    pets = load_json(PKG_ROOT / "data" / "pets_items.json")
    scenario = load_json(PKG_ROOT / "data" / "scenario_input.json")
    factors_path = PROJECT_ROOT / "data/runs" / NINE_STEP_RUN / "scenario_factors.json"
    factors = load_json(factors_path) if factors_path.exists() else {}
    direct = pick_direct_runs()
    scenario_text = scenario.get("scenario_text") or scenario_text_from_interview(scenario)
    prompt_path = PKG_ROOT / "direct_llm_runs" / "prompt_used.txt"
    prompt_meta_path = PKG_ROOT / "direct_llm_runs" / "prompt_meta.json"
    payload = build_direct_prompt_payload(scenario_text)
    filled_prompt = payload["filled"]
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(filled_prompt, encoding="utf-8")
    prompt_meta = load_json(prompt_meta_path) if prompt_meta_path.exists() else {}
    manifest = load_json(PKG_ROOT / "direct_llm_runs" / "manifest.json") if (
        PKG_ROOT / "direct_llm_runs" / "manifest.json"
    ).exists() else {}
    model_name = prompt_meta.get("model") or (
        (manifest.get("runs") or [{}])[0].get("model") if manifest.get("runs") else "—"
    )

    return {
        "scenario_label": "肌肉骨骼 · 并肩装配 · 共享料架",
        "scenario_display": build_scenario_display(scenario, factors),
        "nine_step": nine,
        "pets": pets,
        "direct_llm": direct,
        "comparison_rows": COMPARISON_ROWS,
        "similar_pairs": SIMILAR_PAIRS,
        "evidence_links": [{"label": a, "path": b} for a, b in EVIDENCE_LINKS],
        "direct_llm_prompt": {
            "filled": filled_prompt,
            "model": model_name,
            "temperature": prompt_meta.get("temperature", 0.85),
            "seeds": prompt_meta.get("seeds", [42, 43, 44, 45, 46]),
            "source_file": "qualitative_musculoskeletal_comparison/direct_llm_runs/prompt_used.txt",
        },
    }



from report_render import render_html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--init-data', action='store_true')
    args = parser.parse_args()
    if args.init_data or not (PKG_ROOT / 'data/nine_step_scale.json').exists():
        init_data()
    data = build_comparison_data()
    data = localize_to_zh(data)
    out_dir = PKG_ROOT / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)
    save_json(out_dir / 'comparison_data.json', data)
    html_path = out_dir / 'qualitative_comparison.html'
    html_path.write_text(render_html(data), encoding='utf-8')
    print('Wrote', html_path)


if __name__ == '__main__':
    main()
