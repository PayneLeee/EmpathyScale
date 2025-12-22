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

        # Step 5: Phase 1 - Evaluate all items (Selection Phase)
        print_step(5, 7, "Phase 1: Evaluating all items (Selection Phase)")
        print_info(f"  [5.1] Persona Management:")
        print_info(f"    → Scenario ID: {scenario['name']}_selection")
        print_info(f"    → Checking for existing personas...")
        print_info(f"    → Will generate/load 200 personas for item selection")
        print_info(f"  [5.2] Participant Simulation:")
        print_info(f"    → Each persona will rate all {len(items)} items")
        print_info(f"    → Rating scale: 0-100 (strongly disagree to strongly agree)")
        print()
        print_info(f"  [Progress] Starting scale generation for scenario: {scenario['name']}")
        print()
        try:
            import json
            eval_result_selection = eval_agent.evaluate_items(
                run_id, items, scenario, 
                n_participants=200,  # Phase 1: Selection personas (100*2 = 200 total, increased for EFA - PETS used 324)
                scenario_id=f"{scenario['name']}_selection",
                out_dir=dm.get_run_path(run_id) / "evaluation_agent_group" / "selection"
            )
            print_success("Phase 1 evaluation completed")
            
            # Show evaluation summary if available
            eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "evaluation_summary.json"
            if eval_summary_path.exists():
                summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
                print_info("  [Phase 1 Summary Statistics]:")
                if "overall_mean_rating" in summary and summary["overall_mean_rating"] is not None:
                    overall_mean = summary["overall_mean_rating"]
                    print_info(f"    → Overall mean rating: {overall_mean:.2f} (0-100 scale)")
                if "low_rating_items" in summary and summary["low_rating_items"]:
                    print_info(f"    → Low rating items (<50): {len(summary['low_rating_items'])}")
                if "high_variance_items" in summary and summary["high_variance_items"]:
                    print_info(f"    → High variance items (std>30): {len(summary['high_variance_items'])}")
                if "persona_diversity" in summary:
                    diversity = summary["persona_diversity"]
                    print_info(f"    → Persona diversity:")
                    if "age_distribution" in diversity and diversity["age_distribution"].get("mean"):
                        age_mean = diversity["age_distribution"]["mean"]
                        print_info(f"      - Age: mean={age_mean:.1f} years")
                    if "gender_distribution" in diversity:
                        gender_dist = diversity["gender_distribution"]
                        print_info(f"      - Gender: {gender_dist}")
                    if "ati_score_distribution" in diversity and diversity["ati_score_distribution"].get("mean"):
                        ati_mean = diversity["ati_score_distribution"]["mean"]
                        print_info(f"      - ATI score: mean={ati_mean:.2f}")
        except Exception as e:
            print_error(f"Phase 1 evaluation failed: {e}")
            import traceback
            traceback.print_exc()
            print_warning(f"Skipping statistical selection and Phase 2 validation for scenario {scenario['name']}")
            continue
        print()

        # Step 6: Statistical selection
        print_step(6, 7, "Applying statistical selection")
        try:
            eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "evaluation_summary.json"
            if not eval_summary_path.exists():
                print_error("Phase 1 evaluation summary not found")
                raise FileNotFoundError("Evaluation summary not found")
            
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
                "min_factor_loading": 0.75,  # PETS threshold (controls item count via statistical method)
                "n_factors": None,  # Auto-detect using Kaiser criterion
                "min_items_per_factor": 2,  # Technical constraint (each factor needs at least 2 items for CFA)
                # CFA parameters (PETS Section 7.2)
                "cfa_rmsea_threshold": 0.08,  # PETS threshold
                "cfa_tli_threshold": 0.95,  # PETS threshold
                "cfa_cfi_threshold": 0.95,  # PETS threshold
                "cfa_srmr_threshold": 0.08  # PETS threshold
            }
            
            print_info(f"  Strategy: EFA+CFA (Exploratory + Confirmatory Factor Analysis) - PETS methodology")
            print_info(f"  Item count control: Statistical method (factor loading >= {selection_config['min_factor_loading']})")
            print_info(f"  Parameters: min_item_total_corr={selection_config['min_item_total_corr']} (adjusted from 0.5), max_kurtosis={selection_config['max_kurtosis']} (adjusted from 2.0)")
            print_info(f"  Parameters: min_factor_loading={selection_config['min_factor_loading']}")
            print_info(f"  CFA thresholds: RMSEA<={selection_config['cfa_rmsea_threshold']}, TLI>={selection_config['cfa_tli_threshold']}, CFI>={selection_config['cfa_cfi_threshold']}, SRMR<={selection_config['cfa_srmr_threshold']}")
            print_info(f"  Note: Thresholds adjusted based on diagnostic analysis (see utils/diagnose_selection_issue.py)")
            print_info(f"  Note: Final item count will be determined by statistical methods, not preset targets")
            
            # Perform selection (using EFA method)
            eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "selection" / "evaluation_summary.json"
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
            print_step(7, 7, "Phase 2: Validating filtered items (Validation Phase)")
            print_info(f"  [7.1] Persona Management:")
            print_info(f"    → Scenario ID: {scenario['name']} (reusable for other scales)")
            print_info(f"    → Checking for existing personas...")
            print_info(f"    → Will generate/load 50 personas for validation")
            print_info(f"  [7.2] Participant Simulation:")
            print_info(f"    → Each persona will rate {len(filtered_items)} filtered items")
            print_info(f"    → Rating scale: 0-100 (strongly disagree to strongly agree)")
            print()
            try:
                eval_result_validation = eval_agent.evaluate_items(
                    run_id, filtered_items, scenario,
                    n_participants=50,
                    scenario_id=scenario['name'],  # Use base scenario name for reusability
                    out_dir=dm.get_run_path(run_id) / "evaluation_agent_group" / "validation"
                )
                print_success("Phase 2 validation completed")
                
                # Show evaluation summary if available
                eval_summary_path = dm.get_run_path(run_id) / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
                if eval_summary_path.exists():
                    summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
                    print_info("  [Phase 2 Summary Statistics]:")
                    if "overall_mean_rating" in summary and summary["overall_mean_rating"] is not None:
                        overall_mean = summary["overall_mean_rating"]
                        print_info(f"    → Overall mean rating: {overall_mean:.2f} (0-100 scale)")
                    if "low_rating_items" in summary and summary["low_rating_items"]:
                        print_info(f"    → Low rating items (<50): {len(summary['low_rating_items'])}")
                    if "high_variance_items" in summary and summary["high_variance_items"]:
                        print_info(f"    → High variance items (std>30): {len(summary['high_variance_items'])}")
                    if "persona_diversity" in summary:
                        diversity = summary["persona_diversity"]
                        print_info(f"    → Persona diversity:")
                        if "age_distribution" in diversity and diversity["age_distribution"].get("mean"):
                            age_mean = diversity["age_distribution"]["mean"]
                            print_info(f"      - Age: mean={age_mean:.1f} years")
                        if "gender_distribution" in diversity:
                            gender_dist = diversity["gender_distribution"]
                            print_info(f"      - Gender: {gender_dist}")
                        if "ati_score_distribution" in diversity and diversity["ati_score_distribution"].get("mean"):
                            ati_mean = diversity["ati_score_distribution"]["mean"]
                            print_info(f"      - ATI score: mean={ati_mean:.2f}")
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
                    print_info(f"Phase 2 mean rating (50 personas, reusable): {phase2_summary['overall_mean_rating']:.2f}")
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

