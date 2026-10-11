"""
Diagnostic tool to analyze why EFA+CFA selection filters out too many items.

This script helps identify:
1. Item-total correlation distribution
2. Rating variance across items
3. Persona diversity (rating patterns)
4. Data quality issues
"""

import json
import sys
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.factor_analysis import (
    load_participant_ratings,
    calculate_item_total_correlation,
    calculate_skewness_kurtosis,
    calculate_inter_item_correlations
)


def diagnose_selection_issue(evaluation_summary_path: Path):
    """
    Diagnose why EFA+CFA selection filters out too many items.
    
    Args:
        evaluation_summary_path: Path to evaluation_summary.json
    """
    print("=" * 80)
    print("DIAGNOSING EFA+CFA SELECTION ISSUE")
    print("=" * 80)
    print()
    
    # Load ratings matrix
    ratings_matrix = load_participant_ratings(evaluation_summary_path)
    if ratings_matrix is None:
        print("[ERROR] Could not load participant ratings")
        return
    
    n_participants, n_items = ratings_matrix.shape
    print(f"[INFO] Loaded {n_participants} participants, {n_items} items")
    print()
    
    # 1. Analyze item-total correlations
    print("=" * 80)
    print("1. ITEM-TOTAL CORRELATION ANALYSIS")
    print("=" * 80)
    item_total_corrs = calculate_item_total_correlation(ratings_matrix)
    corr_values = list(item_total_corrs.values())
    
    if corr_values:
        print(f"  Statistics:")
        print(f"    - Mean: {np.mean(corr_values):.3f}")
        print(f"    - Median: {np.median(corr_values):.3f}")
        print(f"    - Std: {np.std(corr_values):.3f}")
        print(f"    - Min: {np.min(corr_values):.3f}")
        print(f"    - Max: {np.max(corr_values):.3f}")
        print(f"    - Items >= 0.5: {sum(1 for c in corr_values if c >= 0.5)}/{len(corr_values)}")
        print(f"    - Items >= 0.3: {sum(1 for c in corr_values if c >= 0.3)}/{len(corr_values)}")
        print(f"    - Items >= 0.1: {sum(1 for c in corr_values if c >= 0.1)}/{len(corr_values)}")
        
        # Show distribution
        bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        hist, _ = np.histogram(corr_values, bins=bins)
        print(f"  Distribution:")
        for i in range(len(bins) - 1):
            print(f"    [{bins[i]:.1f}-{bins[i+1]:.1f}): {hist[i]} items")
    print()
    
    # 2. Analyze rating variance
    print("=" * 80)
    print("2. RATING VARIANCE ANALYSIS")
    print("=" * 80)
    item_means = np.nanmean(ratings_matrix, axis=0)
    item_stds = np.nanstd(ratings_matrix, axis=0)
    
    print(f"  Item mean ratings:")
    print(f"    - Mean: {np.nanmean(item_means):.2f}")
    print(f"    - Std: {np.nanstd(item_means):.2f}")
    print(f"    - Min: {np.nanmin(item_means):.2f}")
    print(f"    - Max: {np.nanmax(item_means):.2f}")
    print()
    print(f"  Item standard deviations:")
    print(f"    - Mean: {np.nanmean(item_stds):.2f}")
    print(f"    - Std: {np.nanstd(item_stds):.2f}")
    print(f"    - Min: {np.nanmin(item_stds):.2f}")
    print(f"    - Max: {np.nanmax(item_stds):.2f}")
    print()
    
    # Count items with low variance (potential issue)
    low_variance_threshold = 10.0  # std < 10
    low_variance_items = sum(1 for std in item_stds if std < low_variance_threshold)
    print(f"  Items with low variance (std < {low_variance_threshold}): {low_variance_items}/{n_items} ({low_variance_items/n_items*100:.1f}%)")
    print()
    
    # 3. Analyze persona diversity
    print("=" * 80)
    print("3. PERSONA DIVERSITY ANALYSIS")
    print("=" * 80)
    
    # Calculate mean rating per persona
    persona_means = np.nanmean(ratings_matrix, axis=1)
    persona_stds = np.nanstd(ratings_matrix, axis=1)
    
    print(f"  Persona mean ratings:")
    print(f"    - Mean: {np.nanmean(persona_means):.2f}")
    print(f"    - Std: {np.nanstd(persona_means):.2f}")
    print(f"    - Min: {np.nanmin(persona_means):.2f}")
    print(f"    - Max: {np.nanmax(persona_means):.2f}")
    print()
    print(f"  Persona rating std (how much each persona varies):")
    print(f"    - Mean: {np.nanmean(persona_stds):.2f}")
    print(f"    - Std: {np.nanstd(persona_stds):.2f}")
    print(f"    - Min: {np.nanmin(persona_stds):.2f}")
    print(f"    - Max: {np.nanmax(persona_stds):.2f}")
    print()
    
    # Check if personas are too similar (low variance in persona means)
    if np.nanstd(persona_means) < 5.0:
        print(f"  [WARNING] Personas have very similar mean ratings (std={np.nanstd(persona_means):.2f})")
        print(f"  [WARNING] This suggests personas may not be diverse enough")
        print(f"  [WARNING] All personas are rating items similarly, reducing item discrimination")
    print()
    
    # 4. Analyze skewness and kurtosis
    print("=" * 80)
    print("4. DISTRIBUTION ANALYSIS (SKEWNESS & KURTOSIS)")
    print("=" * 80)
    skew_kurt_stats = calculate_skewness_kurtosis(ratings_matrix)
    
    skew_values = [stats["skewness"] for stats in skew_kurt_stats.values()]
    kurt_values = [stats["kurtosis"] for stats in skew_kurt_stats.values()]
    
    print(f"  Skewness:")
    print(f"    - Mean: {np.mean(skew_values):.3f}")
    print(f"    - Std: {np.std(skew_values):.3f}")
    print(f"    - Items with |skew| <= 1.0: {sum(1 for s in skew_values if abs(s) <= 1.0)}/{len(skew_values)}")
    print(f"    - Items with |skew| <= 1.5: {sum(1 for s in skew_values if abs(s) <= 1.5)}/{len(skew_values)}")
    print()
    print(f"  Kurtosis:")
    print(f"    - Mean: {np.mean(kurt_values):.3f}")
    print(f"    - Std: {np.std(kurt_values):.3f}")
    print(f"    - Items with |kurt| <= 2.0: {sum(1 for k in kurt_values if abs(k) <= 2.0)}/{len(kurt_values)}")
    print(f"    - Items with |kurt| <= 3.0: {sum(1 for k in kurt_values if abs(k) <= 3.0)}/{len(kurt_values)}")
    print()
    
    # 5. Recommendations
    print("=" * 80)
    print("5. RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = []
    
    # Check item-total correlation
    if sum(1 for c in corr_values if c >= 0.5) < n_items * 0.1:
        recommendations.append(
            f"  - Lower min_item_total_corr threshold: "
            f"Only {sum(1 for c in corr_values if c >= 0.5)}/{n_items} items pass >= 0.5. "
            f"Consider using 0.3 or 0.4 instead."
        )
    
    # Check persona diversity
    if np.nanstd(persona_means) < 5.0:
        recommendations.append(
            f"  - Improve persona diversity: "
            f"Personas have very similar mean ratings (std={np.nanstd(persona_means):.2f}). "
            f"Consider generating more diverse personas with different backgrounds, experiences, and attitudes."
        )
    
    # Check rating variance
    if low_variance_items > n_items * 0.5:
        recommendations.append(
            f"  - Items lack discrimination: "
            f"{low_variance_items}/{n_items} items have low variance (std < {low_variance_threshold}). "
            f"This suggests items may not differentiate well between participants."
        )
    
    # Check distribution
    if sum(1 for s in skew_values if abs(s) <= 1.0) < n_items * 0.1:
        recommendations.append(
            f"  - Relax skewness threshold: "
            f"Only {sum(1 for s in skew_values if abs(s) <= 1.0)}/{n_items} items pass |skew| <= 1.0. "
            f"Consider using 1.5 instead."
        )
    
    if recommendations:
        for rec in recommendations:
            print(rec)
    else:
        print("  - No major issues detected. Data quality appears good.")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python utils/diagnose_selection_issue.py <evaluation_summary_path>")
        print("Example: python utils/diagnose_selection_issue.py data/runs/2025-12-18_193304/evaluation_agent_group/selection/evaluation_summary.json")
        sys.exit(1)
    
    eval_path = Path(sys.argv[1])
    if not eval_path.exists():
        print(f"[ERROR] Path does not exist: {eval_path}")
        sys.exit(1)
    
    diagnose_selection_issue(eval_path)

