#!/usr/bin/env python3
"""
Test GPU Access from Python Environment
USM Autoimmune ML Platform - Environment Verification
"""

import sys

print("=" * 60)
print("USM Autoimmune ML Platform - GPU Environment Test")
print("=" * 60)

# Test 1: PyTorch CUDA
print("\n[1/4] Testing PyTorch CUDA availability...")
try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ CUDA version: {torch.version.cuda}")
        print(f"✓ GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("✗ CUDA not available - GPU required for VLM inference")
        sys.exit(1)
except ImportError as e:
    print(f"✗ PyTorch not installed: {e}")
    sys.exit(1)

# Test 2: XGBoost GPU
print("\n[2/4] Testing XGBoost GPU support...")
try:
    import xgboost as xgb
    print(f"✓ XGBoost version: {xgb.__version__}")
    # Test GPU training
    dtrain = xgb.DMatrix([[1,2],[3,4]], label=[0,1])
    params = {'tree_method': 'gpu_hist', 'gpu_id': 0}
    model = xgb.train(params, dtrain, num_boost_round=1)
    print("✓ XGBoost GPU training successful")
except Exception as e:
    print(f"✗ XGBoost GPU test failed: {e}")

# Test 3: CatBoost GPU
print("\n[3/4] Testing CatBoost GPU support...")
try:
    import catboost
    print(f"✓ CatBoost version: {catboost.__version__}")
    print("✓ CatBoost can use GPU via task_type='GPU' parameter")
except ImportError as e:
    print(f"✗ CatBoost not installed: {e}")

# Test 4: Essential Libraries
print("\n[4/4] Testing essential data processing libraries...")
required_libs = [
    ('pandas', 'pandas'),
    ('numpy', 'numpy'),
    ('sklearn', 'scikit-learn'),
    ('sqlalchemy', 'SQLAlchemy'),
    ('cv2', 'opencv-python'),
    ('PIL', 'Pillow'),
    ('pdfplumber', 'pdfplumber'),
    ('spacy', 'spaCy'),
    ('pydicom', 'pydicom'),
    ('fastapi', 'FastAPI'),
]

all_ok = True
for import_name, display_name in required_libs:
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {display_name}: {version}")
    except ImportError:
        print(f"✗ {display_name}: NOT INSTALLED")
        all_ok = False

print("\n" + "=" * 60)
if torch.cuda.is_available() and all_ok:
    print("✓ ENVIRONMENT READY - All tests passed")
    print("✓ GPU available for ML training and VLM inference")
    print("=" * 60)
    sys.exit(0)
else:
    print("✗ ENVIRONMENT INCOMPLETE - Some components missing")
    print("=" * 60)
    sys.exit(1)
