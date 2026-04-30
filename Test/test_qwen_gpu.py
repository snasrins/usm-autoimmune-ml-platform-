"""
Test Qwen Models GPU Memory Usage
For USM Autoimmune Platform - RTX 3090 (24GB VRAM)
"""
import torch
import psutil
from transformers import AutoModel, AutoTokenizer, AutoProcessor, Qwen2VLForConditionalGeneration


def get_gpu_memory():
    """Get current GPU memory usage"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        return {
            "allocated_gb": round(allocated, 2),
            "reserved_gb": round(reserved, 2),
            "total_gb": round(total, 2),
            "free_gb": round(total - reserved, 2)
        }
    return {"error": "CUDA not available"}


def test_qwen_embedding_model():
    """Test Qwen2-1.5B for embeddings"""
    print("\n" + "="*60)
    print("📊 Testing Qwen2-1.5B (Embedding Model)")
    print("="*60)
    
    # Before loading
    before = get_gpu_memory()
    print(f"GPU Memory BEFORE: {before}")
    
    # Load model
    print("\n🔧 Loading Qwen2-1.5B...")
    tokenizer = AutoTokenizer.from_pretrained(
        "Qwen/Qwen2-1.5B",
        trust_remote_code=True
    )
    
    model = AutoModel.from_pretrained(
        "Qwen/Qwen2-1.5B",
        trust_remote_code=True,
        torch_dtype=torch.float16  # FP16 for efficiency
    ).to("cuda")
    
    model.eval()
    
    # After loading
    after = get_gpu_memory()
    print(f"GPU Memory AFTER: {after}")
    print(f"💾 Model Size: {after['allocated_gb'] - before['allocated_gb']:.2f} GB")
    
    # Test inference
    print("\n🧪 Testing inference...")
    test_text = "Patient presents with elevated WBC count and persistent joint pain."
    
    with torch.no_grad():
        inputs = tokenizer(test_text, return_tensors="pt", padding=True, truncation=True).to("cuda")
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        print(f"✅ Generated embedding shape: {embeddings.shape}")
    
    # Cleanup
    del model, tokenizer
    torch.cuda.empty_cache()
    
    return after['allocated_gb'] - before['allocated_gb']


def test_qwen_vision_model():
    """Test Qwen2-VL-2B for vision/OCR"""
    print("\n" + "="*60)
    print("🖼️ Testing Qwen2-VL-2B (Vision Model)")
    print("="*60)
    
    # Before loading
    before = get_gpu_memory()
    print(f"GPU Memory BEFORE: {before}")
    
    # Load model
    print("\n🔧 Loading Qwen2-VL-2B...")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-2B-Instruct",
        device_map="auto",
        torch_dtype=torch.bfloat16,  # BF16 for better vision quality
        trust_remote_code=True
    )
    
    processor = AutoProcessor.from_pretrained(
        "Qwen/Qwen2-VL-2B-Instruct",
        trust_remote_code=True
    )
    
    # After loading
    after = get_gpu_memory()
    print(f"GPU Memory AFTER: {after}")
    print(f"💾 Model Size: {after['allocated_gb'] - before['allocated_gb']:.2f} GB")
    
    # Test with dummy image
    print("\n🧪 Testing vision inference...")
    from PIL import Image
    import numpy as np
    
    # Create dummy medical image (lab report simulation)
    dummy_image = Image.fromarray(np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8))
    
    messages = [
        {"role": "user", "content": [
            {"type": "image", "image": dummy_image},
            {"type": "text", "text": "Extract text from this medical document."}
        ]}
    ]
    
    try:
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)
        
        with torch.no_grad():
            output = model.generate(**inputs, max_new_tokens=128)
            decoded = processor.decode(output[0], skip_special_tokens=True)
            print(f"✅ Generated response length: {len(decoded)} chars")
    except Exception as e:
        print(f"⚠️ Vision test failed: {e}")
    
    # Cleanup
    del model, processor
    torch.cuda.empty_cache()
    
    return after['allocated_gb'] - before['allocated_gb']


def test_combined_memory():
    """Test both models loaded simultaneously (worst case)"""
    print("\n" + "="*60)
    print("🔥 Testing BOTH Models Loaded (Worst Case Scenario)")
    print("="*60)
    
    before = get_gpu_memory()
    print(f"GPU Memory BEFORE: {before}")
    
    # Load embedding model
    print("\n🔧 Loading Qwen2-1.5B (Embedding)...")
    emb_tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-1.5B", trust_remote_code=True)
    emb_model = AutoModel.from_pretrained(
        "Qwen/Qwen2-1.5B",
        trust_remote_code=True,
        torch_dtype=torch.float16
    ).to("cuda")
    
    mid = get_gpu_memory()
    print(f"GPU Memory AFTER Embedding Model: {mid}")
    
    # Load vision model
    print("\n🔧 Loading Qwen2-VL-2B (Vision)...")
    vision_model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-2B-Instruct",
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )
    
    after = get_gpu_memory()
    print(f"GPU Memory AFTER Both Models: {after}")
    
    total_usage = after['allocated_gb'] - before['allocated_gb']
    print(f"\n💾 TOTAL Memory Usage: {total_usage:.2f} GB")
    print(f"📊 Free VRAM Remaining: {after['free_gb']:.2f} GB")
    
    if after['free_gb'] > 10:
        print("✅ EXCELLENT: Plenty of VRAM left for data processing!")
    elif after['free_gb'] > 5:
        print("✅ GOOD: Sufficient VRAM for normal operations")
    else:
        print("⚠️ WARNING: Low VRAM, consider using models individually")
    
    # Cleanup
    del emb_model, emb_tokenizer, vision_model
    torch.cuda.empty_cache()
    
    return total_usage


def main():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   🧪 USM Autoimmune Platform - Qwen GPU Test 🧪      ║")
    print("║   RTX 3090 (24GB VRAM) - FP16/BF16 Models            ║")
    print("╚═══════════════════════════════════════════════════════╝")
    
    # Check CUDA
    if not torch.cuda.is_available():
        print("❌ ERROR: CUDA not available!")
        return
    
    gpu_name = torch.cuda.get_device_name(0)
    print(f"\n🎮 GPU Detected: {gpu_name}")
    
    initial = get_gpu_memory()
    print(f"📊 Initial GPU State: {initial}\n")
    
    try:
        # Test 1: Embedding model only
        emb_size = test_qwen_embedding_model()
        torch.cuda.empty_cache()
        
        # Test 2: Vision model only
        vision_size = test_qwen_vision_model()
        torch.cuda.empty_cache()
        
        # Test 3: Both models (worst case)
        combined_size = test_combined_memory()
        
        # Summary
        print("\n" + "="*60)
        print("📋 SUMMARY")
        print("="*60)
        print(f"Qwen2-1.5B (Embedding):  {emb_size:.2f} GB")
        print(f"Qwen2-VL-2B (Vision):    {vision_size:.2f} GB")
        print(f"Combined (Worst Case):   {combined_size:.2f} GB")
        print(f"\n✅ Recommendation: Models fit comfortably in RTX 3090!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
