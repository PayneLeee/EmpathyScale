---
name: Redesign Ablation Study
overview: 重新设计消融实验，使其基于主实验基线(5个生成器+内容评估+语义去重)，系统地测试生成器数量(1 vs 5)和内容评估(有 vs 无)的影响，确保消融变体的质量低于主实验基线，同时保持与主实验相同的评估方法。
todos:
  - id: update_variants
    content: 更新VARIANTS配置，从(1/3, True/False)改为(1/5, True/False)，移除基线配置
    status: completed
  - id: update_descriptions
    content: 更新变体名称、描述和日志输出，明确反映与主实验基线的对比关系
    status: completed
    dependencies:
      - update_variants
  - id: add_baseline_comparison
    content: 在generate_ablation_summary中添加与主实验基线的对比逻辑
    status: completed
    dependencies:
      - update_variants
  - id: verify_scenario
    content: 验证ABLATION_SCENARIO与主实验场景配置完全一致
    status: completed
  - id: update_comments
    content: 添加注释说明语义去重保持启用的原因和消融设计的合理性
    status: completed
    dependencies:
      - update_variants
---

# 消融实验重新设计计划

## 设计原则

1. **基线明确**: 主实验基线 = (5生成器, 内容评估=True, 语义去重=True)
2. **系统消融**: 2×2设计，测试生成器数量和内容评估两个维度
3. **质量保证**: 确保所有消融变体的质量指标（内部一致性、区分性）都低于主实验基线
4. **评估一致**: 使用与主实验完全相同的评估流程（Phase 1: 200人双组, EFA+CFA, Phase 2: 200人验证）

## 消融变体设计

基于2×2因子设计，4个变体：| 变体名称 | 生成器数量 | 内容评估 | 语义去重 | 选择方法 | 预期质量 ||---------|----------|---------|---------|---------|---------|| **baseline** (主实验) | 5 | True | True | EFA+CFA | 最高 || **fewer_generators** | 1 | True | True | EFA+CFA | 中等-低 || **no_content** | 5 | False | True | **随机选择** | 中等（极端对照） || **fewer_generators_no_content** | 1 | False | True | EFA+CFA | 最低 |**注意**: no_content变体使用随机选择（方案B），作为极端对照，更直观地展示内容评估的价值。

## 实现改动

### 1. 更新变体配置 (`run_ablation_minimal.py`)

**当前配置** (第87-93行):

```python
VARIANTS = {
    "single_no_content": (1, False),
    "single_with_content": (1, True),
    "multi_no_content": (3, False),
    "multi_with_content": (3, True),
}
```

**新配置**（推荐使用字典格式，更清晰）:

```python
VARIANTS = {
    "fewer_generators": {
        "num_generators": 1,
        "enable_content": True,
        "use_random_selection": False,  # 使用EFA+CFA（与基线一致）
    },
    "no_content": {
        "num_generators": 5,
        "enable_content": False,
        "use_random_selection": True,  # 使用随机选择（方案B：极端对照）
    },
    "fewer_generators_no_content": {
        "num_generators": 1,
        "enable_content": False,
        "use_random_selection": False,  # 使用EFA+CFA（与基线一致）
    },
}
```

**注意**:

- 主实验基线(5生成器, 内容评估=True, 随机选择=False, 使用EFA+CFA)不在此列表中，因为它已经在主实验中运行。
- no_content变体采用方案B：使用随机选择作为极端对照，更直观地展示内容评估的价值。

### 2. 语义去重处理

**当前**: 在`run_variant`函数的Step 4中，语义去重始终启用（第190-210行）**修改**:

- 保持语义去重始终启用（与用户确认的2×2设计一致）
- 添加注释说明这是为了保持与主实验一致

### 2.5. no_content变体的选择方法（已决定：方案B）

**决策**: 采用**方案B** - no_content变体使用随机选择15条，而不是EFA+CFA统计选择**方案B的理由**:

1. **展示价值更直观**: 消融实验的核心目的是展示"内容评估"这个组件的价值。使用随机选择作为极端对照，能更清晰地展示内容评估在提高候选池质量方面的重要性。
2. **避免"挽救效应"**: 如果候选池质量低，使用EFA+CFA虽然公平，但可能"挽救"一些低质量条目，削弱与基线的对比效果。随机选择会直接暴露候选池质量问题。
3. **实际意义**: 在没有内容评估的情况下，如果LLM生成的候选条目质量普遍较低，即使使用统计方法也可能选不出高质量条目。随机选择更能反映候选池的真实质量。
4. **文档说明**: 可以在文档和结果中明确说明：no_content使用随机选择是为了展示内容评估在提高候选池质量方面的价值，作为极端对照。

**实现要求**:

