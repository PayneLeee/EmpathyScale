# 架构重构：将筛选逻辑移至 Agent

## 重构目标

将所有筛选、去重等具体操作功能从 run 文件移到 agent 中，使 run 文件只负责工作流控制。

## 重构内容

### 1. 创建 `ItemSelectionAgent`

**文件**: `agents/item_selection_agent.py`

**功能**:
- 封装所有统计筛选逻辑
- 支持多阶段筛选（百分位数、质量过滤、语义去重、维度平衡）
- 提供统一的接口 `select_items()`
- 自动保存选择结果

**主要方法**:
- `select_items()`: 执行多阶段筛选
- `save_selection_results()`: 保存选择结果到磁盘

### 2. 更新 Run 文件

#### `run_predefined_scenarios.py`
- **移除**: 直接调用 `select_items_by_percentile`, `filter_scale_by_item_ids` 等工具函数
- **添加**: 使用 `ItemSelectionAgent` 进行筛选
- **简化**: Step 6 的代码从 ~180 行减少到 ~50 行

#### `run_statistical_item_selection.py`
- **移除**: 直接调用筛选工具函数
- **添加**: 使用 `ItemSelectionAgent`，支持向后兼容的策略参数

#### `tests/test_single_scenario_quick.py`
- **移除**: 内联的筛选逻辑
- **添加**: 使用 `ItemSelectionAgent`

## 架构优势

### 1. 关注点分离
- **Run 文件**: 只负责工作流编排（调用 agent、传递参数、处理结果）
- **Agent**: 负责具体业务逻辑（筛选算法、去重、平衡）

### 2. 代码复用
- 所有筛选逻辑集中在 `ItemSelectionAgent` 中
- 避免在多个 run 文件中重复实现相同逻辑

### 3. 易于维护
- 筛选策略的修改只需更新 `ItemSelectionAgent`
- Run 文件保持简洁，易于理解工作流

### 4. 易于测试
- Agent 可以独立测试
- Run 文件可以专注于工作流测试

## 使用示例

### 在 Run 文件中使用

```python
from agents.item_selection_agent import ItemSelectionAgent

# 初始化 agent
selection_agent = ItemSelectionAgent()

# 配置筛选参数
selection_config = {
    "percentile_min": 0.20,
    "percentile_max": 0.30,
    "min_mean_rating": 85.0,
    "max_std": 20.0,
    "similarity_threshold": 0.80,
    "min_items_per_dimension": 3,
    "max_items_per_dimension": 5
}

# 执行筛选
selection_result = selection_agent.select_items(
    items=items,
    evaluation_summary=eval_summary,
    target_min=10,
    target_max=20,
    selection_config=selection_config
)

# 获取结果
selected_ids = selection_result["selected_item_ids"]
filtered_items = selection_result["filtered_items"]
selection_stats = selection_result["selection_statistics"]

# 保存结果
selection_agent.save_selection_results(run_id, selection_result)
```

## 筛选策略

`ItemSelectionAgent` 支持多阶段筛选策略：

1. **百分位数筛选**: 选择评分前 20-30% 的条目
2. **质量过滤**: 过滤掉评分 < 85 或标准差 > 20 的条目
3. **语义去重**: 移除相似度 ≥ 80% 的条目对，保留评分更高的
4. **维度平衡**: 确保每个维度保留 3-5 个条目
5. **回退机制**: 如果筛选后条目数不足，选择评分最高的条目

## 文件变更清单

### 新增文件
- `agents/item_selection_agent.py`: 新的筛选 agent

### 修改文件
- `run_predefined_scenarios.py`: 使用 `ItemSelectionAgent`
- `run_statistical_item_selection.py`: 使用 `ItemSelectionAgent`
- `tests/test_single_scenario_quick.py`: 使用 `ItemSelectionAgent`

### 保留文件（工具函数）
- `utils/statistical_item_selection.py`: 保留底层工具函数，供 agent 内部使用
- `utils/semantic_deduplication.py`: 保留语义去重工具函数，供 agent 内部使用

## 向后兼容性

- `run_statistical_item_selection.py` 仍然支持旧的策略参数（`rating_threshold`, `percentile`, `dimension_balanced`）
- 这些参数会被转换为 `ItemSelectionAgent` 的配置格式

## 测试建议

1. 运行 `tests/test_single_scenario_quick.py` 验证筛选功能
2. 运行 `run_predefined_scenarios.py` 验证完整工作流
3. 检查生成的选择结果是否符合预期（10-20 个条目）

## 后续优化建议

1. 可以考虑将筛选策略配置化（JSON/YAML 文件）
2. 可以添加更多筛选策略（如因子分析、聚类等）
3. 可以添加筛选结果的详细日志和可视化




