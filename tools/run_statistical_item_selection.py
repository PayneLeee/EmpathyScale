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

# Update paths for tools/ subdirectory
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))

from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from agents.evaluation_agent_group import EvaluationAgentGroup
from agents.persona_generation_agent import PersonaGenerationAgent
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
        if not config_path.is_absolute():
            # If relative path, resolve from project root (tools/ -> project root)
            config_path = Path(__file__).parent.parent / "config.json"
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
    
    # Step 2: Phase 1 - Evaluate all items (if not already done) - Dual Groups Pattern
    print_step(2, 5, "Phase 1: Evaluating all items (Selection Phase - Dual Groups)")
    print_info(f"  [2.1] Setup:")
    print_info(f"    → Items to evaluate: {len(items)}")
    print_info(f"    → Dual persona groups: empathic + non-empathic (following PETS methodology)")
    print_info(f"    → Participants per group: 100, Total: 200 (for EFA)")
    print_info(f"    → Base scenario ID: {scenario_id}")
    print()
    
    # Check for merged evaluation summary in combined directory first
    eval_summary_path = run_path / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
    
    if not eval_summary_path.exists():
        # Fallback to old location
        eval_summary_path = run_path / "evaluation_agent_group" / "evaluation_summary.json"
        if not eval_summary_path.exists():
            print_info("  Initial evaluation not found, running Phase 1 evaluation with dual groups...")
            
            eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompts.prompts_dir)
            persona_agent = PersonaGenerationAgent(api_key=api_key, prompts_dir=prompts.prompts_dir)
            
            # Step 2.1: Load or generate personas for Phase 1 (selection)
            selection_personas = persona_agent.load_personas(scenario_id, phase="selection")
            n_per_group = 100  # 100*2 = 200 total personas (100 empathic + 100 non-empathic)
            
            if selection_personas is None or len(selection_personas) < n_per_group * 2:
                # Need to generate new personas
                print_info(f"  [2.1] Generating {n_per_group * 2} personas for Phase 1...")
                base_personas = persona_agent.generate_personas(scenario, n_personas=n_per_group)
                
                # Step 2.2: Create two groups with different interaction experiences
                print_info(f"  [2.2] Creating dual persona groups (empathic + non_empathic)...")
                personas_empathic = persona_agent.add_interaction_experiences(
                    base_personas.copy(), scenario, interaction_type="empathic"
                )
                personas_non_empathic = persona_agent.add_interaction_experiences(
                    base_personas.copy(), scenario, interaction_type="non_empathic"
                )
                
                # Merge both groups into one list
                selection_personas = personas_empathic + personas_non_empathic
                print_info(f"    → Total personas: {len(selection_personas)} (empathic: {len(personas_empathic)}, non_empathic: {len(personas_non_empathic)})")
                
                # Save merged personas
                persona_agent.save_personas(scenario_id, selection_personas, phase="selection")
                print_info(f"    → Saved to {scenario_id}/selection.json")
            else:
                # Load existing personas and split them for evaluation
                print_info(f"  [2.1] Loaded {len(selection_personas)} personas from {scenario_id}/selection.json")
                personas_empathic = [p for p in selection_personas if p.get("empathy_condition") == "empathic"]
                personas_non_empathic = [p for p in selection_personas if p.get("empathy_condition") == "non_empathic"]
                print_info(f"    → Empathic: {len(personas_empathic)}, Non-empathic: {len(personas_non_empathic)}")
                # Use first n_per_group from each
                personas_empathic = personas_empathic[:n_per_group]
                personas_non_empathic = personas_non_empathic[:n_per_group]
            print()
            
            # Step 2.3: Evaluate with empathic personas
            print_info(f"  [2.3] Evaluating with empathic personas...")
            result_empathic = eval_agent.evaluate_items(
                run_id, items, scenario,
                n_participants=n_per_group,
                scenario_id=scenario_id,
                phase="selection",
                personas=personas_empathic,
                out_dir=run_path / "evaluation_agent_group" / "selection" / "empathic"
            )
            print_success(f"    → Empathic group evaluation completed")
            
            # Step 2.4: Evaluate with non-empathic personas
            print_info(f"  [2.4] Evaluating with non-empathic personas...")
            result_non_empathic = eval_agent.evaluate_items(
                run_id, items, scenario,
                n_participants=n_per_group,
                scenario_id=scenario_id,
                phase="selection",
                personas=personas_non_empathic,
                out_dir=run_path / "evaluation_agent_group" / "selection" / "non_empathic"
            )
            print_success(f"    → Non-empathic group evaluation completed")
            print()
            
            # Step 2.5: Merge data for EFA/CFA
            print_info(f"  [2.5] Merging evaluation data for EFA+CFA...")
            combined_dir = run_path / "evaluation_agent_group" / "selection" / "combined"
            combined_dir.mkdir(parents=True, exist_ok=True)
            
            # Load participant data from both groups
            empathic_participants_path = Path(result_empathic['summary_path']).parent / "participant_level_evaluations.json"
            non_empathic_participants_path = Path(result_non_empathic['summary_path']).parent / "participant_level_evaluations.json"
            
            empathic_participants = json.loads(empathic_participants_path.read_text(encoding="utf-8"))
            non_empathic_participants = json.loads(non_empathic_participants_path.read_text(encoding="utf-8"))
            
            # Merge participant data
            combined_participants = empathic_participants + non_empathic_participants
            
            # Save merged participant data
            combined_participants_path = combined_dir / "participant_level_evaluations.json"
            with open(combined_participants_path, 'w', encoding='utf-8') as f:
                json.dump(combined_participants, f, indent=2, ensure_ascii=False)
            
            # Generate merged evaluation summary
            combined_summary = eval_agent._summarize(combined_participants, items)
            combined_summary["evaluation_groups"] = {
                "empathic": {"n_participants": len(empathic_participants)},
                "non_empathic": {"n_participants": len(non_empathic_participants)}
            }
            
            combined_summary_path = combined_dir / "evaluation_summary.json"
            with open(combined_summary_path, 'w', encoding='utf-8') as f:
                json.dump(combined_summary, f, indent=2, ensure_ascii=False)
            
            print_success(f"    → Merged data: {len(combined_participants)} participants, {len(items)} items")
            print_success("Phase 1 evaluation completed (dual groups merged)")
            
            # Update eval_summary_path to point to merged summary
            eval_summary_path = combined_summary_path
        else:
            print_info("  Phase 1 evaluation already exists (old format), using it...")
            eval_summary_path = run_path / "evaluation_agent_group" / "evaluation_summary.json"
    else:
        print_info("  Phase 1 merged evaluation already exists, using it...")
    
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
    
    # Step 4: Phase 2 - Validate filtered items with independent personas (Dual Groups Pattern)
    print_step(4, 5, "Phase 2: Validating filtered items (Validation Phase - Dual Groups)")
    print_info(f"  [4.1] Setup:")
    print_info(f"    → Filtered items: {len(filtered_items)}")
    print_info(f"    → Dual persona groups: empathic + non-empathic (100*2 = 200 total)")
    print_info(f"    → Scenario ID: {scenario_id} (reusable)")
    print_info(f"  [4.2] Participant Simulation:")
    print_info(f"    → Each persona will rate {len(filtered_items)} filtered items")
    print_info(f"    → Rating scale: 0-100 (strongly disagree to strongly agree)")
    print()
    
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
        scenario=scenario,  # Pass scenario for factor interpretation context
        output_path=filtered_draft_path
    )
    print_success(f"Created filtered scale draft: {filtered_draft_path}")
    
    # Evaluate filtered items with dual groups pattern
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompts.prompts_dir)
    persona_agent = PersonaGenerationAgent(api_key=api_key, prompts_dir=prompts.prompts_dir)
    
    try:
        # Load or generate personas for Phase 2 (validation)
        validation_personas = persona_agent.load_personas(scenario_id, phase="validation")
        n_per_group = 100  # 100*2 = 200 total personas
        
        if validation_personas is None or len(validation_personas) < n_per_group * 2:
            # Need to generate new personas
            print_info(f"  [4.1] Generating {n_per_group * 2} personas for Phase 2...")
            base_personas = persona_agent.generate_personas(scenario, n_personas=n_per_group)
            
            # Create dual groups
            print_info(f"  [4.2] Creating dual persona groups (empathic + non_empathic)...")
            personas_empathic = persona_agent.add_interaction_experiences(
                base_personas.copy(), scenario, interaction_type="empathic"
            )
            personas_non_empathic = persona_agent.add_interaction_experiences(
                base_personas.copy(), scenario, interaction_type="non_empathic"
            )
            
            # Merge and save
            validation_personas = personas_empathic + personas_non_empathic
            persona_agent.save_personas(scenario_id, validation_personas, phase="validation")
            print_info(f"    → Total personas: {len(validation_personas)} (empathic: {len(personas_empathic)}, non_empathic: {len(personas_non_empathic)})")
            print_info(f"    → Saved to {scenario_id}/validation.json")
        else:
            # Load existing personas
            print_info(f"  [4.1] Loaded {len(validation_personas)} personas from {scenario_id}/validation.json")
            personas_empathic = [p for p in validation_personas if p.get("empathy_condition") == "empathic"]
            personas_non_empathic = [p for p in validation_personas if p.get("empathy_condition") == "non_empathic"]
            print_info(f"    → Empathic: {len(personas_empathic)}, Non-empathic: {len(personas_non_empathic)}")
            # Use first n_per_group from each if we have more
            if len(personas_empathic) > n_per_group:
                personas_empathic = personas_empathic[:n_per_group]
            if len(personas_non_empathic) > n_per_group:
                personas_non_empathic = personas_non_empathic[:n_per_group]
            validation_personas = personas_empathic + personas_non_empathic
        print()
        
        # Evaluate with all validation personas
        eval_result_validation = eval_agent.evaluate_items(
            filtered_run_id, filtered_items, scenario,
            n_participants=len(validation_personas),
            scenario_id=scenario_id,  # Use base scenario name for reusability
            phase="validation",
            personas=validation_personas,
            out_dir=filtered_run_path / "evaluation_agent_group" / "validation"
        )
        print_success("Phase 2 validation completed")
    except Exception as e:
        print_error(f"Phase 2 validation failed: {e}")
        import traceback
        traceback.print_exc()
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

