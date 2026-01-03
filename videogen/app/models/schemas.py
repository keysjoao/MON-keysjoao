"""
Pydantic schemas for VideoGen API
Extended with voice presets, video duration, and edit styles
"""
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class Emotion(str, Enum):
    """Available character emotions/categories"""
    ANGRY = "angry"
    ARTIST = "artist"
    ASTRONAUT = "astronaut"
    ATHLETE = "athlete"
    BABY = "baby"
    BUSINESS = "business"
    CHEF = "chef"
    CONSTRUCTION = "construction"
    DETECTIVE = "detective"
    DOCTOR = "doctor"
    FARMER = "farmer"
    FIREFIGHTER = "firefighter"
    HAPPY = "happy"
    KING = "king"
    MAGICIAN = "magician"
    MUSICIAN = "musician"
    OLD = "old"
    PIRATE = "pirate"
    POOR = "poor"
    RICH = "rich"
    SAD = "sad"
    SCIENTIST = "scientist"
    STUDENT = "student"
    SUPERHERO = "superhero"
    THINKING = "thinking"
    TRAVELER = "traveler"
    YOGA = "yoga"
    
    # Fallbacks/Aliases (mapped to closest visual)
    CONFUSED = "thinking" 
    EXPLAINING = "business"
    CODING = "scientist" # or create coding folder if not exists, but for now map to existing
    SURPRISED = "happy"


class VideoFormat(str, Enum):
    """Video output formats"""
    VERTICAL = "vertical"    # 1080x1920 (TikTok, Reels, Shorts)
    HORIZONTAL = "horizontal"  # 1920x1080 (YouTube)


class Language(str, Enum):
    """Supported languages"""
    PT = "pt"
    EN = "en"
    ES = "es"


class ScriptStyle(str, Enum):
    """Script writing styles"""
    EDUCATIONAL = "educational"
    POLEMIC = "polemic"
    NEWS = "news"
    STORYTELLING = "storytelling"
    HUMOR = "humor"
    PRIMATA = "primata"
    AUTOLABS = "autolabs"


class SceneLayout(str, Enum):
    """Visual layout for a scene"""
    TITLE = "title"
    TEXT_ONLY = "text_only"
    IMAGE_ONLY = "image_only"
    IMAGE_TEXT = "image_text"
    MULTI_IMAGE = "multi_image"


class VideoDuration(str, Enum):
    """Video duration presets"""
    SHORT = "short"      # 15-30s (3-5 cenas)
    MEDIUM = "medium"    # 30-60s (5-8 cenas)
    LONG = "long"        # 60-90s (8-12 cenas)
    EXTRA_LONG = "extra_long" # 5 min (30+ cenas)


class EditStyle(str, Enum):
    """Video editing styles"""
    TIKTOK = "tiktok"    # Cortes rápidos (2-3s por cena)
    CALM = "calm"        # Cortes mais lentos (5-8s por cena)
    DYNAMIC = "dynamic"  # Variado por emoção


class VoicePreset(str, Enum):
    """OpenAI TTS voice presets"""
    ALLOY = "alloy"
    ASH = "ash"
    BALLAD = "ballad"
    CORAL = "coral"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SAGE = "sage"
    SHIMMER = "shimmer"
    VERSE = "verse"
    MARIN = "marin"
    CEDAR = "cedar"
    ELEVENLABS = "elevenlabs"


# Voice instruction presets (like openai.fm)
VOICE_INSTRUCTIONS = {
    "brazilian_energetic": "Voice: Authentically Brazilian, younger energetic male/female. Tone: High energy (HYPE), fast-paced, wildly enthusiastic like a YouTuber/Tiktoker. Style: Extremely natural, using Brazilian colloquialisms (e.g. 'tá', 'né', 'galera'), dynamic intonation shifts, and avoiding robotic monotony. Emphasize excitement!",
    "brazilian_calm": "Voice: Warm, wise advice-giver (Brazilian). Tone: Calm, reassuring, intimate but engaging. Style: Podcast-style conversational flow, natural breath pauses, clear but not formal. Like a friend giving deep advice.",
    "narrator": "Voice: Professional narrator. Tone: Serious, authoritative, documentary-style. Style: Clear enunciation, measured pace.",
    "friendly": "Voice: Friendly and approachable. Tone: Conversational, like talking to a friend. Style: Natural pauses, casual expressions.",
    "dramatic": "Voice: Dramatic storyteller. Tone: Building tension, varied pace. Style: Emotional highs and lows, pauses for effect.",
}


class Scene(BaseModel):
    """A single scene in the script"""
    id: int
    texto: str
    emocao: Emotion
    duracao_estimada: float
    texto_destaque: Optional[str] = None
    texto_tela: Optional[str] = None
    layout: Optional[SceneLayout] = None
    assets: Optional[List[str]] = None


class Script(BaseModel):
    """Complete video script"""
    titulo: str
    idioma: Language
    cenas: List[Scene]


class GenerateRequest(BaseModel):
    """Request to generate a video"""
    tema: str
    idioma: Language = Language.PT
    formato: VideoFormat = VideoFormat.VERTICAL
    estilo: ScriptStyle = ScriptStyle.EDUCATIONAL
    duracao: VideoDuration = VideoDuration.MEDIUM
    edicao: EditStyle = EditStyle.DYNAMIC
    voz: VoicePreset = VoicePreset.ALLOY
    voz_instrucao: str = "brazilian_energetic"
    velocidade: float = 1.1


class GenerateFromScriptRequest(BaseModel):
    """Request to generate video from an edited script"""
    script: Script
    idioma: Language = Language.PT
    formato: VideoFormat = VideoFormat.VERTICAL
    voz: VoicePreset = VoicePreset.ALLOY
    voz_instrucao: str = "brazilian_energetic"
    velocidade: float = 1.1


class GenerateResponse(BaseModel):
    """Response with generated video info"""
    success: bool
    video_path: Optional[str] = None
    script: Optional[Script] = None
    audio_path: Optional[str] = None
    error: Optional[str] = None
