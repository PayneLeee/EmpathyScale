"""
Check progress of running experiments.

Usage:
    python tools/check_progress.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_run_progress(run_id: str):
    """Check progress of a specific run."""
    run_path = project_root / "data" / "runs" / run_id
    
    if not run_path.exists():
        return None
    
    progress = {
        "run_id": run_id,
        "exists": True,
        "stages": {}
    }
    
    # Check generation stage
    scale_draft = run_path / "empathy_scale_generation_agent_group" / "scale_draft.md"
    if scale_draft.exists():
        progress["stages"]["generation"] = {
            "completed": True,
            "items": None
        }
        # Try to count items
        try:
            from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
            items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(
                scale_draft.read_text(encoding="utf-8", errors="replace")
            )
            progress["stages"]["generation"]["items"] = len(items) if items else 0
        except:
            pass
    
    # Check Phase 1 evaluation
    phase1_combined = run_path / "evaluation_agent_group" / "selection" / "combined" / "evaluation_summary.json"
    phase1_old = run_path / "evaluation_agent_group" / "evaluation_summary.json"
    
    if phase1_combined.exists():
        progress["stages"]["phase1"] = {"completed": True, "location": "combined"}
        try:
            summary = json.loads(phase1_combined.read_text(encoding="utf-8"))
            progress["stages"]["phase1"]["participants"] = summary.get("n_participants", 0)
            progress["stages"]["phase1"]["items"] = summary.get("n_items", 0)
        except:
            pass
    elif phase1_old.exists():
        progress["stages"]["phase1"] = {"completed": True, "location": "old"}
    
    # Check statistical selection
    selection_stats = run_path / "statistical_selection" / "selection_statistics.json"
    if selection_stats.exists():
        progress["stages"]["selection"] = {"completed": True}
        try:
            stats = json.loads(selection_stats.read_text(encoding="utf-8"))
            progress["stages"]["selection"]["selected_items"] = stats.get("n_selected_items", 0)
            progress["stages"]["selection"]["original_items"] = stats.get("n_original_items", 0)
        except:
            pass
    
    # Check Phase 2 validation
    phase2_summary = run_path / "evaluation_agent_group" / "validation" / "evaluation_summary.json"
    if phase2_summary.exists():
        progress["stages"]["phase2"] = {"completed": True}
        try:
            summary = json.loads(phase2_summary.read_text(encoding="utf-8"))
            progress["stages"]["phase2"]["participants"] = summary.get("n_participants", 0)
            progress["stages"]["phase2"]["items"] = summary.get("n_items", 0)
        except:
            pass
    
    return progress


def main():
    """Main function."""
    print("=" * 80)
    print("EXPERIMENT PROGRESS CHECKER".center(80))
    print("=" * 80)
    print()
    
    runs_dir = project_root / "data" / "runs"
    
    if not runs_dir.exists():
        print("No runs directory found.")
        return
    
    # Get all run directories
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    
    if not runs:
        print("No runs found.")
        return
    
    print(f"Found {len(runs)} run(s). Showing latest 10:")
    print()
    
    for run in runs[:10]:
        progress = check_run_progress(run.name)
        
        if progress:
            print(f"Run ID: {run.name}")
            print(f"  Path: {run}")
            
            stages = progress.get("stages", {})
            
            if "generation" in stages:
                gen = stages["generation"]
                items = gen.get("items", "?")
                print(f"  ✓ Generation: {items} items")
            else:
                print(f"  ✗ Generation: Not started")
            
            if "phase1" in stages:
                p1 = stages["phase1"]
                parts = p1.get("participants", "?")
                items = p1.get("items", "?")
                print(f"  ✓ Phase 1: {parts} participants, {items} items")
            else:
                print(f"  ✗ Phase 1: Not started")
            
            if "selection" in stages:
                sel = stages["selection"]
                selected = sel.get("selected_items", "?")
                original = sel.get("original_items", "?")
                print(f"  ✓ Selection: {selected}/{original} items")
            else:
                print(f"  ✗ Selection: Not started")
            
            if "phase2" in stages:
                p2 = stages["phase2"]
                parts = p2.get("participants", "?")
                items = p2.get("items", "?")
                print(f"  ✓ Phase 2: {parts} participants, {items} items")
            else:
                print(f"  ✗ Phase 2: Not started")
            
            print()
        else:
            print(f"Run ID: {run.name} (empty or invalid)")
            print()


if __name__ == "__main__":
    main()


