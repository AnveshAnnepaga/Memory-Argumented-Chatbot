"""
Remove background from logo image and save to frontend/public/vyron-logo.png
Usage: python remove_bg.py
"""

import sys
from pathlib import Path

SRC = Path(r"C:\Users\anvesh4\Downloads\logo.png")
DST = Path(__file__).parent / "frontend" / "public" / "vyron-logo.png"

def remove_bg_pil():
    """Remove background using PIL's threshold-based approach (no extra deps)."""
    from PIL import Image
    
    img = Image.open(SRC).convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    for item in datas:
        # If pixel is mostly white/light (background), make transparent
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    DST.parent.mkdir(parents=True, exist_ok=True)
    img.save(DST, "PNG")
    print(f"Saved transparent logo to {DST}")

def remove_bg_rembg():
    """Remove background using rembg (more accurate)."""
    from rembg import remove
    from PIL import Image
    
    input_img = Image.open(SRC)
    output_img = remove(input_img)
    DST.parent.mkdir(parents=True, exist_ok=True)
    output_img.save(DST, "PNG")
    print(f"Saved transparent logo (rembg) to {DST}")


if __name__ == "__main__":
    if not SRC.exists():
        print(f"Source logo not found at {SRC}")
        print("Please update SRC path at the top of this script.")
        sys.exit(1)
    
    try:
        remove_bg_rembg()
    except ImportError:
        print("rembg not installed, falling back to PIL threshold method...")
        try:
            remove_bg_pil()
        except ImportError:
            print("PIL/Pillow not installed. Install with: pip install Pillow rembg")
            sys.exit(1)
