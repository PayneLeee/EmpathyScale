"""
Comprehensive Analysis Script

Analyzes ablation study results and cross-scenario results,
generating a comprehensive comparison report.

Usage:
    python tools/analyze_all_results.py
"""

from pathlib import Path
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Ensure local imports work when run as script
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "agents"))
sys.path.append(str(project_root / "utils"))

from utils.data_manager import DataManager


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text:^{width}}")
    print(f"{char * width}\n")


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


def load_ablation_summary(scenario_id: str = "collab_robot_assembly") -> Optional[Dict[str, Any]]:
    """Load ablation study summary."""
    project_root = Path(__file__).parent.parent
    ablation_path = project_root / f"data/ablation_studies/{scenario_id}/ablation_summary.json"
    if not ablation_path.exists():
        print_warning(f"Ablation summary not found: {ablation_path}")
        return None
    
    try:
        summary = json.loads(ablation_path.read_text(encoding="utf-8"))
        print_success(f"Loaded ablation summary for {scenario_id}")
        return summary
    except Exception as e:
        print_error(f"Failed to load ablation summary: {e}")
        return None


def load_evaluation_summary(run_id: str, dm: DataManager) -> Optional[Dict[str, Any]]:
    """Load evaluation summary for a run."""
    run_path = dm.get_run_path(run_id)
    eval_summary_path = run_path / "evaluation_agent_group" / "evaluation_summary.json"
    if not eval_summary_path.exists():
        return None
    
    try:
        return json.loads(eval_summary_path.read_text(encoding="utf-8"))
    except Exception as e:
        print_warning(f"Failed to load evaluation summary for {run_id}: {e}")
        return None


def load_scale_summary(run_id: str, dm: DataManager) -> Optional[Dict[str, Any]]:
    """Load scale generation summary for a run."""
    run_path = dm.get_run_path(run_id)
    scale_summary_path = run_path / "empathy_scale_generation_agent_group" / "summary.json"
    if not scale_summary_path.exists():
        return None
    
    try:
        return json.loads(scale_summary_path.read_text(encoding="utf-8"))
    except Exception as e:
        print_warning(f"Failed to load scale summary for {run_id}: {e}")
        return None


def analyze_ablation_results(ablation_summary: Dict[str, Any], dm: DataManager) -> Dict[str, Any]:
    """Analyze ablation study results."""
    print_info("Analyzing ablation study results...")
    
    analysis = {
        "scenario": ablation_summary.get("scenario", "unknown"),
        "variants": {},
        "comparison": {}
    }
    
    variants = ablation_summary.get("variants", {})
    for variant_name, variant_data in variants.items():
        run_id = variant_data.get("run_id")
        if not run_id:
            continue
        
        eval_summary = load_evaluation_summary(run_id, dm)
        scale_summary = load_scale_summary(run_id, dm)
        
        analysis["variants"][variant_name] = {
            "num_generators": variant_data.get("num_generators"),
            "enable_content": variant_data.get("enable_content"),
            "n_items": variant_data.get("n_items", 0),
            "overall_mean_rating": eval_summary.get("overall_mean_rating") if eval_summary else None,
            "rating_std": eval_summary.get("overall_rating_std") if eval_summary else None,
            "n_participants": eval_summary.get("n_participants") if eval_summary else None,
        }
        
        # Calculate high/low rating item counts
        if eval_summary:
            item_stats = eval_summary.get("item_statistics", [])
            high_rating_count = sum(1 for item in item_stats 
                                  if item.get("rating_statistics", {}).get("mean", 0) > 70)
            low_rating_count = sum(1 for item in item_stats 
                                  if item.get("rating_statistics", {}).get("mean", 0) < 50)
            analysis["variants"][variant_name]["high_rating_items"] = high_rating_count
            analysis["variants"][variant_name]["low_rating_items"] = low_rating_count
    
    # Generate comparison metrics
    if len(analysis["variants"]) >= 2:
        ratings = {
            name: data.get("overall_mean_rating")
            for name, data in analysis["variants"].items()
            if data.get("overall_mean_rating") is not None
        }
        if ratings:
            best_variant = max(ratings.items(), key=lambda x: x[1] if x[1] is not None else 0)
            worst_variant = min(ratings.items(), key=lambda x: x[1] if x[1] is not None else float('inf'))
            analysis["comparison"]["best_variant"] = {
                "name": best_variant[0],
                "rating": best_variant[1]
            }
            analysis["comparison"]["worst_variant"] = {
                "name": worst_variant[0],
                "rating": worst_variant[1]
            }
    
    return analysis


