"""
Unit Test: Factor Balance and Item Count Control with Historical Data

This script tests the improved factor balancing and item count control logic
using existing historical run data. It re-runs the statistical selection process
and compares results to verify improvements.

Usage:
    python tests/test_factor_balance_with_history.py [run_id]

If run_id is not provided, it will use the most recent run with complete data.
"""

from pathlib import Path
import sys
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Force unbuffered output for real-time progress display
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Ensure local imports work when run as script
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "agents"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))

from agents.item_selection_agent import ItemSelectionAgent
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
    print(f"  {text}", flush=True)
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
    """Find runs with complete Phase 1 evaluation data."""
    complete_runs = []
    
    for run_dir in sorted(data_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        
        run_id = run_dir.name
        
        # Check for required files
        eval_summary = run_dir / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
        participant_data = run_dir / "evaluation_agent_group" / "selection" / "combined" / "participant_level_evaluations.json"
        scale_draft = run_dir / "empathy_scale_generation_agent_group" / "scale_draft.md"
        
        if eval_summary.exists() and participant_data.exists() and scale_draft.exists():
            complete_runs.append(run_id)
    
    return complete_runs


def load_historical_selection_result(run_id: str, dm: DataManager) -> Optional[Dict[str, Any]]:
    """Load historical selection result for comparison."""
    run_path = dm.get_run_path(run_id)
    selection_config_path = run_path / "statistical_selection" / "selection_config.json"
    
    if not selection_config_path.exists():
        return None
    
    try:
        with open(selection_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print_warning(f"Could not load historical selection config: {e}")
        return None


def load_items(run_id: str, dm: DataManager) -> List[Dict[str, str]]:
    """Load items from scale draft."""
    run_path = dm.get_run_path(run_id)
    scale_draft_path = run_path / "empathy_scale_generation_agent_group" / "scale_draft.md"
    
    if not scale_draft_path.exists():
        raise FileNotFoundError(f"Scale draft not found: {scale_draft_path}")
    
    items = []
    current_dimension = None
    
    with open(scale_draft_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('###'):
                # Extract dimension name
                current_dimension = line.replace('###', '').strip()
            elif line.startswith('- Item'):
                # Extract item text
                parts = line.split(':', 1)
                if len(parts) == 2:
                    item_id_str = parts[0].replace('- Item', '').strip()
                    item_text = parts[1].strip()
                    try:
                        item_id = int(item_id_str)
                        items.append({
                            "item_id": item_id,
                            "dimension": current_dimension or "Unknown",
                            "item_text": item_text
                        })
                    except ValueError:
                        continue
    
    return items


def calculate_factor_balance_metrics(factor_distribution: Dict[str, int]) -> Dict[str, Any]:
    """Calculate balance metrics from factor distribution."""
    if not factor_distribution:
        return {
            "imbalance_ratio": float('inf'),
            "max_items": 0,
            "min_items": 0,
            "balance_score": 0.0
        }
    
    counts = list(factor_distribution.values())
    max_items = max(counts)
    min_items = min(counts)
    imbalance_ratio = max_items / min_items if min_items > 0 else float('inf')
    
    # Balance score: 1.0 = perfectly balanced, 0.0 = completely imbalanced
    # Using coefficient of variation (CV) as balance metric
    if len(counts) > 1:
        mean_count = sum(counts) / len(counts)
        std_count = (sum((c - mean_count) ** 2 for c in counts) / len(counts)) ** 0.5
        cv = std_count / mean_count if mean_count > 0 else 1.0
        balance_score = max(0.0, 1.0 - cv)  # Lower CV = better balance
    else:
        balance_score = 1.0
    
    return {
        "imbalance_ratio": imbalance_ratio,
        "max_items": max_items,
        "min_items": min_items,
        "balance_score": balance_score,
        "factor_counts": factor_distribution
    }


def compare_results(historical: Dict[str, Any], new_result: Dict[str, Any]) -> Dict[str, Any]:
    """Compare historical and new selection results."""
    comparison = {
        "item_count": {
            "historical": historical.get("n_selected_items", 0),
            "new": len(new_result.get("selected_item_ids", [])),
            "improvement": None
        },
        "factor_balance": {
            "historical": calculate_factor_balance_metrics(historical.get("factor_distribution", {})),
            "new": calculate_factor_balance_metrics(new_result.get("factor_distribution", {})),
            "improvement": None
        },
        "target_range": {
            "target_min": historical.get("target_range", [10, 18])[0],
            "target_max": historical.get("target_range", [10, 18])[1],
            "historical_in_range": None,
            "new_in_range": None
        }
    }
    
    # Calculate improvements
    target_min = comparison["target_range"]["target_min"]
    target_max = comparison["target_range"]["target_max"]
    
    hist_count = comparison["item_count"]["historical"]
    new_count = comparison["item_count"]["new"]
    
    comparison["target_range"]["historical_in_range"] = target_min <= hist_count <= target_max
    comparison["target_range"]["new_in_range"] = target_min <= new_count <= target_max
    
    # Item count improvement
    if not comparison["target_range"]["historical_in_range"] and comparison["target_range"]["new_in_range"]:
        comparison["item_count"]["improvement"] = "IMPROVED: Now within target range"
    elif comparison["target_range"]["historical_in_range"] and not comparison["target_range"]["new_in_range"]:
        comparison["item_count"]["improvement"] = "REGRESSED: No longer in target range"
    elif abs(new_count - (target_min + target_max) / 2) < abs(hist_count - (target_min + target_max) / 2):
        comparison["item_count"]["improvement"] = "IMPROVED: Closer to target center"
    elif new_count == hist_count:
        comparison["item_count"]["improvement"] = "UNCHANGED"
    else:
        comparison["item_count"]["improvement"] = "NEEDS_REVIEW"
    
    # Factor balance improvement
    hist_ratio = comparison["factor_balance"]["historical"]["imbalance_ratio"]
    new_ratio = comparison["factor_balance"]["new"]["imbalance_ratio"]
    hist_score = comparison["factor_balance"]["historical"]["balance_score"]
    new_score = comparison["factor_balance"]["new"]["balance_score"]
    
    if new_ratio < hist_ratio and new_score > hist_score:
        comparison["factor_balance"]["improvement"] = "IMPROVED: Better balance"
    elif new_ratio == hist_ratio and new_score == hist_score:
        comparison["factor_balance"]["improvement"] = "UNCHANGED"
    elif new_ratio > hist_ratio or new_score < hist_score:
        comparison["factor_balance"]["improvement"] = "REGRESSED: Worse balance"
    else:
        comparison["factor_balance"]["improvement"] = "MIXED"
    
    return comparison


def print_comparison(comparison: Dict[str, Any]):
    """Print comparison results in a readable format."""
    print_section("Comparison Results")
    
    # Item count comparison
    print("Item Count:")
    print(f"  Historical: {comparison['item_count']['historical']} items")
    print(f"  New:        {comparison['item_count']['new']} items")
    print(f"  Target:     {comparison['target_range']['target_min']}-{comparison['target_range']['target_max']} items")
    print(f"  Status:     {comparison['item_count']['improvement']}")
    print()
    
    # Factor balance comparison
    print("Factor Balance:")
    hist_bal = comparison['factor_balance']['historical']
    new_bal = comparison['factor_balance']['new']
    
    print(f"  Historical:")
    print(f"    Imbalance Ratio: {hist_bal['imbalance_ratio']:.2f}")
    print(f"    Balance Score:   {hist_bal['balance_score']:.3f}")
    print(f"    Distribution:    {hist_bal['factor_counts']}")
    print()
    
    print(f"  New:")
    print(f"    Imbalance Ratio: {new_bal['imbalance_ratio']:.2f}")
    print(f"    Balance Score:   {new_bal['balance_score']:.3f}")
    print(f"    Distribution:    {new_bal['factor_counts']}")
    print()
    
    print(f"  Status: {comparison['factor_balance']['improvement']}")
    print()
    
    # Overall assessment
    print("Overall Assessment:")
    improvements = []
    regressions = []
    
    if "IMPROVED" in comparison['item_count']['improvement']:
        improvements.append("Item count control")
    elif "REGRESSED" in comparison['item_count']['improvement']:
        regressions.append("Item count control")
    
    if "IMPROVED" in comparison['factor_balance']['improvement']:
        improvements.append("Factor balance")
    elif "REGRESSED" in comparison['factor_balance']['improvement']:
        regressions.append("Factor balance")
    
    if improvements:
        print_success(f"Improvements: {', '.join(improvements)}")
    if regressions:
        print_warning(f"Regressions: {', '.join(regressions)}")
    if not improvements and not regressions:
        print_info("No significant changes")


def test_with_historical_data(run_id: str, dm: DataManager, prompts: PromptManager):
    """Test improved selection logic with historical data."""
    print_header(f"Testing Factor Balance with Historical Data: {run_id}")
    
    # Load historical result
    print_section("Loading Historical Data")
    historical_result = load_historical_selection_result(run_id, dm)
    if not historical_result:
        print_error(f"Could not load historical selection result for {run_id}")
        return False
    
    print_success(f"Loaded historical selection result")
    print_info(f"Historical: {historical_result.get('n_selected_items', 0)} items")
    print_info(f"Factor distribution: {historical_result.get('factor_distribution', {})}")
    
    # Load items and evaluation data
    print_section("Loading Items and Evaluation Data")
    try:
        items = load_items(run_id, dm)
        print_success(f"Loaded {len(items)} items from scale draft")
    except Exception as e:
        print_error(f"Could not load items: {e}")
        return False
    
    run_path = dm.get_run_path(run_id)
    eval_summary_path = run_path / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
    
    if not eval_summary_path.exists():
        print_error(f"Evaluation summary not found: {eval_summary_path}")
        return False
    
    try:
        with open(eval_summary_path, 'r', encoding='utf-8') as f:
            evaluation_summary = json.load(f)
        print_success("Loaded evaluation summary")
    except Exception as e:
        print_error(f"Could not load evaluation summary: {e}")
        return False
    
    # Re-run selection with improved logic
    print_section("Re-running Selection with Improved Logic")
    
    selection_agent = ItemSelectionAgent(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Use same configuration as historical run
    target_min = historical_result.get("target_range", [10, 18])[0]
    target_max = historical_result.get("target_range", [10, 18])[1]
    
    selection_config = {
        "min_item_total_corr": historical_result.get("min_item_total_corr", 0.5),
        "max_skewness": historical_result.get("max_skewness", 1.0),
        "max_kurtosis": historical_result.get("max_kurtosis", 2.0),
        "max_inter_corr": historical_result.get("max_inter_corr", 0.8),
        "min_factor_loading": historical_result.get("min_factor_loading", 0.75),
        "n_factors": historical_result.get("n_factors"),
        "use_cfa": historical_result.get("use_cfa", True),
        "cfa_rmsea_threshold": historical_result.get("cfa_rmsea_threshold", 0.08),
        "cfa_tli_threshold": historical_result.get("cfa_tli_threshold", 0.95),
        "cfa_cfi_threshold": historical_result.get("cfa_cfi_threshold", 0.95),
        "cfa_srmr_threshold": historical_result.get("cfa_srmr_threshold", 0.08),
        "min_items_per_factor": historical_result.get("min_items_per_factor", 2),
        "enable_factor_balance": True,  # Ensure factor balance is enabled
        "try_multiple_n_factors": True,
        "prefer_balanced_factors": True
    }
    
    try:
        new_result = selection_agent.select_items(
            items=items,
            evaluation_summary=evaluation_summary,
            target_min=target_min,
            target_max=target_max,
            selection_config=selection_config,
            evaluation_summary_path=eval_summary_path
        )
        print_success("Selection completed successfully")
    except Exception as e:
        print_error(f"Selection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Extract factor distribution from new result
    factor_structure = new_result.get("efa_cfa_results", {}).get("factor_structure", {})
    factor_distribution = {}
    for item_id in new_result.get("selected_item_ids", []):
        # factor_structure keys may be strings (from JSON serialization) or integers
        # Try both string and integer keys
        factor_idx = factor_structure.get(str(item_id)) or factor_structure.get(item_id, 0)
        factor_name = f"Factor{factor_idx + 1}"
        factor_distribution[factor_name] = factor_distribution.get(factor_name, 0) + 1
    
    new_result["factor_distribution"] = factor_distribution
    
    # Compare results
    print_section("Comparing Results")
    comparison = compare_results(historical_result, new_result)
    print_comparison(comparison)
    
    # Save comparison results
    output_dir = Path("data") / "test_runs" / f"factor_balance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    comparison_output = {
        "run_id": run_id,
        "test_timestamp": datetime.now().isoformat(),
        "historical_result": historical_result,
        "new_result": {
            "selected_item_ids": new_result.get("selected_item_ids", []),
            "n_selected_items": len(new_result.get("selected_item_ids", [])),
            "factor_distribution": factor_distribution,
            "selection_statistics": new_result.get("selection_statistics", {})
        },
        "comparison": comparison
    }
    
    output_path = output_dir / "comparison_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_output, f, indent=2, ensure_ascii=False)
    
    print_success(f"Comparison results saved to: {output_path}")
    
    return True


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test factor balance with historical data")
    parser.add_argument("run_id", nargs="?", help="Run ID to test (default: most recent complete run)")
    args = parser.parse_args()
    
    # Initialize data manager and prompts
    dm = DataManager()
    prompts = PromptManager()
    
    # Find run to test
    if args.run_id:
        run_id = args.run_id
    else:
        print_info("Finding most recent complete run...")
        complete_runs = find_complete_runs(dm.data_dir / "runs")
        if not complete_runs:
            print_error("No complete runs found with Phase 1 evaluation data")
            return 1
        
        run_id = complete_runs[0]
        print_info(f"Using run: {run_id}")
    
    # Run test
    success = test_with_historical_data(run_id, dm, prompts)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
