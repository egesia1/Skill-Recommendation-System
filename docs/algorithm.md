# WALS Algorithm Explanation

## Weighted Matrix Factorisation (WMF)

### Objective Function

The goal is to factorize a sparse matrix **C** (Occupation × Skill) into two low-rank matrices:

```
C ≈ U · V^T
```

Where:
- **C**: Original matrix (M × N) - Occupation × Skill
- **U**: User factors (M × k) - Occupation embeddings
- **V**: Item factors (N × k) - Skill embeddings
- **k**: Number of latent factors (typically 20-100)

### Objective Function

```
min_{U,V} ∑_{i,j ∈ Obs} w_{i,j}(C_{i,j} - u_i^T v_j)² + 
         w_0 ∑_{i,j ∈ Nobs} (u_i^T v_j)² + 
         λ(||U||²_F + ||V||²_F)
```

**Terms:**
1. **Observed term**: Minimizes error on observed entries (i,j) where C_{i,j} > 0
2. **Unobserved term**: Penalizes predictions on unobserved entries (w_0 weight)
3. **Regularization term**: Prevents overfitting (λ parameter)

**Parameters:**
- **w_{i,j}**: Weight for observed entry (i,j) - can be uniform (1.0) or importance-based
- **w_0**: Weight for unobserved entries (default: 0.01)
- **λ**: Regularization parameter (default: 0.1)

---

## WALS Algorithm

**Weighted Alternating Least Squares (WALS)** is an optimization algorithm for WMF.

### Steps

#### 1. Initialization

```python
U = np.random.normal(0, 0.1, (M, k))  # Occupation embeddings
V = np.random.normal(0, 0.1, (N, k))  # Skill embeddings
```

#### 2. Fix V, Optimize U

For each occupation `i`:

```python
# Build linear system for u_i
A_obs = sum(w_{i,j} * v_j * v_j^T) for all j where (i,j) is observed
b_obs = sum(w_{i,j} * C_{i,j} * v_j) for all j where (i,j) is observed

# Unobserved term
A_nobs = w_0 * (V^T * V - A_obs)

# Regularization
A_reg = λ * I

# Solve: (A_obs + A_nobs + A_reg) * u_i = b_obs
u_i = solve(A, b)
```

#### 3. Fix U, Optimize V

For each skill `j`:

```python
# Build linear system for v_j
A_obs = sum(w_{i,j} * u_i * u_i^T) for all i where (i,j) is observed
b_obs = sum(w_{i,j} * C_{i,j} * u_i) for all i where (i,j) is observed

# Unobserved term
A_nobs = w_0 * (U^T * U - A_obs)

# Regularization
A_reg = λ * I

# Solve: (A_obs + A_nobs + A_reg) * v_j = b_obs
v_j = solve(A, b)
```

#### 4. Iterate

Repeat steps 2-3 until convergence or max iterations.

---

## Recommendation Process

### 1. Build Position Embedding

Given input skills for a position, compute the position embedding as the average of skill embeddings:

```python
u_position = mean([v_skill1, v_skill2, v_skill3, ...])
```

### 2. Predict Scores

For all skills, compute the prediction score:

```python
score[position, skill] = u_position^T · v_skill
```

### 3. Rank and Filter

- Sort skills by score (descending)
- Filter out skills already in the position
- Return top-k recommendations

---

## Matrix Types

### Binary Matrix (ESCO)

- **Values**: 0 or 1 (presence/absence)
- **Weights**: Uniform (w_{i,j} = 1.0)
- **Use case**: When importance is not available

### Weighted Matrix (ONET)

- **Values**: Continuous (1.00-5.00 for importance)
- **Weights**: Variable (w_{i,j} = importance)
- **Use case**: When importance/relevance is available

---

## Advantages of WALS

- **Guaranteed convergence**: Alternating optimization converges
- **Parallelizable**: Each row can be optimized independently
- **Efficient for sparse matrices**: Only processes non-zero entries
- **No learning rate**: Direct solution via linear systems
- **Interpretable**: Embeddings represent latent features

---

## Performance Considerations

### Training Time

- **Matrix size**: Larger matrices take longer
- **Factors**: More factors = longer training
- **Iterations**: More iterations = longer training
- **Sparsity**: Sparse matrices are faster

### Typical Times

| Matrix Size | Factors | Iterations | Time |
|-------------|---------|------------|------|
| 3K × 14K | 50 | 15 | 5-10 min |
| 3K × 14K | 100 | 15 | 10-20 min |
| 1K × 35 | 50 | 15 | 3-5 min |

### Error Reduction

- **Simple configs**: 60-70% error reduction
- **Medium configs**: 75-80% error reduction
- **Complex configs**: 80-85% error reduction

---

## References

- Lecture 9: Recommender Systems (WMF/WALS theory)
- Weighted Matrix Factorisation for Collaborative Filtering
- Alternating Least Squares for Matrix Factorisation