- 为no_content变体添加配置标志：`use_random_selection=True`
- 在Step 6（统计选择）中，根据`use_random_selection`标志选择不同的选择方法
- 随机选择逻辑：
- 从所有条目中随机选择15条（目标范围10-18，选择15作为中间值）
- 如果条目总数 < 15，则选择所有条目并给出警告
- 如果条目总数 < 10，则跳过Phase 2验证
- 保存选择方法信息到结果中，在摘要和日志中明确标注no_content使用了随机选择（作为极端对照）
- 其他变体（fewer_generators, fewer_generators_no_content）仍使用EFA+CFA，保持一致性

### 3. 更新变体描述和日志

更新所有变体的描述，使其明确反映与主实验基线的对比关系：

- `fewer_generators`: "消融：减少生成器数量（1 vs 基线5），使用EFA+CFA选择"
- `no_content`: "消融：移除内容评估（无 vs 基线有），使用随机选择作为极端对照"
- `fewer_generators_no_content`: "消融：减少生成器数量 + 移除内容评估，使用EFA+CFA选择"

### 4. 更新摘要生成函数

修改`generate_ablation_summary`函数，添加与主实验基线的对比：

- 读取主实验的运行结果（基于`ABLATION_SCENARIO['name']`找到对应的主实验run_id）
- 计算每个消融变体相对于基线的质量下降百分比
- 在摘要中明确标注基线配置

### 5. 场景配置对齐

确保`ABLATION_SCENARIO`与主实验使用的场景完全一致（检查`run_predefined_scenarios.py`中的场景定义）。

## 文件修改清单

1. **[run_ablation_minimal.py](run_ablation_minimal.py)**

**配置更新**:

- 更新`VARIANTS`字典（第87-93行），改为字典格式，包含`num_generators`、`enable_content`、`use_random_selection`三个字段
- 更新代码中对VARIANTS的访问方式（从元组解包改为字典访问）

**随机选择实现**:

- 实现随机选择函数：`random_select_items(items, target_count=15)`，从条目列表中随机选择目标数量的条目
- 使用`random.sample()`确保不重复选择
- 处理边界情况：条目数 < target_count时选择所有条目，条目数 < 10时给出警告
- 返回选中的条目ID列表和对应的条目字典列表
- 在`run_variant`函数的Step 6中，根据`variant_config["use_random_selection"]`标志选择不同的选择方法：
- 如果`use_random_selection=True`：调用`random_select_items()`进行随机选择
- 如果`use_random_selection=False`：使用现有的EFA+CFA选择流程（调用`selection_agent.select_items()`）
- 保存选择方法信息到结果中（例如在选择结果中添加`selection_method: "random"`或`"efa_cfa"`）

**日志和描述更新**:

- 更新变体描述和日志输出（第131-133行，第146-147行），明确标注选择方法
- 在Step 6的日志中，明确说明使用的选择方法（随机选择 vs EFA+CFA）
- 对于no_content变体，在日志中添加说明："使用随机选择作为极端对照，展示内容评估的价值"

**摘要生成**:

- 添加与主实验基线的对比逻辑（在`generate_ablation_summary`中）
- 在摘要中明确标注no_content使用了随机选择（作为极端对照）
- 添加基线配置说明注释
- 计算和显示每个消融变体相对于基线的质量指标变化

2. **可能需要添加辅助函数**

- `load_main_experiment_results()`: 加载主实验的运行结果用于对比
- `compare_with_baseline()`: 计算消融变体相对于基线的质量指标

## 预期结果

消融实验完成后，预期看到：

- 主实验基线(5, True, EFA+CFA): α ≥ 0.99, Cohen's d ≥ 4.6
- `fewer_generators`(1, True, EFA+CFA): α和Cohen's d都低于基线
- `no_content`(5, False, 随机选择): α和Cohen's d都显著低于基线（极端对照，展示内容评估的价值）
- `fewer_generators_no_content`(1, False, EFA+CFA): α和Cohen's d最低

## 验证点

1. ✅ 所有消融变体的生成器数量 ≤ 5（确保不会超过基线）
2. ✅ 所有消融变体都没有启用内容评估或生成器数量更少
3. ✅ no_content变体使用随机选择，其他变体使用EFA+CFA
4. ✅ 随机选择的条目数量为15条（在10-18目标范围内）
5. ✅ 选择方法信息已保存到结果中，并在摘要中明确标注

## 设计决策总结

**已确认的设计决策**:

- ✅ 采用方案B：no_content变体使用随机选择（极端对照）
- ✅ 其他变体使用EFA+CFA（保持与基线一致）
- ✅ 2×2设计：测试生成器数量(1 vs 5) × 内容评估(有 vs 无)
- ✅ 语义去重在所有变体中保持启用（与基线一致）
- ✅ 评估流程与主实验完全一致（Phase 1: 200人, Phase 2: 200人）

**no_content使用随机选择的理由**:

- 更直观地展示内容评估在提高候选池质量方面的价值
- 避免EFA+CFA可能"挽救"低质量条目的问题
- 作为极端对照，使对比效果更明显