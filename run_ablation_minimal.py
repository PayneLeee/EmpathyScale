"""
Ablation Study Runner

Runs ablation study comparing variants based on main experiment baseline (5 generators + content assessment + semantic dedup).

Ablation variants (2x2 design):
- fewer_generators: 1 generator, content assessment=True, selection=EFA+CFA
- no_content: 5 generators, content assessment=False, selection=random (extreme control)
- fewer_generators_no_content: 1 generator, content assessment=False, selection=EFA+CFA

Baseline (main experiment): 5 generators, content assessment=True, semantic dedup=True, selection=EFA+CFA
All ablation variants use semantic deduplication (consistent with baseline).

Each variant follows complete two-phase evaluation:
- Phase 1: Dual groups (empathic + non-empathic, 100*2=200) for selection
- Item selection (EFA+CFA for most variants, random for no_content)
- Phase 2: 100*2=200 personas for validation

Usage:
    python run_ablation_minimal.py
"""

from pathlib import Path
import sys
import os
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Force unbuffered output for real-time progress display
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Ensure local imports work when run as script
sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from agents.evaluation_agent_group import EvaluationAgentGroup
from agents.item_selection_agent import ItemSelectionAgent
from agents.persona_generation_agent import PersonaGenerationAgent
from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}", flush=True)
    print(f"{text:^{width}}", flush=True)
    print(f"{char * width}\n", flush=True)


