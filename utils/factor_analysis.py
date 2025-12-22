"""
Factor Analysis Module for Item Selection

Implements Exploratory Factor Analysis (EFA) and Confirmatory Factor Analysis (CFA)
following PETS paper methodology (Schmidmaier et al., 2024).

Reference: 
- PETS paper Section 6 - Item Reduction: Exploratory Factor Analysis
- PETS paper Section 7.2 - Test of Dimensionality: Confirmatory Factor Analysis
"""

import json
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.stats import skew, kurtosis

# Suppress deprecation warning from factor-analyzer using old sklearn API
# factor-analyzer 0.5.1 still uses force_all_finite (deprecated in sklearn 1.6, removed in 1.8)
# This warning does not affect functionality and will be fixed in future factor-analyzer updates
warnings.filterwarnings(
    "ignore",
    message=".*force_all_finite.*was renamed to.*ensure_all_finite.*",
    category=FutureWarning,
    module="sklearn"
)

try:
    from factor_analyzer import FactorAnalyzer
    from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
    FACTOR_ANALYZER_AVAILABLE = True
except ImportError:
    FACTOR_ANALYZER_AVAILABLE = False
    print("[WARN] factor_analyzer not installed. Install with: pip install factor_analyzer")

try:
    from semopy import Model
    import pandas as pd
    SEMOPY_AVAILABLE = True
except ImportError:
    SEMOPY_AVAILABLE = False
    print("[WARN] semopy not installed. Install with: pip install semopy")


def load_participant_ratings(evaluation_summary_path: Path) -> Optional[np.ndarray]:
    """
    Load participant-level ratings from evaluation data.
    
    Args:
        evaluation_summary_path: Path to evaluation_summary.json or participant_level_evaluations.json
    
    Returns:
        numpy array of shape (n_participants, n_items) with ratings, or None if not available
    """
    # Try to load participant-level data first
    participant_data_path = evaluation_summary_path.parent / "participant_level_evaluations.json"
    if participant_data_path.exists():
        with open(participant_data_path, "r", encoding="utf-8") as f:
            participant_data = json.load(f)
        
        if not participant_data:
            return None
        
        # Extract ratings matrix
        n_participants = len(participant_data)
        n_items = len(participant_data[0].get("ratings", []))
        
        if n_items == 0:
            return None
        
        ratings_matrix = np.zeros((n_participants, n_items))
        for p_idx, participant in enumerate(participant_data):
            ratings = participant.get("ratings", [])
            for i_idx, rating_data in enumerate(ratings):
                rating = rating_data.get("rating")
                if rating is not None:
                    ratings_matrix[p_idx, i_idx] = float(rating)
                else:
                    ratings_matrix[p_idx, i_idx] = np.nan
        
        return ratings_matrix
    
    return None


def calculate_item_total_correlation(ratings_matrix: np.ndarray) -> Dict[int, float]:
    """
    Calculate item-total correlation for each item.
    
    Item-total correlation measures how well each item correlates with the total scale score.
    PETS threshold: >= 0.5
    
    Args:
        ratings_matrix: numpy array of shape (n_participants, n_items)
    
    Returns:
        Dictionary mapping item_id (1-indexed) to correlation coefficient
    """
    n_items = ratings_matrix.shape[1]
    correlations = {}
    
    # Calculate total score for each participant (sum of all items)
    total_scores = np.nansum(ratings_matrix, axis=1)
    
    for item_idx in range(n_items):
        item_ratings = ratings_matrix[:, item_idx]
        
        # Skip if all NaN
        if np.all(np.isnan(item_ratings)):
            correlations[item_idx + 1] = 0.0
            continue
        
        # Calculate correlation between item and total score
        # Use total score excluding this item to avoid inflation
        total_excluding_item = total_scores - item_ratings
        
        # Remove NaN pairs
        valid_mask = ~(np.isnan(item_ratings) | np.isnan(total_excluding_item))
        if np.sum(valid_mask) < 3:  # Need at least 3 valid pairs
            correlations[item_idx + 1] = 0.0
            continue
        
        item_valid = item_ratings[valid_mask]
        total_valid = total_excluding_item[valid_mask]
        
        if np.std(item_valid) == 0 or np.std(total_valid) == 0:
            correlations[item_idx + 1] = 0.0
            continue
        
        corr, _ = stats.pearsonr(item_valid, total_valid)
        correlations[item_idx + 1] = corr if not np.isnan(corr) else 0.0
    
    return correlations


def calculate_inter_item_correlations(ratings_matrix: np.ndarray) -> Dict[Tuple[int, int], float]:
    """
    Calculate inter-item correlations (correlations between pairs of items).
    
    PETS removes items that correlate > 0.8 with several other items (redundancy check).
    
    Args:
        ratings_matrix: numpy array of shape (n_participants, n_items)
    
    Returns:
        Dictionary mapping (item_id1, item_id2) tuples to correlation coefficient
    """
    n_items = ratings_matrix.shape[1]
    correlations = {}
    
    for i in range(n_items):
        for j in range(i + 1, n_items):
            item_i = ratings_matrix[:, i]
            item_j = ratings_matrix[:, j]
            
            # Remove NaN pairs
            valid_mask = ~(np.isnan(item_i) | np.isnan(item_j))
            if np.sum(valid_mask) < 3:
                correlations[(i + 1, j + 1)] = 0.0
                continue
            
            item_i_valid = item_i[valid_mask]
            item_j_valid = item_j[valid_mask]
            
            if np.std(item_i_valid) == 0 or np.std(item_j_valid) == 0:
                correlations[(i + 1, j + 1)] = 0.0
                continue
            
            corr, _ = stats.pearsonr(item_i_valid, item_j_valid)
            correlations[(i + 1, j + 1)] = corr if not np.isnan(corr) else 0.0
    
    return correlations


def calculate_skewness_kurtosis(ratings_matrix: np.ndarray) -> Dict[int, Dict[str, float]]:
    """
    Calculate skewness and kurtosis for each item.
    
    PETS thresholds:
    - Skewness: <= |1|
    - Kurtosis: <= |2|
    
    Args:
        ratings_matrix: numpy array of shape (n_participants, n_items)
    
    Returns:
        Dictionary mapping item_id (1-indexed) to {"skewness": float, "kurtosis": float}
    """
    n_items = ratings_matrix.shape[1]
    stats_dict = {}
    
    for item_idx in range(n_items):
        item_ratings = ratings_matrix[:, item_idx]
        
        # Remove NaN
        valid_ratings = item_ratings[~np.isnan(item_ratings)]
        
        if len(valid_ratings) < 3:
            stats_dict[item_idx + 1] = {"skewness": 0.0, "kurtosis": 0.0}
            continue
        
        item_skew = skew(valid_ratings)
        item_kurt = kurtosis(valid_ratings, fisher=False)  # Fisher=False gives excess kurtosis
        
        stats_dict[item_idx + 1] = {
            "skewness": float(item_skew) if not np.isnan(item_skew) else 0.0,
            "kurtosis": float(item_kurt) if not np.isnan(item_kurt) else 0.0
        }
    
    return stats_dict


def calculate_adaptive_distribution_thresholds(
    skew_kurt_stats: Dict[int, Dict[str, float]],
    items_to_check: List[int],
    initial_max_skewness: float,
    initial_max_kurtosis: float,
    min_pass_rate: float = 0.1,
    min_items: int = 5
) -> Tuple[float, float, bool]:
    """
    Calculate adaptive distribution thresholds based on data characteristics.
    
    Following Boateng et al. (2018) recommendation: distribution checks should be
    flexible and adjusted based on data characteristics.
    
    Strategy:
    1. Calculate distribution statistics for items
    2. If pass rate is too low (< min_pass_rate or < min_items), adjust thresholds
    3. Use percentiles or data-driven approach to set reasonable thresholds
    
    Args:
        skew_kurt_stats: Dictionary mapping item_id to {"skewness": float, "kurtosis": float}
        items_to_check: List of item IDs to check
        initial_max_skewness: Initial skewness threshold
        initial_max_kurtosis: Initial kurtosis threshold
        min_pass_rate: Minimum pass rate (0.0-1.0) to trigger adjustment (default: 0.1 = 10%)
        min_items: Minimum number of items to pass (default: 5)
    
    Returns:
        Tuple of (adjusted_max_skewness, adjusted_max_kurtosis, was_adjusted)
    """
    if not items_to_check:
        return initial_max_skewness, initial_max_kurtosis, False
    
    # Calculate statistics for items to check
    skew_values = [abs(skew_kurt_stats[item_id]["skewness"]) for item_id in items_to_check]
    kurt_values = [abs(skew_kurt_stats[item_id]["kurtosis"]) for item_id in items_to_check]
    
    if not skew_values or not kurt_values:
        return initial_max_skewness, initial_max_kurtosis, False
    
    # Check how many items would pass with initial thresholds
    items_passed = [
        item_id for item_id in items_to_check
        if (abs(skew_kurt_stats[item_id]["skewness"]) <= initial_max_skewness and
            abs(skew_kurt_stats[item_id]["kurtosis"]) <= initial_max_kurtosis)
    ]
    pass_rate = len(items_passed) / len(items_to_check) if items_to_check else 0
    
    # If pass rate is acceptable, use initial thresholds
    if len(items_passed) >= min_items and pass_rate >= min_pass_rate:
        return initial_max_skewness, initial_max_kurtosis, False
    
    # Need to adjust thresholds
    # Strategy: Use 75th percentile or 1.5x max, whichever is more conservative
    # This ensures we keep a reasonable number of items while not being too lenient
    
    # Calculate percentiles
    skew_75th = np.percentile(skew_values, 75) if skew_values else initial_max_skewness
    kurt_75th = np.percentile(kurt_values, 75) if kurt_values else initial_max_kurtosis
    
    # Calculate max values
    max_skew = max(skew_values) if skew_values else initial_max_skewness
    max_kurt = max(kurt_values) if kurt_values else initial_max_kurtosis
    
    # Adjusted thresholds: use 75th percentile, but ensure at least 1.5x initial threshold
    # and cap at reasonable maximums based on Boateng et al. (2018):
    # - Skewness: excellent <= |1|, acceptable <= |2| (cap at 2.0)
    # - Kurtosis: excellent <= |2|, acceptable <= |7| (cap at 7.0)
    adjusted_skew = min(
        max(skew_75th * 1.2, initial_max_skewness * 1.5),  # At least 1.5x initial, or 1.2x 75th percentile
        2.0  # Cap at 2.0 (Boateng et al., 2018 acceptable maximum for Likert scales)
    )
    adjusted_kurt = min(
        max(kurt_75th * 1.2, initial_max_kurtosis * 1.5),  # At least 1.5x initial, or 1.2x 75th percentile
        7.0  # Cap at 7.0 (Boateng et al., 2018 acceptable maximum for Likert scales)
    )
    
    # Verify that adjusted thresholds would pass enough items
    items_passed_adjusted = [
        item_id for item_id in items_to_check
        if (abs(skew_kurt_stats[item_id]["skewness"]) <= adjusted_skew and
            abs(skew_kurt_stats[item_id]["kurtosis"]) <= adjusted_kurt)
    ]
    
    # If still not enough, use more lenient thresholds (90th percentile)
    if len(items_passed_adjusted) < min_items:
        skew_90th = np.percentile(skew_values, 90) if skew_values else adjusted_skew
        kurt_90th = np.percentile(kurt_values, 90) if kurt_values else adjusted_kurt
        
        adjusted_skew = min(max(skew_90th * 1.1, adjusted_skew), 2.0)
        adjusted_kurt = min(max(kurt_90th * 1.1, adjusted_kurt), 7.0)
    
    return adjusted_skew, adjusted_kurt, True


