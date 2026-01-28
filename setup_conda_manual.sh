#!/bin/bash
# Manual setup script for Skill Recommendation System
# Alternative method if automatic setup fails

ENV_NAME="skill_recommendation"
PYTHON_VERSION="3.12"

echo "=========================================="
echo "Manual Conda Environment Setup"
echo "=========================================="
echo ""

echo "Step 1: Create base environment with Python ${PYTHON_VERSION}"
echo "Command: conda create -n ${ENV_NAME} python=${PYTHON_VERSION} -y"
read -p "Press Enter to continue or Ctrl+C to cancel..."
conda create -n ${ENV_NAME} python=${PYTHON_VERSION} -y

echo ""
echo "Step 2: Activate environment"
echo "Command: conda activate ${ENV_NAME}"
echo "Please run this command manually:"
echo "  conda activate ${ENV_NAME}"
echo ""

echo "Step 3: Install packages with conda"
echo "Command: conda install numpy scipy matplotlib jupyter ipykernel notebook -c conda-forge -y"
read -p "Press Enter to continue or Ctrl+C to cancel..."
conda install numpy scipy matplotlib jupyter ipykernel notebook -c conda-forge -y

echo ""
echo "Step 4: Install additional packages with pip (if needed)"
echo "Command: pip install -r requirements.txt"
read -p "Press Enter to continue or Ctrl+C to cancel..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Activate the environment:"
echo "  conda activate ${ENV_NAME}"
echo ""
