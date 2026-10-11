"""
分析筛选后条目的语义重复性

检查筛选后的条目是否有语义重复，以及如何优化筛选策略。

Usage:
    python tools/analyze_semantic_duplicates.py
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


def normalize_text(text: str) -> str:
    """标准化文本用于比较（去除大小写、标点、多余空格）"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # 去除标点
    text = " ".join(text.split())  # 标准化空格
    return text


def similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度（0-1）"""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def analyze_semantic_duplicates(items: list, threshold: float = 0.7) -> dict:
    """
    分析条目语义重复性
    
    Args:
        items: 条目列表，每个条目是 {"dimension": "...", "item_text": "..."}
        threshold: 相似度阈值，超过此值视为语义重复
    
    Returns:
        分析结果字典
    """
    # 1. 精确重复检查
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
    
    # 2. 高相似度检查（语义重复）
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
                    "text2": text2,
                    "dimension1": items[i].get("dimension", "Unknown"),
                    "dimension2": items[j].get("dimension", "Unknown")
                })
    
    # 3. 按维度统计
    dimension_counts = Counter(item.get("dimension", "Unknown") for item in items)
    
    # 4. 计算重复率
    total_items = len(items)
    unique_normalized = len(normalized_items)
    exact_dup_count = len(exact_duplicates)
    high_sim_count = len(high_similarity_pairs)
    
    return {
        "total_items": total_items,
        "unique_items_after_normalization": unique_normalized,
        "exact_duplicates_count": exact_dup_count,
        "high_similarity_pairs_count": high_sim_count,
        "duplication_rate": (total_items - unique_normalized) / total_items * 100 if total_items > 0 else 0,
        "semantic_duplication_rate": high_sim_count / (total_items * (total_items - 1) / 2) * 100 if total_items > 1 else 0,
        "dimension_distribution": dict(dimension_counts),
        "exact_duplicates": exact_duplicates[:20],
        "high_similarity_pairs": sorted(high_similarity_pairs, key=lambda x: x["similarity"], reverse=True)[:30]
    }


def main():
    """分析测试运行结果"""
    project_root = Path(__file__).parent.parent
    run_id = "2025-12-18_154237"
    
    # 加载筛选后的条目
    filtered_draft_path = project_root / f"data/runs/{run_id}/empathy_scale_generation_agent_group/filtered_scale_draft.md"
    if not filtered_draft_path.exists():
        print(f"[ERROR] 未找到筛选后的量表草稿: {filtered_draft_path}")
        return
    
    md_text = filtered_draft_path.read_text(encoding="utf-8", errors="replace")
    filtered_items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
    
    if not filtered_items:
        print("[ERROR] 没有找到筛选后的条目")
        return
    
    print("="*80)
    print("筛选后条目语义重复性分析")
    print("="*80)
    print(f"\n筛选后条目总数: {len(filtered_items)}")
    print(f"目标范围: 10-20个条目")
    
    # 分析语义重复
    results = analyze_semantic_duplicates(filtered_items, threshold=0.7)
    
    print(f"\n[统计信息]")
    print(f"  - 总条目数: {results['total_items']}")
    print(f"  - 去重后唯一条目数: {results['unique_items_after_normalization']}")
    print(f"  - 精确重复数: {results['exact_duplicates_count']}")
    print(f"  - 高相似度对（相似度≥70%）: {results['high_similarity_pairs_count']}")
    print(f"  - 精确重复率: {results['duplication_rate']:.2f}%")
    print(f"  - 语义重复率: {results['semantic_duplication_rate']:.2f}%")
    
    print(f"\n[维度分布]")
    for dim, count in results['dimension_distribution'].items():
        print(f"  - {dim}: {count} 个条目")
    
    # 显示高相似度条目对
    if results['high_similarity_pairs']:
        print(f"\n[高相似度条目对示例] (前20个)")
        for idx, pair in enumerate(results['high_similarity_pairs'][:20], 1):
            print(f"\n  {idx}. 相似度 {pair['similarity']:.1%}:")
            print(f"     条目 {pair['idx1']+1} [{pair['dimension1']}]: \"{pair['text1'][:70]}...\"")
            print(f"     条目 {pair['idx2']+1} [{pair['dimension2']}]: \"{pair['text2'][:70]}...\"")
    
    # 加载评估数据
    eval_summary_path = project_root / f"data/runs/{run_id}/evaluation_agent_group/selection/evaluation_summary.json"
    if eval_summary_path.exists():
        eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
        selected_ids = json.loads((project_root / f"data/runs/{run_id}/statistical_selection/selected_item_ids.json").read_text(encoding="utf-8"))
        
        # 分析筛选后的条目评分分布
        selected_items_stats = [
            item for item in eval_summary.get("item_statistics", [])
            if item.get("item_id") in selected_ids
        ]
        
        if selected_items_stats:
            means = [s["rating_statistics"]["mean"] for s in selected_items_stats if s["rating_statistics"].get("mean") is not None]
            stds = [s["rating_statistics"]["std"] for s in selected_items_stats if s["rating_statistics"].get("std") is not None]
            
            print(f"\n[筛选后条目评分统计]")
            print(f"  - 平均评分范围: {min(means):.2f} - {max(means):.2f}")
            print(f"  - 平均评分: {sum(means)/len(means):.2f}")
            print(f"  - 标准差范围: {min(stds):.2f} - {max(stds):.2f}")
            print(f"  - 平均标准差: {sum(stds)/len(stds):.2f}")
    
    # 评估和建议
    print("\n" + "="*80)
    print("评估和建议")
    print("="*80)
    
    if results['exact_duplicates_count'] == 0:
        print("[OK] 没有发现精确重复")
    else:
        print(f"[WARN] 发现 {results['exact_duplicates_count']} 个精确重复")
    
    if results['high_similarity_pairs_count'] == 0:
        print("[OK] 没有发现高相似度条目对（语义重复）")
    elif results['high_similarity_pairs_count'] < len(filtered_items) * 0.1:
        print(f"[OK] 语义重复率较低（{results['high_similarity_pairs_count']}对，约{results['semantic_duplication_rate']:.1f}%）")
    else:
        print(f"[WARN] 语义重复率较高（{results['high_similarity_pairs_count']}对，约{results['semantic_duplication_rate']:.1f}%）")
        print("      建议：使用更严格的筛选策略或语义去重")
    
    if len(filtered_items) > 20:
        print(f"\n[WARN] 筛选后条目数（{len(filtered_items)}）超过目标范围（10-20）")
        print("      建议：")
        print("      1. 提高筛选阈值（min_mean_rating从60提高到75-80）")
        print("      2. 降低标准差阈值（max_std从30降低到20-25）")
        print("      3. 使用百分位数筛选（保留前20-30%）")
        print("      4. 使用维度平衡筛选（每个维度保留3-5个条目）")
    elif len(filtered_items) < 10:
        print(f"\n[WARN] 筛选后条目数（{len(filtered_items)}）低于目标范围（10-20）")
        print("      建议：降低筛选阈值或使用更宽松的筛选策略")
    else:
        print(f"\n[OK] 筛选后条目数（{len(filtered_items)}）在目标范围内（10-20）")
    
    # 保存分析结果
    output_path = project_root / "data/test_runs/20251218_154237/semantic_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] 分析结果已保存到: {output_path}")


if __name__ == "__main__":
    main()


