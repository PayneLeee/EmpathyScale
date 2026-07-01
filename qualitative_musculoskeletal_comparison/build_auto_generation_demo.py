"""Build an HTML replay that simulates the full demo UI generation process."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List

PKG_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_ROOT.parent
RUN_ID = "2026-05-11_155408"
DEMO_ROOT = PROJECT_ROOT / "demo_musculoskeletal_run" / RUN_ID

DIMENSION_ZH = {
    "Spatial Coordination Understanding": "空间协调理解",
    "Collision-Responsive Adaptation": "碰撞响应适应",
    "Explicit Communication Repair": "显式沟通修复",
    "Coordination Communication (6 items)": "协调沟通（6 条）",
    "Shared Workspace Consideration (4 items)": "共享工位考量（4 条）",
}

ITEM_ZH = {
    "The robot paused its arm to let me reach first.": "机器人暂停手臂动作，让我先伸手取物。",
    "I could tell the robot was aware of my working area.": "我能看出机器人知道我的工作区域。",
    "The robot changed its path to avoid reaching at the same time as me.": "机器人会改变路径，避免和我同时伸手。",
    "The robot left enough space for me to access the tool rack.": "机器人给我留出了足够空间去拿共享工具架上的物品。",
    "The robot's movements showed it understood where I needed to reach.": "机器人的动作表明它理解我需要伸手的位置。",
    "I felt the robot respected my personal space at the workstation.": "我觉得机器人尊重我在工位上的个人空间。",
    "The robot yielded when I started to reach for a part.": "当我开始伸手拿零件时，机器人会让行。",
    "The robot's arm trajectory made it easy to anticipate its next move.": "机器人的手臂轨迹使我容易预判它的下一步动作。",
    "The robot adjusted its reach to avoid blocking my hand.": "机器人会调整伸手动作，避免挡住我的手。",
    "I could predict when the robot would reach for a tool by watching its arm.": "通过观察它的手臂，我能预判机器人何时会去取工具。",
    "The robot seemed to know when I needed a particular tool.": "机器人似乎知道我什么时候需要某个特定工具。",
    "The robot's pauses helped us coordinate who takes which part.": "机器人的暂停帮助我们协调谁来拿哪个零件。",
    "When we bumped, the robot immediately retracted its arm.": "当我们发生碰撞时，机器人会立即收回手臂。",
    "The robot apologized verbally after accidental contact.": "发生意外接触后，机器人会口头道歉。",
    "I felt the robot cared about my safety when it stopped after touching me.": "机器人在碰到我后停下来，让我觉得它在关心我的安全。",
    "The robot's quick reaction to contact reassured me.": "机器人对接触的快速反应让我感到安心。",
    "After a collision, the robot adjusted its movement to avoid repeating it.": "碰撞后，机器人会调整动作，避免再次发生。",
    "The robot seemed sensitive to physical contact with me.": "机器人似乎对与我的身体接触很敏感。",
    "I felt the robot was considerate when it pulled back after a bump.": "机器人在碰撞后退回时，我觉得它很体贴。",
    "The robot's response to accidental touch made me feel respected.": "机器人对意外接触的反应让我觉得被尊重。",
    "When our arms touched, the robot paused and then moved more carefully.": "当我们的手臂碰到时，机器人会暂停，然后更谨慎地移动。",
    "The robot's behavior after contact showed it understood my discomfort.": "机器人接触后的行为表明它理解我的不适。",
    "I trusted the robot more because of how it handled unintended contact.": "机器人处理意外接触的方式让我更信任它。",
    "The robot's immediate retraction after a bump felt protective.": "机器人碰撞后立即收回手臂，让我觉得它在保护我。",
    "When we both reached at the same time, the robot said '你先拿' to let me go first.": "当我们同时伸手时，机器人会说「你先拿」，让我先取。",
    "The robot's verbal phrases helped resolve coordination conflicts.": "机器人的口头短句帮助解决了协调冲突。",
    "I found the robot's spoken cues clear when we needed to take turns.": "当我们需要轮流取物时，我觉得机器人的口头提示很清楚。",
    "The robot's words ('我来拿这个') made its intention obvious.": "机器人说「我来拿这个」等话语，使其意图一目了然。",
    "After a misreach, the robot's verbal response quickly got us back on track.": "误抓之后，机器人的口头回应能迅速让我们重新协调。",
    "The robot's short phrases reduced my frustration during simultaneous reaching.": "在同时伸手取物时，机器人的短句减轻了我的挫败感。",
    "I felt the robot communicated effectively when we almost collided.": "当我们几乎相撞时，我觉得机器人的沟通是有效的。",
    "The robot's verbal repair statements restored smooth collaboration.": "机器人的口头修复语句恢复了顺畅协作。",
    "When coordination failed, the robot's words helped me understand what to do next.": "当协调失败时，机器人的话帮助我理解下一步该怎么做。",
    "The robot's spoken instructions made the shared workspace feel safer.": "机器人的口头指示让共享工位感觉更安全。",
    "I appreciated that the robot verbally indicated when it would wait for me.": "我很欣赏机器人用口头方式表明它会等我先取。",
    "The robot's use of phrases like '你先拿' showed it understood my need to reach.": "机器人使用「你先拿」这类话语，表明它理解我需要伸手取物。",
}

MECHANISM_ZH = {
    "collision/contact adaptation": "碰撞/接触后的适应",
    "shared workspace coordination": "共享工位协调",
    "implicit coordination through action observation": "通过观察动作进行隐性协调",
    "explicit communication and repair": "显式沟通与修复",
    "bodily limitation understanding": "对身体限制的理解",
}

PAPER_ZH = {
    "Human-robot proxemics": "人机近身距离研究",
    "Generating behavioral protocol for human-robot physical-contact interaction": "人机身体接触交互的行为协议生成",
    "The path towards contact-based physical human–robot interaction": "面向接触式身体人机交互的发展路径",
    "Physical interaction learning: Behavior adaptation in cooperative human-robot tasks involving physical contact": "涉及身体接触的协作人机任务中的行为适应学习",
    "Human Factors Considerations and Metrics in Shared Space Human-Robot Collaboration: A Systematic Review": "共享空间人机协作中的人因考量与指标综述",
    "Advantages of Multimodal versus Verbal-Only Robot-to-Human Communication with an Anthropomorphic Robotic Mock Driver": "多模态机器人沟通相对纯语音沟通的优势",
    "Towards Effective Interface Designs for Collaborative HRI in Manufacturing": "面向制造业协作人机交互的有效界面设计",
    "When Robots Say No: The Empathic Ethical Disobedience Benchmark": "当机器人说“不”：共情伦理违抗基准",
    "Bilateral human-robot interaction with physical contact": "包含身体接触的双向人机交互",
    "A Virtual Sandbox Approach to Studying the Effect of Augmented Communication on Human-Robot Collaboration": "用于研究增强沟通对人机协作影响的虚拟沙盒方法",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_scale_items(markdown: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    current_dim: str | None = None
    in_items_section = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if re.match(r"^##\s+Items\b", stripped, re.IGNORECASE):
            in_items_section = True
            continue
        dim_match = re.match(r"^###\s+(.+)$", stripped)
        if dim_match:
            if in_items_section:
                current_dim = dim_match.group(1).strip()
            continue
        if not in_items_section or not current_dim:
            continue
        item_match = re.match(r"^[-*]\s*Item\s+\d+:\s*(.+)$", stripped, re.IGNORECASE)
        if not item_match:
            item_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if item_match:
            text = item_match.group(1).strip()
            if len(text) >= 18:
                items.append({"dimension": current_dim, "text": text})
    return items


def compact_text(text: Any, max_len: int = 210) -> str:
    text = re.sub(r"\s+", " ", str(text).strip())
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def first_values(values: List[str], limit: int = 3) -> str:
    return "；".join(values[:limit])


def grouped_scale_sections(items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[str]] = {}
    for item in items:
        groups.setdefault(item["dimension"], []).append(item["text"])
    return [{"dimension": dim, "items": texts} for dim, texts in groups.items()]


def zh_item(text: str) -> str:
    return ITEM_ZH.get(text, text)


def zh_dimension(name: str) -> str:
    return DIMENSION_ZH.get(name, name)


def zh_items(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {"dimension": zh_dimension(item["dimension"]), "text": zh_item(item["text"])}
        for item in items
    ]


def zh_conversation_content(text: str) -> str:
    # The opening message is bilingual. Keep only Chinese paragraphs for the replay.
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    zh_paragraphs = [p for p in paragraphs if re.search(r"[\u4e00-\u9fff]", p)]
    return "\n\n".join(zh_paragraphs) if zh_paragraphs else text


def zh_interaction_modalities(value: Any) -> str:
    return "机器人使用简短口头短句（如「我来拿这个」「你先拿」）；人通过观察机器人手臂暂停、让位、换路径或收回等动作判断意图。"


def zh_summary_value(label: str, interview: Dict[str, Any]) -> str:
    if label == "评估场景":
        return "人与肌肉骨骼机器人并肩坐在同一装配工位，共享工具架；人负责需要判断的精细拿取，机器人负责较重或靠近自身一侧的物品。时序或协调出错时，可能出现同时伸手、互相挡路、轻微身体接触或碰撞。"
    if label == "机器人平台":
        return "肌肉骨骼机器人"
    if label == "交互方式":
        return zh_interaction_modalities(interview.get("interaction_modalities", ""))
    if label == "协作分工":
        return "人负责更精细、需要判断的物品；机器人负责较重或更靠近机器人一侧的物品。"
    if label == "失败模式":
        return "双方同时伸手拿同一层零件；一方误以为对方已看到自己的伸手；挡路或擦碰；接触后没有暂停、避让或说明。"
    return ""


def build_demo_data() -> Dict[str, Any]:
    conversation = load_json(DEMO_ROOT / "interview_agent_group" / "conversation.json")
    interview = load_json(DEMO_ROOT / "interview_agent_group" / "summary.json")
    literature = load_json(DEMO_ROOT / "literature_search_agent_group" / "summary.json")
    generation = load_json(DEMO_ROOT / "empathy_scale_generation_agent_group" / "summary.json")
    validation = load_json(
        DEMO_ROOT / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
    )
    selection_stats = load_json(DEMO_ROOT / "statistical_selection" / "selection_statistics.json")
    timing = load_json(DEMO_ROOT / "run_timing.json")

    initial_md = (
        DEMO_ROOT / "empathy_scale_generation_agent_group" / "scale_draft.md"
    ).read_text(encoding="utf-8")
    final_md = (
        DEMO_ROOT / "empathy_scale_generation_agent_group" / "filtered_scale_draft.md"
    ).read_text(encoding="utf-8")
    initial_items = parse_scale_items(initial_md)
    final_items = parse_scale_items(final_md)
    initial_items_zh = zh_items(initial_items)
    final_items_zh = zh_items(final_items)

    mechanisms = [
        MECHANISM_ZH.get(m, m)
        for m in literature.get("scenario_specific_factors", {}).get("empathy_mechanisms", [])
    ]
    coverage = generation.get("mechanism_coverage_report", {})
    metrics = validation.get("validation_metrics", {})
    discriminant = metrics.get("discriminant_ability", {})
    consistency = metrics.get("internal_consistency", {})

    pipeline_steps = [
        {
            "id": "step_1",
            "title": "场景访谈解析",
            "detail": "已完成结构化访谈，提取工位、平台、沟通方式与失败模式。",
            "result": (
                "肌肉骨骼机器人 / 装配工位与共享工具架 / "
                f"{len(interview.get('failure_modes', []))} 类失败模式"
            ),
        },
        {
            "id": "step_2",
            "title": "文献检索",
            "detail": "围绕共享空间、身体人机交互、动作可预期与口头修复检索论文。",
            "result": (
                f"检索到 {literature.get('total_papers_found', 602)} 篇 / "
                f"筛读 {literature.get('screened_papers', 24)} 篇 / "
                f"高相关 {literature.get('high_relevance_count', 8)} 篇"
            ),
        },
        {
            "id": "step_3",
            "title": "构念界定与初始题项生成",
            "detail": "把访谈与文献证据合成为构念，并生成第一版候选条目。",
            "result": (
                f"{len(coverage.get('covered', mechanisms))} 类机制覆盖，"
                f"候选条目 {selection_stats.get('n_original_items', len(initial_items_zh))} 条"
            ),
        },
        {
            "id": "step_4",
            "title": "语义去重",
            "detail": "删除近似重复与过泛条目，保留能被现场核验的表述。",
            "result": "保留共享料架、让行、手臂轨迹、碰后修复等锚点。",
        },
        {
            "id": "step_5",
            "title": "双组模拟参与者评估",
            "detail": "用共情机器人组与非共情机器人组的模拟参与者对候选条目评分。",
            "result": "生成参与者层级评分数据，用于后续统计分析。",
        },
        {
            "id": "step_6",
            "title": "双组合并",
            "detail": "合并共情组与非共情组评分，形成统计分析数据。",
            "result": "合并评估摘要已生成，可用于因子分析与区分性验证。",
        },
        {
            "id": "step_7",
            "title": "探索性/验证性因子分析选题",
            "detail": "根据因子结构、载荷和可解释性筛选题项。",
            "result": (
                f"{selection_stats.get('n_original_items', len(initial_items_zh))} 条候选 -> "
                f"{selection_stats.get('n_selected_items', len(final_items_zh))} 条保留，"
                f"保留率 {selection_stats.get('selection_ratio', 0.303):.1%}"
            ),
        },
        {
            "id": "step_8",
            "title": "独立样本验证",
            "detail": "用验证样本检查区分能力与内部一致性。",
            "result": (
                f"Cohen's d = {discriminant.get('cohens_d', 0.931)}，"
                f"Cronbach's α = {consistency.get('alpha', 0.936)}"
            ),
        },
        {
            "id": "step_9",
            "title": "输出最终量表与关键指标",
            "detail": "写出筛选后量表草案，并在网页界面中展示结果。",
            "result": (
                f"{len(final_items_zh)} 条 / {len({item['dimension'] for item in final_items_zh})} 个维度 / "
                f"{timing.get('elapsed_human', '2h 45m 56s')}"
            ),
        },
    ]

    paper_titles: List[str] = []
    for titles in coverage.get("paper_links", {}).values():
        for title in titles:
            zh_title = PAPER_ZH.get(title, title)
            if zh_title not in paper_titles:
                paper_titles.append(zh_title)

    summary_rows = [
        ("评估场景", zh_summary_value("评估场景", interview)),
        ("机器人平台", zh_summary_value("机器人平台", interview)),
        ("交互方式", zh_summary_value("交互方式", interview)),
        ("协作分工", zh_summary_value("协作分工", interview)),
        ("失败模式", zh_summary_value("失败模式", interview)),
    ]

    feed_lines = [
        "读取访谈对话记录",
        "生成结构化访谈摘要",
        f"生成 {len(literature.get('search_queries', []))} 个文献检索问题",
        f"检索到 {literature.get('total_papers_found', 602)} 篇论文，筛读 {literature.get('screened_papers', 24)} 篇",
        "构建机制卡片：共享工位协调 / 碰撞恢复 / 显式沟通修复",
        f"读取 {len(generation.get('used_expert_pdfs', []))} 份专家 PDF 指南",
        f"生成候选条目 {selection_stats.get('n_original_items', len(initial_items))} 条",
        "运行共情机器人组模拟评分",
        "运行非共情机器人组模拟评分",
        "合并参与者层级评分数据",
        "执行探索性/验证性因子分析和统计选题",
        f"筛选后保留 {selection_stats.get('n_selected_items', len(final_items))} 条",
        f"验证结果：Cronbach's α={consistency.get('alpha', 0.936)}，Cohen's d={discriminant.get('cohens_d', 0.931)}",
        "渲染网页结果快照",
    ]

    return {
        "run_id": RUN_ID,
        "title": "EmpathyScale 生成过程回放",
        "subtitle": "模拟网页结果快照的对话、流水线与最终结果生成",
        "duration_seconds": 105,
        "conversation": [
            {
                "type": msg.get("type", "agent"),
                "content": zh_conversation_content(msg.get("content", "")),
                "timestamp": msg.get("timestamp", ""),
            }
            for msg in conversation
        ],
        "summary_rows": [(label, compact_text(value)) for label, value in summary_rows],
        "pipeline_steps": pipeline_steps,
        "feed_lines": feed_lines,
        "paper_titles": paper_titles[:10],
        "initial_items": [item["text"] for item in initial_items_zh[:7]],
        "scale_sections": grouped_scale_sections(final_items_zh),
        "metrics": [
            ("最终题项", str(len(final_items_zh))),
            ("内部一致性", f"Cronbach's α = {consistency.get('alpha', 0.936)}"),
            ("区分性", f"Cohen's d = {discriminant.get('cohens_d', 0.931)}"),
        ],
    }


def esc(value: Any) -> str:
    return html.escape(str(value))


def render_html(data: Dict[str, Any]) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    step_cards = "\n".join(
        f"""<div class="step-card pending" id="{esc(step["id"])}">
          <div class="step-icon">○</div>
          <div><div class="step-title">{i + 1}. {esc(step["title"])}</div>
          <div class="step-detail">等待中</div><div class="step-result"></div></div>
        </div>"""
        for i, step in enumerate(data["pipeline_steps"])
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(data["title"])}</title>
<style>
  :root {{
    --bg: #f5f7fb; --card: #fff; --text: #222; --muted: #7b8794;
    --blue: #0084ff; --green: #28a745; --border: #e5e9f0; --soft: #f0f6ff;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; }}
  .header {{ background: #fff; border-bottom: 1px solid var(--border); padding: 14px 22px; position: sticky; top: 0; z-index: 5; }}
  .header-inner {{ max-width: 1320px; margin: 0 auto; display: flex; justify-content: space-between; gap: 16px; align-items: center; }}
  h1 {{ margin: 0; font-size: 20px; }}
  .subtitle {{ margin: 4px 0 0; font-size: 13px; color: var(--muted); }}
  .controls {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
  button {{ border: none; border-radius: 8px; background: var(--blue); color: #fff; padding: 8px 12px; cursor: pointer; font: inherit; }}
  button.secondary {{ background: #eef2f7; color: #334155; }}
  .speed {{ font-size: 12px; color: var(--muted); }}
  .progress-shell {{ height: 5px; background: #e9eef6; }}
  .progress {{ height: 100%; width: 0%; background: linear-gradient(90deg, var(--blue), var(--green)); transition: width .2s linear; }}
  .app {{ max-width: 1320px; margin: 0 auto; padding: 16px; display: grid; grid-template-columns: minmax(380px, 1fr) minmax(420px, 1fr); gap: 16px; }}
  .panel {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 10px 24px rgba(15, 23, 42, .06); }}
  .panel h2 {{ font-size: 16px; margin: 0; padding: 14px 16px; border-bottom: 1px solid var(--border); }}
  .chat-area {{ height: 660px; overflow: auto; padding: 16px; background: #f8fafc; }}
  .message {{ display: flex; margin-bottom: 14px; align-items: flex-start; animation: pop .32s ease; }}
  .message.user {{ justify-content: flex-end; }}
  .bubble {{ max-width: 78%; padding: 10px 14px; border-radius: 13px; line-height: 1.55; font-size: 14px; white-space: pre-wrap; box-shadow: 0 2px 8px rgba(15,23,42,.06); }}
  .message.agent .bubble {{ background: #fff; border: 1px solid var(--border); border-bottom-left-radius: 4px; }}
  .message.user .bubble {{ background: var(--blue); color: #fff; border-bottom-right-radius: 4px; }}
  .typing {{ display: inline-flex; gap: 3px; align-items: center; }}
  .typing span {{ width: 6px; height: 6px; background: #9aa6b2; border-radius: 50%; animation: blink 1s infinite; }}
  .typing span:nth-child(2) {{ animation-delay: .15s; }}
  .typing span:nth-child(3) {{ animation-delay: .3s; }}
  .input-bar {{ display: flex; gap: 8px; border-top: 1px solid var(--border); padding: 12px; background: #fff; }}
  .fake-input {{ flex: 1; border: 1px solid #d8dee8; border-radius: 8px; padding: 10px 12px; color: var(--muted); min-height: 42px; }}
  .pipeline {{ padding: 14px 16px; height: 660px; overflow: auto; }}
  .live {{ background: var(--soft); border: 1px solid #dbeafe; border-radius: 10px; padding: 12px; margin-bottom: 12px; }}
  .live-title {{ font-weight: 700; font-size: 14px; margin-bottom: 4px; }}
  .live-line {{ color: #526071; font-size: 13px; line-height: 1.5; }}
  .step-card {{ border-left: 4px solid #cbd5e1; background: #fff; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; display: flex; gap: 10px; align-items: flex-start; border-top: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
  .step-card.running {{ border-left-color: var(--blue); background: #f7fbff; }}
  .step-card.done {{ border-left-color: var(--green); }}
  .step-icon {{ width: 24px; font-size: 18px; text-align: center; color: var(--muted); }}
  .step-card.running .step-icon {{ color: var(--blue); animation: spin 1s linear infinite; }}
  .step-card.done .step-icon {{ color: var(--green); animation: none; }}
  .step-title {{ font-weight: 700; font-size: 14px; }}
  .step-detail, .step-result {{ font-size: 12px; color: var(--muted); margin-top: 3px; line-height: 1.45; }}
  .step-result {{ color: #334155; }}
  .feed {{ margin-top: 12px; background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 10px; max-height: 150px; overflow: auto; }}
  .feed-item {{ font-size: 12px; color: #4b5563; padding: 4px 0; border-bottom: 1px dashed #edf0f5; animation: pop .25s ease; }}
  .paper-list {{ margin-top: 12px; display: none; background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 10px; }}
  .paper-item {{ font-size: 12px; color: #3f4a5a; padding: 3px 0; }}
  .summary {{ display: none; margin: 0 16px 14px; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
  .summary table {{ width: 100%; border-collapse: collapse; background: #fff; }}
  .summary th, .summary td {{ text-align: left; border-bottom: 1px solid #edf0f5; padding: 8px 10px; font-size: 13px; vertical-align: top; }}
  .summary th {{ width: 100px; color: var(--muted); background: #fafafa; }}
  .result {{ display: none; grid-column: 1 / -1; }}
  .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding: 14px 16px 0; }}
  .metric {{ border: 1px solid #cfe8d7; background: #f0fdf4; border-radius: 10px; padding: 10px; }}
  .metric label {{ display: block; color: #4b6354; font-size: 12px; }}
  .metric strong {{ display: block; color: #176534; font-size: 18px; margin-top: 3px; }}
  .scale-sections {{ padding: 14px 16px 16px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
  .dimension {{ border: 1px solid var(--border); border-left: 4px solid var(--blue); border-radius: 10px; background: #fff; padding: 12px; }}
  .dimension h3 {{ margin: 0 0 8px; color: var(--blue); font-size: 15px; }}
  .item {{ padding: 7px 0; border-bottom: 1px solid #f0f2f5; font-size: 13px; line-height: 1.45; }}
  .item:last-child {{ border-bottom: none; }}
  .item-label {{ color: var(--muted); font-size: 11px; margin-right: 5px; }}
  @keyframes pop {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  @keyframes blink {{ 50% {{ opacity: .25; }} }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  @media (max-width: 980px) {{
    .app {{ grid-template-columns: 1fr; }}
    .result {{ grid-column: auto; }}
    .scale-sections, .metrics {{ grid-template-columns: 1fr; }}
    .chat-area, .pipeline {{ height: 560px; }}
  }}
</style>
</head>
<body>
<div class="header">
  <div class="header-inner">
    <div>
      <h1>{esc(data["title"])}</h1>
      <p class="subtitle">{esc(data["subtitle"])} · 运行编号 <code>{esc(data["run_id"])}</code></p>
    </div>
    <div class="controls">
      <button id="play">播放</button>
      <button id="pause" class="secondary">暂停</button>
      <button id="restart" class="secondary">重播</button>
      <span class="speed">约 {esc(data["duration_seconds"])} 秒</span>
    </div>
  </div>
</div>
<div class="progress-shell"><div class="progress" id="progress"></div></div>
<main class="app" aria-label="自动生成过程回放">
  <section class="panel">
    <h2>智能访谈对话</h2>
    <div class="chat-area" id="chatArea"></div>
    <div class="summary" id="summary"></div>
    <div class="input-bar">
      <div class="fake-input" id="fakeInput">正在等待用户输入…</div>
      <button class="secondary">发送</button>
    </div>
  </section>
  <section class="panel">
    <h2>九步骤自动处理</h2>
    <div class="pipeline">
      <div class="live">
        <div class="live-title" id="liveTitle">等待访谈完成</div>
        <div class="live-line" id="liveLine">访谈信息会被转化为结构化场景，再进入自动生成流水线。</div>
      </div>
      <div id="steps">{step_cards}</div>
      <div class="feed" id="feed"><div class="feed-item">等待进度事件...</div></div>
      <div class="paper-list" id="papers"></div>
    </div>
  </section>
  <section class="panel result" id="result">
    <h2>生成结果：最终量表</h2>
    <div class="metrics" id="metrics"></div>
    <div class="scale-sections" id="scaleSections"></div>
  </section>
</main>
<script>
const demo = {data_json};
const progressEl = document.getElementById("progress");
const chatArea = document.getElementById("chatArea");
const fakeInput = document.getElementById("fakeInput");
const totalMs = demo.duration_seconds * 1000;
let startedAt = 0;
let elapsedBeforePause = 0;
let raf = null;
let fired = new Set();
let playing = false;

const eventPlan = [];
demo.conversation.forEach((msg, i) => eventPlan.push({{ at: 2 + i * 7, type: "message", payload: msg, key: "msg_" + i }}));
eventPlan.push({{ at: 43, type: "summary", key: "summary" }});
eventPlan.push({{ at: 48, type: "pipeline-start", key: "pipeline-start" }});
demo.pipeline_steps.forEach((step, i) => {{
  eventPlan.push({{ at: 50 + i * 5.4, type: "step-running", payload: step, key: "run_" + step.id }});
  eventPlan.push({{ at: 53 + i * 5.4, type: "step-done", payload: step, key: "done_" + step.id }});
}});
demo.feed_lines.forEach((line, i) => eventPlan.push({{ at: 50 + i * 3.2, type: "feed", payload: line, key: "feed_" + i }}));
eventPlan.push({{ at: 60, type: "papers", key: "papers" }});
eventPlan.push({{ at: 96, type: "result", key: "result" }});

function escapeHtml(value) {{
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}}

function addTyping(kind) {{
  const div = document.createElement("div");
  div.className = "message " + kind;
  div.id = "typing";
  div.innerHTML = '<div class="bubble"><span class="typing"><span></span><span></span><span></span></span></div>';
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
}}

function removeTyping() {{
  const el = document.getElementById("typing");
  if (el) el.remove();
}}

function addMessage(msg) {{
  removeTyping();
  const div = document.createElement("div");
  div.className = "message " + msg.type;
  div.innerHTML = `<div class="bubble">${{escapeHtml(msg.content)}}</div>`;
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
  fakeInput.textContent = msg.type === "agent" ? "用户正在输入回答…" : "智能体正在生成追问…";
}}

function showSummary() {{
  const box = document.getElementById("summary");
  box.style.display = "block";
  box.innerHTML = "<table>" + demo.summary_rows.map(([label, value]) =>
    `<tr><th>${{escapeHtml(label)}}</th><td>${{escapeHtml(value)}}</td></tr>`
  ).join("") + "</table>";
  fakeInput.textContent = "访谈已完成，点击继续进入自动处理阶段";
}}

function setStep(step, status) {{
  const card = document.getElementById(step.id);
  card.className = "step-card " + status;
  card.querySelector(".step-icon").textContent = status === "running" ? "⟳" : "✓";
  card.querySelector(".step-detail").textContent = step.detail;
  card.querySelector(".step-result").textContent = status === "done" ? step.result : "处理中…";
  document.getElementById("liveTitle").textContent = status === "running" ? "当前环节：" + step.title : "已完成：" + step.title;
  document.getElementById("liveLine").textContent = step.detail;
  card.scrollIntoView({{ block: "nearest", behavior: "smooth" }});
}}

function addFeed(line) {{
  const feed = document.getElementById("feed");
  if (feed.textContent.includes("等待进度事件")) feed.innerHTML = "";
  const div = document.createElement("div");
  div.className = "feed-item";
  div.textContent = "[进度] " + line;
  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;
}}

function showPapers() {{
  const box = document.getElementById("papers");
  box.style.display = "block";
  box.innerHTML = "<strong style='font-size:13px'>文献预览</strong>" + demo.paper_titles.map((title, i) =>
    `<div class="paper-item">[${{i + 1}}] ${{escapeHtml(title)}}</div>`
  ).join("");
}}

function showResult() {{
  document.getElementById("liveTitle").textContent = "全部处理完成";
  document.getElementById("liveLine").textContent = "请查看下方生成的量表条目。";
  addMessage({{ type: "agent", content: "全部处理完成！请查看下方生成的量表条目。" }});
  const result = document.getElementById("result");
  result.style.display = "block";
  document.getElementById("metrics").innerHTML = demo.metrics.map(([label, value]) =>
    `<div class="metric"><label>${{escapeHtml(label)}}</label><strong>${{escapeHtml(value)}}</strong></div>`
  ).join("");
  document.getElementById("scaleSections").innerHTML = demo.scale_sections.map((section) =>
    `<div class="dimension"><h3>${{escapeHtml(section.dimension)}}</h3>` +
    section.items.map((item, i) => `<div class="item"><span class="item-label">题项 ${{i + 1}}</span>${{escapeHtml(item)}}</div>`).join("") +
    "</div>"
  ).join("");
  result.scrollIntoView({{ behavior: "smooth", block: "start" }});
}}

function executeEvent(event) {{
  if (event.type === "message") {{
    addTyping(event.payload.type);
    setTimeout(() => addMessage(event.payload), 450);
  }} else if (event.type === "summary") {{
    showSummary();
  }} else if (event.type === "pipeline-start") {{
    fakeInput.textContent = "自动处理阶段运行中…";
    document.getElementById("liveTitle").textContent = "自动处理阶段启动";
    document.getElementById("liveLine").textContent = "流水线开始调用文献检索、题项生成、评估和统计筛选模块。";
  }} else if (event.type === "step-running") {{
    setStep(event.payload, "running");
  }} else if (event.type === "step-done") {{
    setStep(event.payload, "done");
  }} else if (event.type === "feed") {{
    addFeed(event.payload);
  }} else if (event.type === "papers") {{
    showPapers();
  }} else if (event.type === "result") {{
    showResult();
  }}
}}

function tick() {{
  if (!playing) return;
  const elapsed = elapsedBeforePause + (performance.now() - startedAt);
  const seconds = elapsed / 1000;
  progressEl.style.width = Math.min(100, (elapsed / totalMs) * 100) + "%";
  for (const event of eventPlan) {{
    if (seconds >= event.at && !fired.has(event.key)) {{
      fired.add(event.key);
      executeEvent(event);
    }}
  }}
  if (elapsed < totalMs) {{
    raf = requestAnimationFrame(tick);
  }} else {{
    playing = false;
  }}
}}

function play() {{
  if (playing) return;
  playing = true;
  startedAt = performance.now();
  raf = requestAnimationFrame(tick);
}}

function pause() {{
  if (!playing) return;
  elapsedBeforePause += performance.now() - startedAt;
  playing = false;
  if (raf) cancelAnimationFrame(raf);
}}

function resetAll() {{
  if (raf) cancelAnimationFrame(raf);
  playing = false;
  elapsedBeforePause = 0;
  fired = new Set();
  progressEl.style.width = "0%";
  chatArea.innerHTML = "";
  fakeInput.textContent = "正在等待用户输入…";
  document.getElementById("summary").style.display = "none";
  document.getElementById("summary").innerHTML = "";
  document.getElementById("feed").innerHTML = '<div class="feed-item">等待进度事件...</div>';
  document.getElementById("papers").style.display = "none";
  document.getElementById("papers").innerHTML = "";
  document.getElementById("result").style.display = "none";
  document.getElementById("liveTitle").textContent = "等待访谈完成";
  document.getElementById("liveLine").textContent = "访谈信息会被转化为结构化场景，再进入自动生成流水线。";
  for (const step of demo.pipeline_steps) {{
    const card = document.getElementById(step.id);
    card.className = "step-card pending";
    card.querySelector(".step-icon").textContent = "○";
    card.querySelector(".step-detail").textContent = "等待中";
    card.querySelector(".step-result").textContent = "";
  }}
}}

document.getElementById("play").addEventListener("click", play);
document.getElementById("pause").addEventListener("click", pause);
document.getElementById("restart").addEventListener("click", () => {{
  resetAll();
  play();
}});

resetAll();
play();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=PKG_ROOT / "output" / "auto_generation_demo.html",
        help="Path for the generated HTML replay.",
    )
    args = parser.parse_args()
    data = build_demo_data()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(data), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
