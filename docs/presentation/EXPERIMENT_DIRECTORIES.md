# 实验目录快速参考

## 主实验目录

### 1. 工厂装配协作机器人 (collab_robot_assembly)
**Run ID**: `2025-12-22_215026`  
**完整路径**: `data/runs/2025-12-22_215026`

**关键文件**:
- 量表草案: `empathy_scale_generation_agent_group/filtered_scale_draft.md`
- 评估结果: `evaluation_agent_group/validation/evaluation_summary.json`
- 统计选择: `statistical_selection/selection_statistics.json`
- 访谈摘要: `interview_agent_group/summary.json`

---

### 2. 家庭服务机器人 (home_service_robot)
**Run ID**: `2025-12-22_210718`  
**完整路径**: `data/runs/2025-12-22_210718`

**关键文件**:
- 量表草案: `empathy_scale_generation_agent_group/filtered_scale_draft.md`
- 评估结果: `evaluation_agent_group/validation/evaluation_summary.json`
- 统计选择: `statistical_selection/selection_statistics.json`
- EFA/CFA结果: `statistical_selection/efa_cfa_results.json`
- 访谈摘要: `interview_agent_group/summary.json`

---

### 3. 心理咨询聊天机器人 (counseling_chatbot)
**Run ID**: `2025-12-22_212205`  
**完整路径**: `data/runs/2025-12-22_212205`

**关键文件**:
- 量表草案: `empathy_scale_generation_agent_group/filtered_scale_draft.md`
- 评估结果: `evaluation_agent_group/validation/evaluation_summary.json`
- 统计选择: `statistical_selection/selection_statistics.json`
- 访谈摘要: `interview_agent_group/summary.json`

---

## 消融实验目录

### 基础目录
**路径**: `data/ablation_studies/collab_robot_assembly/`  
**摘要文件**: `ablation_summary.json`

### 基线配置

**基线**: 5 generators + Content Assessment + EFA+CFA  
**Run ID**: `2025-12-22_215026`  
**路径**: `data/runs/2025-12-22_215026`
- α = 0.992, Cohen's d = 4.634, 16 items

### 三个消融变体

#### 1. Fewer Generators (1 vs 5 generators, content=True, EFA+CFA)
**Run ID**: `2025-12-23_142045`  
**路径**: `data/runs/2025-12-23_142045`
- α = 0.974, Cohen's d = 2.194, 14 items

#### 2. No Content Assessment (5 generators, content=False, random selection)
**Run ID**: `2025-12-23_142911`  
**路径**: `data/runs/2025-12-23_142911`
- α = 0.966, Cohen's d = 2.241, 15 items

#### 3. Fewer Generators + No Content (1 generator, content=False, EFA+CFA)
**Run ID**: `2025-12-23_143310`  
**路径**: `data/runs/2025-12-23_143310`
- α = 0.941, Cohen's d = 2.042, 10 items

---

## 快速访问命令

### 查看主实验量表
```bash
# 工厂装配
cat data/runs/2025-12-22_215026/empathy_scale_generation_agent_group/filtered_scale_draft.md

# 家庭服务
cat data/runs/2025-12-22_210639/empathy_scale_generation_agent_group/filtered_scale_draft.md

# 心理咨询
cat data/runs/2025-12-22_212205/empathy_scale_generation_agent_group/filtered_scale_draft.md
```

### 查看评估结果
```bash
# 工厂装配
cat data/runs/2025-12-22_215026/evaluation_agent_group/validation/evaluation_summary.json

# 家庭服务
cat data/runs/2025-12-22_210718/evaluation_agent_group/validation/evaluation_summary.json

# 心理咨询
cat data/runs/2025-12-22_212205/evaluation_agent_group/validation/evaluation_summary.json
```

### 查看消融实验摘要
```bash
cat data/ablation_studies/collab_robot_assembly/ablation_summary.json
```

---

## 文件结构说明

每个主实验的目录结构：

```
data/runs/{run_id}/
├── interview_agent_group/
│   └── summary.json                    # 场景信息
├── literature_search_agent_group/
│   └── summary.json                    # 文献搜索结果
├── empathy_scale_generation_agent_group/
│   ├── scale_draft.md                  # 原始量表草案
│   ├── filtered_scale_draft.md         # 最终精选量表 ⭐
│   └── summary.json                    # 生成摘要
├── evaluation_agent_group/
│   ├── selection/                      # Phase 1评估
│   │   ├── empathic/
│   │   ├── non_empathic/
│   │   └── combined/
│   └── validation/                     # Phase 2验证
│       ├── evaluation_summary.json     # 评估摘要 ⭐
│       └── participant_level_evaluations.json
└── statistical_selection/
    ├── selection_statistics.json       # 选择统计 ⭐
    ├── selected_item_ids.json          # 选择的项目ID
    └── efa_cfa_results.json            # 因子分析结果
```

⭐ = 展示中最重要的文件

---

## 数据引用格式

在展示或报告中引用时：

**主实验**:
- "基于多因子优先策略和质量评分系统选择的三个场景的最佳实验（Run IDs: 2025-12-22_215026, 2025-12-22_210718, 2025-12-22_212205）"

**消融实验**:
- "消融实验在collab_robot_assembly场景下进行，包含4个变体（Run IDs: 2025-12-22_215303, 2025-12-22_215922, 2025-12-22_220713, 2025-12-22_222157）"

---

**最后更新**: 2025-12-22

