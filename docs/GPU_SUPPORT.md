# GPU Support for WALS Training

## Current Status

The current WALS implementation uses **CPU-only** computation with:
- `numpy` for array operations
- `scipy` for sparse matrices and linear algebra

## Why CPU-Only?

The implementation was designed to be:
- **Standalone**: No external ML framework dependencies
- **Simple**: Pure Python with numpy/scipy
- **Portable**: Works on any machine with Python

## Adding GPU Support

If you want to accelerate training with GPU, you have several options:

### Option 1: CuPy (Recommended for NumPy-like API)

CuPy provides a NumPy-compatible API that runs on GPU.

**Installation:**
```bash
# For CUDA 12.x
pip install cupy-cuda12x

# For CUDA 11.x
pip install cupy-cuda11x

# For CUDA 10.x
pip install cupy-cuda10x
```

**Code Changes:**
```python
# In src/wals.py, replace:
import numpy as np

# With:
try:
    import cupy as np
    import cupyx.scipy.sparse as sparse_module
    import cupyx.scipy.linalg as linalg_module
    GPU_AVAILABLE = True
except ImportError:
    import numpy as np
    from scipy import sparse as sparse_module
    from scipy import linalg as linalg_module
    GPU_AVAILABLE = False
```

**Modifications needed:**
1. Replace `csr_matrix` with `cupyx.scipy.sparse.csr_matrix`
2. Replace `scipy.linalg.solve` with `cupyx.scipy.linalg.solve`
3. Move arrays to GPU: `array_gpu = np.asarray(array_cpu)`
4. Move arrays back to CPU when saving: `array_cpu = np.asnumpy(array_gpu)`

### Option 2: JAX

JAX provides NumPy-like API with GPU/TPU support and automatic differentiation.

**Installation:**
```bash
# CPU only
pip install jax jaxlib

# With CUDA support
pip install jax[cuda12] -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
```

**Code Changes:**
- Replace numpy operations with JAX equivalents
- Use `jax.numpy` instead of `numpy`
- Use `jax.scipy.linalg` instead of `scipy.linalg`

### Option 3: PyTorch / TensorFlow

For more advanced GPU acceleration, you could rewrite using PyTorch or TensorFlow, but this would require significant code changes.

## Performance Considerations

**When GPU helps:**
- Large matrices (10K+ rows/columns)
- Many iterations (20+)
- High factor counts (100+)

**When CPU is sufficient:**
- Small to medium matrices (<5K rows/columns)
- Few iterations (<15)
- Low factor counts (<50)

**Current typical performance (CPU):**
- ESCO (3K × 14K): 5-10 minutes
- ONET (1K × 35): 3-5 minutes

**Expected GPU speedup:**
- 2-5x faster for large matrices
- Depends on GPU model and matrix size

## Testing GPU Setup

If you've added GPU support, test it:

```python
import cupy as np
print(f"CuPy version: {np.__version__}")
print(f"CUDA available: {np.cuda.is_available()}")
print(f"CUDA device: {np.cuda.Device().id}")
print(f"GPU memory: {np.cuda.Device().mem_info}")
```

## Notes

- GPU memory is limited - very large matrices may not fit
- Data transfer CPU↔GPU has overhead - only worth it for large computations
- Current implementation loops over rows/columns - may not fully utilize GPU parallelism
- For maximum GPU utilization, consider batch processing or vectorized operations

## Implementation Status

**Current:** CPU-only (numpy/scipy)  
**Planned:** Optional GPU support via CuPy (not yet implemented)

If you need GPU support, you can:
1. Modify `src/wals.py` to use CuPy (see Option 1 above)
2. Or use a GPU-accelerated library like `implicit` (which uses Cython/CUDA)