def perform_efa(
    ratings_matrix: np.ndarray,
    n_factors: Optional[int] = None,
    rotation: str = "promax",
    min_factor_loading: float = 0.75
) -> Dict[str, Any]:
    """
    Perform Exploratory Factor Analysis (EFA) following PETS methodology.
    
    PETS method:
    - Principal Axis Factoring (PAF)
    - Promax Rotation (oblique, because factors are correlated)
    - Keep only items with factor loadings >= 0.75
    
    Args:
        ratings_matrix: numpy array of shape (n_participants, n_items)
        n_factors: Number of factors to extract (None = auto-detect using Kaiser criterion)
        rotation: Rotation method ("promax" or "varimax")
        min_factor_loading: Minimum factor loading to keep (default: 0.75 as per PETS)
    
    Returns:
        Dictionary with:
        - factor_loadings: numpy array of shape (n_items, n_factors)
        - selected_items: List of item IDs (1-indexed) with loadings >= min_factor_loading
        - n_factors: Number of factors extracted
        - bartlett_test: Bartlett's sphericity test results
        - kmo_test: KMO test results
        - eigenvalues: Eigenvalues for each factor
    """
    if not FACTOR_ANALYZER_AVAILABLE:
        raise ImportError("factor_analyzer library not installed. Install with: pip install factor_analyzer")
    
    # Remove items with all NaN
    valid_item_mask = ~np.all(np.isnan(ratings_matrix), axis=0)
    valid_items = np.where(valid_item_mask)[0]
    
    if len(valid_items) == 0:
        raise ValueError("No valid items in ratings matrix")
    
    if len(valid_items) < 2:
        raise ValueError(f"Only {len(valid_items)} valid item(s) in ratings matrix. EFA requires at least 2 items.")
    
    ratings_clean = ratings_matrix[:, valid_item_mask]
    
    # Validate shape
    if ratings_clean.shape[1] < 2:
        raise ValueError(f"Ratings matrix has only {ratings_clean.shape[1]} column(s). EFA requires at least 2 items.")
    
    # Handle missing values: impute with column mean
    for col_idx in range(ratings_clean.shape[1]):
        col = ratings_clean[:, col_idx]
        nan_mask = np.isnan(col)
        if np.any(nan_mask):
            col_mean = np.nanmean(col)
            if not np.isnan(col_mean):
                ratings_clean[nan_mask, col_idx] = col_mean
            else:
                ratings_clean[nan_mask, col_idx] = 50.0  # Default to neutral
    
    # Check prerequisites
    # Validate that we have enough samples relative to items
    n_samples, n_items = ratings_clean.shape
    if n_items > n_samples:
        raise ValueError(f"Too many items ({n_items}) relative to samples ({n_samples}). "
                        f"EFA requires n_samples >= n_items. Consider reducing items or increasing samples.")
    
    # Check correlation matrix for singularity issues
    # For large item sets, small determinants are common due to multicollinearity
    # Use a more lenient threshold that scales with number of items
    corr_matrix = np.corrcoef(ratings_clean.T)
    corr_det = np.linalg.det(corr_matrix)
    # Threshold: 1e-20 for small sets (<20 items), 1e-30 for larger sets
    # This accounts for the fact that determinants decrease exponentially with matrix size
    det_threshold = 1e-30 if n_items > 20 else 1e-20
    if corr_det <= det_threshold:
        # Check condition number as alternative metric
        try:
            cond_num = np.linalg.cond(corr_matrix)
            if cond_num > 1e12:  # Very ill-conditioned
                raise ValueError(f"Correlation matrix is near-singular (det={corr_det:.2e}, cond={cond_num:.2e}). "
                              f"This may indicate multicollinearity or too many items relative to samples. "
                              f"Consider reducing items or checking for duplicate items.")
        except np.linalg.LinAlgError:
            # If condition number calculation fails, use determinant check
            raise ValueError(f"Correlation matrix is near-singular (det={corr_det:.2e}). "
                          f"This may indicate multicollinearity or too many items relative to samples. "
                          f"Consider reducing items or checking for duplicate items.")
    
    bartlett_chi2, bartlett_p = calculate_bartlett_sphericity(ratings_clean)
    kmo_result = calculate_kmo(ratings_clean)
    
    # Handle KMO result: calculate_kmo returns (kmo_all_array, kmo_model_scalar)
    # kmo_all is an array (one value per item), kmo_model is a scalar (overall KMO)
    if isinstance(kmo_result, tuple):
        kmo_all_array, kmo_model = kmo_result
    else:
        # Fallback if structure is different
        kmo_all_array = kmo_result[0] if hasattr(kmo_result, '__getitem__') else kmo_result
        kmo_model = kmo_result[1] if hasattr(kmo_result, '__getitem__') and len(kmo_result) > 1 else kmo_result
    
    # Convert to scalars
    # kmo_all: array -> use mean for overall KMO (or we can keep as array for per-item analysis)
    if isinstance(kmo_all_array, np.ndarray):
        kmo_all = float(np.mean(kmo_all_array))  # Use mean of per-item KMO values
    else:
        kmo_all = float(kmo_all_array)
    
    # kmo_model: should already be scalar, but ensure it is
    if isinstance(kmo_model, np.ndarray):
        kmo_model = float(kmo_model.item()) if kmo_model.size == 1 else float(np.mean(kmo_model))
    else:
        kmo_model = float(kmo_model)
    
    # Determine number of factors if not specified
    if n_factors is None:
        # Use Kaiser criterion: eigenvalues >= 1
        # Limit max factors to avoid overfitting (max: min(n_items//3, n_samples//5))
        max_factors = min(ratings_clean.shape[1] // 3, n_samples // 5, ratings_clean.shape[1] - 1)
        max_factors = max(1, max_factors)  # At least 1 factor
        
        fa_temp = FactorAnalyzer(n_factors=min(ratings_clean.shape[1], max_factors * 2), rotation=None, method='principal')
        fa_temp.fit(ratings_clean)
        eigenvalues = fa_temp.get_eigenvalues()[0]
        n_factors = np.sum(eigenvalues >= 1.0)
        n_factors = int(max(1, min(n_factors, max_factors)))  # Convert to Python int for JSON serialization
    
    # Perform EFA
    fa = FactorAnalyzer(
        n_factors=n_factors,
        rotation=rotation,
        method='principal'  # Principal Axis Factoring (PAF)
    )
    fa.fit(ratings_clean)
    
    # Get factor loadings
    loadings = fa.loadings_  # Shape: (n_items, n_factors)
    eigenvalues = fa.get_eigenvalues()[0][:n_factors]
    
    # Normalize factor loadings signs for interpretability
    # Factor direction is arbitrary, so we ensure each factor has predominantly positive loadings
    # This makes interpretation clearer (following common practice in psychometrics)
    for factor_idx in range(n_factors):
        factor_loadings = loadings[:, factor_idx]
        # If majority of loadings are negative, flip the factor
        if np.sum(factor_loadings < 0) > np.sum(factor_loadings > 0):
            loadings[:, factor_idx] = -factor_loadings
    
    # Select items based on factor loadings
    selected_item_indices = []
    item_loadings = {}
    
    for item_idx, valid_item_idx in enumerate(valid_items):
        item_id = valid_item_idx + 1  # Convert to 1-indexed
        
        # Find maximum loading across all factors
        max_loading = np.max(np.abs(loadings[item_idx, :]))
        max_factor = np.argmax(np.abs(loadings[item_idx, :]))
        
        # Check for cross-loadings (loading > 0.3 on multiple factors)
        abs_loadings = np.abs(loadings[item_idx, :])
        high_loadings = np.sum(abs_loadings > 0.3)
        
        # Keep if:
        # 1. Maximum loading >= min_factor_loading
        # 2. No significant cross-loadings (only one factor with loading > 0.3)
        if max_loading >= min_factor_loading and high_loadings <= 1:
            selected_item_indices.append(item_id)
            item_loadings[item_id] = {
                "max_loading": float(max_loading),
                "max_factor": int(max_factor),
                "loadings": [float(loadings[item_idx, f]) for f in range(n_factors)]
            }
    
    return {
        "factor_loadings": loadings.tolist(),
        "selected_items": sorted(selected_item_indices),
        "item_loadings": item_loadings,
        "n_factors": int(n_factors),  # Convert to Python int for JSON serialization
        "bartlett_test": {
            "chi_square": float(bartlett_chi2),
            "p_value": float(bartlett_p),
            "significant": bool(bartlett_p < 0.001)  # Convert numpy bool_ to Python bool for JSON serialization
        },
        "kmo_test": {
            "kmo_all": kmo_all if not np.isnan(kmo_all) else 0.0,
            "kmo_model": kmo_model if not np.isnan(kmo_model) else 0.0,
            "adequate": bool(kmo_model >= 0.6) if not np.isnan(kmo_model) else False  # Convert numpy bool_ to Python bool
        },
        "eigenvalues": [float(e) for e in eigenvalues],
        "valid_items": [int(i + 1) for i in valid_items.tolist()]
    }


def perform_cfa(
    ratings_matrix: np.ndarray,
    factor_structure: Dict[int, int],
    max_iterations: int = 3,
    rmsea_threshold: float = 0.08,
    tli_threshold: float = 0.95,
    cfi_threshold: float = 0.95,
    srmr_threshold: float = 0.08,
    min_items_per_factor: int = 2,
    target_range: Optional[Tuple[int, int]] = None
) -> Dict[str, Any]:
    """
    Perform Confirmatory Factor Analysis (CFA) following PETS methodology.
    
    PETS method (Section 7.2):
    - Use new sample (PETS used 200 and 100 participants)
    - Verify factor structure from EFA
    - Check fit indices: RMSEA, TLI, CFI, SRMR
    - If fit is inadequate, remove items and re-run CFA
    - Final model: RMSEA <= 0.08, TLI >= 0.95, CFI >= 0.95, SRMR <= 0.08
    - If target_range is provided and items exceed target_max, continue removing items
      even if fit is adequate (for aggressive item reduction when min_factor_loading at upper bound)
    
    Args:
        ratings_matrix: numpy array of shape (n_participants, n_items)
        factor_structure: Dictionary mapping item_id (1-indexed) to factor_id (0-indexed)
        max_iterations: Maximum number of iterations to improve fit (default: 3)
        rmsea_threshold: Maximum RMSEA (default: 0.08)
        tli_threshold: Minimum TLI (default: 0.95)
        cfi_threshold: Minimum CFI (default: 0.95)
        srmr_threshold: Maximum SRMR (default: 0.08)
        min_items_per_factor: Minimum items per factor (default: 2)
        target_range: Optional target range (min, max). If provided and items exceed target_max,
            will continue removing items even if fit is adequate (default: None)
    
    Returns:
        Dictionary with:
        - selected_items: List of final selected item IDs
        - fit_indices: Dictionary with fit indices (RMSEA, TLI, CFI, SRMR)
        - factor_loadings: Dictionary mapping item_id to factor loading
        - iterations: Number of iterations performed
        - removed_items: List of items removed during iterations
    """
    if not SEMOPY_AVAILABLE:
        raise ImportError("semopy library not installed. Install with: pip install semopy")
    
    # Get unique items and factors
    items = sorted(factor_structure.keys())
    factors = sorted(set(factor_structure.values()))
    n_factors = len(factors)
    
    if n_factors == 0 or len(items) == 0:
        raise ValueError("Invalid factor structure: no items or factors")
    
    # Determine if factor_structure keys are 0-indexed (column indices) or 1-indexed (item IDs)
    # If all keys are < ratings_matrix.shape[1], they are likely 0-indexed column indices
    # Otherwise, they are 1-indexed item IDs
    max_key = max(items)
    if max_key < ratings_matrix.shape[1]:
        # Keys are 0-indexed column indices (submatrix format)
        item_indices = items
        # Create mapping from column index to item_id for DataFrame column names
        # Use 1-indexed item IDs for column names (item_id = col_idx + 1)
        item_id_map = {col_idx: col_idx + 1 for col_idx in items}
    else:
        # Keys are 1-indexed item IDs (original format)
        # Create item indices mapping (1-indexed item_id to 0-indexed column index)
        item_to_col = {item_id: item_id - 1 for item_id in items}
        item_indices = [item_to_col[item_id] for item_id in items]
        item_id_map = {col_idx: item_id for item_id, col_idx in zip(items, item_indices)}
    
    # Extract relevant columns from ratings matrix
    ratings_subset = ratings_matrix[:, item_indices]
    
    # Handle missing values: impute with column mean
    for col_idx in range(ratings_subset.shape[1]):
        col = ratings_subset[:, col_idx]
        nan_mask = np.isnan(col)
        if np.any(nan_mask):
            col_mean = np.nanmean(col)
            if not np.isnan(col_mean):
                ratings_subset[nan_mask, col_idx] = col_mean
            else:
                ratings_subset[nan_mask, col_idx] = 50.0
    
    # Convert to DataFrame for semopy
    # Use item IDs as column names for clarity
    # Map column indices to item IDs for column names
    if max_key < ratings_matrix.shape[1]:
        # Keys are 0-indexed, column names use item_id = key + 1
        df_columns = [f"Item{col_idx + 1}" for col_idx in item_indices]
    else:
        # Keys are 1-indexed, column names use key directly
        df_columns = [f"Item{item_id}" for item_id in items]
    df = pd.DataFrame(ratings_subset, columns=df_columns)
    
    # current_items stores the keys from factor_structure (either 0-indexed or 1-indexed)
    # We'll use them as-is, but need to map to column names correctly
    current_items = items.copy()
    
    # Create mapping: factor_structure key -> column name in DataFrame
    # If keys are 0-indexed, map to item_id = key + 1
    # If keys are 1-indexed, use key directly
    if max_key < ratings_matrix.shape[1]:
        # Keys are 0-indexed, column names use item_id = key + 1
        item_to_colname = {key: f"Item{key + 1}" for key in items}
    else:
        # Keys are 1-indexed, column names use key directly
        item_to_colname = {key: f"Item{key}" for key in items}
    removed_items = []
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"    [CFA Iteration {iteration}] Testing {len(current_items)} items...")
        
        # Build SEM model specification
        # Format: "Factor =~ Item1 + Item2 + ..."
        model_spec = []
        for factor_idx in factors:
            factor_items = [item_id for item_id in current_items if factor_structure.get(item_id) == factor_idx]
            if factor_items:
                # Map item_id to column name using the mapping
                item_cols = [item_to_colname.get(item_id, f"Item{item_id}") for item_id in factor_items]
                factor_name = f"Factor{factor_idx+1}"
                model_spec.append(f"{factor_name} =~ " + " + ".join(item_cols))
        
        # Allow factors to covary
        if n_factors > 1:
            factor_names = [f"Factor{f+1}" for f in factors]
            for i in range(len(factor_names)):
                for j in range(i + 1, len(factor_names)):
                    model_spec.append(f"{factor_names[i]} ~~ {factor_names[j]}")
        
        model_str = "\n".join(model_spec)
        
        try:
            # Fit CFA model
            model = Model(model_str)
            model.fit(df)
            
            # Get fit indices
            fit_indices = model.inspect()
            
            rmsea = fit_indices.get("RMSEA", float('inf'))
            tli = fit_indices.get("TLI", 0.0)
            cfi = fit_indices.get("CFI", 0.0)
            srmr = fit_indices.get("SRMR", float('inf'))
            
            print(f"    [CFA Iteration {iteration}] Fit indices: RMSEA={rmsea:.4f}, TLI={tli:.4f}, CFI={cfi:.4f}, SRMR={srmr:.4f}")
            
            # Check if fit is adequate
            fit_adequate = (
                rmsea <= rmsea_threshold and
                tli >= tli_threshold and
                cfi >= cfi_threshold and
                srmr <= srmr_threshold
            )
            
            # Check if we need to continue removing items even if fit is adequate
            # (e.g., when min_factor_loading at upper bound and items exceed target range)
            continue_removing_for_target = False
            if fit_adequate and target_range:
                target_min, target_max = target_range
                if len(current_items) > target_max:
                    continue_removing_for_target = True
                    print(f"    [CFA] Fit adequate but {len(current_items)} items > target_max ({target_max}), continuing to remove items")
            
            if fit_adequate and not continue_removing_for_target:
                print(f"    [CFA] Model fit is adequate after {iteration} iteration(s)")
                break
            
            # If fit is inadequate OR we need to reach target range, find worst item to remove
            # Check minimum items per factor constraint (PETS: each factor needs at least 2 items)
            factor_item_counts = {}
            for item_id in current_items:
                factor_idx = factor_structure.get(item_id)
                factor_item_counts[factor_idx] = factor_item_counts.get(factor_idx, 0) + 1
            
            min_items_required = min_items_per_factor * n_factors
            # Determine target item count for removal decision
            target_item_count = None
            if continue_removing_for_target and target_range:
                target_min, target_max = target_range
                target_item_count = target_max  # Remove until we reach target_max
            
            can_remove_items = (
                iteration < max_iterations and 
                len(current_items) > min_items_required and
                all(count >= min_items_per_factor for count in factor_item_counts.values()) and
                (not target_item_count or len(current_items) > target_item_count)
            )
            
            if can_remove_items:
                # Get factor loadings
                params = model.inspect(std_est=True)
                
                # Calculate imbalance ratio to determine if we should prioritize balancing
                max_items = max(factor_item_counts.values()) if factor_item_counts else 0
                min_items = min(factor_item_counts.values()) if factor_item_counts else 0
                imbalance_ratio = max_items / min_items if min_items > 0 else float('inf')
                
                # If imbalance is severe (ratio > 2.0) OR we're trying to reach target range, prioritize removing from larger factors
                prioritize_balance = imbalance_ratio > 2.0 or continue_removing_for_target
                
                # Find item with lowest loading (but ensure we don't violate min_items_per_factor)
                # If prioritizing balance, prioritize items from factors with more items
                min_loading = float('inf')
                worst_item = None
                
                # If prioritizing balance, first identify factors with excess items
                factors_to_target = set()
                if prioritize_balance and len(factor_item_counts) > 1:
                    avg_items = sum(factor_item_counts.values()) / len(factor_item_counts)
                    # Target factors that have significantly more items than average
                    for factor_idx, count in factor_item_counts.items():
                        if count > avg_items * 1.2:  # 20% above average (more aggressive)
                            factors_to_target.add(factor_idx)
                
                # If trying to reach target range and imbalance is severe, be more aggressive
                if continue_removing_for_target and imbalance_ratio > 3.0:
                    # When severely imbalanced and trying to reach target, prioritize largest factor
                    largest_factor = max(factor_item_counts.items(), key=lambda x: x[1])[0]
                    factors_to_target = {largest_factor}
                
                for item_id in current_items:
                    item_factor = factor_structure.get(item_id)
                    # Check if removing this item would violate min_items_per_factor
                    if factor_item_counts.get(item_factor, 0) <= min_items_per_factor:
                        continue  # Cannot remove this item
                    
                    # If prioritizing balance, only consider items from targeted factors
                    if prioritize_balance and factors_to_target:
                        if item_factor not in factors_to_target:
                            continue
                    
                    # Map item_id to column name
                    item_col = item_to_colname.get(item_id, f"Item{item_id}")
                    
                    # Find loading for this item
                    loading_row = params[params['lval'] == item_col]
                    if not loading_row.empty:
                        loading = abs(loading_row.iloc[0]['Estimate'])
                        if loading < min_loading:
                            min_loading = loading
                            worst_item = item_id
                
                # If no item found with balance priority, fall back to any item (but still respect min_items_per_factor)
                if not worst_item and prioritize_balance:
                    for item_id in current_items:
                        item_factor = factor_structure.get(item_id)
                        if factor_item_counts.get(item_factor, 0) <= min_items_per_factor:
                            continue
                        
                        item_col = item_to_colname.get(item_id, f"Item{item_id}")
                    loading_row = params[params['lval'] == item_col]
                    if not loading_row.empty:
                        loading = abs(loading_row.iloc[0]['Estimate'])
                        if loading < min_loading:
                            min_loading = loading
                            worst_item = item_id
                
                if worst_item:
                    removed_factor = factor_structure.get(worst_item)
                    factor_name = f"Factor{removed_factor+1}"
                    balance_note = f" (balance_priority={prioritize_balance}, imbalance_ratio={imbalance_ratio:.2f})" if prioritize_balance else ""
                    print(f"    [CFA Iteration {iteration}] Removing item {worst_item} from {factor_name} (loading={min_loading:.3f}{balance_note})")
                    current_items.remove(worst_item)
                    removed_items.append(worst_item)
                    # Update factor counts
                    if removed_factor in factor_item_counts:
                        factor_item_counts[removed_factor] -= 1
                    
                    # Update DataFrame by selecting columns from existing df
                    # current_items are keys from factor_structure, need to map to column names
                    remaining_cols = [item_to_colname.get(item_id, f"Item{item_id}") for item_id in current_items]
                    df = df[remaining_cols].copy()
                else:
                    print(f"    [CFA] Cannot find item to remove, stopping")
                    break
            else:
                print(f"    [CFA] Maximum iterations reached or too few items, stopping")
                break
                
        except Exception as e:
            print(f"    [CFA ERROR] Iteration {iteration} failed: {e}")
            if iteration == 1:
                raise
            break
    
    # Get final factor loadings
    factor_loadings = {}
    try:
        # Rebuild model with final items (model_str may be outdated if items were removed)
        # Only use items that are actually in the DataFrame
        available_cols = set(df.columns)
        final_model_spec = []
        for factor_idx in factors:
            factor_items = [item_id for item_id in current_items if factor_structure.get(item_id) == factor_idx]
            if factor_items:
                # Map item_id to column name using the same mapping as before
                item_cols = []
                for item_id in factor_items:
                    # Use item_to_colname mapping (created earlier) to get correct column name
                    col_name = item_to_colname.get(item_id, f"Item{item_id}")
                    
                    # Only include if column exists in DataFrame
                    if col_name in available_cols:
                        item_cols.append(col_name)
                
                if item_cols:  # Only add factor if it has at least one item
                    factor_name = f"Factor{factor_idx+1}"
                    final_model_spec.append(f"{factor_name} =~ " + " + ".join(item_cols))
        
        if not final_model_spec:
            print(f"    [CFA WARN] No valid items remaining for final model")
            factor_loadings = {}
        else:
            if n_factors > 1:
                factor_names = [f"Factor{f+1}" for f in factors]
                for i in range(len(factor_names)):
                    for j in range(i + 1, len(factor_names)):
                        final_model_spec.append(f"{factor_names[i]} ~~ {factor_names[j]}")
            
            final_model_str = "\n".join(final_model_spec)
            final_model = Model(final_model_str)
            final_model.fit(df)
            params = final_model.inspect(std_est=True)
            
            # Extract factor loadings only for items that exist in DataFrame
            for item_id in current_items:
                # Use item_to_colname mapping to get correct column name
                item_col = item_to_colname.get(item_id, f"Item{item_id}")
                
                # Only extract if column exists in DataFrame
                if item_col in available_cols:
                    loading_row = params[params['lval'] == item_col]
                    if not loading_row.empty:
                        factor_loadings[item_id] = float(loading_row.iloc[0]['Estimate'])
    except Exception as e:
        print(f"    [CFA WARN] Could not extract final factor loadings: {e}")
        factor_loadings = {}
    
    return {
        "selected_items": sorted(current_items),
        "fit_indices": {
            "RMSEA": float(rmsea) if 'rmsea' in locals() else None,
            "TLI": float(tli) if 'tli' in locals() else None,
            "CFI": float(cfi) if 'cfi' in locals() else None,
            "SRMR": float(srmr) if 'srmr' in locals() else None,
            "adequate": fit_adequate if 'fit_adequate' in locals() else False
        },
        "factor_loadings": factor_loadings,
        "iterations": iteration,
        "removed_items": removed_items
    }


