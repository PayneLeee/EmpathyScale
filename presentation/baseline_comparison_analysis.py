"""
分析生成的量表与baseline（PETS、RoPE）的定性和定量对比
"""
import json
from pathlib import Path
from typing import Dict, List

def load_baseline_evaluation(scenario_id: str, baseline_name: str) -> Dict:
    """加载baseline评估结果"""
    baseline_path = Path(f"data/baseline_comparison/{scenario_id}/{baseline_name}/evaluation_summary.json")
    if baseline_path.exists():
        with open(baseline_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_generated_evaluation(run_id: str) -> Dict:
    """加载生成量表的评估结果"""
    eval_path = Path(f"data/runs/{run_id}/evaluation_agent_group/validation/evaluation_summary.json")
    if eval_path.exists():
        with open(eval_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_generated_scale(run_id: str) -> List[Dict]:
    """加载生成的量表条目"""
    scale_path = Path(f"data/runs/{run_id}/empathy_scale_generation_agent_group/filtered_scale_draft.md")
    if scale_path.exists():
        text = scale_path.read_text(encoding='utf-8')
        items = []
        current_dimension = None
        item_id = 1
        
        for line in text.split('\n'):
            if line.startswith('### '):
                current_dimension = line.replace('### ', '').strip()
            elif line.startswith('- Item ') or line.startswith('- '):
                item_text = line.split(':', 1)[1].strip() if ':' in line else line.replace('- Item ', '').replace('- ', '').strip()
                if item_text:
                    items.append({
                        'item_id': item_id,
                        'dimension': current_dimension or 'Unknown',
                        'item_text': item_text
                    })
                    item_id += 1
        return items
    return []

def extract_pets_items() -> List[Dict]:
    """提取PETS条目"""
    pets_items = [
        {"item_id": 1, "dimension": "PETS-ER", "item_text": "The system considered my mental state."},
        {"item_id": 2, "dimension": "PETS-ER", "item_text": "The system seemed emotionally intelligent."},
        {"item_id": 3, "dimension": "PETS-ER", "item_text": "The system expressed emotions."},
        {"item_id": 4, "dimension": "PETS-ER", "item_text": "The system sympathized with me."},
        {"item_id": 5, "dimension": "PETS-ER", "item_text": "The system showed interest in me."},
        {"item_id": 6, "dimension": "PETS-ER", "item_text": "The system supported me in coping with an emotional situation."},
        {"item_id": 7, "dimension": "PETS-UT", "item_text": "The system understood my goals."},
        {"item_id": 8, "dimension": "PETS-UT", "item_text": "The system understood my needs."},
        {"item_id": 9, "dimension": "PETS-UT", "item_text": "I trusted the system."},
        {"item_id": 10, "dimension": "PETS-UT", "item_text": "The system understood my intentions."},
    ]
    return pets_items

def extract_rope_items() -> List[Dict]:
    """提取RoPE条目（主要条目，不包括filler items）"""
    rope_items = [
        # Empathic Understanding
        {"item_id": 1, "dimension": "Empathic Understanding", "item_text": "The robot appreciates exactly how the things I experience feel to me."},
        {"item_id": 2, "dimension": "Empathic Understanding", "item_text": "The robot knows me and my needs."},
        {"item_id": 3, "dimension": "Empathic Understanding", "item_text": "The robot cares about my feelings."},
        {"item_id": 4, "dimension": "Empathic Understanding", "item_text": "The robot does not understand me."},  # reversed
        {"item_id": 5, "dimension": "Empathic Understanding", "item_text": "The robot perceives and accepts my individual characteristics."},
        {"item_id": 6, "dimension": "Empathic Understanding", "item_text": "The robot usually understands the whole of what I mean."},
        {"item_id": 7, "dimension": "Empathic Understanding", "item_text": "The robot reacts to my words but does not see the way I feel."},  # reversed
        {"item_id": 8, "dimension": "Empathic Understanding", "item_text": "The robot seems to feel bad when I am sad or disappointed."},
        # Empathic Response
        {"item_id": 9, "dimension": "Empathic Response", "item_text": "Whether thoughts or feelings I express are \"good\" or \"bad\" makes no difference to the robot's actions toward me."},  # reversed
        {"item_id": 10, "dimension": "Empathic Response", "item_text": "No matter what I tell about myself, the robot acts just the same."},  # reversed
        {"item_id": 11, "dimension": "Empathic Response", "item_text": "The robot comforts me when I am upset."},
        {"item_id": 12, "dimension": "Empathic Response", "item_text": "The robot encourages me."},
        {"item_id": 13, "dimension": "Empathic Response", "item_text": "The robot praises me when I have done something well."},
        {"item_id": 14, "dimension": "Empathic Response", "item_text": "The robot helps me when I need it."},
        {"item_id": 15, "dimension": "Empathic Response", "item_text": "The robot knows when I want to talk and lets me do so."},
        {"item_id": 16, "dimension": "Empathic Response", "item_text": "The robot's response to me is so fixed and automatic that I do not get through to it."},  # reversed
    ]
    return rope_items

def analyze_comparison():
    """分析对比"""
    # 选择的实验
    selected_experiments = {
        "collab_robot_assembly": "2025-12-22_215026",
        "home_service_robot": "2025-12-22_210718",
        "counseling_chatbot": "2025-12-22_212205"
    }
    
    comparison_results = {}
    
    for scenario_id, run_id in selected_experiments.items():
        print(f"\n分析场景: {scenario_id}")
        
        # 加载数据
        generated_eval = load_generated_evaluation(run_id)
        generated_items = load_generated_scale(run_id)
        pets_eval = load_baseline_evaluation(scenario_id, "PETS")
        rope_eval = load_baseline_evaluation(scenario_id, "RoPE")
        
        if not generated_eval or not generated_items:
            print(f"  警告: 无法加载生成量表数据 (Run: {run_id})")
            continue
        
        # 提取指标
        gen_alpha = generated_eval.get("validation_metrics", {}).get("internal_consistency", {}).get("alpha", 0)
        gen_cohens_d = generated_eval.get("validation_metrics", {}).get("discriminant_ability", {}).get("cohens_d", 0)
        gen_n_items = len(generated_items)
        
        pets_alpha = pets_eval.get("validation_metrics", {}).get("internal_consistency", {}).get("alpha", 0) if pets_eval else 0
        pets_cohens_d = pets_eval.get("validation_metrics", {}).get("discriminant_ability", {}).get("cohens_d", 0) if pets_eval else 0
        
        rope_alpha = rope_eval.get("validation_metrics", {}).get("internal_consistency", {}).get("alpha", 0) if rope_eval else 0
        rope_cohens_d = rope_eval.get("validation_metrics", {}).get("discriminant_ability", {}).get("cohens_d", 0) if rope_eval else 0
        
        comparison_results[scenario_id] = {
            "generated": {
                "run_id": run_id,
                "n_items": gen_n_items,
                "alpha": gen_alpha,
                "cohens_d": gen_cohens_d,
                "items": generated_items
            },
            "PETS": {
                "n_items": 10,
                "alpha": pets_alpha,
                "cohens_d": pets_cohens_d,
                "items": extract_pets_items() if pets_eval else []
            },
            "RoPE": {
                "n_items": 16,  # 不包括filler items
                "alpha": rope_alpha,
                "cohens_d": rope_cohens_d,
                "items": extract_rope_items() if rope_eval else []
            }
        }
    
    # 保存结果
    output_path = Path("presentation/baseline_comparison_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n对比分析完成！结果保存到: {output_path}")
    return comparison_results

if __name__ == "__main__":
    results = analyze_comparison()
    
    # 打印摘要
    print("\n=== 对比摘要 ===")
    for scenario, data in results.items():
        print(f"\n{scenario}:")
        print(f"  生成量表: {data['generated']['n_items']}项, α={data['generated']['alpha']:.3f}, d={data['generated']['cohens_d']:.3f}")
        if data['PETS']['alpha'] > 0:
            print(f"  PETS: 10项, α={data['PETS']['alpha']:.3f}, d={data['PETS']['cohens_d']:.3f}")
        if data['RoPE']['alpha'] > 0:
            print(f"  RoPE: 16项, α={data['RoPE']['alpha']:.3f}, d={data['RoPE']['cohens_d']:.3f}")
