"""
Recommendation System

Generates skill recommendations from trained models.
"""

import pickle
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def load_model(model_path: str) -> Dict:
    """
    Load trained model from .pkl file.
    
    Args:
        model_path: Path to .pkl model file
    
    Returns:
        Model data dictionary
    """
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    logger.info(f"Model loaded from: {model_path}")
    logger.info(f"  - Factors: {model_data.get('factors', 'N/A')}")
    logger.info(f"  - Matrix shape: {model_data.get('matrix_shape', 'N/A')}")
    
    return model_data


def recommend_skills(model_data: Dict, input_skill_uris: List[str], 
                     top_k: int = 20, filter_existing: bool = True) -> List[Tuple[str, float]]:
    """
    Generate skill recommendations for input skills.
    
    Args:
        model_data: Loaded model data dictionary
        input_skill_uris: List of input skill URIs (or element_ids for ONET)
        top_k: Number of recommendations to return
        filter_existing: If True, filters out input skills from results
    
    Returns:
        List of tuples (skill_uri, score) sorted by score descending
    """
    # Get model and mappings
    model = model_data['model']
    skill_to_idx = model_data['skill_to_idx']
    
    # Get reverse mapping (check which key format is used)
    if 'idx_to_skill_uri' in model_data:
        idx_to_skill = model_data['idx_to_skill_uri']
    elif 'idx_to_skill_element_id' in model_data:
        idx_to_skill = model_data['idx_to_skill_element_id']
    else:
        raise ValueError("Model data missing skill index mapping")
    
    # Build position embedding (average of input skill embeddings)
    position_embedding = np.zeros(model.factors)
    valid_skills = 0
    
    for skill_uri in input_skill_uris:
        if skill_uri in skill_to_idx:
            skill_idx = skill_to_idx[skill_uri]
            position_embedding += model.item_factors[skill_idx]
            valid_skills += 1
    
    if valid_skills == 0:
        logger.warning("No valid input skills found")
        return []
    
    position_embedding /= valid_skills  # Average
    
    logger.info(f"Built position embedding from {valid_skills} skills")
    
    # Predict scores for all skills
    # score[position, skill] = u_position^T · v_skill
    scores = position_embedding @ model.item_factors.T
    
    # Filter and rank
    scored_skills = []
    existing_skill_set = set(input_skill_uris) if filter_existing else set()
    
    for skill_idx, score in enumerate(scores):
        skill_uri = idx_to_skill[skill_idx]
        if skill_uri not in existing_skill_set:
            scored_skills.append((skill_uri, float(score)))
    
    # Sort by score descending
    scored_skills.sort(key=lambda x: x[1], reverse=True)
    
    # Return top_k
    recommendations = scored_skills[:top_k]
    
    logger.info(f"Generated {len(recommendations)} recommendations")
    if recommendations:
        logger.info(f"  - Top score: {recommendations[0][1]:.4f}")
        logger.info(f"  - Bottom score: {recommendations[-1][1]:.4f}")
    
    return recommendations


def recommend_skills_by_category(model_data: Dict, input_skill_uris: List[str],
                                 top_k_per_category: int = 10) -> Dict[str, List[Tuple[str, float]]]:
    """
    Generate recommendations divided into categories.
    
    Note: This requires skill metadata (skill_type) which may not be available
    in standalone mode. This is a placeholder for integration with full systems.
    
    Args:
        model_data: Loaded model data dictionary
        input_skill_uris: List of input skill URIs
        top_k_per_category: Number of recommendations per category
    
    Returns:
        Dictionary with categories and recommendations
    """
    # Get basic recommendations
    all_recommendations = recommend_skills(
        model_data=model_data,
        input_skill_uris=input_skill_uris,
        top_k=top_k_per_category * 4,  # Get more to split into categories
        filter_existing=True
    )
    
    # For standalone version, we can't categorize without skill metadata
    # Return all recommendations in a single category
    return {
        'all': all_recommendations[:top_k_per_category]
    }
