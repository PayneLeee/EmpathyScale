"""HTML rendering for qualitative comparison report."""
from __future__ import annotations

import html
from typing import Any, Dict, List

STABILITY_QUALITATIVE = [
    "五次单提示直出的维度命名不一致（如「意图沟通」「空间协调」「碰后响应」等混用）。",
    "条目数量与维度划分随每次生成变化，未经文献检索、模拟评估与统计筛选。",
    "主观选定最差样本（run_05）含「只能推断意图」「像人类队友」等难以在现场核实的表述。",
]


def render_html(data: Dict[str, Any]) -> str:
    def esc(s: str) -> str:
        return html.escape(str(s))

    def item_list(items: List[Dict[str, str]], dim_key: str = "dimension") -> str:
        if not items:
            return "<p class='muted'>（无条目）</p>"
        by_dim: Dict[str, List[str]] = {}
        for it in items:
            by_dim.setdefault(it.get(dim_key, "—"), []).append(it["item_text"])
        parts = []
        for dim, texts in by_dim.items():
            lis = "".join(f"<li>{esc(t)}</li>" for t in texts)
            parts.append(f"<h4>{esc(dim)}</h4><ul>{lis}</ul>")
        return "".join(parts)

    nine_items = data["nine_step"]["items"]
    pets_items = data["pets"]["items"]
    worst = data["direct_llm"].get("worst") or {}
    best = data["direct_llm"].get("best") or {}

    rows_html = ""
    for row in data["comparison_rows"]:
        rows_html += (
            f"<tr><td>{esc(row['theme'])}</td>"
            f"<td class='cell-good'>{esc(row['nine_step_good'])}</td>"
            f"<td class='cell-bad'>{esc(row['contrast_bad'])}"
            f"<br><span class='tag'>{esc(row['contrast_source'])}</span></td>"
            f"<td>{esc(row['why'])}</td></tr>"
        )

    pairs_html = ""
    for p in data["similar_pairs"]:
        pairs_html += (
            f'<div class="pair-card">'
            f"<h3>{esc(p['title'])}</h3>"
            f'<div class="pair-grid">'
            f"<div><label>九步骤</label><p>{esc(p['nine_step'])}</p></div>"
            f"<div><label>PETS</label><p>{esc(p['pets'])}</p></div>"
            f"<div><label>单提示直出</label><p>{esc(p['direct'])}</p></div>"
            f"</div>"
            f'<p class="note">{esc(p["note"])}</p>'
            f"</div>"
        )
    stability_bullets = "".join(
        f"<li>{esc(b)}</li>"
        for b in (data.get("stability_qualitative") or STABILITY_QUALITATIVE)
    )

    evidence = "".join(
        f'<li><code>{esc(e["path"])}</code></li>' for e in data["evidence_links"]
    )

    worst_id = worst.get("run_id", "—")
    best_id = best.get("run_id", "—")

    scen = data.get("scenario_display") or {}
    scenario_rows = "".join(
        f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in scen.get("rows", [])
    )
    mech_list = "".join(f"<li>{esc(m)}</li>" for m in scen.get("mechanisms", []))
    risk_list = "".join(f"<li>{esc(r)}</li>" for r in scen.get("risk_flags", []))

    analysis_html = ""
    for block in data.get("deep_analysis") or []:
        pts = "".join(f"<li>{esc(p)}</li>" for p in block.get("points", []))

        ex_parts: List[str] = []
        for grp in block.get("example_groups") or []:
            entries = "".join(
                f'<p class="ex-item"><span class="tag">{esc(e.get("label", ""))}</span> '
                f'{esc(e.get("item_text", ""))}</p>'
                for e in grp.get("entries", [])
            )
            ex_parts.append(
                f'<div class="ex-card">'
                f'<p class="ex-issue">{esc(grp.get("issue", ""))}</p>{entries}'
                f"</div>"
            )
        for ex in block.get("examples") or []:
            ex_parts.append(
                f'<div class="ex-card">'
                f'<span class="tag">{esc(ex.get("label") or ex.get("source", ""))}</span>'
                f'<p class="ex-item">{esc(ex.get("item_text", ""))}</p>'
                f'<p class="ex-issue">{esc(ex.get("issue", ""))}</p>'
                f"</div>"
            )
        examples_block = (
            f'<div class="examples">{"".join(ex_parts)}</div>' if ex_parts else ""
        )

        mech_html = ""
        for ref in block.get("mechanism_refs") or []:
            papers = ref.get("papers") or []
            paper_txt = "；".join(esc(p) for p in papers) if papers else "（见文献检索摘要）"
            mech_html += (
                f'<li><strong>{esc(ref.get("mechanism", ""))}</strong>：{esc(ref.get("items", ""))}'
                f'<br><span class="lit-note">文献：{paper_txt}</span></li>'
            )
        mech_block = f'<ul class="mech-refs">{mech_html}</ul>' if mech_html else ""

        hi_parts = []
        for h in block.get("nine_highlights") or []:
            hi_parts.append(
                f'<div class="highlight-row">'
                f'<span class="tag">{esc(h.get("theme", ""))}</span>'
                f'<p class="ex-item">{esc(h.get("item_text", ""))}</p>'
                f'<p class="lit-note">{esc(h.get("note", ""))}</p>'
                f"</div>"
            )
        hi_block = f'<div class="highlights">{"".join(hi_parts)}</div>' if hi_parts else ""

        analysis_html += (
            f'<div class="analysis-block">'
            f"<h3>{esc(block.get('heading', ''))}</h3>"
            f'<p class="analysis-summary">{esc(block.get("summary", ""))}</p>'
            f"<ul>{pts}</ul>{mech_block}{hi_block}{examples_block}</div>"
        )

    source_run = esc(scen.get("source_run", ""))

    prompt_block = ""
    prompt_info = data.get("direct_llm_prompt") or {}
    if prompt_info.get("filled"):
        seeds = prompt_info.get("seeds") or []
        seeds_txt = ", ".join(str(s) for s in seeds) if seeds else "—"
        prompt_block = f"""
  <section>
    <h2>附录 · 单提示直出提示词</h2>
    <p class="muted">五次单提示直出（{esc(worst_id)} / {esc(best_id)} 等）均使用同一段提示词；场景正文与上文「场景设定」同源。
    模型：<code>{esc(prompt_info.get('model', '—'))}</code> · temperature {esc(prompt_info.get('temperature', '—'))} · seeds [{esc(seeds_txt)}]</p>
    <details open>
      <summary>完整提示词（英文，与发送给模型一致）</summary>
      <pre class="prompt-block">{esc(prompt_info['filled'])}</pre>
    </details>
    <p class="muted">存档路径：<code>{esc(prompt_info.get('source_file', ''))}</code></p>
  </section>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>肌肉骨骼场景 · 量表定性对照</title>
<style>
  :root {{
    --bg: #f6f7f9; --card: #fff; --text: #1a1a1a; --muted: #666;
    --good: #0d6b3a; --good-bg: #e8f5ee; --bad: #9b2335; --bad-bg: #fdecef;
    --accent: #2563eb; --border: #e5e7eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Segoe UI", system-ui, sans-serif; margin: 0; background: var(--bg); color: var(--text); line-height: 1.5; }}
  .wrap {{ max-width: 1200px; margin: 0 auto; padding: 24px 20px 48px; }}
  h1 {{ font-size: 1.35rem; margin: 0 0 8px; }}
  .subtitle {{ color: var(--muted); margin-bottom: 20px; font-size: 0.95rem; }}
  section {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px 22px; margin-bottom: 20px; }}
  h2 {{ font-size: 1.05rem; margin: 0 0 14px; border-bottom: 2px solid var(--accent); padding-bottom: 6px; }}
  .scenario-table th {{ width: 140px; background: #f8fafc; font-weight: 600; }}
  .scenario-sub h4 {{ margin: 0 0 6px; font-size: 0.85rem; color: var(--muted); }}
  .analysis-block {{ margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px dashed var(--border); }}
  .analysis-block:last-child {{ border-bottom: none; }}
  .analysis-summary {{ font-size: 0.9rem; color: #333; margin: 0 0 8px; }}
  .analysis-block ul {{ margin: 0 0 10px; padding-left: 1.2rem; font-size: 0.88rem; }}
  .ex-card {{ background: #fafbfc; border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; margin-top: 8px; }}
  .ex-item {{ margin: 6px 0 4px; font-size: 0.86rem; }}
  .ex-issue {{ margin: 0 0 6px; font-size: 0.82rem; color: var(--bad); font-weight: 600; }}
  .lit-note {{ font-size: 0.8rem; color: #555; margin: 4px 0 0; }}
  .mech-refs {{ margin: 10px 0; padding-left: 1.2rem; font-size: 0.84rem; }}
  .highlights {{ margin-top: 10px; }}
  .highlight-row {{ background: var(--good-bg); border: 1px solid #c8e6d4; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; }}
  .cols3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
  @media (max-width: 900px) {{ .cols3 {{ grid-template-columns: 1fr; }} }}
  .col h3 {{ font-size: 0.9rem; margin: 0 0 8px; color: var(--accent); }}
  .col ul {{ margin: 0; padding-left: 1.2rem; font-size: 0.88rem; }}
  .col h4 {{ font-size: 0.8rem; margin: 12px 0 4px; color: var(--muted); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th, td {{ border: 1px solid var(--border); padding: 10px; vertical-align: top; text-align: left; }}
  th {{ background: #f0f4ff; }}
  .cell-good {{ background: var(--good-bg); }}
  .cell-bad {{ background: var(--bad-bg); }}
  .tag {{ font-size: 0.75rem; color: var(--muted); }}
  .pair-card {{ border: 1px solid var(--border); border-radius: 8px; padding: 14px; margin-bottom: 12px; background: #fafbfc; }}
  .pair-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }}
  @media (max-width: 800px) {{ .pair-grid {{ grid-template-columns: 1fr; }} }}
  .pair-grid label {{ font-size: 0.72rem; font-weight: 600; color: var(--muted); }}
  .pair-grid p {{ margin: 4px 0 0; font-size: 0.86rem; }}
  .note {{ margin: 10px 0 0; font-size: 0.85rem; color: #444; }}
  details {{ margin-top: 12px; }}
  .muted {{ color: var(--muted); font-size: 0.85rem; }}
  .badge {{ display: inline-block; background: #eef2ff; color: var(--accent); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-left: 6px; }}
  .link-row {{ margin: -8px 0 18px; font-size: 0.9rem; }}
  .link-row a {{ color: var(--accent); font-weight: 600; }}
  .prompt-block {{ background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; margin: 10px 0; font-size: 0.8rem; line-height: 1.45; white-space: pre-wrap; word-break: break-word; max-height: 480px; overflow: auto; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>{esc(data['scenario_label'])}</h1>
  <p class="subtitle">九步骤最终量表 · 单提示直出（{esc(worst_id)} 最差 / {esc(best_id)} 最好）· PETS 基线 · run {source_run}</p>
  <p class="link-row"><a href="auto_generation_demo.html">查看自动生成过程 HTML 视频</a></p>

  <section>
    <h2>场景设定（本报告评价对象）</h2>
    <table class="scenario-table">{scenario_rows}</table>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:14px;font-size:0.88rem;">
      <div><h4 class="scenario-sub">场景共情机制</h4><ul>{mech_list}</ul></div>
      <div><h4 class="scenario-sub">风险与约束</h4><ul>{risk_list}</ul></div>
    </div>
  </section>

  <section>
    <h2>1 · 定性分析：为何九步骤量表更适合本场景</h2>
    {analysis_html}
  </section>

  <section>
    <h2>2 · 三份量表（最终结果）</h2>
    <div class="cols3">
      <div class="col"><h3>九步骤 <span class="badge">{len(nine_items)} 条</span></h3>{item_list(nine_items)}</div>
      <div class="col">
        <h3>单提示 <span class="badge">最差 {esc(worst_id)}</span></h3>{item_list(worst.get('items', []))}
        <h3 style="margin-top:14px">单提示 <span class="badge">最好 {esc(best_id)}</span></h3>{item_list(best.get('items', []))}
      </div>
      <div class="col"><h3>PETS <span class="badge">{len(pets_items)} 条</span></h3>{item_list(pets_items)}</div>
    </div>
  </section>

  <section>
    <h2>3 · 恰当 / 不恰当条目对照</h2>
    <table><thead><tr><th>主题</th><th>九步骤（恰当）</th><th>对照（不恰当）</th><th>差异</th></tr></thead>
    <tbody>{rows_html}</tbody></table>
    <p class="muted">{esc(data['direct_llm'].get('selection_note', ''))}</p>
  </section>

  <section><h2>4 · 相似主题并排</h2>{pairs_html}</section>
  <section><h2>5 · 单提示五次定性小结</h2><ul>{stability_bullets}</ul></section>
  <section><details><summary>九步骤证据链（收起）</summary><ul>{evidence}</ul></details></section>
{prompt_block}
</div>
</body>
</html>"""
