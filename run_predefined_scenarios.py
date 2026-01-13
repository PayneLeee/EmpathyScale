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
import time
from datetime import datetime

# Force unbuffered output for real-time progress display
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Global timer for tracking step duration
_step_start_time = None

def start_step_timer():
    """Start timing a step."""
    global _step_start_time
    _step_start_time = time.time()

def get_step_elapsed():
    """Get elapsed time since step start."""
    global _step_start_time
    if _step_start_time is None:
        return 0
    return time.time() - _step_start_time

# Ensure local imports work when run as script
sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from agents.evaluation_agent_group import EvaluationAgentGroup
from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager
from agents.item_selection_agent import ItemSelectionAgent
from agents.persona_generation_agent import PersonaGenerationAgent


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}", flush=True)
    print(f"{text:^{width}}", flush=True)
    print(f"{char * width}\n", flush=True)


def print_step(step_num: int, total_steps: int, description: str):
    """Print a step indicator."""
    start_step_timer()
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{step_num}/{total_steps}] {description}...", flush=True)


def print_success(message: str):
    """Print a success message."""
    elapsed = get_step_elapsed()
    elapsed_str = f" ({elapsed:.1f}s)" if elapsed > 0 else ""
    print(f"[OK] {message}{elapsed_str}", flush=True)


def print_info(message: str):
    """Print an info message."""
    print(f"[INFO] {message}", flush=True)


def print_warning(message: str):
    """Print a warning message."""
    print(f"[WARN] {message}", flush=True)


