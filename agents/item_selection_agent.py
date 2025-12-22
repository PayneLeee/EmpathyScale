"""
Item Selection Agent

Handles statistical item selection using EFA+CFA methodology following PETS paper.
This agent encapsulates all item filtering logic, keeping run files focused on workflow orchestration.

Reference: PETS paper (Schmidmaier et al., 2024)
- Section 6: Exploratory Factor Analysis (EFA)
- Section 7.2: Confirmatory Factor Analysis (CFA)
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.statistical_item_selection import (
    filter_scale_by_item_ids,
    get_selection_statistics
)

try:
    from langchain_openai import ChatOpenAI
    from openai import APIConnectionError
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from utils.factor_analysis import select_items_by_efa_cfa
    FACTOR_ANALYSIS_AVAILABLE = True
except ImportError as e:
    FACTOR_ANALYSIS_AVAILABLE = False
    print(f"[ERROR] Factor analysis not available: {e}")
    raise


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    
    Args:
        obj: Object that may contain numpy types
        
    Returns:
        Object with all numpy types converted to Python native types
    """
    if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


class ItemSelectionAgent:
    """
    Agent for selecting items using EFA+CFA methodology (PETS paper).
    
    This agent performs item selection based on psychometric methods:
    - Item-total correlation
    - Skewness/Kurtosis checks
    - Inter-item correlation
    - Exploratory Factor Analysis (EFA)
    - Confirmatory Factor Analysis (CFA)
    
    No rating-based selection is performed, as it is not scientifically valid.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        """
        Initialize the Item Selection Agent.
        
        Args:
            api_key: Optional OpenAI API key for factor interpretation (LLM-based naming)
            model_name: Model name for LLM calls (default: gpt-4o-mini)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.llm = None
        if api_key and LLM_AVAILABLE:
            try:
                self.llm = ChatOpenAI(
                    api_key=api_key,
                    model_name=model_name,
                    temperature=0.3,
                    timeout=60.0
                )
            except Exception as e:
                print(f"[WARN] Failed to initialize LLM for factor interpretation: {e}")
                self.llm = None
    
    def select_items(
        self,
        items: List[Dict[str, str]],
        evaluation_summary: Dict[str, Any],
        target_min: int = 10,
        target_max: int = 20,
        selection_config: Optional[Dict[str, Any]] = None,
        evaluation_summary_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Select items using EFA+CFA method following PETS paper methodology.
        
        This method does NOT use rating-based selection, as it is not scientifically valid.
        All selection is based on psychometric methods (EFA/CFA).
        
        Args:
            items: List of items to filter
            evaluation_summary: Evaluation summary with item_statistics
            target_min: Minimum number of items to select
            target_max: Maximum number of items to select
            selection_config: Configuration dict with EFA/CFA parameters:
                - min_item_total_corr: Minimum item-total correlation (default: 0.5)
                - max_skewness: Maximum absolute skewness (default: 1.0)
                - max_kurtosis: Maximum absolute kurtosis (default: 2.0)
                - max_inter_corr: Maximum inter-item correlation (default: 0.8)
                - min_factor_loading: Minimum factor loading (default: 0.75)
                - n_factors: Number of factors (None = auto-detect)
                - use_cfa: Whether to perform CFA (default: True)
                - cfa_rmsea_threshold: Maximum RMSEA (default: 0.08)
                - cfa_tli_threshold: Minimum TLI (default: 0.95)
                - cfa_cfi_threshold: Minimum CFI (default: 0.95)
                - cfa_srmr_threshold: Maximum SRMR (default: 0.08)
            evaluation_summary_path: Path to evaluation_summary.json (required for EFA/CFA)
        
        Returns:
            Dictionary with:
                - selected_item_ids: List of selected item IDs (1-indexed)
                - filtered_items: List of filtered item dictionaries
                - selection_statistics: Statistics about the selection
                - selection_config: Configuration used for selection
                - efa_cfa_results: Complete EFA+CFA analysis results
        """
        if selection_config is None:
            selection_config = {}
        
        # Validate requirements
        if not FACTOR_ANALYSIS_AVAILABLE:
            raise ImportError("Factor analysis libraries not available. Cannot perform EFA/CFA selection.")
        
        if not evaluation_summary_path or not evaluation_summary_path.exists():
            raise ValueError("evaluation_summary_path is required for EFA/CFA selection. Cannot proceed without participant-level data.")
        
        # Extract EFA+CFA configuration (PETS methodology)
        min_item_total_corr = selection_config.get("min_item_total_corr", 0.5)
        max_skewness = selection_config.get("max_skewness", 1.0)
        max_kurtosis = selection_config.get("max_kurtosis", 2.0)
        max_inter_corr = selection_config.get("max_inter_corr", 0.8)
        min_factor_loading = selection_config.get("min_factor_loading", 0.75)
        n_factors = selection_config.get("n_factors", None)
        use_cfa = selection_config.get("use_cfa", True)  # Default to True (full PETS methodology)
        min_items_per_factor = selection_config.get("min_items_per_factor", 2)  # Technical constraint
        
        # CFA parameters
        cfa_rmsea_threshold = selection_config.get("cfa_rmsea_threshold", 0.08)
        cfa_tli_threshold = selection_config.get("cfa_tli_threshold", 0.95)
        cfa_cfi_threshold = selection_config.get("cfa_cfi_threshold", 0.95)
        cfa_srmr_threshold = selection_config.get("cfa_srmr_threshold", 0.08)
        
        # Adaptive adjustment parameters
        adaptive_factor_loading = selection_config.get("adaptive_factor_loading", True)  # Default: enabled
        max_adaptive_iterations = selection_config.get("max_adaptive_iterations", 5)
        
        # Target range (for adaptive adjustment if enabled)
        target_range = (target_min, target_max) if target_min > 0 and target_max > 0 else None
        
        n_items = len(items)
        
        # Perform EFA+CFA selection (PETS methodology - no fallback to rating-based selection)
        print(f"    [Item Selection] Using EFA+CFA method (PETS methodology)")
        if adaptive_factor_loading and target_range:
            print(f"    [Item Selection] Adaptive adjustment enabled: target range {target_min}-{target_max} items")
        print(f"    [Item Selection] No rating-based selection will be performed (not scientifically valid)")
        
        # Extract factor balance configuration (default: enabled)
        enable_factor_balance = selection_config.get("enable_factor_balance", True)
        max_items_per_factor = selection_config.get("max_items_per_factor", None)
        
        # Extract multi-factor iteration configuration
        try_multiple_n_factors = selection_config.get("try_multiple_n_factors", True)
        max_n_factors_to_try = selection_config.get("max_n_factors_to_try", None)
        prefer_balanced_factors = selection_config.get("prefer_balanced_factors", True)
        
        try:
            efa_cfa_results = select_items_by_efa_cfa(
                evaluation_summary_path,
                min_item_total_corr=min_item_total_corr,
                max_skewness=max_skewness,
                max_kurtosis=max_kurtosis,
                max_inter_corr=max_inter_corr,
                min_factor_loading=min_factor_loading,
                n_factors=n_factors,
                use_cfa=use_cfa,
                cfa_rmsea_threshold=cfa_rmsea_threshold,
                cfa_tli_threshold=cfa_tli_threshold,
                cfa_cfi_threshold=cfa_cfi_threshold,
                cfa_srmr_threshold=cfa_srmr_threshold,
                min_items_per_factor=min_items_per_factor,
                target_range=target_range,
                adaptive_factor_loading=adaptive_factor_loading,
                max_adaptive_iterations=max_adaptive_iterations,
                enable_factor_balance=enable_factor_balance,
                max_items_per_factor=max_items_per_factor,
                try_multiple_n_factors=try_multiple_n_factors,
                max_n_factors_to_try=max_n_factors_to_try,
                prefer_balanced_factors=prefer_balanced_factors
            )
            selected_ids = efa_cfa_results.get("selected_items", [])
            
            if len(selected_ids) == 0:
                raise ValueError("EFA+CFA selected 0 items. Cannot proceed.")
            
            # Validate minimum items per factor (technical constraint)
            factor_counts = {}
            for item_id in selected_ids:
                # Get factor assignment from EFA results
                if efa_cfa_results.get("efa_results") and str(item_id) in efa_cfa_results["efa_results"].get("item_loadings", {}):
                    factor_idx = efa_cfa_results["efa_results"]["item_loadings"][str(item_id)]["max_factor"]
                    factor_name = f"Factor{factor_idx+1}"
                    factor_counts[factor_name] = factor_counts.get(factor_name, 0) + 1
            
            for factor_name, count in factor_counts.items():
                if count < min_items_per_factor:
                    print(f"    [WARN] Factor {factor_name} has only {count} items (minimum: {min_items_per_factor})")
                    print(f"    [WARN] This may affect CFA model stability. Consider adjusting min_factor_loading threshold.")
            
        except Exception as e:
            print(f"    [ERROR] EFA+CFA method failed: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"EFA+CFA analysis failed: {e}. Cannot proceed without factor analysis-based selection.")
        
        # Filter items and compute statistics
        filtered_items = filter_scale_by_item_ids(items, selected_ids) if selected_ids else []
        selection_stats = get_selection_statistics(evaluation_summary, selected_ids) if selected_ids else {
            "n_original_items": n_items,
            "n_selected_items": 0,
            "selection_ratio": 0.0
        }
        
        # Update selection config with actual values used (EFA+CFA method)
        actual_config = {
            "strategy": "efa_cfa",
            "method": efa_cfa_results.get("method", "efa_cfa"),
            "target_range": [target_min, target_max] if target_range else None,  # For reporting only
            "target_range_status": efa_cfa_results.get("target_range_status"),
            "n_factors": efa_cfa_results.get("n_factors"),
            "n_selected_items": efa_cfa_results.get("n_selected_items"),
            "factor_distribution": efa_cfa_results.get("factor_distribution", {}),
            "min_item_total_corr": min_item_total_corr,
            "max_skewness": max_skewness,
            "max_kurtosis": max_kurtosis,
            "max_inter_corr": max_inter_corr,
            "min_factor_loading": min_factor_loading,
            "min_items_per_factor": min_items_per_factor,
            "use_cfa": use_cfa,
            "cfa_rmsea_threshold": cfa_rmsea_threshold,
            "cfa_tli_threshold": cfa_tli_threshold,
            "cfa_cfi_threshold": cfa_cfi_threshold,
            "cfa_srmr_threshold": cfa_srmr_threshold,
            "filtering_steps": efa_cfa_results.get("filtering_steps")
        }
        
        # Add EFA and CFA test results
        if efa_cfa_results.get("efa_results"):
            actual_config["efa_results"] = {
                "bartlett_test": efa_cfa_results["efa_results"].get("bartlett_test"),
                "kmo_test": efa_cfa_results["efa_results"].get("kmo_test"),
                "eigenvalues": efa_cfa_results["efa_results"].get("eigenvalues")
            }
        
        if efa_cfa_results.get("cfa_results"):
            actual_config["cfa_results"] = {
                "fit_indices": efa_cfa_results["cfa_results"].get("fit_indices"),
                "iterations": efa_cfa_results["cfa_results"].get("iterations"),
                "removed_items": efa_cfa_results["cfa_results"].get("removed_items")
            }
        
        result = {
            "selected_item_ids": selected_ids,
            "filtered_items": filtered_items,
            "selection_statistics": selection_stats,
            "selection_config": actual_config,
            "efa_cfa_results": efa_cfa_results
        }
        
        return result
    
    def save_selection_results(
        self,
        run_id: str,
        selection_result: Dict[str, Any],
        output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Save selection results to disk.
        
        Args:
            run_id: Run ID for path construction
            selection_result: Result from select_items()
            output_dir: Optional output directory (default: data/runs/{run_id}/statistical_selection)
        
        Returns:
            Dictionary with paths to saved files:
                - config_path: selection_config.json
                - item_ids_path: selected_item_ids.json
                - statistics_path: selection_statistics.json
        """
        from utils.data_manager import DataManager
        
        if output_dir is None:
            dm = DataManager()
            output_dir = dm.get_run_path(run_id) / "statistical_selection"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy types to Python native types for JSON serialization
        selection_config_clean = convert_numpy_types(selection_result["selection_config"])
        selected_item_ids_clean = convert_numpy_types(selection_result["selected_item_ids"])
        selection_statistics_clean = convert_numpy_types(selection_result["selection_statistics"])
        
        # Save selection config
        config_path = output_dir / "selection_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(selection_config_clean, f, indent=2, ensure_ascii=False)
        
        # Save selected item IDs
        item_ids_path = output_dir / "selected_item_ids.json"
        with open(item_ids_path, "w", encoding="utf-8") as f:
            json.dump(selected_item_ids_clean, f, indent=2, ensure_ascii=False)
        
        # Save selection statistics
        statistics_path = output_dir / "selection_statistics.json"
        with open(statistics_path, "w", encoding="utf-8") as f:
            json.dump(selection_statistics_clean, f, indent=2, ensure_ascii=False)
        
        # Save complete EFA+CFA results
        if "efa_cfa_results" in selection_result:
            efa_cfa_path = output_dir / "efa_cfa_results.json"
            efa_cfa_results_clean = convert_numpy_types(selection_result["efa_cfa_results"])
            with open(efa_cfa_path, "w", encoding="utf-8") as f:
                json.dump(efa_cfa_results_clean, f, indent=2, ensure_ascii=False)
        
        return {
            "config_path": config_path,
            "item_ids_path": item_ids_path,
            "statistics_path": statistics_path
        }
    
    def interpret_factors(
        self,
        factor_items: Dict[int, List[Dict[str, str]]],
        scenario: Optional[Dict[str, Any]] = None
    ) -> Dict[int, str]:
        """
        Interpret and name factors based on items content (following PETS methodology).
        
        Uses LLM to analyze items within each factor and generate meaningful names.
        Similar to how PETS named factors as "Emotional Responsiveness" and "Understanding and Trust".
        
        Args:
            factor_items: Dictionary mapping factor_idx to list of items (with item_text)
            scenario: Optional scenario context for better interpretation
        
        Returns:
            Dictionary mapping factor_idx to factor name
        """
        if not self.llm:
            # Fallback: use generic names
            return {idx: f"Factor{idx + 1}" for idx in factor_items.keys()}
        
        factor_names = {}
        
        for factor_idx, items in factor_items.items():
            if not items:
                factor_names[factor_idx] = f"Factor{factor_idx + 1}"
                continue
            
            # Build prompt for factor interpretation
            items_text = "\n".join([f"- {item.get('item_text', '')}" for item in items])
            scenario_context = ""
            if scenario:
                scenario_context = f"\n\nScenario Context:\n{scenario.get('assessment_context', '')}"
            
            prompt = f"""Analyze the following items that were grouped together by factor analysis (EFA). 
These items share a common underlying theme or construct.

Items in this factor:
{items_text}
{scenario_context}

Based on the common themes across these items, provide a concise, meaningful name for this factor (2-4 words).
The name should capture the core construct that these items measure, similar to how PETS named factors as "Emotional Responsiveness" or "Understanding and Trust".

Respond with ONLY the factor name, nothing else."""
            
            try:
                response = self.llm.invoke(prompt).content.strip()
                # Clean up response (remove quotes, extra text)
                factor_name = response.strip('"\'')
                if len(factor_name) > 50:  # Too long, use generic name
                    factor_name = f"Factor{factor_idx + 1}"
                factor_names[factor_idx] = factor_name
            except Exception as e:
                print(f"    [WARN] Failed to interpret Factor{factor_idx + 1}: {e}, using generic name")
                factor_names[factor_idx] = f"Factor{factor_idx + 1}"
        
        return factor_names
    
    def generate_filtered_scale_draft(
        self,
        filtered_items: List[Dict[str, str]],
        selected_item_ids: List[int],
        efa_cfa_results: Optional[Dict[str, Any]] = None,
        scenario: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate filtered scale draft markdown following PETS methodology.
        
        When EFA extracts multiple factors, items are organized by factors (statistical structure).
        When EFA extracts only 1 factor, items are organized by theoretical dimensions.
        
        For multiple factors, attempts to interpret and name factors using LLM (similar to PETS).
        
        Args:
            filtered_items: List of filtered items with dimension and item_text
            selected_item_ids: List of selected item IDs (1-indexed)
            efa_cfa_results: Optional EFA/CFA results dictionary
            scenario: Optional scenario context for factor interpretation
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
            factor_items_dict = {}  # {factor_idx: [items]}
            # Use factor_structure from efa_cfa_results (maps item_id -> factor_idx)
            # This is more reliable than trying to extract from item_loadings
            # (item_loadings uses subset indices as keys, not item_ids)
            factor_structure = efa_cfa_results.get("factor_structure", {}) if efa_cfa_results else {}
            # Convert string keys to int if needed (JSON serialization may convert keys to strings)
            if factor_structure:
                factor_structure = {int(k) if isinstance(k, str) else k: v for k, v in factor_structure.items()}
            
            # Fallback: try to extract from efa_results["item_loadings"] if factor_structure not available
            # But note: item_loadings keys are subset indices (1-indexed), not item_ids
            item_loadings = efa_results.get("item_loadings", {})
            efa_selected_items = efa_results.get("efa_selected_items", [])
            
            for item_id in selected_item_ids:
                factor_idx = None
                
                # First try: use factor_structure (most reliable, maps item_id directly)
                if factor_structure:
                    factor_idx = factor_structure.get(item_id)
                
                # Fallback: try to find in efa_selected_items and map via subset index
                if factor_idx is None and efa_selected_items:
                    try:
                        idx_in_efa_selected = efa_selected_items.index(item_id)
                        subset_idx = idx_in_efa_selected + 1  # Convert to 1-indexed
                        subset_idx_str = str(subset_idx)
                        if subset_idx_str in item_loadings:
                            factor_idx = item_loadings[subset_idx_str].get("max_factor", 0)
                    except (ValueError, IndexError):
                        pass
                
                # Default to Factor 0 if still not found
                if factor_idx is None:
                    factor_idx = 0
                
                if factor_idx not in factor_items_dict:
                    factor_items_dict[factor_idx] = []
                if item_id in item_map:
                    factor_items_dict[factor_idx].append(item_map[item_id])
            
            # Interpret and name factors
            print("    [LLM Call] Interpreting factors and generating names...")
            factor_names = self.interpret_factors(factor_items_dict, scenario)
            
            # Sort factors and output items
            item_num = 1
            for factor_idx in sorted(factor_items_dict.keys()):
                factor_items_list = factor_items_dict[factor_idx]
                factor_name = factor_names.get(factor_idx, f"Factor{factor_idx + 1}")
                md_lines.append(f"### {factor_name} ({len(factor_items_list)} items)")
                
                for item in factor_items_list:
                    item_text = item.get("item_text", "")
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
