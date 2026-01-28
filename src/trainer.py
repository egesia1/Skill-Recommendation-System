"""
Model Trainer for ESCO and ONET

Trains WMF models and saves them in .pkl format.
"""

import os
import pickle
import time
import logging
from typing import Dict, Optional
import numpy as np
from scipy.sparse import csr_matrix

from .wals import ManualWALS, MockImplicitModel
from .wals_weighted import WeightedWALS
from .data_loader import load_esco_data, load_onet_task_data, load_onet_technology_skill_data

logger = logging.getLogger(__name__)


def build_sparse_matrix(occupation_to_idx: Dict, skill_to_idx: Dict, 
                        occupation_skill_rels: list, weighted: bool = False) -> csr_matrix:
    """
    Builds CSR sparse matrix from occupation-skill relations.
    
    Args:
        occupation_to_idx: Mapping occupation URI -> index
        skill_to_idx: Mapping skill URI -> index
        occupation_skill_rels: List of tuples (occ_uri, skill_uri) or (occ_uri, skill_uri, weight)
        weighted: If True, uses third element of tuple as weight
    
    Returns:
        CSR sparse matrix (M × N)
    """
    rows, cols, data = [], [], []
    
    for rel in occupation_skill_rels:
        if weighted and len(rel) == 3:
            occ_uri, skill_uri, weight = rel
        else:
            occ_uri, skill_uri = rel
            weight = 1.0
        
        if occ_uri in occupation_to_idx and skill_uri in skill_to_idx:
            occ_idx = occupation_to_idx[occ_uri]
            skill_idx = skill_to_idx[skill_uri]
            rows.append(occ_idx)
            cols.append(skill_idx)
            data.append(float(weight))
    
    M = len(occupation_to_idx)
    N = len(skill_to_idx)
    matrix = csr_matrix((data, (rows, cols)), shape=(M, N))
    
    logger.info(f"Built sparse matrix: {matrix.shape}, {len(data)} non-zero entries")
    
    return matrix


def train_esco_model(db_path: str, output_dir: str, language: str = 'en',
                     factors: int = 50, regularization: float = 0.1,
                     iterations: int = 15, w_0: float = 0.01, 
                     save_history: bool = False) -> Dict:
    """
    Trains WALS model on ESCO data and saves in .pkl format.
    
    Args:
        db_path: Path to ESCO SQLite database
        output_dir: Directory to save the model
        language: ESCO language
        factors: Number of latent factors
        regularization: Regularization parameter
        iterations: Number of WALS iterations
        w_0: Weight for unobserved entries
        save_history: If True, saves training history
    
    Returns:
        dict with 'model_path', 'total_time', and optionally 'history'
    """
    # 1. Load ESCO data
    occupation_to_idx, skill_to_idx, occupation_skill_rels, idx_to_occupation_uri, idx_to_skill_uri = \
        load_esco_data(db_path, language)
    
    # 2. Build sparse matrix (binary)
    matrix = build_sparse_matrix(occupation_to_idx, skill_to_idx, occupation_skill_rels, weighted=False)
    
    # 3. Train WALS model
    logger.info(f"Training WALS model (factors={factors}, regularization={regularization}, iterations={iterations})")
    model = ManualWALS(
        factors=factors,
        regularization=regularization,
        iterations=iterations
    )
    
    total_start = time.time()
    history = model.fit(matrix, w_0=w_0, verbose=True, save_history=save_history)
    total_time = time.time() - total_start
    
    # 4. Create MockImplicitModel for compatibility
    mock_model = MockImplicitModel(
        factors=factors,
        user_factors=model.user_factors,
        item_factors=model.item_factors
    )
    
    # 5. Prepare model_data
    model_data = {
        'model': mock_model,
        'occupation_to_idx': occupation_to_idx,
        'skill_to_idx': skill_to_idx,
        'idx_to_skill_uri': idx_to_skill_uri,
        'idx_to_occupation_uri': idx_to_occupation_uri,
        'language': language,
        'factors': factors,
        'regularization': regularization,
        'iterations': iterations,
        'matrix_shape': matrix.shape,
        'non_zero_entries': len(occupation_skill_rels)
    }
    
    # 6. Save model
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, f"esco_wmf_model_{language}.pkl")
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    logger.info(f"Model saved to: {model_path}")
    logger.info(f"Model stats:")
    logger.info(f"  - Matrix shape: {matrix.shape}")
    logger.info(f"  - Non-zero entries: {model_data['non_zero_entries']}")
    logger.info(f"  - Factors: {factors}")
    logger.info(f"  - User factors shape: {model.user_factors.shape}")
    logger.info(f"  - Item factors shape: {model.item_factors.shape}")
    logger.info(f"  - Total training time: {total_time:.2f} seconds")
    
    result = {
        'model_path': model_path,
        'total_time': total_time,
        'final_error': history[-1]['error'] if history else None,
        'initial_error': history[0]['error'] if history else None
    }
    
    if save_history:
        result['history'] = history
    
    return result


