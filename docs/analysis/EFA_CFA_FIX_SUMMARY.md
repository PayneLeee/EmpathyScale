# EFA+CFA筛选问题修复总结

## 问题描述

在运行`tests/test_single_scenario_quick.py`时，EFA+CFA筛选失败，错误信息：
```
[Step 1] 3/301 items passed item-total correlation (>= 0.5)
[Step 2] 1/3 items passed distribution checks (skew <= 1.0, kurt <= 2.0)
[Step 3] 1/1 items passed inter-item correlation check
[EFA ERROR] EFA failed: 0-dimensional array given. Array must be at least two-dimensional
```

## 根本原因

1. **筛选阈值过严**：经过多轮筛选后，只剩下1个条目
2. **缺少条目数量检查**：在执行EFA之前没有检查是否有足够的条目
3. **缺少诊断信息**：无法了解为什么筛选后条目数量这么少

## 修复内容

### 1. 添加条目数量检查

在`select_items_by_efa_cfa`函数中，在执行EFA之前检查条目数量：

```python
# Check minimum items required for EFA (at least 3 items needed, preferably 5+)
min_items_for_efa = 3
if len(items_passed_inter) < min_items_for_efa:
    # Provide diagnostic information
    print(f"    [ERROR] Only {len(items_passed_inter)} item(s) passed all preliminary checks.")
    print(f"    [ERROR] EFA requires at least {min_items_for_efa} items to proceed.")
    # ... 详细的诊断信息和建议
    raise ValueError(...)
```

### 2. 添加诊断信息

在筛选过程中添加统计信息和建议：

- **Item-total correlation统计**：显示最大值和平均值
- **筛选结果诊断**：显示每个筛选步骤后剩余的条目数量
- **建议**：如果条目太少，提供调整阈值的建议

### 3. 在`perform_efa`函数中添加检查

确保在调用EFA之前验证条目数量：

```python
if len(valid_items) < 2:
    raise ValueError(f"Only {len(valid_items)} valid item(s) in ratings matrix. EFA requires at least 2 items.")

if ratings_clean.shape[1] < 2:
    raise ValueError(f"Ratings matrix has only {ratings_clean.shape[1]} column(s). EFA requires at least 2 items.")
```

## 可能的解决方案

如果遇到条目太少的问题，可以考虑：

1. **降低item-total correlation阈值**：
   - 当前：0.5
   - 建议：0.3-0.4（如果数据质量允许）

2. **放宽分布检查阈值**：
   - 当前：skew <= 1.0, kurt <= 2.0
   - 建议：skew <= 1.5, kurt <= 3.0

3. **检查数据质量**：
   - 所有条目可能评分相似（导致item-total correlation低）
   - 可能需要检查评估数据的质量

## 下一步

1. 重新运行测试，查看诊断信息
2. 根据诊断信息调整阈值
3. 如果问题持续，检查评估数据的质量




