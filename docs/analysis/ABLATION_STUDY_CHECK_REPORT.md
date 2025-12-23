# 消融实验完整性检查报告

生成时间: 2025-12-23

## 检查结果概览

### ❌ 新格式消融实验未完成

根据 `run_ablation_minimal.py` 的新设计，消融实验应该包含**3个变体**：
1. `fewer_generators` - 1生成器, 内容评估=True, EFA+CFA选择
2. `no_content` - 5生成器, 内容评估=False, 随机选择
3. `fewer_generators_no_content` - 1生成器, 内容评估=False, EFA+CFA选择

**状态**: ❌ 未完成
- 摘要文件应该保存在: `data/ablation_studies/collab_robot_assembly/ablation_summary.json`
- 该目录不存在，说明新格式的消融实验还没有成功运行完成

### ⚠️ 最近运行状态

#### 最新运行: `2025-12-23_140337`
- **状态**: `running` (未完成)
- **完成步骤**:
  - ✅ Step 1: Setup (interview + literature summaries)
  - ✅ Step 2-3: Scale generation
  - ✅ Step 4: Semantic deduplication
  - ⚠️ Step 5: Phase 1 Evaluation (只完成了empathic组，non_empathic组未完成)
  - ❌ Step 6: Item selection (未开始)
  - ❌ Step 7: Phase 2 Validation (未开始)

**文件夹结构**:
```
data/runs/2025-12-23_140337/
├── interview_agent_group/ ✅
├── literature_search_agent_group/ ✅
├── empathy_scale_generation_agent_group/ ✅
│   ├── scale_draft.md ✅
│   └── semantic_deduplication_stats.json ✅
├── evaluation_agent_group/
│   └── selection/
│       └── empathic/ ⚠️ (部分完成)
└── metadata.json (status: "running")
```

#### 其他未完成运行
- `2025-12-23_130451`: 只完成到Step 3（scale generation）
- `2025-12-23_125228`: 只完成到Step 5（Phase 1 empathic组）

### ✅ 旧格式消融实验已完成（在past_runs中）

旧格式的消融实验（4个变体）已经完整完成，保存在 `data/past_runs/` 目录下：

1. **single_no_content** (`2025-12-22_215303`)
   - ✅ 完整的两阶段评估
   - ✅ Phase 2验证指标: α=0.982, Cohen's d=3.174

2. **single_with_content** (`2025-12-22_215922`)
   - ✅ 完整的两阶段评估
   - ✅ Phase 2验证指标: α=0.968, Cohen's d=1.786

3. **multi_no_content** (`2025-12-22_220713`)
   - ✅ 完整的两阶段评估
   - ✅ Phase 2验证指标: α=0.99, Cohen's d=3.4

4. **multi_with_content** (`2025-12-22_222157`)
   - ✅ 完整的两阶段评估
   - ✅ Phase 2验证指标: α=0.978, Cohen's d=2.407

摘要文件: `data/past_runs/ablation_studies/collab_robot_assembly/ablation_summary.json`

## 完整运行应该包含的文件

根据 `run_ablation_minimal.py` 的设计，每个完整的消融变体运行应该包含：

```
data/runs/{run_id}/
├── interview_agent_group/
│   └── summary.json
├── literature_search_agent_group/
│   └── summary.json
├── empathy_scale_generation_agent_group/
│   ├── scale_draft.md
│   ├── filtered_scale_draft.md  ⭐ (最终量表)
│   ├── semantic_deduplication_stats.json
│   └── summary.json
├── evaluation_agent_group/
│   ├── selection/  (Phase 1)
│   │   ├── empathic/
│   │   │   ├── evaluation_summary.json
│   │   │   └── participant_level_evaluations.json
│   │   ├── non_empathic/
│   │   │   ├── evaluation_summary.json
│   │   │   └── participant_level_evaluations.json
│   │   └── combined/  (仅当使用EFA+CFA时)
│   │       ├── evaluation_summary.json
│   │       └── participant_level_evaluations.json
│   └── validation/  (Phase 2) ⭐
│       ├── evaluation_summary.json
│       └── participant_level_evaluations.json
├── statistical_selection/  (或随机选择结果)
│   ├── selection_config.json
│   ├── selection_statistics.json
│   └── [其他选择相关文件]
└── metadata.json
```

## 建议

1. **检查运行中断原因**: 最新运行 `2025-12-23_140337` 在Phase 1评估阶段中断，建议检查：
   - API调用是否失败
   - 是否有错误日志
   - 系统资源是否充足

2. **重新运行消融实验**: 如果需要完成新格式的消融实验，建议：
   - 清理未完成的运行（或移到past_runs）
   - 重新运行 `python run_ablation_minimal.py`
   - 确保3个变体都完整运行

3. **使用旧格式结果**: 如果旧格式的消融实验结果可用，可以继续使用 `data/past_runs/ablation_studies/collab_robot_assembly/ablation_summary.json`

## 结论

**新格式的消融实验未完整运行**。最近3次运行都未完成，最接近完成的是 `2025-12-23_140337`，但仍在Phase 1评估阶段中断。

旧格式的消融实验已经完整完成，保存在 `past_runs` 目录中。

