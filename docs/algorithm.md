# WALS Algorithm Explanation

## Weighted Matrix Factorisation (WMF)

The goal is to factorize a sparse matrix $C$ (Occupation $\times$ Skill) into two low-rank matrices:

$$
C \approx U \cdot V^T
$$

Where:
- $C$: Original matrix ($M \times N$) - Occupation $\times$ Skill
- $U$: User factors ($M \times k$) - Occupation embeddings
- $V$: Item factors ($N \times k$) - Skill embeddings
- $k$: Number of latent factors (typically 20-100)

---

## 1. Standard WALS (Binary Data)

Used for **ESCO** where data is implicit binary feedback (present/absent).

### Objective Function

$$
\min_{U,V} \sum_{i,j \in \text{Obs}} (1 - u_i^T v_j)^2 + w_0 \sum_{i,j \in \text{Nobs}} (0 - u_i^T v_j)^2 + \lambda(\|U\|^2_F + \|V\|^2_F)
$$

**Interpretation:**
- **Observed entries ($C_{ij}=1$)**: We want the prediction $u_i^T v_j$ to be close to 1.
- **Unobserved entries ($C_{ij}=0$)**: We want the prediction to be close to 0, but with a much lower weight $w_0$ (confidence).
- **Weights**: Implicitly, $w_{ij}=1$ for observed and $w_{ij}=w_0$ for unobserved.

---

## 2. Weighted WALS (Confidence-Based)

Used for **O*NET** where we have explicit ratings (e.g., Importance 1-5) that serve as **confidence weights**.

### Objective Function

$$
\min_{U,V} \sum_{i,j \in \text{Obs}} w_{i,j}(1 - u_i^T v_j)^2 + w_0 \sum_{i,j \in \text{Nobs}} (0 - u_i^T v_j)^2 + \lambda(\|U\|^2_F + \|V\|^2_F)
$$

**Differences from Standard WALS:**
- **Target Value**: We still treat observed entries as **binary positives (target=1)**. We are not trying to predict the rating itself (e.g., 4.5).
- **Confidence Weights ($w_{ij}$)**: The rating determines **how confident** we are that this is a positive match. A task with Importance 5 has a higher weight in the loss function than a task with Importance 2.
- **Non-Relevant Weight ($w_0$)**: Weight for skills explicitly marked as not relevant. In ESCO/O*NET databases, **missing relations indicate "not relevant"**, not "not yet observed". A missing relation means the skill has been evaluated and determined to be non-relevant for that occupation. Consider using higher $w_0$ values (0.1-1.0) to better penalize predictions of high scores for non-relevant skills.

**Why this approach?**
In implicit feedback datasets like job descriptions, a high rating (Importance) doesn't necessarily mean "more of" a skill, but rather a "stronger signal" that the skill defines the job. This formulation allows the model to focus on reproducing the most critical skills while still learning from less important ones.

**Important Note on Missing Relations:**
Unlike typical recommendation systems (e.g., movie ratings) where missing entries mean "not yet observed", in ESCO/O*NET databases, missing relations explicitly mean "not relevant". For example, "brewing beer" is not relevant for a "Data Analyst" - the relation is missing because it has been evaluated and determined to be non-relevant, not because it hasn't been evaluated yet. This semantic difference should be reflected in the choice of $w_0$.

---

## WALS Optimization Steps

**Weighted Alternating Least Squares (WALS)** optimizes $U$ and $V$ iteratively.

### 1. Initialization
$$
U \sim \mathcal{N}(0, 0.1)^{M \times k}
$$
$$
V \sim \mathcal{N}(0, 0.1)^{N \times k}
$$

### 2. Fix V, Optimize U
For each occupation $i$, solve the ridge regression to find $u_i$:

$$
(A_{\text{obs}} + A_{\text{nobs}} + \lambda I) u_i = b_{\text{obs}}
$$

Where:
- **Weighted Gram matrix of V for observed items**:
  $$A_{\text{obs}} = \sum_{j \in \text{Obs}(i)} w_{i,j} v_j v_j^T$$

- **Weighted target vector (target=1)**:
  $$b_{\text{obs}} = \sum_{j \in \text{Obs}(i)} w_{i,j} \cdot 1 \cdot v_j$$

- **Contribution from unobserved items** (approximated for efficiency):
  $$A_{\text{nobs}} = w_0 \left( V^T V - \sum_{j \in \text{Obs}(i)} v_j v_j^T \right)$$

### 3. Fix U, Optimize V
Symmetric process for each skill $j$:

$$
(A_{\text{obs}} + A_{\text{nobs}} + \lambda I) v_j = b_{\text{obs}}
$$

Where:
- **Weighted Gram matrix of U for observed occupations**: $$A_{\text{obs}} = \sum_{i \in \text{Obs}(j)} w_{i,j} u_i u_i^T$$

- **Weighted target vector**: $$b_{\text{obs}} = \sum_{i \in \text{Obs}(j)} w_{i,j} \cdot 1 \cdot u_i$$

- **Contribution from unobserved occupations**: $$A_{\text{nobs}} = w_0 \left( U^T U - \sum_{i \in \text{Obs}(j)} u_i u_i^T \right)$$

### 4. Iterate
Repeat steps 2-3 until convergence (RMSE stabilizes) or max iterations is reached.

---

## Recommendation Process

### For New Occupations (Folding-in)

When creating a new "hybrid" profession that doesn't exist in the training data, we use **WALS folding-in** to find the optimal occupation embedding.

#### 1. Folding-in: Solve Linear System
Given input skills for a new position, solve the WALS linear system to find the optimal occupation vector $u_{\text{new}}$:

$$
(A_{\text{obs}} + A_{\text{nobs}} + \lambda I) u_{\text{new}} = b_{\text{obs}}
$$

Where:
- **Observed terms** (selected skills):
  $$A_{\text{obs}} = \sum_{j \in S_{\text{input}}} w_j v_j v_j^T$$
  $$b_{\text{obs}} = \sum_{j \in S_{\text{input}}} w_j \cdot 1 \cdot v_j$$
  
- **Unobserved terms** (non-selected skills, treated as non-relevant):
  $$A_{\text{nobs}} = w_0 \left( V^T V - A_{\text{obs}} \right)$$

- **Regularization**: $\lambda I$

This is the **correct method** for generative use cases where you want the system to "reason by analogy" using the learned structure from ESCO.

#### 2. Predict Scores
For all skills, compute the prediction score:

$$
\text{score}(\text{position}, \text{skill}_j) = u_{\text{new}}^T \cdot v_j
$$

#### 3. Rank and Filter
- Sort skills by score (descending)
- Filter out skills already in the position
- Return top-k recommendations

### Legacy Method: Simple Average (Not Recommended)

The simple average method:
$$
u_{\text{position}} = \frac{1}{|S_{\text{input}}|} \sum_{v \in S_{\text{input}}} v
$$

is an approximation that works but is **not optimal**. It doesn't account for:
- The regularization term
- The proper weighting of non-relevant skills ($w_0$)
- The optimal projection into the learned latent space

**Use folding-in for generative/profession creation use cases.**

---

## Implementation Details

### Binary Matrix (ESCO)
- **Data**: Occupation-Skill relations (Essential/Optional).
- **Weights**: $w_{ij} = 1.0$ for all relations.
- **Logic**: A skill is either required or not.

### Weighted Matrix (O*NET)
- **Data**: 
    - Tasks: Importance ratings (1.0 - 5.0).
    - Tech Skills: Derived weights (e.g., 5.0 for Hot Tech, 1.0 otherwise).
- **Weights**: $w_{ij} = \text{rating}$.
- **Logic**: "Importance" is treated as the confidence level. We are more penalized for missing a highly important task than a minor one.

---

## Performance Considerations

### Training Time
- **Matrix size**: Larger matrices take longer
- **Factors**: More factors = longer training ($O(k^3)$ matrix inversion)
- **Iterations**: Linear scaling
- **Sparsity**: Sparse matrices are faster (fewer observed terms to sum)

### Typical Metrics
| Dataset | Matrix Size | Factors | Time (CPU) |
|---------|-------------|---------|------------|
| ESCO | 3K $\times$ 14K | 50 | 5-10 min |
| O*NET (Tasks) | 1K $\times$ 18K | 50 | 3-5 min |
| O*NET (Tech) | 1K $\times$ 9K | 50 | 2-4 min |

### Convergence
- **Simple configs**: 60-70% error reduction
- **Medium configs**: 75-80% error reduction
- **Complex configs**: 80-85% error reduction

---

## References
- Lecture 9: Recommender Systems (WMF/WALS theory)
- Hu, Y., Koren, Y., & Volinsky, C. (2008). **Collaborative Filtering for Implicit Feedback Datasets**. (The foundational paper for WMF/WALS).
- Pan, R., et al. (2008). **One-Class Collaborative Filtering**.