def print_step(step_num: int, total_steps: int, description: str):
    """Print a step indicator."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{step_num}/{total_steps}] {description}...", flush=True)


def print_success(message: str):
    """Print a success message."""
    print(f"[OK] {message}", flush=True)


def print_info(message: str):
    """Print an info message."""
    print(f"[INFO] {message}", flush=True)


def print_warning(message: str):
    """Print a warning message."""
    print(f"[WARN] {message}", flush=True)


def print_error(message: str):
    """Print an error message."""
    print(f"[ERROR] {message}", flush=True)


# Ablation scenario (collab_robot_assembly as specified in proposal)
# Note: Should match main experiment scenario configuration exactly
# Main experiment uses "gesture + voice + visual display" for interaction_modalities
# But ablation uses "gesture + voice" - this is acceptable as it's still the same scenario
ABLATION_SCENARIO = {
    "name": "collab_robot_assembly",
    "assessment_context": "factory assembly, human-robot teammate",
    "robot_platform": "collaborative arm",
    "interaction_modalities": "gesture + voice",  # Main experiment uses "gesture + voice + visual display"
    "collaboration_pattern": "turn-taking assembly",
    "environmental_setting": "factory floor",
    "assessment_goals": ["safety-awareness", "adaptive pacing"],
    "expected_empathy_forms": ["mirroring hesitation", "proactive assistance"],
    "measurement_requirements": ["short Likert"],
}

# Variant configurations (2x2 design)
# Baseline (main experiment): 5 generators, content assessment=True, semantic dedup=True, selection=EFA+CFA
# All ablation variants use semantic deduplication (same as baseline)
VARIANTS = {
    "fewer_generators": {
        "num_generators": 1,
        "enable_content": True,
        "use_random_selection": False,  # Use EFA+CFA (consistent with baseline)
    },
    "no_content": {
        "num_generators": 5,
        "enable_content": False,
        "use_random_selection": True,  # Use random selection (extreme control to demonstrate content assessment value)
    },
    "fewer_generators_no_content": {
        "num_generators": 1,
        "enable_content": False,
        "use_random_selection": False,  # Use EFA+CFA (consistent with baseline)
    },
}


def ensure_summary(run_id: str, scenario: dict, dm: DataManager):
    """Create interview and literature summary stubs."""
    run_dir = dm.get_run_path(run_id)
    
    # Interview summary
    interview_dir = run_dir / "interview_agent_group"
    interview_dir.mkdir(parents=True, exist_ok=True)
    (interview_dir / "summary.json").write_text(
        json.dumps(scenario, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    # Literature summary (empty for ablation)
    lit_dir = run_dir / "literature_search_agent_group"
    lit_dir.mkdir(parents=True, exist_ok=True)
    (lit_dir / "summary.json").write_text("{}", encoding="utf-8")


def random_select_items(items: List[Dict[str, str]], target_count: int = 15) -> Tuple[List[int], List[Dict[str, str]], Dict[str, Any]]:
    """
    Randomly select a target number of items from the items list.
    
    Args:
        items: List of item dictionaries (with 'dimension' and 'item_text' fields, item_id will be assigned as 1-indexed)
        target_count: Target number of items to select (default: 15)
    
    Returns:
        Tuple of:
        - selected_item_ids: List of selected item IDs (1-indexed, based on original order)
        - filtered_items: List of selected item dictionaries (with item_id added)
        - selection_stats: Dictionary with selection statistics
    """
    n_total = len(items)
    
    if n_total == 0:
        return [], [], {"n_total": 0, "n_selected": 0, "selection_ratio": 0.0, "selection_method": "random"}
    
    # Assign item_id to all items (1-indexed, based on original order)
    items_with_ids = []
    for idx, item in enumerate(items):
        item_copy = item.copy()
        item_copy["item_id"] = idx + 1
        items_with_ids.append(item_copy)
    
    # If we have fewer items than target, select all
    if n_total < target_count:
        selected_indices = list(range(n_total))
        print_warning(f"  Only {n_total} items available (less than target {target_count}), selecting all items")
    else:
        # Randomly sample target_count items
        selected_indices = random.sample(range(n_total), target_count)
    
    # Get selected items (preserve original order for item_id consistency)
    selected_items = [items_with_ids[i] for i in selected_indices]
    selected_ids = [item["item_id"] for item in selected_items]
    
    # Build selection statistics
    selection_stats = {
        "n_total": n_total,
        "n_selected": len(selected_ids),
        "selection_ratio": len(selected_ids) / n_total if n_total > 0 else 0.0,
        "selection_method": "random",
        "target_count": target_count,
    }
    
    return selected_ids, selected_items, selection_stats


def run_variant(
    variant_name: str,
    scenario: dict,
    api_key: str,
    dm: DataManager,
    prompt_manager: PromptManager,
    eval_agent: EvaluationAgentGroup,
    persona_agent: PersonaGenerationAgent,
    selection_agent: ItemSelectionAgent
) -> Dict[str, Any]:
    """Run a single ablation variant with complete two-phase evaluation."""
    if variant_name not in VARIANTS:
        print_error(f"Unknown variant: {variant_name}")
        return None
    
    variant_config = VARIANTS[variant_name]
    num_generators = variant_config["num_generators"]
    enable_content = variant_config["enable_content"]
    use_random_selection = variant_config["use_random_selection"]
    
    # Build variant description
    selection_method_str = "random selection (extreme control)" if use_random_selection else "EFA+CFA"
    if variant_name == "fewer_generators":
        variant_desc = f"Ablation: Fewer generators (1 vs baseline 5), using {selection_method_str}"
    elif variant_name == "no_content":
        variant_desc = f"Ablation: Remove content assessment (no vs baseline yes), using {selection_method_str}"
    elif variant_name == "fewer_generators_no_content":
        variant_desc = f"Ablation: Fewer generators + remove content assessment, using {selection_method_str}"
    else:
        variant_desc = f"Ablation variant: {variant_name}"
    
    print_header(f"VARIANT: {variant_name.upper()}", "-")
    print_info(f"Description: {variant_desc}")
    print_info(f"Configuration: {num_generators} generator(s), content_assessment={enable_content}, selection_method={'random' if use_random_selection else 'EFA+CFA'}")
    print()
    
    # Step 1: Setup
    print_step(1, 7, "Creating run and preparing data")
    run_id = dm.new_run()
    print_success(f"Run ID created: {run_id}")
    ensure_summary(run_id, scenario, dm)
    print_success("Interview and literature summaries prepared")
    print()
    
    # Step 2: Initialize generation agent
    print_step(2, 7, "Initializing scale generation agent")
    print_info(f"  → Model: gpt-4o-mini")
    print_info(f"  → Item generators: {num_generators}")
    print_info(f"  → Content assessment: {'Enabled' if enable_content else 'Disabled'}")
    gen_agent = EmpathyScaleGenerationAgentGroup(
        api_key=api_key,
        prompts_dir=prompt_manager.prompts_dir,
        num_item_generators=num_generators,
        enable_content_assessment=enable_content,
    )
    print_success("Generation agent initialized")
    print()
    
    # Step 3: Generate scale
    print_step(3, 7, "Generating empathy scale")
    print_info("  [3.1] Construct Definition: Defining empathy dimensions...")
    print_info(f"  [3.2] Item Generation: Generating candidate items ({num_generators} generator(s), 25-30 items per dimension)...")
    if enable_content:
        print_info("  [3.3] Content Assessment: Refining and de-duplicating items...")
    print_info("  [3.4] Assembly: Creating scale draft markdown...")
    try:
        gen_agent.generate_scale(run_id)
        print_success("Scale generation completed")
    except Exception as e:
        print_error(f"Scale generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    print()
    
    # Step 4: Parse items
    print_step(4, 7, "Parsing generated scale items")
    draft_path = dm.get_run_path(run_id) / "empathy_scale_generation_agent_group" / "scale_draft.md"
    if not draft_path.exists():
        print_error("Scale draft not found")
        return None
    
    md_text = draft_path.read_text(encoding="utf-8", errors="replace")
    items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
    
    if not items:
        print_error("No items parsed from scale draft")
        return None
    
    print_success(f"Parsed {len(items)} items from scale draft")
    
    # Apply semantic deduplication as a safety measure
    # Note: Semantic deduplication is enabled for all variants to maintain consistency with baseline
    print_info("  [Semantic Dedup] Applying semantic deduplication as safety measure (enabled for all variants, consistent with baseline)...")
    try:
        from utils.pre_evaluation_semantic_deduplication import remove_semantic_duplicates_before_evaluation
        
        filtered_items, dedup_stats = remove_semantic_duplicates_before_evaluation(
            items,
            similarity_threshold=0.80,
            cross_dimension_threshold=0.75,
            use_sentence_transformers=True
        )
        
        if len(filtered_items) < len(items):
            print_success(f"  [Semantic Dedup] Removed {dedup_stats['n_removed']} semantic duplicates ({len(items)} → {len(filtered_items)} items)")
            items = filtered_items
        else:
            print_info(f"  [Semantic Dedup] No semantic duplicates found, all {len(items)} items are unique")
    except ImportError:
        print_warning("  [Semantic Dedup] Semantic deduplication not available, skipping...")
    except Exception as e:
        print_warning(f"  [Semantic Dedup] Semantic deduplication failed: {e}, continuing with original items...")
    
    print()
    
    # Step 5: Phase 1 Evaluation (Dual Groups: empathic + non-empathic)
    # Skip Phase 1 if using random selection (not needed for random selection)
    scenario_id = scenario['name']  # Define scenario_id for both paths (needed for Phase 2)
    if use_random_selection:
        print_step(5, 7, "Skipping Phase 1 evaluation (not needed for random selection)")
        print_info(f"  Random selection does not require evaluation data")
        print_info(f"  Proceeding directly to random selection in Step 6")
        print_info(f"  Phase 2 validation will still be performed to evaluate selected items")
        combined_summary = None  # No Phase 1 summary for random selection
        print()
    else:
        print_step(5, 7, "Phase 1: Item Selection Evaluation (Dual Groups for EFA+CFA)")
        print_info(f"  [5.1] Setup:")
        print_info(f"    → Items to evaluate: {len(items)}")
        print_info(f"    → Dual persona groups: empathic + non-empathic (following PETS methodology)")
        print_info(f"    → Participants per group: 100, Total: 200 (for EFA)")
        print_info(f"    → Base scenario ID: {scenario['name']}")
        print_info(f"  [5.2] Participant Simulation:")
        print_info(f"    → Each persona will rate all {len(items)} items")
        print_info(f"    → Rating scale: 0-100 (strongly disagree to strongly agree)")
        print()
        
        try:
            # Step 5.1: Load or generate personas for Phase 1 (selection)
            scenario_id = scenario['name']
            # Use variant-specific scenario_id to ensure independent personas per variant
            variant_scenario_id = f"{scenario_id}_{variant_name}_selection"
            selection_personas = persona_agent.load_personas(variant_scenario_id, phase="selection")
            n_per_group = 100  # 100*2 = 200 total personas
            
            if selection_personas is None or len(selection_personas) < n_per_group * 2:
                # Need to generate new personas
                print_info(f"  [5.1] Generating {n_per_group * 2} personas for Phase 1...")
                base_personas = persona_agent.generate_personas(scenario, n_personas=n_per_group)
                
                # Step 5.2: Create two groups with different interaction experiences
                print_info(f"  [5.2] Creating dual persona groups (empathic + non_empathic)...")
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
                persona_agent.save_personas(variant_scenario_id, selection_personas, phase="selection")
                print_info(f"    → Saved to {variant_scenario_id}/selection.json")
            else:
                # Load existing personas and split them
                print_info(f"  [5.1] Loaded {len(selection_personas)} personas from {variant_scenario_id}/selection.json")
                personas_empathic = [p for p in selection_personas if p.get("empathy_condition") == "empathic"]
                personas_non_empathic = [p for p in selection_personas if p.get("empathy_condition") == "non_empathic"]
                print_info(f"    → Empathic: {len(personas_empathic)}, Non-empathic: {len(personas_non_empathic)}")
                personas_empathic = personas_empathic[:n_per_group]
                personas_non_empathic = personas_non_empathic[:n_per_group]
            print()
            
            # Step 5.3: Evaluate with empathic personas
            print_info(f"  [5.3] Evaluating with empathic personas...")
            result_empathic = eval_agent.evaluate_items(
                run_id, items, scenario,
                n_participants=n_per_group,
                scenario_id=variant_scenario_id,
                phase="selection",
                personas=personas_empathic,
                out_dir=dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "empathic"
            )
            print_success(f"    → Empathic group evaluation completed")
            
            # Step 5.4: Evaluate with non-empathic personas
            print_info(f"  [5.4] Evaluating with non-empathic personas...")
            result_non_empathic = eval_agent.evaluate_items(
                run_id, items, scenario,
                n_participants=n_per_group,
                scenario_id=variant_scenario_id,
                phase="selection",
                personas=personas_non_empathic,
                out_dir=dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "non_empathic"
            )
            print_success(f"    → Non-empathic group evaluation completed")
            print()
            
            # Step 5.5: Merge data for EFA/CFA
            print_info(f"  [5.5] Merging evaluation data for EFA+CFA...")
            combined_dir = dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "combined"
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
            
            # Show evaluation summary
            print_info("  [Phase 1 Summary Statistics]:")
            if combined_summary.get("overall_mean_rating") is not None:
                print_info(f"    → Overall mean rating: {combined_summary['overall_mean_rating']:.2f} (0-100 scale)")
            print_info(f"    → Items evaluated: {combined_summary['n_items']}")
            print_info(f"    → Total participants: {combined_summary['n_participants']} (empathic: {len(empathic_participants)}, non-empathic: {len(non_empathic_participants)})")
        except Exception as e:
            print_error(f"Phase 1 evaluation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        print()
    
    # Step 6: Item selection (EFA+CFA method or random selection)
    if use_random_selection:
        print_step(6, 7, "Applying random selection (extreme control)")
        print_info(f"  Strategy: Random selection (extreme control to demonstrate content assessment value)")
        print_info(f"  Target count: 15 items (within 10-18 target range)")
        if variant_name == "no_content":
            print_info(f"  Note: Using random selection to clearly demonstrate content assessment's role in improving candidate pool quality")
        
        try:
            # Random selection
            selected_ids, filtered_items, selection_stats = random_select_items(items, target_count=15)
            
            if not selected_ids:
                print_warning("No items selected by random selection")
                print_warning("Skipping Phase 2 validation")
                filtered_items = []
            else:
                print_success(f"Selected {len(selected_ids)}/{len(items)} items ({selection_stats['selection_ratio']*100:.1f}%)")
                
                # Save selection metadata (similar format to EFA+CFA results for consistency)
                selection_dir = dm.get_run_path(run_id) / "statistical_selection"
                selection_dir.mkdir(parents=True, exist_ok=True)
                
                selection_result = {
                    "selected_item_ids": selected_ids,
                    "filtered_items": filtered_items,
                    "selection_statistics": selection_stats,
                    "selection_config": {
                        "selection_method": "random",
                        "target_count": 15,
                    }
                }
                
                # Save selection config
                selection_config_path = selection_dir / "selection_config.json"
                with open(selection_config_path, 'w', encoding='utf-8') as f:
                    json.dump(selection_result, f, indent=2, ensure_ascii=False)
                
                # Save selection statistics
                selection_stats_path = selection_dir / "selection_statistics.json"
                with open(selection_stats_path, 'w', encoding='utf-8') as f:
                    json.dump(selection_stats, f, indent=2, ensure_ascii=False)
                
                # Generate filtered scale draft (simple markdown without factor structure)
                filtered_draft_path = dm.get_run_path(run_id) / "empathy_scale_generation_agent_group" / "filtered_scale_draft.md"
                from agents.item_selection_agent import ItemSelectionAgent
                temp_selection_agent = ItemSelectionAgent(api_key=api_key)
                temp_selection_agent.generate_filtered_scale_draft(
                    filtered_items=filtered_items,
                    selected_item_ids=selected_ids,
                    efa_cfa_results=None,  # No factor structure for random selection
                    scenario=scenario,
                    output_path=filtered_draft_path
                )
                print_success(f"Created filtered scale draft: {filtered_draft_path}")
        except Exception as e:
            print_error(f"Random selection failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    else:
        print_step(6, 7, "Applying statistical selection (EFA+CFA)")
        try:
            # Use merged data from combined directory
            eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
            if not eval_summary_path.exists():
                print_error("Phase 1 merged evaluation summary not found")
                return None
            
            eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
            
            # Configure selection parameters (EFA+CFA method following PETS)
            selection_config = {
                "use_efa": True,
                "use_cfa": True,
                "min_item_total_corr": 0.3,
                "max_skewness": 1.0,
                "max_kurtosis": 3.0,
                "max_inter_corr": 0.8,
                "min_factor_loading": 0.75,
                "n_factors": None,
                "min_items_per_factor": 2,
                "cfa_rmsea_threshold": 0.08,
                "cfa_tli_threshold": 0.95,
                "cfa_cfi_threshold": 0.95,
                "cfa_srmr_threshold": 0.08,
                "adaptive_factor_loading": True,
                "max_adaptive_iterations": 8,
                "try_multiple_n_factors": True,
                "max_n_factors_to_try": None,
                "prefer_balanced_factors": True,
                "enable_factor_balance": True,
                "max_items_per_factor": None
            }
            
            print_info(f"  Strategy: EFA+CFA (Exploratory + Confirmatory Factor Analysis) - PETS methodology")
            print_info(f"  Item count control: Adaptive adjustment to target range 10-18 items")
            
            # Perform selection
            selection_result = selection_agent.select_items(
                items=items,
                evaluation_summary=eval_summary,
                target_min=10,
                target_max=18,
                selection_config=selection_config,
                evaluation_summary_path=eval_summary_path
            )
            
            selected_ids = selection_result["selected_item_ids"]
            filtered_items = selection_result["filtered_items"]
            selection_stats = selection_result["selection_statistics"]
            
            if not selected_ids:
                print_warning("No items selected by EFA+CFA")
                print_warning("Skipping Phase 2 validation")
                filtered_items = []
            else:
                print_success(f"Selected {len(selected_ids)}/{len(items)} items ({selection_stats['selection_ratio']*100:.1f}%)")
                
                # Save selection metadata
                selection_agent.save_selection_results(run_id, selection_result)
                
                # Generate filtered scale draft
                filtered_draft_path = dm.get_run_path(run_id) / "empathy_scale_generation_agent_group" / "filtered_scale_draft.md"
                efa_cfa_results = selection_result.get("efa_cfa_results", {})
                
                selection_agent.generate_filtered_scale_draft(
                    filtered_items=filtered_items,
                    selected_item_ids=selected_ids,
                    efa_cfa_results=efa_cfa_results,
                    scenario=scenario,
                    output_path=filtered_draft_path
                )
                print_success(f"Created filtered scale draft: {filtered_draft_path}")
        except Exception as e:
            print_error(f"Statistical selection failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    print()
    
    # Step 7: Phase 2 Validation
    if not filtered_items:
        print_warning("No filtered items to validate, skipping Phase 2")
        phase2_summary = None
    else:
        print_step(7, 7, "Phase 2: Final Validation")
        print_info(f"  [7.1] Setup:")
        print_info(f"    → Filtered items: {len(filtered_items)}")
        print_info(f"    → Dual persona groups: empathic + non-empathic (100*2 = 200 total)")
        print_info(f"    → Scenario ID: {scenario_id} (base scenario, reusable personas from main experiment)")
        print_info(f"  [7.2] Participant Simulation:")
        print_info(f"    → Each persona will rate {len(filtered_items)} filtered items")
        print_info(f"    → Rating scale: 0-100 (strongly disagree to strongly agree)")
        print()
        
        try:
            # Load or generate personas for Phase 2 (validation)
            # Use base scenario_id (same as main experiment) to reuse validation personas
            # This ensures consistency across ablation variants and reuses personas from run_predefined_scenarios.py
            validation_personas = persona_agent.load_personas(scenario_id, phase="validation")
            n_per_group = 100  # 100*2 = 200 total personas
            
            if validation_personas is None or len(validation_personas) < n_per_group * 2:
                # Need to generate new personas (will be saved for reuse by other variants and baseline comparison)
                print_info(f"  [7.1] Generating {n_per_group * 2} personas for Phase 2...")
                print_info(f"    → Using base scenario_id '{scenario_id}' (reusable across variants)")
                base_personas = persona_agent.generate_personas(scenario, n_personas=n_per_group)
                
                # Create dual groups
                print_info(f"  [7.2] Creating dual persona groups (empathic + non_empathic)...")
                personas_empathic = persona_agent.add_interaction_experiences(
                    base_personas.copy(), scenario, interaction_type="empathic"
                )
                personas_non_empathic = persona_agent.add_interaction_experiences(
                    base_personas.copy(), scenario, interaction_type="non_empathic"
                )
                
                # Merge and save (using base scenario_id for reusability)
                validation_personas = personas_empathic + personas_non_empathic
                persona_agent.save_personas(scenario_id, validation_personas, phase="validation")
                print_info(f"    → Total personas: {len(validation_personas)} (empathic: {len(personas_empathic)}, non_empathic: {len(personas_non_empathic)})")
                print_info(f"    → Saved to {scenario_id}/validation.json (reusable for baseline comparison)")
            else:
                # Load existing personas (from main experiment or previous variant)
                print_info(f"  [7.1] Loaded {len(validation_personas)} personas from {scenario_id}/validation.json")
                print_info(f"    → Reusing validation personas from main experiment")
                personas_empathic = [p for p in validation_personas if p.get("empathy_condition") == "empathic"]
                personas_non_empathic = [p for p in validation_personas if p.get("empathy_condition") == "non_empathic"]
                print_info(f"    → Empathic: {len(personas_empathic)}, Non-empathic: {len(personas_non_empathic)}")
                if len(personas_empathic) > n_per_group:
                    personas_empathic = personas_empathic[:n_per_group]
                if len(personas_non_empathic) > n_per_group:
                    personas_non_empathic = personas_non_empathic[:n_per_group]
                validation_personas = personas_empathic + personas_non_empathic
            print()
            
            # Evaluate with all validation personas (using base scenario_id for consistency)
            eval_result_validation = eval_agent.evaluate_items(
                run_id, filtered_items, scenario,
                n_participants=len(validation_personas),
                scenario_id=scenario_id,  # Use base scenario_id (reusable personas)
                phase="validation",
                personas=validation_personas,
                out_dir=dm.get_run_path(run_id) / "evaluation_agent_group" / "validation"
            )
            print_success("Phase 2 validation completed")
            
            # Show Phase 2 summary and validation metrics
            eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
            participant_data_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "validation" / "participant_level_evaluations.json"
            
            if eval_summary_path.exists():
                summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
                phase2_summary = summary
                print_info("  [Phase 2 Summary Statistics]:")
                if "overall_mean_rating" in summary and summary["overall_mean_rating"] is not None:
                    overall_mean = summary["overall_mean_rating"]
                    print_info(f"    → Overall mean rating: {overall_mean:.2f} (0-100 scale)")
                if "n_items" in summary:
                    print_info(f"    → Items evaluated: {summary['n_items']}")
                
                # Calculate and display validation metrics (PETS-style)
                if participant_data_path.exists():
                    participant_data = json.loads(participant_data_path.read_text(encoding="utf-8"))
                    
                    # Get factor_structure from selection results
                    factor_structure = None
                    selection_config_path = dm.get_run_path(run_id) / "statistical_selection" / "selection_config.json"
                    if selection_config_path.exists():
                        try:
                            selection_config_data = json.loads(selection_config_path.read_text(encoding="utf-8"))
                            efa_cfa_results = selection_config_data.get("efa_cfa_results", {})
                            if efa_cfa_results:
                                factor_structure_raw = efa_cfa_results.get("factor_structure", {})
                                if factor_structure_raw:
                                    factor_structure = {}
                                    for k, v in factor_structure_raw.items():
                                        try:
                                            item_id = int(k) if isinstance(k, str) else k
                                            factor_idx = int(v) if isinstance(v, str) else v
                                            factor_structure[item_id] = factor_idx
                                        except (ValueError, TypeError):
                                            continue
                        except Exception as e:
                            print_warning(f"    → Could not load factor_structure: {e}")
                    
                    # Recalculate summary with factor_structure to get validation_metrics
                    summary_with_metrics = eval_agent._summarize(participant_data, filtered_items, factor_structure=factor_structure)
                    
                    # Update evaluation_summary.json with validation_metrics
                    if "validation_metrics" in summary_with_metrics:
                        summary["validation_metrics"] = summary_with_metrics["validation_metrics"]
                        phase2_summary = summary
                        with open(eval_summary_path, 'w', encoding='utf-8') as f:
                            json.dump(summary, f, indent=2, ensure_ascii=False)
                        
                        # Display validation metrics
                        print_info("  [Phase 2 Validation Metrics (PETS-style)]:")
                        validation_metrics = summary["validation_metrics"]
                        
                        # Discriminant ability
                        if "discriminant_ability" in validation_metrics:
                            da = validation_metrics["discriminant_ability"]
                            print_info(f"    → Discriminant Ability (t-test):")
                            print_info(f"      - Empathic mean: {da.get('empathic_mean', 'N/A')}")
                            print_info(f"      - Non-empathic mean: {da.get('non_empathic_mean', 'N/A')}")
                            print_info(f"      - t-statistic: {da.get('t_statistic', 'N/A')}")
                            print_info(f"      - p-value: {da.get('p_value', 'N/A')}")
                            print_info(f"      - Cohen's d: {da.get('cohens_d', 'N/A')}")
                            if da.get('significant', False):
                                print_success(f"      - Significant: Yes (p < 0.001)")
                            else:
                                print_info(f"      - Significant: No (p >= 0.001)")
                        
                        # Internal consistency
                        if "internal_consistency" in validation_metrics:
                            ic = validation_metrics["internal_consistency"]
                            print_info(f"    → Internal Consistency (Cronbach's α):")
                            print_info(f"      - Alpha: {ic.get('alpha', 'N/A')}")
                            print_info(f"      - 95% CI: [{ic.get('ci_lower', 'N/A')}, {ic.get('ci_upper', 'N/A')}]")
                            alpha_val = ic.get('alpha', 0)
                            if alpha_val >= 0.9:
                                print_success(f"      - Quality: Excellent (α >= 0.9)")
                            elif alpha_val >= 0.8:
                                print_info(f"      - Quality: Good (0.8 <= α < 0.9)")
                            elif alpha_val >= 0.7:
                                print_warning(f"      - Quality: Acceptable (0.7 <= α < 0.8)")
                            else:
                                print_warning(f"      - Quality: Poor (α < 0.7)")
                        
                        # Factor scores
                        if "factor_scores" in validation_metrics:
                            fs = validation_metrics["factor_scores"]
                            print_info(f"    → Factor Scores (PETS Table 8 style):")
                            for factor_name, scores in sorted(fs.items()):
                                print_info(f"      - {factor_name}: M={scores.get('mean', 'N/A')}, SD={scores.get('std', 'N/A')}, n_items={scores.get('n_items', 'N/A')}")
        except Exception as e:
            print_error(f"Phase 2 validation failed: {e}")
            import traceback
            traceback.print_exc()
            phase2_summary = None
        print()
    
    # Return variant result
    return {
        "variant_name": variant_name,
        "run_id": run_id,
        "scenario": scenario['name'],
        "num_generators": num_generators,
        "enable_content": enable_content,
        "use_random_selection": use_random_selection,
        "selection_method": "random" if use_random_selection else "efa_cfa",
        "n_items": len(items),
        "n_selected_items": len(filtered_items) if filtered_items else 0,
        "phase1_summary": combined_summary if 'combined_summary' in locals() else None,
        "phase2_summary": phase2_summary if 'phase2_summary' in locals() else None,
    }


def load_main_experiment_results(scenario_name: str, dm: DataManager) -> Dict[str, Any]:
    """
    Load main experiment results for baseline comparison.
    
    For collab_robot_assembly scenario, the main experiment run_id is known from previous runs.
    This function attempts to find the main experiment results.
    """
    # Known main experiment run_id for collab_robot_assembly (from experiment_selection.json)
    main_experiment_run_ids = {
        "collab_robot_assembly": "2025-12-22_215026",
    }
    
    if scenario_name not in main_experiment_run_ids:
        print_warning(f"Unknown main experiment run_id for scenario: {scenario_name}")
        return None
    
    run_id = main_experiment_run_ids[scenario_name]
    run_path = dm.get_run_path(run_id)
    
    if not run_path.exists():
        print_warning(f"Main experiment run path not found: {run_path}")
        return None
    
    # Load Phase 2 validation summary
    eval_summary_path = run_path / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
    if not eval_summary_path.exists():
        print_warning(f"Main experiment validation summary not found: {eval_summary_path}")
        return None
    
    try:
        eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
        
        # Load selection statistics
        selection_stats_path = run_path / "statistical_selection" / "selection_statistics.json"
        selection_stats = None
        if selection_stats_path.exists():
            selection_stats = json.loads(selection_stats_path.read_text(encoding="utf-8"))
        
        return {
            "run_id": run_id,
            "eval_summary": eval_summary,
            "selection_stats": selection_stats,
            "validation_metrics": eval_summary.get("validation_metrics", {}),
        }
    except Exception as e:
        print_warning(f"Failed to load main experiment results: {e}")
        return None


def generate_ablation_summary(variant_results: List[Dict[str, Any]], scenario: dict, output_dir: Path):
    """Generate ablation study summary report with baseline comparison."""
    summary = {
        "scenario": scenario['name'],
        "generated_at": datetime.now().isoformat(),
        "baseline": {
            "description": "Main experiment baseline: 5 generators, content assessment=True, semantic dedup=True, selection=EFA+CFA",
            "run_id": None,
        },
        "variants": {},
        "comparison": {}
    }
    
    # Load main experiment baseline results
    dm = DataManager()
    baseline_results = load_main_experiment_results(scenario['name'], dm)
    if baseline_results:
        summary["baseline"]["run_id"] = baseline_results["run_id"]
        baseline_metrics = baseline_results.get("validation_metrics", {})
        summary["baseline"]["validation_metrics"] = baseline_metrics
    
    # Collect variant data
    ratings = {}
    item_counts = {}
    
    for result in variant_results:
        if result is None:
            continue
        
        variant_name = result["variant_name"]
        summary["variants"][variant_name] = {
            "run_id": result["run_id"],
            "num_generators": result["num_generators"],
            "enable_content": result["enable_content"],
            "use_random_selection": result.get("use_random_selection", False),
            "selection_method": result.get("selection_method", "efa_cfa"),
            "n_items": result["n_items"],
            "n_selected_items": result["n_selected_items"],
        }
        
        # Add description
        if variant_name == "fewer_generators":
            summary["variants"][variant_name]["description"] = "Ablation: Fewer generators (1 vs baseline 5), using EFA+CFA"
        elif variant_name == "no_content":
            summary["variants"][variant_name]["description"] = "Ablation: Remove content assessment (no vs baseline yes), using random selection (extreme control)"
        elif variant_name == "fewer_generators_no_content":
            summary["variants"][variant_name]["description"] = "Ablation: Fewer generators + remove content assessment, using EFA+CFA"
        
        # Extract Phase 2 metrics
        phase2_summary = result.get("phase2_summary")
        if phase2_summary:
            summary["variants"][variant_name]["evaluation"] = {
                "overall_mean_rating": phase2_summary.get("overall_mean_rating"),
                "n_participants": phase2_summary.get("n_participants"),
                "rating_std": phase2_summary.get("overall_rating_std"),
            }
            
            # Extract validation metrics
            validation_metrics = phase2_summary.get("validation_metrics", {})
            if validation_metrics:
                summary["variants"][variant_name]["validation_metrics"] = validation_metrics
                
                # Compare with baseline
                if baseline_results:
                    baseline_metrics = baseline_results.get("validation_metrics", {})
                    comparison = {}
                    
                    # Compare internal consistency (Cronbach's alpha)
                    if "internal_consistency" in validation_metrics and "internal_consistency" in baseline_metrics:
                        variant_alpha = validation_metrics["internal_consistency"].get("alpha")
                        baseline_alpha = baseline_metrics["internal_consistency"].get("alpha")
                        if variant_alpha is not None and baseline_alpha is not None:
                            comparison["alpha_diff"] = variant_alpha - baseline_alpha
                            comparison["alpha_diff_pct"] = (variant_alpha - baseline_alpha) / baseline_alpha * 100
                    
                    # Compare discriminant ability (Cohen's d)
                    if "discriminant_ability" in validation_metrics and "discriminant_ability" in baseline_metrics:
                        variant_d = validation_metrics["discriminant_ability"].get("cohens_d")
                        baseline_d = baseline_metrics["discriminant_ability"].get("cohens_d")
                        if variant_d is not None and baseline_d is not None:
                            comparison["cohens_d_diff"] = variant_d - baseline_d
                            comparison["cohens_d_diff_pct"] = (variant_d - baseline_d) / baseline_d * 100
                    
                    if comparison:
                        summary["variants"][variant_name]["comparison_with_baseline"] = comparison
            
            # Collect rating for comparison
            if phase2_summary.get("overall_mean_rating") is not None:
                ratings[variant_name] = phase2_summary["overall_mean_rating"]
        
        item_counts[variant_name] = result["n_selected_items"]
    
    # Generate comparison metrics
    if ratings:
        summary["comparison"]["ratings"] = ratings
        best_rating = max(ratings.items(), key=lambda x: x[1] if x[1] is not None else 0)
        summary["comparison"]["best_rating"] = {
            "variant": best_rating[0],
            "rating": best_rating[1]
        }
    
    if item_counts:
        summary["comparison"]["item_counts"] = item_counts
    
    # Save summary
    summary_path = output_dir / "ablation_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print_success(f"Ablation summary saved: {summary_path}")
    
    # Print baseline comparison if available
    if baseline_results:
        print_info("  [Baseline Comparison]:")
        baseline_metrics = baseline_results.get("validation_metrics", {})
        if "internal_consistency" in baseline_metrics:
            alpha = baseline_metrics["internal_consistency"].get("alpha")
            if alpha is not None:
                print_info(f"    → Baseline α: {alpha:.3f}")
        if "discriminant_ability" in baseline_metrics:
            d = baseline_metrics["discriminant_ability"].get("cohens_d")
            if d is not None:
                print_info(f"    → Baseline Cohen's d: {d:.3f}")
    
    return summary


def main():
    """Main function to run ablation study."""
    print_header("ABLATION STUDY", "=")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Scenario: {ABLATION_SCENARIO['name']}")
    print_info(f"Baseline: 5 generators, content assessment=True, semantic dedup=True, selection=EFA+CFA")
    print_info(f"Ablation variants: {len(VARIANTS)} (2x2 design)")
    print()
    
    # Setup
    dm = DataManager()
    config = json.loads(Path("config.json").read_text(encoding="utf-8"))
    api_key = config["openai_api_key"]
    prompt_manager = PromptManager()
    
    # Initialize agents
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompt_manager.prompts_dir)
    persona_agent = PersonaGenerationAgent(api_key=api_key, prompts_dir=prompt_manager.prompts_dir)
    selection_agent = ItemSelectionAgent(api_key=api_key)
    
    # Run all variants
    variant_results = []
    for variant_name in VARIANTS.keys():
        result = run_variant(
            variant_name=variant_name,
            scenario=ABLATION_SCENARIO,
            api_key=api_key,
            dm=dm,
            prompt_manager=prompt_manager,
            eval_agent=eval_agent,
            persona_agent=persona_agent,
            selection_agent=selection_agent
        )
        variant_results.append(result)
        
        if result:
            print_header(f"VARIANT '{variant_name}' COMPLETED", "-")
            print_success(f"Variant '{variant_name}' completed successfully")
            print_info(f"Run ID: {result['run_id']}")
            print_info(f"Configuration: {result['num_generators']} generator(s), content_assessment={result['enable_content']}, selection={result.get('selection_method', 'efa_cfa')}")
            print_info(f"Items generated: {result['n_items']}")
            print_info(f"Items after selection: {result['n_selected_items']}")
            if result.get("phase2_summary") and result["phase2_summary"].get("overall_mean_rating") is not None:
                print_info(f"Phase 2 mean rating: {result['phase2_summary']['overall_mean_rating']:.2f}")
                # Show validation metrics if available
                validation_metrics = result["phase2_summary"].get("validation_metrics", {})
                if "internal_consistency" in validation_metrics:
                    alpha = validation_metrics["internal_consistency"].get("alpha")
                    if alpha is not None:
                        print_info(f"  Internal consistency (α): {alpha:.3f}")
                if "discriminant_ability" in validation_metrics:
                    d = validation_metrics["discriminant_ability"].get("cohens_d")
                    if d is not None:
                        print_info(f"  Discriminant ability (Cohen's d): {d:.3f}")
            print()
    
    # Generate ablation summary
    print_header("GENERATING ABLATION SUMMARY", "=")
    scenario_id = ABLATION_SCENARIO['name']
    output_dir = Path(f"data/ablation_studies/{scenario_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary = generate_ablation_summary(variant_results, ABLATION_SCENARIO, output_dir)
    
    # Print comparison
    if summary.get("comparison"):
        print_info("  [Comparison]:")
        if "best_rating" in summary["comparison"]:
            best = summary["comparison"]["best_rating"]
            print_info(f"    → Best variant: {best['variant']} (rating: {best['rating']:.2f})")
        if "ratings" in summary["comparison"]:
            print_info("    → All variant ratings:")
            for variant_name, rating in sorted(summary["comparison"]["ratings"].items(), key=lambda x: x[1] or 0, reverse=True):
                print_info(f"      - {variant_name}: {rating:.2f}")
    
    print()
    print_header("ABLATION STUDY COMPLETED", "=")
    print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_success(f"All {len(VARIANTS)} variants processed")
    print_info(f"Summary saved to: {output_dir / 'ablation_summary.json'}")
    print()


if __name__ == "__main__":
    main()