def train_onet_task_model(db_path: str, output_dir: str,
                          factors: int = 50, regularization: float = 0.1,
                          iterations: int = 15, w_0: float = 0.01,
                          save_history: bool = False) -> Dict:
    """
    Trains WALS model on ONET occupation x task data (IM importance) and saves in .pkl format.
    """
    occupation_to_idx, skill_to_idx, occupation_skill_rels, idx_to_occupation_code, idx_to_skill_element_id = \
        load_onet_task_data(db_path)

    matrix = build_sparse_matrix(occupation_to_idx, skill_to_idx, occupation_skill_rels, weighted=True)
    importance_values = [rel[2] for rel in occupation_skill_rels]
    if importance_values:
        logger.info(f"Task importance: avg={np.mean(importance_values):.4f}, range [{min(importance_values):.4f}, {max(importance_values):.4f}]")

    model = WeightedWALS(factors=factors, regularization=regularization, iterations=iterations)
    total_start = time.time()
    history = model.fit(matrix, w_0=w_0, verbose=True, save_history=save_history)
    total_time = time.time() - total_start

    mock_model = MockImplicitModel(
        factors=factors,
        user_factors=model.user_factors,
        item_factors=model.item_factors
    )
    model_data = {
        'model': mock_model,
        'occupation_to_idx': occupation_to_idx,
        'skill_to_idx': skill_to_idx,
        'idx_to_skill_element_id': idx_to_skill_element_id,
        'idx_to_occupation_code': idx_to_occupation_code,
        'language': 'en',
        'data_source': 'onet_task',
        'factors': factors,
        'regularization': regularization,
        'iterations': iterations,
        'matrix_shape': matrix.shape,
        'non_zero_entries': len(occupation_skill_rels),
        'weighted': True,
        'weight_type': 'importance'
    }
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "onet_task_wmf_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    logger.info(f"Model saved to: {model_path} (shape {matrix.shape}, {len(occupation_skill_rels)} non-zero)")
    result = {
        'model_path': model_path,
        'total_time': total_time,
        'final_error': history[-1]['error'] if history else None,
        'initial_error': history[0]['error'] if history else None
    }
    if save_history:
        result['history'] = history
    return result


def train_onet_technology_skill_model(db_path: str, output_dir: str,
                                      factors: int = 50, regularization: float = 0.1,
                                      iterations: int = 15, w_0: float = 0.01,
                                      save_history: bool = False) -> Dict:
    """
    Trains WALS model on ONET occupation x technology skill data (derived weight) and saves in .pkl format.
    """
    occupation_to_idx, skill_to_idx, occupation_skill_rels, idx_to_occupation_code, idx_to_skill_uri = \
        load_onet_technology_skill_data(db_path)

    matrix = build_sparse_matrix(occupation_to_idx, skill_to_idx, occupation_skill_rels, weighted=True)
    weight_values = [rel[2] for rel in occupation_skill_rels]
    if weight_values:
        logger.info(f"Tech skill weight: avg={np.mean(weight_values):.4f}, range [{min(weight_values):.4f}, {max(weight_values):.4f}]")

    model = WeightedWALS(factors=factors, regularization=regularization, iterations=iterations)
    total_start = time.time()
    history = model.fit(matrix, w_0=w_0, verbose=True, save_history=save_history)
    total_time = time.time() - total_start

    mock_model = MockImplicitModel(
        factors=factors,
        user_factors=model.user_factors,
        item_factors=model.item_factors
    )
    model_data = {
        'model': mock_model,
        'occupation_to_idx': occupation_to_idx,
        'skill_to_idx': skill_to_idx,
        'idx_to_skill_uri': idx_to_skill_uri,
        'idx_to_occupation_code': idx_to_occupation_code,
        'language': 'en',
        'data_source': 'onet_tech_skill',
        'factors': factors,
        'regularization': regularization,
        'iterations': iterations,
        'matrix_shape': matrix.shape,
        'non_zero_entries': len(occupation_skill_rels),
        'weighted': True,
        'weight_type': 'derived'
    }
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "onet_tech_skill_wmf_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    logger.info(f"Model saved to: {model_path} (shape {matrix.shape}, {len(occupation_skill_rels)} non-zero)")
    result = {
        'model_path': model_path,
        'total_time': total_time,
        'final_error': history[-1]['error'] if history else None,
        'initial_error': history[0]['error'] if history else None
    }
    if save_history:
        result['history'] = history
    return result
