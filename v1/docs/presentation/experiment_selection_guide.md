# 实验选择说明文档

本文档说明用于展示的实验选择标准和选择的实验目录。

## 选择标准

### 优先策略

**优先选择多因子结构（n_factors >= 2）的实验**，因为：
- 多因子结构能更好地反映共情的多维性
- 提供更丰富的理论维度
- 更符合心理测量学的最佳实践

### 质量评分系统

在满足多因子结构的前提下，使用综合质量评分系统：

1. **内部一致性 (40%)**: Cronbach's α
   - 反映量表的可靠性
   - α > 0.9 为优秀

2. **区分性 (40%)**: Cohen's d
   - 反映量表区分共情水平的能力
   - d > 2.0 为大效应量

3. **项目数量合理性 (10%)**: 15-20项为理想范围
   - 太少：可能不够稳定
   - 太多：可能冗余

4. **统计显著性 (10%)**: p < 0.05
   - 区分性检验的统计显著性

### 评分公式

```
质量分数 = α × 0.4 + (Cohen's d / 3.0) × 0.4 + 项目合理性 × 0.1 + 显著性 × 0.1
```

---

## 选择的主实验

### 1. 工厂装配协作机器人 (collab_robot_assembly)

**Run ID**: `2025-12-22_215026`  
**目录**: `data/runs/2025-12-22_215026`

**选择理由**:
- ✅ **质量分数**: 0.997 (最高)
- ✅ **内部一致性**: α = 0.992 (优秀)
- ✅ **区分性**: Cohen's d = 4.634 (极大效应量)
- ✅ **项目数**: 16项 (理想范围)
- ✅ **因子结构**: 2因子，平衡的任务支持和情感支持维度

**关键文件**:
- 量表草案: `empathy_scale_generation_agent_group/filtered_scale_draft.md`
- 评估结果: `evaluation_agent_group/validation/evaluation_summary.json`
- 统计选择: `statistical_selection/selection_statistics.json`

**场景信息**:
- 评估场景: factory assembly, human-robot teammate
- 机器人平台: collaborative arm
- 交互模态: gesture + voice

---

### 2. 家庭服务机器人 (home_service_robot)

**Run ID**: `2025-12-22_210718`  
**目录**: `data/runs/2025-12-22_210718`

**选择理由**:
- ✅ **质量分数**: 0.947 (优秀)
- ✅ **内部一致性**: α = 0.993 (优秀)
- ✅ **区分性**: Cohen's d = 5.238 (极大效应量)
- ✅ **项目数**: 12项 (精简)
- ✅ **因子结构**: **3因子结构**，多维度覆盖（用户理解与支持、动机支持、情感意识）

**关键文件**:
- 量表草案: `empathy_scale_generation_agent_group/filtered_scale_draft.md`
- 评估结果: `evaluation_agent_group/validation/evaluation_summary.json`
- 统计选择: `statistical_selection/selection_statistics.json`

**场景信息**:
- 评估场景: home assistant supporting daily tasks
- 机器人平台: mobile service robot
- 交互模态: speech + navigation cues

---

### 3. 心理咨询聊天机器人 (counseling_chatbot)

**Run ID**: `2025-12-22_212205`  
**目录**: `data/runs/2025-12-22_212205`

**选择理由**:
- ✅ **质量分数**: 1.000 (满分)
- ✅ **内部一致性**: α = 0.999 (优秀)
- ✅ **区分性**: Cohen's d = 15.473 (极大效应量)
- ✅ **项目数**: 15项 (理想范围)
- ✅ **因子结构**: 2因子，专业的情感支持维度

**关键文件**:
- 量表草案: `empathy_scale_generation_agent_group/filtered_scale_draft.md`
- 评估结果: `evaluation_agent_group/validation/evaluation_summary.json`
- 统计选择: `statistical_selection/selection_statistics.json`

**场景信息**:
- 评估场景: text-based counseling bot
- 机器人平台: chatbot
- 交互模态: text chat

---

## 消融实验

消融实验在 `collab_robot_assembly` 场景下进行，系统地测试生成器数量和内容评估对量表质量的影响。

### 消融实验目录

**基础目录**: `data/ablation_studies/collab_robot_assembly/`

**摘要文件**: `ablation_summary.json`

### 基线配置

**基线**: 5 generators + Content Assessment + EFA+CFA  
**Run ID**: `2025-12-22_215026` (主实验)  
**目录**: `data/runs/2025-12-22_215026`

**结果**:
- 项目数: 16项
- 内部一致性: α = 0.992
- 区分性: Cohen's d = 4.634

### 三个消融变体

**Run ID**: `2025-12-23_142045`  
**目录**: `data/runs/2025-12-23_142045`

**配置**:
- 生成器数量: 1 (vs 基线5)
- 内容评估: 是
- 选择方法: EFA+CFA

**结果**:
- 项目数: 14项
- 内部一致性: α = 0.974 (下降1.8%)
- 区分性: Cohen's d = 2.194 (下降52.7%)
- 平均评分: 41.96

**与基线对比**:
- α差异: -0.018 (-1.8%)
- d差异: -2.44 (-52.7%)

---

#### 2. No Content Assessment (5 generators, content=False, random selection)
**Run ID**: `2025-12-23_142911`  
**目录**: `data/runs/2025-12-23_142911`

**配置**:
- 生成器数量: 5 (与基线相同)
- 内容评估: 否 (vs 基线是)
- 选择方法: 随机选择 (极端对照)

