"""
WALS (Weighted Alternating Least Squares) Algorithm Implementation

Manual implementation of WALS for Weighted Matrix Factorisation.
Completely independent from external ML libraries (only numpy, scipy).

NOTE: This implementation uses CPU-only (numpy/scipy).
For GPU acceleration, you would need to:
1. Replace numpy with cupy (CUDA) or use JAX
2. Replace scipy.linalg.solve with GPU-compatible solver
3. Ensure all operations are GPU-compatible
"""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.linalg import solve
import logging
from typing import Optional, List, Dict

# TODO: Add GPU support option
# Example: import cupy as np  # For GPU acceleration
# Requires: pip install cupy-cuda12x (or appropriate CUDA version)

logger = logging.getLogger(__name__)


class ManualWALS:
    """
    Manual implementation of WALS (Weighted Alternating Least Squares)
    for Weighted Matrix Factorisation.
    
    This class is completely independent and produces embeddings
    (user_factors, item_factors) for matrix factorisation.
    """
    
    def __init__(self, factors=50, regularization=0.1, iterations=15, random_state=42):
        """
        Initialize WALS model.
        
        Args:
            factors: Number of latent factors (k)
            regularization: Regularization parameter (λ)
            iterations: Number of WALS iterations
            random_state: Random seed for reproducibility
        """
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        self.random_state = random_state
        self.user_factors = None  # U (occupation embeddings)
        self.item_factors = None   # V (skill embeddings)
    
    def fit(self, matrix: csr_matrix, w_0=0.01, verbose=True, save_history=False) -> Optional[List[Dict]]:
        """
        Train the WALS model on a sparse matrix.
        
        Args:
            matrix: CSR sparse matrix (M × N) - Occupation × Skill
            w_0: Weight for unobserved entries (default: 0.01)
            verbose: If True, prints progress during training
            save_history: If True, saves error and timing for each iteration
        
        Returns:
            List of dicts with iteration history if save_history=True, None otherwise
        """
        import time
        M, N = matrix.shape
        k = self.factors
        np.random.seed(self.random_state)
        
        # Initialize history
        history = []
        
        # 1. Initialization: U and V randomly generated
        self.user_factors = np.random.normal(0, 0.1, (M, k))
        self.item_factors = np.random.normal(0, 0.1, (N, k))
        
        if verbose:
            logger.info(f"Starting WALS training: {M} occupations × {N} skills, {k} factors")
        
        # Compute initial error
        initial_error = self._compute_error(matrix, w_0)
        if save_history:
            history.append({
                'iteration': 0,
                'error': float(initial_error),
                'elapsed_time': 0.0,
                'error_reduction': 0.0,
                'relative_error': 1.0
            })
        if verbose:
            logger.info(f"Initial error: {initial_error:.6f}")
        
        start_time = time.time()
        
        # 2. WALS iterations
        for iteration in range(self.iterations):
            iter_start = time.time()
            
            # 2a. Fix V, optimize U
            self._update_user_factors(matrix, w_0)
            
            # 2b. Fix U, optimize V
            self._update_item_factors(matrix, w_0)
            
            iter_end = time.time()
            iter_time = iter_end - iter_start
            elapsed_time = iter_end - start_time
            
            # Compute error
            error = self._compute_error(matrix, w_0)
            error_reduction = initial_error - error
            relative_error = error / initial_error if initial_error > 0 else 0.0
            
            # Save history
            if save_history:
                history.append({
                    'iteration': iteration + 1,
                    'error': float(error),
                    'elapsed_time': float(elapsed_time),
                    'iteration_time': float(iter_time),
                    'error_reduction': float(error_reduction),
                    'relative_error': float(relative_error),
                    'convergence_rate': float((error_reduction / initial_error) * 100) if initial_error > 0 else 0.0
                })
            
            # Log progress
            if verbose:
                logger.info(f"Iteration {iteration + 1}/{self.iterations}, error: {error:.6f}, "
                          f"reduction: {error_reduction:.2f} ({relative_error*100:.2f}% of initial)")
        
        if verbose:
            final_time = time.time() - start_time
            logger.info(f"Training completed in {final_time:.2f} seconds")
        
        return history if save_history else None
    
    def _update_user_factors(self, matrix: csr_matrix, w_0: float):
        """Fix V, optimize U."""
        M, N = matrix.shape
        k = self.factors
        
        for i in range(M):
            obs_indices = matrix[i].indices
            obs_values = matrix[i].data
            
            # Build linear system for u_i
            A_obs = np.zeros((k, k))
            b_obs = np.zeros(k)
            
            for idx, val in zip(obs_indices, obs_values):
                v_j = self.item_factors[idx]
                w_ij = 1.0  # Uniform weight (can be modified for weighted matrices)
                A_obs += w_ij * np.outer(v_j, v_j)
                b_obs += w_ij * val * v_j
            
            # Unobserved term
            V_all_sum = self.item_factors.T @ self.item_factors
            A_nobs = w_0 * (V_all_sum - A_obs)
            
            # Regularization
            A_reg = self.regularization * np.eye(k)
            
            # Complete system
            A = A_obs + A_nobs + A_reg
            b = b_obs
            
            # Solve linear system
            try:
                u_i = solve(A, b)
                self.user_factors[i] = u_i
            except np.linalg.LinAlgError:
                # Fallback to pseudo-inverse if singular
                u_i = np.linalg.pinv(A) @ b
                self.user_factors[i] = u_i
    
    def _update_item_factors(self, matrix: csr_matrix, w_0: float):
        """Fix U, optimize V."""
        M, N = matrix.shape
        k = self.factors
        matrix_T = matrix.T.tocsr()
        
        for j in range(N):
            obs_indices = matrix_T[j].indices
            obs_values = matrix_T[j].data
            
            A_obs = np.zeros((k, k))
            b_obs = np.zeros(k)
            
            for idx, val in zip(obs_indices, obs_values):
                u_i = self.user_factors[idx]
                w_ij = 1.0
                A_obs += w_ij * np.outer(u_i, u_i)
                b_obs += w_ij * val * u_i
            
            # Unobserved term
            U_all_sum = self.user_factors.T @ self.user_factors
            A_nobs = w_0 * (U_all_sum - A_obs)
            
            # Regularization
            A_reg = self.regularization * np.eye(k)
            
            A = A_obs + A_nobs + A_reg
            b = b_obs
            
            try:
                v_j = solve(A, b)
                self.item_factors[j] = v_j
            except np.linalg.LinAlgError:
                v_j = np.linalg.pinv(A) @ b
                self.item_factors[j] = v_j
    
    def _compute_error(self, matrix: csr_matrix, w_0: float) -> float:
        """Compute the objective function error."""
        error = 0.0
        M, N = matrix.shape
        
        # Observed term
        for i in range(M):
            obs_indices = matrix[i].indices
            obs_values = matrix[i].data
            for idx, val in zip(obs_indices, obs_values):
                u_i = self.user_factors[i]
                v_j = self.item_factors[idx]
                pred = u_i @ v_j
                error += (val - pred) ** 2
        
        # Unobserved term (approximated with sample)
        sample_size = min(1000, M * N - matrix.nnz)
        if sample_size > 0:
            for _ in range(sample_size):
                i = np.random.randint(0, M)
                j = np.random.randint(0, N)
                if matrix[i, j] == 0:
                    u_i = self.user_factors[i]
                    v_j = self.item_factors[j]
                    pred = u_i @ v_j
                    error += w_0 * (pred ** 2)
        
        return error


class MockImplicitModel:
    """
    Mock object that simulates implicit.als.AlternatingLeastSquares
    for compatibility with existing systems.
    """
    def __init__(self, factors: int, user_factors: np.ndarray, item_factors: np.ndarray):
        self.factors = factors
        self.user_factors = user_factors
        self.item_factors = item_factors
