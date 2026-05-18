# 2026-05-18 本轮更新记录（定性对照报告）

## 本轮目标
- 精简单提示直出的提示词，移除带量表设计引导性质的硬约束。
- 重新生成 5 次单提示直出结果，并维持同样的 HTML 报告结构进行对照分析。
- 强化“按缺点组织”的定性分析展示，而非仅强调条目数量。

## 关键变更
- 新增 `direct_llm_prompt.py`，统一维护单提示模板。
- 更新 `run_direct_llm_baseline.py`：
  - 改为读取统一模板。
  - 运行时保存 `direct_llm_runs/prompt_used.txt` 与 `direct_llm_runs/prompt_meta.json`。
- 更新 `build_report.py`：
  - 报告数据中加入 `direct_llm_prompt`，供 HTML 附录展示完整提示词与参数。
  - 自动写回最新 `prompt_used.txt`，避免附录与当前模板不一致。
  - 将“单提示直出”分析重写为“可核验性与构念漂移”为主，而非“条目明显过多”。
- 更新 `report_render.py`：
  - 报告末尾新增“附录·单提示直出提示词”区块，展示模型、temperature、seeds 与完整提示词。
- 更新翻译与解析：
  - `qmc_translate.py` 增强字符串归一化匹配，降低英文示例漏翻译概率。
  - `qmc_utils.py` 对扁平 `## Items` 结构设置默认维度标签，避免显示 `Unknown`。

## 单提示模板（当前）
- 开头保留场景输入 + 一个“仅作结构示例”的 Markdown 输出样式。
- 已移除：
  - “Use ONLY this scenario text. Do not cite papers or external scales.”
  - “2-4 dimensions / at least 14 items / 必须以 The robot 开头”等组织性约束。

## 重跑结果（direct_llm_runs/manifest.json）
- `run_01`: 10 条
- `run_02`: 10 条
- `run_03`: 12 条
- `run_04`: 15 条
- `run_05`: 12 条

## 报告现状
- 输出文件：`output/qualitative_comparison.html`
- 报告结构保持不变（场景、定性分析、三份量表、对照表、相似主题、稳定性、证据链）。
- “单提示直出”分析已按具体问题组织：
  - 可核验性问题（读心式判断）
  - 构念漂移问题（整体印象化表述）
  - 稳定性问题（一次成稿、缺少筛选与可比性）
