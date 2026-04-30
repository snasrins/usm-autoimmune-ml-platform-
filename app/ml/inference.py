"""
GPU-Accelerated ML Inference Engine
"""
# Optional torch imports
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

import numpy as np
from typing import Dict, List, Tuple, Optional
import time
import os
from pathlib import Path


if TORCH_AVAILABLE:
    class AutoimmuneClassifier(nn.Module):
        """
        Simple Neural Network for Autoimmune Disease Classification
        This is a demo model - replace with your actual trained model
        """
        def __init__(self, input_dim: int = 20, hidden_dim: int = 128, num_classes: int = 5):
            super(AutoimmuneClassifier, self).__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(hidden_dim // 2, num_classes),
                nn.Softmax(dim=1)
            )
        
        def forward(self, x):
            return self.network(x)


    class InferenceEngine:
        """GPU-accelerated inference engine"""
        
        def __init__(self, model_path: str = None):
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = None
            self.model_version = "1.0.0"
            self.class_names = ["SLE", "Rheumatoid Arthritis", "Sjogren's", "Scleroderma", "Mixed CTD"]
            
            if model_path and os.path.exists(model_path):
                self.load_model(model_path)
            else:
                # Initialize with demo model
                self.model = AutoimmuneClassifier(input_dim=20, hidden_dim=128, num_classes=5)
                self.model.to(self.device)
                self.model.eval()
            
            print(f"Inference Engine initialized on device: {self.device}")
        
        def load_model(self, model_path: str):
            """Load a trained model from disk"""
            try:
                self.model = torch.load(model_path, map_location=self.device)
                self.model.eval()
                print(f"Model loaded from {model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                # Fallback to demo model
                self.model = AutoimmuneClassifier()
                self.model.to(self.device)
                self.model.eval()
        
        def preprocess_features(self, features: Dict[str, float]) -> torch.Tensor:
            """Convert feature dictionary to tensor"""
            # Extract feature values in consistent order
            feature_values = [features.get(f"feature_{i}", 0.0) for i in range(20)]
            tensor = torch.tensor([feature_values], dtype=torch.float32)
            return tensor.to(self.device)
        
        def predict(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float], float]:
            """
            Make a single prediction
            
            Returns:
                prediction: predicted class name
                confidence: confidence score
                probabilities: probability distribution over classes
                inference_time_ms: inference time in milliseconds
            """
            start_time = time.time()
            
            # Preprocess
            input_tensor = self.preprocess_features(features)
            
            # Inference
            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = output.cpu().numpy()[0]
            
            # Post-process
            predicted_class_idx = np.argmax(probabilities)
            predicted_class = self.class_names[predicted_class_idx]
            confidence = float(probabilities[predicted_class_idx])
            
            prob_dict = {
                class_name: float(prob) 
                for class_name, prob in zip(self.class_names, probabilities)
            }
            
            inference_time_ms = (time.time() - start_time) * 1000
            
            return predicted_class, confidence, prob_dict, inference_time_ms
        
        def batch_predict(self, features_list: List[Dict[str, float]]) -> List[Tuple]:
            """Make batch predictions"""
            results = []
            for features in features_list:
                result = self.predict(features)
                results.append(result)
            return results
        
        def get_gpu_info(self) -> Dict:
            """Get GPU information"""
            if torch.cuda.is_available():
                return {
                    "gpu_available": True,
                    "gpu_name": torch.cuda.get_device_name(0),
                    "gpu_memory_allocated": torch.cuda.memory_allocated(0) / 1024**2,  # MB
                    "gpu_memory_reserved": torch.cuda.memory_reserved(0) / 1024**2,  # MB
                    "cuda_version": torch.version.cuda
                }
            return {"gpu_available": False}

else:
    # Stub implementation when torch is not available
    class InferenceEngine:
        """Stub inference engine (PyTorch not available)"""
        
        def __init__(self, model_path: str = None):
            self.model_version = "stub"
            self.class_names = ["SLE", "Rheumatoid Arthritis", "Sjogren's", "Scleroderma", "Mixed CTD"]
            print("Warning: PyTorch not available. ML inference disabled.")
        
        def predict(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float], float]:
            """Stub predict method"""
            raise RuntimeError("ML inference not available - PyTorch not installed")
        
        def batch_predict(self, features_list: List[Dict[str, float]]) -> List[Tuple]:
            """Stub batch predict method"""
            raise RuntimeError("ML inference not available - PyTorch not installed")
        
        def get_gpu_info(self) -> Dict:
            """Return stub GPU info"""
            return {"gpu_available": False, "error": "PyTorch not installed"}

# Global inference engine instance
_inference_engine = None


def get_inference_engine() -> Optional[InferenceEngine]:
    """Get or create global inference engine"""
    global _inference_engine
    if _inference_engine is None:
        model_path = os.getenv("MODEL_PATH", "/models/autoimmune_classifier.pt")
        _inference_engine = InferenceEngine(model_path)
    return _inference_engine
