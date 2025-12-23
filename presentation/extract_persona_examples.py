"""
提取每个场景的代表性persona示例用于展示
"""
import json
from pathlib import Path
from typing import List, Dict

def load_personas(run_id: str) -> List[Dict]:
    """加载persona数据"""
    eval_path = Path(f"data/runs/{run_id}/evaluation_agent_group/validation/participant_level_evaluations.json")
    if not eval_path.exists():
        return []
    
    with open(eval_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取唯一的persona
    personas_dict = {}
    for entry in data:
        persona = entry.get('persona', {})
        persona_id = persona.get('persona_id')
        if persona_id and persona_id not in personas_dict:
            personas_dict[persona_id] = persona
    
    return list(personas_dict.values())

def select_representative_personas(personas: List[Dict], n_examples: int = 3) -> List[Dict]:
    """选择有代表性的persona示例"""
    if len(personas) <= n_examples:
        return personas
    
    # 选择策略：多样化（年龄、性别、教育、职业、ATI分数）
    selected = []
    used_combinations = set()
    
    # 按empathy_condition分组
    empathic = [p for p in personas if p.get('empathy_condition') == 'empathic']
    non_empathic = [p for p in personas if p.get('empathy_condition') == 'non_empathic']
    
    # 从共情组选择
    for p in empathic[:n_examples//2 + 1]:
        key = (p.get('age'), p.get('gender'), p.get('profession'))
        if key not in used_combinations:
            selected.append(p)
            used_combinations.add(key)
            if len(selected) >= n_examples:
                break
    
    # 从非共情组选择
    for p in non_empathic[:n_examples//2]:
        key = (p.get('age'), p.get('gender'), p.get('profession'))
        if key not in used_combinations:
            selected.append(p)
            used_combinations.add(key)
            if len(selected) >= n_examples:
                break
    
    return selected[:n_examples]

def format_persona(p: Dict) -> Dict:
    """格式化persona信息"""
    return {
        "age": p.get('age'),
        "gender": p.get('gender'),
        "education": p.get('education'),
        "profession": p.get('profession'),
        "ati_score": p.get('ati_score'),
        "tech_experience": p.get('tech_experience'),
        "empathy_condition": p.get('empathy_condition'),
        "concrete_interaction_experience": p.get('concrete_interaction_experience', '')
    }

def extract_scenario_settings(run_id: str) -> Dict:
    """提取场景设定"""
    interview_path = Path(f"data/runs/{run_id}/interview_agent_group/summary.json")
    if interview_path.exists():
        with open(interview_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def main():
    """主函数"""
    selected_experiments = {
        "collab_robot_assembly": "2025-12-22_215026",
        "home_service_robot": "2025-12-22_210718",
        "counseling_chatbot": "2025-12-22_212205"
    }
    
    results = {}
    
    for scenario_id, run_id in selected_experiments.items():
        print(f"\n处理场景: {scenario_id}")
        
        # 提取场景设定
        scenario_settings = extract_scenario_settings(run_id)
        
        # 提取persona
        all_personas = load_personas(run_id)
        print(f"  找到 {len(all_personas)} 个persona")
        
        # 选择代表性persona
        representative_personas = select_representative_personas(all_personas, n_examples=4)
        print(f"  选择了 {len(representative_personas)} 个代表性persona")
        
        results[scenario_id] = {
            "run_id": run_id,
            "scenario_settings": scenario_settings,
            "representative_personas": [format_persona(p) for p in representative_personas]
        }
    
    # 保存结果
    output_path = Path("presentation/persona_examples.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Persona示例已保存到: {output_path}")
    return results

if __name__ == "__main__":
    results = main()
    
    # 打印摘要
    print("\n=== 提取摘要 ===")
    for scenario, data in results.items():
        print(f"\n{scenario}:")
        print(f"  场景设定: {data['scenario_settings'].get('assessment_context', 'N/A')}")
        print(f"  代表性persona数: {len(data['representative_personas'])}")
        for i, p in enumerate(data['representative_personas'][:2], 1):
            print(f"    Persona {i}: {p.get('age')}岁, {p.get('gender')}, {p.get('profession')}, "
                  f"ATI={p.get('ati_score')}, {p.get('empathy_condition')}")
