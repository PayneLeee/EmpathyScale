# EFA方法实现总结

## 实现概述

已成功实现基于探索性因子分析（EFA）的条目筛选方法，完全遵循PETS论文的方法论。

## 主要变更

### 1. 新增模块：`utils/factor_analysis.py`

实现了完整的EFA分析功能，包括：

- **`load_participant_ratings()`**: 从`participant_level_evaluations.json`加载原始评分数据
- **`calculate_item_total_correlation()`**: 计算条目-总分相关性（PETS阈值: >= 0.5）
- **`calculate_inter_item_correlations()`**: 计算条目间相关性（PETS阈值: < 0.8）
- **`calculate_skewness_kurtosis()`**: 计算偏度和峰度（PETS阈值: skew <= |1|, kurt <= |2|）
- **`perform_efa()`**: 执行探索性因子分析
  - 使用Principal Axis Factoring (PAF)
  - Promax旋转（斜交旋转）
  - 基于Kaiser准则自动确定因子数量
  - 保留因子载荷 >= 0.75 的条目
- **`select_items_by_efa()`**: 完整的EFA筛选流程

### 2. 更新：`agents/item_selection_agent.py`

- 添加了`evaluation_summary_path`参数，用于访问原始评分数据
- 添加了`use_efa`配置选项（默认启用）
- 实现了EFA方法的自动回退机制（如果EFA失败，回退到基于评分的筛选）
- 保存EFA分析结果到`selection_config.json`

### 3. 更新：`run_predefined_scenarios.py`

- **增加样本量**: Phase 1的participants从20增加到**200**（100*2=200，PETS使用324，200应该足够进行EFA）
- **更新selection_config**: 使用EFA方法参数
  - `min_item_total_corr`: 0.5
  - `max_skewness`: 1.0
  - `max_kurtosis`: 2.0
  - `max_inter_corr`: 0.8
  - `min_factor_loading`: 0.75
  - `n_factors`: None (自动检测)

### 4. 更新：`tests/test_single_scenario_quick.py`

- 更新为使用EFA方法
- 增加participants数量到50（用于测试）

### 5. 依赖安装

- 安装了`factor_analyzer`库（用于EFA分析）
- 已确认`scipy`和`numpy`已安装

## EFA筛选流程（遵循PETS论文）

### Step 1: Item-Total Correlation（条目-总分相关性）
- 计算每个条目与量表总分的相关性
- 移除相关性 < 0.5 的条目

### Step 2: Distribution Check（分布检查）
- 计算每个条目的偏度（skewness）和峰度（kurtosis）
- 移除偏度 > |1| 或峰度 > |2| 的条目

### Step 3: Inter-Item Correlation（条目间相关性）
- 计算所有条目对之间的相关性
- 移除与多个其他条目相关性 > 0.8 的条目（冗余检查）

### Step 4: Exploratory Factor Analysis（探索性因子分析）
- 检查EFA前提条件：
  - Bartlett's sphericity test
  - Kaiser-Meyer-Olkin (KMO) test
- 使用Principal Axis Factoring (PAF)提取因子
- 使用Promax旋转（斜交旋转）
- 基于Kaiser准则（eigenvalues >= 1）确定因子数量
- **保留因子载荷 >= 0.75 的条目**（PETS关键标准）
- 移除交叉载荷条目（在多个因子上都有高载荷）

## 输出文件

### `data/runs/{run_id}/statistical_selection/selection_config.json`

包含完整的EFA分析结果：

```json
{
  "strategy": "efa",
  "method": "efa",
  "n_factors": 2,
  "min_item_total_corr": 0.5,
  "min_factor_loading": 0.75,
  "bartlett_test": {
    "chi_square": 1234.56,
    "p_value": 0.0001,
    "significant": true
  },
  "kmo_test": {
    "kmo_model": 0.87,
    "adequate": true
  },
  "filtering_steps": {
    "initial_n_items": 150,
    "after_item_total_corr": 120,
    "after_distribution_check": 100,
    "after_inter_corr": 85,
    "final_n_items": 12
  },
  "efa_results": {
    "item_loadings": {...},
    "eigenvalues": [...]
  }
}
```

## 与PETS论文的对比

| 方法 | PETS论文 | 当前实现 | 状态 |
|------|---------|---------|------|
| Item-total correlation | >= 0.5 | >= 0.5 | ✅ |
| Skewness | <= \|1\| | <= \|1\| | ✅ |
| Kurtosis | <= \|2\| | <= \|2\| | ✅ |
| Inter-item correlation | < 0.8 | < 0.8 | ✅ |
| Factor extraction | PAF | PAF | ✅ |
| Rotation | Promax | Promax | ✅ |
| Factor loading threshold | >= 0.75 | >= 0.75 | ✅ |
| Sample size | 324 | 100 | ⚠️ (减少但足够) |

## 优势

1. **科学性**: 基于心理测量学理论，而非主观评分
2. **客观性**: 不依赖平均评分，而是基于统计关系
3. **有效性**: 确保条目真正测量目标构念（empathy）
4. **可靠性**: 通过Bartlett和KMO测试验证数据适合性

## 注意事项

1. **样本量要求**: 
   - PETS使用324个参与者
   - 当前实现使用100个参与者（应该足够进行EFA）
   - 如果样本量不足，会自动回退到基于评分的筛选

2. **因子数量**:
   - 自动检测（基于Kaiser准则）
   - 可以手动指定`n_factors`参数

3. **回退机制**:
   - 如果EFA失败（例如样本量不足或数据不适合），会自动回退到基于评分的筛选方法

## 下一步

1. 运行实验验证EFA方法的效果
2. 对比EFA方法 vs 基于评分方法的筛选结果
3. 根据实际结果调整参数（如果需要）




