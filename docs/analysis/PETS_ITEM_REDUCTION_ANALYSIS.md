# PETS论文条目缩减方法分析

## PETS论文的条目缩减流程

根据PETS论文Section 6，条目缩减过程如下：

### 阶段1: 数据准备 (Section 6.1)

1. **移除反向计分条目**
2. **移除偏态条目**（基于histograms和density plots）
3. **计算item-total correlation（条目-总分相关性）**
   - 移除相关性 < 0.5 的条目
4. **计算skewness和kurtosis（偏度和峰度）**
   - 移除 skewness > |1| 的条目
   - 移除 kurtosis > |2| 的条目
5. **计算intercorrelations（条目间相关性）**
   - 移除与其他条目相关性 > 0.8 的条目

**结果**: 从38个条目减少到26个条目

### 阶段2: 探索性因子分析 (Section 6.2)

1. **检查EFA前提条件**:
   - Bartlett's sphericity test
   - Kaiser-Meyer-Olkin (KMO) test

2. **确定因子数量**:
   - 使用Kaiser准则（eigenvalues >= 1）
   - Scree plot
   - Parallel analysis
   - **结果**: 2个因子

3. **执行EFA**:
   - 方法: **Principal Axis Factoring (PAF)**
   - 旋转: **Promax Rotation**（斜交旋转，因为因子相关）

4. **基于因子载荷筛选**:
   - 移除因子载荷 < 0.4 的条目
   - 移除交叉载荷条目
   - **只保留因子载荷 >= 0.75 的条目** ⭐ **这是关键！**

**结果**: 从26个条目减少到12个条目（Factor 1: 8个，Factor 2: 4个）

### 阶段3: 验证性因子分析 (Section 7.2)

1. **CFA验证因子结构**
2. **优化模型拟合**
3. **进一步缩减**

**结果**: 从12个条目减少到10个条目

## 当前方法的问题

### 当前方法使用的指标

1. **Mean rating（平均评分）**: `min_mean_rating >= 85.0`
2. **Standard deviation（标准差）**: `max_std <= 20.0`
3. **Percentile（百分位数）**: 选择前20-30%高评分条目
4. **Semantic similarity（语义相似度）**: 移除相似度>=80%的条目
5. **Dimension balance（维度平衡）**: 每个维度3-5个条目

### 问题分析

**问题1: 基于评分筛选 vs 基于因子载荷筛选**

- **PETS方法**: 基于**因子载荷**（factor loadings），反映条目与潜在构念（latent construct）的关系
- **当前方法**: 基于**平均评分**，只反映条目的受欢迎程度

**为什么这是问题？**

1. **高评分 ≠ 好条目**: 
   - 一个条目可能评分很高，但与量表要测量的构念（empathy）关系很弱
   - 例如："The system was easy to use" 可能评分很高，但不测量empathy

2. **因子载荷反映构念相关性**:
   - 因子载荷高（>=0.75）意味着条目与潜在因子（如Emotional Responsiveness）高度相关
   - 这是条目质量的**心理测量学指标**，而不仅仅是受欢迎程度

3. **PETS论文明确说明**:
   - Section 6.2: "we kept only items that loaded >= 0.75 on the respective factor"
   - 这是基于**统计方法**，而不是基于评分

**问题2: 缺少关键统计指标**

当前方法缺少PETS使用的关键指标：

1. **Item-total correlation（条目-总分相关性）**:
   - 测量条目与量表总分的相关性
   - PETS阈值: >= 0.5

2. **Factor loadings（因子载荷）**:
   - 测量条目与潜在因子的关系
   - PETS阈值: >= 0.75

3. **Inter-item correlations（条目间相关性）**:
   - 检测冗余条目
   - PETS阈值: < 0.8

4. **Skewness/Kurtosis（偏度/峰度）**:
   - 检测分布问题
   - PETS阈值: skewness <= |1|, kurtosis <= |2|

## PETS方法的优势

1. **科学性**: 基于心理测量学理论（因子分析）
2. **客观性**: 不依赖主观评分，而是基于统计关系
3. **有效性**: 确保条目真正测量目标构念
4. **可靠性**: 通过CFA验证因子结构

## 建议的改进方案

### 方案1: 实现EFA/CFA方法（推荐）

**优点**: 与PETS方法完全一致，科学严谨

**实现步骤**:
1. 计算item-total correlation
2. 执行EFA（Principal Axis Factoring + Promax Rotation）
3. 基于因子载荷筛选（>= 0.75）
4. 执行CFA验证
5. 计算Cronbach's alpha

**挑战**: 
- 需要足够的样本量（PETS使用324个参与者）
- 需要实现EFA/CFA（可以使用Python的`factor_analyzer`或`semopy`库）

### 方案2: 混合方法（折中方案）

**结合当前方法和PETS方法**:

1. **第一阶段**: 使用当前方法快速筛选（基于评分、语义去重）
2. **第二阶段**: 对筛选后的条目应用PETS方法（item-total correlation, factor loadings）

**优点**: 
- 保留当前方法的效率
- 增加PETS方法的科学性

### 方案3: 简化EFA方法

**如果样本量不足，使用简化方法**:

1. **Item-total correlation**: 计算条目与总分的相关性
2. **Inter-item correlation**: 检测冗余条目
3. **基于相关性的筛选**: 而不是因子载荷

**优点**: 
- 不需要完整的EFA
- 仍然比单纯基于评分更科学

## 当前方法的适用场景

当前方法（基于评分筛选）可能适用于：

1. **初步筛选**: 快速减少条目数量
2. **样本量不足**: 无法进行完整的EFA/CFA
3. **快速原型**: 需要快速生成量表草稿

但**不应该**作为最终筛选方法，因为：
- 不保证条目测量目标构念
- 可能选择高评分但不相关的条目
- 不符合心理测量学标准

## 结论

**PETS论文的条目缩减方法**:
- ✅ 基于**因子分析**（EFA/CFA）
- ✅ 使用**因子载荷**作为主要筛选标准（>= 0.75）
- ✅ 使用**item-total correlation**、**inter-item correlation**等统计指标
- ❌ **不使用**mean rating作为筛选标准

**当前方法**:
- ❌ 主要基于**mean rating**筛选
- ❌ 缺少**因子载荷**等关键指标
- ⚠️ 不符合PETS论文的方法论

**建议**: 
1. 实现EFA/CFA方法（如果样本量足够）
2. 或至少添加item-total correlation作为筛选指标
3. 将基于评分的筛选作为**初步筛选**，而不是最终筛选




