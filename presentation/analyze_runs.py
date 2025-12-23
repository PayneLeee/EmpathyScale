"""
分析所有runs数据，生成展示用的统计摘要
"""
import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import statistics

def analyze_all_runs():
    """分析所有runs的数据"""
    runs_dir = Path("data/runs")
    if not runs_dir.exists():
        return None
    
    runs_data = {
        "total_runs": 0,
        "runs_with_interview": 0,
        "runs_with_literature": 0,
        "runs_with_scale": 0,
        "runs_with_evaluation": 0,
        "runs_with_selection": 0,
        "scenarios": defaultdict(int),
        "scale_statistics": {
            "total_items_generated": [],
            "items_per_dimension": defaultdict(list),
            "dimensions_used": set()
        },
        "evaluation_statistics": {
            "n_participants": [],
            "mean_ratings": [],
            "internal_consistency": []
        },
        "selection_statistics": {
            "original_items": [],
            "selected_items": [],
            "selection_ratios": []
        }
    }
    
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()])
    
    for run_dir in run_dirs:
        runs_data["total_runs"] += 1
        
        # 检查各个阶段
        if (run_dir / "interview_agent_group" / "summary.json").exists():
            runs_data["runs_with_interview"] += 1
            try:
                with open(run_dir / "interview_agent_group" / "summary.json", 'r', encoding='utf-8') as f:
                    interview_data = json.load(f)
                    if "name" in interview_data:
                        runs_data["scenarios"][interview_data["name"]] += 1
            except:
                pass
        
        if (run_dir / "literature_search_agent_group" / "summary.json").exists():
            runs_data["runs_with_literature"] += 1
        
        if (run_dir / "empathy_scale_generation_agent_group" / "scale_draft.md").exists():
            runs_data["runs_with_scale"] += 1
            # 统计scale items
            try:
                scale_path = run_dir / "empathy_scale_generation_agent_group" / "scale_draft.md"
                scale_text = scale_path.read_text(encoding='utf-8')
                # 简单统计item数量
                item_count = scale_text.count("- Item ")
                runs_data["scale_statistics"]["total_items_generated"].append(item_count)
                
                # 统计维度
                if "### " in scale_text:
                    dimensions = [line.replace("### ", "").strip() 
                                for line in scale_text.split("\n") 
                                if line.startswith("### ") and not line.startswith("### Purpose")]
                    for dim in dimensions:
                        runs_data["scale_statistics"]["dimensions_used"].add(dim)
            except Exception as e:
                print(f"Error analyzing scale in {run_dir}: {e}")
        
        if (run_dir / "evaluation_agent_group" / "validation" / "evaluation_summary.json").exists():
            runs_data["runs_with_evaluation"] += 1
            try:
                with open(run_dir / "evaluation_agent_group" / "validation" / "evaluation_summary.json", 'r', encoding='utf-8') as f:
                    eval_data = json.load(f)
                    if "n_participants" in eval_data:
                        runs_data["evaluation_statistics"]["n_participants"].append(eval_data["n_participants"])
                    if "overall_mean_rating" in eval_data:
                        runs_data["evaluation_statistics"]["mean_ratings"].append(eval_data["overall_mean_rating"])
                    if "validation_metrics" in eval_data and "internal_consistency" in eval_data["validation_metrics"]:
                        alpha = eval_data["validation_metrics"]["internal_consistency"].get("alpha")
                        if alpha:
                            runs_data["evaluation_statistics"]["internal_consistency"].append(alpha)
            except Exception as e:
                print(f"Error analyzing evaluation in {run_dir}: {e}")
        
        if (run_dir / "statistical_selection" / "selection_statistics.json").exists():
            runs_data["runs_with_selection"] += 1
            try:
                with open(run_dir / "statistical_selection" / "selection_statistics.json", 'r', encoding='utf-8') as f:
                    sel_data = json.load(f)
                    if "n_original_items" in sel_data:
                        runs_data["selection_statistics"]["original_items"].append(sel_data["n_original_items"])
                    if "n_selected_items" in sel_data:
                        runs_data["selection_statistics"]["selected_items"].append(sel_data["n_selected_items"])
                    if "selection_ratio" in sel_data:
                        runs_data["selection_statistics"]["selection_ratios"].append(sel_data["selection_ratio"])
            except Exception as e:
                print(f"Error analyzing selection in {run_dir}: {e}")
    
    # 计算统计摘要
    summary = {
        "overview": {
            "total_runs": runs_data["total_runs"],
            "runs_with_interview": runs_data["runs_with_interview"],
            "runs_with_literature": runs_data["runs_with_literature"],
            "runs_with_scale": runs_data["runs_with_scale"],
            "runs_with_evaluation": runs_data["runs_with_evaluation"],
            "runs_with_selection": runs_data["runs_with_selection"]
        },
        "scenarios": dict(runs_data["scenarios"]),
        "scale_statistics": {
            "total_runs_with_scales": len(runs_data["scale_statistics"]["total_items_generated"]),
            "mean_items_per_scale": statistics.mean(runs_data["scale_statistics"]["total_items_generated"]) if runs_data["scale_statistics"]["total_items_generated"] else 0,
            "min_items": min(runs_data["scale_statistics"]["total_items_generated"]) if runs_data["scale_statistics"]["total_items_generated"] else 0,
            "max_items": max(runs_data["scale_statistics"]["total_items_generated"]) if runs_data["scale_statistics"]["total_items_generated"] else 0,
            "unique_dimensions": list(runs_data["scale_statistics"]["dimensions_used"])
        },
        "evaluation_statistics": {
            "total_evaluations": len(runs_data["evaluation_statistics"]["mean_ratings"]),
            "mean_participants": statistics.mean(runs_data["evaluation_statistics"]["n_participants"]) if runs_data["evaluation_statistics"]["n_participants"] else 0,
            "mean_rating": statistics.mean(runs_data["evaluation_statistics"]["mean_ratings"]) if runs_data["evaluation_statistics"]["mean_ratings"] else 0,
            "mean_internal_consistency": statistics.mean(runs_data["evaluation_statistics"]["internal_consistency"]) if runs_data["evaluation_statistics"]["internal_consistency"] else 0
        },
        "selection_statistics": {
            "total_selections": len(runs_data["selection_statistics"]["original_items"]),
            "mean_original_items": statistics.mean(runs_data["selection_statistics"]["original_items"]) if runs_data["selection_statistics"]["original_items"] else 0,
            "mean_selected_items": statistics.mean(runs_data["selection_statistics"]["selected_items"]) if runs_data["selection_statistics"]["selected_items"] else 0,
            "mean_selection_ratio": statistics.mean(runs_data["selection_statistics"]["selection_ratios"]) if runs_data["selection_statistics"]["selection_ratios"] else 0
        }
    }
    
    return summary

