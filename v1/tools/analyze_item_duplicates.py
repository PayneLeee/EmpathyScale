"""
分析条目重复性的工具脚本

检查生成的条目是否有重复，以及重复性程度。

Usage:
    python tools/analyze_item_duplicates.py
"""

import sys
import os
import json
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "agents"))

from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager


def normalize_text(text: str) -> str:
    """标准化文本用于比较（去除大小写、标点、多余空格）"""
    import re
    # 转换为小写，去除标点，标准化空格
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # 去除标点
    text = " ".join(text.split())  # 标准化空格
    return text


def similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度（0-1）"""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def analyze_duplicates(items: list, threshold: float = 0.8) -> dict:
    """
    分析条目重复性
    
    Args:
        items: 条目列表，每个条目是 {"dimension": "...", "item_text": "..."}
        threshold: 相似度阈值，超过此值视为重复
    
    Returns:
        分析结果字典
    """
    # 1. 精确重复检查（标准化后）
    normalized_items = {}
    exact_duplicates = []
    for idx, item in enumerate(items):
        norm_text = normalize_text(item.get("item_text", ""))
        if norm_text in normalized_items:
            exact_duplicates.append({
                "original_idx": normalized_items[norm_text],
                "duplicate_idx": idx,
                "text": item.get("item_text", "")
            })
        else:
            normalized_items[norm_text] = idx
    
    # 2. 高相似度检查
    high_similarity_pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            text1 = items[i].get("item_text", "")
            text2 = items[j].get("item_text", "")
            sim = similarity(text1, text2)
            if sim >= threshold:
                high_similarity_pairs.append({
                    "idx1": i,
                    "idx2": j,
                    "similarity": sim,
                    "text1": text1,
                    "text2": text2
                })
    
    # 3. 统计信息
    total_items = len(items)
    unique_normalized = len(normalized_items)
    exact_dup_count = len(exact_duplicates)
    high_sim_count = len(high_similarity_pairs)
    
    # 4. 按维度统计
    dimension_counts = Counter(item.get("dimension", "Unknown") for item in items)
    
    return {
        "total_items": total_items,
        "unique_items_after_normalization": unique_normalized,
        "exact_duplicates_count": exact_dup_count,
        "high_similarity_pairs_count": high_sim_count,
        "duplication_rate": (total_items - unique_normalized) / total_items * 100 if total_items > 0 else 0,
        "dimension_distribution": dict(dimension_counts),
        "exact_duplicates": exact_duplicates[:10],  # 只显示前10个
        "high_similarity_pairs": sorted(high_similarity_pairs, key=lambda x: x["similarity"], reverse=True)[:10]  # 只显示前10个
    }


def main():
    """从最新的运行中加载条目并分析重复性"""
    dm = DataManager()
    project_root = Path(__file__).parent.parent
    
    # 找到最新的运行
    runs_dir = project_root / "data/runs"
    if not runs_dir.exists():
        print("[ERROR] 未找到运行数据目录")
        return
    
    # 获取最新的运行ID（从测试运行）
    test_run_id = "2025-12-18_145541"
    run_path = runs_dir / test_run_id
    
    all_items = None
    
    if run_path.exists():
        # 尝试从已有运行中加载
        draft_path = run_path / "empathy_scale_generation_agent_group" / "scale_draft.md"
        if draft_path.exists():
            md_text = draft_path.read_text(encoding="utf-8", errors="replace")
            all_items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
            print(f"[OK] 从运行 {test_run_id} 加载了 {len(all_items)} 个条目")
    
    if all_items is None:
        print(f"[INFO] 运行 {test_run_id} 中没有找到量表草稿，重新生成条目进行分析...")
        
        # 重新生成条目（不进行内容评估）
        config = json.loads((project_root / "config.json").read_text(encoding="utf-8"))
        api_key = config["openai_api_key"]
        prompt_manager = PromptManager()
        
        from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
        
        gen_agent = EmpathyScaleGenerationAgentGroup(
            api_key=api_key,
            prompts_dir=prompt_manager.prompts_dir,
            num_item_generators=5,
            enable_content_assessment=False  # 跳过内容评估，直接分析原始条目
        )
        
        # 使用测试场景
        test_scenario = {
            "name": "test_collab_robot",
            "assessment_context": "factory assembly, human-robot teammate",
            "robot_platform": "collaborative arm",
            "interaction_modalities": "gesture + voice",
            "collaboration_pattern": "turn-taking assembly",
            "environmental_setting": "factory floor",
        }
        
        # 创建临时运行
        temp_run_id = dm.new_run()
        ensure_summary(temp_run_id, test_scenario, dm)
        
        # 生成条目
        print("[INFO] 正在生成条目...")
        constructs = gen_agent._run_construct_definition(test_scenario)
        candidates = gen_agent._run_multi_item_generation(constructs, test_scenario)
        
        # 展平条目列表
        all_items = []
        for block in candidates:
            dimension = block.get("dimension", "Unknown")
            for item_text in block.get("items", []):
                all_items.append({
                    "dimension": dimension,
                    "item_text": item_text
                })
        
        print(f"[OK] 生成了 {len(all_items)} 个条目")
    
    if not all_items:
        print("[ERROR] 没有找到条目")
        return
    
    # 分析重复性
    print("\n" + "="*80)
    print("条目重复性分析")
    print("="*80)
    
    results = analyze_duplicates(all_items, threshold=0.8)
    
    print(f"\n📊 总体统计:")
    print(f"  - 总条目数: {results['total_items']}")
    print(f"  - 去重后唯一条目数: {results['unique_items_after_normalization']}")
    print(f"  - 精确重复数: {results['exact_duplicates_count']}")
    print(f"  - 高相似度对（相似度≥80%）: {results['high_similarity_pairs_count']}")
    print(f"  - 重复率: {results['duplication_rate']:.2f}%")
    
    print(f"\n📋 维度分布:")
    for dim, count in results['dimension_distribution'].items():
        print(f"  - {dim}: {count} 个条目")
    
    if results['exact_duplicates']:
        print(f"\n[WARN] 精确重复示例（前{min(10, len(results['exact_duplicates']))}个）:")
        for dup in results['exact_duplicates'][:5]:
            print(f"  - 条目 {dup['original_idx']} 和 {dup['duplicate_idx']}:")
            print(f"    \"{dup['text'][:80]}...\"")
    
    if results['high_similarity_pairs']:
        print(f"\n[WARN] 高相似度条目对示例（前{min(10, len(results['high_similarity_pairs']))}个）:")
        for pair in results['high_similarity_pairs'][:5]:
            print(f"  - 相似度 {pair['similarity']:.2%}:")
            print(f"    条目 {pair['idx1']}: \"{pair['text1'][:60]}...\"")
            print(f"    条目 {pair['idx2']}: \"{pair['text2'][:60]}...\"")
    
    # 评估结果
    print("\n" + "="*80)
    print("评估结果")
    print("="*80)
    
    if results['duplication_rate'] < 5:
        print("[OK] 重复率很低（<5%），条目多样性良好")
    elif results['duplication_rate'] < 15:
        print("[WARN] 重复率中等（5-15%），可以考虑进一步去重")
    else:
        print("[ERROR] 重复率较高（>15%），建议进行更严格的去重")
    
    if results['exact_duplicates_count'] == 0:
        print("[OK] 没有发现精确重复，去重逻辑有效")
    else:
        print(f"[WARN] 发现 {results['exact_duplicates_count']} 个精确重复")
    
    if results['high_similarity_pairs_count'] < results['total_items'] * 0.1:
        print("[OK] 高相似度条目对较少，条目多样性良好")
    else:
        print(f"[WARN] 高相似度条目对较多（{results['high_similarity_pairs_count']}对），可能需要语义去重")
    
    # 保存分析结果
    output_path = project_root / "data/test_runs" / test_run_id / "duplicate_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] 分析结果已保存到: {output_path}")


def ensure_summary(run_id: str, scenario: dict, dm: DataManager):
    """创建interview和literature summary stubs"""
    run_dir = dm.get_run_path(run_id)
    
    interview_dir = run_dir / "interview_agent_group"
    interview_dir.mkdir(parents=True, exist_ok=True)
    (interview_dir / "summary.json").write_text(
        json.dumps(scenario, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    lit_dir = run_dir / "literature_search_agent_group"
    lit_dir.mkdir(parents=True, exist_ok=True)
    (lit_dir / "summary.json").write_text("{}", encoding="utf-8")


if __name__ == "__main__":
    main()


