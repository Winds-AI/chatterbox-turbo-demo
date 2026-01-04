import os
import torch


def unload_model_from_gpu():
    print("=" * 60)
    print("Chatterbox Turbo - Model De-Load")
    print("=" * 60)
    print()

    if not torch.cuda.is_available():
        print("[De-Load] CUDA is not available. Nothing to de-load from GPU.")
        return

    print(f"[De-Load] CUDA Available: Yes")
    print(f"[De-Load] GPU Count: {torch.cuda.device_count()}")
    print()

    for i in range(torch.cuda.device_count()):
        print(f"[De-Load] GPU {i}: {torch.cuda.get_device_name(i)}")
        memory_allocated = torch.cuda.memory_allocated(i)
        memory_reserved = torch.cuda.memory_reserved(i)

        print(f"  Memory Allocated: {memory_allocated / 1024**3:.2f} GB")
        print(f"  Memory Reserved: {memory_reserved / 1024**3:.2f} GB")

    print()
    choice = input("Unload all models and clear GPU memory? (y/N): ").strip().lower()

    if choice == "y":
        print()
        print("[De-Load] Clearing GPU cache...")
        torch.cuda.empty_cache()

        print("[De-Load] Running garbage collection...")
        import gc

        gc.collect()

        for i in range(torch.cuda.device_count()):
            memory_after = torch.cuda.memory_allocated(i)
            print(f"  GPU {i} Memory after cleanup: {memory_after / 1024**3:.2f} GB")

        print()
        print("[De-Load] Models unloaded from GPU.")
        print("[De-Load] Note: Python libraries (torch, torchaudio) remain installed.")
        print("[De-Load] To free library space, run: python cleanup.py")
    else:
        print("[De-Load] Aborted.")


if __name__ == "__main__":
    unload_model_from_gpu()
