# Skill Recommendation System - Presentation Guide

## Context & Use Case

**The Problem:**
When companies design new job positions, selecting the right set of skills and tasks from thousands of possibilities (e.g., ~14,000 in ESCO, ~18,000 in O*NET) is a complex and time-consuming challenge. HR managers often start with a few core competencies but struggle to identify related, complementary skills that define a complete role.

**Our Solution:**
We provide an intelligent recommendation engine that acts as a co-pilot for job design. As the user builds a job profile by adding initial skills or tasks, our system analyzes the latent relationships between occupations and skills to suggest the most relevant missing items in real-time.

**Real-World Application:**
This system is **already live in production** within the **[KS-Agents](https://ks-agents.com)** Soft HR application, where it powers the job creation workflow. It has also been successfully demonstrated in operation as a response to a **Call4Startup** promoted by a major multinational corporation, validating its effectiveness in enterprise scenarios.

---

## Quick Overview

**What it does:**
- Recommends skills for job positions using Matrix Factorisation
- Trains on ESCO (European Skills) or ONET (US Occupational Network) databases
- Uses WALS (Weighted Alternating Least Squares) algorithm

**Key Features:**
- Pure Python (only numpy, scipy)
- **Weighted WALS**: Uses importance/confidence weights
- **Auto-Tuning**: Built-in Grid Search for hyperparameters
- Standalone & Production-ready

---

## Architecture

```
Input: Occupation-Skill Relations (Database)
    ↓
Sparse Matrix Construction (Occupation × Skill)
    ↓
WALS Training (Matrix Factorisation)
    ↓
Embeddings: U (Occupations) × V (Skills)
    ↓
Recommendation: Position Embedding → Skill Scores
```

---

## Core Components

### 1. WALS Algorithm (`src/wals*.py`)
- **Standard**: For binary data (ESCO)
- **Weighted**: For O*NET, uses Importance as confidence ($w_{ij}$)
- Alternates between optimizing U and V

### 2. Hyperparameter Search (`src/onet_hyperparameter_search.py`)
- Splits data (Train/Val)
- Optimizes factors, regularization, iterations, w_0
- Evaluates using RMSE on held-out data

### 3. Data Loader (`src/data_loader.py`)
- Loads ESCO or ONET data from SQLite
- Builds occupation-skill relations
- Handles binary (ESCO) or weighted (ONET) matrices

### 3. Trainer (`src/trainer.py`)
- Trains WMF models
- Saves models in .pkl format
- Supports ESCO and ONET

### 4. Recommender (`src/recommender.py`)
- Loads trained models
- Generates recommendations from input skills
- Returns ranked skill suggestions

---

## Demo Flow

### Step 1: Tune & Train Model

**Notebook:** `complete_pipeline.ipynb`

1. **Hyperparameter Search**:
   - Run grid search (36 combinations)
   - Auto-select best params (e.g. factors=100, w_0=0.05)

2. **Training**:
   - Train final model using best parameters
   - Saves `.pkl` files to `models/`

### Step 2: Generate Recommendations

```bash
python examples/recommend.py \
    --model_path models/esco_wmf_model_en.pkl \
    --skill_uris "skill_uri_1" "skill_uri_2" "skill_uri_3" \
    --top_k 20
```

**Output:** Ranked list of recommended skills with scores

---

## Algorithm Highlights

### Matrix Factorisation

```
C (Occupation × Skill) ≈ U (Occupation embeddings) × V^T (Skill embeddings)
```

### WALS Process

1. **Initialize**: Random U and V
2. **Fix V, optimize U**: Solve linear system for each occupation
3. **Fix U, optimize V**: Solve linear system for each skill
4. **Iterate**: Until convergence

### Recommendation

1. **Position Embedding**: Average of input skill embeddings
2. **Score Prediction**: `score = u_position^T · v_skill`
3. **Ranking**: Sort by score, filter existing, return top-k

---

## Key Points for Presentation

### 1. Standalone System
- No dependencies on frameworks
- Can run on any machine with Python + numpy/scipy
- Perfect for demos and presentations

### 2. Manual Implementation
- Full control over algorithm
- Easy to understand and modify
- No black-box ML libraries

### 3. Production Ready
- Compatible output format
- Can integrate with other systems
- Scalable to large datasets

### 4. Flexible
- Supports binary (ESCO) and weighted (ONET) matrices
- Configurable parameters (factors, regularization, iterations)
- Works with different skill databases

---

## Performance Metrics

### Training Times
- **ESCO** (3K × 14K): 5-10 minutes
- **ONET** (1K × 35): 3-5 minutes

### Error Reduction
- **Simple**: 60-70%
- **Medium**: 75-80%
- **Complex**: 80-85%

### Model Sizes
- **ESCO**: 2-10 MB
- **ONET**: 0.2-1 MB

---

## Presentation Script

### Introduction (1 min)
- Problem: How to recommend skills for job positions?
- Solution: Matrix Factorisation using WALS algorithm
- Key advantage: Standalone system

### Architecture (2 min)
- Show diagram: Database → Matrix → Training → Embeddings → Recommendations
- Explain sparse matrix construction
- Explain WALS optimization

### Demo (3 min)
1. Show training command
2. Show training progress (iterations, error reduction)
3. Show recommendation generation
4. Display results with scores

### Technical Details (2 min)
- WALS algorithm steps
- Matrix factorisation objective
- Recommendation process

### Q&A (2 min)

---

## File Structure for Demo

```
skill_recommendation/
├── README.md              # Overview
├── src/                    # Core code
│   ├── wals.py            # Algorithm
│   ├── data_loader.py     # Data loading
│   ├── trainer.py         # Training
│   └── recommender.py     # Recommendations
├── examples/              # Demo scripts
│   ├── train_esco.py
│   ├── train_onet.py
│   └── recommend.py
└── docs/                   # Documentation
    └── algorithm.md
```

---

## Key Messages

1. **Standalone**: No framework dependencies, pure Python
2. **Manual**: Full control, easy to understand
3. **Production Ready**: Compatible with existing systems
4. **Flexible**: Works with ESCO and ONET databases
5. **Efficient**: Fast training and recommendation generation

---

**Ready for Presentation!**