def _perform_stage1_filtering(
    ratings_matrix: np.ndarray,
    min_item_total_corr: float,
    max_skewness: float,
    max_kurtosis: float,
    max_inter_corr: float,
    adaptive_distribution_thresholds: bool,
    min_distribution_pass_rate: float,
    min_distribution_items: int
) -> Dict[str, Any]:
    """
    Stage 1: Perform Step 1-3 filtering to select 35-50 items for EFA.
    
    This stage adaptively adjusts thresholds to ensure enough items enter EFA.
    Target: 35-50 items pass all preliminary checks (preferred: 40-45 items).
    
    Returns:
        Dictionary containing:
        - items_passed_inter: List of item IDs that passed Step 1-3
        - item_total_corrs: Dict of item-total correlations
        - skew_kurt_stats: Dict of skewness/kurtosis statistics
        - inter_corrs: Dict of inter-item correlations
        - filtering_steps: Dict with counts at each step
        - actual_thresholds: Dict with actual thresholds used
    """
    n_participants, n_items = ratings_matrix.shape
    
    print(f"    [Stage 1] Starting preliminary filtering (Step 1-3)...")
    # Calculate max items based on sample size to avoid matrix singularity
    # EFA requires items < samples, use 80% of samples as upper bound for stability
    max_items_for_efa_sample_limit = int(0.8 * n_participants)
    print(f"    [Stage 1] Sample size: {n_participants}, maximum items for EFA (80% of samples): {max_items_for_efa_sample_limit}")
    
    # Step 1: Calculate item-total correlation
    print(f"    [Step 1] Calculating item-total correlations...")
    item_total_corrs = calculate_item_total_correlation(ratings_matrix)
    
    # Show correlation statistics for diagnosis
    if item_total_corrs:
        corr_values = list(item_total_corrs.values())
        max_corr = max(corr_values) if corr_values else 0
        mean_corr = np.mean(corr_values) if corr_values else 0
        print(f"    [Step 1] Item-total correlation statistics: max={max_corr:.3f}, mean={mean_corr:.3f}")
    
    # Filter by item-total correlation with adaptive adjustment if needed
    # Adaptive adjustment range: 0.25 (quality floor) to initial threshold (PETS standard: 0.5)
    # Following Boateng et al. (2018): flexible adjustment based on data characteristics
    min_item_total_corr_floor = 0.25  # Quality floor (below this, item quality too poor)
    target_items_after_corr = 30  # Target: ensure enough items for EFA (30-40 range)
    
    actual_min_item_total_corr = min_item_total_corr
    items_passed_corr = [
        item_id for item_id, corr in item_total_corrs.items()
        if corr >= actual_min_item_total_corr
    ]
    
    # Adaptive adjustment: if too few items, lower threshold (but not below quality floor)
    if len(items_passed_corr) < target_items_after_corr and item_total_corrs:
        max_corr = max(item_total_corrs.values())
        # Only adjust if max correlation is reasonable (>= quality floor)
        if max_corr >= min_item_total_corr_floor:
            # Try to lower threshold to reach target, but not below floor
            # Strategy: test thresholds from initial-0.05 down to floor, in 0.05 steps
            test_thresholds = []
            current = min_item_total_corr - 0.05
            while current >= min_item_total_corr_floor:
                test_thresholds.append(round(current, 2))
                current -= 0.05
            
            best_items = items_passed_corr
            best_threshold = actual_min_item_total_corr
            
            for test_threshold in test_thresholds:
                test_items = [
                    item_id for item_id, corr in item_total_corrs.items()
                    if corr >= test_threshold
                ]
                if len(test_items) >= target_items_after_corr:
                    best_items = test_items
                    best_threshold = test_threshold
                    break
                elif len(test_items) > len(best_items):
                    best_items = test_items
                    best_threshold = test_threshold
            
            if best_threshold < actual_min_item_total_corr:
                actual_min_item_total_corr = max(best_threshold, min_item_total_corr_floor)
                items_passed_corr = best_items
                print(f"    [Step 1] Adaptive adjustment: Lowered min_item_total_corr from {min_item_total_corr} to {actual_min_item_total_corr:.2f}")
                print(f"    [Step 1] Reason: Only {len(items_passed_corr)} items passed initial threshold (target: {target_items_after_corr})")
                if actual_min_item_total_corr < 0.30:
                    print(f"    [Step 1] WARNING: Threshold below 0.30. Item quality may be compromised (PETS standard: >=0.5)")
    
    print(f"    [Step 1] {len(items_passed_corr)}/{n_items} items passed item-total correlation (>= {actual_min_item_total_corr:.2f})")
    
    if len(items_passed_corr) == 0:
        # Provide diagnostic information
        if item_total_corrs:
            max_corr = max(item_total_corrs.values())
            print(f"    [DIAGNOSTIC] Maximum item-total correlation: {max_corr:.3f} (threshold: {actual_min_item_total_corr:.2f})")
            print(f"    [DIAGNOSTIC] Quality floor: {min_item_total_corr_floor} (below this, item quality too poor)")
            if max_corr < min_item_total_corr_floor:
                print(f"    [DIAGNOSTIC] All item-total correlations below quality floor. Data quality issue - consider regenerating items.")
            else:
                print(f"    [SUGGESTION] Consider lowering min_item_total_corr threshold (e.g., to {max_corr:.2f})")
        raise ValueError(f"No items passed item-total correlation threshold (>= {actual_min_item_total_corr:.2f}). Cannot proceed with EFA.")
    
    # Step 2: Calculate skewness and kurtosis
    print(f"    [Step 2] Calculating skewness and kurtosis...")
    skew_kurt_stats = calculate_skewness_kurtosis(ratings_matrix)
    
    # Apply adaptive threshold adjustment if enabled
    actual_max_skewness = max_skewness
    actual_max_kurtosis = max_kurtosis
    thresholds_adjusted = False
    
    if adaptive_distribution_thresholds:
        # First, try with initial thresholds
        items_passed_initial = [
        item_id for item_id in items_passed_corr
        if (abs(skew_kurt_stats[item_id]["skewness"]) <= max_skewness and
            abs(skew_kurt_stats[item_id]["kurtosis"]) <= max_kurtosis)
    ]
        pass_rate_initial = len(items_passed_initial) / len(items_passed_corr) if items_passed_corr else 0
        
        # If pass rate is too low, calculate adaptive thresholds
        if len(items_passed_initial) < min_distribution_items or pass_rate_initial < min_distribution_pass_rate:
            actual_max_skewness, actual_max_kurtosis, thresholds_adjusted = calculate_adaptive_distribution_thresholds(
                skew_kurt_stats,
                items_passed_corr,
                max_skewness,
                max_kurtosis,
                min_distribution_pass_rate,
                min_distribution_items
            )
            
            if thresholds_adjusted:
                print(f"    [Step 2] Adaptive threshold adjustment applied (Boateng et al., 2018 recommendation):")
                print(f"      - Initial thresholds: skew <= {max_skewness}, kurt <= {max_kurtosis}")
                print(f"      - Adjusted thresholds: skew <= {actual_max_skewness:.2f}, kurt <= {actual_max_kurtosis:.2f}")
                print(f"      - Reason: Only {len(items_passed_initial)}/{len(items_passed_corr)} items passed initial thresholds")
                print(f"      - Pass rate: {pass_rate_initial:.1%} (minimum required: {min_distribution_pass_rate:.1%} or {min_distribution_items} items)")
    
    # Filter by skewness/kurtosis (using actual thresholds, which may be adjusted)
    items_passed_dist = [
        item_id for item_id in items_passed_corr
        if (abs(skew_kurt_stats[item_id]["skewness"]) <= actual_max_skewness and
            abs(skew_kurt_stats[item_id]["kurtosis"]) <= actual_max_kurtosis)
    ]
    print(f"    [Step 2] {len(items_passed_dist)}/{len(items_passed_corr)} items passed distribution checks (skew <= {actual_max_skewness:.2f}, kurt <= {actual_max_kurtosis:.2f})")
    
    if len(items_passed_dist) == 0:
        # Provide diagnostic information
        if items_passed_corr:
            skew_values = [abs(skew_kurt_stats[item_id]["skewness"]) for item_id in items_passed_corr]
            kurt_values = [abs(skew_kurt_stats[item_id]["kurtosis"]) for item_id in items_passed_corr]
            max_skew = max(skew_values) if skew_values else 0
            max_kurt = max(kurt_values) if kurt_values else 0
            mean_skew = np.mean(skew_values) if skew_values else 0
            mean_kurt = np.mean(kurt_values) if kurt_values else 0
            print(f"    [DIAGNOSTIC] Distribution statistics for items that passed correlation check:")
            print(f"      - Max skewness: {max_skew:.3f} (threshold: {actual_max_skewness:.2f})")
            print(f"      - Max kurtosis: {max_kurt:.3f} (threshold: {actual_max_kurtosis:.2f})")
            print(f"      - Mean skewness: {mean_skew:.3f}")
            print(f"      - Mean kurtosis: {mean_kurt:.3f}")
            print(f"    [SUGGESTION] Consider:")
            print(f"      1. Further relaxing distribution thresholds manually")
            print(f"      2. Checking data quality (all items may have similar ratings)")
            print(f"      3. Using adaptive_distribution_thresholds=True (if not already enabled)")
        raise ValueError("No items passed distribution checks. Cannot proceed with EFA.")
    
    # Step 3: Calculate inter-item correlations
    print(f"    [Step 3] Calculating inter-item correlations (only for items passed previous steps)...")
    
    # Create subset of ratings matrix for items that passed distribution checks
    item_indices = [item_id - 1 for item_id in items_passed_dist]
    ratings_subset = ratings_matrix[:, item_indices]
    
    # Calculate inter-item correlations only for items_passed_dist
    inter_corrs = calculate_inter_item_correlations(ratings_subset)
    
    # Find items that correlate > max_inter_corr with many other items
    # Map correlation indices (1-indexed in subset) back to original item IDs
    high_corr_counts = {}
    for (i1_subset, i2_subset), corr in inter_corrs.items():
        if abs(corr) > max_inter_corr:
            # Map subset indices (1-indexed) back to original item IDs
            orig_i1 = items_passed_dist[i1_subset - 1]
            orig_i2 = items_passed_dist[i2_subset - 1]
            high_corr_counts[orig_i1] = high_corr_counts.get(orig_i1, 0) + 1
            high_corr_counts[orig_i2] = high_corr_counts.get(orig_i2, 0) + 1
    
    # Adaptive threshold adjustment for Step 3
    # Target: 35-50 items enter EFA (preferred: 40-45 items)
    # But also need to consider sample size: EFA requires items < samples
    # For matrix stability, use max(0.8 * n_samples, 35) as upper bound, capped at 50
    max_items_for_efa = min(50, max_items_for_efa_sample_limit)  # Maximum items to allow (limit by sample size)
    max_items_for_efa = max(max_items_for_efa, 35)  # At least 35 for sufficient selection space
    min_items_for_efa = 35  # Minimum target items for EFA
    # Target: 75% of samples (if samples are few) or 42 (if samples are many), at least 35
    target_items_for_efa = min(42, max(int(0.75 * n_participants), 35))
    print(f"    [Stage 1] Adjusted targets: max={max_items_for_efa}, min={min_items_for_efa}, target={target_items_for_efa} items")
    
    # Try different thresholds to achieve target range (35-50 items, preferred: 40-45)
    # Start with very lenient thresholds and work backwards if needed
    high_corr_thresholds = [50, 40, 30, 25, 20, 15, 12, 10, 8, 5, 3]  # Start lenient, work to strict
    items_passed_inter = []
    actual_threshold_used = None
    
    # Strategy: Find threshold that gets us closest to target_items_for_efa (35-50 range, preferred: 40-45)
    best_count = 0
    best_threshold = None
    best_distance_to_target = float('inf')
    
    # Evaluate all thresholds to find best match for target range
    for threshold in high_corr_thresholds:
        candidate_items = [
            item_id for item_id in items_passed_dist
            if high_corr_counts.get(item_id, 0) < threshold  # Remove items with >= threshold high correlations
        ]
        
        # Calculate distance to target
        distance_to_target = abs(len(candidate_items) - target_items_for_efa)
        
        # Prefer items in target range (35-50, preferred: 40-45), or closest to target
        if min_items_for_efa <= len(candidate_items) <= max_items_for_efa:
            # In target range - prefer closest to target_items_for_efa
            if distance_to_target < best_distance_to_target:
                best_threshold = threshold
                best_count = len(candidate_items)
                best_distance_to_target = distance_to_target
                items_passed_inter = candidate_items
        elif len(candidate_items) > max_items_for_efa:
            # Above max - only use if we haven't found anything better
            if best_threshold is None:
                best_threshold = threshold
                best_count = len(candidate_items)
                best_distance_to_target = distance_to_target
                items_passed_inter = candidate_items
        elif len(candidate_items) < min_items_for_efa:
            # Below target - only use if closest to target and we haven't found anything in range
            if best_threshold is None or (best_count < min_items_for_efa and distance_to_target < best_distance_to_target):
                best_threshold = threshold
                best_count = len(candidate_items)
                best_distance_to_target = distance_to_target
                items_passed_inter = candidate_items
    
    if best_threshold is not None:
        actual_threshold_used = best_threshold
    
    # If we still don't have enough items, use the most lenient approach possible
    if len(items_passed_inter) < min_items_for_efa:
        max_corr_count = max(high_corr_counts.values()) if high_corr_counts else 0
        # Use threshold that allows all items (threshold = max count + 1)
        actual_threshold_used = max_corr_count + 1
        items_passed_inter = items_passed_dist
        print(f"    [Step 3] WARNING: Using most lenient threshold ({actual_threshold_used}) to maximize items for EFA")
        print(f"    [Step 3] WARNING: Only {len(items_passed_inter)} items available (target: {min_items_for_efa}-{max_items_for_efa})")
    
    if actual_threshold_used is None:
        actual_threshold_used = 50  # Default to lenient threshold
    
    # Only limit items if we have too many (> max_items_for_efa)
    if len(items_passed_inter) > max_items_for_efa:
        # Sort items by correlation count (ascending) and select top max_items_for_efa
        items_with_counts = [(item_id, high_corr_counts.get(item_id, 0)) for item_id in items_passed_inter]
        items_with_counts.sort(key=lambda x: x[1])  # Sort by correlation count (ascending)
        items_passed_inter = [item_id for item_id, _ in items_with_counts[:max_items_for_efa]]
        print(f"    [Step 3] Limiting items to maximum ({max_items_for_efa}): {len(items_passed_inter)} items selected")
    
    if actual_threshold_used > 3:
        print(f"    [Step 3] Adaptive threshold adjustment applied:")
        print(f"      - Initial threshold: >= 3 high correlations (PETS: 'several')")
        print(f"      - Adjusted threshold: >= {actual_threshold_used} high correlations")
        print(f"      - Reason: Relaxed to reach target range ({min_items_for_efa}-{max_items_for_efa} items for EFA)")
    
    print(f"    [Step 3] {len(items_passed_inter)}/{len(items_passed_dist)} items passed inter-item correlation check (removed items with >= {actual_threshold_used} high correlations > {max_inter_corr})")
    
    if len(items_passed_inter) == 0:
        # Provide diagnostic information
        if items_passed_dist:
            print(f"    [DIAGNOSTIC] Inter-item correlation analysis:")
            high_corr_items = [item_id for item_id in items_passed_dist if high_corr_counts.get(item_id, 0) >= 3]
            print(f"      - Items with >= 3 high correlations (> {max_inter_corr}): {len(high_corr_items)}")
            if high_corr_items:
                print(f"      - Example: Item {high_corr_items[0]} has {high_corr_counts.get(high_corr_items[0], 0)} high correlations")
            print(f"    [SUGGESTION] Consider:")
            print(f"      1. Lowering max_inter_corr threshold (current: {max_inter_corr})")
            print(f"      2. Or allowing more high correlations (current: < 3, could try < 5)")
        raise ValueError("No items passed inter-item correlation check. Cannot proceed with EFA.")
    
    # Check minimum items required for EFA
    if len(items_passed_inter) < min_items_for_efa:
        print(f"    [Stage 1] WARNING: Only {len(items_passed_inter)} item(s) passed all preliminary checks (target: {min_items_for_efa}-{max_items_for_efa})")
        print(f"    [Stage 1] Proceeding with available items")
        if len(items_passed_inter) < 3:
            raise ValueError(f"Only {len(items_passed_inter)} item(s) passed all preliminary checks. EFA requires at least 3 items.")
    
    print(f"    [Stage 1] COMPLETE: {len(items_passed_inter)} items ready for EFA (target: {min_items_for_efa}-{max_items_for_efa})")
    
    return {
        "items_passed_inter": items_passed_inter,
        "item_total_corrs": item_total_corrs,
        "skew_kurt_stats": skew_kurt_stats,
        "inter_corrs": inter_corrs,
        "high_corr_counts": high_corr_counts,
        "filtering_steps": {
            "initial_n_items": n_items,
            "after_item_total_corr": len(items_passed_corr),
            "after_distribution_check": len(items_passed_dist),
            "after_inter_corr": len(items_passed_inter)
        },
        "actual_thresholds": {
            "min_item_total_corr": actual_min_item_total_corr,
            "max_skewness": actual_max_skewness,
            "max_kurtosis": actual_max_kurtosis,
            "inter_corr_threshold": actual_threshold_used
        }
    }


