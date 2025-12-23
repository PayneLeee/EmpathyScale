"""
选择每个场景最好的实验用于展示
评估标准：内部一致性、区分性、项目质量等
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import statistics

def load_evaluation_summary(run_dir: Path) -> Optional[Dict]:
    """加载评估摘要"""
    eval_path = run_dir / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
    if eval_path.exists():
        try:
            with open(eval_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def load_interview_summary(run_dir: Path) -> Optional[Dict]:
    """加载访谈摘要"""
    interview_path = run_dir / "interview_agent_group" / "summary.json"
    if interview_path.exists():
        try:
            with open(interview_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def load_selection_stats(run_dir: Path) -> Optional[Dict]:
    """加载统计选择摘要"""
    sel_path = run_dir / "statistical_selection" / "selection_statistics.json"
    if sel_path.exists():
        try:
            with open(sel_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def load_efa_cfa_results(run_dir: Path) -> Optional[Dict]:
    """加载EFA/CFA结果，获取因子数量"""
    efa_cfa_path = run_dir / "statistical_selection" / "efa_cfa_results.json"
    if efa_cfa_path.exists():
        try:
            with open(efa_cfa_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def calculate_quality_score(eval_data: Dict, sel_data: Optional[Dict] = None) -> float:
    """计算质量分数"""
    score = 0.0
    
    # 内部一致性 (权重: 40%)
    if "validation_metrics" in eval_data and "internal_consistency" in eval_data["validation_metrics"]:
        alpha = eval_data["validation_metrics"]["internal_consistency"].get("alpha", 0)
        score += alpha * 0.4
    
    # 区分性 (权重: 40%)
    if "validation_metrics" in eval_data and "discriminant_ability" in eval_data["validation_metrics"]:
        disc = eval_data["validation_metrics"]["discriminant_ability"]
        cohens_d = disc.get("cohens_d", 0)
        # Cohen's d > 2.0 是优秀，归一化到0-1
        normalized_d = min(cohens_d / 3.0, 1.0)  # 假设3.0是上限
        score += normalized_d * 0.4
    
    # 项目数量合理性 (权重: 10%)
    # 理想项目数：15-20项
    if sel_data and "n_selected_items" in sel_data:
        n_items = sel_data["n_selected_items"]
        if 15 <= n_items <= 20:
            score += 0.1
        elif 10 <= n_items < 15 or 20 < n_items <= 25:
            score += 0.05
    
    # 统计显著性 (权重: 10%)
    if "validation_metrics" in eval_data and "discriminant_ability" in eval_data["validation_metrics"]:
        disc = eval_data["validation_metrics"]["discriminant_ability"]
        if disc.get("significant", False):
            score += 0.1
    
    return score

def analyze_all_runs():
    """分析所有runs，找出每个场景最好的实验"""
    runs_dir = Path("data/runs")
    if not runs_dir.exists():
        return None
    
    # 按场景组织实验
    experiments_by_scenario = {
        "collab_robot_assembly": [],
        "home_service_robot": [],
        "counseling_chatbot": []
    }
    
    # 分析每个run
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()])
    
    for run_dir in run_dirs:
        # 获取场景信息
        interview_data = load_interview_summary(run_dir)
        if not interview_data or "name" not in interview_data:
            continue
        
        scenario = interview_data["name"]
        if scenario not in experiments_by_scenario:
            continue
        
        # 加载评估和选择数据
        eval_data = load_evaluation_summary(run_dir)
        sel_data = load_selection_stats(run_dir)
        efa_cfa_data = load_efa_cfa_results(run_dir)
        
        if not eval_data:
            continue
        
        # 计算质量分数
        quality_score = calculate_quality_score(eval_data, sel_data)
        
        # 提取关键指标
        alpha = eval_data.get("validation_metrics", {}).get("internal_consistency", {}).get("alpha", 0)
        cohens_d = eval_data.get("validation_metrics", {}).get("discriminant_ability", {}).get("cohens_d", 0)
        n_selected = sel_data.get("n_selected_items", 0) if sel_data else 0
        n_original = sel_data.get("n_original_items", 0) if sel_data else 0
        n_factors = efa_cfa_data.get("n_factors", 1) if efa_cfa_data else 1
        
        experiments_by_scenario[scenario].append({
            "run_id": run_dir.name,
            "run_dir": str(run_dir),
            "quality_score": quality_score,
            "alpha": alpha,
            "cohens_d": cohens_d,
            "n_selected_items": n_selected,
            "n_original_items": n_original,
            "n_factors": n_factors,
            "eval_data": eval_data,
            "sel_data": sel_data,
            "interview_data": interview_data
        })
    
    # 为每个场景选择最好的实验
    # 优先选择多因子结构（n_factors >= 2）的实验
    best_experiments = {}
    for scenario, experiments in experiments_by_scenario.items():
        if not experiments:
            continue
        
        # 分离多因子和单因子实验
        multi_factor_experiments = [exp for exp in experiments if exp.get("n_factors", 1) >= 2]
        single_factor_experiments = [exp for exp in experiments if exp.get("n_factors", 1) < 2]
        
        # 优先选择多因子实验
        if multi_factor_experiments:
            # 多因子实验中按质量分数排序
            multi_factor_experiments.sort(key=lambda x: x["quality_score"], reverse=True)
            best_experiments[scenario] = multi_factor_experiments[0]
        elif single_factor_experiments:
            # 如果没有多因子，选择单因子中最好的
            single_factor_experiments.sort(key=lambda x: x["quality_score"], reverse=True)
            best_experiments[scenario] = single_factor_experiments[0]
        else:
            # 如果都没有，按原逻辑选择
            experiments.sort(key=lambda x: x["quality_score"], reverse=True)
            best_experiments[scenario] = experiments[0]
    
    return {
        "best_experiments": best_experiments,
        "all_experiments": experiments_by_scenario
    }

def identify_ablation_experiments():
    """识别消融实验"""
    ablation_dir = Path("data/ablation_studies")
    ablation_runs = []
    
    if ablation_dir.exists():
        # 查找消融实验的运行目录
        for scenario_dir in ablation_dir.iterdir():
            if scenario_dir.is_dir():
                summary_path = scenario_dir / "ablation_summary.json"
                if summary_path.exists():
                    try:
                        with open(summary_path, 'r', encoding='utf-8') as f:
                            ablation_summary = json.load(f)
                        
                        # 提取变体信息
                        if "variants" in ablation_summary:
                            for variant_name, variant_data in ablation_summary["variants"].items():
                                if "run_id" in variant_data:
                                    ablation_runs.append({
                                        "variant": variant_name,
                                        "scenario": scenario_dir.name,
                                        "run_id": variant_data["run_id"],
                                        "run_dir": f"data/runs/{variant_data['run_id']}",
                                        "summary": variant_data
                                    })
                    except:
                        pass
    
    return ablation_runs

if __name__ == "__main__":
    print("分析所有实验...")
    
    # 分析主实验
    results = analyze_all_runs()
    
    # 识别消融实验
    ablation_runs = identify_ablation_experiments()
    
    # 生成选择报告
    selection_report = {
        "main_experiments": {},
        "ablation_experiments": ablation_runs,
        "selection_criteria": {
            "priority": "优先选择多因子结构（n_factors >= 2）的实验",
            "quality_score_components": {
                "internal_consistency": "40% (Cronbach's alpha)",
                "discriminant_ability": "40% (Cohen's d)",
                "item_count_reasonableness": "10% (15-20 items ideal)",
                "statistical_significance": "10% (p < 0.05)"
            },
            "factor_structure_preference": "多因子结构（>=2个因子）优先于单因子结构"
        }
    }
    
    if results:
        for scenario, best_exp in results["best_experiments"].items():
            selection_report["main_experiments"][scenario] = {
                "run_id": best_exp["run_id"],
                "run_dir": best_exp["run_dir"],
                "quality_score": best_exp["quality_score"],
                "metrics": {
                    "internal_consistency_alpha": best_exp["alpha"],
                    "cohens_d": best_exp["cohens_d"],
                    "n_selected_items": best_exp["n_selected_items"],
                    "n_original_items": best_exp["n_original_items"],
                    "n_factors": best_exp.get("n_factors", 1)
                },
                "interview_summary": {
                    "assessment_context": best_exp["interview_data"].get("assessment_context", ""),
                    "robot_platform": best_exp["interview_data"].get("robot_platform", ""),
                    "interaction_modalities": best_exp["interview_data"].get("interaction_modalities", "")
                }
            }
    
    # 保存报告
    output_path = Path("presentation/experiment_selection.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(selection_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n实验选择完成！结果保存到: {output_path}")
    print("\n=== 选择的主实验 ===")
    for scenario, exp in selection_report["main_experiments"].items():
        print(f"\n{scenario}:")
        print(f"  Run ID: {exp['run_id']}")
        print(f"  质量分数: {exp['quality_score']:.3f}")
        print(f"  内部一致性: α = {exp['metrics']['internal_consistency_alpha']:.3f}")
        print(f"  区分性: Cohen's d = {exp['metrics']['cohens_d']:.3f}")
        print(f"  项目数: {exp['metrics']['n_selected_items']} / {exp['metrics']['n_original_items']}")
        print(f"  因子数: {exp['metrics'].get('n_factors', 1)}")
        print(f"  目录: {exp['run_dir']}")
    
    if ablation_runs:
        print("\n=== 消融实验 ===")
        for ablation in ablation_runs:
            print(f"\n变体: {ablation['variant']}")
            print(f"  场景: {ablation['scenario']}")
            print(f"  Run ID: {ablation['run_id']}")
            print(f"  目录: {ablation['run_dir']}")
