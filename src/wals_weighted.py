"""
Weighted WALS Implementation for O*NET data (Importance/Confidence based).
Manual implementation of WALS where matrix values are used as confidence weights.
"""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.linalg import solve
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class WeightedWALS:
    """
    Weighted WALS implementation where matrix values are treated as confidence weights.
    Target value (p_ui) is implicitly 1 for all observed entries.
    
    Objective function:
    min sum_{i,j in Obs} w_{ij} (1 - u_i^T v_j)^2 + sum_{i,j not in Obs} w_0 (0 - u_i^T v_j)^2
    
    where w_{ij} = matrix[i,j] (e.g. Importance 1-5)
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
        Train the Weighted WALS model on a sparse matrix.
        
        Args:
            matrix: CSR sparse matrix (M × N) - Occupation × Skill (Values are weights!)
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
            logger.info(f"Starting Weighted WALS training: {M} occupations × {N} skills, {k} factors")
        
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
        """Fix V, optimize U using weighted formula."""
        M, N = matrix.shape
        k = self.factors
        
        # Precompute V^T V (as if all entries were unobserved with weight w_0)
        # This corresponds to w_0 * sum_{all j} v_j v_j^T
        V_all_sum = self.item_factors.T @ self.item_factors
        A_base = w_0 * V_all_sum + self.regularization * np.eye(k)
        
        for i in range(M):
            obs_indices = matrix[i].indices
            obs_values = matrix[i].data
            
            # Start with base matrix
            A = A_base.copy()
            b = np.zeros(k)
            
            for idx, val in zip(obs_indices, obs_values):
                v_j = self.item_factors[idx]
                
                # val is the confidence weight w_{ij}
                w_ij = val
                c_ij = 1.0  # Target is 1 for observed
                
                # Update A: add (w_{ij} - w_0) * v_j v_j^T
                # Explanation: We want sum_{j in Obs} w_{ij} v_j v_j^T + sum_{j not in Obs} w_0 v_j v_j^T
                # = sum_{j in Obs} w_{ij} v_j v_j^T + sum_{all j} w_0 v_j v_j^T - sum_{j in Obs} w_0 v_j v_j^T
                # = w_0 * V_all_sum + sum_{j in Obs} (w_{ij} - w_0) v_j v_j^T
                A += (w_ij - w_0) * np.outer(v_j, v_j)
                
                # Update b: sum_{j in Obs} w_{ij} c_{ij} v_j
                b += w_ij * c_ij * v_j
            
            # Solve linear system
            try:
                self.user_factors[i] = solve(A, b)
            except np.linalg.LinAlgError:
                self.user_factors[i] = np.linalg.pinv(A) @ b
    
    def _update_item_factors(self, matrix: csr_matrix, w_0: float):
        """Fix U, optimize V using weighted formula."""
        M, N = matrix.shape
        k = self.factors
        matrix_T = matrix.T.tocsr()
        
        # Precompute U^T U
        U_all_sum = self.user_factors.T @ self.user_factors
        A_base = w_0 * U_all_sum + self.regularization * np.eye(k)
        
        for j in range(N):
            obs_indices = matrix_T[j].indices
            obs_values = matrix_T[j].data
            
            A = A_base.copy()
            b = np.zeros(k)
            
            for idx, val in zip(obs_indices, obs_values):
                u_i = self.user_factors[idx]
                w_ij = val
                c_ij = 1.0
                
                A += (w_ij - w_0) * np.outer(u_i, u_i)
                b += w_ij * c_ij * u_i
            
            try:
                self.item_factors[j] = solve(A, b)
            except np.linalg.LinAlgError:
                self.item_factors[j] = np.linalg.pinv(A) @ b
    
    def _compute_error(self, matrix: csr_matrix, w_0: float) -> float:
        """Compute the weighted objective function error."""
        error = 0.0
        M, N = matrix.shape
        
        # Observed term: w_{ij} (1 - pred)^2
        for i in range(M):
            obs_indices = matrix[i].indices
            obs_values = matrix[i].data
            for idx, val in zip(obs_indices, obs_values):
                u_i = self.user_factors[i]
                v_j = self.item_factors[idx]
                pred = u_i @ v_j
                
                w_ij = val
                c_ij = 1.0
                error += w_ij * ((c_ij - pred) ** 2)
        
        # Unobserved term: w_0 (0 - pred)^2
        # Approximated with sample
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