def _perform_stage2_efa_cfa(
    ratings_matrix: np.ndarray,
    items_passed_inter: List[int],
    high_corr_counts: Dict[int, int],
    min_factor_loading: float,
    n_factors: Optional[int],
    use_cfa: bool,
    cfa_rmsea_threshold: float,
    cfa_tli_threshold: float,
    cfa_cfi_threshold: float,
    cfa_srmr_threshold: float,
    min_items_per_factor: int,
    enable_factor_balance: bool = True,
    max_items_per_factor: Optional[int] = None,
    target_range: Optional[Tuple[int, int]] = None,
    min_factor_loading_at_upper_bound: bool = False
) -> Dict[str, Any]:
    """
    Stage 2: Perform EFA + CFA on items that passed Stage 1.
    
    This stage only adjusts min_factor_loading to control final item count.
    Does NOT repeat Step 1-3 filtering.
    
    Args:
        ratings_matrix: Full ratings matrix
        items_passed_inter: List of item IDs that passed Stage 1 (Step 1-3)
        high_corr_counts: Dict mapping item_id to count of high correlations (from Stage 1)
        min_factor_loading: Minimum factor loading threshold
        ... (other CFA parameters)
        enable_factor_balance: Whether to balance factors after EFA (default: True)
            If True, will limit items per factor to max_items_per_factor (or calculate automatically)
        max_items_per_factor: Maximum items per factor for balancing (default: None = auto-calculate)
            If None and enable_factor_balance=True, will calculate as (total_items / n_factors) * 1.5
    
    Returns:
        Dictionary with EFA+CFA results including selected_items
    """
    if not FACTOR_ANALYZER_AVAILABLE:
        raise ImportError("factor_analyzer not available. Cannot perform EFA.")
    
    print(f"    [Stage 2] Starting EFA + CFA (using {len(items_passed_inter)} items from Stage 1)...")
    
    # Check that items don't exceed samples (causes matrix singularity issues)
    n_samples, _ = ratings_matrix.shape
    if len(items_passed_inter) > n_samples:
        # Limit items to sample size (select items with lowest correlation counts from Step 3)
        print(f"    [Stage 2] WARNING: {len(items_passed_inter)} items exceed {n_samples} samples. Limiting to {n_samples} items to avoid matrix issues.")
        items_with_counts = [(item_id, high_corr_counts.get(item_id, 0)) for item_id in items_passed_inter]
        items_with_counts.sort(key=lambda x: x[1])  # Sort by correlation count (ascending)
        items_passed_inter = [item_id for item_id, _ in items_with_counts[:n_samples]]
        print(f"    [Stage 2] Selected {len(items_passed_inter)} items with lowest inter-item correlations")
    
    # Create subset of ratings matrix for items that passed Stage 1
    item_indices = [item_id - 1 for item_id in items_passed_inter]
    ratings_subset = ratings_matrix[:, item_indices]
    
    # Validate ratings_subset shape
    n_samples, n_items_subset = ratings_subset.shape
    if n_items_subset < 3:
        raise ValueError(f"Ratings subset has only {n_items_subset} items, but EFA requires at least 3 items.")
    
    # Handle missing values: impute with column mean before computing correlations
    # This prevents NaN values in correlation matrix
    ratings_subset_clean = ratings_subset.copy()
    for col_idx in range(ratings_subset_clean.shape[1]):
        col = ratings_subset_clean[:, col_idx]
        nan_mask = np.isnan(col)
        if np.any(nan_mask):
            col_mean = np.nanmean(col)
            if not np.isnan(col_mean) and np.isfinite(col_mean):
                ratings_subset_clean[nan_mask, col_idx] = col_mean
            else:
                # If column is all NaN, use neutral value (50.0 for 0-100 scale)
                ratings_subset_clean[nan_mask, col_idx] = 50.0
    
    # Pre-check correlation matrix to avoid singularity issues
    # Use iterative reduction until matrix condition is acceptable (based on condition number)
    max_precheck_iterations = 5
    precheck_iteration = 0
    matrix_acceptable = False
    
    while precheck_iteration < max_precheck_iterations and not matrix_acceptable:
        # Use cleaned ratings subset (always use ratings_subset_clean which has NaN imputed)
        corr_matrix_precheck = np.corrcoef(ratings_subset_clean.T)
        
        # Check for NaN or Inf values in correlation matrix
        has_nan_or_inf = np.any(np.isnan(corr_matrix_precheck)) or np.any(np.isinf(corr_matrix_precheck))
        
        if has_nan_or_inf:
            print(f"    [Stage 2] WARNING: Correlation matrix contains NaN or Inf values. Reducing items...")
            # Skip condition number check, directly reduce items
            cond_num_precheck = float('inf')
            corr_det_precheck = 0.0
        else:
            # Try to compute determinant first (simpler check)
            try:
                corr_det_precheck = np.linalg.det(corr_matrix_precheck)
                if not np.isfinite(corr_det_precheck):
                    corr_det_precheck = 0.0
            except (np.linalg.LinAlgError, ValueError):
                corr_det_precheck = 0.0
            
            # Check condition number (more robust than determinant alone)
            # Condition number measures sensitivity to input errors
            # High condition number (>1e10) indicates near-singular matrix
            # Note: If determinant is exactly 0 or very small, condition number may fail to compute
            try:
                cond_num_precheck = np.linalg.cond(corr_matrix_precheck)
                # Check if condition number is valid (not NaN or Inf)
                if not np.isfinite(cond_num_precheck):
                    cond_num_precheck = float('inf')
            except (np.linalg.LinAlgError, ValueError, RuntimeError) as e:
                # Matrix is too singular to compute condition number
                # This can happen when matrix is exactly singular (determinant = 0)
                cond_num_precheck = float('inf')
                print(f"    [Stage 2] Cannot compute condition number (matrix too singular): {e}")
        
        # Matrix is acceptable if condition number < 1e10 (less strict than perform_efa's 1e12)
        # This allows some buffer before hitting the actual EFA check
        if cond_num_precheck < 1e10 and np.isfinite(cond_num_precheck):
            matrix_acceptable = True
            if precheck_iteration > 0:
                print(f"    [Stage 2] Matrix condition improved after {precheck_iteration} iteration(s) (cond={cond_num_precheck:.2e})")
        else:
            # Matrix is near-singular, reduce items
            cond_str = f"{cond_num_precheck:.2e}" if np.isfinite(cond_num_precheck) else "inf"
            det_str = f"{corr_det_precheck:.2e}" if np.isfinite(corr_det_precheck) else "0.00e+00"
            print(f"    [Stage 2] WARNING: Correlation matrix is ill-conditioned (det={det_str}, cond={cond_str}). Reducing items to improve matrix condition.")
            
            # Calculate inter-item correlations to identify redundant items
            # Use cleaned ratings to avoid NaN issues
            inter_corrs_subset = calculate_inter_item_correlations(ratings_subset_clean)
            
            # Find items with highest average correlation (most redundant)
            item_avg_corrs = {}
            for (i1, i2), corr in inter_corrs_subset.items():
                item_avg_corrs[i1] = item_avg_corrs.get(i1, []) + [abs(corr)]
                item_avg_corrs[i2] = item_avg_corrs.get(i2, []) + [abs(corr)]
            
            # Calculate average correlation for each item
            item_avg_corr_values = {
                item_idx: np.mean(corrs) if corrs else 0
                for item_idx, corrs in item_avg_corrs.items()
            }
            
            # Reduce items: keep items with lower average correlations (more independent)
            # More aggressive reduction: target 60-70% of current items, or max(0.6 * n_samples, 25)
            reduction_factor = 0.7 if precheck_iteration == 0 else 0.85  # Reduce by 30% first time, then 15% per iteration
            target_reduced = max(int(n_items_subset * reduction_factor), int(0.6 * n_samples), 25)
            target_reduced = min(target_reduced, n_items_subset - 1)  # At least remove 1 item
            
            if n_items_subset > target_reduced:
                items_with_avg_corr = [
                    (items_passed_inter[subset_idx - 1], item_avg_corr_values.get(subset_idx, 0)) 
                    for subset_idx in range(1, len(items_passed_inter) + 1)
                ]
                items_with_avg_corr.sort(key=lambda x: x[1])  # Sort by average correlation (ascending)
                items_passed_inter = [item_id for item_id, _ in items_with_avg_corr[:target_reduced]]
                
                # Recreate ratings_subset
                item_indices = [item_id - 1 for item_id in items_passed_inter]
                ratings_subset = ratings_matrix[:, item_indices]
                # Clean the new subset
                for col_idx in range(ratings_subset.shape[1]):
                    col = ratings_subset[:, col_idx]
                    nan_mask = np.isnan(col)
                    if np.any(nan_mask):
                        col_mean = np.nanmean(col)
                        if not np.isnan(col_mean) and np.isfinite(col_mean):
                            ratings_subset[nan_mask, col_idx] = col_mean
                        else:
                            ratings_subset[nan_mask, col_idx] = 50.0
                ratings_subset_clean = ratings_subset  # Update cleaned version
                n_items_subset = len(items_passed_inter)
                print(f"    [Stage 2] Reduced to {n_items_subset} items with lowest average inter-item correlations (iteration {precheck_iteration + 1})")
                precheck_iteration += 1
            else:
                # Cannot reduce further
                print(f"    [Stage 2] WARNING: Cannot reduce items further. Matrix condition may still be problematic.")
                break
    
    if not matrix_acceptable and precheck_iteration >= max_precheck_iterations:
        print(f"    [Stage 2] WARNING: Matrix condition check reached max iterations ({max_precheck_iterations}). Proceeding with current {n_items_subset} items.")
    
    # Perform EFA (use cleaned ratings_subset to avoid NaN issues)
    print(f"    [Stage 2] Performing EFA with min_factor_loading={min_factor_loading:.3f}...")
    efa_results = perform_efa(
        ratings_subset_clean,  # Use cleaned version (NaN values already imputed)
        n_factors=n_factors,
        rotation="promax",
        min_factor_loading=min_factor_loading
    )
    
    # Map selected items back to original item IDs
    selected_item_indices = efa_results["selected_items"]
    efa_selected_items = [items_passed_inter[idx - 1] for idx in selected_item_indices if 1 <= idx <= len(items_passed_inter)]
    
    print(f"    [Stage 2] EFA selected {len(efa_selected_items)}/{len(items_passed_inter)} items (factor loading >= {min_factor_loading:.3f})")
    print(f"    [Stage 2] Extracted {efa_results['n_factors']} factors")
    
    if len(efa_selected_items) == 0:
        raise ValueError("EFA selected 0 items. Cannot proceed with CFA.")
    
    # Build factor structure from EFA results
    factor_structure = {}
    for idx, item_id in enumerate(efa_selected_items):
        if idx < len(selected_item_indices):
            subset_idx = selected_item_indices[idx]
            if subset_idx in efa_results["item_loadings"]:
                factor_structure[item_id] = efa_results["item_loadings"][subset_idx]["max_factor"]
            else:
                try:
                    subset_idx_alt = items_passed_inter.index(item_id) + 1
                    if subset_idx_alt in efa_results["item_loadings"]:
                        factor_structure[item_id] = efa_results["item_loadings"][subset_idx_alt]["max_factor"]
                    else:
                        factor_structure[item_id] = 0
                except ValueError:
                    factor_structure[item_id] = 0
        else:
            factor_structure[item_id] = 0
        
    # Factor balancing: Balance factors after EFA, before CFA (if enabled)
    items_removed_for_balance = []
    if enable_factor_balance and len(efa_selected_items) > 0:
        # Count items per factor
        factor_item_counts = {}
        for item_id in efa_selected_items:
            factor_idx = factor_structure.get(item_id, 0)
            factor_item_counts[factor_idx] = factor_item_counts.get(factor_idx, 0) + 1
        
        n_factors_detected = len(factor_item_counts)
        max_items = max(factor_item_counts.values()) if factor_item_counts else 0
        min_items = min(factor_item_counts.values()) if factor_item_counts else 0
        
        # Check if balancing is needed (max/min > 1.5 indicates imbalance)
        # Lowered from 2.0 to 1.5 to trigger balancing earlier and prevent severe imbalance
        if n_factors_detected > 1 and max_items > 0 and min_items > 0:
            imbalance_ratio = max_items / min_items if min_items > 0 else float('inf')
            
            if imbalance_ratio > 1.5:
                # Calculate target max items per factor
                if max_items_per_factor is None:
                    # Auto-calculate: (total_items / n_factors) * 1.5
                    # This allows some flexibility while preventing severe imbalance
                    avg_items_per_factor = len(efa_selected_items) / n_factors_detected
                    target_max_per_factor = int(avg_items_per_factor * 1.5)
                    target_max_per_factor = max(target_max_per_factor, min_items_per_factor + 1)  # At least min+1
                    
                    # If min_factor_loading is at upper bound and we still have too many items,
                    # use more aggressive balancing based on target range
                    if min_factor_loading_at_upper_bound and target_range:
                        target_min, target_max = target_range
                        # If current items exceed target_max, calculate based on target range
                        if len(efa_selected_items) > target_max:
                            # Calculate ideal max per factor based on target_max
                            # Distribute target_max across factors (allow some imbalance, but not extreme)
                            ideal_max_per_factor = int(target_max / n_factors_detected * 1.3)  # Allow 30% flexibility
                            ideal_max_per_factor = max(ideal_max_per_factor, min_items_per_factor + 1)
                            # Use the more aggressive (smaller) target
                            target_max_per_factor = min(target_max_per_factor, ideal_max_per_factor)
                            print(f"    [Stage 2] min_factor_loading at upper bound ({min_factor_loading:.2f}) with {len(efa_selected_items)} items > target_max ({target_max})")
                            print(f"    [Stage 2] Using aggressive balancing: target_max_per_factor = {target_max_per_factor} (based on target range)")
                else:
                    target_max_per_factor = max(max_items_per_factor, min_items_per_factor + 1)
                
                print(f"    [Stage 2] Factor imbalance detected (max={max_items}, min={min_items}, ratio={imbalance_ratio:.2f})")
                print(f"    [Stage 2] Balancing factors: target max items per factor = {target_max_per_factor}")
                
                # For factors exceeding target, remove items with lowest loadings
                for factor_idx, count in factor_item_counts.items():
                    if count > target_max_per_factor:
                        # Find items in this factor
                        factor_items = [item_id for item_id in efa_selected_items 
                                      if factor_structure.get(item_id) == factor_idx]
                        
                        # Get loadings for these items from EFA results
                        factor_items_with_loadings = []
                        for item_id in factor_items:
                            # Find the subset index for this item in EFA results
                            # efa_results["item_loadings"] uses subset indices (1-indexed) as keys
                            subset_idx = None
                            try:
                                # Find which selected_item_indices corresponds to this item_id
                                # selected_item_indices are subset indices (1-indexed)
                                item_idx_in_selected = efa_selected_items.index(item_id)
                                if item_idx_in_selected < len(selected_item_indices):
                                    subset_idx = selected_item_indices[item_idx_in_selected]
                                else:
                                    # Fallback: use position in items_passed_inter
                                    item_pos = items_passed_inter.index(item_id)
                                    subset_idx = item_pos + 1
                            except (ValueError, IndexError):
                                continue
                            
                            # Get loading from EFA results (key is subset index, 1-indexed)
                            if subset_idx and subset_idx in efa_results["item_loadings"]:
                                loading = efa_results["item_loadings"][subset_idx]["max_loading"]
                                factor_items_with_loadings.append((item_id, loading))
                        
                        if not factor_items_with_loadings:
                            continue
                        
                        # Sort by loading (descending), keep top target_max_per_factor
                        factor_items_with_loadings.sort(key=lambda x: x[1], reverse=True)
                        items_to_keep = {item_id for item_id, _ in factor_items_with_loadings[:target_max_per_factor]}
                        
                        # Identify items to remove
                        items_to_remove = [item_id for item_id in factor_items 
                                         if item_id not in items_to_keep]
                        
                        if items_to_remove:
                            removed_count = len(items_to_remove)
                            print(f"    [Stage 2] Factor {factor_idx}: removing {removed_count} items (from {count} to {target_max_per_factor})")
                            items_removed_for_balance.extend(items_to_remove)
                            
                            # Remove from efa_selected_items and factor_structure
                            efa_selected_items = [item_id for item_id in efa_selected_items 
                                                if item_id not in items_to_remove]
                            for item_id in items_to_remove:
                                factor_structure.pop(item_id, None)
                
                if items_removed_for_balance:
                    # Recalculate factor distribution after balancing
                    factor_item_counts_after = {}
                    for item_id in efa_selected_items:
                        factor_idx = factor_structure.get(item_id, 0)
                        factor_item_counts_after[factor_idx] = factor_item_counts_after.get(factor_idx, 0) + 1
                    
                    # Check if any factor has fewer than min_items_per_factor items
                    # This is a critical issue that needs to be addressed
                    factors_below_min = {f: c for f, c in factor_item_counts_after.items() 
                                        if c < min_items_per_factor}
                    
                    if factors_below_min:
                        print(f"    [Stage 2] WARNING: Some factors have fewer than {min_items_per_factor} items after balancing:")
                        for factor_idx, count in factors_below_min.items():
                            print(f"    [Stage 2]   Factor {factor_idx}: {count} items (minimum required: {min_items_per_factor})")
                        print(f"    [Stage 2]   This may indicate severe data imbalance or insufficient items for this factor structure.")
                        print(f"    [Stage 2]   Consider: 1) Adjusting min_factor_loading, 2) Trying different n_factors, 3) Reviewing item generation")
                    
                    print(f"    [Stage 2] Balance complete: {len(items_removed_for_balance)} items removed")
                    print(f"    [Stage 2] Factor distribution after balance: {factor_item_counts_after}")
                    print(f"    [Stage 2] Remaining items: {len(efa_selected_items)}")
                    
                    # Calculate final imbalance ratio after balancing
                    if len(factor_item_counts_after) > 1:
                        final_max = max(factor_item_counts_after.values())
                        final_min = min(factor_item_counts_after.values())
                        final_ratio = final_max / final_min if final_min > 0 else float('inf')
                        print(f"    [Stage 2] Final imbalance ratio: {final_ratio:.2f}")
                        if final_ratio > 5.0:
                            print(f"    [Stage 2] WARNING: Final imbalance ratio ({final_ratio:.2f}) is still very high (>5.0)")
                            print(f"    [Stage 2]   This result may be rejected in multi-factor iteration selection.")
    
    # Additional reduction: if min_factor_loading at upper bound and items still exceed target, reduce further
    if min_factor_loading_at_upper_bound and target_range and len(efa_selected_items) > 0:
        target_min, target_max = target_range
        if len(efa_selected_items) > target_max:
            # Calculate how many items to remove
            excess_items = len(efa_selected_items) - target_max
            
            # Get all items with their loadings from factor_structure and efa_results
            all_items_with_loadings = []
            for item_id in efa_selected_items:
                # Find subset_idx for this item (needed to access efa_results["item_loadings"])
                # First try: use position in original efa_selected_items before balancing
                # We need to map back to original EFA selected items
                try:
                    # Find the original subset_idx by checking item_loadings keys
                    # The keys are subset indices (1-indexed) from items_passed_inter
                    item_pos_in_inter = items_passed_inter.index(item_id)
                    subset_idx = item_pos_in_inter + 1  # Convert to 1-indexed
                    
                    # Check if this subset_idx corresponds to an item that was selected by EFA
                    # by checking if it's in selected_item_indices
                    if subset_idx in selected_item_indices:
                        if subset_idx in efa_results["item_loadings"]:
                            loading = efa_results["item_loadings"][subset_idx]["max_loading"]
                            all_items_with_loadings.append((item_id, loading))
                except (ValueError, KeyError):
                    # If we can't find the loading, skip this item (shouldn't happen)
                    continue
            
            if all_items_with_loadings:
                # Sort by loading (ascending) to remove lowest-loading items first
                all_items_with_loadings.sort(key=lambda x: x[1])
                
                # Remove items while ensuring min_items_per_factor constraint
                items_to_remove_additional = []
                factor_item_counts_current = {}
                for item_id in efa_selected_items:
                    factor_idx = factor_structure.get(item_id, 0)
                    factor_item_counts_current[factor_idx] = factor_item_counts_current.get(factor_idx, 0) + 1
                
                for item_id, loading in all_items_with_loadings:
                    if len(items_to_remove_additional) >= excess_items:
                        break
                    
                    # Check if removing this item would violate min_items_per_factor
                    factor_idx = factor_structure.get(item_id, 0)
                    if factor_item_counts_current.get(factor_idx, 0) > min_items_per_factor:
                        items_to_remove_additional.append(item_id)
                        factor_item_counts_current[factor_idx] -= 1
                
                if items_to_remove_additional:
                    print(f"    [Stage 2] min_factor_loading at upper bound: removing {len(items_to_remove_additional)} additional items to reach target_max ({target_max})")
                    efa_selected_items = [item_id for item_id in efa_selected_items 
                                        if item_id not in items_to_remove_additional]
                    for item_id in items_to_remove_additional:
                        factor_structure.pop(item_id, None)
                    items_removed_for_balance.extend(items_to_remove_additional)
    
    # Perform CFA if requested
    cfa_results = None
    final_selected_items = efa_selected_items
    
    if use_cfa:
        print(f"    [Stage 2] Performing CFA...")
        try:
            # Create ratings matrix for CFA (only EFA-selected items)
            cfa_item_indices = [item_id - 1 for item_id in efa_selected_items]
            
            if max(cfa_item_indices) >= ratings_matrix.shape[1] or min(cfa_item_indices) < 0:
                raise ValueError(f"Invalid item indices for CFA")
            
            cfa_ratings = ratings_matrix[:, cfa_item_indices]
            
            # Remap factor_structure to use 0-indexed column indices
            cfa_factor_structure = {}
            for idx, item_id in enumerate(efa_selected_items):
                if item_id in factor_structure:
                    cfa_factor_structure[idx] = factor_structure[item_id]
                else:
                    cfa_factor_structure[idx] = 0
            
            # Determine CFA max_iterations: increase if min_factor_loading at upper bound
            cfa_max_iterations = 3
            if min_factor_loading_at_upper_bound and target_range:
                # Increase iterations when at upper bound to allow more item removal
                cfa_max_iterations = 6  # Allow more iterations for aggressive item reduction
                print(f"    [Stage 2] min_factor_loading at upper bound: increasing CFA max_iterations to {cfa_max_iterations}")
            
            cfa_results = perform_cfa(
                cfa_ratings,
                cfa_factor_structure,
                max_iterations=cfa_max_iterations,
                rmsea_threshold=cfa_rmsea_threshold,
                tli_threshold=cfa_tli_threshold,
                cfi_threshold=cfa_cfi_threshold,
                srmr_threshold=cfa_srmr_threshold,
                min_items_per_factor=min_items_per_factor,
                target_range=target_range if min_factor_loading_at_upper_bound else None
            )
            
            # Map CFA selected items back to original item IDs
            cfa_selected_indices = cfa_results["selected_items"]
            final_selected_items = [efa_selected_items[idx] for idx in cfa_selected_indices if 0 <= idx < len(efa_selected_items)]
            print(f"    [Stage 2] CFA selected {len(final_selected_items)}/{len(efa_selected_items)} items")
            print(f"    [Stage 2] Fit indices: RMSEA={cfa_results['fit_indices']['RMSEA']:.4f}, TLI={cfa_results['fit_indices']['TLI']:.4f}, CFI={cfa_results['fit_indices']['CFI']:.4f}, SRMR={cfa_results['fit_indices']['SRMR']:.4f}")
            
            # Rebuild factor_structure for final selected items
            final_factor_structure = {}
            for item_id in final_selected_items:
                if item_id in factor_structure:
                    final_factor_structure[item_id] = factor_structure[item_id]
            
            # Post-CFA: Aggressive reduction if still exceeding target range
            if target_range and len(final_selected_items) > target_range[1]:
                target_min, target_max = target_range
                excess = len(final_selected_items) - target_max
                print(f"    [Stage 2] Post-CFA: {len(final_selected_items)} items still exceed target_max ({target_max}), need to remove {excess} items")
                
                # Get factor distribution
                factor_item_counts_post_cfa = {}
                for item_id in final_selected_items:
                    factor_idx = final_factor_structure.get(item_id, 0)
                    factor_item_counts_post_cfa[factor_idx] = factor_item_counts_post_cfa.get(factor_idx, 0) + 1
                
                # Get item loadings from CFA results
                cfa_item_loadings = cfa_results.get("factor_loadings", {})
                
                # Collect all items with their loadings, prioritizing from larger factors
                all_items_with_loadings_post_cfa = []
                for item_id in final_selected_items:
                    factor_idx = final_factor_structure.get(item_id, 0)
                    factor_count = factor_item_counts_post_cfa.get(factor_idx, 0)
                    
                    # Skip if removing would violate min_items_per_factor
                    if factor_count <= min_items_per_factor:
                        continue
                    
                    # Get loading from CFA results
                    loading = 1.0  # Default high loading if not found
                    if item_id in efa_selected_items:
                        efa_idx = efa_selected_items.index(item_id)
                        if efa_idx < len(cfa_selected_indices):
                            cfa_idx = cfa_selected_indices[efa_idx]
                            if cfa_idx in cfa_item_loadings:
                                loading = abs(cfa_item_loadings[cfa_idx])
                            else:
                                # Fallback to EFA loading
                                subset_idx = efa_idx + 1
                                if str(subset_idx) in efa_results.get("item_loadings", {}):
                                    loading = efa_results["item_loadings"][str(subset_idx)].get("max_loading", 1.0)
                    
                    # Priority score: lower loading = higher priority to remove
                    # Also prioritize items from larger factors (to balance)
                    max_factor_count = max(factor_item_counts_post_cfa.values()) if factor_item_counts_post_cfa else 1
                    factor_priority = factor_count / max_factor_count  # Higher for larger factors
                    priority_score = loading - (factor_priority * 0.1)  # Subtract factor priority to prefer removing from larger factors
                    
                    all_items_with_loadings_post_cfa.append((item_id, loading, priority_score, factor_idx))
                
                # Sort by priority score (ascending = remove first)
                all_items_with_loadings_post_cfa.sort(key=lambda x: x[2])
                
                # Remove items while respecting min_items_per_factor
                items_to_remove_post_cfa = []
                factor_counts_temp = factor_item_counts_post_cfa.copy()
                
                for item_id, loading, priority_score, factor_idx in all_items_with_loadings_post_cfa:
                    if len(items_to_remove_post_cfa) >= excess:
                        break
                    
                    # Check if removing would violate constraint
                    if factor_counts_temp.get(factor_idx, 0) > min_items_per_factor:
                        items_to_remove_post_cfa.append(item_id)
                        factor_counts_temp[factor_idx] -= 1
                
                if items_to_remove_post_cfa:
                    print(f"    [Stage 2] Post-CFA aggressive reduction: removing {len(items_to_remove_post_cfa)} items to reach target_max")
                    final_selected_items = [item_id for item_id in final_selected_items 
                                          if item_id not in items_to_remove_post_cfa]
                    for item_id in items_to_remove_post_cfa:
                        final_factor_structure.pop(item_id, None)
                    
                    # Recalculate distribution
                    final_factor_counts = {}
                    for item_id in final_selected_items:
                        factor_idx = final_factor_structure.get(item_id, 0)
                        final_factor_counts[factor_idx] = final_factor_counts.get(factor_idx, 0) + 1
                    print(f"    [Stage 2] Final distribution after post-CFA reduction: {final_factor_counts}")
                    print(f"    [Stage 2] Final item count: {len(final_selected_items)} (target: {target_min}-{target_max})")
                    
                    # Update factor_structure for return
                    factor_structure = final_factor_structure
            
            # Check factor balance after CFA and re-balance if needed (even if within target range)
            if enable_factor_balance and len(final_selected_items) > 0:
                factor_item_counts_after_cfa = {}
                for item_id in final_selected_items:
                    factor_idx = final_factor_structure.get(item_id, 0)
                    factor_item_counts_after_cfa[factor_idx] = factor_item_counts_after_cfa.get(factor_idx, 0) + 1
                
                n_factors_detected = len(factor_item_counts_after_cfa)
                if n_factors_detected > 1:
                    max_items_after = max(factor_item_counts_after_cfa.values())
                    min_items_after = min(factor_item_counts_after_cfa.values())
                    imbalance_ratio_after = max_items_after / min_items_after if min_items_after > 0 else float('inf')
                    
                    # Enhanced: Lower threshold from 2.0 to 1.5 for more aggressive balancing
                    if imbalance_ratio_after > 1.5:  # More aggressive threshold
                        print(f"    [Stage 2] Factor imbalance after CFA (max={max_items_after}, min={min_items_after}, ratio={imbalance_ratio_after:.2f})")
                        print(f"    [Stage 2] Re-balancing factors...")
                        
                        # Calculate target max items per factor (more aggressive: 1.3x instead of 1.5x)
                        avg_items = len(final_selected_items) / n_factors_detected
                        if max_items_per_factor is None:
                            # More aggressive: use 1.3x multiplier instead of 1.5x
                            target_max_per_factor = int(avg_items * 1.3)
                            target_max_per_factor = max(target_max_per_factor, min_items_per_factor + 1)
                        else:
                            target_max_per_factor = max(max_items_per_factor, min_items_per_factor + 1)
                        
                        print(f"    [Stage 2] Target max items per factor: {target_max_per_factor} (avg: {avg_items:.2f})")
                        
                        # Enhanced: Always try to get loadings, prefer CFA but fallback to EFA
                        cfa_item_loadings = cfa_results.get("factor_loadings", {}) if cfa_results else {}
                        
                        # Remove excess items from factors exceeding target
                        items_to_remove_post_cfa_balance = []
                        for factor_idx, count in factor_item_counts_after_cfa.items():
                            if count > target_max_per_factor:
                                # Find items in this factor
                                factor_items = [item_id for item_id in final_selected_items 
                                              if final_factor_structure.get(item_id) == factor_idx]
                                
                                # Enhanced: Get loadings with improved fallback logic
                                factor_items_with_loadings = []
                                for item_id in factor_items:
                                    loading = None
                                    
                                    # Try CFA loadings first
                                    if item_id in efa_selected_items and cfa_item_loadings:
                                        efa_idx = efa_selected_items.index(item_id)
                                        if efa_idx < len(cfa_selected_indices):
                                            cfa_idx = cfa_selected_indices[efa_idx]
                                            if cfa_idx in cfa_item_loadings:
                                                loading = abs(cfa_item_loadings[cfa_idx])
                                    
                                    # Fallback to EFA loadings (always available)
                                    if loading is None and item_id in efa_selected_items:
                                        efa_idx = efa_selected_items.index(item_id)
                                        subset_idx = efa_idx + 1
                                        if str(subset_idx) in efa_results.get("item_loadings", {}):
                                            loading = efa_results["item_loadings"][str(subset_idx)].get("max_loading", 0.0)
                                    
                                    # If still no loading found, use default low priority
                                    if loading is None:
                                        loading = 0.0  # Lowest priority for items without loadings
                                    
                                    factor_items_with_loadings.append((item_id, loading))
                                
                                if factor_items_with_loadings:
                                    # Sort by loading (ascending), remove lowest
                                    factor_items_with_loadings.sort(key=lambda x: x[1])
                                    # Calculate how many items to remove
                                    excess_count = count - target_max_per_factor
                                    # Ensure we don't violate min_items_per_factor
                                    items_to_remove = []
                                    for item_id, loading_val in factor_items_with_loadings:
                                        if len(items_to_remove) >= excess_count:
                                            break
                                        # Check if removing would violate constraint
                                        remaining_count = count - len(items_to_remove) - 1
                                        if remaining_count >= min_items_per_factor:
                                            items_to_remove.append(item_id)
                                    
                                    items_to_remove_post_cfa_balance.extend(items_to_remove)
                        
                        if items_to_remove_post_cfa_balance:
                            print(f"    [Stage 2] Post-CFA balancing: removing {len(items_to_remove_post_cfa_balance)} items")
                            final_selected_items = [item_id for item_id in final_selected_items 
                                                  if item_id not in items_to_remove_post_cfa_balance]
                            for item_id in items_to_remove_post_cfa_balance:
                                final_factor_structure.pop(item_id, None)
                            
                            # Recalculate distribution
                            final_factor_counts = {}
                            for item_id in final_selected_items:
                                factor_idx = final_factor_structure.get(item_id, 0)
                                final_factor_counts[factor_idx] = final_factor_counts.get(factor_idx, 0) + 1
                            
                            # Recalculate imbalance ratio after balancing
                            max_items_final = max(final_factor_counts.values()) if final_factor_counts else 0
                            min_items_final = min(final_factor_counts.values()) if final_factor_counts else 0
                            imbalance_ratio_final = max_items_final / min_items_final if min_items_final > 0 else float('inf')
                            
                            print(f"    [Stage 2] Final factor distribution after post-CFA balance: {final_factor_counts}")
                            print(f"    [Stage 2] Final imbalance ratio: {imbalance_ratio_final:.2f}")
                            
                            # Update factor_structure for return
                            factor_structure = final_factor_structure
                    
        except Exception as e:
            print(f"    [Stage 2] CFA failed: {e}, using EFA results only")
            import traceback
            traceback.print_exc()
        
    return {
        "selected_items": sorted(final_selected_items),
        "efa_results": efa_results,
        "cfa_results": cfa_results,
        "factor_structure": factor_structure,
        "efa_selected_items": sorted(efa_selected_items),
        "n_efa_items": len(efa_selected_items),
        "n_final_items": len(final_selected_items),
        "items_removed_for_balance": sorted(items_removed_for_balance) if items_removed_for_balance else []
    }


