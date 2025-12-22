# 语义去重功能集成完成

## 集成位置

语义去重功能已成功集成到以下三个位置：

### 1. 生成流程中（主要位置）
**文件**: `agents/empathy_scale_generation_agent_group.py`

**位置**: `generate_scale()` 方法中，Step 3.5（在content assessment之后，组装markdown之前）

**功能**:
- 在条目生成流程中自动执行语义去重
- 使用Sentence Transformers进行语义相似度计算
- 保存去重统计信息到 `semantic_deduplication_stats.json`

**代码位置**: 第160-195行

### 2. 运行流程中（安全措施）
**文件**: `run_predefined_scenarios.py`

**位置**: Step 4之后（解析条目之后，评估之前）

**功能**:
- 作为双重保险，确保即使生成流程中未执行，运行流程中也会执行
- 在评估前移除语义重复的条目

**代码位置**: 第208-225行

### 3. 测试流程中（安全措施）
**文件**: `tests/test_single_scenario_quick.py`

**位置**: Step 4之后（解析条目之后，评估之前）

**功能**:
- 在测试流程中也包含语义去重
- 确保测试结果的一致性

**代码位置**: 第187-204行

## 工作流程

### 修改前
```
生成条目 → Content Assessment → 组装Markdown → 评估 → 统计筛选
```

### 修改后
```
生成条目 → Content Assessment → 语义去重 → 组装Markdown → 评估 → 统计筛选
                                    ↑
                              新增步骤（Step 3.5）
```

**双重保险**:
- 生成流程中执行一次（Step 3.5）
- 运行/测试流程中再执行一次（作为安全措施）

## 技术实现

### 使用的函数
`utils/pre_evaluation_semantic_deduplication.py` 中的 `remove_semantic_duplicates_before_evaluation()`

### 参数设置
- `similarity_threshold`: 0.80（默认）
- `use_sentence_transformers`: True（默认，如果可用）

### 去重方法
1. **优先方法**: Sentence Transformers (`all-MiniLM-L6-v2`)
   - 使用cosine similarity计算语义相似度
   - 更准确，能捕获语义相似性

2. **回退方法**: 基于文本的相似度 (`difflib.SequenceMatcher`)
   - 如果sentence transformers不可用，自动回退
   - 基于文本归一化后的字符序列匹配

### 去重策略
- 对于相似度 >= 0.80的条目对，保留第一个，删除第二个
- 这样可以确保保留的条目在原始列表中的顺序

## 输出信息

### 生成流程中
```
[Semantic Dedup] Removing semantically similar items...
[Semantic Dedup] Using sentence transformers for semantic similarity...
[OK] After semantic deduplication: 250 items (removed 60 semantic duplicates)
```

### 运行/测试流程中
```
[Semantic Dedup] Applying semantic deduplication as safety measure...
[Semantic Dedup] Removed 5 semantic duplicates (310 → 305 items)
```

## 统计信息保存

生成流程中会保存去重统计信息到：
```
data/runs/{run_id}/empathy_scale_generation_agent_group/semantic_deduplication_stats.json
```

统计信息包括：
- `n_original`: 原始条目数量
- `n_filtered`: 过滤后条目数量
- `n_removed`: 删除的条目数量
- `removal_ratio`: 删除比例
- `similar_pairs`: 发现的相似对列表
- `similarity_threshold`: 使用的阈值
- `method`: 使用的方法（sentence_transformers 或 text_based）

## 错误处理

- 如果 `sentence-transformers` 不可用，自动回退到文本相似度
- 如果导入失败，打印警告并继续执行（不中断流程）
- 如果执行失败，打印警告并继续使用原始条目

## 预期效果

1. **条目语义多样性提高**：
   - 移除语义重复的条目
   - 确保评估的条目都是语义上不同的

2. **评估效率提高**：
   - 减少需要评估的条目数量
   - 减少评估时间

3. **统计筛选效果改善**：
   - 条目多样性提高后，item-total correlation应该提高
   - 条目区分度应该提高（方差增加）

## 注意事项

1. **阈值选择**: 0.80是一个平衡点，既删除明显的语义重复，又保留有细微差异的条目
2. **性能**: Sentence transformers需要下载模型（首次使用），但后续会缓存
3. **双重保险**: 在生成流程和运行流程中都添加了语义去重，确保即使生成流程中失败，运行流程中也会执行
4. **向后兼容**: 如果语义去重功能不可用，流程会继续执行，不会中断

## 验证方法

运行测试后，检查：
1. 生成流程中是否执行了语义去重
2. 运行流程中是否也执行了语义去重（作为安全措施）
3. `semantic_deduplication_stats.json` 文件是否生成
4. 条目数量是否减少（如果有语义重复）
5. 条目多样性是否提高（item-total correlation是否提高）




