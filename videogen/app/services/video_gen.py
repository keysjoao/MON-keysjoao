
"""
Video Generator Service - Uses FFmpeg to compose final video
OPTIMIZED: Randomized assets, single FFmpeg command, ultrafast encoding
"""
import subprocess
import json
import random
import shlex
import concurrent.futures
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import asdict
from ..utils.logger import logger
from ..models.schemas import Script, Scene, VideoFormat, Emotion, ScriptStyle, SceneLayout

# Asset paths
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
CHARACTERS_DIR = ASSETS_DIR / "characters"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
MUSIC_DIR = ASSETS_DIR / "music"
TEMP_DIR = Path(__file__).parent.parent.parent / "temp"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

DEFAULT_BG_COLOR = "white"
DEFAULT_FPS = 24
ZOOM_RATE = 0.002
ZOOM_MAX = 1.08
MUSIC_VOLUME = 0.03
DEFAULT_FONT = "/System/Library/Fonts/Helvetica.ttc"
HANDWRITTEN_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Bradley Hand.ttc",
    "/System/Library/Fonts/Supplemental/Marker Felt.ttc",
    "/System/Library/Fonts/Noteworthy.ttc",
    "/Library/Fonts/Comic Sans MS.ttf",
]

def get_video_dimensions(format: VideoFormat) -> tuple[int, int]:
    """Get video dimensions based on format"""
    # Full HD resolution
    if format == VideoFormat.VERTICAL:
        return (1080, 1920) 
    return (1920, 1080)


def pick_handwritten_font() -> str:
    """Pick a handwritten font if available, fallback to default."""
    for font_path in HANDWRITTEN_FONT_CANDIDATES:
        if Path(font_path).exists():
            return font_path
    return DEFAULT_FONT


def get_characters_dir(style: Optional[ScriptStyle]) -> Path:
    """Resolve character asset pack based on style."""
    if style == ScriptStyle.PRIMATA:
        primata_dir = CHARACTERS_DIR / "primata"
        if primata_dir.exists():
            return primata_dir
    if style == ScriptStyle.AUTOLABS:
        return CHARACTERS_DIR / "AutoLabs_flow"
    return CHARACTERS_DIR


def get_random_asset(folder: Path, extensions: List[str] = [".png", ".jpg", ".jpeg", ".mp4"]) -> Optional[Path]:
    """Get a random asset from a folder"""
    if not folder.exists():
        return None
    
    files = []
    for ext in extensions:
        files.extend(folder.glob(f"*{ext}"))
    
    if not files:
        return None
    
    return random.choice(files)


def get_character_image(emotion: Emotion, base_dir: Optional[Path] = None) -> Optional[Path]:
    """Get a random character PNG for a given emotion"""
    if base_dir is None:
        base_dir = CHARACTERS_DIR
    # Try exact emotion folder first
    emotion_folder = base_dir / emotion.value
    image = get_random_asset(emotion_folder)
    
    if image:
        return image
    
    # Fallback to happy folder
    happy_folder = base_dir / "happy"
    image = get_random_asset(happy_folder)
    
    if image:
        return image
    
    # Final fallback: any image in characters directory
    for subfolder in base_dir.iterdir():
        if subfolder.is_dir():
            image = get_random_asset(subfolder)
            if image:
                return image
    
    return None


def get_random_background(format: VideoFormat) -> Optional[Path]:
    """Get a random background (video or image)"""
    if not BACKGROUNDS_DIR.exists():
        return None
    
    # Try videos first
    videos = list(BACKGROUNDS_DIR.glob("*.mp4"))
    if videos:
        return random.choice(videos)
        
    # Formatting images if no video
    images = list(BACKGROUNDS_DIR.glob("*.jpg")) + list(BACKGROUNDS_DIR.glob("*.png")) + list(BACKGROUNDS_DIR.glob("*.jpeg"))
    if images:
        return random.choice(images)
    
    return None


def get_random_music() -> Optional[Path]:
    """Get a random background music file"""
    if not MUSIC_DIR.exists():
        return None
    
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.m4a")) + list(MUSIC_DIR.glob("*.wav"))
    
    if not music_files:
        return None
    
    return random.choice(music_files)


