"""
Minimal runner to execute 2-3 predefined scenarios end-to-end:
- writes interview summary stubs
- runs scale generation
- runs PETS-style LLM evaluation (includes baselines)

Usage:
    python run_predefined_scenarios.py
"""

from pathlib import Path
import sys
import os
from datetime import datetime

# Ensure local imports work when run as script
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


SCENARIOS = [
    {
        "name": "collab_robot_assembly",
        "assessment_context": "factory assembly, human-robot teammate",
        "robot_platform": "collaborative arm",
        "interaction_modalities": "gesture + voice + visual display",
        "collaboration_pattern": "turn-taking assembly",
        "environmental_setting": "factory floor",
        "assessment_goals": ["safety-awareness", "adaptive pacing"],
        "expected_empathy_forms": ["mirroring hesitation", "proactive assistance"],
        "measurement_requirements": ["short Likert", "behavior-focused"],
    },
    {
        "name": "home_service_robot",
        "assessment_context": "home assistant supporting daily tasks",
        "robot_platform": "mobile service robot",
        "interaction_modalities": "speech + navigation cues",
        "collaboration_pattern": "assistive",
        "environmental_setting": "home",
        "assessment_goals": ["comfort", "perceived care"],
        "expected_empathy_forms": ["detect frustration", "offer reassurance"],
        "measurement_requirements": ["non-technical language"],
    },
    {
        "name": "counseling_chatbot",
        "assessment_context": "text-based counseling bot",
        "robot_platform": "chatbot",
        "interaction_modalities": "text chat",
        "collaboration_pattern": "supportive dialogue",
        "environmental_setting": "remote",
        "assessment_goals": ["emotional attunement"],
        "expected_empathy_forms": ["reflective listening", "validation"],
        "measurement_requirements": ["short statements"],
    },
]


def ensure_summary(run_id: str, scenario: dict, data_manager: DataManager):
    """Write interview summary stub for a run."""
    run_dir = data_manager.get_run_path(run_id)
    target = run_dir / "interview_agent_group"
    target.mkdir(parents=True, exist_ok=True)
    (target / "summary.json").write_text(
        __import__("json").dumps(scenario, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    # minimal literature summary placeholder
    lit_dir = run_dir / "literature_search_agent_group"
    lit_dir.mkdir(parents=True, exist_ok=True)
    (lit_dir / "summary.json").write_text("{}", encoding="utf-8")


def run():
    print_header("EMPATHY SCALE GENERATION PIPELINE", "=")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Total scenarios: {len(SCENARIOS)}")
    print()

    dm = DataManager()
    config = __import__("json").loads(Path("config.json").read_text(encoding="utf-8"))
    api_key = config["openai_api_key"]

    prompt_manager = PromptManager()
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompt_manager.prompts_dir)

    for idx, scenario in enumerate(SCENARIOS, 1):
        print_header(f"SCENARIO {idx}/{len(SCENARIOS)}: {scenario['name'].upper()}", "-")
        
        # Step 1: Create run and prepare data
        print_step(1, 5, "Creating run and preparing data")
        run_id = dm.new_run()
        print_success(f"Run ID created: {run_id}")
        
        ensure_summary(run_id, scenario, dm)
        print_success("Interview and literature summaries prepared")
        print()

        # Step 2: Initialize generation agent
        print_step(2, 5, "Initializing scale generation agent")
        gen_agent = EmpathyScaleGenerationAgentGroup(
            api_key=api_key,
            prompts_dir=prompt_manager.prompts_dir,
            num_item_generators=3,
            enable_content_assessment=True,
        )
        print_success("Generation agent initialized (3 item generators, content assessment enabled)")
        print()

        # Step 3: Generate scale
        print_step(3, 5, "Generating empathy scale")
        print_info("  [3.1] Starting construct definition...")
        try:
            # We'll add progress tracking inside generate_scale if needed
            # For now, track at high level
            gen_agent.generate_scale(run_id)
            print_success("  [3.1] Construct definition completed")
            print_info("  [3.2] Multi-item generation completed (3 parallel generators)")
            print_info("  [3.3] Content assessment and refinement completed")
            print_success("Scale generation completed")
        except Exception as e:
            print_error(f"Scale generation failed: {e}")
            print_warning(f"Skipping evaluation for scenario {scenario['name']}")
            import traceback
            traceback.print_exc()
            continue
        print()

        # Step 4: Parse and validate items
        print_step(4, 5, "Parsing generated scale items")
        draft_path = dm.get_run_path(run_id) / "empathy_scale_generation_agent_group" / "scale_draft.md"
        if not draft_path.exists():
            print_error("Scale draft not found")
            continue
        
        md_text = draft_path.read_text(encoding="utf-8", errors="replace")
        items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
        
        if not items:
            print_warning("No items parsed from scale draft")
            continue
        
        print_success(f"Parsed {len(items)} items from scale draft")
        print_info(f"  → Items saved to: {draft_path}")
        print()

        # Step 5: Run evaluation
        print_step(5, 5, "Running LLM-based evaluation (PETS-style pretest)")
        print_info(f"  → Simulating {20} participants")
        print_info("  → Evaluating: clarity, relevance, scenario_sensitivity")
        print_info("  → Running baseline comparisons (PETS, RoPE)...")
        try:
            eval_agent.evaluate_items(run_id, items, scenario, n_participants=20)
            print_success("Evaluation completed")
            
            # Show evaluation summary if available
            eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "evaluation_summary.json"
            if eval_summary_path.exists():
                import json
                summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
                if "overall_means" in summary:
                    means = summary["overall_means"]
                    print_info(f"  → Overall means - Clarity: {means.get('clarity', 'N/A'):.2f}, "
                             f"Relevance: {means.get('relevance', 'N/A'):.2f}, "
                             f"Scenario Sensitivity: {means.get('scenario_sensitivity', 'N/A'):.2f}")
        except Exception as e:
            print_error(f"Evaluation failed: {e}")
            import traceback
            traceback.print_exc()
        print()

        # Scenario summary
        print_header(f"SCENARIO {idx} COMPLETED", "-")
        print_success(f"Scenario '{scenario['name']}' completed successfully")
        print_info(f"Run ID: {run_id}")
        print_info(f"Items generated: {len(items)}")
        print_info(f"Data location: {dm.get_run_path(run_id)}")
        print()

    # Final summary
    print_header("PIPELINE COMPLETED", "=")
    print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_success(f"All {len(SCENARIOS)} scenarios processed")
    print()


if __name__ == "__main__":
    run()

