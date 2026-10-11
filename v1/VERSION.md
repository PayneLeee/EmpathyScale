# EmpathyScale — `v1/`（版本子目录）

本 `v1/` 目录是我们在 EmpathyScale 多智能体 LLM 量表流水线上的工作快照，于 2026-10-11 贡献到 `PayneLeee/EmpathyScale`。
This `v1/` folder is a self-contained snapshot of our work on the EmpathyScale multi-agent LLM pipeline, contributed to `PayneLeee/EmpathyScale` on 2026-10-11.

## 包含内容 / What's inside
- **主流水线（9 步法，Boateng 2018）**：`agents/`、`tools/`、`prompts/`、`main.py`、`run_*.py`、`utils/`、`tests/`、`docs/`、`scenarios/`、`scripts/`。
- **`llm_empathy_eval/`**（任务 8）：复用已验证量表评估某个 LLM 的共情能力（被试=LLM，评委=LLM），含激励迭代闭环。详见其内部 `README.md`。

## 故意不含的内容 / Deliberately excluded
- **密钥 / Secrets**：`config.json`、`key.txt` 未纳入。请自行准备 `config.json`（复制 `config.example.json` 并填入 `openai_api_key` / `model_name`）。
- **运行数据 / Run data**：`data/`（模拟施测、CFA、NMI 产物）可重新生成，为精简仓库未带上。重跑 `run_largeN_validation.py` + `run_largeN_selection_only.py` 可复现。
- **虚拟环境与缓存 / Venvs & caches**：`venv/`、`__pycache__/`、`*.pyc` 已排除。
- **AI 助手运行时/中间产物**：无——本目录只含项目源码。

## 快速开始 / Quick start
1. `pip install -r requirements.txt`
2. 复制 `config.example.json` → `config.json`，填入你的 API key 与模型名。
3. 主流水线：`python main.py`（或各 `run_*.py` 入口）。
4. LLM 共情评估：`cd llm_empathy_eval && python run_demo.py --model glm`

## 当前状态 / Status
- N=80 的 CFA：RMSEA 0.215 / TLI 0.876 / CFI 0.891（对比 n=30 基线 0.387 / 0.716 / 0.751）。
- 选题后 NMI = 1.00（条目网络社区与 EFA 因子结构完全吻合）。
- LLM 共情评估闭环已用 GLM-4-Flash 同时充当被试与评委端到端验证。
