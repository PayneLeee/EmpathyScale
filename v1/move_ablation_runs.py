"""
Move past ablation experiment runs to past_runs folder and prepare for new ablation study.
"""
import json
import shutil
from pathlib import Path

def main():
    # Load ablation summary to get run IDs
    summary_path = Path("data/ablation_studies/collab_robot_assembly/ablation_summary.json")
    if not summary_path.exists():
        print(f"Error: Ablation summary not found at {summary_path}")
        return
    
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    
    # Extract run IDs from variants
    run_ids = []
    for variant_name, variant_data in summary.get("variants", {}).items():
        if "run_id" in variant_data:
            run_ids.append(variant_data["run_id"])
    
    print(f"Found {len(run_ids)} ablation experiment runs:")
    for run_id in run_ids:
        print(f"  - {run_id}")
    
    # Create past_runs directory
    past_runs_dir = Path("data/past_runs")
    past_runs_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nCreated/verified past_runs directory: {past_runs_dir}")
    
    # Move runs
    runs_dir = Path("data/runs")
    moved = []
    failed = []
    
    for run_id in run_ids:
        src = runs_dir / run_id
        if src.exists():
            dst = past_runs_dir / run_id
            try:
                if dst.exists():
                    print(f"  Removing existing {dst}...")
                    shutil.rmtree(dst)
                shutil.move(str(src), str(dst))
                moved.append(run_id)
                print(f"  [OK] Moved {run_id}")
            except Exception as e:
                failed.append((run_id, str(e)))
                print(f"  [ERROR] Failed to move {run_id}: {e}")
        else:
            print(f"  [WARN] Run {run_id} not found in {runs_dir}")
    
    print(f"\nSummary:")
    print(f"  Successfully moved: {len(moved)} runs")
    if failed:
        print(f"  Failed: {len(failed)} runs")
        for run_id, error in failed:
            print(f"    - {run_id}: {error}")
    
    if moved:
        print(f"\nAll ablation runs have been moved to {past_runs_dir}")
        print("You can now run the new ablation study with: python run_ablation_minimal.py")

if __name__ == "__main__":
    main()

