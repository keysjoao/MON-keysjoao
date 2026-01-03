import os
import time
import google.generativeai as genai
from pathlib import Path

# Configure API (using same key as script_gen)
GEMINI_API_KEY = "AIzaSyC_a03J5r5V9WBoOvwOxhr5Mld9U6b-Lgs"
genai.configure(api_key=GEMINI_API_KEY)

BASE_DIR = Path("/Users/joao/core-casts/chatterbox/videogen/assets/characters/AutoLabs_whisk")

def tag_assets():
    if not BASE_DIR.exists():
        print(f"Directory not found: {BASE_DIR}")
        return

    model = genai.GenerativeModel('gemini-2.0-flash')
    
    files = sorted([f for f in BASE_DIR.glob("whisk_*.png") if f.is_file()])
    print(f"Found {len(files)} files to tag...")

    existing_names = set()

    for file_path in files:
        # Skip if already tagged (contains more than numbers)
        # Assuming normalized format is whisk_001.png
        # If it has more parts like whisk_001_angry.png, skip? 
        # User normalized them to whisk_001.png recently.
        
        print(f"👀 Analyzing {file_path.name}...")
        
        try:
            # Upload/Process image
            sample_file = genai.upload_file(path=file_path, display_name=file_path.name)
            
            response = model.generate_content([
                "Describe the main action/emotion of this monkey character in exactly 2 to 3 words separated by underscores. Examples: 'holding_bitcoin', 'angry_phone', 'sad_crying', 'driving_car'. Output ONLY the tag.",
                sample_file
            ])
            
            tag = response.text.strip().lower().replace(" ", "_").replace(".", "")
            
            # Keep original number to ensure uniqueness + tag
            # e.g. whisk_001_angry_phone.png
            original_stem = file_path.stem # whisk_001
            new_name = f"{original_stem}_{tag}.png"
            new_path = BASE_DIR / new_name
            
            file_path.rename(new_path)
            print(f"✅ Renamed: {new_name}")
            
            # Rate limit safety
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    tag_assets()
