"""
Analyze whether the low item-total correlation is due to:
1. Persona diversity issues (personas rate items similarly)
2. Item diversity issues (items measure similar content)

This script compares:
- Persona rating patterns (how differently personas rate)
- Item rating patterns (how differently items are rated)
- Item semantic similarity (if items measure similar things)
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

# Try to import sentence transformers for semantic similarity
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_ANALYSIS_AVAILABLE = True
except ImportError:
    SEMANTIC_ANALYSIS_AVAILABLE = False
    print("[WARN] sentence-transformers not available, skipping semantic analysis")


def analyze_diversity_issue(evaluation_summary_path: Path, scale_draft_path: Path = None):
    """
    Analyze whether low item-total correlation is due to persona or item diversity issues.
    """
    print("=" * 80)
    print("ANALYZING DIVERSITY ISSUE: PERSONA vs ITEM DIVERSITY")
    print("=" * 80)
    print()
    
    # Load evaluation data
    with open(evaluation_summary_path, 'r', encoding='utf-8') as f:
        eval_data = json.load(f)
    
    # Try to load participant-level data from separate file
    eval_dir = evaluation_summary_path.parent
    participant_file = eval_dir / "participant_level_evaluations.json"
    
    if participant_file.exists():
        with open(participant_file, 'r', encoding='utf-8') as f:
            participant_data = json.load(f)
    else:
        participant_data = eval_data.get('participant_level_evaluations', [])
    
    item_stats = eval_data.get('item_statistics', [])
    
    if not participant_data or not item_stats:
        print("[ERROR] Missing participant or item data")
        print(f"  Participant data: {len(participant_data) if participant_data else 0} entries")
        print(f"  Item stats: {len(item_stats) if item_stats else 0} entries")
        return
    
    n_participants = len(participant_data)
    n_items = len(item_stats)
    
    # Build ratings matrix
    ratings_matrix = np.full((n_participants, n_items), np.nan)
    for p_idx, participant in enumerate(participant_data):
        ratings = participant.get('ratings', [])
        for i_idx in range(min(len(ratings), n_items)):
            # Handle both dict format ({"rating": 85}) and direct number format
            rating_value = ratings[i_idx]
            if isinstance(rating_value, dict):
                rating_value = rating_value.get('rating', None)
            if rating_value is None:
                continue  # Keep as NaN
            try:
                ratings_matrix[p_idx, i_idx] = float(rating_value)
            except (ValueError, TypeError):
                continue  # Keep as NaN
    
    print(f"[INFO] Loaded {n_participants} participants, {n_items} items")
    print()
    
    # ========== ANALYSIS 1: PERSONA DIVERSITY ==========
    print("=" * 80)
    print("1. PERSONA DIVERSITY ANALYSIS")
    print("=" * 80)
    
    # Calculate mean rating per persona (handle NaN)
    persona_means = np.nanmean(ratings_matrix, axis=1)
    persona_stds = np.nanstd(ratings_matrix, axis=1)
    
    print(f"  Persona mean ratings:")
    print(f"    - Mean: {np.nanmean(persona_means):.2f}")
    print(f"    - Std: {np.nanstd(persona_means):.2f}")
    print(f"    - Range: {np.nanmin(persona_means):.2f} - {np.nanmax(persona_means):.2f}")
    print(f"    - Range width: {np.nanmax(persona_means) - np.nanmin(persona_means):.2f}")
    print()
    
    # Check if personas rate similarly
    persona_mean_std = np.nanstd(persona_means)
    if persona_mean_std < 5.0:
        print(f"  [WARNING] Personas have similar mean ratings (std={persona_mean_std:.2f})")
        print(f"  [WARNING] This suggests personas may not be diverse enough")
    else:
        print(f"  [OK] Personas have diverse mean ratings (std={persona_mean_std:.2f})")
    print()
    
    # Calculate how much each persona varies in their ratings
    print(f"  Persona rating variance (how much each persona varies):")
    print(f"    - Mean std per persona: {np.nanmean(persona_stds):.2f}")
    print(f"    - Std of persona stds: {np.nanstd(persona_stds):.2f}")
    print(f"    - Range: {np.nanmin(persona_stds):.2f} - {np.nanmax(persona_stds):.2f}")
    print()
    
    # Calculate inter-persona correlation (how similarly personas rate)
    persona_correlations = []
    for i in range(n_participants):
        for j in range(i+1, n_participants):
            corr = np.corrcoef(ratings_matrix[i], ratings_matrix[j])[0, 1]
            if not np.isnan(corr):
                persona_correlations.append(corr)
    
    if persona_correlations:
        print(f"  Inter-persona rating correlations:")
        print(f"    - Mean: {np.mean(persona_correlations):.3f}")
        print(f"    - Std: {np.std(persona_correlations):.3f}")
        print(f"    - Range: {np.min(persona_correlations):.3f} - {np.max(persona_correlations):.3f}")
        if np.mean(persona_correlations) > 0.8:
            print(f"    [WARNING] Personas rate items very similarly (mean corr={np.mean(persona_correlations):.3f})")
            print(f"    [WARNING] This suggests persona diversity is insufficient")
        else:
            print(f"    [OK] Personas rate items differently (mean corr={np.mean(persona_correlations):.3f})")
    print()
    
    # ========== ANALYSIS 2: ITEM DIVERSITY ==========
    print("=" * 80)
    print("2. ITEM DIVERSITY ANALYSIS")
    print("=" * 80)
    
    # Calculate mean rating per item (handle NaN)
    item_means = np.nanmean(ratings_matrix, axis=0)
    item_stds = np.nanstd(ratings_matrix, axis=0)
    
    print(f"  Item mean ratings:")
    print(f"    - Mean: {np.nanmean(item_means):.2f}")
    print(f"    - Std: {np.nanstd(item_means):.2f}")
    print(f"    - Range: {np.nanmin(item_means):.2f} - {np.nanmax(item_means):.2f}")
    print(f"    - Range width: {np.nanmax(item_means) - np.nanmin(item_means):.2f}")
    print()
    
    # Check if items have similar mean ratings
    item_mean_std = np.nanstd(item_means)
    if item_mean_std < 5.0:
        print(f"  [WARNING] Items have similar mean ratings (std={item_mean_std:.2f})")
        print(f"  [WARNING] This suggests items may measure similar content")
    else:
        print(f"  [OK] Items have diverse mean ratings (std={item_mean_std:.2f})")
    print()
    
    # Check item variance
    print(f"  Item rating variance (how much each item varies across personas):")
    print(f"    - Mean std per item: {np.nanmean(item_stds):.2f}")
    print(f"    - Std of item stds: {np.nanstd(item_stds):.2f}")
    print(f"    - Range: {np.nanmin(item_stds):.2f} - {np.nanmax(item_stds):.2f}")
    print()
    
    # Count items with low variance
    low_variance_threshold = 10.0
    low_variance_items = sum(1 for s in item_stds if s < low_variance_threshold)
    print(f"  Items with low variance (std < {low_variance_threshold}): {low_variance_items}/{n_items} ({low_variance_items/n_items*100:.1f}%)")
    if low_variance_items > n_items * 0.5:
        print(f"  [WARNING] Most items have low variance - items may lack discrimination")
    print()
    
    # Calculate inter-item correlation (how similarly items are rated)
    item_correlations = []
    for i in range(n_items):
        for j in range(i+1, n_items):
            corr = np.corrcoef(ratings_matrix[:, i], ratings_matrix[:, j])[0, 1]
            if not np.isnan(corr):
                item_correlations.append(corr)
    
    if item_correlations:
        print(f"  Inter-item rating correlations:")
        print(f"    - Mean: {np.mean(item_correlations):.3f}")
        print(f"    - Std: {np.std(item_correlations):.3f}")
        print(f"    - Range: {np.min(item_correlations):.3f} - {np.max(item_correlations):.3f}")
        if np.mean(item_correlations) > 0.7:
            print(f"    [WARNING] Items are rated very similarly (mean corr={np.mean(item_correlations):.3f})")
            print(f"    [WARNING] This suggests items may measure similar content")
        else:
            print(f"    [OK] Items are rated differently (mean corr={np.mean(item_correlations):.3f})")
    print()
    
    # ========== ANALYSIS 3: SEMANTIC SIMILARITY (if available) ==========
    if SEMANTIC_ANALYSIS_AVAILABLE and scale_draft_path and scale_draft_path.exists():
        print("=" * 80)
        print("3. ITEM SEMANTIC SIMILARITY ANALYSIS")
        print("=" * 80)
        
        try:
            # Load items from scale draft
            from agents.empathy_scale_generation_agent_group import EmpathyScaleGenerationAgentGroup
            md_text = scale_draft_path.read_text(encoding='utf-8', errors='replace')
            items = EmpathyScaleGenerationAgentGroup.parse_scale_markdown(md_text)
            
            if items:
                # Extract item texts
                item_texts = [item.get('item_text', '') for item in items[:n_items]]
                
                # Calculate semantic embeddings
                model = SentenceTransformer('all-MiniLM-L6-v2')
                embeddings = model.encode(item_texts)
                
                # Calculate pairwise cosine similarity
                similarity_matrix = cosine_similarity(embeddings)
                
                # Get upper triangle (excluding diagonal)
                similarities = []
                for i in range(len(item_texts)):
                    for j in range(i+1, len(item_texts)):
                        similarities.append(similarity_matrix[i, j])
                
                if similarities:
                    print(f"  Item semantic similarities (cosine similarity):")
                    print(f"    - Mean: {np.mean(similarities):.3f}")
                    print(f"    - Std: {np.std(similarities):.3f}")
                    print(f"    - Range: {np.min(similarities):.3f} - {np.max(similarities):.3f}")
                    
                    # Count high similarity pairs
                    high_sim_threshold = 0.8
                    high_sim_pairs = sum(1 for s in similarities if s > high_sim_threshold)
                    print(f"    - Pairs with similarity > {high_sim_threshold}: {high_sim_pairs}/{len(similarities)} ({high_sim_pairs/len(similarities)*100:.1f}%)")
                    
                    if np.mean(similarities) > 0.7:
                        print(f"    [WARNING] Items are semantically very similar (mean similarity={np.mean(similarities):.3f})")
                        print(f"    [WARNING] This suggests items may measure similar content")
                    else:
                        print(f"    [OK] Items are semantically diverse (mean similarity={np.mean(similarities):.3f})")
        except Exception as e:
            print(f"  [ERROR] Semantic analysis failed: {e}")
        print()
    
    # ========== CONCLUSION ==========
    print("=" * 80)
    print("4. CONCLUSION")
    print("=" * 80)
    
    persona_issue_score = 0
    item_issue_score = 0
    
    # Persona diversity indicators
    if persona_mean_std < 5.0:
        persona_issue_score += 2
        print("  [PERSONA ISSUE] Personas have similar mean ratings")
    if persona_correlations and np.mean(persona_correlations) > 0.8:
        persona_issue_score += 3
        print("  [PERSONA ISSUE] Personas rate items very similarly (high inter-persona correlation)")
    
    # Item diversity indicators
    if item_mean_std < 5.0:
        item_issue_score += 2
        print("  [ITEM ISSUE] Items have similar mean ratings")
    if low_variance_items > n_items * 0.5:
        item_issue_score += 2
        print("  [ITEM ISSUE] Most items have low variance (lack discrimination)")
    if item_correlations and np.mean(item_correlations) > 0.7:
        item_issue_score += 3
        print("  [ITEM ISSUE] Items are rated very similarly (high inter-item correlation)")
    
    print()
    if persona_issue_score > item_issue_score:
        print("  [CONCLUSION] The issue is MORE LIKELY due to PERSONA DIVERSITY")
        print("  [RECOMMENDATION] Focus on improving persona generation to create more diverse personas")
    elif item_issue_score > persona_issue_score:
        print("  [CONCLUSION] The issue is MORE LIKELY due to ITEM DIVERSITY")
        print("  [RECOMMENDATION] Focus on improving item generation to create more semantically diverse items")
    else:
        print("  [CONCLUSION] The issue is likely due to BOTH persona and item diversity")
        print("  [RECOMMENDATION] Improve both persona generation and item generation")
    
    print()
    print(f"  Persona issue score: {persona_issue_score}")
    print(f"  Item issue score: {item_issue_score}")
    print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python utils/analyze_item_vs_persona_diversity.py <evaluation_summary_path> [scale_draft_path]")
        print("Example: python utils/analyze_item_vs_persona_diversity.py data/runs/2025-12-18_193304/evaluation_agent_group/selection/evaluation_summary.json data/runs/2025-12-18_193304/empathy_scale_generation_agent_group/scale_draft.md")
        sys.exit(1)
    
    eval_path = Path(sys.argv[1])
    scale_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not eval_path.exists():
        print(f"[ERROR] Path does not exist: {eval_path}")
        sys.exit(1)
    
    analyze_diversity_issue(eval_path, scale_path)

