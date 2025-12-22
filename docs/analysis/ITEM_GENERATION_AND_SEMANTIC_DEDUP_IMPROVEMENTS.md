# 条目生成和语义去重改进

## 概述

根据分析结果，问题更可能是**条目多样性不足**而非persona多样性不足。因此，我们进行了以下改进：

1. **改进条目生成prompt**：强调语义多样性
2. **添加预评估语义去重**：在评估前删除语义相近的条目

## 改进详情

### 1. 条目生成Prompt改进

**文件**: `prompts/scale_generation_support.json`

**改进内容**:
- 更明确地强调**语义多样性是关键**
- 明确列出10个不同的语义方面，确保条目覆盖不同方面
- 明确说明**避免语义等价**：不要创建表达相同概念但措辞不同的条目
- 强调每个条目应该测量**独特的共情相关行为或感知**

**关键要求**:
- 每个条目必须测量不同的方面、行为或共情表现
- 条目不应是彼此的语义改写
- 覆盖认知理解、情绪响应、支持行为、视角采择、信任安全、沟通质量、适应性、主动意识、错误处理、情境敏感性等不同方面

### 2. 预评估语义去重

**新文件**: `utils/pre_evaluation_semantic_deduplication.py`

**功能**:
- 在评估前删除语义相近的条目
- 使用sentence transformers进行语义相似度计算（更准确）
- 如果sentence transformers不可用，回退到基于文本的相似度
- 保留每个相似对中的第一个条目，删除第二个

**集成位置**:
1. **`agents/empathy_scale_generation_agent_group.py`**: 在content assessment之后、组装markdown之前
2. **`run_predefined_scenarios.py`**: 在解析条目之后、评估之前（双重保险）
3. **`tests/test_single_scenario_quick.py`**: 在测试流程中也包含

**参数**:
- `similarity_threshold`: 0.80（默认）
- `use_sentence_transformers`: True（默认，如果可用）

**输出**:
- 过滤后的条目列表
- 统计信息（原始数量、过滤后数量、删除数量、相似对列表）
- 保存到 `semantic_deduplication_stats.json`

## 工作流程

### 修改前
```
生成条目 → Content Assessment → 组装Markdown → 评估 → 统计筛选
```

### 修改后
```
生成条目 → Content Assessment → 语义去重 → 组装Markdown → 评估 → 统计筛选
                                    ↑
                              新增步骤
```

## 预期效果

1. **条目语义多样性提高**：
   - 生成的条目覆盖更多不同的语义方面
   - 减少语义重复的条目

2. **评估效率提高**：
   - 评估前删除语义重复的条目，减少评估工作量
   - 确保评估的条目都是语义上不同的

3. **统计筛选效果改善**：
   - 条目多样性提高后，item-total correlation应该提高
   - 条目区分度应该提高（方差增加）

## 技术细节

### 语义相似度计算

**方法1（优先）**: Sentence Transformers
- 模型: `all-MiniLM-L6-v2`
- 使用cosine similarity计算语义相似度
- 更准确，能捕获语义相似性

**方法2（回退）**: 基于文本的相似度
- 使用`difflib.SequenceMatcher`
- 基于文本归一化后的字符序列匹配
- 如果sentence transformers不可用，自动回退

### 去重策略

- 对于相似度 >= threshold的条目对，保留第一个，删除第二个
- 这样可以确保保留的条目在原始列表中的顺序

## 使用示例

```python
from utils.pre_evaluation_semantic_deduplication import remove_semantic_duplicates_before_evaluation

items = [
    {"dimension": "Safety Awareness", "item_text": "The robot recognizes hazardous materials."},
    {"dimension": "Safety Awareness", "item_text": "The robot identifies dangerous substances."},
    {"dimension": "Adaptive Pacing", "item_text": "The robot adjusts its speed to match my pace."},
]

filtered_items, stats = remove_semantic_duplicates_before_evaluation(
    items,
    similarity_threshold=0.80,
    use_sentence_transformers=True
)

print(f"Original: {stats['n_original']}, Filtered: {stats['n_filtered']}, Removed: {stats['n_removed']}")
```

## 注意事项

1. **阈值选择**: 0.80是一个平衡点，既删除明显的语义重复，又保留有细微差异的条目
2. **性能**: Sentence transformers需要下载模型（首次使用），但后续会缓存
3. **回退机制**: 如果sentence transformers不可用，会自动使用文本相似度，确保功能可用
4. **双重保险**: 在生成流程和运行流程中都添加了语义去重，确保即使生成流程中失败，运行流程中也会执行

## 下一步

1. 运行测试验证改进效果
2. 检查语义去重统计，确认删除了多少重复条目
3. 验证条目多样性是否提高（item-total correlation是否提高）

