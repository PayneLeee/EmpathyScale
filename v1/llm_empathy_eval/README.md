# llm_empathy_eval — 把共情量表流水线推广到"评估 LLM 的共情能力"

借鉴 `EmpathyScale-main` 九步流水线的产出，把"被试"换成"被评估的 LLM"。

## 思路（逻辑闭环）

```
共情量表（复用已验证的 18 题/2 因子，run 2026-10-07_012327）
   ↓
被评模型（本地超小免费模型, CPU）按 system prompt 对共情情境生成回应
   ↓
评审模型（GLM glm-4-flash, 免费）按量表逐题 0-100 打分 → reward
   ↓
激励迭代：变异 system prompt → 再评 → reward 提升才保留（爬山）
```

与原流水线的对应关系：
| 原流水线（机器人量表） | 本项目（LLM 共情评估） |
|---|---|
| persona 当被试给机器人量表打分 | GLM 当评审给 **LLM 的实际回应** 打分 |
| 机器人的共情表现 | 被评 LLM 的 system prompt 决定的行为 |
| 心理测量指标作自激励 | 量表 reward 作 prompt 激励 |
| （被评对象是机器人） | （被评对象是 LLM） |

## 文件
- `scale_adapter.py` — 从 run 产物加载 18 题量表（含因子归属）
- `subject_model.py` — 被评模型：`stub`（离线桩）/ `qwen`（Qwen2.5-0.5B-Instruct, CPU）
- `judge.py` — GLM 评审：逐题打分、因子聚合、reward
- `incentive_loop.py` — 激励回路（prompt 爬山）+ 全程轨迹落盘
- `run_demo.py` — 入口

## 运行
```bash
# 首次：venv 已含 torch(CPU)+transformers；qwen 首跑自动下载 ~1GB 权重
venv/Scripts/python.exe run_demo.py --model stub --iters 2 --k 1   # 离线被评模型
venv/Scripts/python.exe run_demo.py --model qwen --iters 2 --k 1   # 真实小模型
```

## 可行性结论（demo 已验证）
1. **管道成立**：量表评分→reward→prompt 迭代全程可跑，stub 模型上 reward 对
   prompt 中共情要素敏感，爬山能识别更优 prompt。
2. **"以评估为激励迭代模型"的两条路线**：
   - 免训练（本 demo）：prompt 层爬山/最佳n选一，零训练成本，立即可用；
   - 训练路线：把 `(情境, 回应, reward)` 轨迹转成偏好对做 DPO/LoRA——0.5B 模型
     在 CPU 上可承受极小规模（<1e4 样本），但需要数小时/轮；建议后续接
     `peft` 做 LoRA 实验。
3. **方法学提醒（如实）**：评审也是 LLM，存在"评审偏置"；正式研究应报告
   评审一致性（多评审 Kappa）并抽样人工校验——这正是原流水线
   "评价者也可以是 agent"（PPT slide 18）的同一方法论边界。
4. **量表迁移提醒**：18 题量表是为"家庭陪伴机器人"场景生成的；正式评估
   LLM 共情时，应把场景文本换成"LLM 对话助手"重新走一遍九步流水线生成
   场景定制量表——本流水线天然支持（改 `run_real.py` 的 SCENARIO 即可）。
