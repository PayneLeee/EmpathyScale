"""
Statistical Item Selection Workflow

Implements two-phase evaluation process with independent persona sets:
1. Phase 1 (Selection): Evaluate all items using {scenario_id}_selection personas
2. Statistical Selection: Filter items based on evaluation statistics
3. Phase 2 (Validation): Validate filtered items using {scenario_id}_validation personas

Reference: PETS paper methodology (Schmidmaier et al., 2024)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from agents.evaluation_agent_group import EvaluationAgentGroup
from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager
from agents.item_selection_agent import ItemSelectionAgent


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


def apply_statistical_selection(
    run_id: str,
    selection_strategy: str = "rating_threshold",
    strategy_params: Dict[str, Any] = None,
    dm: DataManager = None,
    api_key: str = None,
    prompts: PromptManager = None
) -> Dict[str, Any]:
    """
    Apply statistical selection with two-phase evaluation.
    
    Phase 1: Evaluate all items using {scenario_id}_selection personas
    Phase 2: Validate filtered items using {scenario_id}_validation personas
    
    Args:
        run_id: Original run ID
        selection_strategy: Selection strategy ("rating_threshold", "percentile", "dimension_balanced")
        strategy_params: Strategy-specific parameters
        dm: DataManager instance
        api_key: OpenAI API key
        prompts: PromptManager instance
    
    Returns:
        Dictionary with original and filtered results
    """
    if strategy_params is None:
        strategy_params = {}
    
    if dm is None:
        dm = DataManager()
    
    if prompts is None:
        prompts = PromptManager()
    
    if api_key is None:
        config_path = Path("config.json")
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            api_key = config.get("openai_api_key")
        else:
            raise ValueError("API key not provided and config.json not found")
    
    print_header("STATISTICAL ITEM SELECTION WORKFLOW", "=")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Original run ID: {run_id}")
    print_info(f"Selection strategy: {selection_strategy}")
    print()
    
    # Step 1: Load original run data
    print_step(1, 5, "Loading original run data")
    run_path = dm.get_run_path(run_id)
    
    if not run_path.exists():
        print_error(f"Run directory not found: {run_path}")
        return None
    
    # Load scenario context
    interview_summary_path = run_path / "interview_agent_group" / "summary.json"
    if not interview_summary_path.exists():
        print_error("Interview summary not found")
        return None
    
    scenario = json.loads(interview_summary_path.read_text(encoding="utf-8"))
    scenario_id = scenario.get('name')
    if not scenario_id:
        print_error("Scenario name not found in interview summary")
        return None
    
    print_success(f"Loaded scenario: {scenario_id}")
    
    # Load scale draft
    scale_draft_path = run_path / "empathy_scale_generation_agent_group" / "scale_draft.md"
    if not scale_draft_path.exists():
        print_error("Scale draft not found")
        return None
    
    items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(
        scale_draft_path.read_text(encoding="utf-8", errors="replace")
    )
    if not items:
        print_error("No items parsed from scale draft")
        return None
    
    print_success(f"Loaded {len(items)} items")
    print()
    
    # Step 2: Phase 1 - Evaluate all items (if not already done)
    print_step(2, 5, "Phase 1: Evaluating all items (Selection Phase)")
    eval_summary_path = run_path / "evaluation_agent_group" / "evaluation_summary.json"
    
    if not eval_summary_path.exists():
        print_info("  Initial evaluation not found, running Phase 1 evaluation...")
        print_info(f"  Using persona set: {scenario_id}_selection")
        
        eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompts.prompts_dir)
        eval_agent.evaluate_items(
            run_id, items, scenario,
            n_participants=200,  # Phase 1: Standard selection personas (100*2=200 total)
            scenario_id=f"{scenario_id}_selection"  # Use selection personas
        )
        print_success("Phase 1 evaluation completed")
    else:
        print_info("  Phase 1 evaluation already exists, skipping...")
    
    # Load evaluation summary
    eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
    print_success(f"Loaded evaluation summary: {eval_summary.get('n_items')} items, {eval_summary.get('n_participants')} participants")
    print()
    
    # Step 3: Apply statistical selection
    print_step(3, 5, "Applying statistical selection")
    print_info(f"  Strategy: {selection_strategy}")
    
    # Use ItemSelectionAgent to handle selection logic
    selection_agent = ItemSelectionAgent(api_key=api_key)
    
    # Convert legacy strategy to selection_config
    selection_config = {}
    if selection_strategy == "rating_threshold":
        selection_config = {
            "min_mean_rating": strategy_params.get("min_mean_rating", 60.0),
            "max_std": strategy_params.get("max_std", 30.0)
        }
        print_info(f"  Parameters: min_rating={selection_config['min_mean_rating']}, max_std={selection_config['max_std']}")
    elif selection_strategy == "percentile":
        percentile = strategy_params.get("top_percentile", 0.75)
        selection_config = {
            "percentile_min": percentile,
            "percentile_max": percentile,
            "min_mean_rating": strategy_params.get("min_mean_rating", 60.0),
            "max_std": strategy_params.get("max_std", 30.0)
        }
        print_info(f"  Parameters: top_percentile={percentile}")
    elif selection_strategy == "dimension_balanced":
        selection_config = {
            "min_items_per_dimension": strategy_params.get("min_items_per_dimension", 2),
            "max_items_per_dimension": strategy_params.get("max_items_per_dimension", 6),
            "min_mean_rating": strategy_params.get("min_mean_rating", 60.0),
            "max_std": strategy_params.get("max_std", 30.0)
        }
        print_info(f"  Parameters: min_per_dim={selection_config['min_items_per_dimension']}, max_per_dim={selection_config['max_items_per_dimension']}")
    else:
        print_error(f"Unknown selection strategy: {selection_strategy}")
        return None
    
    # Perform selection
    selection_result = selection_agent.select_items(
        items=items,
        evaluation_summary=eval_summary,
        target_min=10,
        target_max=20,
        selection_config=selection_config
    )
    
    selected_ids = selection_result["selected_item_ids"]
    filtered_items = selection_result["filtered_items"]
    selection_stats = selection_result["selection_statistics"]
    
    if not selected_ids:
        print_warning("No items selected by the strategy")
        return None
    
    print_success(f"Selected {len(selected_ids)}/{len(items)} items ({selection_stats['selection_ratio']*100:.1f}%)")
    print_info(f"  Original mean rating: {selection_stats.get('original_mean_rating', 'N/A')}")
    print_info(f"  Selected mean rating: {selection_stats.get('selected_mean_rating', 'N/A')}")
    print_info(f"  Dimension distribution: {selection_stats.get('dimension_distribution', {})}")
    print()
    
    # Step 4: Phase 2 - Validate filtered items with independent personas
    print_step(4, 5, "Phase 2: Validating filtered items (Validation Phase)")
    print_info(f"  Using independent persona set: {scenario_id}_validation")
    
    filtered_run_id = dm.new_run()
    filtered_run_path = dm.get_run_path(filtered_run_id)
    
    # Copy necessary files to new run directory
    (filtered_run_path / "interview_agent_group").mkdir(parents=True, exist_ok=True)
    (filtered_run_path / "empathy_scale_generation_agent_group").mkdir(parents=True, exist_ok=True)
    
    # Copy interview summary
    import shutil
    shutil.copy(interview_summary_path, filtered_run_path / "interview_agent_group" / "summary.json")
    
    # Generate filtered scale draft markdown using agent method
    filtered_draft_path = filtered_run_path / "empathy_scale_generation_agent_group" / "scale_draft.md"
    
    # Get EFA/CFA results from selection_result if available
    efa_cfa_results = selection_result.get("efa_cfa_results", {}) if selection_result else None
    
    # Use agent to generate filtered scale draft
    selection_agent.generate_filtered_scale_draft(
        filtered_items=filtered_items,
        selected_item_ids=selected_ids,
        efa_cfa_results=efa_cfa_results,
        scenario=None,  # Scenario context not available in this context
        output_path=filtered_draft_path
    )
    print_success(f"Created filtered scale draft: {filtered_draft_path}")
    
    # Evaluate filtered items with independent personas
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompts.prompts_dir)
    eval_agent.evaluate_items(
        filtered_run_id, filtered_items, scenario,
        n_participants=10,
        scenario_id=f"{scenario_id}_validation"  # Use independent validation personas
    )
    print_success("Phase 2 validation completed")
    print()
    
    # Step 5: Save selection metadata (using agent's save method)
    selection_agent.save_selection_results(run_id, selection_result)
    print_step(5, 5, "Saving selection metadata")
    selection_metadata = {
        "original_run_id": run_id,
        "filtered_run_id": filtered_run_id,
        "scenario_id": scenario_id,
        "selection_strategy": selection_strategy,
        "strategy_params": strategy_params,
        "n_original_items": len(items),
        "n_filtered_items": len(filtered_items),
        "selected_item_ids": selected_ids,
        "selection_statistics": selection_stats,
        "created_at": datetime.now().isoformat()
    }
    
    metadata_path = filtered_run_path / "statistical_selection_metadata.json"
    metadata_path.write_text(
        json.dumps(selection_metadata, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print_success(f"Saved selection metadata: {metadata_path}")
    print()
    
    print_header("STATISTICAL SELECTION COMPLETED", "=")
    print_success(f"Original run ID: {run_id}")
    print_success(f"Filtered run ID: {filtered_run_id}")
    print_info(f"Items: {len(items)} → {len(filtered_items)} ({selection_stats['selection_ratio']*100:.1f}%)")
    print_info(f"Selection strategy: {selection_strategy}")
    print()
    
    return selection_metadata


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Apply statistical item selection with two-phase evaluation"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Original run ID to apply selection to"
    )
    parser.add_argument(
        "--strategy",
        default="rating_threshold",
        choices=["rating_threshold", "percentile", "dimension_balanced"],
        help="Selection strategy"
    )
    parser.add_argument(
        "--min-rating",
        type=float,
        default=60.0,
        help="Minimum mean rating for rating_threshold strategy"
    )
    parser.add_argument(
        "--max-std",
        type=float,
        default=30.0,
        help="Maximum standard deviation for rating_threshold strategy"
    )
    parser.add_argument(
        "--percentile",
        type=float,
        default=0.75,
        help="Top percentile for percentile strategy (0.0-1.0)"
    )
    parser.add_argument(
        "--min-per-dim",
        type=int,
        default=2,
        help="Minimum items per dimension for dimension_balanced strategy"
    )
    parser.add_argument(
        "--max-per-dim",
        type=int,
        default=6,
        help="Maximum items per dimension for dimension_balanced strategy"
    )
    
    args = parser.parse_args()
    
    # Prepare strategy parameters
    strategy_params = {}
    if args.strategy == "rating_threshold":
        strategy_params = {
            "min_mean_rating": args.min_rating,
            "max_std": args.max_std
        }
    elif args.strategy == "percentile":
        strategy_params = {
            "top_percentile": args.percentile
        }
    elif args.strategy == "dimension_balanced":
        strategy_params = {
            "min_items_per_dimension": args.min_per_dim,
            "max_items_per_dimension": args.max_per_dim
        }
    
    # Run selection
    result = apply_statistical_selection(
        run_id=args.run_id,
        selection_strategy=args.strategy,
        strategy_params=strategy_params
    )
    
    if result:
        print_success("Statistical selection completed successfully")
        print_info(f"Filtered run ID: {result['filtered_run_id']}")
    else:
        print_error("Statistical selection failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