if __name__ == "__main__":
    summary = analyze_all_runs()
    if summary:
        output_path = Path("presentation/run_analysis_summary.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"分析完成，结果保存到: {output_path}")
        print("\n=== 运行摘要 ===")
        print(f"总运行次数: {summary['overview']['total_runs']}")
        print(f"包含访谈的运行: {summary['overview']['runs_with_interview']}")
        print(f"包含文献搜索的运行: {summary['overview']['runs_with_literature']}")
        print(f"包含量表生成的运行: {summary['overview']['runs_with_scale']}")
        print(f"包含评估的运行: {summary['overview']['runs_with_evaluation']}")
        print(f"包含统计选择的运行: {summary['overview']['runs_with_selection']}")
        print(f"\n场景分布: {summary['scenarios']}")
        if summary['scale_statistics']['total_runs_with_scales'] > 0:
            print(f"\n量表统计:")
            print(f"  平均项目数: {summary['scale_statistics']['mean_items_per_scale']:.1f}")
            print(f"  项目数范围: {summary['scale_statistics']['min_items']}-{summary['scale_statistics']['max_items']}")
            print(f"  维度数: {len(summary['scale_statistics']['unique_dimensions'])}")
        if summary['evaluation_statistics']['total_evaluations'] > 0:
            print(f"\n评估统计:")
            print(f"  平均参与者数: {summary['evaluation_statistics']['mean_participants']:.0f}")
            print(f"  平均评分: {summary['evaluation_statistics']['mean_rating']:.2f}")
            print(f"  平均内部一致性: {summary['evaluation_statistics']['mean_internal_consistency']:.3f}")
    else:
        print("未找到runs数据")

