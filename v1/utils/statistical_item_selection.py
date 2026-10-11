"""
Statistical Item Selection Module

Provides functions for selecting items based on evaluation statistics.
Similar to PETS paper's EFA/CFA approach, but using rating-based selection.

Reference: Schmidmaier et al. (2024) - PETS paper
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import statistics


def select_items_by_rating_threshold(
    evaluation_summary: Dict[str, Any],
    min_mean_rating: float = 60.0,
    max_std: float = 30.0
) -> List[int]:
    """
    Select items based on rating statistics.
    
    Keeps items that meet both criteria:
    - Mean rating >= min_mean_rating
    - Standard deviation <= max_std
    
    Args:
        evaluation_summary: Evaluation summary JSON (contains item_statistics)
        min_mean_rating: Minimum mean rating to keep (0-100)
        max_std: Maximum standard deviation to keep
    
    Returns:
        List of item IDs (1-indexed) to keep
    """
    item_stats = evaluation_summary.get("item_statistics", [])
    selected_items = []
    
    for item_stat in item_stats:
        rating_stats = item_stat.get("rating_statistics", {})
        mean_rating = rating_stats.get("mean")
        std_rating = rating_stats.get("std")
        
        if mean_rating is None:
            continue
        
        # Keep items with good ratings and low variance
        if mean_rating >= min_mean_rating:
            if std_rating is None or std_rating <= max_std:
                selected_items.append(item_stat.get("item_id"))
    
    return sorted(selected_items)


def select_items_by_percentile(
    evaluation_summary: Dict[str, Any],
    top_percentile: float = 0.75
) -> List[int]:
    """
    Select top N% items by mean rating.
    
    Args:
        evaluation_summary: Evaluation summary JSON
        top_percentile: Percentile threshold (0.0-1.0), e.g., 0.75 means top 75%
    
    Returns:
        List of item IDs (1-indexed) to keep
    """
    item_stats = evaluation_summary.get("item_statistics", [])
    
    # Collect all mean ratings
    ratings = []
    for item_stat in item_stats:
        rating_stats = item_stat.get("rating_statistics", {})
        mean_rating = rating_stats.get("mean")
        if mean_rating is not None:
            ratings.append((item_stat.get("item_id"), mean_rating))
    
    if not ratings:
        return []
    
    # Sort by rating (descending)
    ratings.sort(key=lambda x: x[1], reverse=True)
    
    # Select top percentile
    n_select = max(1, int(len(ratings) * top_percentile))
    selected_items = [item_id for item_id, _ in ratings[:n_select]]
    
    return sorted(selected_items)


def select_items_by_dimension_balance(
    evaluation_summary: Dict[str, Any],
    items: List[Dict[str, str]],
    min_items_per_dimension: int = 2,
    max_items_per_dimension: int = 6
) -> List[int]:
    """
    Select items ensuring balanced representation across dimensions.
    
    For each dimension, selects top-rated items up to max_items_per_dimension,
    ensuring at least min_items_per_dimension items per dimension.
    
    Args:
        evaluation_summary: Evaluation summary JSON
        items: Original items list (for dimension mapping)
        min_items_per_dimension: Minimum items to keep per dimension
        max_items_per_dimension: Maximum items to keep per dimension
    
    Returns:
        List of item IDs (1-indexed) to keep
    """
    item_stats = evaluation_summary.get("item_statistics", [])
    
    # Group items by dimension
    dimension_items = {}
    for item_stat in item_stats:
        dimension = item_stat.get("dimension", "Unknown")
        item_id = item_stat.get("item_id")
        rating_stats = item_stat.get("rating_statistics", {})
        mean_rating = rating_stats.get("mean")
        
        if mean_rating is None:
            continue
        
        if dimension not in dimension_items:
            dimension_items[dimension] = []
        
        dimension_items[dimension].append((item_id, mean_rating))
    
    # Select items per dimension
    selected_items = []
    for dimension, dim_items in dimension_items.items():
        # Sort by rating (descending)
        dim_items.sort(key=lambda x: x[1], reverse=True)
        
        # Select top items for this dimension
        n_select = min(max_items_per_dimension, len(dim_items))
        n_select = max(min_items_per_dimension, n_select)  # Ensure minimum
        n_select = min(n_select, len(dim_items))  # Don't exceed available
        
        selected_items.extend([item_id for item_id, _ in dim_items[:n_select]])
    
    return sorted(selected_items)


def filter_scale_by_item_ids(
    items: List[Dict[str, str]],
    selected_item_ids: List[int]
) -> List[Dict[str, str]]:
    """
    Filter scale items by selected item IDs.
    
    Args:
        items: Original items list
        selected_item_ids: Item IDs to keep (1-indexed)
    
    Returns:
        Filtered items list
    """
    # Filter items based on their position (item_id is 1-indexed)
    filtered_items = []
    for idx, item in enumerate(items, 1):
        if idx in selected_item_ids:
            filtered_items.append(item)
    
    return filtered_items


def generate_filtered_scale_draft(
    filtered_items: List[Dict[str, str]],
    selected_item_ids: List[int],
    efa_cfa_results: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> str:
    """
    Generate filtered scale draft markdown following PETS methodology.
    
    When EFA extracts multiple factors, items are organized by factors (statistical structure).
    When EFA extracts only 1 factor, items are organized by theoretical dimensions.
    
    Args:
        filtered_items: List of filtered items with dimension and item_text
        selected_item_ids: List of selected item IDs (1-indexed)
        efa_cfa_results: Optional EFA/CFA results dictionary
        output_path: Optional path to save the markdown file
    
    Returns:
        Markdown string content
    """
    md_lines = ["# Empathy Scale (Filtered)", ""]
    
    # Create mapping from original item_id to item object
    # filtered_items is in the same order as selected_item_ids (from filter_scale_by_item_ids)
    item_map = {item_id: item for item_id, item in zip(selected_item_ids, filtered_items)}
    
    # Get EFA results if available
    n_factors = 1
    efa_results = {}
    if efa_cfa_results:
        n_factors = efa_cfa_results.get("n_factors", 1)
        efa_results = efa_cfa_results.get("efa_results", {})
    
    if n_factors > 1:
        # Multiple factors: organize by EFA factors (PETS methodology)
        md_lines.append("## Items by Factor (EFA-based)")
        md_lines.append("")
        md_lines.append(f"*Note: Items are organized by EFA factors (n={n_factors}). Factor structure determined by statistical analysis.*")
        md_lines.append("")
        
        # Group items by factor
        factor_items = {}
        item_loadings = efa_results.get("item_loadings", {})
        
        for item_id in selected_item_ids:
            item_id_str = str(item_id)
            if item_id_str in item_loadings:
                factor_idx = item_loadings[item_id_str].get("max_factor", 0)
                factor_name = f"Factor{factor_idx + 1}"
                if factor_name not in factor_items:
                    factor_items[factor_name] = []
                factor_items[factor_name].append(item_id)
            else:
                # Fallback: assign to Factor1
                if "Factor1" not in factor_items:
                    factor_items["Factor1"] = []
                factor_items["Factor1"].append(item_id)
        
        # Sort factors and output items
        item_num = 1
        for factor_name in sorted(factor_items.keys()):
            factor_item_ids = sorted(factor_items[factor_name])
            md_lines.append(f"### {factor_name} ({len(factor_item_ids)} items)")
            
            for item_id in factor_item_ids:
                if item_id in item_map:
                    item_text = item_map[item_id].get("item_text", "")
                    md_lines.append(f"- Item {item_num}: {item_text}")
                    item_num += 1
            md_lines.append("")
    else:
        # Single factor: use theoretical dimensions with note
        md_lines.append("## Items by Dimension")
        md_lines.append("")
        md_lines.append(f"*Note: EFA extracted 1 factor (unidimensional structure). Items organized by theoretical dimensions for reference.*")
        md_lines.append("")
        
        current_dimension = None
        item_num = 1
        
        for item in filtered_items:
            dimension = item.get("dimension", "Unknown")
            item_text = item.get("item_text", "")
            
            if dimension != current_dimension:
                if current_dimension is not None:
                    md_lines.append("")
                md_lines.append(f"### {dimension}")
                current_dimension = dimension
            
            md_lines.append(f"- Item {item_num}: {item_text}")
            item_num += 1
    
    md_content = "\n".join(md_lines)
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md_content, encoding="utf-8")
    
    return md_content


def get_selection_statistics(
    evaluation_summary: Dict[str, Any],
    selected_item_ids: List[int]
) -> Dict[str, Any]:
    """
    Get statistics about the selected items.
    
    Args:
        evaluation_summary: Evaluation summary JSON
        selected_item_ids: Selected item IDs (1-indexed)
    
    Returns:
        Dictionary with selection statistics
    """
    item_stats = evaluation_summary.get("item_statistics", [])
    
    selected_stats = [s for s in item_stats if s.get("item_id") in selected_item_ids]
    all_stats = item_stats
    
    # Calculate statistics
    selected_means = [
        s.get("rating_statistics", {}).get("mean")
        for s in selected_stats
        if s.get("rating_statistics", {}).get("mean") is not None
    ]
    all_means = [
        s.get("rating_statistics", {}).get("mean")
        for s in all_stats
        if s.get("rating_statistics", {}).get("mean") is not None
    ]
    
    result = {
        "n_original_items": len(all_stats),
        "n_selected_items": len(selected_stats),
        "selection_ratio": len(selected_stats) / len(all_stats) if all_stats else 0.0,
    }
    
    if selected_means:
        result["selected_mean_rating"] = round(statistics.mean(selected_means), 2)
        result["selected_std_rating"] = round(statistics.stdev(selected_means), 2) if len(selected_means) > 1 else 0.0
    
    if all_means:
        result["original_mean_rating"] = round(statistics.mean(all_means), 2)
        result["original_std_rating"] = round(statistics.stdev(all_means), 2) if len(all_means) > 1 else 0.0
    
    # Dimension distribution
    dimension_counts = {}
    for stat in selected_stats:
        dim = stat.get("dimension", "Unknown")
        dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
    
    result["dimension_distribution"] = dimension_counts
    
    return result