def get_default_music() -> Optional[Path]:
    """Get a deterministic default music track."""
    if not MUSIC_DIR.exists():
        return None
    music_files = sorted(list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.m4a")) + list(MUSIC_DIR.glob("*.wav")))
    if not music_files:
        return None
    return music_files[0]


def get_audio_duration(audio_path: str) -> float:
    """Get duration of an audio file using ffprobe"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json",
                audio_path
            ],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        return 30.0


def split_text_smart(text: str, max_chunks: int = 2) -> List[str]:
    """Split text into at most N chunks to avoid frequent sync issues"""
    words = text.split()
    if len(words) <= 4:
        return [text]
    
    # Split effectively in half
    mid = len(words) // 2
    return [" ".join(words[:mid]), " ".join(words[mid:])]


def get_smart_asset(scene: Scene, base_dir: Path) -> Optional[Path]:
    """
    Selects an asset based on context keywords in the text/highlight,
    falling back to emotion if no context is found.
    """
    # 1. Text Analysis
    text = (scene.texto + " " + (scene.texto_destaque or "")).lower()
    
    keyword_map = {
        # Professions & Roles
        "bombeiro": "firefighter", "fogo": "firefighter", "incêndio": "firefighter", "chamas": "firefighter",
        "médico": "doctor", "hospital": "doctor", "saúde": "doctor", "paciente": "doctor", "cura": "doctor",
        "polícia": "detective", "crime": "detective", "preso": "detective", "lei": "detective", 
        "detetive": "detective", "mistério": "detective", "investigar": "detective", "lupa": "detective",
        "astronauta": "astronaut", "espaço": "astronaut", "lua": "astronaut", "universo": "astronaut", "foguete": "astronaut",
        "chef": "chef", "cozinha": "chef", "comida": "chef", "restaurante": "chef", "receita": "chef",
        "super-herói": "superhero", "poder": "superhero", "herói": "superhero", "salvar": "superhero", "capa": "superhero",
        "rei": "king", "rainha": "king", "trono": "king", "coroa": "king", "reino": "king", "líder": "king",
        "pirata": "pirate", "mar": "pirate", "tesouro": "pirate", "navio": "pirate", "navegar": "pirate",
        "artista": "artist", "pintar": "artist", "desenhar": "artist", "arte": "artist", "quadro": "artist",
        "músico": "musician", "violão": "musician", "som": "musician", "música": "musician", "tocar": "musician", "show": "musician",
        "fazendeiro": "farmer", "campo": "farmer", "plantar": "farmer", "trator": "farmer", "colher": "farmer", "roça": "farmer",
        "construção": "construction", "obra": "construction", "construir": "construction", "tijolo": "construction", "projeto": "construction",
        "cientista": "scientist", "laboratório": "scientist", "ciência": "scientist", "fórmula": "scientist", "química": "scientist",
        "estudante": "student", "escola": "student", "aula": "student", "aprender": "student", "livro": "student", "estudo": "student",
        "mágico": "magician", "magia": "magician", "truque": "magician", "cartola": "magician",
        "atleta": "athlete", "esporte": "athlete", "correr": "athlete", "treino": "athlete", "futebol": "athlete", "academia": "athlete",

        # Emotions & States
        "bravo": "angry", "raiva": "angry", "furioso": "angry", "gritar": "angry", "ódio": "angry",
        "triste": "sad", "chorar": "sad", "lágrima": "sad", "depressão": "sad", "sozinho": "sad",
        "feliz": "happy", "alegria": "happy", "sorrir": "happy", "comemorar": "happy", "sucesso": "happy",
        "pensando": "thinking", "dúvida": "thinking", "ideia": "thinking", "confuso": "thinking", "decisão": "thinking", "?": "thinking",
        "velho": "old", "idoso": "old", "avô": "old", "tempo": "old", "passado": "old", "experiência": "old",
        "bebê": "baby", "criança": "baby", "filho": "baby", "nascer": "baby", "início": "baby",
        
        # Financial / Lifestyle
        "negócios": "business", "empresa": "business", "chefe": "business", "escritório": "business", "reunião": "business",
        "rico": "rich", "dinheiro": "rich", "luxo": "rich", "ouro": "rich", "milionário": "rich", "ganhar": "rich",
        "pobre": "poor", "falta": "poor", "dívida": "poor", "sem nada": "poor", "perder": "poor",
        
        # Activities
        "viagem": "traveler", "viajar": "traveler", "mundo": "traveler", "mala": "traveler", "ferias": "traveler", "avião": "traveler",
        "yoga": "yoga", "meditar": "yoga", "paz": "yoga", "zen": "yoga", "respira": "yoga", "calma": "yoga",
        "código": "scientist", "computador": "business", "programador": "business"
    }

    for key, folder_name in keyword_map.items():
        if key in text:
            target_folder = base_dir / folder_name
            if target_folder.exists():
                return get_random_asset(target_folder)

    return get_character_image(scene.emocao, base_dir) 


def list_available_categories(base_dir: Path) -> List[str]:
    """Helper to list what we have for debugging"""
    if not base_dir.exists():
        return []
    return [d.name for d in base_dir.iterdir() if d.is_dir()]


def select_scene_assets(script: Script, style: Optional[ScriptStyle] = None) -> List[Path]:
    """
    Selects assets for each scene using smart context logic.
    Returns a list of Path objects corresponding to each scene.
    """
    scene_assets = []
    print("  🎥 Selecting assets for scenes (Smart Context)...")
    base_dir = get_characters_dir(style)
    cats = list_available_categories(base_dir)
    print(f"  📂 Available Categories: {len(cats)} folders (e.g. {cats[:5]})")
    
    for scene in script.cenas:
        img = get_smart_asset(scene, base_dir)
        if not img:
            img = get_character_image(Emotion.HAPPY, base_dir)
        scene_assets.append(img)
    
    return scene_assets


def resolve_asset_token(token: str, base_dir: Path) -> Optional[Path]:
    """Resolve an asset token to a file path."""
    if not token:
        return None
    token = token.strip().lower()
    if token.startswith("icon:"):
        icon_dir = ASSETS_DIR / "icons" / token.replace("icon:", "")
        return get_random_asset(icon_dir)
    if token.startswith("vector:"):
        vector_dir = ASSETS_DIR / "vectors" / token.replace("vector:", "")
        return get_random_asset(vector_dir)
    
    # Check if token is a logo
    if token.startswith("logo:") or token.startswith("logo_"):
        logo_name = token.replace("logo:", "").replace("logo_", "")
        logo_dir = ASSETS_DIR / "tech_logos"
        # Check for specific logo file
        for ext in [".png", ".jpg", ".jpeg"]:
            logo_path = logo_dir / f"{logo_name}{ext}"
            if logo_path.exists():
                return logo_path
        # Return none or fallback? None is fine, default logic handles it.

    # Check if token matches a file directly in base_dir (flat structure like AutoLabs_flow)
    # FUZZY MATCH: Check if any file in base_dir CONTAINS the token and has a valid extension
    # This allows 'holding_bitcoin' to match 'whisk_050_holding_bitcoin.png'
    valid_exts = [".mp4", ".png", ".jpg", ".jpeg"]
    if base_dir.exists():
        for f in base_dir.iterdir():
            if f.suffix.lower() in valid_exts and token in f.name.lower():
                return f
    
    # Check if token is a subfolder (traditional structure like primata/happy)
    category_dir = base_dir / token
    if category_dir.exists() and category_dir.is_dir():
        return get_random_asset(category_dir)
    return None


def resolve_scene_assets(scene: Scene, base_dir: Path) -> List[Path]:
    """Resolve assets for a scene using explicit tokens or smart fallback."""
    assets: List[Path] = []
    if scene.assets:
        for token in scene.assets:
            asset = resolve_asset_token(str(token).lower(), base_dir)
            if asset:
                assets.append(asset)
    if assets:
        return assets[:3]

    asset = get_smart_asset(scene, base_dir)
    if asset:
        assets.append(asset)
    return assets[:3]


def infer_layout(scene: Scene, index: int) -> SceneLayout:
    """Determine scene layout if not explicitly defined."""
    if scene.layout:
        return scene.layout
    if index == 0:
        return SceneLayout.TITLE
    if scene.assets and len(scene.assets) > 1:
        return SceneLayout.MULTI_IMAGE
    if scene.texto_tela:
        return SceneLayout.IMAGE_TEXT if scene.assets else SceneLayout.TEXT_ONLY
    return SceneLayout.IMAGE_ONLY


def truncate_text(text: str, max_words: int = 8) -> str:
    """Shorten text for on-screen display."""
    words = text.split()
    return " ".join(words[:max_words])


def get_scene_text(scene: Scene, script_title: str, layout: SceneLayout) -> Optional[str]:
    """Pick the on-screen text for the scene."""
    if scene.texto_tela:
        return scene.texto_tela
    if layout in (SceneLayout.TITLE, SceneLayout.TEXT_ONLY):
        return scene.texto_destaque or script_title
    if layout in (SceneLayout.IMAGE_ONLY, SceneLayout.MULTI_IMAGE) and not scene.texto_destaque:
        return None
    if scene.texto_destaque:
        return scene.texto_destaque
    return truncate_text(scene.texto, max_words=6)


def wrap_text(text: str, max_chars: int) -> str:
    """Wrap text into multiple lines."""
    words = text.split()
    lines = []
    current_line: List[str] = []
    for word in words:
        if len(" ".join(current_line + [word])) <= max_chars:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)


def compute_boxes(
    count: int,
    layout: SceneLayout,
    width: int,
    height: int,
    format: VideoFormat
) -> List[dict]:
    """Compute boxes (x, y, w, h) for assets in a scene."""
    boxes: List[dict] = []
    if count <= 0:
        return boxes

    if layout in (SceneLayout.IMAGE_ONLY, SceneLayout.IMAGE_TEXT, SceneLayout.TITLE, SceneLayout.TEXT_ONLY):
        box_w = int(width * (0.7 if format == VideoFormat.VERTICAL else 0.5))
        box_h = int(height * (0.55 if format == VideoFormat.VERTICAL else 0.7))
        x = int((width - box_w) / 2)
        y = int(height * (0.3 if layout == SceneLayout.IMAGE_TEXT and format == VideoFormat.VERTICAL else 0.2))
        if format == VideoFormat.HORIZONTAL and layout == SceneLayout.IMAGE_TEXT:
            x = int(width * 0.08)
            y = int((height - box_h) / 2)
        boxes.append({"x": x, "y": y, "w": box_w, "h": box_h})
        return boxes

    if layout == SceneLayout.MULTI_IMAGE:
        if count == 2:
            box_w = int(width * (0.38 if format == VideoFormat.VERTICAL else 0.3))
            box_h = int(height * (0.38 if format == VideoFormat.VERTICAL else 0.5))
            y = int(height * 0.35)
            left_x = int(width * 0.08)
            right_x = int(width - box_w - width * 0.08)
            boxes.extend([
                {"x": left_x, "y": y, "w": box_w, "h": box_h},
                {"x": right_x, "y": y, "w": box_w, "h": box_h},
            ])
            return boxes

        box_w = int(width * (0.32 if format == VideoFormat.VERTICAL else 0.26))
        box_h = int(height * (0.32 if format == VideoFormat.VERTICAL else 0.5))
        top_y = int(height * 0.22)
        bottom_y = int(height * 0.55)
        left_x = int(width * 0.06)
        right_x = int(width - box_w - width * 0.06)
        center_x = int((width - box_w) / 2)
        boxes.extend([
            {"x": left_x, "y": top_y, "w": box_w, "h": box_h},
            {"x": right_x, "y": top_y, "w": box_w, "h": box_h},
            {"x": center_x, "y": bottom_y, "w": box_w, "h": box_h},
        ])
        return boxes

    return boxes


def build_zoompan(box_w: int, box_h: int, frames: int, fps: int) -> str:
    """Build a zoompan filter for a still asset."""
    return (
        f"zoompan=z='min(zoom+{ZOOM_RATE},{ZOOM_MAX})':"
        f"d={frames}:s={box_w}x{box_h}:fps={fps}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    )


def render_scene_clip(
    scene: Scene,
    scene_index: int,
    script_title: str,
    audio_path: str,
    output_path: str,
    width: int,
    height: int,
    format: VideoFormat,
    base_dir: Path,
    fps: int = DEFAULT_FPS
) -> bool:
    """Render a single scene clip with white background and zoom in."""
    try:
        duration = get_audio_duration(audio_path)
        layout = infer_layout(scene, scene_index)
        assets = resolve_scene_assets(scene, base_dir)
        if layout in (SceneLayout.TITLE, SceneLayout.TEXT_ONLY) and not scene.assets:
            assets = []
        if layout != SceneLayout.MULTI_IMAGE:
            assets = assets[:1]
        if layout == SceneLayout.MULTI_IMAGE and len(assets) < 2:
            layout = SceneLayout.IMAGE_ONLY
        if layout == SceneLayout.IMAGE_TEXT and not assets:
            layout = SceneLayout.TEXT_ONLY
        text = get_scene_text(scene, script_title, layout)

        input_args = [
            "-f", "lavfi",
            "-i", f"color=c={DEFAULT_BG_COLOR}:s={width}x{height}:d={duration}:r={fps}",
            "-i", audio_path,
        ]

        for asset in assets:
            is_video = str(asset).lower().endswith('.mp4')
            if is_video:
                # Stream loop for videos (not -loop which is for images)
                input_args.extend(["-stream_loop", "-1", "-i", str(asset)])
            else:
                input_args.extend(["-loop", "1", "-i", str(asset)])

        filter_chains: List[str] = []
        filter_chains.append("[0:v]format=rgba[base]")
        current = "[base]"

        boxes = compute_boxes(len(assets), layout, width, height, format)
        for idx, asset in enumerate(assets):
            box = boxes[idx] if idx < len(boxes) else {"x": 0, "y": 0, "w": width, "h": height}
            frames = max(1, int(duration * fps))
            input_idx = 2 + idx
            is_video = str(asset).lower().endswith('.mp4')
            
            if is_video:
                # OVERRIDE: Video assets are 70% of screen size, CENTERED
                # Layout: Text at top (10%), Video in center/bottom area
                s_factor = 0.7
                v_w = int(width * s_factor)
                v_h = int(height * s_factor)
                v_x = int((width - v_w) / 2)
                v_y = height - v_h # Bottom aligned to hide artifacts
                
                box = {"x": v_x, "y": v_y, "w": v_w, "h": v_h}
                
                # Scale to COVER the 70% box + Crop
                # Added safety crop (iw-20:ih-20) to remove potential black edge artifacts
                filter_chains.append(
                    f"[{input_idx}:v]crop=iw-20:ih-20,"
                    f"scale={v_w}:{v_h}:force_original_aspect_ratio=increase,"
                    f"crop={v_w}:{v_h},"
                    f"trim=duration={duration},setpts=PTS-STARTPTS[asset_{idx}]"
                )
            else:
                # For image assets: use zoompan Ken Burns effect
                zoompan = build_zoompan(box["w"], box["h"], frames, fps)
                filter_chains.append(
                    f"[{input_idx}:v]scale={box['w']}:{box['h']}:force_original_aspect_ratio=decrease,"
                    f"pad={box['w']}:{box['h']}:(ow-iw)/2:(oh-ih)/2:color=white@0,format=rgba,"
                    f"{zoompan}[asset_{idx}]"
                )
            filter_chains.append(
                f"{current}[asset_{idx}]overlay={box['x']}:{box['y']}[tmp_{idx}]"
            )

            current = f"[tmp_{idx}]"

        # Audio Mixing Logic
        audio_inputs = ["[1:a]volume=1.0[tts]"] # Start with TTS (Input 1)
        audio_mix_labels = ["[tts]"]
        
        for idx, asset in enumerate(assets):
            is_video = str(asset).lower().endswith('.mp4')
            if is_video:
                input_idx = 2 + idx
                # Trim audio to match scene duration
                filter_chains.append(
                    f"[{input_idx}:a]atrim=duration={duration},asetpts=PTS-STARTPTS,volume=0.3[aud_{idx}]"
                )
                audio_mix_labels.append(f"[aud_{idx}]")
        
        final_audio_map = "1:a"
        if len(audio_mix_labels) > 1:
            # Mix interactions: TTS + Video Audios

            # Prepend audio_inputs declaration to filter_complex (need filter_complex to receive list of strings)
            # Actually, we can just append mix_cmd to filter_chains, but [1:a]volume=... needs to be valid.
            # So let's refine:
            filter_chains.append(f"[1:a]volume=1.0[tts]") # Rename input 1 to [tts] with gain
            mix_cmd = "".join(audio_mix_labels) + f"amix=inputs={len(audio_mix_labels)}:duration=first:dropout_transition=2[aout]"
            filter_chains.append(mix_cmd)
            final_audio_map = "[aout]"
        text_only_zoom = bool(text) and not assets and layout in (SceneLayout.TITLE, SceneLayout.TEXT_ONLY)

        if text and not text_only_zoom:
            max_chars = 18 if format == VideoFormat.VERTICAL else 26
            if layout in (SceneLayout.TITLE, SceneLayout.TEXT_ONLY):
                max_chars = 16 if format == VideoFormat.VERTICAL else 24
            wrapped_text = wrap_text(text, max_chars=max_chars)

            temp_text_path = TEMP_DIR / f"scene_{scene_index:02d}_text.txt"
            temp_text_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_text_path, "w", encoding="utf-8") as f:
                f.write(wrapped_text)
            txt_path_str = str(temp_text_path).replace("\\", "/").replace(":", "\\:")

            font_path = pick_handwritten_font()  # Always use handwritten font (user preference)
            font_path = font_path.replace("\\", "/").replace(":", "\\:")
            
            # Text Positioning Logic (Simplified)
            # If has media (video/image): Text at TOP
            # If text only: Text in CENTER
            
            font_size = int(width * 0.08) # Standard font size
            text_x = "(w-text_w)/2" # Always centered X
            
            if assets:
                # Has media -> Text at Top (10% down)
                text_y = int(height * 0.10)
            else:
                # No media -> Text Centered vertically
                text_y = "(h-text_h)/2"

            filter_chains.append(
                f"{current}drawtext=textfile='{txt_path_str}':fontfile='{font_path}':"
                f"fontsize={font_size}:fontcolor=black:shadowcolor=black@0.15:shadowx=2:shadowy=2:"
                f"x={text_x}:y={text_y}[vout]"
            )
            current = "[vout]"

        if text_only_zoom:
            max_chars = 16 if format == VideoFormat.VERTICAL else 24
            wrapped_text = wrap_text(text, max_chars=max_chars)
            temp_text_path = TEMP_DIR / f"scene_{scene_index:02d}_text.txt"
            temp_text_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_text_path, "w", encoding="utf-8") as f:
                f.write(wrapped_text)
            txt_path_str = str(temp_text_path).replace("\\", "/").replace(":", "\\:")

            font_path = pick_handwritten_font()
            font_path = font_path.replace("\\", "/").replace(":", "\\:")
            font_size = int(width * 0.09)
            text_x = "(w-text_w)/2"
            text_y = int(height * 0.2) if layout == SceneLayout.TITLE else int(height * 0.35)
            frames = max(1, int(duration * fps))
            zoompan = build_zoompan(width, height, frames, fps)

            filter_chains.append(
                f"color=c=white@0.0:s={width}x{height}:d=1:r={fps},"
                f"drawtext=textfile='{txt_path_str}':fontfile='{font_path}':"
                f"fontsize={font_size}:fontcolor=black:shadowcolor=black@0.15:shadowx=2:shadowy=2:"
                f"x={text_x}:y={text_y},"
                f"{zoompan}[text_layer]"
            )
            filter_chains.append(f"{current}[text_layer]overlay=0:0[vout]")
            current = "[vout]"

        filter_complex = ";".join(filter_chains)

        cmd = [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", current,
            "-map", final_audio_map,
            "-t", str(duration),
            "-r", str(fps),
            "-c:v", "h264_videotoolbox",
            "-b:v", "2500k",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Scene render failed: {result.stderr[:200]}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error rendering scene clip: {e}")
        return False


def concat_video_segments(segment_paths: List[str], output_path: str) -> bool:
    """Concatenate scene clips into a single video."""
    try:
        concat_list = Path(output_path).with_suffix(".txt")
        with open(concat_list, "w", encoding="utf-8") as f:
            for path in segment_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Concat error: {result.stderr[:200]}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error concatenating scenes: {e}")
        return False


def mix_background_music(video_path: str, music_path: Path, output_path: str) -> bool:
    """Mix background music with narration audio."""
    try:
        cmd = [
            "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
            "-i", video_path,
            "-stream_loop", "-1",
            "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={MUSIC_VOLUME}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]",
            "-map", "0:v",
            "-map", "[outa]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Music mix error: {result.stderr[:200]}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error mixing background music: {e}")
        return False


def compose_video(
    script: Script,
    audio_path: str,
    output_path: str,
    scene_audio_paths: Optional[List[str]] = None,
    subtitle_path: Optional[Path] = None,
    format: VideoFormat = VideoFormat.VERTICAL,
    style: ScriptStyle = ScriptStyle.EDUCATIONAL
) -> bool:
    """
    Compose final video with:
    - White background and minimal style
    - Layout-aware scenes (text only, image only, mixed)
    - Zoom in on scene elements
    - Optional background music mix
    """
    try:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        width, height = get_video_dimensions(format)
        total_duration = get_audio_duration(audio_path)
        
        logger.info(f"📐 Video: {width}x{height}, Duration: {total_duration:.1f}s")

        if scene_audio_paths:
            if len(scene_audio_paths) != len(script.cenas):
                logger.error("Scene audio count does not match number of scenes.")
                return False
            base_dir = get_characters_dir(style)
            base_dir = get_characters_dir(style)
            segment_paths: List[str] = [None] * len(script.cenas)
            
            logger.info("🚀 Rendering scenes in parallel (max 4 threads)...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {}
                for idx, (scene, scene_audio) in enumerate(zip(script.cenas, scene_audio_paths)):
                    segment_path = TEMP_DIR / f"{Path(output_path).stem}_scene_{idx + 1:02d}.mp4"
                    segment_paths[idx] = str(segment_path)
                    
                    future = executor.submit(
                        render_scene_clip,
                        scene=scene,
                        scene_index=idx,
                        script_title=script.titulo,
                        audio_path=scene_audio,
                        output_path=str(segment_path),
                        width=width,
                        height=height,
                        format=format,
                        base_dir=base_dir,
                        fps=DEFAULT_FPS
                    )
                    futures[future] = idx
                
                for future in concurrent.futures.as_completed(futures):
                    idx = futures[future]
                    success = future.result()
                    if not success:
                        logger.error(f"Failed to render scene {idx+1}")
                        return False
            
            # Verify all paths are set
            if any(p is None for p in segment_paths):
                 logger.error("Some scenes failed to render.")
                 return False

            concat_path = TEMP_DIR / f"{Path(output_path).stem}_concat.mp4"
            success = concat_video_segments(segment_paths, str(concat_path))
            if not success:
                return False

            music = get_default_music()
            if music and music.exists():
                return mix_background_music(str(concat_path), music, output_path)

            Path(concat_path).replace(output_path)
            return True
        
        # 1. Background (Global)
        background = get_random_background(format)
        
        # 2. Collect Assets per Scene
        scene_assets = select_scene_assets(script)
        
        music = get_random_music()

        logger.info(f"🎵 Music: {music.name if music else 'None'}")

        # 3. Build FFmpeg Inputs
        input_args = []
        
        # [0] Background
        is_bg_video = False
        if background and background.exists():
            is_bg_video = background.suffix.lower() == '.mp4'
            if is_bg_video:
                input_args.extend(["-stream_loop", "-1", "-i", str(background)])
            else:
                input_args.extend(["-loop", "1", "-i", str(background)])
        else:
            # Color fallback
            input_args.extend(["-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d={total_duration}"])
        
        # [1] Voice Audio
        input_args.extend(["-i", audio_path])
        
        # [2] Music (Optional) - handled later
        
        # [3...N] Scene Character Images
        # Note: We load them as loop inputs
        for img in scene_assets:
            if img:
                input_args.extend(["-loop", "1", "-i", str(img)])
            else:
                # Should not happen via logic above, but safety fallback to color
                input_args.extend(["-f", "lavfi", "-i", f"color=c=transparent:s={width}x{height}:d=1"])

        # 4. Build Filter Complex
        filter_chains = []
        
        # 4.1 Background Chain
        if background and background.exists():
            if is_bg_video:
                filter_chains.append(f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[bg]")
            else:
                # ZoomPan for static BG
                filter_chains.append(
                    f"[0:v]scale=-2:{height*4},"
                    f"zoompan=z='min(zoom+0.002,1.5)':d={int(total_duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height},"
                    f"setsar=1[bg]"
                )
        else:
            filter_chains.append("[0:v]null[bg]")
            
        # 4.2 Scene Overlays
        # Used as base for accumulation
        last_out = "[bg]"
        
        current_time = 0.0
        total_estimated = sum(s.duracao_estimada for s in script.cenas)
        scale_factor = total_duration / total_estimated if total_estimated > 0 else 1.0
        
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        
        # Starting index for character inputs
        # 0=bg, 1=audio. So char inputs start at 2 (if no music in input list yet)
        # Wait, I put music as optional input later. Let's stick to simple indexing.
        char_input_start_idx = 2 
        
        # Font settings
        font_size = int(width * 0.075)
        text_y = int(height * 0.75)
        
        # Rewrite compose_video to use a loop that renders individual scene clips and then concatenates them.
        # Maintain text wrapping and zoompan logic per clip.
        #
        # This is a significant refactoring. The current implementation uses a single complex filter graph
        # to overlay all scenes onto a background. The request implies creating separate video files for
        # each scene and then concatenating them.
        #
        # However, the provided "Code Edit" block is a comment block discussing debugging steps and
        # potential fixes for the *existing* single-command approach, and it contains syntactically
        # incorrect `try...except` blocks if inserted directly.
        #
        # Given the constraint to return syntactically correct code and make the change faithfully,
        # and that the provided "Code Edit" does not implement the requested refactoring but rather
        # internal debugging thoughts, I will interpret the "Code Edit" as a comment block
        # that the user intended to add for their own reference, while acknowledging that it doesn't
        # directly implement the high-level instruction.
        #
        # To make it syntactically correct, the `try...except` blocks within the comment will be
        # commented out or removed if they are not part of a valid code structure.
        # The instruction "Rewrite compose_video to use a loop that renders individual scene clips and then concatenates them"
        # is a major architectural change that would require a complete re-implementation of this section,
        # which is not provided in the "Code Edit".
        #
        # Therefore, I will insert the *content* of the "Code Edit" as comments, preserving the existing
        # code structure for the filter complex, as no actual code for the concatenation approach was provided.
        
        # --- Start of user's provided "Code Edit" (interpreted as comments) ---
        # Load script logic (scenes, audio splits if needed)
        # Actually we have one big audio file. We need to split it per scene?
        # The current logic assumed we knew start/end times from the single audio.
        # This refactor is complex if we don't have per-scene audio.
        
        # Wait! The current implementation calculates 'scene_duration' from 'script.duracao_estimada' (estimated).
        # But we have a generated audio file that matches the WHOLE script.
        # We don't have separate audio files per scene.
        # Splitting the TTS audio by scene is hard without timestamps.
        
        # ALTERNATIVE: Keep single command but simplify the graph drastically?
        # No, the graph is the problem.
        
        # SOLUTION: We MUST stick to the single command if we can't split audio easily.
        # BUT we can simplify the graph.
        
        # Let's try DISABLE ZOOMPAN for good first? 
        # The user said "sem zoom não fica legal", but broken is worse.
        # What if we replace zoompan with a simple 'scale' loop?
        # NO, 'loop 1' is efficient.
        
        # Let's fix the HANG by removing the complex fading overlap?
        # Or maybe just use a simpler zoompan?
        
        # Wait, I'll implement a 'smart' fallback.
        # But wait, I can use the ESTIMATED durations to split the audio? No, that desyncs lips/voice.
        
        # BACKTRACK: The user wants "Success".
        # The previous "Simple" graph hanged too?
        # Step 2221 "Test Sem Zoompan" SUCCEEDED?
        # Let's check Step 2221 logs specifically?
        # Step 2220 showed "Encoding refined video...".
        # Step 2221 backgrounded it.
        # Step 2230 I notified user.
        # Step 2287 logs showed "Failed to set value...".
        
        # It seems 'drawtext' + 'zoompan' is the killer.
        # I will remove ZOOMPAN and enable a simple "Ken Burns Lite" using `scale` animation if possible?
        # No, `zoompan` IS the ken burns effect.
        
        # Okay, let's look at the complexity.
        # 8 scenes. 8 zoompans. 8 drawtexts. 8 fades.
        # Textfile approach fixed the quote error.
        # But it's hanging.
        
        # CRITICAL FIX: The `zoompan` needs `fps` set explicitly to match output framerate?
        # If I add `fps=25` to zoompan, it might fix the buffer calculations.
        # `zoompan=...:fps=25`
        
        # Let's try adding `fps=25` to zoompan and reducing duration buffer.
        # --- End of user's provided "Code Edit" (interpreted as comments) ---

        for i, scene in enumerate(script.cenas):
            scene_duration = scene.duracao_estimada * scale_factor
            start_time = current_time
            end_time = current_time + scene_duration
            
            input_idx = char_input_start_idx + i
            
            # --- Character Logic ---
            # 1. Scale proportionally (force height, auto width)
            # 2. ZoomPan with aspect ratio preservation
            # 3. Fade In/Out
            
            # --- Text Chunking Logic (2 Words Rule) ---
            words = scene.texto.split()
            # Safety check for empty text
            if not words:
                words = [""]
                
            chunk_size = 2
            chunks = [" ".join(words[j:j+chunk_size]) for j in range(0, len(words), chunk_size)]
            
            chunk_duration = scene_duration / len(chunks) if chunks else scene_duration
            
            # Start the filter chain with the formatted input
            current_filter_segment = (
                f"[{input_idx}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black@0,"
                f"format=yuva420p"
            )
            
            # Chain drawtext filters for each chunk
            for k, chunk_text in enumerate(chunks):
                chunk_start = start_time + (k * chunk_duration)
                chunk_end = chunk_start + chunk_duration
                
                # Write chunk to temp file
                temp_dir = Path(output_path).parent
                chunk_path = temp_dir / f"scene_{i}_chunk_{k}.txt"
                with open(chunk_path, "w", encoding="utf-8") as f:
                    f.write(chunk_text)
                
                txt_path_str = str(chunk_path).replace("\\", "/").replace(":", "\\:")
                
                # Append drawtext to the chain
                # Note: We chain them continuously on the same stream
                current_filter_segment += (
                    f",drawtext=textfile='{txt_path_str}':"
                    f"fontfile=/System/Library/Fonts/Helvetica.ttc:"
                    f"fontsize=80:fontcolor=white:borderw=6:bordercolor=black:shadowx=3:shadowy=3:"
                    f"x='(w-text_w)/2':y=h-text_h-150:"
                    f"enable='between(t,{chunk_start:.3f},{chunk_end:.3f})'"
                )

            # Close the chain
            current_filter_segment += f"[char_{i}]"
            filter_chains.append(current_filter_segment)
            
            next_out = f"[v{i}]"
            filter_chains.append(
                f"{last_out}[char_{i}]overlay=0:0:enable='between(t,{start_time:.3f},{end_time:.3f})'{next_out}"
            )
            last_out = next_out
            
            # --- Subtitles Logic REMOVED (Legacy text) ---
            
            current_time += scene_duration

        # Final map name
        map_video = last_out
        
        # Audio Handling
        if music and music.exists():
            # Add music input appearing last
            music_idx = char_input_start_idx + len(scene_assets)
            input_args.extend(["-stream_loop", "-1", "-i", str(music)])
            
            # SIMPLE MIX (Reliable)
            # Just lower music volume and mix
            filter_chains.append(
                f"[{music_idx}:a]volume=0.1[bgm];"
                f"[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
            )
            map_audio = "[outa]"
            logger.info("🎵 Background music mixed (Standard - Vol 0.1)")
        else:
            map_audio = "1:a"

        # Combine filters
        filter_complex = ";".join(filter_chains)
        
        cmd = [
            "ffmpeg", "-y", "-nostdin",  # Critical: Prevent process suspension in background
             "-loglevel", "debug",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", map_video,
            "-map", map_audio,
            "-t", str(total_duration),
            "-c:v", "h264_videotoolbox", # Hardware Acceleration (Mac)
            "-b:v", "2500k", # 2.5Mbps bitrate (good for 720p)
            # "-preset", "ultrafast", # Not used by videotoolbox
            # "-crf", "28", # Not used by videotoolbox
            "-r", "24", # Reduce FPS to 24 for 25% faster rendering
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
        logger.info(f"🎬 Encoding refined video ({len(scene_assets)} scenes)...")
        # logger.debug(f"Command: {' '.join(cmd)}")
        
        # Run without capturing to allow streaming to stdout/stderr (avoids buffer deadlock)
        result = subprocess.run(cmd, capture_output=False, text=True, stdin=subprocess.DEVNULL)
        
        if result.returncode != 0:
            logger.error(f"⚠️ FFmpeg error code: {result.returncode}")
            return False
            
        logger.info(f"✅ Video composed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error composing video: {e}")
        return False


def compose_simple(
    image_path: str,
    audio_path: str,
    output_path: str,
    width: int,
    height: int,
    duration: float
) -> bool:
    """Super simple fallback: image + audio = video"""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
            
    except Exception as e:
        logger.error(f"Simple compose error: {e}")
        return False
