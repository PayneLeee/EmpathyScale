# 实验执行计划

根据 `ProjectRequirements/FINALproposal.txt` 和 `ProjectRequirements/GuildLine.txt` 的要求，以下是需要依次进行的实验和分析。

## Proposal要求总结

### 核心要求（Section 3 & 5）

1. **生成2-3个场景特定的共情量表**
   - 场景：robot teammate (collab_robot_assembly), home robot (home_service_robot), counseling agent (counseling_chatbot)
   - 使用统一的两阶段评估流程（Phase 1 selection + 统计筛选 + Phase 2 validation）

2. **消融实验**
   - Single-agent vs multi-agent generation
   - With vs without content refinement
   - 在collab_robot_assembly场景运行

3. **基线对比**
   - 评估PETS和RoPE基线量表
   - 使用与生成量表相同的validation persona（50个participants）
   - 在3个场景都进行评估

4. **Metrics分析**
   - Mean clarity（平均清晰度）
   - Contextual relevance（情境相关性）
   - Differences across scenarios（跨场景差异）
   - Stability across repeated simulation runs（重复运行的稳定性）

## 实验执行顺序

### Phase 1: 核心实验运行

#### 实验1: 运行消融实验
**脚本**: `run_ablation_minimal.py`

**目的**: 
- 比较single vs multi-agent, with vs without content assessment
- 使用统一的两阶段评估流程

**执行**:
```bash
python run_ablation_minimal.py
```

**输出**:
- `data/ablation_studies/collab_robot_assembly/ablation_summary.json`
- 4个变体的运行结果（每个包含Phase 1和Phase 2评估）

**检查点**:
- [ ] 4个变体都成功运行
- [ ] 每个变体都有Phase 1和Phase 2评估结果
- [ ] 消融摘要包含Phase 2评分对比

---

#### 实验2: 运行核心场景实验
**脚本**: `run_predefined_scenarios.py`

**目的**:
- 生成3个场景特定的共情量表
- 使用统一的两阶段评估流程和统计筛选

**执行**:
```bash
python run_predefined_scenarios.py
```

**输出**:
- 3个场景的运行结果（每个包含Phase 1、统计筛选、Phase 2）
- `data/runs/{run_id}/` - 每个场景的完整数据

**检查点**:
- [ ] 3个场景都成功运行
- [ ] 每个场景都有Phase 1评估（200个_selection persona）
- [ ] 每个场景都有统计筛选结果
- [ ] 每个场景都有Phase 2验证（50个基础场景名persona）
- [ ] 生成了筛选后的量表draft

---

#### 实验3: 运行基线对比
**脚本**: `run_baseline_comparison.py`

**目的**:
- 评估PETS和RoPE基线量表
- 使用与生成量表相同的validation persona（50个participants）

**执行**:
```bash
python run_baseline_comparison.py
```

**前提条件**:
- 必须先运行 `run_predefined_scenarios.py`，生成validation persona（50个基础场景名persona）

**输出**:
- `data/baseline_comparison/{scenario}/PETS/` - PETS评估结果
- `data/baseline_comparison/{scenario}/RoPE/` - RoPE评估结果
- `data/baseline_comparison/{scenario}/comparison_report.json` - 对比报告

**检查点**:
- [ ] 3个场景的PETS和RoPE都成功评估
- [ ] 使用50个participants（与validation阶段一致）
- [ ] 生成了对比报告

---

### Phase 2: 数据分析

#### 分析1: 消融实验结果分析
**数据源**: `data/ablation_studies/collab_robot_assembly/ablation_summary.json`

**分析内容**:
- 比较4个变体的Phase 2评分
- 比较条目数量（原始 vs 筛选后）
- 分析content assessment的影响
- 分析single vs multi-agent的影响

**输出**: 包含在综合分析报告中

---

#### 分析2: 跨场景差异分析
**数据源**: `data/runs/` 中3个场景的运行结果

**分析内容**:
- 比较3个场景的Phase 2评分
- 比较条目数量和维度分布
- 分析场景特异性（contextual relevance）
- 比较筛选前后的变化

**输出**: 包含在综合分析报告中

---

#### 分析3: 基线对比分析
**数据源**: `data/baseline_comparison/` 中3个场景的对比报告

**分析内容**:
- 生成量表 vs PETS vs RoPE的评分对比
- 各场景下的基线表现
- 生成量表的相对优势

**输出**: 包含在综合分析报告中

---

#### 分析4: 生成综合分析报告
**脚本**: `analyze_all_results.py`

**目的**:
- 汇总所有实验结果
- 生成JSON和Markdown格式的综合报告

**执行**:
```bash
python analyze_all_results.py
```

**输出**:
- `data/analysis/comprehensive_report.json`
- `data/analysis/comprehensive_report.md`

**检查点**:
- [ ] 报告包含消融实验结果
- [ ] 报告包含跨场景分析
- [ ] 报告包含基线对比
- [ ] 报告包含所有关键metrics

---

## 执行检查清单

