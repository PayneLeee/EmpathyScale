---
name: Phase 2 validation metrics and independent persona groups
overview: 在 `evaluation_agent_group.py` 中添加 PETS 风格的验证指标（区分能力、Cronbach's alpha、因子分数），并修改 `evaluate_items` 支持 `phase` 参数以确保 Phase 1 和 Phase 2 使用独立的人设组。同时更新 `test_single_scenario_quick.py` 以正确传递 `phase` 和 `scenario_id` 参数。
todos:
  - id: modify_evaluate_items
    content: 修改 evaluate_items 方法：添加 phase 参数（默认 'selection'），在加载/生成persona时使用该参数
    status: completed
  - id: add_discriminant_ability
    content: 添加 _calculate_discriminant_ability 方法：计算 empathic vs non-empathic 的 t-test 和 Cohen's d
    status: completed
  - id: add_cronbach_alpha
    content: 添加 _calculate_cronbach_alpha 方法：计算 Cronbach's alpha（内部一致性）
    status: completed
  - id: add_factor_scores
    content: 添加 _calculate_factor_scores 方法：计算每个因子的平均分和标准差
    status: completed
  - id: modify_summarize
    content: 修改 _summarize 方法：添加 factor_structure 参数，调用三个新方法并添加 validation_metrics 字段
    status: completed
  - id: update_test_phase1
    content: 更新 test_single_scenario_quick.py Phase 1 调用：添加 scenario_id 和 phase='selection'
    status: completed
  - id: update_test_phase2
    content: 更新 test_single_scenario_quick.py Phase 2 调用：添加 scenario_id 和 phase='validation'
    status: completed
  - id: add_validation_metrics
    content: 在 test_single_scenario_quick.py Phase 2 中：从 selection_result 获取 factor_structure，重新计算 summary 并显示验证指标
    status: completed
---

# Phase 2 验证指标和独立人设组实施计划

## 目标

1. 在 `evaluation_agent_group.py` 中添加 PETS 风格的验证指标计算
2. 修改 `evaluate_items` 支持 `phase` 参数，确保 Phase 1 和 Phase 2 使用独立的人设组
3. 更新 `test_single_scenario_quick.py` 以正确传递参数

## 实施步骤

### 1. 修改 `agents/evaluation_agent_group.py`

#### 1.1 修改 `evaluate_items` 方法签名

- 添加 `phase: str = "selection"` 参数（默认值保持向后兼容）
- 在加载/生成persona时使用 `phase` 参数：
- 将硬编码的 `phase="selection"` 改为使用传入的 `phase` 参数
- 位置：第83行、第88行、第96行

#### 1.2 添加 `_calculate_discriminant_ability` 方法

- 计算 empathic vs non-empathic 场景的区分能力（t-test）
- 输入：`participant_data`（包含 `empathy_condition` 字段的persona）
- 输出：包含 `empathic_mean`, `non_empathic_mean`, `t_statistic`, `p_value`, `cohens_d`, `significant` 的字典
- 如果数据不足或缺少 `empathy_condition`，返回 `None`

#### 1.3 添加 `_calculate_cronbach_alpha` 方法

- 计算 Cronbach's alpha（内部一致性）
- 输入：`ratings_matrix` (n_participants × n_items)
- 输出：包含 `alpha`, `ci_lower`, `ci_upper` 的字典
- 使用 `scipy.stats` 或手动计算（如果 scipy 不可用，提供回退）

#### 1.4 添加 `_calculate_factor_scores` 方法

- 计算每个因子的平均分和标准差（参考 PETS Table 8）
- 输入：`item_statistics`（来自 `_summarize`），`factor_structure`（`{item_id: factor_idx}` 字典）
- 输出：`{factor_name: {"mean": float, "std": float, "n_items": int}}` 字典
- 如果 `factor_structure` 为 `None` 或空，返回空字典

#### 1.5 修改 `_summarize` 方法

- 添加可选参数 `factor_structure: Optional[Dict[int, int]] = None`
- 在方法内部：

