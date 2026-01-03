"""
Image Generator Service - Uses Gemini to generate character images
"""
import os
import base64
from pathlib import Path
from typing import Optional
import google.generativeai as genai

from ..models.schemas import Emotion


# Gemini API Key
GEMINI_API_KEY = "AIzaSyC_a03J5r5V9WBoOvwOxhr5Mld9U6b-Lgs"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Asset paths
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
CHARACTERS_DIR = ASSETS_DIR / "characters"


# Character description for consistency
CHARACTER_DESCRIPTION = """A cute minimalist cartoon character mascot for educational videos.
- Simple flat design with clean vector art style (like Kurzgesagt or Duolingo mascot)
- Wearing a purple hoodie with headphones around neck
- Pastel purple and blue color palette
- White/transparent background
- Full body view, facing slightly to the right
- Friendly and approachable appearance
"""


EMOTION_PROMPTS = {
    Emotion.HAPPY: "happy smiling expression, eyes slightly closed with joy, one hand waving",
    Emotion.THINKING: "thinking expression with hand on chin, looking up thoughtfully, curious pose",
    Emotion.SURPRISED: "surprised amazed expression with wide eyes and open mouth, hands up in excitement",
    Emotion.CODING: "sitting at a laptop computer typing, focused concentrated expression, side view",
    Emotion.CRYING: "sad expression with tears, hands covering face slightly, emotional moment",
    Emotion.EXPLAINING: "confident explaining gesture with one hand raised pointing up, teacher pose",
    Emotion.CONFUSED: "confused expression with tilted head, question mark vibe, scratching head",
}


async def generate_character_image(
    emotion: Emotion,
    save_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Generate a character image for a specific emotion using Gemini.
    
    Args:
        emotion: The emotion/pose to generate
        save_path: Optional custom save path. If None, uses default location.
        
    Returns:
        Path to the saved image, or None if failed
    """
    try:
        # Determine save path
        if save_path is None:
            CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
            save_path = CHARACTERS_DIR / f"{emotion.value}.png"
        
        # Skip if already exists
        if save_path.exists():
            print(f"✓ Image already exists: {save_path}")
            return save_path
        
        # Build the prompt
        emotion_desc = EMOTION_PROMPTS.get(emotion, "neutral standing pose")
        full_prompt = f"{CHARACTER_DESCRIPTION}\n\nPose/Expression: {emotion_desc}"
        
        print(f"🎨 Generating character image for: {emotion.value}")
        
        # Use Gemini with image generation
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        response = model.generate_content(
            f"Generate an image: {full_prompt}",
            generation_config={
                "temperature": 0.7,
            }
        )
        
        # Check if response contains an image
        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Save the image
                    image_data = base64.b64decode(part.inline_data.data)
                    with open(save_path, 'wb') as f:
                        f.write(image_data)
                    print(f"✅ Saved: {save_path}")
                    return save_path
        
        print(f"⚠️ No image in response for {emotion.value}")
        return None
        
    except Exception as e:
        print(f"❌ Error generating image for {emotion.value}: {e}")
        return None


async def ensure_character_images() -> dict[Emotion, Path]:
    """
    Ensure all character images exist, generating missing ones.
    
    Returns:
        Dict mapping emotions to their image paths
    """
    results = {}
    
    for emotion in Emotion:
        image_path = CHARACTERS_DIR / f"{emotion.value}.png"
        
        if image_path.exists():
            results[emotion] = image_path
        else:
            # Try to generate
            path = await generate_character_image(emotion)
            if path:
                results[emotion] = path
    
    return results


def get_character_image(emotion: Emotion) -> Optional[Path]:
    """
    Get the character image for a given emotion (sync version).
    Falls back to happy.png if specific emotion not found.
    """
    # Try exact match first
    image_path = CHARACTERS_DIR / f"{emotion.value}.png"
    if image_path.exists():
        return image_path
    
    # Try fallback
    fallback_path = CHARACTERS_DIR / "happy.png"
    if fallback_path.exists():
        return fallback_path
    
    # No images available
    return None


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing image generation...")
        path = await generate_character_image(Emotion.HAPPY)
        print(f"Result: {path}")
    
    asyncio.run(test())
