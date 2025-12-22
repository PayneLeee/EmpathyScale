"""
测试脚本：验证内容评估修改后的条目保留率

此脚本用于对比修改前后的内容评估效果：
- 修改前：每个维度保留3-6个条目
- 修改后：只去除完全重复的条目，保留大部分条目

使用方法：
1. 运行修改前的版本（需要先恢复旧的prompt）
2. 运行修改后的版本
3. 对比两个版本的条目数量
"""

import json
from pathlib import Path
from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager


def count_items_before_after_content_assessment(run_id: str, dm: DataManager):
    """
    统计内容评估前后的条目数量
    
    注意：此函数需要在实际运行后才能使用，因为它需要读取运行结果
    """
    run_path = dm.get_run_path(run_id)
    
    # 读取生成阶段的中间结果（如果保存了的话）
    # 注意：当前实现可能没有保存内容评估前的条目列表
    # 这个函数主要用于说明如何验证修改效果
    
    draft_path = run_path / "empathy_scale_generation_agent_group" / "scale_draft.md"
    if draft_path.exists():
        md_text = draft_path.read_text(encoding="utf-8", errors="replace")
        items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
        return len(items)
    return 0


def print_verification_guide():
    """打印验证指南"""
    print("=" * 80)
    print("内容评估修改验证指南")
    print("=" * 80)
    print()
    print("修改内容：")
    print("  - 修改前：内容评估会保留每个维度3-6个最强条目")
    print("  - 修改后：内容评估只去除完全重复的条目，保留大部分条目")
    print()
    print("验证步骤：")
    print("  1. 运行一个场景的生成流程（使用修改后的prompt）")
    print("  2. 检查生成的条目数量")
    print("  3. 对比修改前的运行结果（如果有）")
    print("  4. 确认修改后保留了更多条目")
    print()
    print("预期效果：")
    print("  - 如果生成20个条目，修改前可能只保留10-15个")
    print("  - 修改后应该保留18-20个（假设只有1-2个完全重复）")
    print()
    print("验证命令示例：")
    print("  python run_predefined_scenarios.py")
    print("  # 然后检查 data/runs/{run_id}/empathy_scale_generation_agent_group/scale_draft.md")
    print("  # 统计条目数量，对比修改前的运行结果")
    print()
    print("=" * 80)


if __name__ == "__main__":
    print_verification_guide()

