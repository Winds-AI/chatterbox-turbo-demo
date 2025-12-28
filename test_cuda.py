#!/usr/bin/env python3
"""
Test script to verify PyTorch CUDA installation
"""
import torch

print("=" * 50)
print("PyTorch CUDA Verification")
print("=" * 50)

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"GPU {i} Memory: {torch.cuda.get_device_properties(i).total_memory // 1024**3} GB")

    # Test tensor operations on GPU
    print("\nTesting GPU tensor operations...")
    try:
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.mm(x, y)
        print("✓ GPU tensor operations successful")
    except Exception as e:
        print(f"✗ GPU tensor operations failed: {e}")

else:
    print("❌ CUDA not available - PyTorch installed without GPU support")
    print("Please reinstall PyTorch with CUDA support:")
    print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")

print("=" * 50)
