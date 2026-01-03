import os
import asyncio
from pathlib import Path
from app.services.audio_gen import generate_audio
from app.models.schemas import VoicePreset

# Directory for voice previews
ASSETS_DIR = Path(__file__).parent / "assets"
VOICES_DIR = ASSETS_DIR / "voices"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# Preview text
TEXT = "Olá, eu sou a voz {voice}. Vamos criar vídeos incríveis juntos."

def generate_voice_previews():
    print("🎙️ Generating voice previews...")
    
    for voice in VoicePreset:
        output_path = VOICES_DIR / f"{voice.value}.mp3"
        print(f"  generating {voice.value}...")
        
        # Customize text slightly for gender/vibe? No, keep standard.
        text = TEXT.format(voice=voice.value.capitalize())
        
        success = generate_audio(
            text=text,
            output_path=str(output_path),
            voice=voice,
            # Use play speed 1.0 for clearer preview
            speed=1.0 
        )
        
        if success:
            print(f"  ✅ {voice.value} ready.")
        else:
            print(f"  ❌ {voice.value} failed.")

if __name__ == "__main__":
    generate_voice_previews()
