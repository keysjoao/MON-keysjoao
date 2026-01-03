"""
Audio Generator Service - Uses OpenAI TTS API
FAST: ~5-10 seconds for any text length!
Supports multiple voices and instruction presets
"""
import os
import httpx
from pathlib import Path
from typing import Optional, List, Tuple


from ..models.schemas import Script, Language, VoicePreset, VOICE_INSTRUCTIONS


# API Keys from environment variables - NEVER hardcode secrets!
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "tS45q0QcrDHqHoaWdCDR")

# TTS Configuration
TTS_MODEL = "gpt-4o-mini-tts" # Supports all 13 voices including verse, marin, cedar
TTS_FORMAT = "mp3"


def generate_audio(
    text: str,
    output_path: str,
    voice: VoicePreset = VoicePreset.ALLOY,
    voice_instruction: str = "brazilian_energetic", # Ignored by tts-1, keeping argument for compatibility
    language: Language = Language.PT,
    speed: float = 1.5,
) -> bool:
    """
    Generate audio from text using OpenAI TTS API (tts-1 model)
    """
    try:
        from ..utils.logger import logger
        
        # Clean up text for TTS
        cleaned_text = text.replace("###", "").replace("\\n", "\n")
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        if voice == VoicePreset.ELEVENLABS:
             return generate_audio_elevenlabs(cleaned_text, output_path, ELEVENLABS_VOICE_ID)

        # tts-1 endpoint only accepts: model, input, voice, response_format, speed
        safe_speed = max(0.5, min(speed, 2.0))
        payload = {
            "model": TTS_MODEL,
        # ... continuation of openai payload
            "voice": voice.value, # alloy, echo, fable, onyx, nova, shimmer
            "input": cleaned_text,
            "response_format": TTS_FORMAT,
            "speed": safe_speed
        }
        
        logger.info(f"🎤 Generating TTS ({len(cleaned_text)} chars) using {voice.value}...")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload
            )
        
        if response.status_code != 200:
            logger.error(f"❌ API Error: {response.status_code} - {response.text[:200]}")
            return False
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        logger.info(f"✅ Audio saved: {output_path}")
        return True
        
    except Exception as e:
        # Fallback to print if logger fails import loop context (though unlikely inside func)
        print(f"❌ Error: {e}") 
        return False

    except Exception as e:
        # Fallback to print if logger fails import loop context (though unlikely inside func)
        print(f"❌ Error: {e}") 
        return False


def generate_audio_elevenlabs(
    text: str,
    output_path: str,
    voice_id: str,
) -> bool:
    """Generate audio using ElevenLabs API"""
    try:
        from ..utils.logger import logger
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        logger.info(f"🔊 Generating ElevenLabs Audio ({len(text)} chars)...")
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            
        if response.status_code != 200:
            logger.error(f"❌ ElevenLabs Error: {response.status_code} - {response.text[:200]}")
            return False
            
        with open(output_path, "wb") as f:
            f.write(response.content)
            
        logger.info(f"✅ ElevenLabs Audio saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ ElevenLabs Exception: {e}")
        return False
def generate_script_audio(
    script: Script,
    output_dir: str,
    voice: VoicePreset = VoicePreset.ALLOY,
    voice_instruction: str = "brazilian_energetic",
    speed: float = 1.5
) -> Optional[str]:
    """
    Generate audio for an entire script using OpenAI TTS
    
    FAST: Single API request for all text = ~5-10 seconds total!
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Combine all scene texts into one
        full_text = " ".join([scene.texto for scene in script.cenas])
        
        print(f"🎙️ Generating audio ({len(full_text)} chars)...")
        
        main_audio_path = output_path / "audio.mp3"
        
        success = generate_audio(
            text=full_text,
            output_path=str(main_audio_path),
            voice=voice,
            voice_instruction=voice_instruction,
            language=script.idioma,
            speed=speed
        )
        
        if success:
            print(f"  🎉 Audio complete!")
            return str(main_audio_path)
        else:
            return None
            
    except Exception as e:
        print(f"Error generating script audio: {e}")
        return None


def generate_script_audio_segments(
    script: Script,
    output_dir: str,
    voice: VoicePreset = VoicePreset.ALLOY,
    voice_instruction: str = "brazilian_energetic",
    speed: float = 1.5
) -> Optional[Tuple[str, List[str]]]:
    """
    Generate audio per scene for better sync and return the concatenated audio.
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        scene_audio_paths: List[str] = []
        for idx, scene in enumerate(script.cenas):
            scene_audio_path = output_path / f"scene_{idx + 1:02d}.mp3"
            success = generate_audio(
                text=scene.texto,
                output_path=str(scene_audio_path),
                voice=voice,
                voice_instruction=voice_instruction,
                language=script.idioma,
                speed=speed
            )
            if not success:
                return None
            scene_audio_paths.append(str(scene_audio_path))

        concat_path = output_path / "audio.mp3"
        success = concat_audio_files(scene_audio_paths, str(concat_path))
        if not success:
            return None

        return str(concat_path), scene_audio_paths
    except Exception as e:
        print(f"Error generating segmented audio: {e}")
        return None


def concat_audio_files(audio_paths: List[str], output_path: str) -> bool:
    """Concatenate audio files using ffmpeg."""
    try:
        from ..utils.logger import logger
        concat_list = Path(output_path).with_suffix(".txt")
        with open(concat_list, "w", encoding="utf-8") as f:
            for path in audio_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:a", "libmp3lame",
            "-q:a", "2",
            output_path
        ]
        import subprocess
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"FFmpeg concat error: {process.stderr[:200]}")
            return False
        return True
    except Exception as e:
        print(f"Error concatenating audio: {e}")
        return False


# Compatibility
def get_model():
    """No-op for OpenAI TTS"""
    return None


def generate_subtitles_srt(audio_path: str, output_srt_path: str) -> bool:
    """
    Generate SRT subtitles using OpenAI Whisper API
    """
    try:
        from ..utils.logger import logger
        
        logger.info(f"📜 Generating subtitles (Whisper) for {audio_path}...")
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "whisper-1",
            "response_format": "srt",
            "language": "pt"
        }
        
        # httpx multipart upload
        with open(audio_path, "rb") as f:
            files = {"file": ("audio.mp3", f, "audio/mpeg")}
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, data=data, files=files)
                
        if response.status_code != 200:
            logger.error(f"❌ Whisper API Error: {response.status_code} - {response.text[:200]}")
            return False
            
        srt_content = response.text
        
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
            
        logger.info(f"✅ Subtitles saved: {output_srt_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating subtitles: {e}")
        return False