def analyze_cross_scenario_results(dm: DataManager) -> Dict[str, Any]:
    """Analyze cross-scenario results from data/runs/."""
    print_info("Analyzing cross-scenario results...")
    
    project_root = Path(__file__).parent.parent
    runs_dir = project_root / "data/runs"
    if not runs_dir.exists():
        print_warning("Runs directory not found")
        return {}
    
    scenario_results = {}
    
    # Scan runs directory for recent runs
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    
    # Look for runs from cross-scenario analysis (home_service_robot, counseling_chatbot)
    target_scenarios = ["home_service_robot", "counseling_chatbot"]
    
    for run_dir in run_dirs:
        interview_summary_path = run_dir / "interview_agent_group" / "summary.json"
        if not interview_summary_path.exists():
            continue
        
        try:
            interview_summary = json.loads(interview_summary_path.read_text(encoding="utf-8"))
            scenario_name = interview_summary.get("name")
            
            if scenario_name in target_scenarios and scenario_name not in scenario_results:
                eval_summary = load_evaluation_summary(run_dir.name, dm)
                scale_summary = load_scale_summary(run_dir.name, dm)
                
                # Parse items to count
                scale_draft_path = run_dir / "empathy_scale_generation_agent_group" / "scale_draft.md"
                n_items = 0
                if scale_draft_path.exists():
                    from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
                    md_text = scale_draft_path.read_text(encoding="utf-8", errors="replace")
                    items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
                    n_items = len(items) if items else 0
                
                scenario_results[scenario_name] = {
                    "run_id": run_dir.name,
                    "n_items": n_items,
                    "overall_mean_rating": eval_summary.get("overall_mean_rating") if eval_summary else None,
                    "rating_std": eval_summary.get("overall_rating_std") if eval_summary else None,
                    "n_participants": eval_summary.get("n_participants") if eval_summary else None,
                }
                
                # Extract dimensions if available
                if scale_summary:
                    dimensions = scale_summary.get("dimensions", [])
                    scenario_results[scenario_name]["n_dimensions"] = len(dimensions)
                    scenario_results[scenario_name]["dimensions"] = [
                        dim.get("name", "Unknown") for dim in dimensions
                    ]
        except Exception as e:
            print_warning(f"Failed to process run {run_dir.name}: {e}")
            continue
    
    return scenario_results


