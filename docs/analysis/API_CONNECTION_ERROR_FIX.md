# API连接错误问题分析与修复

## 问题分析

### 为什么在条目生成阶段出现连接错误？

1. **Prompt长度增加**：
   - 更新后的`item_generation_prompt`包含了10个语义方面的详细说明
   - Prompt长度：3622字符，约905 tokens
   - 加上scenario和dimensions信息，总长度可能达到1500+ tokens
   - 长prompt需要更长的处理时间，容易超时

2. **5个生成器顺序调用**：
   - 虽然代码是顺序执行（for循环），但5个连续调用可能导致：
     - API速率限制（rate limiting）
     - 连接池耗尽
     - 网络不稳定时的累积错误

3. **缺少超时设置**：
   - `ItemGenerationAgent`的`ChatOpenAI`没有设置`timeout`参数
   - 默认超时可能不足以处理长prompt

4. **重试机制不够健壮**：
   - 重试延迟是线性的（2s, 4s, 6s）
   - 对于连接错误，指数退避更合适

## 修复方案

### 1. 增加超时设置
```python
self.llm = ChatOpenAI(
    api_key=api_key, 
    model_name=model_name, 
    temperature=0.7,
    timeout=180.0  # 3分钟超时，足够处理长prompt
)
```

### 2. 添加调用间隔
在5个生成器之间添加1秒延迟，避免速率限制：
```python
for idx, g in enumerate(gens):
    if idx > 0:
        time.sleep(1)  # 1秒延迟
    results.append(g.generate_items(dimensions, scenario))
```

### 3. 改进重试机制
使用指数退避（exponential backoff）：
```python
wait_time = delay * (2 ** attempt)  # 2s, 4s, 8s
```

### 4. 添加进度提示
在每个生成器调用时显示进度，便于监控。

## 预期效果

1. **减少超时错误**：180秒超时足够处理长prompt
2. **减少速率限制**：1秒间隔避免触发API速率限制
3. **更好的错误恢复**：指数退避给API更多恢复时间
4. **更好的可观测性**：进度提示帮助定位问题

## 为什么前面步骤没问题？

1. **Construct Definition**：
   - 只有一个LLM调用
   - Prompt较短（construct_system_prompt）
   - 不会触发速率限制

2. **Content Assessment**：
   - 已经有超时设置（300秒）
   - 已经有批处理机制（避免长prompt）
   - 已经有重试机制

3. **Item Generation**（问题所在）：
   - 5个连续调用
   - 长prompt（10个语义方面）
   - 没有超时设置
   - 没有调用间隔




