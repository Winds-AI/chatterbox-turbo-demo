import os
import sys

def patch_chatterbox():
    # Locate the file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(base_dir, ".venv_chatterbox", "Lib", "site-packages", "chatterbox", "tts_turbo.py")
    
    if not os.path.exists(target_file):
        print(f"Error: File not found at {target_file}")
        return

    print(f"Patching {target_file}...")
    
    with open(target_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    new_lines = []
    patched_init = False
    patched_generate = False
    
    for line in lines:
        # Patch __init__
        if "self.watermarker = perth.PerthImplicitWatermarker()" in line:
            new_lines.append(line.replace("self.watermarker", "# self.watermarker"))
            patched_init = True
            print("Disabled watermarker setup in __init__")
            continue
            
        # Patch generate
        if "watermarked_wav = self.watermarker.apply_watermark(wav, sample_rate=self.sr)" in line:
            new_lines.append("        watermarked_wav = wav # self.watermarker.apply_watermark(wav, sample_rate=self.sr)\n")
            patched_generate = True
            print("Disabled watermarker usage in generate")
            continue
            
        new_lines.append(line)
        
    if patched_init and patched_generate:
        with open(target_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("Successfully patched tts_turbo.py")
    else:
        print("Warning: Could not find all targets to patch.")
        if not patched_init: print("- Failed to find __init__ line")
        if not patched_generate: print("- Failed to find generate line")

if __name__ == "__main__":
    patch_chatterbox()
