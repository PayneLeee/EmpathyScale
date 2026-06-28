# Demo · 肌肉骨骼场景代表 Run

本目录存放 **EmpathyScale 九步骤流水线** 在肌肉骨骼并肩装配场景下的代表实验记录，供仓库演示、复现与 Git 追踪使用。完整原始数据仍位于 `data/runs/`（该目录默认不纳入 Git）。

## 代表 Run

| 字段 | 值 |
|------|-----|
| Run ID | `2026-05-11_155408` |
| 场景 | 人与肌肉骨骼机器人并肩装配，共享工具架 |
| 最终题项 | 10 条（EFA 二维：Coordination Communication × Shared Workspace Consideration） |
| 内部一致性 | Cronbach's α = 0.936 |
| 区分性 | Cohen's d = 0.931（p < 0.001） |

该 run 为 `qualitative_musculoskeletal_comparison/` 与 `docs/TechRep/6.13 共情量表的生成方法.md` 附录 D 的固定主结果，在场景贴合度与条目可核验性上优于同场景其他 run 及单提示直出基线。

## 目录结构

```
demo_musculoskeletal_run/
└── 2026-05-11_155408/
    ├── interview_agent_group/          # 场景访谈摘要
    ├── literature_search_agent_group/  # 文献证据（不含 PDF 原件）
    ├── empathy_scale_generation_agent_group/
    │   ├── scale_draft.md              # 初始量表
    │   └── filtered_scale_draft.md     # EFA/CFA 筛选后定稿
    ├── evaluation_agent_group/         # Phase 1 选择与 Phase 2 验证
    ├── statistical_selection/          # EFA/CFA 统计结果
    ├── metadata.json
    └── scenario_factors.json
```

## 证据链快速入口

- 场景输入：`2026-05-11_155408/interview_agent_group/summary.json`
- 文献机制：`2026-05-11_155408/literature_search_agent_group/summary.json`
- 定稿量表：`2026-05-11_155408/empathy_scale_generation_agent_group/filtered_scale_draft.md`
- 验证指标：`2026-05-11_155408/evaluation_agent_group/validation/evaluation_summary.json`

## 说明

- 文献检索 PDF 原件（约 48 MB）未纳入 Git；结构化摘要与机制卡片已保留在 `literature_search_agent_group/` 的 JSON 中。
- 定性对照 HTML 报告见 `qualitative_musculoskeletal_comparison/output/qualitative_comparison.html`。
