# Skill Recommendation System

**Weighted Matrix Factorisation (WMF) using WALS Algorithm**

---

## Context & Problem

**The Challenge:**
When companies design new job positions, selecting the right set of skills and tasks from thousands of possibilities (e.g., ~14,000 in ESCO, ~18,000 in O*NET) is a complex and time-consuming challenge. HR managers often start with a few core competencies but struggle to identify related, complementary skills that define a complete role.

**Our Solution:**
We provide an intelligent recommendation engine that acts as a **co-pilot for job design**. As the user builds a job profile by adding initial skills or tasks, our system analyzes the latent relationships between occupations and skills to suggest the most relevant missing items in real-time.

**Real-World Application:**
This system is **already live in production** within the **[KS-Agents](https://ks-agents.com)** Soft HR application, where it powers the job creation workflow. It has also been successfully demonstrated in operation as a response to a **Call4Startup** promoted by a major multinational corporation, validating its effectiveness in enterprise scenarios.

---

## Overview

This is a standalone implementation of a skill recommendation system based on **Weighted Matrix Factorisation (WMF)** using the **Weighted Alternating Least Squares (WALS)** algorithm.

The system can:
- Train recommendation models on ESCO (European Skills) or ONET (US Occupational Network) databases
- Generate skill recommendations for job positions
- Work completely independently

---

## Features

- **Pure Python Implementation**: No external ML libraries required (only numpy, scipy)
- **WALS Algorithm**: Manual implementation of Weighted Alternating Least Squares
- **Weighted WALS**: Specialized implementation for O*NET using importance/confidence weights
- **Hyperparameter Tuning**: Grid search with train/val split and RMSE evaluation
- **ESCO Support**: Binary matrix (0/1) for occupation-skill relations
- **ONET Support**: Two models — occupation x task (IM importance as confidence) and occupation x technology skill (derived weight)
- **Standalone**: No framework dependencies
- **Production Ready**: Compatible output format for integration

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Setup Databases

#### 1. Download Data Files

**ESCO:**
- Download ESCO classification CSV ZIP files from [ESCO Portal](https://ec.europa.eu/esco/portal)
- Place ZIP files in `data/` directory (e.g., `data/esco_classification_en.zip`)

**ONET:**
- Download ONET database ZIP file from [ONET Resource Center](https://www.onetcenter.org/database.html)
- Place ZIP file in `data/` directory (e.g., `data/db_30_1_text.zip`)

#### 2. Create and Populate Databases

**ESCO:**
```bash
# Create database and import English data
python scripts/import_esco.py \
    --zip_path data/esco_classification_en.zip \
    --db_path data/esco.db \
    --language en

# Import additional languages (optional)
python scripts/import_esco.py \
    --zip_path data/esco_classification_it.zip \
    --db_path data/esco.db \
    --language it
```

**ONET:**
```bash
# Create database and import data (tasks + technology skills; use --recreate to replace existing)
python scripts/import_onet.py \
    --zip_path data/db_30_1_text.zip \
    --db_path data/onet.db \
    --recreate
```

### Train Models

**ESCO:**
```bash
python examples/train_esco.py \
    --db_path data/esco.db \
    --output_dir models \
    --language en
```

**ONET:** (trains both task and technology skill models by default)
```bash
python examples/train_onet.py \
    --db_path data/onet.db \
    --output_dir models
# Or train only one: --type task or --type tech_skill
```
Produces `models/onet_task_wmf_model.pkl` and `models/onet_tech_skill_wmf_model.pkl`.

### Generate Recommendations

```bash
python examples/recommend.py \
    --model_path models/esco_wmf_model_en.pkl \
    --skill_uris "skill_uri_1" "skill_uri_2" "skill_uri_3" \
    --top_k 20

# ONET task model: input = task IDs (e.g. "8823" "8824")
# ONET tech skill model: input = software/tool names (e.g. "Adobe Acrobat" "Microsoft Excel")
```

---

## Project Structure

```
skill_recommendation/
├── README.md                 # This file
├── PRESENTATION.md           # Presentation guide
├── requirements.txt          # Python dependencies
├── src/                      # Core source code
│   ├── __init__.py
│   ├── wals.py              # Standard WALS algorithm
│   ├── wals_weighted.py     # Weighted WALS (O*NET specific)
│   ├── onet_hyperparameter_search.py # Grid search & evaluation
│   ├── data_loader.py       # ESCO/ONET data loading
│   ├── trainer.py           # Model training
│   └── recommender.py       # Recommendation generation
├── scripts/                  # Database setup scripts
│   ├── create_esco_db.sql   # ESCO database schema
│   ├── create_onet_db.sql   # ONET database schema
│   ├── import_esco.py       # ESCO data import
│   └── import_onet.py       # ONET data import
├── examples/                 # Example scripts
│   ├── train_esco.py        # ESCO training example
│   ├── train_onet.py        # ONET training example
│   └── recommend.py         # Recommendation example
├── docs/                     # Documentation
│   └── algorithm.md         # Algorithm explanation
├── tests/                    # Unit tests
│   └── test_wals.py
└── data/                     # Data directory
    ├── esco.db              # ESCO database (created by import)
    ├── onet.db              # ONET database (created by import)
    └── *.zip                # ZIP files with source data
```

---

## Core Components

### 1. WALS Algorithms
#### Standard WALS (`src/wals.py`)
Manual implementation for binary matrices (ESCO).

#### Weighted WALS (`src/wals_weighted.py`)
Specialized implementation for O*NET that uses matrix values (Importance/Weight) as confidence weights ($w_{ij}$) and target $p_{ij}=1$.

### 2. Hyperparameter Search (`src/onet_hyperparameter_search.py`)
- Splits data into train/validation sets (e.g. 90/10)
- Performs grid search over factors, regularization, iterations, and w_0
- Evaluates models using RMSE on held-out observed entries

### 3. Data Loader (`src/data_loader.py`)

Loads ESCO or ONET data from SQLite databases.

**Functions:**
- `load_esco_data()`: Load ESCO occupations, skills, and relations
- `load_onet_task_data()`: Load ONET occupations, tasks, and occupation-task importance
- `load_onet_technology_skill_data()`: Load ONET occupations, technology skills, and derived weights

### 3. Trainer (`src/trainer.py`)

Trains WMF models and saves them in .pkl format.

**Functions:**
- `train_esco_model()`: Train model on ESCO data
- `train_onet_task_model()`: Train model on ONET occupation x task (IM scale)
- `train_onet_technology_skill_model()`: Train model on ONET occupation x technology skill

### 4. Recommender (`src/recommender.py`)

Generates skill recommendations from trained models.

**Functions:**
- `load_model()`: Load trained model from .pkl file
- `recommend_skills()`: Generate recommendations for input skills

---

## Algorithm

### Weighted Matrix Factorisation (O*NET)

For O*NET, we use **confidence-based** WMF where $w_{ij}$ comes from the data (Importance 1-5 or derived weights):

```
min_{U,V} ∑_{i,j ∈ Obs} w_{i,j}(1 - u_i^T v_j)² + 
         w_0 ∑_{i,j ∈ Nobs} (0 - u_i^T v_j)² + 
         λ(||U||²_F + ||V||²_F)
```

Where:
- **Target**: 1 for observed entries (occupation has this skill)
- **Weight ($w_{ij}$)**: Confidence level (e.g., Task Importance)
- **Weight ($w_0$)**: Confidence for unobserved entries (0.01, 0.05, 0.1)

### Standard WALS (ESCO)

Uses uniform weights ($w_{ij}=1$) for observed entries.

### WALS Algorithm Steps

1. **Initialize**: Random U and V matrices
2. **Fix V, optimize U**: Solve linear system for each row u_i
3. **Fix U, optimize V**: Solve linear system for each row v_j
4. **Iterate**: Repeat until convergence or max iterations

### Recommendation Process

1. **Build position embedding**: Average of existing skill embeddings
   ```python
   u_position = mean([v_skill1, v_skill2, v_skill3, ...])
   ```

2. **Predict scores**: For all skills
   ```python
   score[position, skill] = u_position^T · v_skill
   ```

3. **Rank and filter**: Sort by score, filter existing skills

---

## Usage Examples

### Example 1: Train ESCO Model

```python
from src.trainer import train_esco_model

result = train_esco_model(
    db_path='data/esco.db',
    output_dir='models',
    language='en',
    factors=50,
    regularization=0.1,
    iterations=15
)

print(f"Model saved to: {result['model_path']}")
print(f"Training time: {result['total_time']:.2f} seconds")
```

### Example 2: Generate Recommendations

```python
from src.recommender import load_model, recommend_skills

# Load model
model_data = load_model('models/esco_wmf_model_en.pkl')

# Input skills (URIs)
input_skills = [
    "http://data.europa.eu/esco/skill/...",
    "http://data.europa.eu/esco/skill/...",
    "http://data.europa.eu/esco/skill/..."
]

# Generate recommendations
recommendations = recommend_skills(
    model_data=model_data,
    input_skill_uris=input_skills,
    top_k=5
)

# Display results
for skill_uri, score in recommendations:
    print(f"{skill_uri}: {score:.4f}")
```

---

## Model Format

The trained model is saved as a `.pkl` file with the following structure:

```python
{
    'model': MockImplicitModel,      # Object with user_factors and item_factors
    'occupation_to_idx': {...},       # Mapping URI -> index
    'skill_to_idx': {...},            # Mapping URI -> index
    'idx_to_skill_uri': {...},        # Reverse mapping
    'idx_to_occupation_uri': {...},   # Reverse mapping
    'language': 'en',
    'factors': 50,
    'regularization': 0.1,
    'iterations': 15,
    'matrix_shape': (3042, 13939),
    'non_zero_entries': 126051
}
```

---

## Configuration

### Hardware Requirements

**Current Implementation:**
- **CPU-only**: Uses numpy/scipy (no GPU acceleration)
- **Storage**: ~200 MB for databases and models

**GPU Support:**
- Currently not implemented (CPU-only)
- For GPU acceleration, see `docs/GPU_SUPPORT.md`
- Would require modifications to use CuPy or JAX

### Training Parameters & Tuning

We use **Grid Search** to optimize hyperparameters:

| Parameter | Range explored | Description |
|-----------|----------------|-------------|
| `factors` | `[50, 100]` | Latent factors (k) |
| `regularization` | `[0.01, 0.1]` | Regularization (λ) |
| `iterations` | `[10, 15, 20]` | WALS iterations |
| `w_0` | `[0.01, 0.05, 0.1]` | Unobserved weight |

The notebook `complete_pipeline.ipynb` includes a section to run this grid search and automatically select the best parameters.

---

## Testing

Run unit tests:

```bash
python -m pytest tests/
```

---

## Documentation

- **Algorithm**: `docs/algorithm.md` - Detailed algorithm explanation
- **Data Setup**: `DATA_SETUP.md` - Guide for downloading and importing ESCO/ONET data
- **Presentation**: `PRESENTATION.md` - A more discursive guide that explains and presents the system

---

## Integration

The generated `.pkl` files can be integrated into other systems. Example path:

```
models/esco_wmf_model_{language}.pkl
```

---

## License

Internal use only.

---

## Author

Luca Ricatti

---

**Date**: 29th January 2026