def _calculate_factor_balance_score(factor_structure: Dict[int, int]) -> Dict[str, Any]:
    """
    Calculate balance score for factor structure.
    
    Args:
        factor_structure: Dictionary mapping item_id -> factor_idx
        
    Returns:
        Dictionary with balance metrics:
        - imbalance_ratio: max/min ratio (lower is better, 1.0 is perfect)
        - balance_score: normalized score (0-1, higher is better)
        - max_count: maximum items in any factor
        - min_count: minimum items in any factor
        - factor_counts: count per factor
    """
    if not factor_structure:
        return {
            "imbalance_ratio": float('inf'),
            "balance_score": 0.0,
            "max_count": 0,
            "min_count": 0,
            "factor_counts": {}
        }
    
    # Count items per factor
    factor_counts = {}
    for factor_idx in factor_structure.values():
        factor_counts[factor_idx] = factor_counts.get(factor_idx, 0) + 1
    
    if len(factor_counts) == 0:
        return {
            "imbalance_ratio": float('inf'),
            "balance_score": 0.0,
            "max_count": 0,
            "min_count": 0,
            "factor_counts": {}
        }
    
    max_count = max(factor_counts.values())
    min_count = min(factor_counts.values())
    
    # Calculate imbalance ratio (lower is better)
    imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
    
    # Calculate balance score (0-1, higher is better)
    # Perfect balance (ratio = 1.0) -> score = 1.0
    # Ratio increases -> score decreases (using inverse exponential decay)
    if imbalance_ratio == 1.0:
        balance_score = 1.0
    elif imbalance_ratio >= 10.0:
        balance_score = 0.0
    else:
        # Exponential decay: score = exp(-(ratio-1) * 0.5)
        # ratio=1 -> score=1.0, ratio=2 -> score≈0.61, ratio=4 -> score≈0.22
        balance_score = np.exp(-(imbalance_ratio - 1.0) * 0.5)
    
    return {
        "imbalance_ratio": float(imbalance_ratio),
        "balance_score": float(balance_score),
        "max_count": max_count,
        "min_count": min_count,
        "factor_counts": factor_counts
    }


