"""
Test ML Inference with GPU
Tests the complete ML pipeline including GPU acceleration
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import time
from app.ml.inference import get_inference_engine


def test_gpu_availability():
    """Test if GPU is available"""
    print("=" * 60)
    print("GPU Availability Test")
    print("=" * 60)
    
    if torch.cuda.is_available():
        print(f"✓ GPU is available!")
        print(f"  Device: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA Version: {torch.version.cuda}")
        print(f"  Total Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        return True
    else:
        print("✗ GPU is NOT available - using CPU")
        return False


def test_inference():
    """Test ML inference"""
    print("\n" + "=" * 60)
    print("ML Inference Test")
    print("=" * 60)
    
    # Initialize engine
    print("\nInitializing inference engine...")
    engine = get_inference_engine()
    print(f"✓ Engine initialized on device: {engine.device}")
    
    # Create dummy test data
    test_features = {f"feature_{i}": float(i * 0.1) for i in range(20)}
    
    print("\nRunning single prediction...")
    start_time = time.time()
    prediction, confidence, probabilities, inference_time = engine.predict(test_features)
    total_time = (time.time() - start_time) * 1000
    
    print(f"✓ Prediction completed!")
    print(f"  Predicted Class: {prediction}")
    print(f"  Confidence: {confidence:.4f}")
    print(f"  Inference Time: {inference_time:.2f} ms")
    print(f"  Total Time: {total_time:.2f} ms")
    print(f"\nClass Probabilities:")
    for class_name, prob in probabilities.items():
        print(f"  {class_name}: {prob:.4f}")
    
    return True


def test_batch_inference():
    """Test batch inference"""
    print("\n" + "=" * 60)
    print("Batch Inference Test")
    print("=" * 60)
    
    engine = get_inference_engine()
    
    # Create batch of test data
    batch_size = 10
    batch_features = [
        {f"feature_{i}": float(i * 0.1 + j * 0.01) for i in range(20)}
        for j in range(batch_size)
    ]
    
    print(f"\nRunning batch prediction ({batch_size} samples)...")
    start_time = time.time()
    results = engine.batch_predict(batch_features)
    total_time = (time.time() - start_time) * 1000
    
    print(f"✓ Batch prediction completed!")
    print(f"  Total Samples: {batch_size}")
    print(f"  Total Time: {total_time:.2f} ms")
    print(f"  Avg Time per Sample: {total_time / batch_size:.2f} ms")
    
    # Show sample results
    print(f"\nSample Results (first 3):")
    for i, (pred, conf, probs, inf_time) in enumerate(results[:3]):
        print(f"  Sample {i+1}: {pred} (confidence: {conf:.4f}, time: {inf_time:.2f}ms)")
    
    return True


def test_gpu_memory():
    """Test GPU memory usage"""
    if not torch.cuda.is_available():
        return False
    
    print("\n" + "=" * 60)
    print("GPU Memory Test")
    print("=" * 60)
    
    print(f"\nMemory Allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
    print(f"Memory Reserved: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB")
    print(f"Max Memory Allocated: {torch.cuda.max_memory_allocated(0) / 1024**2:.2f} MB")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("USM Autoimmune ML Platform - GPU & ML Test Suite")
    print("=" * 60)
    
    # Run tests
    gpu_available = test_gpu_availability()
    inference_ok = test_inference()
    batch_ok = test_batch_inference()
    
    if gpu_available:
        test_gpu_memory()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"GPU Available: {'✓ Yes' if gpu_available else '✗ No (using CPU)'}")
    print(f"Inference Test: {'✓ Passed' if inference_ok else '✗ Failed'}")
    print(f"Batch Test: {'✓ Passed' if batch_ok else '✗ Failed'}")
    print("\n✓ All tests completed successfully!")
    print("=" * 60)