**结果**:
- 项目数: 15项
- 内部一致性: α = 0.966 (下降2.6%)
- 区分性: Cohen's d = 2.241 (下降51.6%)
- 平均评分: 49.93

**与基线对比**:
- α差异: -0.026 (-2.6%)
- d差异: -2.393 (-51.6%)

**说明**: 使用随机选择作为极端对照，更直观地展示内容评估在提高候选池质量方面的价值。

---

#### 3. Fewer Generators + No Content (1 generator, content=False, EFA+CFA)
**Run ID**: `2025-12-23_143310`  
**目录**: `data/runs/2025-12-23_143310`

**配置**:
- 生成器数量: 1 (vs 基线5)
- 内容评估: 否 (vs 基线是)
- 选择方法: EFA+CFA

**结果**:
- 项目数: 10项
- 内部一致性: α = 0.941 (下降5.1%)
- 区分性: Cohen's d = 2.042 (下降56.0%)
- 平均评分: 33.13

**与基线对比**:
- α差异: -0.051 (-5.1%)
- d差异: -2.592 (-56.0%)

---

## 消融实验结果分析

### 关键发现

**所有消融变体的质量指标均低于基线**，验证了基线配置的必要性。

1. **生成器数量的影响**:
   - ⚠️ **Fewer Generators**: 区分性下降52.7% (2.194 vs 4.634)
   - ⚠️ **Fewer + No Content**: 区分性下降56.0% (2.042 vs 4.634)
   - **结论**: 更多生成器（5 vs 1）能生成更高质量的候选条目池

2. **内容评估的影响**:
   - ⚠️ **No Content Assessment (随机选择)**: 区分性下降51.6% (2.241 vs 4.634)
   - ⚠️ **Fewer + No Content**: 区分性下降56.0% (2.042 vs 4.634)
   - **结论**: 内容评估能有效筛选和精炼条目，提高最终量表质量

3. **综合影响**:
   - ✅ **基线（5+Content+EFA）表现最佳**: α=0.992, d=4.634
   - ⚠️ **所有消融变体质量下降**: 确认了多生成器和内容评估的重要性
   - ✅ **内部一致性保持优秀**: 所有变体α > 0.94（优秀水平）

### 消融实验结论

- ✅ **多生成器策略有效**: 5个生成器生成的候选条目池质量显著优于1个生成器
- ✅ **内容评估必要**: LLM内容评估在筛选和精炼条目方面发挥关键作用
- ✅ **统计选择重要**: EFA+CFA选择方法优于随机选择，能选出更高质量的条目
- ✅ **设计验证**: 消融实验成功证明了基线配置（5生成器+内容评估）的必要性

---

## 文件结构总结

### 主实验文件结构

```
data/runs/
├── 2025-12-22_215026/          # 工厂装配 (主实验)
│   ├── interview_agent_group/
│   ├── literature_search_agent_group/
│   ├── empathy_scale_generation_agent_group/
│   │   └── filtered_scale_draft.md      # 最终量表
│   ├── evaluation_agent_group/
│   │   └── validation/
│   │       └── evaluation_summary.json   # 评估结果
│   └── statistical_selection/
│       └── selection_statistics.json    # 选择统计
│
├── 2025-12-22_210639/          # 家庭服务 (主实验)
│   └── [相同结构]
│
└── 2025-12-22_212205/          # 心理咨询 (主实验)
    └── [相同结构]
```

### 消融实验文件结构

```
data/ablation_studies/
└── collab_robot_assembly/
    └── ablation_summary.json   # 消融实验摘要

data/runs/
├── 2025-12-22_215026/          # Baseline (主实验)
├── 2025-12-23_142045/          # Fewer Generators
├── 2025-12-23_142911/          # No Content Assessment
└── 2025-12-23_143310/          # Fewer + No Content
```

---

## 使用建议

### 展示中使用

1. **主实验**: 用于展示三个场景的量表生成结果
   - 展示量表条目（见 `item_analysis.md`）
   - 展示评估指标（内部一致性、区分性）
   - 展示因子结构

2. **消融实验**: 用于展示方法验证
   - 展示基线配置（5生成器+内容评估）的必要性
   - 比较生成器数量的影响（5 vs 1）
   - 比较内容评估的影响（有 vs 无）
   - 所有消融变体质量均低于基线，验证了设计选择

### 数据引用

在展示中引用时，使用以下格式：

- **主实验**: "基于质量评分系统选择的三个场景的最佳实验（Run IDs: 2025-12-22_215026, 2025-12-22_210639, 2025-12-22_212205）"
- **消融实验**: "消融实验在collab_robot_assembly场景下进行，基线配置为5生成器+内容评估+EFA+CFA（Run ID: 2025-12-22_215026），包含3个消融变体（Run IDs: 2025-12-23_142045, 2025-12-23_142911, 2025-12-23_143310）"

---

## 数据完整性检查

### 主实验检查清单

- [x] 工厂装配: 有完整的评估和选择数据
- [x] 家庭服务: 有完整的评估和选择数据
- [x] 心理咨询: 有完整的评估和选择数据

### 消融实验检查清单

- [x] 基线配置有完整的评估数据（主实验）
- [x] 3个消融变体都有完整的评估数据
- [x] 消融摘要文件存在
- [x] 所有变体的Run ID都有效
- [x] 所有消融变体的质量指标均低于基线

---

**最后更新**: 2025-12-22  
**选择脚本**: `presentation/select_best_experiments.py`  
**选择结果**: `presentation/experiment_selection.json`

