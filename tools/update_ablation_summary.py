"""
Update ablation summary with new multi_no_content result.

Usage:
    python tools/update_ablation_summary.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.data_manager import DataManager


def update_ablation_summary():
    """Update ablation summary with new multi_no_content result."""
    scenario_id = "collab_robot_assembly"
    summary_path = project_root / f"data/ablation_studies/{scenario_id}/ablation_summary.json"
    
    if not summary_path.exists():
        print("Ablation summary not found. Please run full ablation study first.")
        return
    
    dm = DataManager()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    
    # Update multi_no_content variant with new run
    new_run_id = "2025-12-17_152040"
    run_path = dm.get_run_path(new_run_id)
    
    # Load evaluation summary
    eval_summary_path = run_path / "evaluation_agent_group" / "evaluation_summary.json"
    if eval_summary_path.exists():
        eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
        
        # Update variant data
        summary["variants"]["multi_no_content"] = {
            "scenario": scenario_id,
            "num_generators": 3,
            "enable_content": False,
            "n_items": eval_summary.get("n_items", 0),
            "run_id": new_run_id,
            "evaluation": {
                "overall_mean_rating": eval_summary.get("overall_mean_rating"),
                "n_participants": eval_summary.get("n_participants"),
                "rating_std": eval_summary.get("overall_rating_std"),
            }
        }
        
        # Update comparison metrics
        ratings = {
            name: data.get("evaluation", {}).get("overall_mean_rating")
            for name, data in summary["variants"].items()
            if data.get("evaluation", {}).get("overall_mean_rating") is not None
        }
        if ratings:
            summary["comparison"]["ratings"] = ratings
            best_rating = max(ratings.items(), key=lambda x: x[1] if x[1] is not None else 0)
            summary["comparison"]["best_rating"] = {
                "variant": best_rating[0],
                "rating": best_rating[1]
            }
        
        # Update item counts
        summary["comparison"]["item_counts"]["multi_no_content"] = eval_summary.get("n_items", 0)
        
        # Save updated summary
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"Updated ablation summary: {summary_path}")
        print(f"multi_no_content: {eval_summary.get('n_items', 0)} items, rating: {eval_summary.get('overall_mean_rating', 'N/A')}")
    else:
        print(f"Evaluation summary not found for run {new_run_id}")


if __name__ == "__main__":
    update_ablation_summary()


