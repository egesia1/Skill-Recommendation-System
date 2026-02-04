"""
Recommendation System

Generates skill recommendations from trained models.
"""

import pickle
import logging
import numpy as np
from scipy.linalg import solve
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


def fold_in_new_occupation(model_data: Dict, input_skill_uris: List[str], 
                           skill_weights: Optional[List[float]] = None,
                           w_0: float = 0.01, regularization: Optional[float] = None) -> np.ndarray:
    """
    Folding-in: Compute optimal occupation embedding for a new occupation with given skills.
    
    This implements the WALS inference step: given a new occupation with selected skills,
    solve the linear system to find the optimal occupation vector u_new that minimizes
    the WALS objective function, keeping skill vectors V fixed.
    
    This is the correct way to handle new occupations, as described in the WALS theory:
    - The new occupation doesn't exist in the training data
    - We project its skill selections into the learned latent space
    - The system "reasons" by analogy using the structure learned from ESCO
    
    Args:
        model_data: Loaded model data dictionary
        input_skill_uris: List of input skill URIs (or element_ids for ONET)
        skill_weights: Optional list of weights for each skill (default: 1.0 for all)
                      For weighted models, you can pass importance/confidence values
        w_0: Weight for non-relevant skills (should match training w_0)
        regularization: Regularization parameter (default: from model_data)
    
    Returns:
        Optimal occupation embedding vector (k-dimensional)
    """
    model = model_data['model']
    skill_to_idx = model_data['skill_to_idx']
    k = model.factors
    
    # Get regularization from model_data if not provided
    if regularization is None:
        regularization = model_data.get('regularization', 0.1)
    
    # Default weights: 1.0 for all skills
    if skill_weights is None:
        skill_weights = [1.0] * len(input_skill_uris)
    
    if len(skill_weights) != len(input_skill_uris):
        raise ValueError("skill_weights must have same length as input_skill_uris")
    
    # Build linear system: (A_obs + A_nobs + λI) u_new = b_obs
    # This is the same formula used in _update_user_factors during training
    
    # Precompute V^T V (all skill vectors)
    V_all_sum = model.item_factors.T @ model.item_factors
    
    # Observed terms: skills selected by user
    A_obs = np.zeros((k, k))
    b_obs = np.zeros(k)
    
    valid_skills = 0
    for skill_uri, w_ij in zip(input_skill_uris, skill_weights):
        if skill_uri in skill_to_idx:
            skill_idx = skill_to_idx[skill_uri]
            v_j = model.item_factors[skill_idx]
            
            # w_ij is the confidence weight (1.0 for binary, or importance value for weighted)
            # Target value c_ij = 1.0 (we want u_new^T v_j ≈ 1)
            A_obs += w_ij * np.outer(v_j, v_j)
            b_obs += w_ij * 1.0 * v_j  # c_ij = 1.0
            valid_skills += 1
    
    if valid_skills == 0:
        raise ValueError("No valid input skills found")
    
    # Unobserved term: w_0 * (V^T V - sum of observed v_j v_j^T)
    # This accounts for all skills NOT selected (treated as non-relevant with weight w_0)
    A_nobs = w_0 * (V_all_sum - A_obs)
    
    # Regularization term
    A_reg = regularization * np.eye(k)
    
    # Complete system
    A = A_obs + A_nobs + A_reg
    
    # Solve linear system
    try:
        u_new = solve(A, b_obs)
    except np.linalg.LinAlgError:
        # Fallback to pseudo-inverse if singular
        u_new = np.linalg.pinv(A) @ b_obs
    
    logger.info(f"Folded-in new occupation embedding from {valid_skills} skills")
    
    return u_new


def recommend_skills(model_data: Dict, input_skill_uris: List[str], 
                     top_k: int = 20, filter_existing: bool = True,
                     use_folding_in: bool = True, 
                     skill_weights: Optional[List[float]] = None,
                     w_0: Optional[float] = None) -> List[Tuple[str, float]]:
    """
    Generate skill recommendations for input skills.
    
    This function supports two modes:
    1. **Folding-in (recommended)**: Solves the WALS linear system to find the optimal
       occupation embedding. This is the correct approach for generative use cases where
       you want to create new "hybrid" professions.
    2. **Simple average (legacy)**: Uses average of skill embeddings as approximation.
       Faster but less accurate.
    
    Args:
        model_data: Loaded model data dictionary
        input_skill_uris: List of input skill URIs (or element_ids for ONET)
        top_k: Number of recommendations to return
        filter_existing: If True, filters out input skills from results
        use_folding_in: If True, uses proper WALS folding-in (recommended).
                       If False, uses simple average (legacy behavior).
        skill_weights: Optional list of weights for each skill (only used if use_folding_in=True)
                      For weighted models, you can pass importance/confidence values
        w_0: Weight for non-relevant skills (only used if use_folding_in=True)
             Default: from model_data or 0.01
    
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
    
    # Get w_0 from model_data if not provided
    if w_0 is None:
        w_0 = model_data.get('w_0', 0.01)
    
    # Compute occupation embedding
    if use_folding_in:
        # CORRECT METHOD: WALS Folding-in
        # Solves linear system to find optimal occupation vector
        position_embedding = fold_in_new_occupation(
            model_data=model_data,
            input_skill_uris=input_skill_uris,
            skill_weights=skill_weights,
            w_0=w_0
        )
        logger.info("Using WALS folding-in (optimal method)")
    else:
        # LEGACY METHOD: Simple average
        # This is an approximation, not the optimal solution
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
        logger.info(f"Using simple average (legacy method) from {valid_skills} skills")
    
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
