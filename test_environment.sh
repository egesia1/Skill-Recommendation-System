#!/bin/bash
# Test script to verify the conda environment is set up correctly

ENV_NAME="skill_recommendation"

echo "=========================================="
echo "Testing Skill Recommendation Environment"
echo "=========================================="
echo ""

# Check if environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "$ENV_NAME" ]]; then
    echo "WARNING: Environment '${ENV_NAME}' is not activated."
    echo "Please activate it first:"
    echo "  conda activate ${ENV_NAME}"
    echo ""
    exit 1
fi

echo "Environment '${CONDA_DEFAULT_ENV}' is active"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1)
echo "  $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == *"3.12"* ]]; then
    echo "  Python 3.12 detected"
else
    echo "  WARNING: Expected Python 3.12, but found different version"
fi
echo ""

# Test imports
echo "Testing package imports..."

PACKAGES=("numpy" "scipy" "matplotlib" "jupyter" "ipykernel")

ALL_OK=true
for package in "${PACKAGES[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "  $package - OK"
    else
        echo "  $package - NOT FOUND"
        ALL_OK=false
    fi
done

echo ""

# Test project imports
echo "Testing project imports..."
if python -c "from src import wals, data_loader, trainer, recommender" 2>/dev/null; then
    echo "  Project modules - OK"
else
    echo "  WARNING: Project modules - some imports may have failed"
fi

echo ""

# Summary
if [ "$ALL_OK" = true ]; then
    echo "=========================================="
    echo "All tests passed! Environment is ready."
    echo "=========================================="
    echo ""
    echo "You can now:"
    echo "  1. Run the notebook: jupyter notebook complete_pipeline.ipynb"
    echo "  2. Train models: python examples/train_esco.py --help"
    echo "  3. Generate recommendations: python examples/recommend.py --help"
    echo ""
else
    echo "=========================================="
    echo "ERROR: Some packages are missing."
    echo "=========================================="
    echo ""
    echo "Please install missing packages:"
    echo "  conda install <package_name> -c conda-forge"
    echo "  or"
    echo "  pip install <package_name>"
    echo ""
    exit 1
fi