def _run_single_factor_count_stage2(
    ratings_matrix: np.ndarray,
    items_passed_inter: List[int],
    high_corr_counts: Dict[int, int],
    min_factor_loading: float,
    n_factors_try: int,
    use_cfa: bool,
    cfa_rmsea_threshold: float,
    cfa_tli_threshold: float,
    cfa_cfi_threshold: float,
    cfa_srmr_threshold: float,
    min_items_per_factor: int,
    enable_factor_balance: bool,
    max_items_per_factor: Optional[int],
    target_range: Optional[Tuple[int, int]],
    adaptive_factor_loading: bool,
    max_adaptive_iterations: int
) -> Optional[Dict[str, Any]]:
    """
    Run complete Stage 2 process for a specific number of factors.
    
    This function encapsulates the adaptive_factor_loading iteration logic
    but uses n_factors_try instead of n_factors.
    
    Args:
        ratings_matrix: Full ratings matrix
        items_passed_inter: List of item IDs that passed Stage 1
        high_corr_counts: Dict mapping item_id to count of high correlations
        min_factor_loading: Initial minimum factor loading threshold
        n_factors_try: Number of factors to try (replaces n_factors)
        ... (other parameters same as select_items_by_efa_cfa)
        
    Returns:
        Stage 2 result dictionary or None if failed
    """
    if not adaptive_factor_loading or not target_range:
        # Non-adaptive case: run Stage 2 once
        try:
            stage2_result = _perform_stage2_efa_cfa(
                ratings_matrix=ratings_matrix,
                items_passed_inter=items_passed_inter,
                high_corr_counts=high_corr_counts,
                min_factor_loading=min_factor_loading,
                n_factors=n_factors_try,
                use_cfa=use_cfa,
                cfa_rmsea_threshold=cfa_rmsea_threshold,
                cfa_tli_threshold=cfa_tli_threshold,
                cfa_cfi_threshold=cfa_cfi_threshold,
                cfa_srmr_threshold=cfa_srmr_threshold,
                min_items_per_factor=min_items_per_factor,
                enable_factor_balance=enable_factor_balance,
                max_items_per_factor=max_items_per_factor,
                target_range=target_range,
                min_factor_loading_at_upper_bound=False
            )
            return stage2_result
        except Exception as e:
            print(f"    [Single Factor Count] Failed with {n_factors_try} factors: {e}")
            return None
    
    # Adaptive case: iterate to find best min_factor_loading
    target_min, target_max = target_range
    target_center = (target_min + target_max) / 2.0
    current_min_factor_loading = min_factor_loading
    adaptive_iteration = 0
    best_result = None
    best_result_count = None
    best_distance_to_center = float('inf')
    
    while adaptive_iteration < max_adaptive_iterations:
        adaptive_iteration += 1
        
        try:
            min_factor_loading_at_bound = (current_min_factor_loading >= 0.95)
            
            stage2_result = _perform_stage2_efa_cfa(
                ratings_matrix=ratings_matrix,
                items_passed_inter=items_passed_inter,
                high_corr_counts=high_corr_counts,
                min_factor_loading=current_min_factor_loading,
                n_factors=n_factors_try,  # Use n_factors_try instead of n_factors
                use_cfa=use_cfa,
                cfa_rmsea_threshold=cfa_rmsea_threshold,
                cfa_tli_threshold=cfa_tli_threshold,
                cfa_cfi_threshold=cfa_cfi_threshold,
                cfa_srmr_threshold=cfa_srmr_threshold,
                min_items_per_factor=min_items_per_factor,
                enable_factor_balance=enable_factor_balance,
                max_items_per_factor=max_items_per_factor,
                target_range=target_range,
                min_factor_loading_at_upper_bound=min_factor_loading_at_bound
            )
            
            n_selected = len(stage2_result["selected_items"])
            distance_to_center = abs(n_selected - target_center)
            
            # Track best result
            is_in_range = target_min <= n_selected <= target_max
            is_current_best = False
            
            if best_result is None:
                is_current_best = True
            elif is_in_range:
                if target_min <= best_result_count <= target_max:
                    is_current_best = distance_to_center < best_distance_to_center
                else:
                    is_current_best = True
            else:
                if not (target_min <= best_result_count <= target_max):
                    is_current_best = distance_to_center < best_distance_to_center
            
            if is_current_best:
                best_result = stage2_result
                best_result_count = n_selected
                best_distance_to_center = distance_to_center
            
            # Adjust min_factor_loading for next iteration
            if n_selected > target_max:
                gap = n_selected - target_max
                adjustment = min(0.03 + (gap / 5) * 0.01, 0.10)
                current_min_factor_loading = min(0.95, current_min_factor_loading + adjustment)
                if current_min_factor_loading >= 0.95:
                    break  # Stop if at upper bound
            elif n_selected < target_min:
                gap = target_min - n_selected
                adjustment = min(0.03 + (gap / 5) * 0.01, 0.10)
                current_min_factor_loading = max(0.50, current_min_factor_loading - adjustment)
                if current_min_factor_loading < 0.50:
                    break  # Stop if at lower bound
            elif target_min <= n_selected <= target_max:
                # Within range: adjust towards center
                if n_selected > target_center:
                    adjustment = 0.02
                    current_min_factor_loading = min(0.95, current_min_factor_loading + adjustment)
                elif n_selected < target_center:
                    adjustment = 0.02
                    current_min_factor_loading = max(0.50, current_min_factor_loading - adjustment)
                else:
                    # Exactly at center, can stop or continue
                    pass
        
        except Exception as e:
            print(f"    [Single Factor Count] Iteration {adaptive_iteration} failed: {e}")
            if best_result is not None:
                break  # Use best result so far
            continue
    
    return best_result


