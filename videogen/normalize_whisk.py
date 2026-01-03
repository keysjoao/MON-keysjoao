import os
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/joao/core-casts/chatterbox/videogen/assets/characters/AutoLabs_whisk")

def normalize_files():
    if not BASE_DIR.exists():
        print(f"Directory not found: {BASE_DIR}")
        return

    files = sorted([f for f in BASE_DIR.glob("*.png") if f.is_file()])
    print(f"Found {len(files)} files.")

    for idx, file_path in enumerate(files):
        new_name = f"whisk_{idx + 1:03d}.png"
        new_path = BASE_DIR / new_name
        
        # Avoid overwriting if already named correctly (though unlikely with hash names)
        if file_path.name != new_name:
            file_path.rename(new_path)
            print(f"Renamed: {file_path.name} -> {new_name}")

if __name__ == "__main__":
    normalize_files()
