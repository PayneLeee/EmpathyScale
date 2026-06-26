# 肌肉骨骼场景 · 定性对照（九步骤 vs 单提示直出 vs PETS）

## 用途
导师汇报用：直观对比三种量表来源，突出九步骤条目在场景贴合度上的优势。

## 目录
- `data/` — 固定输入与九步骤/PETS 结构化数据
- `direct_llm_runs/` — 同模型单提示直出 5 次原始 Markdown
- `output/` — 生成的 HTML 报告与 `comparison_data.json`
- `run_direct_llm_baseline.py` — 运行 5 次直出实验
- `build_report.py` — 生成 HTML（含恰当/不恰当条目对照）

## 固定主结果
- 九步骤量表：`2026-05-11_155408` → `data/nine_step_scale.json`（10 条）
- 单提示直出：主观选定 **最差 run_05**、**最好 run_02**（5 次全保存在 `direct_llm_runs/`）
- PETS：10 条 → `data/pets_items.json`

## 报告
打开 [`output/qualitative_comparison.html`](output/qualitative_comparison.html)（全文中文条目，无启发分）

翻译缓存：`data/zh_strings.json`（缺译时 `build_report.py` 会调用同模型补全）

## 命令
```bash
# 项目根目录
python qualitative_musculoskeletal_comparison/run_direct_llm_baseline.py
python qualitative_musculoskeletal_comparison/build_report.py
```
打开 `qualitative_musculoskeletal_comparison/output/qualitative_comparison.html`
