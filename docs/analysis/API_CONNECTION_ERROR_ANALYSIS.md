# API Connection Error 重试原因分析

## 问题现象
在评估过程中（192 items, 100 personas），频繁出现 `APIConnectionError` 重试，影响评估速度。

## 可能原因分析

### 1. **缺少 Timeout 配置（最可能）** ⚠️
**问题**：
- `EvaluationAgentGroup` 的 `ChatOpenAI` 初始化时**没有设置 `timeout` 参数**
- 默认 timeout 可能是 60 秒，对于 192 个 items 的 prompt 可能不够
- 其他 agent（如 `ItemGenerationAgent`）都设置了 timeout（180-300秒）

**证据**：
```python
# evaluation_agent_group.py:39
self.llm = ChatOpenAI(api_key=api_key, model_name=model_name, temperature=0.7)
# ❌ 没有 timeout 参数

# 对比：scale_generation_agents.py:58-62
self.llm = ChatOpenAI(
    api_key=api_key, 
    model_name=model_name, 
    temperature=0.7,
    timeout=180.0  # ✅ 有 timeout
)
```

**影响**：
- 192 个 items + 详细 persona 信息 + 场景信息 = **超长 prompt**（可能 5000+ tokens）
- 处理时间可能超过默认 timeout，导致连接超时

### 2. **Prompt 过长导致请求超时**
**问题**：
- 192 个 items 的 prompt 非常长
- 每个 item 包含 dimension 和 item_text
- 加上详细的 persona 信息和场景信息
- 总 token 数可能达到 5000-8000 tokens

**计算**：
```
Prompt 结构：
- Persona 信息：~500 tokens
- 场景信息：~200 tokens  
- 192 items × (dimension + item_text) ≈ 192 × 20 = 3840 tokens
- 指令部分：~1000 tokens
总计：~5500 tokens
```

**影响**：
- API 处理时间长（可能需要 30-60 秒）
- 如果 timeout 设置过短，会导致连接超时

### 3. **并行请求过多导致速率限制**
**问题**：
- 5 个 worker 同时发送请求
- 每个请求都是大 prompt（192 items）
- 可能导致：
  - OpenAI API 速率限制（RPM - Requests Per Minute）
  - 连接池耗尽
  - 网络拥塞

**OpenAI API 限制**（gpt-4o-mini）：
- 默认账户：~60 RPM（Requests Per Minute）
- 5 个并行 worker = 可能超过限制

### 4. **网络连接不稳定**
**问题**：
- 临时网络波动
- DNS 解析问题
- 防火墙/代理问题

### 5. **分批处理未生效**
**问题**：
- `items_batch_size=100`，但 192 items 应该分成 2 个 batch
- 需要确认分批处理是否正常工作

## 解决方案

### 方案 1：增加 Timeout（推荐，立即实施）✅
```python
# evaluation_agent_group.py
self.llm = ChatOpenAI(
    api_key=api_key, 
    model_name=model_name, 
    temperature=0.7,
    timeout=300.0  # 5 分钟 timeout（与 ContentAssessmentAgent 一致）
)
```

### 方案 2：减少并行度（如果速率限制是问题）
```python
# 从 5 个 worker 减少到 3 个
eval_agent = EvaluationAgentGroup(
    api_key=api_key,
    prompts_dir=prompt_manager.prompts_dir,
    max_workers=3,  # 减少并行度
    items_batch_size=100
)
```

### 方案 3：增加重试延迟（给 API 更多恢复时间）
```python
# scale_generation_agents.py:14
def retry_llm_call(func, max_retries=3, delay=3):  # 从 2 秒增加到 3 秒
    """Retry LLM call on connection errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except (APIConnectionError, Exception) as e:
            if attempt < max_retries - 1:
                wait_time = delay * (attempt + 1)  # 3s, 6s, 9s
                ...
```

### 方案 4：添加指数退避和随机抖动
```python
import random

def retry_llm_call(func, max_retries=3, base_delay=2):
    """Retry LLM call with exponential backoff and jitter."""
    for attempt in range(max_retries):
        try:
            return func()
        except (APIConnectionError, Exception) as e:
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"    [RETRY] Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}. Retrying in {wait_time:.1f}s...", flush=True)
                time.sleep(wait_time)
            else:
                ...
```

### 方案 5：验证分批处理是否生效
确保 192 items 被正确分成 2 个 batch（每个 100 items）：
```python
# 检查日志中是否有 "Items will be processed in 2 batch(es)"
```

## 推荐实施顺序

1. **立即**：添加 timeout=300.0（方案 1）
2. **如果仍有问题**：增加重试延迟到 3 秒（方案 3）
3. **如果速率限制明显**：减少 max_workers 到 3（方案 2）
4. **长期优化**：实施指数退避（方案 4）

## 监控建议

在评估过程中监控：
- 重试频率（应该 < 5%）
- 平均响应时间（应该 < 60 秒）
- 成功率（应该 > 95%）

如果重试率仍然很高，考虑：
- 进一步减少并行度
- 增加 batch size（减少 API 调用次数）
- 检查网络连接质量

