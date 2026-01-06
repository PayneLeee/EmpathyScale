"""
Test Phase 1 and Phase 2 Evaluation with Historical Data

This script tests the updated Phase 1 and Phase 2 evaluation logic using historical run data.
It verifies:
1. Phase 1 evaluation summary calculation with new validation metrics
2. Phase 2 evaluation summary calculation with validation_metrics (discriminant ability, Cronbach's alpha, factor scores)
3. Correct usage of phase parameter for independent persona groups
4. JSON serialization of all metrics

Usage:
    python tests/test_phase1_phase2_with_history.py [run_id]
    
If run_id is not provided, uses the most recent complete run.
"""

from pathlib import Path
import sys
import os
import json
from typing import Dict, List, Any, Optional

# Force unbuffered output for real-time progress display
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Ensure local imports work when run as script
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))

from agents.evaluation_agent_group import EvaluationAgentGroup
from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
from utils.data_manager import DataManager
from utils.prompt_manager import PromptManager


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}", flush=True)
    print(f"{text:^{width}}", flush=True)
    print(f"{char * width}\n", flush=True)


def print_section(text: str):
    """Print a section header."""
    print(f"\n{'─' * 80}", flush=True)
    print(f"{text}", flush=True)
    print(f"{'─' * 80}\n", flush=True)


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


