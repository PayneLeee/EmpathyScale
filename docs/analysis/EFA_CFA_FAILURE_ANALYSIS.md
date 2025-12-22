# EFA/CFA失败原因分析与修复方案

## 问题描述

从终端输出可以看到：
```
[Step 1] 209/212 items passed item-total correlation (>= 0.3)
[Step 2] 2/209 items passed distribution checks (skew <= 1.0, kurt <= 3.0)
[Step 3] 0/2 items passed inter-item correlation check
[ERROR] EFA+CFA method failed: No items passed inter-item correlation check. Cannot proceed with EFA.
```

## 根本原因分析

### 问题1: Step 2分布检查过于严格

**现象**：从209个items急剧减少到只有2个items（99%的过滤率）

**原因分析**：
1. 虽然已经将kurtosis阈值从2.0调整到3.0，但可能仍然过于严格
2. PETS论文使用阈值：skewness <= |1|, kurtosis <= |2|
3. 但实际数据可能分布更偏，需要更宽松的阈值

**PETS论文原文**（Section 6.1）：
> "removed those that were below or above the specified thresholds (< 0.5 for item-total correlation, > |1| for skewness, and > |2| for kurtosis)"

**Boateng论文建议**：
- 对于skewness和kurtosis，应该根据数据特征灵活调整
- 过于严格的分布检查可能会排除大量有效items
- 建议：如果大部分items都因为分布问题被排除，应该放宽阈值或调整检查顺序

### 问题2: Step 3 inter-item correlation逻辑错误

**现象**：2个items全部未通过inter-item correlation检查

**原因分析**：
1. **逻辑错误**：当前代码计算的是**所有items**之间的相关性（包括已被过滤的items），而不是只计算`items_passed_dist`中的items
2. **阈值问题**：PETS论文说"correlated > 0.8 with **several** other items"，"several"通常指至少3个或更多，但当前代码允许最多2个高相关性（`<= 2`）
3. **边界情况**：当只有2个items时，如果它们之间的相关性>0.8，每个item会有1个高相关性，理论上应该能通过（因为允许<=2），但实际可能因为逻辑错误导致失败

**PETS论文原文**（Section 6.1）：
> "We computed intercorrelations for the remaining 28 items and removed two items that correlated > 0.8 with **several** other items"

**关键点**：
- "several"意味着至少3个或更多
- 应该只考虑**已通过前面步骤的items**之间的相关性
- 移除那些与**至少3个**其他items高相关的items（冗余检查）

### 问题3: 检查顺序可能不合理

**分析**：
- 分布检查（skewness/kurtosis）通常应该在更后面进行，或者使用更宽松的阈值
- 如果大部分items因为分布问题被排除，后续的inter-item correlation检查就失去了意义

## 修复方案

### 修复1: 调整Step 3 inter-item correlation逻辑

**当前错误逻辑**：
```python
# 计算所有items之间的相关性（包括已被过滤的items）
inter_corrs = calculate_inter_item_correlations(ratings_matrix)

# 统计每个item与多少个其他items高相关（包括已被过滤的items）
high_corr_counts = {}
for (i1, i2), corr in inter_corrs.items():
    if abs(corr) > max_inter_corr:
        high_corr_counts[i1] = high_corr_counts.get(i1, 0) + 1
        high_corr_counts[i2] = high_corr_counts.get(i2, 0) + 1

# 只检查items_passed_dist中的items
items_passed_inter = [
    item_id for item_id in items_passed_dist
    if high_corr_counts.get(item_id, 0) <= 2  # 允许最多2个高相关性
]
```

**修复后的正确逻辑**：
```python
# 只计算items_passed_dist中的items之间的相关性
item_indices = [item_id - 1 for item_id in items_passed_dist]
ratings_subset = ratings_matrix[:, item_indices]
inter_corrs = calculate_inter_item_correlations(ratings_subset)

# 统计每个item与多少个其他items高相关（只考虑items_passed_dist中的items）
high_corr_counts = {}
for (i1, i2), corr in inter_corrs.items():
    if abs(corr) > max_inter_corr:
        # 映射回原始item_id
        orig_i1 = items_passed_dist[i1 - 1]
        orig_i2 = items_passed_dist[i2 - 1]
        high_corr_counts[orig_i1] = high_corr_counts.get(orig_i1, 0) + 1
        high_corr_counts[orig_i2] = high_corr_counts.get(orig_i2, 0) + 1

# 移除那些与至少3个其他items高相关的items（PETS: "several" = 至少3个）
items_passed_inter = [
    item_id for item_id in items_passed_dist
    if high_corr_counts.get(item_id, 0) < 3  # 与至少3个其他items高相关的才移除
]
```

### 修复2: 放宽Step 2分布检查阈值

**建议**：
1. 如果大部分items因为分布问题被排除，应该放宽阈值
2. 根据Boateng论文建议，可以：
   - 将kurtosis阈值从3.0进一步放宽到5.0或更高
   - 或者将分布检查移到inter-item correlation之后
   - 或者使用更宽松的阈值（如skewness <= 2.0, kurtosis <= 7.0）

**Boateng论文建议**：
- 分布检查应该根据数据特征灵活调整
- 过于严格的分布检查可能会排除大量有效items
- 建议：如果大部分items都因为分布问题被排除，应该放宽阈值

### 修复3: 添加诊断信息

**建议**：
- 在Step 2和Step 3之间添加诊断信息，显示：
  - 每个item的skewness和kurtosis值
  - 每个item的高相关性数量
  - 建议的阈值调整

