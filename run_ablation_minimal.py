"""
Minimal ablation runner:
- single vs multi item generators
- with vs without content assessment
Outputs markdown + summary JSON per run.
"""

import os
import sys
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
    "assessment_context": "factory assembly, human-robot teammate",
    "robot_platform": "collaborative arm",
    "interaction_modalities": "gesture + voice",
    "collaboration_pattern": "turn-taking assembly",
    "environmental_setting": "factory floor",
    "assessment_goals": ["safety-awareness", "adaptive pacing"],
    "expected_empathy_forms": ["mirroring hesitation", "proactive assistance"],
    "measurement_requirements": ["short Likert"],
}


def write_interview_stub(run_id: str, scenario: dict, dm: DataManager):
    run_dir = dm.get_run_path(run_id)
    tgt = run_dir / "interview_agent_group"
    tgt.mkdir(parents=True, exist_ok=True)
    (tgt / "summary.json").write_text(
        __import__("json").dumps(scenario, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    lit_dir = run_dir / "literature_search_agent_group"
    lit_dir.mkdir(parents=True, exist_ok=True)
    (lit_dir / "summary.json").write_text("{}", encoding="utf-8")


def run_variant(name: str, num_generators: int, enable_content: bool, api_key: str, dm: DataManager, prompts: PromptManager):
    print_header(f"ABLATION VARIANT: {name.upper()}", "-")
    print_info(f"Configuration: {num_generators} generator(s), content_assessment={enable_content}")
    
    # Step 1: Setup
    print_step(1, 4, "Setting up run and data")
    run_id = dm.new_run()
    print_success(f"Run ID created: {run_id}")
    write_interview_stub(run_id, BASE_SCENARIO, dm)
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
    print_success(f"Agent initialized")
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
        return run_id
    print()
    
    # Step 3: Parse items
    print_step(4, 4, "Parsing and evaluating items")
    draft = dm.get_run_path(run_id) / "empathy_scale_generation_agent_group" / "scale_draft.md"
    if not draft.exists():
        print_error("Scale draft not found")
        return run_id
    
    items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(draft.read_text(encoding="utf-8", errors="replace"))
    if not items:
        print_warning("No items parsed from scale draft")
        return run_id
    
    print_success(f"Parsed {len(items)} items")
    print()
    
    # Step 4: Evaluation
    print_info("  [4.1] Running LLM-based evaluation...")
    print_info(f"  [4.2] Simulating 10 participants...")
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompts.prompts_dir)
    try:
        eval_agent.evaluate_items(run_id, items, BASE_SCENARIO, n_participants=10)
        print_success("Evaluation completed")
    except Exception as e:
        print_error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print_header(f"VARIANT '{name}' COMPLETED", "-")
    print_success(f"Variant '{name}' completed successfully")
    print_info(f"Run ID: {run_id}")
    print_info(f"Items generated: {len(items)}")
    print_info(f"Configuration: {num_generators} generator(s), content_assessment={enable_content}")
    print()
    
    return run_id


def main():
    print_header("ABLATION STUDY PIPELINE", "=")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info("Comparing: single vs multi generators, with vs without content assessment")
    print()
    
    config = __import__("json").loads(Path("config.json").read_text(encoding="utf-8"))
    api_key = config["openai_api_key"]
    dm = DataManager()
    prompts = PromptManager()

    variants = [
        ("single_no_content", 1, False),
        ("multi_with_content", 3, True),
    ]
    
    run_ids = []
    for idx, (name, num_gen, enable_content) in enumerate(variants, 1):
        print_info(f"Running variant {idx}/{len(variants)}: {name}")
        run_id = run_variant(name, num_gen, enable_content, api_key, dm, prompts)
        run_ids.append((name, run_id))
    
    # Final summary
    print_header("ABLATION STUDY COMPLETED", "=")
    print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_success(f"All {len(variants)} variants processed")
    print()
    print_info("Summary of runs:")
    for name, run_id in run_ids:
        print_info(f"  - {name}: {run_id}")
    print()


if __name__ == "__main__":
    main()