1. 构建 `ratings_matrix`（用于 Cronbach's alpha）
2. 调用 `_calculate_discriminant_ability(participant_data, items)`
3. 调用 `_calculate_cronbach_alpha(ratings_matrix)`
4. 调用 `_calculate_factor_scores(item_stats, factor_structure)`
5. 将结果添加到返回字典的 `validation_metrics` 字段

### 2. 修改 `tests/test_single_scenario_quick.py`

#### 2.1 Phase 1 评估调用（第269行和第279行）

- 在 `eval_agent.evaluate_items` 调用中添加：
- `scenario_id=scenario_id`（基础场景名，与persona保存位置对齐：`data/personas/{scenario_id}/selection.json`）
- `phase="selection"`
- 注意：当前代码已经传入了 `personas` 参数，添加 `scenario_id` 和 `phase` 是为了让 `evaluate_items` 内部可以正确保存/加载persona

#### 2.2 Phase 2 评估调用（第495行和第517行）

- 在 `eval_agent.evaluate_items` 调用中添加：
- `scenario_id=scenario_id`（基础场景名，已存在，与persona保存位置对齐：`data/personas/{scenario_id}/validation.json`）
- `phase="validation"`（新增）

#### 2.3 Phase 2 验证指标计算（第527-536行附近）

- 在加载 Phase 2 的 `evaluation_summary.json` 后：

1. 从 `selection_result` 中获取 `factor_structure`（如果可用）
2. 加载 `participant_level_evaluations.json`
3. 调用 `eval_agent._summarize(participant_data, filtered_items, factor_structure=factor_structure)`
4. 更新 `evaluation_summary.json` 以包含 `validation_metrics`
5. 打印验证指标（区分能力、Cronbach's alpha、因子分数）

## 文件修改清单

### `agents/evaluation_agent_group.py`

- [ ] 修改 `evaluate_items` 方法：添加 `phase` 参数，使用该参数加载/保存persona
- [ ] 添加 `_calculate_discriminant_ability` 方法
- [ ] 添加 `_calculate_cronbach_alpha` 方法
- [ ] 添加 `_calculate_factor_scores` 方法
- [ ] 修改 `_summarize` 方法：添加 `factor_structure` 参数，调用三个新方法

### `tests/test_single_scenario_quick.py`

- [ ] Phase 1 调用：添加 `scenario_id` 和 `phase="selection"`
- [ ] Phase 2 调用：添加 `scenario_id` 和 `phase="validation"`
- [ ] Phase 2 验证指标：从 `selection_result` 获取 `factor_structure`，重新计算 summary 并显示验证指标

## 注意事项

1. **向后兼容性**：`phase` 参数默认值为 `"selection"`，确保现有代码不受影响
2. **依赖检查**：`_calculate_cronbach_alpha` 需要 `scipy`，如果不可用应提供回退或警告
3. **数据完整性**：区分能力计算需要 `empathy_condition` 字段，如果缺失应返回 `None` 而不是报错
4. **因子结构**：`factor_structure` 的键可能是字符串（JSON序列化），需要转换为整数
5. **Persona 对齐**：

- Phase 1: `scenario_id` 使用基础场景名（`scenario['name']`），persona保存在 `data/personas/{scenario_id}/selection.json`
- Phase 2: `scenario_id` 使用基础场景名（`scenario['name']`），persona保存在 `data/personas/{scenario_id}/validation.json`
- 确保 `evaluate_items` 中使用的 `scenario_id` 与 `persona_agent.save_personas` 和 `load_personas` 使用的 `scenario_id` 一致（都是基础场景名，不是带后缀的）

## 预期结果

- Phase 1 使用 `{scenario}`（基础场景名）+ `phase="selection"` 的人设组
- Persona 文件位置：`data/personas/{scenario}/selection.json`
- Phase 2 使用 `{scenario}`（基础场景名）+ `phase="validation"` 的独立人设组
- Persona 文件位置：`data/personas/{scenario}/validation.json`
- Phase 2 的 `evaluation_summary.json` 包含 `validation_metrics` 字段，包含：
- `discriminant_ability`: t-test 结果（如果数据可用）