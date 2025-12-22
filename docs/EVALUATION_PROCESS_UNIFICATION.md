# 评估流程统一说明

## 概述

为了确保实验的客观性和一致性，所有run文件现在使用相同的评估流程：

1. **Phase 1 (Selection)**: 评估所有条目，用于统计筛选
2. **统计筛选**: 基于评估数据筛选最优条目
3. **Phase 2 (Validation)**: 验证筛选后的条目（或最终量表）

## 统一的评估配置

### Phase 1 (Selection) - 用于条目筛选
- **Persona**: `{scenario}_selection`
- **Participants**: 200
- **输出目录**: `evaluation_agent_group/selection/`
- **用途**: 评估所有生成的条目，用于统计筛选

### Phase 2 (Validation) - 用于最终验证
- **Persona**: `{scenario}` (基础场景名，可复用)
- **Participants**: 50
- **输出目录**: `evaluation_agent_group/validation/`
- **用途**: 验证筛选后的条目或最终量表

## 各文件实现

### 1. `run_predefined_scenarios.py` (核心流程)
**流程**:
- Step 5: Phase 1评估（200个_selection persona）
- Step 6: 统计筛选
- Step 7: Phase 2验证（50个基础场景名persona）

**状态**: ✅ 已实现

### 2. `run_ablation_minimal.py` (消融实验)
**流程**:
- Step 5: Phase 1评估（200个_selection persona）
- Step 6: 统计筛选
- Step 7: Phase 2验证（50个基础场景名persona）

**状态**: ✅ 已更新为统一流程

**关键变化**:
- 从单次评估（10个participants）改为两阶段评估
- 添加统计筛选步骤
- 更新摘要生成以包含Phase 1和Phase 2结果

### 3. `run_baseline_comparison.py` (基线对比)
**流程**:
- 直接使用Phase 2配置（50个基础场景名persona）
- 基线量表（PETS和RoPE）不需要统计筛选，直接验证

**状态**: ✅ 已更新为使用Phase 2配置

**关键变化**:
- 明确使用50个participants（validation阶段标准）
- 使用基础场景名persona（与validation阶段一致）
- 确保基线量表与生成量表使用相同的验证persona

## Persona复用机制

### Selection Persona
- **命名**: `{scenario}_selection`
- **数量**: 200
- **用途**: 专门用于条目筛选
- **独立性**: 每个场景独立，不与其他场景共享

### Validation Persona
- **命名**: `{scenario}` (基础场景名)
- **数量**: 50
- **用途**: 验证最终量表
- **复用性**: 
  - 生成量表的Phase 2验证
  - 基线量表（PETS、RoPE）的评估
  - 确保所有量表在同一场景下使用相同的验证persona

## 统计筛选配置

**默认参数**:
- **策略**: `rating_threshold`
- **min_mean_rating**: 60.0
- **max_std**: 30.0

**输出**:
- `statistical_selection/selection_config.json` - 筛选配置
- `statistical_selection/selected_item_ids.json` - 选中的条目ID
- `statistical_selection/selection_statistics.json` - 筛选统计信息

## 数据流程对比

### 修改前（不一致）
```
run_predefined_scenarios.py: 单次评估（20个participants）
run_ablation_minimal.py: 单次评估（10个participants）
run_baseline_comparison.py: 单次评估（加载的persona数量）
```

### 修改后（统一）
```
所有文件:
  Phase 1: 200个_selection persona → 统计筛选
  Phase 2: 50个基础场景名persona → 最终验证
```

## 实验客观性保证

### 1. 一致的评估标准
- 所有生成量表使用相同的两阶段评估流程
- 所有基线量表使用与生成量表相同的验证persona

### 2. 独立的筛选数据
- Selection阶段使用独立的persona集合
- 确保筛选数据不影响最终验证

### 3. 可复用的验证persona
- 所有量表（生成和基线）使用相同的验证persona
- 确保对比的公平性

## 输出结构

### 消融实验
```
data/runs/{run_id}/
├── evaluation_agent_group/
│   ├── selection/
│   │   └── evaluation_summary.json  # Phase 1
│   └── validation/
│       └── evaluation_summary.json   # Phase 2
└── statistical_selection/
    └── selection_statistics.json

data/ablation_studies/{scenario}/
└── ablation_summary.json  # 包含Phase 1和Phase 2结果
```

### 基线对比
```
data/baseline_comparison/{scenario}/
├── PETS/
│   └── evaluation_summary.json  # 使用50个validation persona
├── RoPE/
│   └── evaluation_summary.json  # 使用50个validation persona
└── comparison_report.json
```

## 验证清单

- [x] `run_predefined_scenarios.py` 使用两阶段评估
- [x] `run_ablation_minimal.py` 使用两阶段评估
- [x] `run_baseline_comparison.py` 使用Phase 2配置（50个participants）
- [x] 所有文件使用相同的persona命名规则
- [x] 所有文件使用相同的统计筛选参数
- [x] 摘要生成包含两阶段评估结果

## 注意事项

1. **基线量表不需要统计筛选**: PETS和RoPE已经是最终量表，直接使用Phase 2验证
2. **Persona复用**: 确保先运行`run_predefined_scenarios.py`生成validation persona，再运行基线对比
3. **消融实验**: 每个变体都独立运行完整的两阶段流程，确保公平对比




