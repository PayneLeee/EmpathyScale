# PETS条目数量控制方法分析

## PETS论文的条目数量控制

根据PETS论文，条目数量控制**不是通过预设目标数量**，而是通过**统计方法的自然结果**：

### PETS的条目缩减过程

1. **初始条目**: 100个（专家访谈生成）
2. **Expert Ratings后**: 38个（基于CVI < 0.6移除）
3. **Focus Group后**: 38个（微调，移除9个，添加2个）
4. **EFA后**: 12个（基于因子载荷 >= 0.75，Factor 1: 8个，Factor 2: 4个）
5. **CFA后**: 10个（通过模型拟合优化，移除2个条目）

### 关键发现

**PETS没有预设目标条目数量**，而是：

1. **EFA阶段**：
   - 使用**因子载荷阈值**（>= 0.75）作为唯一筛选标准
   - 条目数量是**统计方法的结果**，不是预设目标
   - 结果：12个条目（Factor 1: 8个，Factor 2: 4个）

2. **CFA阶段**：
   - 使用**模型拟合指标**作为优化标准
   - 如果拟合不佳（RMSEA > 0.08），移除最低载荷的条目
   - 迭代优化直到拟合指标满足要求
   - 结果：10个条目（从12个减少到10个）

3. **维度平衡**：
   - PETS的最终结果是**自然形成的**：
     - Factor 1 (Emotional Responsiveness): 6个条目
     - Factor 2 (Understanding and Trust): 4个条目
   - 不是通过"每个维度3-5个条目"这样的规则强制平衡

## 当前实现的问题

### 问题1: target_min和target_max参数

当前实现中有`target_min`和`target_max`参数，但在EFA+CFA方法中：
- **没有真正使用**这些参数来控制条目数量
- 条目数量完全由统计方法决定（因子载荷、模型拟合）

### 问题2: 维度平衡逻辑

当前实现中有`min_items_per_dimension`和`max_items_per_dimension`参数，但：
- PETS**没有使用**这样的规则
- 维度平衡是**统计方法的结果**，不是强制规则

## PETS方法的条目数量控制逻辑

### 控制机制1: 因子载荷阈值（EFA阶段）

```python
# PETS方法：只保留因子载荷 >= 0.75 的条目
min_factor_loading = 0.75
selected_items = [item_id for item_id in items 
                  if max_loading(item_id) >= min_factor_loading]
```

**特点**：
- 条目数量是**统计方法的结果**
- 不预设目标数量
- 如果所有条目都满足阈值，就全部保留
- 如果没有条目满足阈值，就全部移除（需要调整阈值）

### 控制机制2: 模型拟合优化（CFA阶段）

```python
# PETS方法：通过模型拟合指标控制
while not fit_adequate and len(items) > min_items:
    if rmsea > 0.08 or tli < 0.95 or cfi < 0.95 or srmr > 0.08:
        # 移除最低载荷的条目
        remove_worst_item()
        re_run_cfa()
```

**特点**：
- 条目数量是**优化过程的结果**
- 不预设目标数量
- 通过迭代移除条目来优化拟合
- 最终数量取决于数据质量

### 控制机制3: 最小条目数保护

虽然PETS没有明确说明，但实际做法是：
- **每个因子至少保留2-3个条目**（否则无法进行CFA）
- 这是**技术限制**，不是预设目标

## 建议的实现方案

### 方案1: 完全遵循PETS方法（推荐）

**特点**：
- 不预设目标条目数量
- 条目数量完全由统计方法决定
- 只设置**最小保护值**（技术限制）

**实现**：
```python
def select_items_by_efa_cfa(
    ...,
    min_factor_loading: float = 0.75,  # EFA筛选标准
    min_items_per_factor: int = 2,     # 技术限制：每个因子至少2个条目
    cfa_fit_thresholds: {...}          # CFA拟合标准
) -> Dict[str, Any]:
    # EFA: 保留所有因子载荷 >= 0.75 的条目
    # CFA: 优化拟合，直到满足阈值或达到最小条目数
    # 不预设目标数量
```

### 方案2: 添加"期望范围"（折中方案）

**特点**：
- 保留PETS的统计方法
- 添加"期望范围"作为参考（不强制）

**实现**：
```python
def select_items_by_efa_cfa(
    ...,
    target_range: Optional[Tuple[int, int]] = None,  # 期望范围（仅用于报告）
    min_items_per_factor: int = 2,                   # 技术限制
    ...
) -> Dict[str, Any]:
    # 执行EFA+CFA（不强制目标范围）
    # 在结果中报告是否在期望范围内
    # 如果不在范围内，给出建议（调整阈值或接受结果）
```

### 方案3: 自适应阈值调整

**特点**：
- 如果EFA结果不在期望范围内，调整因子载荷阈值

**实现**：
```python
def select_items_by_efa_cfa(
    ...,
    target_range: Tuple[int, int] = (10, 20),
    min_factor_loading: float = 0.75,
    adaptive_threshold: bool = True,  # 是否自适应调整
    ...
) -> Dict[str, Any]:
    # 先使用默认阈值
    # 如果结果不在目标范围内，调整阈值
    # 但最终仍以统计方法为准
```

## 推荐方案

**推荐使用方案1（完全遵循PETS方法）**：

1. **科学性**：完全遵循PETS论文的方法论
2. **客观性**：条目数量由数据质量决定，不人为干预
3. **可解释性**：结果可以明确解释为"统计方法的结果"

**实现要点**：
- 移除`target_min`和`target_max`作为强制参数
- 只保留`min_items_per_factor`作为技术限制（每个因子至少2个条目）
- 在结果中报告条目数量，但不强制在某个范围内
- 如果结果不在期望范围内，给出建议（例如：调整因子载荷阈值或接受结果）

## 当前实现需要修改的地方

1. **`select_items_by_efa_cfa()`函数**：
   - 移除对`target_min`和`target_max`的依赖
   - 添加`min_items_per_factor`参数（技术限制）

2. **`ItemSelectionAgent.select_items()`方法**：
   - `target_min`和`target_max`仅用于报告，不用于筛选
   - 添加结果验证：检查是否满足最小条目数要求

3. **CFA迭代逻辑**：
   - 添加最小条目数保护：每个因子至少保留2个条目
   - 如果达到最小条目数但拟合仍不佳，停止迭代并报告




