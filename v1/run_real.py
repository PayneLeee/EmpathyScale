"""
run_real.py — 非交互真实端到端运行驱动器（requires a valid API key in config.json）

与 `main.py`（交互式，依赖终端 input()）不同，本脚本用 `user_input_factory` 让 LLM
自动扮演"被试/受访者"回答访谈问题，从而一条命令跑通 PPT 九步流水线并产出真实共情量表。

用法：
    venv/Scripts/python.exe run_real.py
    N_PER_GROUP=60 venv/Scripts/python.exe run_real.py          # 自定义每组 persona 数
    SCENARIO=my_scenario.json venv/Scripts/python.exe run_real.py  # 用外部场景 JSON

注意：
    - config.json 需含有效 openai_api_key + openai_base_url + model_name（默认读 DeepSeek）。
    - 真实运行会调用 LLM + arXiv/Semantic Scholar，产生 API 费用；key 为明文，跑完勿提交。
    - 访谈 agent 是 langchain ReAct，依赖 LLM 主动调用 save_interview_data 工具落盘摘要；
      若模型未调用该工具，Phase B 门控会跳过后续（属 LLM 行为，非代码崩溃，需换强模型或调 prompt）。
"""
import os
import sys
import json
from pathlib import Path

# 让脚本无论从哪运行都能找到扁平导入的 agent 模块（与 main.py 约定一致）
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import main
import workflow_console as wc


# ---------------------------------------------------------------------------
# 场景：默认一个"家政/协作服务机器人"demo；可被外部 JSON 覆盖
# ---------------------------------------------------------------------------
DEFAULT_SCENARIO = (
    "我们部署了一台家庭陪伴与服务机器人，用于在老年人居家中提供提醒、陪伴与简单协助。"
    "机器人具备语音对话、面部表情显示屏与温湿度/跌倒传感器，通过自然语言与触摸交互，"
    "运行在私密的家庭环境里，与老人形成长期的情感陪伴关系。"
)


def load_scenario() -> str:
    path = os.environ.get("SCENARIO")
    if path and Path(path).exists():
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # 兼容 {"scenario": "..."} 或把字典拼成文本
                if isinstance(data.get("scenario"), str):
                    return data["scenario"]
                return "\n".join(f"{k}: {v}" for k, v in data.items())
            if isinstance(data, str):
                return data
        except Exception as e:
            print(f"[WARN] 读取场景文件失败，回退默认场景：{e}", flush=True)
    return DEFAULT_SCENARIO


SCENARIO_TEXT = load_scenario()
_TURN = {"n": 0}


def user_input_factory(last_agent_message: str) -> str:
    """LLM 自动扮演受访者：第一轮给完整场景，后续推动访谈收口，末尾退出。"""
    _TURN["n"] += 1
    if _TURN["n"] == 1:
        # 明确指示 agent 立即把场景保存下来，避免其在 get_interview_progress 上
        # 反复折返而从不调用 save_interview_data（见 interview_agent_group 的修复说明）。
        return (
            SCENARIO_TEXT
            + "\n\n[指令] 请立即调用 save_interview_data 工具，把上述场景信息"
            "（评估背景、机器人平台、交互方式、协作模式、环境设定）完整保存下来，"
            "然后再视需要追问缺失项；不要反复要求我重新描述已经给出的内容。"
        )
    # 推动 ReAct agent 尽快调用 save_interview_data 落盘摘要
    if _TURN["n"] >= 6:
        return "exit"
    return ("我们的情况如上所述，请基于此继续。如果信息已足够，"
            "请直接调用保存工具生成本次访谈摘要。")


def main_run():
    # 样本量可通过环境变量控制（默认 40/组，平衡 API 成本与 EFA/CFA 收敛）
    n = int(os.environ.get("N_PER_GROUP", "40"))
    main.SELECTION_N_PER_GROUP = n
    print(f"[run_real] SELECTION_N_PER_GROUP = {n}（每组 persona 模拟施测样本量）", flush=True)

    wf = main.MultiAgentWorkflow()  # 这里会用 config.json 的 key/model 创建真实 LLM
    print(f"[run_real] workflow run_id = {wf.run_id}", flush=True)
    try:
        wf.run_interview_session(
            user_input_factory=user_input_factory,
            max_automated_turns=12,
        )
    except Exception as e:
        print(f"\n[run_real] 运行中断：{type(e).__name__}: {e}", flush=True)
        print(f"[run_real] 已落盘数据在 data/runs/{wf.run_id}/", flush=True)
        raise

    run_dir = wf.data_manager.get_run_path(wf.run_id)
    print("\n" + "=" * 70)
    print("REAL RUN COMPLETE")
    print("=" * 70)
    wc.sub(f"产出目录：data/runs/{wf.run_id}/")
    for label, rel in [
        ("访谈摘要", "interview_agent_group/summary.json"),
        ("量表草稿", "empathy_scale_generation_agent_group/scale_draft.md"),
        ("CVI", "content_validity_agent/content_validity_summary.json"),
        ("预测试", "pretest_agent/pretest_result.json"),
        ("Phase1 双组评估", "evaluation_agent_group/selection/empathic/evaluation_summary.json"),
        ("筛选后量表", "empathy_scale_generation_agent_group/filtered_scale_draft.md"),
        ("Phase2 验证", "evaluation_agent_group/validation/evaluation_summary.json"),
        ("运行 README", "README.md"),
    ]:
        p = run_dir / rel
        wc.sub(f"  [{'OK' if p.exists() else 'MISSING'}] {label} -> {rel}")


if __name__ == "__main__":
    main_run()
