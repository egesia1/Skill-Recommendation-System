"""
O*NET Hyperparameter Search

Split train/val, grid search over factors, regularization, iterations, w_0,
and evaluation on held-out relations (RMSE). Used for O*NET task and tech-skill models.
"""

import time
import logging
from typing import List, Dict, Tuple, Any, Union
import numpy as np
from itertools import product

from .trainer import build_sparse_matrix
from .wals_weighted import WeightedWALS
from .data_loader import load_onet_task_data, load_onet_technology_skill_data

logger = logging.getLogger(__name__)


def split_relations(
    occupation_skill_rels: List[Tuple],
    val_frac: float = 0.1,
    random_state: int = 42,
) -> Tuple[List[Tuple], List[Tuple]]:
    """
    Split relations into train and validation sets.

    Args:
        occupation_skill_rels: List of (occ, skill) or (occ, skill, weight).
        val_frac: Fraction of relations to hold out for validation (e.g. 0.1).
        random_state: Random seed for reproducibility.

    Returns:
        (train_rels, val_rels)
    """
    rng = np.random.default_rng(random_state)
    n = len(occupation_skill_rels)
    indices = np.arange(n)
    rng.shuffle(indices)
    n_val = max(1, int(n * val_frac))
    val_idx = set(indices[:n_val].tolist())
    train_rels = [occupation_skill_rels[i] for i in range(n) if i not in val_idx]
    val_rels = [occupation_skill_rels[i] for i in range(n) if i in val_idx]
    return train_rels, val_rels


def evaluate_held_out(
    user_factors: np.ndarray,
    item_factors: np.ndarray,
    val_rels: List[Tuple],
    occupation_to_idx: Dict,
    skill_to_idx: Dict,
    metric: str = "rmse",
) -> float:
    """
    Evaluate predictions on held-out relations (target = 1.0 for confidence-based model).

    Args:
        user_factors: (M, k) occupation embeddings.
        item_factors: (N, k) skill/task embeddings.
        val_rels: List of (occ, skill) or (occ, skill, weight).
        occupation_to_idx: Mapping occ code -> row index.
        skill_to_idx: Mapping skill id -> column index.
        metric: 'rmse' (sqrt of mean (1 - pred)^2).

    Returns:
        Scalar metric (lower is better for RMSE).
    """
    squared_errors = []
    for rel in val_rels:
        occ = rel[0]
        skill = rel[1]
        if occ not in occupation_to_idx or skill not in skill_to_idx:
            continue
        i = occupation_to_idx[occ]
        j = skill_to_idx[skill]
        pred = float(user_factors[i] @ item_factors[j])
        target = 1.0
        squared_errors.append((target - pred) ** 2)
    if not squared_errors:
        return float("inf")
    if metric == "rmse":
        return float(np.sqrt(np.mean(squared_errors)))
    raise ValueError(f"Unknown metric: {metric}")


def _expand_param_grid(param_grid: Dict[str, List]) -> List[Dict[str, Any]]:
    """Expand param_grid dict into list of dicts (one per combination)."""
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combos = list(product(*values))
    return [dict(zip(keys, c)) for c in combos]


def grid_search_onet_task(
    db_path: str,
    param_grid: Union[Dict[str, List], List[Dict[str, Any]]],
    val_frac: float = 0.1,
    metric: str = "rmse",
    verbose: int = 1,
    random_state: int = 42,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run grid search for O*NET task model: train on train_rels, evaluate on val_rels.

    Args:
        db_path: Path to onet.db.
        param_grid: Dict of lists (e.g. {'factors': [50, 100], 'regularization': [0.01, 0.1], ...})
                    or list of param dicts. Must include keys: factors, regularization, iterations, w_0.
        val_frac: Fraction of relations for validation.
        metric: 'rmse'.
        verbose: 0 = quiet, 1 = log each run.
        random_state: For split and WeightedWALS.

    Returns:
        (results_list, best_params)
        results_list: [{'params': {...}, 'val_metric': float, 'time': float}, ...]
        best_params: params with lowest val_metric (for RMSE).
    """
    if isinstance(param_grid, dict):
        param_list = _expand_param_grid(param_grid)
    else:
        param_list = param_grid

    occupation_to_idx, skill_to_idx, occupation_skill_rels, _, _ = load_onet_task_data(db_path)
    train_rels, val_rels = split_relations(occupation_skill_rels, val_frac=val_frac, random_state=random_state)
    if verbose:
        logger.info(f"O*NET task: {len(train_rels)} train, {len(val_rels)} val relations")

    results = []
    for params in param_list:
        factors = params["factors"]
        regularization = params["regularization"]
        iterations = params["iterations"]
        w_0 = params["w_0"]
        t0 = time.time()
        train_matrix = build_sparse_matrix(
            occupation_to_idx, skill_to_idx, train_rels, weighted=True
        )
        model = WeightedWALS(
            factors=factors,
            regularization=regularization,
            iterations=iterations,
            random_state=random_state,
        )
        model.fit(train_matrix, w_0=w_0, verbose=False, save_history=False)
        val_metric = evaluate_held_out(
            model.user_factors,
            model.item_factors,
            val_rels,
            occupation_to_idx,
            skill_to_idx,
            metric=metric,
        )
        elapsed = time.time() - t0
        results.append({"params": params, "val_metric": val_metric, "time": elapsed})
        if verbose:
            logger.info(f"  params {params} -> val_metric={val_metric:.6f} time={elapsed:.1f}s")

    best = min(results, key=lambda x: x["val_metric"])
    best_params = best["params"].copy()
    return results, best_params


def grid_search_onet_tech_skill(
    db_path: str,
    param_grid: Union[Dict[str, List], List[Dict[str, Any]]],
    val_frac: float = 0.1,
    metric: str = "rmse",
    verbose: int = 1,
    random_state: int = 42,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run grid search for O*NET technology skill model.

    Same interface as grid_search_onet_task but uses load_onet_technology_skill_data.
    """
    if isinstance(param_grid, dict):
        param_list = _expand_param_grid(param_grid)
    else:
        param_list = param_grid

    occupation_to_idx, skill_to_idx, occupation_skill_rels, _, _ = load_onet_technology_skill_data(db_path)
    train_rels, val_rels = split_relations(occupation_skill_rels, val_frac=val_frac, random_state=random_state)
    if verbose:
        logger.info(f"O*NET tech skill: {len(train_rels)} train, {len(val_rels)} val relations")

    results = []
    for params in param_list:
        factors = params["factors"]
        regularization = params["regularization"]
        iterations = params["iterations"]
        w_0 = params["w_0"]
        t0 = time.time()
        train_matrix = build_sparse_matrix(
            occupation_to_idx, skill_to_idx, train_rels, weighted=True
        )
        model = WeightedWALS(
            factors=factors,
            regularization=regularization,
            iterations=iterations,
            random_state=random_state,
        )
        model.fit(train_matrix, w_0=w_0, verbose=False, save_history=False)
        val_metric = evaluate_held_out(
            model.user_factors,
            model.item_factors,
            val_rels,
            occupation_to_idx,
            skill_to_idx,
            metric=metric,
        )
        elapsed = time.time() - t0
        results.append({"params": params, "val_metric": val_metric, "time": elapsed})
        if verbose:
            logger.info(f"  params {params} -> val_metric={val_metric:.6f} time={elapsed:.1f}s")

    best = min(results, key=lambda x: x["val_metric"])
    best_params = best["params"].copy()
    return results, best_params
