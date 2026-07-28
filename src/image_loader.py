import os
import subprocess
import tkinter as tk
from src.config import IMAGE_CANDIDATES, ASSETS_DIR


def find_user_image():
    """Locate user image file (robot.png, robot.jpg, etc.)."""
    for path in IMAGE_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


def prepare_and_load_image(max_w=380, max_h=210):
    """
    Load user image for Tkinter Canvas.
    Handles PIL if available, or falls back to ImageMagick / ffmpeg conversion to PNG
    so standard Tkinter PhotoImage can render JPG/PNG seamlessly.
    """
    img_path = find_user_image()
    if not img_path:
        return None

    # Try PIL / Pillow first if installed
    try:
        from PIL import Image, ImageEnhance, ImageTk
        pil_img = Image.open(img_path).convert("RGBA")
        ratio = min(max_w / pil_img.width, max_h / pil_img.height, 1.0)
        new_size = (max(1, int(pil_img.width * ratio)), max(1, int(pil_img.height * ratio)))
        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
        pil_img = ImageEnhance.Contrast(ImageEnhance.Brightness(pil_img).enhance(0.95)).enhance(1.1)
        return ImageTk.PhotoImage(pil_img)
    except ImportError:
        pass
    except Exception as e:
        print(f"[ARC-GHOST Image] PIL load error: {e}")

    # Fallback without PIL: prepare a scaled PNG using CLI tools (magick/convert/ffmpeg)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    scaled_png = os.path.join(ASSETS_DIR, "robot_scaled.png")

    try:
        # Check ImageMagick (magick or convert)
        magick_bin = "magick" if subprocess.run(["which", "magick"], capture_output=True).returncode == 0 else "convert"
        res = subprocess.run(
            [magick_bin, img_path, "-resize", f"{max_w}x{max_h}", scaled_png],
            capture_output=True
        )
        if res.returncode == 0 and os.path.isfile(scaled_png):
            return tk.PhotoImage(file=scaled_png)
    except Exception as e:
        print(f"[ARC-GHOST Image] CLI convert fallback error: {e}")

    # Fallback to direct Tkinter PhotoImage if it's already a PNG
    try:
        if img_path.lower().endswith(".png"):
            raw_img = tk.PhotoImage(file=img_path)
            factor = max(1, raw_img.width() // max_w, raw_img.height() // max_h)
            return raw_img.subsample(factor, factor) if factor > 1 else raw_img
    except Exception as e:
        print(f"[ARC-GHOST Image] Raw PhotoImage error: {e}")

    return None
