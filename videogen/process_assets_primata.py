
import os
import shutil
import csv
from pathlib import Path

# Config
SOURCE_DIR = Path("/Users/joao/Downloads/ImageFX_Images")
DEST_DIR = Path("/Users/joao/core-casts/chatterbox/videogen/assets/characters/primata")
CSV_PATH = SOURCE_DIR / "labs_imagefx_20251226_1452.csv"

# Mapping Prompt ID to Emotion Enum Folder Name
# Based on schemas.py Emotion enum and CSV descriptions
PROMPT_MAP = {
    1: "happy",
    2: "sad",
    3: "thinking", 
    4: "angry",
    5: "student", # studying
    6: "old",
    7: "baby",
    8: "rich",
    9: "poor",
    10: "superhero", # superhero
    11: "astronaut",
    12: "chef",
    13: "musician",
    14: "doctor",
    15: "farmer",
    16: "king",
    17: "pirate",
    18: "detective",
    19: "artist",
    20: "athlete",
    21: "student", # graduating - mapping to student as well, or maybe happy? Let's use student.
    22: "business",
    23: "construction",
    24: "scientist",
    25: "magician",
    26: "superhero", # knight -> mapping to superhero as fallback or maybe "king"? Let's go with superhero for now as it's a "hero"
    27: "traveler",
    28: "scientist", # coder -> mapping to scientist (schema alias)
    29: "yoga",
    30: "firefighter"
}

def main():
    if not CSV_PATH.exists():
        print(f"CSV not found at {CSV_PATH}")
        return

    # Create dest dir
    if DEST_DIR.exists():
        shutil.rmtree(DEST_DIR)
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading CSV from {CSV_PATH}...")
    
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                prompt_idx = int(row['Prompt Index'])
                image_name = row['Image Name']
                
                if prompt_idx not in PROMPT_MAP:
                    print(f"Skipping Unknown Prompt Index: {prompt_idx}")
                    continue
                    
                emotion_folder = PROMPT_MAP[prompt_idx]
                
                # Source file
                src_file = SOURCE_DIR / image_name
                
                # Some files in CSV might have .png extension but on disk are .jpeg or vice versa?
                # The file list showed .jpeg, but CSV shows .png sometimes or .jpeg?
                # Let's check the file list again. The list_dir showed .jpeg for all.
                # The CSV excerpt showed .png.
                # So we need to handle extension mismatch.
                
                if not src_file.exists():
                    # Try swapping extension
                    if src_file.suffix == '.png':
                        src_file = src_file.with_suffix('.jpeg')
                    elif src_file.suffix == '.jpeg':
                        src_file = src_file.with_suffix('.png')
                        
                if not src_file.exists():
                    print(f"File not found: {image_name} (checked {src_file})")
                    continue
                    
                # Dest folder
                target_folder = DEST_DIR / emotion_folder
                target_folder.mkdir(exist_ok=True)
                
                # Copy
                shutil.copy2(src_file, target_folder / src_file.name)
                print(f"Copied {src_file.name} -> {emotion_folder}/")
                
            except ValueError:
                continue
                
    print("Migration complete!")

if __name__ == "__main__":
    main()
