import pandas as pd
from pathlib import Path

CSV_PATH = Path("/Users/joao/Downloads/ImageFX_Images/labs_imagefx_20251226_1452.csv")

def extract_category(prompt):
    prompt_lower = prompt.lower()
    keywords = {
        "firefighter": "firefighter",
        "chef": "chef",
        "doctor": "doctor",
        "police": "police",
        "detective": "detective",
        "astronaut": "astronaut",
        "superhero": "superhero",
        "king": "king",
        "queen": "queen",
        "pirate": "pirate",
        "artist": "artist",
        "musician": "musician",
        "farmer": "farmer",
        "construction": "construction",
        "scientist": "scientist",
        "coder": "coder",
        "student": "student",
        "graduate": "student",
        "business": "business",
        "rich": "rich",
        "poor": "poor",
        "baby": "baby",
        "old": "old",
        "cheerful": "happy",
        "happy": "happy",
        "joyful": "happy",
        "sad": "sad",
        "angry": "angry",
        "thoughtful": "thinking",
        "thinking": "thinking",
        "surprised": "surprised",
        "confused": "confused"
    }
    
    for key, category in keywords.items():
        if key in prompt_lower:
            return category
            
    return "other"

try:
    df = pd.read_csv(CSV_PATH)
    print("Prompts classificados como OTHER:\n")
    for prompt in df['Prompt']:
        if extract_category(prompt) == "other":
            print(f"- {prompt[:100]}...") # Print first 100 chars
except Exception as e:
    print(e)