def select_items_by_efa_cfa(
    evaluation_summary_path: Path,
    min_item_total_corr: float = 0.5,
    max_skewness: float = 1.0,
    max_kurtosis: float = 2.0,
    max_inter_corr: float = 0.8,
    min_factor_loading: float = 0.75,
    n_factors: Optional[int] = None,
    use_cfa: bool = True,
    cfa_rmsea_threshold: float = 0.08,
    cfa_tli_threshold: float = 0.95,
    cfa_cfi_threshold: float = 0.95,
    cfa_srmr_threshold: float = 0.08,
    min_items_per_factor: int = 2,
    target_range: Optional[Tuple[int, int]] = None,
    adaptive_distribution_thresholds: bool = True,
    min_distribution_pass_rate: float = 0.1,
    min_distribution_items: int = 5,
    adaptive_factor_loading: bool = True,
    max_adaptive_iterations: int = 8,
    enable_factor_balance: bool = True,
    max_items_per_factor: Optional[int] = None,
    try_multiple_n_factors: bool = True,
    max_n_factors_to_try: Optional[int] = None,
    prefer_balanced_factors: bool = True
) -> Dict[str, Any]:
    """
    Select items using EFA + CFA method following PETS paper methodology.
    
    Complete process (PETS Sections 6 & 7.2):
    1. Load participant-level ratings
    2. Calculate item-total correlation (remove < 0.5)
    3. Calculate skewness/kurtosis (remove if > thresholds)
    4. Calculate inter-item correlations (remove if > 0.8 with many items)
    5. Perform EFA (keep items with loadings >= 0.75)
    6. Perform CFA (verify factor structure, optimize fit)
    
    Note: Item count is determined by statistical methods, not preset targets.
    Following PETS methodology, we do not enforce target item counts.
    
    Args:
        evaluation_summary_path: Path to evaluation_summary.json
        min_item_total_corr: Minimum item-total correlation (PETS: 0.5). 
            Adaptive adjustment range: 0.25 (quality floor) to initial value.
        max_skewness: Maximum absolute skewness (PETS: 1.0)
        max_kurtosis: Maximum absolute kurtosis (PETS: 2.0)
        max_inter_corr: Maximum inter-item correlation (PETS: 0.8)
        min_factor_loading: Minimum factor loading (PETS: 0.75). 
            Adaptive adjustment range: 0.50 (Kline, 2015 minimum acceptable) to 0.95.
        n_factors: Number of factors (None = auto-detect)
        use_cfa: Whether to perform CFA after EFA (default: True)
        cfa_rmsea_threshold: Maximum RMSEA for CFA (default: 0.08)
        cfa_tli_threshold: Minimum TLI for CFA (default: 0.95)
        cfa_cfi_threshold: Minimum CFI for CFA (default: 0.95)
        cfa_srmr_threshold: Maximum SRMR for CFA (default: 0.08)
        min_items_per_factor: Minimum items per factor (technical constraint, default: 2)
        target_range: Optional target range (min, max) - used for reporting only, not enforced
        adaptive_distribution_thresholds: Whether to adaptively adjust distribution thresholds
            based on data characteristics (Boateng et al., 2018 recommendation, default: True)
        min_distribution_pass_rate: Minimum pass rate (0.0-1.0) to trigger threshold adjustment
            (default: 0.1 = 10%)
        min_distribution_items: Minimum number of items to pass distribution checks
            (default: 5)
        adaptive_factor_loading: Whether to adaptively adjust min_factor_loading to reach target_range
            (default: True). If enabled and target_range is provided, will iteratively adjust
            min_factor_loading until item count is within target range or max_adaptive_iterations reached.
            Uses dynamic adjustment based on gap between current and target item count.
            Adjustment range: 0.50 (Kline, 2015 minimum acceptable) to 0.95 (PETS standard: >=0.75).
        max_adaptive_iterations: Maximum number of iterations for adaptive adjustment (default: 8)
        enable_factor_balance: Whether to balance factors after EFA, before CFA (default: True)
            If True, will limit items per factor to max_items_per_factor (or auto-calculate if None).
            Balancing is applied when imbalance ratio (max/min) > 1.5 (lowered from 2.0 for earlier intervention).
            This helps ensure more balanced factor distribution while maintaining statistical rigor.
        max_items_per_factor: Maximum items per factor for balancing (default: None = auto-calculate)
            If None and enable_factor_balance=True, will calculate as (total_items / n_factors) * 1.5
            Must be >= min_items_per_factor + 1 to ensure technical feasibility.
        try_multiple_n_factors: Whether to try multiple factor counts and select the best balanced result
            (default: True). If True, will iterate through different factor counts and select based on:
            Priority 1: Item count within target range (target_min <= n_items <= target_max)
            Priority 2: Best factor balance score (among results meeting Priority 1)
        max_n_factors_to_try: Maximum number of factor counts to try (default: None = auto-detect)
            If None, will use Kaiser criterion (eigenvalues >= 1) to determine range [1, 2, ..., kaiser+1]
            Limited to max 5 factors to avoid excessive computation time
        prefer_balanced_factors: Whether to prefer balanced factor structures when selecting best result
            (default: True). Only applies when multiple results meet the item count requirement (Priority 1)
    
    Returns:
        Dictionary with selected items and analysis results
    """
    # Two-stage adaptive selection process:
    # - Stage 1: Adaptive Step 1-3 filtering to select 35-50 items for EFA (preferred: 40-45)
    # - Stage 2: Adaptive EFA+CFA (adjusting min_factor_loading only) to reach final target (10-18 items)
    
    # Load ratings matrix
    ratings_matrix = load_participant_ratings(evaluation_summary_path)
    if ratings_matrix is None:
        raise ValueError("Could not load participant ratings. Ensure participant_level_evaluations.json exists.")
    
    n_participants, n_items = ratings_matrix.shape
    print(f"    [Two-Stage Process] Loaded {n_participants} participants, {n_items} items")
    
    # ===== STAGE 1: Adaptive Step 1-3 filtering (target: 35-50 items for EFA, preferred: 40-45) =====
    stage1_results = _perform_stage1_filtering(
        ratings_matrix=ratings_matrix,
        min_item_total_corr=min_item_total_corr,
        max_skewness=max_skewness,
        max_kurtosis=max_kurtosis,
        max_inter_corr=max_inter_corr,
        adaptive_distribution_thresholds=adaptive_distribution_thresholds,
        min_distribution_pass_rate=min_distribution_pass_rate,
        min_distribution_items=min_distribution_items
    )
    
    items_passed_inter = stage1_results["items_passed_inter"]
    item_total_corrs = stage1_results["item_total_corrs"]
    skew_kurt_stats = stage1_results["skew_kurt_stats"]
    inter_corrs = stage1_results["inter_corrs"]
    high_corr_counts = stage1_results["high_corr_counts"]
    
    # ===== Multi-Factor Iteration: Try different factor counts and select best balanced result =====
    if try_multiple_n_factors and target_range and adaptive_factor_loading:
        target_min, target_max = target_range
        
        # 1. Determine factor count range
        if max_n_factors_to_try is None:
            # Auto-detect using Kaiser criterion
            try:
                # Quick EFA to determine factor count range
                items_for_efa = items_passed_inter[:min(len(items_passed_inter), 50)]
                ratings_for_efa = ratings_matrix[:, [idx - 1 for idx in items_for_efa]]
                
                # Remove NaN
                valid_mask = ~np.any(np.isnan(ratings_for_efa), axis=0)
                ratings_clean = ratings_for_efa[:, valid_mask]
                
                if ratings_clean.shape[1] >= 3 and FACTOR_ANALYZER_AVAILABLE:
                    from factor_analyzer import FactorAnalyzer
                    fa_temp = FactorAnalyzer(n_factors=min(ratings_clean.shape[1], 10), rotation=None, method='principal')
                    fa_temp.fit(ratings_clean)
                    eigenvalues = fa_temp.get_eigenvalues()[0]
                    n_factors_by_kaiser = int(np.sum(eigenvalues >= 1.0))
                    n_factors_by_kaiser = max(1, min(n_factors_by_kaiser, 5))  # Limit to max 5
                    factor_range = list(range(1, min(n_factors_by_kaiser + 2, 6)))  # Try up to kaiser+1, max 5
                else:
                    factor_range = [1, 2, 3]  # Default fallback
            except Exception as e:
                print(f"    [Multi-Factor] Failed to auto-detect factor range: {e}, using default [1, 2, 3]")
                factor_range = [1, 2, 3]
        else:
            factor_range = list(range(1, max_n_factors_to_try + 1))
        
        print(f"\n    [Multi-Factor Iteration] Trying {len(factor_range)} different factor counts: {factor_range}")
        print(f"    [Multi-Factor Iteration] Target range: {target_min}-{target_max} items")
        print(f"    [Multi-Factor Iteration] Priority: 1) Item count in range, 2) Factor balance")
        
        # 2. Run Stage 2 for each factor count
        all_results = []
        for n_factors_try in factor_range:
            print(f"\n    [Multi-Factor Iteration] ===== Trying {n_factors_try} factor(s) =====")
            
            try:
                stage2_result = _run_single_factor_count_stage2(
                    ratings_matrix=ratings_matrix,
                    items_passed_inter=items_passed_inter,
                    high_corr_counts=high_corr_counts,
                    min_factor_loading=min_factor_loading,
                    n_factors_try=n_factors_try,
                    use_cfa=use_cfa,
                    cfa_rmsea_threshold=cfa_rmsea_threshold,
                    cfa_tli_threshold=cfa_tli_threshold,
                    cfa_cfi_threshold=cfa_cfi_threshold,
                    cfa_srmr_threshold=cfa_srmr_threshold,
                    min_items_per_factor=min_items_per_factor,
                    enable_factor_balance=enable_factor_balance,
                    max_items_per_factor=max_items_per_factor,
                    target_range=target_range,
                    adaptive_factor_loading=adaptive_factor_loading,
                    max_adaptive_iterations=max_adaptive_iterations
                )
                
                if stage2_result and len(stage2_result.get("selected_items", [])) > 0:
                    factor_structure = stage2_result.get("factor_structure", {})
                    balance_metrics = _calculate_factor_balance_score(factor_structure)
                    n_selected = len(stage2_result["selected_items"])
                    
                    # Check if all factors have at least min_items_per_factor items
                    factor_counts = balance_metrics["factor_counts"]
                    all_factors_meet_min = all(count >= min_items_per_factor for count in factor_counts.values()) if factor_counts else False
                    
                    print(f"    [Multi-Factor Iteration] {n_factors_try} factors: {n_selected} items selected")
                    print(f"    [Multi-Factor Iteration] Factor distribution: {balance_metrics['factor_counts']}")
                    print(f"    [Multi-Factor Iteration] Balance score: {balance_metrics['balance_score']:.3f} "
                          f"(imbalance ratio: {balance_metrics['imbalance_ratio']:.2f})")
                    print(f"    [Multi-Factor Iteration] All factors >= {min_items_per_factor}: {all_factors_meet_min}")
                    
                    all_results.append({
                        "n_factors": n_factors_try,
                        "result": stage2_result,
                        "n_items": n_selected,
                        "balance_score": balance_metrics["balance_score"],
                        "imbalance_ratio": balance_metrics["imbalance_ratio"],
                        "factor_counts": balance_metrics["factor_counts"],
                        "in_target_range": target_min <= n_selected <= target_max,
                        "all_factors_meet_min": all_factors_meet_min
                    })
                else:
                    print(f"    [Multi-Factor Iteration] {n_factors_try} factors: No valid result")
            
            except Exception as e:
                print(f"    [Multi-Factor Iteration] {n_factors_try} factors: Failed - {e}")
                continue
        
        # 3. Priority-based selection
        if not all_results:
            print(f"    [Multi-Factor Iteration] WARNING: No valid results from any factor count. Falling back to original method.")
        else:
            # Priority 1: Filter results within target range
            results_in_range = [r for r in all_results if r["in_target_range"]]
            
            if results_in_range:
                # Priority 2: Among results in range, filter those with all factors >= min_items_per_factor
                results_with_valid_factors = [r for r in results_in_range if r["all_factors_meet_min"]]
                
                if results_with_valid_factors:
                    # Priority 3: Prefer multi-factor structures (n_factors > 1) over single-factor
                    # This aligns with reference scales like PETS (2 factors) and RoPE (2 factors)
                    multi_factor_results = [r for r in results_with_valid_factors if r["n_factors"] > 1]
                    
                    if multi_factor_results:
                        # Select best balanced among multi-factor results
                        best_result_info = max(multi_factor_results, key=lambda x: x["balance_score"])
                        print(f"\n    [Multi-Factor Iteration] ===== Best Result Selected =====")
                        print(f"    [Multi-Factor Iteration] Selected {best_result_info['n_factors']} factors (multi-factor structure preferred)")
                        print(f"    [Multi-Factor Iteration] Items: {best_result_info['n_items']} (within target range)")
                        print(f"    [Multi-Factor Iteration] All factors >= {min_items_per_factor}: True")
                        print(f"    [Multi-Factor Iteration] Balance score: {best_result_info['balance_score']:.3f}")
                        print(f"    [Multi-Factor Iteration] Factor distribution: {best_result_info['factor_counts']}")
                        print(f"    [Multi-Factor Iteration] Imbalance ratio: {best_result_info['imbalance_ratio']:.2f}")
                        note = f"Multi-factor iteration: selected {best_result_info['n_factors']} factors (Priority 1: item count in range, Priority 2: all factors >= {min_items_per_factor}, Priority 3: multi-factor structure, Priority 4: best balance)"
                    else:
                        # No multi-factor results with valid factors, fallback to single-factor
                        best_result_info = max(results_with_valid_factors, key=lambda x: x["balance_score"])
                        print(f"\n    [Multi-Factor Iteration] ===== Best Result Selected =====")
                        print(f"    [Multi-Factor Iteration] WARNING: No multi-factor results with all factors >= {min_items_per_factor}")
                        print(f"    [Multi-Factor Iteration] Selected {best_result_info['n_factors']} factors (fallback to single-factor)")
                        print(f"    [Multi-Factor Iteration] Items: {best_result_info['n_items']} (within target range)")
                        print(f"    [Multi-Factor Iteration] All factors >= {min_items_per_factor}: True")
                        print(f"    [Multi-Factor Iteration] Balance score: {best_result_info['balance_score']:.3f}")
                        print(f"    [Multi-Factor Iteration] Factor distribution: {best_result_info['factor_counts']}")
                        print(f"    [Multi-Factor Iteration] Imbalance ratio: {best_result_info['imbalance_ratio']:.2f}")
                        note = f"Multi-factor iteration: selected {best_result_info['n_factors']} factors (fallback - no multi-factor results with all factors >= {min_items_per_factor}, selected best balanced single-factor)"
                else:
                    # No results with all factors >= min_items_per_factor, but we have results in range
                    # Select best balanced among results in range (even if some factors < min_items_per_factor)
                    print(f"\n    [Multi-Factor Iteration] WARNING: No results in range with all factors >= {min_items_per_factor}")
                    print(f"    [Multi-Factor Iteration] Falling back to best balanced result in range")
                    best_result_info = max(results_in_range, key=lambda x: x["balance_score"])
                    print(f"    [Multi-Factor Iteration] Selected {best_result_info['n_factors']} factors")
                    print(f"    [Multi-Factor Iteration] Items: {best_result_info['n_items']} (within target range)")
                    print(f"    [Multi-Factor Iteration] All factors >= {min_items_per_factor}: {best_result_info['all_factors_meet_min']}")
                    print(f"    [Multi-Factor Iteration] Balance score: {best_result_info['balance_score']:.3f}")
                    print(f"    [Multi-Factor Iteration] Factor distribution: {best_result_info['factor_counts']}")
                    print(f"    [Multi-Factor Iteration] Imbalance ratio: {best_result_info['imbalance_ratio']:.2f}")
                    note = f"Multi-factor iteration: selected {best_result_info['n_factors']} factors (fallback - no results with all factors >= {min_items_per_factor}, selected best balanced in range)"
            else:
                # No results in target range - select best balanced result (even if outside range)
                print(f"\n    [Multi-Factor Iteration] WARNING: No results in target range [{target_min}, {target_max}]")
                print(f"    [Multi-Factor Iteration] Available item counts: {[r['n_items'] for r in all_results]}")
                print(f"    [Multi-Factor Iteration] Selecting best balanced result (may be outside target range)")
                
                # Prefer multi-factor structures, then results with all factors >= min_items_per_factor, then best balance
                multi_factor_results = [r for r in all_results if r["n_factors"] > 1]
                if multi_factor_results:
                    # Prefer multi-factor results with valid factors
                    multi_factor_valid = [r for r in multi_factor_results if r["all_factors_meet_min"]]
                    if multi_factor_valid:
                        best_result_info = max(multi_factor_valid, key=lambda x: x["balance_score"])
                        print(f"    [Multi-Factor Iteration] Selected multi-factor result with all factors >= {min_items_per_factor}")
                    else:
                        # Multi-factor results exist but some factors < min_items_per_factor
                        best_result_info = max(multi_factor_results, key=lambda x: x["balance_score"])
                        print(f"    [Multi-Factor Iteration] Selected multi-factor result (some factors may have < {min_items_per_factor} items)")
                else:
                    # No multi-factor results, fallback to single-factor
                    results_with_valid_factors = [r for r in all_results if r["all_factors_meet_min"]]
                    if results_with_valid_factors:
                        best_result_info = max(results_with_valid_factors, key=lambda x: x["balance_score"])
                        print(f"    [Multi-Factor Iteration] Selected single-factor result with all factors >= {min_items_per_factor}")
                    else:
                        best_result_info = max(all_results, key=lambda x: x["balance_score"])
                        print(f"    [Multi-Factor Iteration] Selected best balanced overall (some factors may have < {min_items_per_factor} items)")
                
                print(f"    [Multi-Factor Iteration] Selected {best_result_info['n_factors']} factors, "
                      f"{best_result_info['n_items']} items (target: {target_min}-{target_max})")
                print(f"    [Multi-Factor Iteration] Balance score: {best_result_info['balance_score']:.3f}")
                print(f"    [Multi-Factor Iteration] Factor distribution: {best_result_info['factor_counts']}")
                print(f"    [Multi-Factor Iteration] Imbalance ratio: {best_result_info['imbalance_ratio']:.2f}")
                note = f"Multi-factor iteration: selected {best_result_info['n_factors']} factors (fallback - no results in target range, selected best balanced)"
            
            # Build final result (common for all branches)
            result = _build_final_result(
                stage2_result=best_result_info["result"],
                stage1_results=stage1_results,
                target_range=target_range,
                use_cfa=use_cfa,
                adaptive_factor_loading=True,
                adaptive_iterations=0,  # Multi-factor iteration handles this
                initial_min_factor_loading=min_factor_loading,
                final_min_factor_loading=min_factor_loading,
                note=note
            )
            
            # Add multi-factor iteration metadata
            result["multi_factor_iteration"] = {
                "enabled": True,
                "factor_range_tried": factor_range,
                "all_results_summary": [
                    {
                        "n_factors": r["n_factors"],
                        "n_items": r["n_items"],
                        "balance_score": r["balance_score"],
                        "imbalance_ratio": r["imbalance_ratio"],
                        "factor_counts": r["factor_counts"],
                        "in_target_range": r["in_target_range"],
                        "all_factors_meet_min": r["all_factors_meet_min"]
                    }
                    for r in all_results
                ],
                "best_result": {
                    "n_factors": best_result_info["n_factors"],
                    "n_items": best_result_info["n_items"],
                    "balance_score": best_result_info["balance_score"],
                    "imbalance_ratio": best_result_info["imbalance_ratio"],
                    "factor_counts": best_result_info["factor_counts"],
                    "all_factors_meet_min": best_result_info["all_factors_meet_min"]
                },
                "selection_strategy": "priority_based" if results_in_range else "fallback_balanced"
            }
            
            return result
    
    # ===== STAGE 2: Adaptive EFA+CFA (target: 10-18 final items) =====
    # Only adjust min_factor_loading, do NOT repeat Step 1-3
    
    if adaptive_factor_loading and target_range:
        target_min, target_max = target_range
        target_center = (target_min + target_max) / 2.0  # Target center of the range (e.g., 13.5 for 12-15)
        current_min_factor_loading = min_factor_loading
        adaptive_iteration = 0
        best_result = None
        best_result_count = None
        best_distance_to_center = float('inf')
        
        print(f"\n    [Stage 2] Starting adaptive EFA+CFA (target: {target_min}-{target_max} items, preferred: {target_center:.1f})")
        print(f"    [Stage 2] Initial min_factor_loading: {current_min_factor_loading:.3f}")
        print(f"    [Stage 2] Using {len(items_passed_inter)} items from Stage 1 (Step 1-3 completed)")
        
        while adaptive_iteration < max_adaptive_iterations:
            adaptive_iteration += 1
            print(f"\n    [Stage 2 Iteration {adaptive_iteration}/{max_adaptive_iterations}] Trying min_factor_loading={current_min_factor_loading:.3f}")
            
            try:
                # Check if min_factor_loading is at upper bound and we still have too many items
                # This triggers more aggressive factor balancing
                min_factor_loading_at_bound = (current_min_factor_loading >= 0.95)
                
                # Perform Stage 2 (EFA+CFA) with current threshold
                stage2_result = _perform_stage2_efa_cfa(
                    ratings_matrix=ratings_matrix,
                    items_passed_inter=items_passed_inter,
                    high_corr_counts=high_corr_counts,
                    min_factor_loading=current_min_factor_loading,
                    n_factors=n_factors,
                    use_cfa=use_cfa,
                    cfa_rmsea_threshold=cfa_rmsea_threshold,
                    cfa_tli_threshold=cfa_tli_threshold,
                    cfa_cfi_threshold=cfa_cfi_threshold,
                    cfa_srmr_threshold=cfa_srmr_threshold,
                    min_items_per_factor=min_items_per_factor,
                    enable_factor_balance=enable_factor_balance,
                    max_items_per_factor=max_items_per_factor,
                    target_range=target_range,
                    min_factor_loading_at_upper_bound=min_factor_loading_at_bound
                )
                
                n_selected = len(stage2_result["selected_items"])
                distance_to_center = abs(n_selected - target_center)
                print(f"    [Stage 2 Iteration {adaptive_iteration}] Selected {n_selected} items (distance to center {target_center:.1f}: {distance_to_center:.1f})")
                
                # Check if within target range
                if target_min <= n_selected <= target_max:
                    print(f"    [Stage 2] {n_selected} items within target range [{target_min}, {target_max}]")
                
                # Track best result (closest to target center, preferring results within target range)
                is_in_range = target_min <= n_selected <= target_max
                is_current_best = False
                
                if best_result is None:
                    is_current_best = True
                elif is_in_range:
                    # If current result is in range, prefer it if:
                    # 1. Best result is not in range, OR
                    # 2. Current result is closer to center than best result
                    if target_min <= best_result_count <= target_max:
                        # Both in range, prefer closer to center
                        is_current_best = distance_to_center < best_distance_to_center
                    else:
                        # Current in range, best not in range - prefer current
                        is_current_best = True
                else:
                    # Current result not in range, only prefer if best is also not in range and current is closer
                    if not (target_min <= best_result_count <= target_max):
                        is_current_best = distance_to_center < best_distance_to_center
                
                if is_current_best:
                    best_result = stage2_result
                    best_result_count = n_selected
                    best_distance_to_center = distance_to_center
                    if is_in_range:
                        print(f"    [Stage 2] New best result: {n_selected} items (distance to center: {distance_to_center:.1f})")
                
                # Continue iterating even if we're in range, to find result closer to center
                # Adjust min_factor_loading for next iteration based on distance to target center
                if n_selected > target_max:
                    # Too many items: increase threshold
                    gap = n_selected - target_max
                    adjustment = min(0.03 + (gap / 5) * 0.01, 0.10)
                    current_min_factor_loading = min(0.95, current_min_factor_loading + adjustment)
                    print(f"    [Stage 2] Too many items ({n_selected} > {target_max}, gap={gap}), increasing min_factor_loading by {adjustment:.3f} to {current_min_factor_loading:.3f}")
                    if current_min_factor_loading >= 0.95:
                        print(f"    [Stage 2] WARNING: min_factor_loading at upper bound (0.95). Factor balancing will be more aggressive if items still exceed target.")
                elif n_selected < target_min:
                    # Too few items: decrease threshold
                    gap = target_min - n_selected
                    adjustment = min(0.03 + (gap / 5) * 0.01, 0.10)
                    current_min_factor_loading = max(0.50, current_min_factor_loading - adjustment)
                    print(f"    [Stage 2] Too few items ({n_selected} < {target_min}, gap={gap}), decreasing min_factor_loading by {adjustment:.3f} to {current_min_factor_loading:.3f}")
                    if current_min_factor_loading < 0.60:
                        print(f"    [Stage 2] WARNING: Threshold below 0.60. Quality may be compromised (PETS requires >=0.75).")
                elif target_min <= n_selected <= target_max:
                    # Within range: adjust towards center (target_center)
                    if n_selected > target_center:
                        # Above center: slightly increase threshold to reduce items
                        adjustment = 0.02  # Small adjustment since we're already in range
                        current_min_factor_loading = min(0.95, current_min_factor_loading + adjustment)
                        print(f"    [Stage 2] Above center ({n_selected} > {target_center:.1f}), slightly increasing min_factor_loading by {adjustment:.3f} to {current_min_factor_loading:.3f}")
                    elif n_selected < target_center:
                        # Below center: slightly decrease threshold to increase items
                        adjustment = 0.02  # Small adjustment since we're already in range
                        current_min_factor_loading = max(0.50, current_min_factor_loading - adjustment)
                        print(f"    [Stage 2] Below center ({n_selected} < {target_center:.1f}), slightly decreasing min_factor_loading by {adjustment:.3f} to {current_min_factor_loading:.3f}")
                    else:
                        # Exactly at center, continue to check for better results
                        print(f"    [Stage 2] Reached target center ({n_selected} = {target_center:.1f}), continuing to check for better results")
                
            except Exception as e:
                print(f"    [Stage 2 Iteration {adaptive_iteration}] Failed: {e}")
                if best_result is not None:
                    print(f"    [Stage 2] Using best result from previous iteration ({best_result_count} items)")
                    result = _build_final_result(
                        stage2_result=best_result,
                        stage1_results=stage1_results,
                        target_range=target_range,
                        use_cfa=use_cfa,
                        adaptive_factor_loading=True,
                        adaptive_iterations=adaptive_iteration,
                        initial_min_factor_loading=min_factor_loading,
                        final_min_factor_loading=current_min_factor_loading,
                        note="Used best result after iteration failure"
                    )
                    return result
                raise
        
        # If we exhausted iterations, use best result (closest to target center)
        if best_result is not None:
            range_status = "within range" if target_min <= best_result_count <= target_max else "outside range"
            print(f"    [Stage 2] Max iterations reached. Using best result: {best_result_count} items ({range_status}, distance to center {target_center:.1f}: {best_distance_to_center:.1f}, target: {target_min}-{target_max})")
            result = _build_final_result(
                stage2_result=best_result,
                stage1_results=stage1_results,
                target_range=target_range,
                use_cfa=use_cfa,
                adaptive_factor_loading=True,
                adaptive_iterations=adaptive_iteration,
                initial_min_factor_loading=min_factor_loading,
                final_min_factor_loading=current_min_factor_loading,
                note="Max iterations reached, using best result (closest to target center)"
            )
            return result
        else:
            print(f"    [Stage 2] WARNING: No valid results found after {max_adaptive_iterations} iterations")
            print(f"    [Stage 2] Proceeding with original threshold {min_factor_loading}")
    
    # Non-adaptive Stage 2 (or fallback)
    stage2_result = _perform_stage2_efa_cfa(
        ratings_matrix=ratings_matrix,
        items_passed_inter=items_passed_inter,
        high_corr_counts=high_corr_counts,
        min_factor_loading=min_factor_loading,
        n_factors=n_factors,
        use_cfa=use_cfa,
        cfa_rmsea_threshold=cfa_rmsea_threshold,
        cfa_tli_threshold=cfa_tli_threshold,
        cfa_cfi_threshold=cfa_cfi_threshold,
        cfa_srmr_threshold=cfa_srmr_threshold,
        min_items_per_factor=min_items_per_factor,
        enable_factor_balance=enable_factor_balance,
        max_items_per_factor=max_items_per_factor,
        target_range=target_range,
        min_factor_loading_at_upper_bound=False  # Not at bound in non-adaptive case
    )
    
    result = _build_final_result(
        stage2_result=stage2_result,
        stage1_results=stage1_results,
        target_range=target_range,
        use_cfa=use_cfa,
        adaptive_factor_loading=adaptive_factor_loading if target_range else False,
        adaptive_iterations=0,
        initial_min_factor_loading=min_factor_loading,
        final_min_factor_loading=min_factor_loading
    )
    
    return result


