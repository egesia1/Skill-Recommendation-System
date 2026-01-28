# Environment Setup Guide

## Conda Environment Setup

This project uses a Conda environment with Python 3.12 for dependency management.

### Quick Setup

**Option 1: Automated Setup (Recommended)**

Run the automated setup script:

```bash
./setup_conda.sh
```

This will:
1. Check if conda is installed
2. Create a new conda environment named `skill_recommendation`
3. Install Python 3.12 and all required packages

**Option 2: Manual Setup (If automated fails)**

If the automated script fails due to network or permission issues, use manual setup:

```bash
# Step 1: Create environment
conda create -n skill_recommendation python=3.12 -y

# Step 2: Activate environment
conda activate skill_recommendation

# Step 3: Install packages with conda
conda install numpy scipy matplotlib jupyter ipykernel notebook -c conda-forge -y

# Step 4: Install any additional packages with pip
pip install -r requirements.txt
```

Or use the interactive manual script:

```bash
./setup_conda_manual.sh
```

### Manual Setup

If you prefer to set up manually:

```bash
# Create environment from environment.yml
conda env create -f environment.yml

# Activate environment
conda activate skill_recommendation

# Verify installation
python --version  # Should show Python 3.12.x
python -c "import numpy, scipy, matplotlib, jupyter; print('All packages installed')"
```

### Activating the Environment

After setup, activate the environment:

```bash
conda activate skill_recommendation
```

### Installing Additional Packages

If you need to install additional packages:

```bash
# Using conda
conda install package_name

# Using pip (within conda environment)
pip install package_name
```

### Running the Notebook

Once the environment is activated:

```bash
# Start Jupyter notebook
jupyter notebook

# Or open the complete pipeline notebook directly
jupyter notebook complete_pipeline.ipynb
```

### Deactivating the Environment

To deactivate the conda environment:

```bash
conda deactivate
```

### Removing the Environment

To remove the environment:

```bash
conda env remove -n skill_recommendation
```

### Troubleshooting

**Issue: conda command not found**
- Install Miniconda or Anaconda: https://docs.conda.io/en/latest/miniconda.html
- Make sure conda is in your PATH

**Issue: Environment creation fails**
- Check your internet connection (conda needs to download packages)
- Try updating conda: `conda update conda`
- Check if Python 3.12 is available: `conda search python=3.12`

**Issue: Package import errors**
- Make sure the environment is activated: `conda activate skill_recommendation`
- Verify packages are installed: `conda list`
- Reinstall packages: `conda env update -f environment.yml --prune`

### Environment Files

- `environment.yml` - Conda environment specification
- `requirements.txt` - Pip requirements (for reference, conda handles most packages)
- `.gitignore` - Excludes conda environment directories from git

---

**Note:** The conda environment directory is excluded from git. Each developer should create their own environment locally.
