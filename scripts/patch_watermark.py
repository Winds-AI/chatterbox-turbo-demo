import os
import sys


def patch_chatterbox():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    site_packages = os.path.join(
        base_dir,
        ".venv_chatterbox",
        "Lib",
        "site-packages",
        "chatterbox",
        "tts_turbo.py",
    )

    if not os.path.exists(site_packages):
        print(f"Error: File not found at {site_packages}")
        return

    print(f"Patching {site_packages}...")

    with open(site_packages, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Remove perth import
    content = content.replace("import perth\n", "")

    # Comment out watermarker initialization
    content = content.replace(
        "self.watermarker = perth.PerthImplicitWatermarker()",
        "# self.watermarker = perth.PerthImplicitWatermarker()",
    )

    # Comment out watermarker usage
    content = content.replace(
        "watermarked_wav = self.watermarker.apply_watermark(wav, sample_rate=self.sr)",
        "watermarked_wav = wav # self.watermarker.apply_watermark(wav, sample_rate=self.sr)",
    )

    if content != original_content:
        with open(site_packages, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully patched tts_turbo.py")
    else:
        print("No changes needed - already patched")


if __name__ == "__main__":
    patch_chatterbox()