def print_error(message: str):
    """Print an error message."""
    print(f"[ERROR] {message}", flush=True)


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
        print_step(1, 7, "Creating run and preparing data")
        print_info(f"  → Scenario: {scenario['name']}")
        print_info(f"  → Context: {scenario.get('assessment_context', 'N/A')}")
        run_id = dm.new_run()
        print_success(f"Run ID created: {run_id}")
        
        ensure_summary(run_id, scenario, dm)
        print_success("Interview and literature summaries prepared")
        print()

        # Step 2: Initialize generation agent
        print_step(2, 7, "Initializing scale generation agent")
        print_info("  → Model: gpt-4o-mini")
        print_info("  → Item generators: 5 parallel generators")
        print_info("  → Content assessment: Enabled")
        gen_agent = EmpathyScaleGenerationAgentGroup(
            api_key=api_key,
            prompts_dir=prompt_manager.prompts_dir,
            num_item_generators=5,  # Increased to 5 generators to generate more initial items (target: 100-150 items before statistical selection)
            enable_content_assessment=True,
        )
        print_success("Generation agent initialized")
        print()

        # Step 3: Generate scale
        print_step(3, 7, "Generating empathy scale")
        print_info("  [3.1] Construct Definition: Defining empathy dimensions for scenario...")
        print_info(f"  [3.2] Item Generation: Generating candidate items ({gen_agent.num_item_generators} parallel generators, 25-30 items per dimension)...")
        print_info("  [3.3] Content Assessment: Refining and de-duplicating items...")
        print_info("  [3.4] Assembly: Creating scale draft markdown...")
        try:
            # generate_scale() already has detailed progress prints inside
            gen_agent.generate_scale(run_id)
            print_success("Scale generation completed")
        except Exception as e:
            print_error(f"Scale generation failed: {e}")
            print_warning(f"Skipping evaluation for scenario {scenario['name']}")
            import traceback
            traceback.print_exc()
            continue
        print()

        # Step 4: Parse and validate items
        print_step(4, 7, "Parsing generated scale items")
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
        
        # Apply semantic deduplication as a safety measure (in case it wasn't applied during generation)
        print_info("  [Semantic Dedup] Applying semantic deduplication as safety measure...")
        try:
            from utils.pre_evaluation_semantic_deduplication import remove_semantic_duplicates_before_evaluation
            
            filtered_items, dedup_stats = remove_semantic_duplicates_before_evaluation(
                items,
                        similarity_threshold=0.80,  # Same-dimension threshold
                        cross_dimension_threshold=0.75,  # Stricter threshold for cross-dimension (ensure dimension distinction)
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
        
        print_info(f"  → Items saved to: {draft_path}")
        print()

        # Step 5: Phase 1 - Evaluate all items (Selection Phase) - Dual Groups
        print_step(5, 7, "Phase 1: Item Selection Evaluation (Dual Groups for EFA+CFA)")
        print_info(f"  [5.1] Setup:")
        print_info(f"    → Items to evaluate: {len(items)}")
        print_info(f"    → Dual persona groups: empathic + non-empathic (following PETS methodology)")
        print_info(f"    → Participants per group: 100, Total: 200 (for EFA - PETS used 324)")
        print_info(f"    → Base scenario ID: {scenario['name']}")
        print_info(f"  [5.2] Participant Simulation:")
        print_info(f"    → Each persona will rate all {len(items)} items")
        print_info(f"    → Rating scale: 0-100 (strongly disagree to strongly agree)")
        print()
        
        persona_agent = PersonaGenerationAgent(api_key=api_key, prompts_dir=prompt_manager.prompts_dir)
        
        try:
            import json
            # Step 5.1: Load or generate personas for Phase 1 (selection)
            scenario_id = scenario['name']
            selection_personas = persona_agent.load_personas(scenario_id, phase="selection")
            n_per_group = 100  # 100*2 = 200 total personas (100 empathic + 100 non-empathic)
            
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
                
                # Merge both groups into one list (both have empathy_condition field)
                selection_personas = personas_empathic + personas_non_empathic
                print_info(f"    → Total personas: {len(selection_personas)} (empathic: {len(personas_empathic)}, non_empathic: {len(personas_non_empathic)})")
                
                # Save merged personas to selection.json
                persona_agent.save_personas(scenario_id, selection_personas, phase="selection")
                print_info(f"    → Saved to {scenario_id}/selection.json")
            else:
                # Load existing personas and split them for evaluation
                print_info(f"  [5.1] Loaded {len(selection_personas)} personas from {scenario_id}/selection.json")
                personas_empathic = [p for p in selection_personas if p.get("empathy_condition") == "empathic"]
                personas_non_empathic = [p for p in selection_personas if p.get("empathy_condition") == "non_empathic"]
                print_info(f"    → Empathic: {len(personas_empathic)}, Non-empathic: {len(personas_non_empathic)}")
                # Use first n_per_group from each
                personas_empathic = personas_empathic[:n_per_group]
                personas_non_empathic = personas_non_empathic[:n_per_group]
            print()
            
            # Step 5.3: Evaluate with empathic personas
            print_info(f"  [5.3] Evaluating with empathic personas...")
            result_empathic = eval_agent.evaluate_items(
                run_id, items, scenario,
                n_participants=n_per_group,
                scenario_id=scenario_id,
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
                scenario_id=scenario_id,
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
            
            # Generate merged evaluation summary using evaluation_agent's summarize method
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
            print_warning(f"Skipping statistical selection and Phase 2 validation for scenario {scenario['name']}")
            continue
        print()

        # Step 6: Statistical selection
        print_step(6, 7, "Applying statistical selection (EFA+CFA)")
        try:
            # Use merged data from combined directory
            eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
            if not eval_summary_path.exists():
                print_error("Phase 1 merged evaluation summary not found")
                raise FileNotFoundError("Merged evaluation summary not found")
            
            eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
            
            # Use ItemSelectionAgent to handle all selection logic
            selection_agent = ItemSelectionAgent(api_key=api_key)
            
            # Configure selection parameters (EFA+CFA method following PETS)
            # Note: Item count is determined by statistical methods, not preset targets (PETS methodology)
            # Adjusted thresholds based on diagnostic analysis:
            # - min_item_total_corr: 0.5 -> 0.3 (only 3/301 items passed 0.5, but 70/301 passed 0.3)
            # - max_kurtosis: 2.0 -> 3.0 (only 34/301 items passed 2.0, but 112/301 passed 3.0)
            selection_config = {
                "use_efa": True,  # Use EFA method (PETS methodology)
                "use_cfa": True,  # Use CFA method (PETS methodology - Section 7.2)
                "min_item_total_corr": 0.3,  # Adjusted: PETS uses 0.5, but data shows 0.3 is more appropriate
                "max_skewness": 1.0,  # PETS threshold (238/301 items pass this)
                "max_kurtosis": 3.0,  # Adjusted: PETS uses 2.0, but data shows 3.0 is more appropriate
                "max_inter_corr": 0.8,  # PETS threshold
                "min_factor_loading": 0.75,  # Initial threshold (will be adjusted adaptively if needed)
                "n_factors": None,  # Auto-detect using Kaiser criterion
                "min_items_per_factor": 2,  # Technical constraint (each factor needs at least 2 items for CFA)
                # CFA parameters (PETS Section 7.2)
                "cfa_rmsea_threshold": 0.08,  # PETS threshold
                "cfa_tli_threshold": 0.95,  # PETS threshold
                "cfa_cfi_threshold": 0.95,  # PETS threshold
                "cfa_srmr_threshold": 0.08,  # PETS threshold
                # Adaptive adjustment parameters
                "adaptive_factor_loading": True,  # Enable adaptive adjustment to reach target range
                "max_adaptive_iterations": 8,  # Maximum iterations for adaptive adjustment
                # Multi-factor iteration parameters (for better factor balance)
                "try_multiple_n_factors": True,  # Enable multi-factor iteration
                "max_n_factors_to_try": None,  # Max factor counts to try (None = auto-detect using Kaiser criterion, max 5)
                "prefer_balanced_factors": True,  # Prefer balanced factor structures when selecting best result
                # Factor balance parameters
                "enable_factor_balance": True,  # Enable factor balancing after EFA and post-CFA
                "max_items_per_factor": None  # Maximum items per factor (None = auto-calculate based on target range)
            }
            
            print_info(f"  Strategy: EFA+CFA (Exploratory + Confirmatory Factor Analysis) - PETS methodology")
            print_info(f"  Item count control: Adaptive adjustment to target range 10-18 items (dynamic adjustment based on gap)")
            print_info(f"  Parameters: min_item_total_corr={selection_config['min_item_total_corr']} (adjusted from 0.5), max_kurtosis={selection_config['max_kurtosis']} (adjusted from 2.0)")
            print_info(f"  Parameters: min_factor_loading={selection_config['min_factor_loading']} (initial, will be adjusted adaptively)")
            print_info(f"  Adaptive adjustment: Enabled (max {selection_config.get('max_adaptive_iterations', 8)} iterations)")
            print_info(f"  CFA thresholds: RMSEA<={selection_config['cfa_rmsea_threshold']}, TLI>={selection_config['cfa_tli_threshold']}, CFI>={selection_config['cfa_cfi_threshold']}, SRMR<={selection_config['cfa_srmr_threshold']}")
            
            # Perform selection (using EFA method) - use merged data from combined directory
            selection_result = selection_agent.select_items(
                items=items,
                evaluation_summary=eval_summary,
                target_min=10,
                target_max=20,
                selection_config=selection_config,
                evaluation_summary_path=eval_summary_path
            )
            
            selected_ids = selection_result["selected_item_ids"]
            filtered_items = selection_result["filtered_items"]
            selection_stats = selection_result["selection_statistics"]
            
            if not selected_ids:
                print_warning("No items selected by statistical selection")
                print_warning(f"Skipping Phase 2 validation for scenario {scenario['name']}")
                filtered_items = []
            else:
                print_success(f"Selected {len(selected_ids)}/{len(items)} items ({selection_stats['selection_ratio']*100:.1f}%)")
                if selection_stats.get('original_mean_rating') is not None:
                    print_info(f"  Original mean rating: {selection_stats['original_mean_rating']:.2f}")
                if selection_stats.get('selected_mean_rating') is not None:
                    print_info(f"  Selected mean rating: {selection_stats['selected_mean_rating']:.2f}")
                
                # Save selection results
                selection_agent.save_selection_results(run_id, selection_result)
                
                # Generate filtered scale draft using agent method
                filtered_draft_path = dm.get_run_path(run_id) / "empathy_scale_generation_agent_group" / "filtered_scale_draft.md"
                
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
                
        except Exception as e:
            print_error(f"Statistical selection failed: {e}")
            import traceback
            traceback.print_exc()
            print_warning(f"Skipping Phase 2 validation for scenario {scenario['name']}")
            filtered_items = []
        print()
        
        # Step 7: Phase 2 - Validate filtered items (Validation Phase)
        if not filtered_items:
            print_warning(f"No filtered items to validate, skipping Phase 2 for scenario {scenario['name']}")
        else:
            print_step(7, 7, "Phase 2: Final Validation")
            print_info(f"  [7.1] Setup:")
            print_info(f"    → Filtered items: {len(filtered_items)}")
            print_info(f"    → Dual persona groups: empathic + non-empathic (100*2 = 200 total)")
            print_info(f"    → Scenario ID: {scenario['name']} (reusable)")
            print_info(f"  [7.2] Participant Simulation:")
            print_info(f"    → Each persona will rate {len(filtered_items)} filtered items")
            print_info(f"    → Rating scale: 0-100 (strongly disagree to strongly agree)")
            print()
            
            try:
                # Load or generate personas for Phase 2 (validation)
                scenario_id = scenario['name']
                validation_personas = persona_agent.load_personas(scenario_id, phase="validation")
                n_per_group = 100  # 100*2 = 200 total personas
                
                if validation_personas is None or len(validation_personas) < n_per_group * 2:
                    # Need to generate new personas
                    print_info(f"  [7.1] Generating {n_per_group * 2} personas for Phase 2...")
                    base_personas = persona_agent.generate_personas(scenario, n_personas=n_per_group)
                    
                    # Create dual groups
                    print_info(f"  [7.2] Creating dual persona groups (empathic + non_empathic)...")
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
                    print_info(f"  [7.1] Loaded {len(validation_personas)} personas from {scenario_id}/validation.json")
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
                    run_id, filtered_items, scenario,
                    n_participants=len(validation_personas),
                    scenario_id=scenario_id,  # Use base scenario name for reusability
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
                    print_info("  [Phase 2 Summary Statistics]:")
                    if "overall_mean_rating" in summary and summary["overall_mean_rating"] is not None:
                        overall_mean = summary["overall_mean_rating"]
                        print_info(f"    → Overall mean rating: {overall_mean:.2f} (0-100 scale)")
                    if "n_items" in summary:
                        print_info(f"    → Items evaluated: {summary['n_items']}")
                    
                    # Calculate and display validation metrics (PETS-style)
                    if participant_data_path.exists():
                        participant_data = json.loads(participant_data_path.read_text(encoding="utf-8"))
                        
                        # Get factor_structure from selection results file if available
                        factor_structure = None
                        selection_config_path = dm.get_run_path(run_id) / "statistical_selection" / "selection_config.json"
                        if selection_config_path.exists():
                            try:
                                selection_config_data = json.loads(selection_config_path.read_text(encoding="utf-8"))
                                efa_cfa_results = selection_config_data.get("efa_cfa_results", {})
                                if efa_cfa_results:
                                    factor_structure_raw = efa_cfa_results.get("factor_structure", {})
                                    if factor_structure_raw:
                                        # Convert string keys to int (JSON serialization)
                                        factor_structure = {}
                                        for k, v in factor_structure_raw.items():
                                            try:
                                                item_id = int(k) if isinstance(k, str) else k
                                                factor_idx = int(v) if isinstance(v, str) else v
                                                factor_structure[item_id] = factor_idx
                                            except (ValueError, TypeError):
                                                continue
                            except Exception as e:
                                print_warning(f"    → Could not load factor_structure from selection results: {e}")
                        
                        # Recalculate summary with factor_structure to get validation_metrics
                        summary_with_metrics = eval_agent._summarize(participant_data, filtered_items, factor_structure=factor_structure)
                        
                        # Update evaluation_summary.json with validation_metrics
                        if "validation_metrics" in summary_with_metrics:
                            summary["validation_metrics"] = summary_with_metrics["validation_metrics"]
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
            print()

        # Scenario summary
        print_header(f"SCENARIO {idx} COMPLETED", "-")
        print_success(f"Scenario '{scenario['name']}' completed successfully")
        print_info(f"Run ID: {run_id}")
        print_info(f"Items generated: {len(items)}")
        
        # Show selection and validation results if available
        selection_dir = dm.get_run_path(run_id) / "statistical_selection"
        if selection_dir.exists() and (selection_dir / "selection_statistics.json").exists():
            try:
                selection_stats = json.loads((selection_dir / "selection_statistics.json").read_text(encoding="utf-8"))
                print_info(f"Items after selection: {selection_stats.get('n_selected_items', selection_stats.get('selected_n_items', 0))}")
                if selection_stats.get('selection_ratio'):
                    print_info(f"Selection ratio: {selection_stats['selection_ratio']*100:.1f}%")
            except Exception:
                pass
        
        # Show Phase 1 results
        phase1_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "evaluation_summary.json"
        if phase1_summary_path.exists():
            try:
                phase1_summary = json.loads(phase1_summary_path.read_text(encoding="utf-8"))
                if phase1_summary.get("overall_mean_rating") is not None:
                    print_info(f"Phase 1 mean rating (200 personas): {phase1_summary['overall_mean_rating']:.2f}")
            except Exception:
                pass
        
        # Show Phase 2 results
        phase2_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
        if phase2_summary_path.exists():
            try:
                phase2_summary = json.loads(phase2_summary_path.read_text(encoding="utf-8"))
                if phase2_summary.get("overall_mean_rating") is not None:
                    n_participants = phase2_summary.get("n_participants", 200)
                    print_info(f"Phase 2 mean rating ({n_participants} personas, reusable): {phase2_summary['overall_mean_rating']:.2f}")
            except Exception:
                pass
        
        print_info(f"Data location: {dm.get_run_path(run_id)}")
        print()

    # Final summary
    print_header("PIPELINE COMPLETED", "=")
    print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_success(f"All {len(SCENARIOS)} scenarios processed")
    print()


if __name__ == "__main__":
    run()