def generate_comprehensive_report(
    ablation_analysis: Dict[str, Any],
    cross_scenario_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate comprehensive comparison report."""
    report = {
        "report_type": "comprehensive_analysis",
        "generated_at": datetime.now().isoformat(),
        "ablation_study": ablation_analysis,
        "cross_scenario_analysis": cross_scenario_analysis,
        "key_findings": []
    }
    
    # Extract key findings
    if ablation_analysis.get("comparison"):
        best_variant = ablation_analysis["comparison"].get("best_variant")
        if best_variant:
            report["key_findings"].append(
                f"Best ablation variant: {best_variant['name']} "
                f"(mean rating: {best_variant['rating']:.2f})"
            )
    
    if cross_scenario_analysis:
        for scenario_name, scenario_data in cross_scenario_analysis.items():
            rating = scenario_data.get("overall_mean_rating")
            if rating:
                report["key_findings"].append(
                    f"{scenario_name}: {scenario_data.get('n_items', 0)} items, "
                    f"mean rating: {rating:.2f}"
                )
    
    return report


def generate_markdown_report(report: Dict[str, Any], output_path: Path):
    """Generate human-readable Markdown report."""
    lines = [
        "# Comprehensive Analysis Report",
        "",
        f"**Generated at:** {report['generated_at']}",
        "",
        "## Ablation Study Results",
        ""
    ]
    
    ablation = report.get("ablation_study", {})
    variants = ablation.get("variants", {})
    
    if variants:
        lines.append("### Variant Comparison")
        lines.append("")
        lines.append("| Variant | Generators | Content Assessment | Items | Mean Rating | Std |")
        lines.append("|---------|------------|-------------------|-------|-------------|-----|")
        
        for variant_name, variant_data in variants.items():
            num_gen = variant_data.get("num_generators", "N/A")
            enable_content = "Yes" if variant_data.get("enable_content") else "No"
            n_items = variant_data.get("n_items", 0)
            rating = variant_data.get("overall_mean_rating")
            rating_str = f"{rating:.2f}" if rating is not None else "N/A"
            std = variant_data.get("rating_std")
            std_str = f"{std:.2f}" if std is not None else "N/A"
            
            lines.append(f"| {variant_name} | {num_gen} | {enable_content} | {n_items} | {rating_str} | {std_str} |")
        
        lines.append("")
        
        comparison = ablation.get("comparison", {})
        if comparison.get("best_variant"):
            best = comparison["best_variant"]
            lines.append(f"**Best variant:** {best['name']} (rating: {best['rating']:.2f})")
            lines.append("")
    
    lines.append("## Cross-Scenario Analysis")
    lines.append("")
    
    cross_scenario = report.get("cross_scenario_analysis", {})
    if cross_scenario:
        lines.append("### Scenario Comparison")
        lines.append("")
        lines.append("| Scenario | Items | Dimensions | Mean Rating | Std |")
        lines.append("|----------|-------|------------|-------------|-----|")
        
        for scenario_name, scenario_data in cross_scenario.items():
            n_items = scenario_data.get("n_items", 0)
            n_dims = scenario_data.get("n_dimensions", "N/A")
            rating = scenario_data.get("overall_mean_rating")
            rating_str = f"{rating:.2f}" if rating is not None else "N/A"
            std = scenario_data.get("rating_std")
            std_str = f"{std:.2f}" if std is not None else "N/A"
            
            lines.append(f"| {scenario_name} | {n_items} | {n_dims} | {rating_str} | {std_str} |")
        lines.append("")
    else:
        lines.append("No cross-scenario results found.")
        lines.append("")
    
    lines.append("## Key Findings")
    lines.append("")
    findings = report.get("key_findings", [])
    if findings:
        for finding in findings:
            lines.append(f"- {finding}")
    else:
        lines.append("No key findings available.")
    
    lines.append("")
    
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print_success(f"Markdown report saved: {output_path}")


def main():
    print_header("COMPREHENSIVE ANALYSIS", "=")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    dm = DataManager()
    
    # Step 1: Load and analyze ablation results
    print_header("Step 1: Analyzing Ablation Study", "-")
    ablation_summary = load_ablation_summary("collab_robot_assembly")
    ablation_analysis = {}
    if ablation_summary:
        ablation_analysis = analyze_ablation_results(ablation_summary, dm)
        print_success("Ablation analysis completed")
    else:
        print_warning("Skipping ablation analysis (summary not found)")
    print()
    
    # Step 2: Analyze cross-scenario results
    print_header("Step 2: Analyzing Cross-Scenario Results", "-")
    cross_scenario_analysis = analyze_cross_scenario_results(dm)
    if cross_scenario_analysis:
        print_success(f"Found {len(cross_scenario_analysis)} cross-scenario results")
    else:
        print_warning("No cross-scenario results found")
    print()
    
    # Step 3: Generate comprehensive report
    print_header("Step 3: Generating Comprehensive Report", "-")
    report = generate_comprehensive_report(ablation_analysis, cross_scenario_analysis)
    
    # Save JSON report
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "data/analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / "comprehensive_report.json"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print_success(f"JSON report saved: {json_path}")
    
    # Generate Markdown report
    md_path = output_dir / "comprehensive_report.md"
    generate_markdown_report(report, md_path)
    
    # Final summary
    print_header("ANALYSIS COMPLETED", "=")
    print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_success("Comprehensive analysis report generated")
    print()
    print_info(f"Reports saved to: {output_dir}")
    print()


if __name__ == "__main__":
    main()