def _build_final_result(
    stage2_result: Dict[str, Any],
    stage1_results: Dict[str, Any],
    target_range: Optional[Tuple[int, int]],
    use_cfa: bool,
    adaptive_factor_loading: bool,
    adaptive_iterations: int,
    initial_min_factor_loading: float,
    final_min_factor_loading: float,
    note: Optional[str] = None
) -> Dict[str, Any]:
    """Helper function to build final result dictionary from stage results."""
    final_selected_items = stage2_result["selected_items"]
    efa_results = stage2_result["efa_results"]
    cfa_results = stage2_result["cfa_results"]
    factor_structure = stage2_result["factor_structure"]
    
    # Check if result is within target range
    target_range_status = None
    if target_range:
        target_min, target_max = target_range
        n_final = len(final_selected_items)
        if n_final < target_min:
            target_range_status = "below_target"
        elif n_final > target_max:
            target_range_status = "above_target"
        else:
            target_range_status = "within_target"
    
    # Calculate factor distribution
    factor_distribution = {}
    for item_id in final_selected_items:
        factor_idx = factor_structure.get(item_id, 0)
        factor_name = f"Factor{factor_idx+1}"
        factor_distribution[factor_name] = factor_distribution.get(factor_name, 0) + 1
    
    # Merge filtering steps info
    filtering_steps = stage1_results["filtering_steps"].copy()
    filtering_steps.update({
        "after_efa": len(stage2_result["efa_selected_items"]),
        "final_n_items": len(final_selected_items)
    })
    
    result = {
            "selected_items": sorted(final_selected_items),
            "method": "efa_cfa" if use_cfa and cfa_results else "efa_only",
            "n_factors": efa_results["n_factors"],
            "n_selected_items": len(final_selected_items),
            "factor_distribution": factor_distribution,
            "target_range": target_range,
            "target_range_status": target_range_status,
        "factor_structure": {str(k): v for k, v in factor_structure.items()},  # Add factor_structure for markdown generation
            "efa_results": {
                "item_loadings": {str(k): v for k, v in efa_results["item_loadings"].items()},
                "bartlett_test": efa_results["bartlett_test"],
                "kmo_test": efa_results["kmo_test"],
                "eigenvalues": efa_results["eigenvalues"],
            "efa_selected_items": sorted(stage2_result["efa_selected_items"]),
            "n_efa_items": len(stage2_result["efa_selected_items"])
            },
            "cfa_results": cfa_results if cfa_results else None,
        "item_total_correlations": {str(k): v for k, v in stage1_results["item_total_corrs"].items()},
        "skewness_kurtosis": {str(k): v for k, v in stage1_results["skew_kurt_stats"].items()},
        "inter_item_correlations": {f"{k[0]}-{k[1]}": v for k, v in stage1_results["inter_corrs"].items()},
        "filtering_steps": filtering_steps,
        "adaptive_adjustment": {
            "enabled": adaptive_factor_loading,
            "iterations": adaptive_iterations,
            "final_min_factor_loading": final_min_factor_loading,
            "initial_min_factor_loading": initial_min_factor_loading
        }
    }
    
    if note:
        result["adaptive_adjustment"]["note"] = note
    
    # Print summary
    print(f"\n    [Final Summary] Selected {len(final_selected_items)} items")
    if factor_distribution:
        print(f"    [Final Summary] Factor distribution: {factor_distribution}")
    if target_range and target_range_status:
        if target_range_status == "within_target":
            print(f"    [Final Summary] Item count ({len(final_selected_items)}) is within target range {target_range}")
        elif target_range_status == "below_target":
            print(f"    [Final Summary] Item count ({len(final_selected_items)}) is below target range {target_range}")
        else:
            print(f"    [Final Summary] Item count ({len(final_selected_items)}) is above target range {target_range}")
        
        return result


# OLD CODE REMOVED - The following code block has been replaced by the two-stage process above
# All Step 1-5 logic has been moved to _perform_stage1_filtering and _perform_stage2_efa_cfa functions


# Backward compatibility alias
def select_items_by_efa(*args, **kwargs):
    """Backward compatibility alias for select_items_by_efa_cfa."""
    return select_items_by_efa_cfa(*args, **kwargs, use_cfa=False)
