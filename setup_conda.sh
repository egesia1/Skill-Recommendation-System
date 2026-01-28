#!/bin/bash
# Setup script for Skill Recommendation System
# Creates conda environment with Python 3.12 and installs all dependencies

set -e  # Exit on error

ENV_NAME="skill_recommendation"
PYTHON_VERSION="3.12"

echo "=========================================="
echo "Skill Recommendation System - Conda Setup"
echo "=========================================="
echo ""

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "ERROR: conda is not installed or not in PATH"
    echo "Please install Miniconda or Anaconda first:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "Conda found: $(conda --version)"
echo ""

# Check if environment already exists (suppress errors)
if conda env list 2>/dev/null | grep -q "^${ENV_NAME} "; then
    echo "WARNING: Environment '${ENV_NAME}' already exists"
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda env remove -n ${ENV_NAME} -y
    else
        echo "Using existing environment. Activate it with:"
        echo "  conda activate ${ENV_NAME}"
        exit 0
    fi
fi

echo "Creating conda environment '${ENV_NAME}' with Python ${PYTHON_VERSION}..."
echo "This may take a few minutes depending on your internet connection..."
echo ""

# Try to create environment, handle errors gracefully
if conda env create -f environment.yml 2>&1; then
    SUCCESS=true
else
    SUCCESS=false
    echo ""
    echo "WARNING: Automatic creation failed. Trying alternative method..."
    echo ""
    
    # Alternative: create with conda create then install packages
    echo "Creating base environment..."
    if conda create -n ${ENV_NAME} python=${PYTHON_VERSION} -y 2>&1; then
        echo "Installing packages..."
        conda activate ${ENV_NAME} || source activate ${ENV_NAME} || true
        conda install -n ${ENV_NAME} numpy scipy matplotlib jupyter ipykernel notebook -c conda-forge -y
        pip install numpy scipy matplotlib jupyter ipykernel notebook
        SUCCESS=true
    fi
fi

if [ "$SUCCESS" = true ]; then
    echo ""
    echo "Environment created successfully!"
    echo ""
else
    echo ""
    echo "ERROR: Failed to create environment automatically."
    echo ""
    echo "Please try manual setup:"
    echo "  1. conda create -n ${ENV_NAME} python=${PYTHON_VERSION}"
    echo "  2. conda activate ${ENV_NAME}"
    echo "  3. conda install numpy scipy matplotlib jupyter ipykernel notebook -c conda-forge"
    echo "  4. pip install -r requirements.txt"
    echo ""
    exit 1
fi
echo "=========================================="
echo "Next steps:"
echo "=========================================="
echo ""
echo "1. Activate the environment:"
echo "   conda activate ${ENV_NAME}"
echo ""
echo "2. Verify installation:"
echo "   python --version"
echo "   python -c 'import numpy, scipy, matplotlib, jupyter; print(\"All packages installed\")'"
echo ""
echo "3. Start Jupyter notebook:"
echo "   jupyter notebook"
echo ""
echo "4. Or run the complete pipeline notebook:"
echo "   jupyter notebook complete_pipeline.ipynb"
echo ""
echo "=========================================="
