"""
Statistical Selection Comparison Analyzer

Compares original evaluation results with filtered evaluation results.
Generates comparison reports in JSON and Markdown formats.

Usage:
    python tools/analyze_statistical_selection.py --original-run-id <id> --filtered-run-id <id>
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "agents"))
sys.path.append(str(project_root / "utils"))

from utils.data_manager import DataManager
from utils.statistical_item_selection import get_selection_statistics


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


def print_error(message: str):
    """Print an error message."""
    print(f"[ERROR] {message}")


def compare_selection_results(
    original_run_id: str,
    filtered_run_id: str,
    dm: DataManager
) -> Dict[str, Any]:
    """
    Compare original evaluation with filtered evaluation results.
    
    Args:
        original_run_id: Original run ID
        filtered_run_id: Filtered run ID
        dm: DataManager instance
    
    Returns:
        Dictionary with comparison metrics
    """
    original_path = dm.get_run_path(original_run_id)
    filtered_path = dm.get_run_path(filtered_run_id)
    
    # Load evaluation summaries
    original_eval_path = original_path / "evaluation_agent_group" / "evaluation_summary.json"
    filtered_eval_path = filtered_path / "evaluation_agent_group" / "evaluation_summary.json"
    
    if not original_eval_path.exists():
        print_error(f"Original evaluation summary not found: {original_eval_path}")
        return None
    
    if not filtered_eval_path.exists():
        print_error(f"Filtered evaluation summary not found: {filtered_eval_path}")
        return None
    
    original_eval = json.loads(original_eval_path.read_text(encoding="utf-8"))
    filtered_eval = json.loads(filtered_eval_path.read_text(encoding="utf-8"))
    
    # Load selection metadata if available
    metadata_path = filtered_path / "statistical_selection_metadata.json"
    selection_metadata = None
    if metadata_path.exists():
        selection_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    
    # Calculate comparison metrics
    comparison = {
        "original_run_id": original_run_id,
        "filtered_run_id": filtered_run_id,
        "comparison_date": datetime.now().isoformat(),
        "item_counts": {
            "original": original_eval.get("n_items", 0),
            "filtered": filtered_eval.get("n_items", 0),
            "reduction": original_eval.get("n_items", 0) - filtered_eval.get("n_items", 0),
            "reduction_percentage": (
                (original_eval.get("n_items", 0) - filtered_eval.get("n_items", 0)) 
                / original_eval.get("n_items", 1) * 100
            ) if original_eval.get("n_items", 0) > 0 else 0.0
        },
        "rating_statistics": {
            "original": {
                "mean": original_eval.get("overall_mean_rating"),
                "n_participants": original_eval.get("n_participants")
            },
            "filtered": {
                "mean": filtered_eval.get("overall_mean_rating"),
                "n_participants": filtered_eval.get("n_participants")
            },
            "change": {
                "mean_difference": (
                    filtered_eval.get("overall_mean_rating", 0) - 
                    original_eval.get("overall_mean_rating", 0)
                ) if original_eval.get("overall_mean_rating") and filtered_eval.get("overall_mean_rating") else None,
                "mean_change_percentage": (
                    ((filtered_eval.get("overall_mean_rating", 0) - original_eval.get("overall_mean_rating", 0)) 
                     / original_eval.get("overall_mean_rating", 1) * 100)
                    if original_eval.get("overall_mean_rating") and original_eval.get("overall_mean_rating") > 0 else None
                )
            }
        },
        "item_quality": {
            "original_low_rating_items": len(original_eval.get("low_rating_items", [])),
            "filtered_low_rating_items": len(filtered_eval.get("low_rating_items", [])),
            "original_high_variance_items": len(original_eval.get("high_variance_items", [])),
            "filtered_high_variance_items": len(filtered_eval.get("high_variance_items", []))
        },
        "dimension_distribution": {}
    }
    
    # Analyze dimension distribution
    original_dims = {}
    filtered_dims = {}
    
    for item_stat in original_eval.get("item_statistics", []):
        dim = item_stat.get("dimension", "Unknown")
        original_dims[dim] = original_dims.get(dim, 0) + 1
    
    for item_stat in filtered_eval.get("item_statistics", []):
        dim = item_stat.get("dimension", "Unknown")
        filtered_dims[dim] = filtered_dims.get(dim, 0) + 1
    
    all_dims = set(list(original_dims.keys()) + list(filtered_dims.keys()))
    for dim in all_dims:
        comparison["dimension_distribution"][dim] = {
            "original": original_dims.get(dim, 0),
            "filtered": filtered_dims.get(dim, 0),
            "change": filtered_dims.get(dim, 0) - original_dims.get(dim, 0)
        }
    
    # Add selection metadata if available
    if selection_metadata:
        comparison["selection_metadata"] = {
            "strategy": selection_metadata.get("selection_strategy"),
            "strategy_params": selection_metadata.get("strategy_params"),
            "selected_item_ids": selection_metadata.get("selected_item_ids"),
            "selection_statistics": selection_metadata.get("selection_statistics")
        }
    
    return comparison


def generate_selection_report(
    comparison_results: Dict[str, Any],
    output_dir: Path
):
    """
    Generate comparison report in JSON and Markdown formats.
    
    Args:
        comparison_results: Comparison results dictionary
        output_dir: Output directory for reports
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    original_run_id = comparison_results.get("original_run_id", "unknown")
    
    # Save JSON report
    json_path = output_dir / f"{original_run_id}_comparison.json"
    json_path.write_text(
        json.dumps(comparison_results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print_success(f"Saved JSON report: {json_path}")
    
    # Generate Markdown report
    md_lines = [
        "# Statistical Selection Comparison Report",
        "",
        f"**Generated:** {comparison_results.get('comparison_date', 'N/A')}",
        "",
        "## Overview",
        "",
        f"- **Original Run ID:** `{comparison_results.get('original_run_id')}`",
        f"- **Filtered Run ID:** `{comparison_results.get('filtered_run_id')}`",
        ""
    ]
    
    # Selection metadata
    if "selection_metadata" in comparison_results:
        metadata = comparison_results["selection_metadata"]
        md_lines.extend([
            "## Selection Configuration",
            "",
            f"- **Strategy:** {metadata.get('strategy', 'N/A')}",
            f"- **Parameters:** {json.dumps(metadata.get('strategy_params', {}), ensure_ascii=False)}",
            ""
        ])
    
    # Item counts
    item_counts = comparison_results.get("item_counts", {})
    md_lines.extend([
        "## Item Counts",
        "",
        "| Metric | Original | Filtered | Change |",
        "|--------|----------|----------|--------|",
        f"| Total Items | {item_counts.get('original', 0)} | {item_counts.get('filtered', 0)} | {item_counts.get('reduction', 0)} ({item_counts.get('reduction_percentage', 0):.1f}%) |",
        ""
    ])
    
    # Rating statistics
    rating_stats = comparison_results.get("rating_statistics", {})
    md_lines.extend([
        "## Rating Statistics",
        "",
        "| Metric | Original | Filtered | Change |",
        "|--------|----------|----------|--------|"
    ])
    
    orig_mean = rating_stats.get("original", {}).get("mean")
    filt_mean = rating_stats.get("filtered", {}).get("mean")
    mean_diff = rating_stats.get("change", {}).get("mean_difference")
    mean_change_pct = rating_stats.get("change", {}).get("mean_change_percentage")
    
    md_lines.append(
        f"| Mean Rating | {orig_mean if orig_mean is not None else 'N/A'} | "
        f"{filt_mean if filt_mean is not None else 'N/A'} | "
        f"{mean_diff if mean_diff is not None else 'N/A'} "
        f"({mean_change_pct if mean_change_pct is not None else 'N/A'}%) |"
    )
    
    md_lines.extend([
        "",
        f"| Participants | {rating_stats.get('original', {}).get('n_participants', 'N/A')} | "
        f"{rating_stats.get('filtered', {}).get('n_participants', 'N/A')} | - |",
        ""
    ])
    
    # Item quality
    item_quality = comparison_results.get("item_quality", {})
    md_lines.extend([
        "## Item Quality Indicators",
        "",
        "| Indicator | Original | Filtered |",
        "|-----------|----------|----------|",
        f"| Low Rating Items (<50) | {item_quality.get('original_low_rating_items', 0)} | {item_quality.get('filtered_low_rating_items', 0)} |",
        f"| High Variance Items (std>30) | {item_quality.get('original_high_variance_items', 0)} | {item_quality.get('filtered_high_variance_items', 0)} |",
        ""
    ])
    
    # Dimension distribution
    dim_dist = comparison_results.get("dimension_distribution", {})
    if dim_dist:
        md_lines.extend([
            "## Dimension Distribution",
            "",
            "| Dimension | Original | Filtered | Change |",
            "|-----------|----------|----------|--------|"
        ])
        
        for dim, counts in sorted(dim_dist.items()):
            md_lines.append(
                f"| {dim} | {counts.get('original', 0)} | {counts.get('filtered', 0)} | {counts.get('change', 0)} |"
            )
        md_lines.append("")
    
    # Selection statistics (if available)
    if "selection_metadata" in comparison_results:
        sel_stats = comparison_results["selection_metadata"].get("selection_statistics", {})
        if sel_stats:
            md_lines.extend([
                "## Selection Statistics",
                "",
                f"- **Selection Ratio:** {sel_stats.get('selection_ratio', 0)*100:.1f}%",
                f"- **Original Mean Rating:** {sel_stats.get('original_mean_rating', 'N/A')}",
                f"- **Selected Mean Rating:** {sel_stats.get('selected_mean_rating', 'N/A')}",
                ""
            ])
            
            dim_dist_sel = sel_stats.get("dimension_distribution", {})
            if dim_dist_sel:
                md_lines.append("### Selected Items by Dimension")
                md_lines.append("")
                for dim, count in sorted(dim_dist_sel.items()):
                    md_lines.append(f"- **{dim}:** {count} items")
                md_lines.append("")
    
    md_lines.extend([
        "## Summary",
        "",
        f"Statistical selection reduced the scale from {item_counts.get('original', 0)} to {item_counts.get('filtered', 0)} items "
        f"({item_counts.get('reduction_percentage', 0):.1f}% reduction)."
    ])
    
    if mean_diff is not None:
        if mean_diff > 0:
            md_lines.append(f"The filtered scale shows an improvement in mean rating (+{mean_diff:.2f} points).")
        elif mean_diff < 0:
            md_lines.append(f"The filtered scale shows a decrease in mean rating ({mean_diff:.2f} points).")
        else:
            md_lines.append("The filtered scale maintains the same mean rating.")
    
    md_lines.append("")
    
    # Save Markdown report
    md_path = output_dir / f"{original_run_id}_comparison.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print_success(f"Saved Markdown report: {md_path}")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Compare original and filtered evaluation results"
    )
    parser.add_argument(
        "--original-run-id",
        required=True,
        help="Original run ID"
    )
    parser.add_argument(
        "--filtered-run-id",
        required=True,
        help="Filtered run ID"
    )
    parser.add_argument(
        "--output-dir",
        default="data/analysis/statistical_selection",
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    print_header("STATISTICAL SELECTION COMPARISON", "=")
    
    dm = DataManager()
    
    # Compare results
    comparison = compare_selection_results(
        args.original_run_id,
        args.filtered_run_id,
        dm
    )
    
    if not comparison:
        print_error("Comparison failed")
        sys.exit(1)
    
    # Generate reports
    project_root = Path(__file__).parent.parent
    output_dir = project_root / args.output_dir
    generate_selection_report(comparison, output_dir)
    
    print_header("COMPARISON COMPLETED", "=")
    print_success(f"Reports saved to: {output_dir}")


if __name__ == "__main__":
    main()


