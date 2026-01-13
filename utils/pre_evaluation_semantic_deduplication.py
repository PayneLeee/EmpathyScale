"""
Pre-Evaluation Semantic Deduplication Module

Removes semantically similar items BEFORE evaluation, using sentence embeddings for semantic similarity.
This is used to reduce the item pool before evaluation, ensuring only semantically diverse items are evaluated.
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    # Only print warning if actually needed (not at import time)


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, remove punctuation, normalize whitespace)."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())
    return text


def text_based_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using improved text-based method (0-1).
    
    Uses TF-IDF vectorization with cosine similarity for better semantic matching
    compared to simple SequenceMatcher.
    """
    try:
        # Try using TF-IDF for better semantic similarity
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # Normalize texts
        norm1 = normalize_text(text1)
        norm2 = normalize_text(text2)
        
        # Use TF-IDF vectorization for better semantic matching
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        try:
            tfidf_matrix = vectorizer.fit_transform([norm1, norm2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except ValueError:
            # Fallback if TF-IDF fails (e.g., empty strings)
            from difflib import SequenceMatcher
            return SequenceMatcher(None, norm1, norm2).ratio()
    except ImportError:
        # Fallback to SequenceMatcher if sklearn not available
        from difflib import SequenceMatcher
        norm1 = normalize_text(text1)
        norm2 = normalize_text(text2)
        return SequenceMatcher(None, norm1, norm2).ratio()


def remove_semantic_duplicates_before_evaluation(
    items: List[Dict[str, str]],
    similarity_threshold: float = 0.80,
    cross_dimension_threshold: float = 0.75,
    use_sentence_transformers: bool = True
) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    """
    Remove semantically similar items BEFORE evaluation.
    
    This function uses semantic similarity to identify and remove duplicate items,
    keeping one representative item from each similar group.
    
    CRITICAL: Cross-dimension similarity is checked with a stricter threshold to ensure
    different dimensions measure different aspects (following PETS methodology where
    Emotional Responsiveness and Understanding are distinct factors).
    
    Args:
        items: List of items with "dimension" and "item_text"
        similarity_threshold: Similarity threshold (0-1) for same-dimension items, items above this are considered duplicates
        cross_dimension_threshold: Similarity threshold (0-1) for cross-dimension items, stricter to ensure dimension distinction
        use_sentence_transformers: Whether to use sentence transformers (more accurate) or text-based similarity
    
    Returns:
        Tuple of:
        - Filtered list of items with semantic duplicates removed
        - Statistics dictionary with:
            - n_original: Original number of items
            - n_filtered: Number of items after filtering
            - n_removed: Number of items removed
            - similar_pairs: List of similar pairs found
            - cross_dimension_pairs: List of cross-dimension similar pairs (for reporting)
    """
    if not items:
        return items, {
            "n_original": 0,
            "n_filtered": 0,
            "n_removed": 0,
            "similar_pairs": []
        }
    
    n_original = len(items)
    
    # Extract item texts
    item_texts = [item.get("item_text", "") for item in items]
    
    # Calculate similarity matrix
    if use_sentence_transformers and SENTENCE_TRANSFORMERS_AVAILABLE:
        print(f"    [Semantic Dedup] Using sentence transformers for semantic similarity...", flush=True)
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(item_texts, show_progress_bar=False)
            similarity_matrix = cosine_similarity(embeddings)
        except Exception as e:
            print(f"    [WARN] Sentence transformers failed: {e}, falling back to text-based similarity", flush=True)
            use_sentence_transformers = False
    
    if not use_sentence_transformers or not SENTENCE_TRANSFORMERS_AVAILABLE:
        print(f"    [Semantic Dedup] Using text-based similarity...", flush=True)
        # Import numpy for text-based similarity matrix
        import numpy as np
        # Calculate text-based similarity matrix
        similarity_matrix = np.zeros((n_original, n_original))
        for i in range(n_original):
            for j in range(i + 1, n_original):
                sim = text_based_similarity(item_texts[i], item_texts[j])
                similarity_matrix[i, j] = sim
                similarity_matrix[j, i] = sim
        # Diagonal is 1.0 (self-similarity)
        np.fill_diagonal(similarity_matrix, 1.0)
    
    # Find similar pairs
    similar_pairs = []
    cross_dimension_pairs = []
    items_to_remove = set()
    
    for i in range(n_original):
        if i in items_to_remove:
            continue
        for j in range(i + 1, n_original):
            if j in items_to_remove:
                continue
            
            sim = similarity_matrix[i, j]
            dim1 = items[i].get("dimension", "Unknown")
            dim2 = items[j].get("dimension", "Unknown")
            is_cross_dimension = (dim1 != dim2)
            
            # Use stricter threshold for cross-dimension pairs to ensure dimension distinction
            threshold = cross_dimension_threshold if is_cross_dimension else similarity_threshold
            
            if sim >= threshold:
                pair_info = {
                    "item1_index": i,
                    "item2_index": j,
                    "item1_text": item_texts[i][:50] + "..." if len(item_texts[i]) > 50 else item_texts[i],
                    "item2_text": item_texts[j][:50] + "..." if len(item_texts[j]) > 50 else item_texts[j],
                    "similarity": float(sim),
                    "dimension1": dim1,
                    "dimension2": dim2,
                    "is_cross_dimension": is_cross_dimension
                }
                
                if is_cross_dimension:
                    # Cross-dimension similarity is a serious issue - log it
                    cross_dimension_pairs.append(pair_info)
                    # Remove the item from the dimension with fewer items, or the second one if equal
                    dim1_count = sum(1 for idx, item in enumerate(items) if item.get("dimension") == dim1 and idx not in items_to_remove)
                    dim2_count = sum(1 for idx, item in enumerate(items) if item.get("dimension") == dim2 and idx not in items_to_remove)
                    # Remove from dimension with more items to preserve balance, or second item if equal
                    if dim2_count > dim1_count:
                        items_to_remove.add(j)
                    elif dim1_count > dim2_count:
                        items_to_remove.add(i)
                    else:
                        items_to_remove.add(j)  # Default: remove second item
                else:
                    # Same dimension similarity - standard deduplication
                    similar_pairs.append(pair_info)
                items_to_remove.add(j)  # Remove the second item in the pair
    
    # Filter out removed items
    filtered_items = [
        item for idx, item in enumerate(items)
        if idx not in items_to_remove
    ]
    
    n_filtered = len(filtered_items)
    n_removed = n_original - n_filtered
    
    stats = {
        "n_original": n_original,
        "n_filtered": n_filtered,
        "n_removed": n_removed,
        "removal_ratio": n_removed / n_original if n_original > 0 else 0.0,
        "similar_pairs": similar_pairs,
        "cross_dimension_pairs": cross_dimension_pairs,
        "n_cross_dimension_removed": len([p for p in cross_dimension_pairs if p["item2_index"] in items_to_remove or p["item1_index"] in items_to_remove]),
        "similarity_threshold": similarity_threshold,
        "cross_dimension_threshold": cross_dimension_threshold,
        "method": "sentence_transformers" if (use_sentence_transformers and SENTENCE_TRANSFORMERS_AVAILABLE) else "text_based"
    }
    
    # Print warning if cross-dimension similarities found
    if cross_dimension_pairs:
        print(f"    [WARN] Found {len(cross_dimension_pairs)} cross-dimension similar pairs (threshold: {cross_dimension_threshold})", flush=True)
        print(f"    [WARN] This may indicate insufficient distinction between dimensions. Removed {stats['n_cross_dimension_removed']} items to ensure dimension distinction.", flush=True)
    
    return filtered_items, stats


if __name__ == "__main__":
    # Test the function
    test_items = [
        {"dimension": "Safety Awareness", "item_text": "The robot recognizes hazardous materials and signals caution."},
        {"dimension": "Safety Awareness", "item_text": "The robot identifies dangerous substances and warns about them."},
        {"dimension": "Safety Awareness", "item_text": "The robot stops immediately when detecting a safety issue."},
        {"dimension": "Adaptive Pacing", "item_text": "The robot adjusts its speed to match my work pace."},
    ]
    
    filtered, stats = remove_semantic_duplicates_before_evaluation(test_items, similarity_threshold=0.80)
    
    print(f"Original items: {stats['n_original']}")
    print(f"Filtered items: {stats['n_filtered']}")
    print(f"Removed items: {stats['n_removed']}")
    print(f"Similar pairs found: {len(stats['similar_pairs'])}")
    for pair in stats['similar_pairs']:
        print(f"  - Similarity {pair['similarity']:.3f}: '{pair['item1_text']}' vs '{pair['item2_text']}'")