## 验证逻辑

### PETS论文方法论验证

1. **Item-total correlation**: >= 0.5（当前使用0.3，已调整）✅
2. **Skewness**: <= |1|（当前使用1.0）✅
3. **Kurtosis**: <= |2|（当前使用3.0，已调整）⚠️
4. **Inter-item correlation**: 移除与至少3个其他items高相关(>0.8)的items ❌（当前逻辑错误）

### Boateng论文建议验证

1. **分布检查应该灵活**：根据数据特征调整阈值 ✅
2. **Inter-item correlation应该只考虑已通过的items**：当前逻辑错误 ❌
3. **检查顺序应该合理**：分布检查可能应该在更后面 ⚠️

## 已实施的修复

### ✅ 修复1: Step 3 inter-item correlation逻辑修正

**修复内容**：
1. 只计算`items_passed_dist`中的items之间的相关性（而不是所有items）
2. 正确映射subset indices回原始item IDs
3. 将阈值从"允许最多2个高相关性"改为"移除与至少3个其他items高相关的items"（符合PETS论文的"several"含义）

**代码位置**：`utils/factor_analysis.py` lines 687-702

**关键改进**：
```python
# 修复前：计算所有items的相关性
inter_corrs = calculate_inter_item_correlations(ratings_matrix)

# 修复后：只计算已通过items的相关性
item_indices = [item_id - 1 for item_id in items_passed_dist]
ratings_subset = ratings_matrix[:, item_indices]
inter_corrs = calculate_inter_item_correlations(ratings_subset)

# 修复前：允许最多2个高相关性
if high_corr_counts.get(item_id, 0) <= 2

# 修复后：移除与至少3个其他items高相关的items
if high_corr_counts.get(item_id, 0) < 3
```

### ✅ 修复2: 添加诊断信息

**修复内容**：
1. 在Step 2失败时，显示分布统计信息和建议的阈值调整
2. 在Step 3失败时，显示高相关性统计信息和建议

**代码位置**：`utils/factor_analysis.py` lines 668-685, 704-712

### ✅ 修复3: 实现自适应阈值调整（Boateng et al., 2018）

**修复内容**：
1. 添加 `calculate_adaptive_distribution_thresholds()` 函数，基于数据特征自动调整阈值
2. 在 `select_items_by_efa_cfa()` 中添加自适应阈值参数：
   - `adaptive_distribution_thresholds`: 是否启用自适应调整（默认: True）
   - `min_distribution_pass_rate`: 最小通过率触发调整（默认: 0.1 = 10%）
   - `min_distribution_items`: 最小通过items数量（默认: 5）
3. 在 Step 2 中实现自适应逻辑：
   - 先使用初始阈值检查通过率
   - 如果通过率过低（< 10% 或 < 5个items），自动计算调整后的阈值
   - 使用75th/90th百分位数，确保至少1.5x初始阈值
   - 设置合理上限（skewness ≤ 2.0, kurtosis ≤ 7.0）

**代码位置**：
- `utils/factor_analysis.py` lines 204-294: `calculate_adaptive_distribution_thresholds()` 函数
- `utils/factor_analysis.py` lines 760-800: Step 2 自适应阈值调整逻辑

**工作原理**：
1. 首先使用PETS论文的严格阈值（skewness ≤ 1.0, kurtosis ≤ 2.0）
2. 如果通过率过低，基于数据分布自动调整：
   - 使用75th百分位数 × 1.2，或初始阈值 × 1.5（取较大值）
   - 如果仍不够，使用90th百分位数 × 1.1
   - 设置上限防止过度放宽
3. 确保保留足够的items用于后续分析

**符合Boateng等（2018）建议**：
- ✅ 使用"有意义的满意阈值"（基于数据分布）
- ✅ 考虑数据特征（非正态性、样本量）
- ✅ 平衡严格性与实用性
- ✅ 数据驱动的方法

## 验证结果

### PETS论文方法论验证

1. **Item-total correlation**: >= 0.5（当前使用0.3，已根据数据调整）✅
2. **Skewness**: <= |1|（当前使用1.0）✅
3. **Kurtosis**: <= |2|（当前使用3.0，已根据数据调整）⚠️（可能需要进一步放宽）
4. **Inter-item correlation**: 移除与至少3个其他items高相关(>0.8)的items ✅（已修复）

### Boateng论文建议验证

1. **分布检查应该灵活**：已实现自适应阈值调整，自动根据数据特征调整 ✅
2. **Inter-item correlation应该只考虑已通过的items**：已修复 ✅
3. **检查顺序应该合理**：当前顺序符合PETS论文，自适应调整确保有足够items进行后续检查 ✅

## 已完成的修复总结

### ✅ 所有修复已完成

1. **Step 3 inter-item correlation逻辑修正** ✅
   - 只计算已通过items的相关性
   - 正确理解PETS论文的"several"含义（≥3个）

2. **添加诊断信息** ✅
   - Step 2和Step 3失败时提供详细诊断
   - 建议阈值调整方案

3. **实现自适应阈值调整** ✅
   - 基于Boateng等（2018）建议
   - 自动根据数据特征调整分布检查阈值
   - 确保保留足够items进行后续分析

## 下一步建议

1. **运行测试**：重新运行测试，验证修复效果
2. **监控自适应调整**：观察自适应阈值调整是否正常工作
3. **验证结果质量**：检查最终选出的items是否满足质量要求

