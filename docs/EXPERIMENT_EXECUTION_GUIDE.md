# 实验执行指南

## 概述

三个核心实验文件需要按顺序运行，每个实验都需要较长时间完成（特别是生成和评估阶段）。

## 运行时间估算

### 1. `run_predefined_scenarios.py` (主实验)
- **3个场景** × 每个场景：
  - 生成阶段：~5-10分钟（生成180+个items）
  - Phase 1评估：~30-60分钟（生成200个personas + 评估180个items）
  - 统计选择：~5-10分钟（EFA+CFA）
  - Phase 2验证：~30-60分钟（生成200个personas + 评估10-20个items）
- **总时间：约3-6小时**

### 2. `run_ablation_minimal.py` (消融研究)
- **4个变体** × 每个变体：
  - 生成阶段：~5-10分钟
  - Phase 1评估：~30-60分钟
  - 统计选择：~5-10分钟
  - Phase 2验证：~30-60分钟
- **总时间：约5-10小时**

### 3. `run_baseline_comparison.py` (基线比较)
- **3个场景** × 每个场景：
  - PETS评估：~15-30分钟（使用已有personas）
  - RoPE评估：~15-30分钟（使用已有personas）
- **总时间：约1.5-3小时**

**总计：约9.5-19小时**

## 运行方式

### 方式1：使用自动化脚本（推荐）

```bash
# 运行所有实验（按顺序）
python tools/run_all_experiments.py
```

### 方式2：手动按顺序运行

```bash
# 步骤1：主实验（必须先运行，生成personas）
python run_predefined_scenarios.py

# 步骤2：消融研究（可选，但需要较长时间）
python run_ablation_minimal.py

# 步骤3：基线比较（需要步骤1完成后运行，使用步骤1生成的personas）
python run_baseline_comparison.py
```

### 方式3：后台运行（Windows PowerShell）

```powershell
# 在后台运行，输出保存到文件
Start-Process python -ArgumentList "run_predefined_scenarios.py" -NoNewWindow -RedirectStandardOutput "run1_output.log" -RedirectStandardError "run1_error.log"
```

## 注意事项

### 1. 运行顺序很重要
- **必须先运行** `run_predefined_scenarios.py`，因为它会生成validation personas
- `run_baseline_comparison.py` **依赖** `run_predefined_scenarios.py` 生成的personas
- `run_ablation_minimal.py` 可以独立运行，但会生成自己的personas

### 2. API费用
- 每个实验需要大量LLM调用（生成personas、评估items等）
- 使用 `gpt-4o-mini` 可以降低成本
- 估算：每个完整实验约需要 $5-20（取决于API定价）

### 3. 中断和恢复
- 如果程序中断，可以重新运行（会重用已生成的personas）
- 已完成的阶段不会重复执行
- 检查 `data/runs/` 目录查看进度

### 4. 快速测试
如果只想快速测试流程，可以使用：
```bash
python tests/test_single_scenario_quick.py
```
这会运行一个简化版本（10个participants而不是200个）。

## 监控进度

### 查看运行目录
```bash
# 查看最新的运行
ls -lt data/runs/ | head -5

# 查看特定运行的进度
ls data/runs/2025-12-22_203259/
```

### 检查生成的文件
- `scale_draft.md` - 生成的量表草稿
- `evaluation_agent_group/selection/combined/` - Phase 1评估结果
- `evaluation_agent_group/validation/` - Phase 2验证结果
- `statistical_selection/` - 统计选择结果

## 常见问题

### Q: 程序运行很慢怎么办？
A: 这是正常的。生成200个personas需要200次LLM调用，每次调用需要几秒钟。建议：
- 使用后台运行
- 或者先运行单个场景测试

### Q: 如果中断了怎么办？
A: 可以重新运行，程序会：
- 重用已生成的personas（如果存在）
- 跳过已完成的阶段
- 继续未完成的部分

### Q: 如何只运行一个场景？
A: 可以修改 `run_predefined_scenarios.py` 中的 `SCENARIOS` 列表，只保留一个场景。

### Q: 如何减少运行时间？
A: 可以修改代码中的participant数量：
- Phase 1: 从200减少到50（但会影响统计有效性）
- Phase 2: 从200减少到50

**注意**：减少participant数量会影响结果的统计有效性，不推荐用于最终实验。

## 检查点

运行前检查：
- [ ] `config.json` 存在且包含有效的 `openai_api_key`
- [ ] 已安装所有依赖：`pip install -r requirements.txt`
- [ ] 有足够的API配额和余额
- [ ] 有足够的磁盘空间（每个运行约需要50-100MB）

运行中检查：
- [ ] 程序正常输出日志
- [ ] 没有API错误
- [ ] 文件正常生成在 `data/runs/` 目录

运行后检查：
- [ ] 所有场景都生成了结果
- [ ] Phase 1和Phase 2评估都完成
- [ ] 统计选择结果存在
- [ ] 验证指标已计算


