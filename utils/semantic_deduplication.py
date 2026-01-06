"""
Semantic Deduplication Module

Removes semantically similar items from a list, keeping only the highest-rated one from each similar pair.
"""

from typing import List, Dict, Any
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, remove punctuation, normalize whitespace)."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())
    return text


def similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts (0-1)."""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def remove_semantic_duplicates(
    items: List[Dict[str, str]],
    evaluation_summary: Dict[str, Any],
    similarity_threshold: float = 0.80
) -> List[Dict[str, str]]:
    """
    Remove semantically similar items, keeping the highest-rated one from each similar pair.
    
    Args:
        items: List of items with "dimension" and "item_text"
        evaluation_summary: Evaluation summary with item_statistics (for ratings)
        similarity_threshold: Similarity threshold (0-1), items above this are considered duplicates
    
    Returns:
        Filtered list of items with semantic duplicates removed
    """
    if not items or not evaluation_summary:
        return items
    
    # Build item_id to item mapping
    item_id_to_item = {}
    item_id_to_text = {}
    for idx, item in enumerate(items, 1):
        item_id_to_item[idx] = item
        item_id_to_text[idx] = item.get("item_text", "")
    
    # Build item_id to rating mapping
    item_id_to_rating = {}
    for item_stat in evaluation_summary.get("item_statistics", []):
        item_id = item_stat.get("item_id")
        rating_stats = item_stat.get("rating_statistics", {})
        mean_rating = rating_stats.get("mean")
        if mean_rating is not None:
            item_id_to_rating[item_id] = mean_rating
    
    # Find similar pairs
    similar_pairs = []
    item_ids = list(item_id_to_item.keys())
    for i in range(len(item_ids)):
        for j in range(i + 1, len(item_ids)):
            item_id1 = item_ids[i]
            item_id2 = item_ids[j]
            text1 = item_id_to_text[item_id1]
            text2 = item_id_to_text[item_id2]
            
            sim = similarity(text1, text2)
            if sim >= similarity_threshold:
                rating1 = item_id_to_rating.get(item_id1, 0)
                rating2 = item_id_to_rating.get(item_id2, 0)
                similar_pairs.append({
                    "item_id1": item_id1,
                    "item_id2": item_id2,
                    "similarity": sim,
                    "rating1": rating1,
                    "rating2": rating2
                })
    
    # Remove duplicates: keep the item with higher rating from each pair
    items_to_remove = set()
    for pair in similar_pairs:
        # Keep the one with higher rating, remove the other
        if pair["rating1"] >= pair["rating2"]:
            items_to_remove.add(pair["item_id2"])
        else:
            items_to_remove.add(pair["item_id1"])
    
    # Filter out removed items
    filtered_items = [
        item for idx, item in enumerate(items, 1)
        if idx not in items_to_remove
    ]
    
    return filtered_items


def remove_semantic_duplicates_by_ids(
    item_ids: List[int],
    items: List[Dict[str, str]],
    evaluation_summary: Dict[str, Any],
    similarity_threshold: float = 0.80
) -> List[int]:
    """
    Remove semantically similar items from a list of item IDs.
    
    Args:
        item_ids: List of item IDs to filter
        items: Full list of items (for text lookup)
        evaluation_summary: Evaluation summary with item_statistics
        similarity_threshold: Similarity threshold (0-1)
    
    Returns:
        Filtered list of item IDs with semantic duplicates removed
    """
    if not item_ids:
        return item_ids
    
    # Get items corresponding to the IDs
    item_id_to_item = {}
    item_id_to_text = {}
    for item_id in item_ids:
        # Find item by position (item_id is 1-indexed)
        if 1 <= item_id <= len(items):
            item = items[item_id - 1]
            item_id_to_item[item_id] = item
            item_id_to_text[item_id] = item.get("item_text", "")
    
    # Build item_id to rating mapping
    item_id_to_rating = {}
    for item_stat in evaluation_summary.get("item_statistics", []):
        item_id = item_stat.get("item_id")
        if item_id in item_ids:
            rating_stats = item_stat.get("rating_statistics", {})
            mean_rating = rating_stats.get("mean")
            if mean_rating is not None:
                item_id_to_rating[item_id] = mean_rating
    
    # Find similar pairs
    similar_pairs = []
    for i in range(len(item_ids)):
        for j in range(i + 1, len(item_ids)):
            item_id1 = item_ids[i]
            item_id2 = item_ids[j]
            
            if item_id1 not in item_id_to_text or item_id2 not in item_id_to_text:
                continue
            
            text1 = item_id_to_text[item_id1]
            text2 = item_id_to_text[item_id2]
            
            sim = similarity(text1, text2)
            if sim >= similarity_threshold:
                rating1 = item_id_to_rating.get(item_id1, 0)
                rating2 = item_id_to_rating.get(item_id2, 0)
                similar_pairs.append({
                    "item_id1": item_id1,
                    "item_id2": item_id2,
                    "similarity": sim,
                    "rating1": rating1,
                    "rating2": rating2
                })
    
    # Remove duplicates: keep the item with higher rating from each pair
    items_to_remove = set()
    for pair in similar_pairs:
        if pair["rating1"] >= pair["rating2"]:
            items_to_remove.add(pair["item_id2"])
        else:
            items_to_remove.add(pair["item_id1"])
    
    # Filter out removed items
    filtered_ids = [item_id for item_id in item_ids if item_id not in items_to_remove]
    
    return filtered_ids