def find_complete_runs(data_dir: Path) -> List[str]:
    """Find runs with complete Phase 1 and Phase 2 evaluation data."""
    complete_runs = []
    
    for run_dir in sorted(data_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        
        run_id = run_dir.name
        
        # Check for Phase 1 data
        phase1_summary = run_dir / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
        phase1_participants = run_dir / "evaluation_agent_group" / "selection" / "combined" / "participant_level_evaluations.json"
        
        # Check for Phase 2 data (optional)
        phase2_summary = run_dir / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
        phase2_participants = run_dir / "evaluation_agent_group" / "validation" / "participant_level_evaluations.json"
        
        # Check for selection results
        selection_config = run_dir / "statistical_selection" / "selection_config.json"
        
        # Check for items
        scale_draft = run_dir / "empathy_scale_generation_agent_group" / "scale_draft.md"
        filtered_draft = run_dir / "empathy_scale_generation_agent_group" / "filtered_scale_draft.md"
        
        has_phase1 = phase1_summary.exists() and phase1_participants.exists()
        has_phase2 = phase2_summary.exists() and phase2_participants.exists()
        has_selection = selection_config.exists()
        has_items = scale_draft.exists()
        
        if has_phase1 and has_selection and has_items:
            complete_runs.append({
                "run_id": run_id,
                "has_phase1": has_phase1,
                "has_phase2": has_phase2,
                "has_selection": has_selection,
                "has_items": has_items
            })
    
    return complete_runs


def load_phase1_data(run_id: str, dm: DataManager) -> Optional[Dict[str, Any]]:
    """Load Phase 1 evaluation data."""
    run_path = dm.get_run_path(run_id)
    
    summary_path = run_path / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
    participants_path = run_path / "evaluation_agent_group" / "selection" / "combined" / "participant_level_evaluations.json"
    
    if not summary_path.exists() or not participants_path.exists():
        return None
    
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        participants = json.loads(participants_path.read_text(encoding="utf-8"))
        return {
            "summary": summary,
            "participants": participants,
            "summary_path": summary_path
        }
    except Exception as e:
        print_error(f"Error loading Phase 1 data: {e}")
        return None


def load_phase2_data(run_id: str, dm: DataManager) -> Optional[Dict[str, Any]]:
    """Load Phase 2 evaluation data."""
    run_path = dm.get_run_path(run_id)
    
    summary_path = run_path / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
    participants_path = run_path / "evaluation_agent_group" / "validation" / "participant_level_evaluations.json"
    
    if not summary_path.exists() or not participants_path.exists():
        return None
    
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        participants = json.loads(participants_path.read_text(encoding="utf-8"))
        return {
            "summary": summary,
            "participants": participants,
            "summary_path": summary_path
        }
    except Exception as e:
        print_error(f"Error loading Phase 2 data: {e}")
        return None


def load_items(run_id: str, dm: DataManager, use_filtered: bool = False) -> List[Dict[str, str]]:
    """Load items from scale draft."""
    run_path = dm.get_run_path(run_id)
    
    if use_filtered:
        draft_path = run_path / "empathy_scale_generation_agent_group" / "filtered_scale_draft.md"
    else:
        draft_path = run_path / "empathy_scale_generation_agent_group" / "scale_draft.md"
    
    if not draft_path.exists():
        return []
    
    try:
        items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(
            draft_path.read_text(encoding="utf-8", errors="replace")
        )
        return items
    except Exception as e:
        print_error(f"Error loading items: {e}")
        return []


def load_factor_structure(run_id: str, dm: DataManager) -> Optional[Dict[int, int]]:
    """Load factor_structure from selection results."""
    run_path = dm.get_run_path(run_id)
    
    # Try efa_cfa_results.json first (newer format)
    efa_cfa_results_path = run_path / "statistical_selection" / "efa_cfa_results.json"
    if efa_cfa_results_path.exists():
        try:
            efa_cfa_results = json.loads(efa_cfa_results_path.read_text(encoding="utf-8"))
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
                
                return factor_structure if factor_structure else None
        except Exception as e:
            print_warning(f"Could not load factor_structure from efa_cfa_results.json: {e}")
    
    # Fallback: try selection_config.json (older format)
    selection_config_path = run_path / "statistical_selection" / "selection_config.json"
    if selection_config_path.exists():
        try:
            selection_config = json.loads(selection_config_path.read_text(encoding="utf-8"))
            efa_cfa_results = selection_config.get("efa_cfa_results", {})
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
                
                return factor_structure if factor_structure else None
        except Exception as e:
            print_warning(f"Could not load factor_structure from selection_config.json: {e}")
    
    return None


def test_phase1_with_history(run_id: str, dm: DataManager, eval_agent: EvaluationAgentGroup) -> bool:
    """Test Phase 1 evaluation summary recalculation."""
    print_section("Testing Phase 1 Evaluation Summary")
    
    # Load Phase 1 data
    phase1_data = load_phase1_data(run_id, dm)
    if not phase1_data:
        print_error("Could not load Phase 1 data")
        return False
    
    print_success(f"Loaded Phase 1 data: {len(phase1_data['participants'])} participants")
    
    # Load items
    items = load_items(run_id, dm, use_filtered=False)
    if not items:
        print_error("Could not load items")
        return False
    
    print_success(f"Loaded {len(items)} items")
    
    # Recalculate summary (without factor_structure for Phase 1)
    print_info("Recalculating Phase 1 summary with new _summarize method...")
    try:
        new_summary = eval_agent._summarize(phase1_data['participants'], items, factor_structure=None)
        
        # Check if validation_metrics were calculated
        if "validation_metrics" in new_summary:
            validation_metrics = new_summary["validation_metrics"]
            print_success("Phase 1 summary includes validation_metrics")
            
            # Check discriminant ability
            if "discriminant_ability" in validation_metrics:
                da = validation_metrics["discriminant_ability"]
                print_info(f"  → Discriminant ability: t={da.get('t_statistic', 'N/A')}, p={da.get('p_value', 'N/A')}, significant={da.get('significant', 'N/A')}")
            
            # Check internal consistency
            if "internal_consistency" in validation_metrics:
                ic = validation_metrics["internal_consistency"]
                print_info(f"  → Cronbach's α: {ic.get('alpha', 'N/A')} (95% CI: [{ic.get('ci_lower', 'N/A')}, {ic.get('ci_upper', 'N/A')}])")
        else:
            print_warning("Phase 1 summary does not include validation_metrics (may be expected if no empathic/non-empathic distinction)")
        
        # Test JSON serialization
        try:
            json_str = json.dumps(new_summary, indent=2, ensure_ascii=False)
            print_success("Phase 1 summary is JSON serializable")
        except TypeError as e:
            print_error(f"Phase 1 summary JSON serialization failed: {e}")
            return False
        
        return True
    except Exception as e:
        print_error(f"Error recalculating Phase 1 summary: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase2_with_history(run_id: str, dm: DataManager, eval_agent: EvaluationAgentGroup) -> bool:
    """Test Phase 2 evaluation summary recalculation with validation metrics."""
    print_section("Testing Phase 2 Evaluation Summary")
    
    # Load Phase 2 data
    phase2_data = load_phase2_data(run_id, dm)
    if not phase2_data:
        print_warning("Phase 2 data not found, skipping Phase 2 test")
        return True  # Not an error, just missing data
    
    print_success(f"Loaded Phase 2 data: {len(phase2_data['participants'])} participants")
    
    # Load filtered items
    filtered_items = load_items(run_id, dm, use_filtered=True)
    if not filtered_items:
        print_warning("Could not load filtered items, using original items")
        filtered_items = load_items(run_id, dm, use_filtered=False)
        if not filtered_items:
            print_error("Could not load any items")
            return False
    
    print_success(f"Loaded {len(filtered_items)} filtered items")
    
    # Load factor_structure
    factor_structure = load_factor_structure(run_id, dm)
    if factor_structure:
        print_success(f"Loaded factor_structure: {len(factor_structure)} items mapped to factors")
    else:
        print_warning("Could not load factor_structure, will calculate without factor scores")
    
    # Recalculate summary with factor_structure
    print_info("Recalculating Phase 2 summary with validation_metrics...")
    try:
        new_summary = eval_agent._summarize(
            phase2_data['participants'], 
            filtered_items, 
            factor_structure=factor_structure
        )
        
        # Check validation_metrics
        if "validation_metrics" not in new_summary:
            print_error("Phase 2 summary does not include validation_metrics")
            return False
        
        validation_metrics = new_summary["validation_metrics"]
        print_success("Phase 2 summary includes validation_metrics")
        
        # Display validation metrics
        print_info("  [Validation Metrics]:")
        
        # Discriminant ability
        if "discriminant_ability" in validation_metrics:
            da = validation_metrics["discriminant_ability"]
            print_info(f"    → Discriminant Ability (t-test):")
            print_info(f"      - Empathic mean: {da.get('empathic_mean', 'N/A')}")
            print_info(f"      - Non-empathic mean: {da.get('non_empathic_mean', 'N/A')}")
            print_info(f"      - t-statistic: {da.get('t_statistic', 'N/A')}")
            print_info(f"      - p-value: {da.get('p_value', 'N/A')}")
            print_info(f"      - Cohen's d: {da.get('cohens_d', 'N/A')}")
            print_info(f"      - Significant: {da.get('significant', 'N/A')} (p < 0.001)")
        else:
            print_warning("    → Discriminant ability not calculated (may need empathic/non-empathic personas)")
        
        # Internal consistency
        if "internal_consistency" in validation_metrics:
            ic = validation_metrics["internal_consistency"]
            print_info(f"    → Internal Consistency (Cronbach's α):")
            print_info(f"      - Alpha: {ic.get('alpha', 'N/A')}")
            print_info(f"      - 95% CI: [{ic.get('ci_lower', 'N/A')}, {ic.get('ci_upper', 'N/A')}]")
            print_info(f"      - n_items: {ic.get('n_items', 'N/A')}, n_participants: {ic.get('n_participants', 'N/A')}")
        else:
            print_warning("    → Internal consistency not calculated")
        
        # Factor scores
        if "factor_scores" in validation_metrics:
            fs = validation_metrics["factor_scores"]
            print_info(f"    → Factor Scores:")
            for factor_name, scores in sorted(fs.items()):
                print_info(f"      - {factor_name}: M={scores.get('mean', 'N/A')}, SD={scores.get('std', 'N/A')}, n_items={scores.get('n_items', 'N/A')}")
        else:
            print_warning("    → Factor scores not calculated (factor_structure may be missing)")
        
        # Test JSON serialization
        try:
            json_str = json.dumps(new_summary, indent=2, ensure_ascii=False)
            print_success("Phase 2 summary is JSON serializable")
            
            # Optionally save updated summary
            output_path = phase2_data['summary_path'].parent / "evaluation_summary_with_validation_metrics.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print_info(f"Saved updated summary to: {output_path.name}")
        except TypeError as e:
            print_error(f"Phase 2 summary JSON serialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    except Exception as e:
        print_error(f"Error recalculating Phase 2 summary: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_parameter_usage(run_id: str, dm: DataManager) -> bool:
    """Test that phase parameter is correctly used for persona loading."""
    print_section("Testing Phase Parameter Usage")
    
    run_path = dm.get_run_path(run_id)
    
    # Load scenario
    interview_summary_path = run_path / "interview_agent_group" / "summary.json"
    if not interview_summary_path.exists():
        print_warning("Interview summary not found, cannot test phase parameter")
        return True
    
    try:
        scenario = json.loads(interview_summary_path.read_text(encoding="utf-8"))
        scenario_id = scenario.get('name')
        
        if not scenario_id:
            print_warning("Scenario name not found")
            return True
        
        print_info(f"Testing persona loading for scenario: {scenario_id}")
        
        # Check persona files
        from agents.persona_generation_agent import PersonaGenerationAgent
        import os
        api_key = os.getenv("OPENAI_API_KEY", "dummy_key")  # Use dummy key for loading only
        persona_agent = PersonaGenerationAgent(api_key=api_key)
        
        # Test Phase 1 (selection)
        selection_personas = persona_agent.load_personas(scenario_id, phase="selection")
        if selection_personas:
            print_success(f"Phase 1 (selection) personas loaded: {len(selection_personas)} personas")
            empathic_count = sum(1 for p in selection_personas if p.get("empathy_condition") == "empathic")
            non_empathic_count = sum(1 for p in selection_personas if p.get("empathy_condition") == "non_empathic")
            print_info(f"  → Empathic: {empathic_count}, Non-empathic: {non_empathic_count}")
        else:
            print_warning("Phase 1 (selection) personas not found")
        
        # Test Phase 2 (validation)
        validation_personas = persona_agent.load_personas(scenario_id, phase="validation")
        if validation_personas:
            print_success(f"Phase 2 (validation) personas loaded: {len(validation_personas)} personas")
            empathic_count = sum(1 for p in validation_personas if p.get("empathy_condition") == "empathic")
            non_empathic_count = sum(1 for p in validation_personas if p.get("empathy_condition") == "non_empathic")
            print_info(f"  → Empathic: {empathic_count}, Non-empathic: {non_empathic_count}")
            
            # Verify they are different from Phase 1
            if selection_personas and validation_personas:
                if len(selection_personas) != len(validation_personas):
                    print_success("Phase 1 and Phase 2 use different persona groups (different sizes)")
                else:
                    # Check if they are actually different
                    selection_ids = {p.get("persona_id") for p in selection_personas}
                    validation_ids = {p.get("persona_id") for p in validation_personas}
                    if selection_ids != validation_ids:
                        print_success("Phase 1 and Phase 2 use different persona groups (different IDs)")
                    else:
                        print_warning("Phase 1 and Phase 2 personas have same IDs (may be same group)")
        else:
            print_warning("Phase 2 (validation) personas not found")
        
        return True
    except Exception as e:
        print_error(f"Error testing phase parameter: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_historical_data(run_id: str, dm: DataManager, prompts: PromptManager) -> bool:
    """Test Phase 1 and Phase 2 evaluation with historical data."""
    print_header(f"Testing Phase 1 & Phase 2 with Historical Data: {run_id}")
    
    # Initialize evaluation agent (API key not needed for summary recalculation)
    import os
    api_key = os.getenv("OPENAI_API_KEY", "dummy_key")  # Use dummy key for summary calculation only
    eval_agent = EvaluationAgentGroup(api_key=api_key, prompts_dir=prompts.prompts_dir)
    
    # Test Phase 1
    phase1_success = test_phase1_with_history(run_id, dm, eval_agent)
    
    # Test Phase 2
    phase2_success = test_phase2_with_history(run_id, dm, eval_agent)
    
    # Test phase parameter usage
    phase_param_success = test_phase_parameter_usage(run_id, dm)
    
    # Summary
    print_section("Test Summary")
    print_info(f"Phase 1 test: {'PASSED' if phase1_success else 'FAILED'}")
    print_info(f"Phase 2 test: {'PASSED' if phase2_success else 'FAILED'}")
    print_info(f"Phase parameter test: {'PASSED' if phase_param_success else 'FAILED'}")
    
    overall_success = phase1_success and phase2_success and phase_param_success
    
    if overall_success:
        print_success("All tests passed!")
    else:
        print_error("Some tests failed")
    
    return overall_success


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Phase 1 and Phase 2 evaluation with historical data")
    parser.add_argument("run_id", nargs="?", help="Run ID to test (default: most recent complete run)")
    args = parser.parse_args()
    
    # Initialize data manager and prompts
    dm = DataManager()
    prompts = PromptManager()
    
    # Find run to test
    if args.run_id:
        run_id = args.run_id
        run_path = dm.get_run_path(run_id)
        if not run_path.exists():
            print_error(f"Run ID not found: {run_id}")
            return 1
    else:
        print_info("Finding most recent complete run...")
        complete_runs = find_complete_runs(dm.runs_dir)
        if not complete_runs:
            print_error("No complete runs found with Phase 1 evaluation data")
            return 1
        
        # Show available runs
        print_info("Available complete runs:")
        for i, run_info in enumerate(complete_runs[:10]):  # Show first 10
            status = "[OK] Phase 1+2" if run_info["has_phase2"] else "[OK] Phase 1 only"
            print_info(f"  {i+1}. {run_info['run_id']} ({status})")
        
        run_id = complete_runs[0]["run_id"]
        print_info(f"\nUsing run: {run_id}")
    
    # Run test
    success = test_with_historical_data(run_id, dm, prompts)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