### 实验运行
- [ ] **实验1**: 运行消融实验（使用新的两阶段评估流程）
- [ ] **实验2**: 运行核心场景实验（3个场景，使用新的两阶段评估流程）
- [ ] **实验3**: 运行基线对比（使用50个validation persona）

### 数据分析
- [ ] **分析1**: 分析消融实验结果
- [ ] **分析2**: 分析跨场景差异
- [ ] **分析3**: 分析基线对比结果
- [ ] **分析4**: 生成综合分析报告

### 结果验证
- [ ] 验证所有实验都使用了统一的评估流程
- [ ] 验证persona配置正确（selection: 200个，validation: 50个）
- [ ] 验证统计筛选已应用
- [ ] 验证所有metrics都已计算

## 关键Metrics（Proposal要求）

根据Proposal Section 5，需要报告的metrics：

1. **Mean clarity** - 平均清晰度
   - 来源：Phase 2评估结果中的overall_mean_rating

2. **Contextual relevance** - 情境相关性
   - 来源：跨场景对比分析
   - 方法：比较不同场景下的评分差异

3. **Differences across scenarios** - 跨场景差异
   - 来源：3个场景的Phase 2评分对比
   - 方法：统计分析场景间的差异

4. **Stability across repeated simulation runs** - 重复运行的稳定性
   - 来源：多次运行的结果（如果需要）
   - 方法：计算评分的一致性

5. **Ablation results** - 消融实验结果
   - Single-agent vs multi-agent
   - With vs without content refinement

6. **Baseline comparison** - 基线对比
   - 生成量表 vs PETS vs RoPE

## 注意事项

1. **执行顺序很重要**:
   - 必须先运行 `run_predefined_scenarios.py` 生成validation persona
   - 然后才能运行 `run_baseline_comparison.py`（需要复用validation persona）

2. **数据一致性**:
   - 所有实验都使用统一的两阶段评估流程
   - 确保persona配置正确

3. **时间估算**:
   - 消融实验：4个变体 × 约30-60分钟 = 2-4小时
   - 核心场景实验：3个场景 × 约30-60分钟 = 1.5-3小时
   - 基线对比：3个场景 × 2个基线 × 约10-20分钟 = 1-2小时
   - 综合分析：约10-30分钟
   - **总计**: 约4.5-9.5小时

4. **Presentation准备**:
   - 根据GuildLine，需要准备7分钟演示
   - 重点展示：Experiments & Results, Key Insights
   - 使用综合分析报告作为数据源

## 当前状态检查

### 已有数据状态
- ⚠️ `data/ablation_studies/collab_robot_assembly/ablation_summary.json` - **旧版消融结果**
  - 使用10个participants（单阶段评估）
  - **需要重新运行**以使用新的两阶段评估流程（20 selection + 50 validation）
  
- ⚠️ `data/baseline_comparison/` - **基线对比结果**
  - 可能使用旧的persona配置
  - **需要重新运行**以使用50个validation persona

- ❓ `data/runs/` - **核心场景实验结果**
  - 需要检查是否使用了新的两阶段评估流程
  - 如果只有单阶段评估，**需要重新运行**

### 需要重新运行的原因
1. **消融实验**: 旧结果使用10个participants，新流程需要200+50个participants
2. **核心场景实验**: 需要确认是否使用了新的两阶段评估和统计筛选
3. **基线对比**: 需要确保使用50个validation persona（与生成量表的validation阶段一致）

### 判断是否需要重新运行的方法
检查运行结果目录结构：
- ✅ **新流程**: `data/runs/{run_id}/evaluation_agent_group/selection/` 和 `validation/` 都存在
- ❌ **旧流程**: 只有 `data/runs/{run_id}/evaluation_agent_group/evaluation_summary.json`

## 建议执行顺序

### 推荐顺序（确保数据一致性）

1. **第一步**: 运行 `run_predefined_scenarios.py`（生成validation persona）
   - 生成3个场景的validation persona（50个participants）
   - 这些persona将被基线对比复用
   - **预计时间**: 1.5-3小时

2. **第二步**: 运行 `run_ablation_minimal.py`（消融实验）
   - 使用新的两阶段评估流程
   - 生成独立的selection persona（200个）
   - 生成独立的validation persona（50个，场景名：collab_robot_assembly）
   - **预计时间**: 2-4小时

3. **第三步**: 运行 `run_baseline_comparison.py`（基线对比，复用validation persona）
   - 复用步骤1生成的validation persona（50个）
   - 确保与生成量表使用相同的评估标准
   - **预计时间**: 1-2小时

4. **第四步**: 运行 `analyze_all_results.py`（综合分析）
   - 汇总所有实验结果
   - 生成综合报告
   - **预计时间**: 10-30分钟

### 总预计时间
- **总计**: 约4.5-9.5小时（取决于API响应速度）

### 注意事项
- 所有实验都使用统一的两阶段评估流程
- 确保persona配置正确（selection: 200个，validation: 50个）
- 基线对比必须在使用相同validation persona的场景下运行

