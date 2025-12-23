"""
Run a single ablation variant for re-running failed experiments.

NOTE: This is a debugging tool for re-running individual variants.
For complete ablation study with full Phase 1/2 evaluation, use run_ablation_minimal.py instead.

Usage:
    python run_single_variant.py multi_no_content
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from agents.evaluation_agent_group import EvaluationAgentGroup
from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text:^{width}}")
    print(f"{char * width}\n")


def print_step(step_num: int, total_steps: int, description: str):
    """Print a step indicator."""
    print(f"[{step_num}/{total_steps}] {description}...")


def print_success(message: str):
    """Print a success message."""
    print(f"[OK] {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"[INFO] {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"[WARN] {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"[ERROR] {message}")


BASE_SCENARIO = {
    "name": "collab_robot_assembly",
    "assessment_context": "factory assembly, human-robot teammate",
    "robot_platform": "collaborative arm",
    "interaction_modalities": "gesture + voice",
    "collaboration_pattern": "turn-taking assembly",
    "environmental_setting": "factory floor",
    "assessment_goals": ["safety-awareness", "adaptive pacing"],
    "expected_empathy_forms": ["mirroring hesitation", "proactive assistance"],
    "measurement_requirements": ["short Likert"],
}

# Variant configurations
VARIANTS = {
    "single_no_content": (1, False),
    "single_with_content": (1, True),
    "multi_no_content": (3, False),
    "multi_with_content": (3, True),
}


def write_interview_stub(run_id: str, scenario: dict, dm: DataManager):
    run_dir = dm.get_run_path(run_id)
    tgt = run_dir / "interview_agent_group"
    tgt.mkdir(parents=True, exist_ok=True)
    (tgt / "summary.json").write_text(
        json.dumps(scenario, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    lit_dir = run_dir / "literature_search_agent_group"
    lit_dir.mkdir(parents=True, exist_ok=True)
    (lit_dir / "summary.json").write_text("{}", encoding="utf-8")


def run_variant(variant_name: str, scenario: dict, api_key: str, dm: DataManager, prompts: PromptManager):
    """Run a single variant."""
    if variant_name not in VARIANTS:
        print_error(f"Unknown variant: {variant_name}")
        print_info(f"Available variants: {', '.join(VARIANTS.keys())}")
        return None
    
    num_generators, enable_content = VARIANTS[variant_name]
    
    print_header(f"RUNNING VARIANT: {variant_name.upper()}", "-")
    print_info(f"Scenario: {scenario.get('name', 'unknown')}")
    print_info(f"Configuration: {num_generators} generator(s), content_assessment={enable_content}")
    
    # Step 1: Setup
    print_step(1, 4, "Setting up run and data")
    run_id = dm.new_run()
    print_success(f"Run ID created: {run_id}")
    write_interview_stub(run_id, scenario, dm)
    print_success("Interview and literature stubs prepared")
    print()
    
    # Step 2: Initialize and generate
    print_step(2, 4, "Initializing generation agent")
    gen = EmpathyScaleGenerationAgentGroup(
        api_key=api_key,
        prompts_dir=prompts.prompts_dir,
        num_item_generators=num_generators,
        enable_content_assessment=enable_content,
    )
    print_success("Agent initialized")
    print()
    
    print_step(3, 4, "Generating empathy scale")
    print_info("  [3.1] Construct definition...")
    print_info(f"  [3.2] Item generation ({num_generators} generator(s))...")
    if enable_content:
        print_info("  [3.3] Content assessment and refinement...")
    try:
        gen.generate_scale(run_id)
        print_success("Scale generation completed")
    except Exception as e:
        print_error(f"Scale generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    print()
    
    # Step 3: Parse items
    print_step(4, 4, "Parsing and evaluating items")
    draft = dm.get_run_path(run_id) / "empathy_scale_generation_agent_group" / "scale_draft.md"
    if not draft.exists():
        print_error("Scale draft not found")
        return None
    
    items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(
        draft.read_text(encoding="utf-8", errors="replace")
    )
    if not items:
        print_warning("No items parsed from scale draft")
        print_info("Checking draft content...")
        draft_content = draft.read_text(encoding="utf-8", errors="replace")
        print_info(f"Draft length: {len(draft_content)} characters")
        print_info(f"First 500 chars: {draft_content[:500]}")
        return None
    
    print_success(f"Parsed {len(items)} items")
    print()
    
    # Step 4: Evaluation (simplified for debugging - use run_ablation_minimal.py for full Phase 1/2)
    print_info("  [4.1] Running LLM-based evaluation (simplified for debugging)...")
    print_info("  [NOTE] For full Phase 1/2 evaluation, use run_ablation_minimal.py instead")
    scenario_id = scenario.get('name', 'collab_robot_assembly')
    print_info(f"  [4.2] Using scenario_id: {scenario_id} (will reuse existing personas if available)")
    print_info(f"  [4.3] Simulating 10 participants (reduced for quick debugging)...")
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompts.prompts_dir)
    try:
        eval_agent.evaluate_items(
            run_id, items, scenario, 
            n_participants=10,
            scenario_id=scenario_id,
            phase="selection"  # Use selection phase for consistency
        )
        print_success("Evaluation completed")
    except Exception as e:
        print_error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print_header(f"VARIANT '{variant_name}' COMPLETED", "-")
    print_success(f"Variant '{variant_name}' completed successfully")
    print_info(f"Run ID: {run_id}")
    print_info(f"Items generated: {len(items)}")
    print_info(f"Configuration: {num_generators} generator(s), content_assessment={enable_content}")
    print()
    
    return {
        "variant_name": variant_name,
        "run_id": run_id,
        "scenario": scenario.get('name', 'unknown'),
        "num_generators": num_generators,
        "enable_content": enable_content,
        "n_items": len(items) if items else 0
    }


def main():
    if len(sys.argv) < 2:
        print_error("Please specify a variant name")
        print_info(f"Available variants: {', '.join(VARIANTS.keys())}")
        print_info("Usage: python run_single_variant.py <variant_name>")
        sys.exit(1)
    
    variant_name = sys.argv[1]
    
    print_header(f"SINGLE VARIANT RUN: {variant_name.upper()}", "=")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    config = json.loads(Path("config.json").read_text(encoding="utf-8"))
    api_key = config["openai_api_key"]
    dm = DataManager()
    prompts = PromptManager()
    
    result = run_variant(variant_name, BASE_SCENARIO, api_key, dm, prompts)
    
    if result:
        print_header("RUN COMPLETED", "=")
        print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_success(f"Variant '{variant_name}' completed")
        print_info(f"Run ID: {result['run_id']}")
        print_info(f"Items: {result['n_items']}")
    else:
        print_error("Run failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

