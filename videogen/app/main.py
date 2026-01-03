"""
VideoGen - Main FastAPI Application
Direct generation mode (no approval step)
"""
import os
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from app.models.schemas import (
    GenerateRequest,
    GenerateFromScriptRequest,
    GenerateResponse,
    Script,
    VideoFormat,
    Language,
    ScriptStyle,
    VideoDuration,
    EditStyle,
    VoicePreset,
    VOICE_INSTRUCTIONS
)
from app.services.script_gen import generate_script
from app.services.audio_gen import generate_script_audio, generate_script_audio_segments
from app.services.video_gen import compose_video, select_scene_assets, CHARACTERS_DIR, get_audio_duration

# Paths
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager"""
    print("🚀 VideoGen starting...")
    print("⚡ OpenAI TTS + Gemini ready!")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    yield
    print("👋 VideoGen shutting down...")


app = FastAPI(
    title="VideoGen",
    description="🎬 Gerador de Vídeos Virais com IA",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR / "characters")), name="assets_chars")
app.mount("/voices", StaticFiles(directory=str(ASSETS_DIR / "voices")), name="assets_voices")
app.mount("/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")


@app.post("/api/preview")
async def api_preview(request: GenerateRequest) -> dict:
    """
    Generate ingredients for instant preview (Script + Audio + Assets Loop)
    Skips FFmpeg rendering for speed (Instant).
    """
    from .utils.logger import logger
    try:
        job_id = str(uuid.uuid4())[:8]
        
        # 1. Script
        logger.info(f"⚡ [{job_id}] generating PREVIEW script...")
        script = await generate_script(
            tema=request.tema,
            idioma=request.idioma,
            estilo=request.estilo,
            duracao=request.duracao,
            edicao=request.edicao
        )
        if not script: return {"success": False, "error": "Script generation failed"}
        
        # 2. Audio
        logger.info(f"⚡ [{job_id}] generating PREVIEW audio...")
        audio_dir = TEMP_DIR / job_id
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        audio_path_abs = generate_script_audio(
            script=script,
            output_dir=str(audio_dir),
            voice=request.voz,
            voice_instruction=request.voz_instrucao,
            speed=request.velocidade
        )
        if not audio_path_abs: return {"success": False, "error": "Audio generation failed"}

        # 3. Assets (Simulate selection)
        logger.info(f"⚡ [{job_id}] selecting PREVIEW assets...")
        assets_paths = select_scene_assets(script, style=request.estilo)
        
        assets_urls = []
        for p in assets_paths:
            if p:
                rel = p.relative_to(CHARACTERS_DIR)
                assets_urls.append(f"/assets/{rel}")
            else:
                assets_urls.append("")

        # 4. Estimation of Durations
        # Simple char-count based ratio
        total_duration = get_audio_duration(audio_path_abs)
        total_chars = sum(len(s.texto) for s in script.cenas)
        if total_chars == 0: total_chars = 1
        
        durations = []
        for s in script.cenas:
            ratio = len(s.texto) / total_chars
            durations.append(ratio * total_duration)

        return {
            "success": True,
            "job_id": job_id,
            "script": script,
            "audio_url": f"/temp/{job_id}/audio.mp3",
            "assets": assets_urls,
            "durations": durations
        }

    except Exception as e:
        logger.error(f"❌ Preview Error: {e}")
        return {"success": False, "error": str(e)}



@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text())
    return HTMLResponse(content="<h1>VideoGen API</h1><p>Use /docs for API.</p>")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "videogen", "version": "2.0"}


@app.get("/api/options")
async def get_options():
    """Get all available options for the frontend"""
    return {
        "estilos": [{"value": s.value, "label": s.value.capitalize()} for s in ScriptStyle],
        "duracoes": [
            {"value": "short", "label": "Curto (15-30s)"},
            {"value": "medium", "label": "Médio (30-60s)"},
            {"value": "long", "label": "Longo (60-90s)"},
        ],
        "edicoes": [
            {"value": "tiktok", "label": "TikTok (cortes rápidos)"},
            {"value": "calm", "label": "Calmo (mais lento)"},
            {"value": "dynamic", "label": "Dinâmico (variado)"},
        ],
        "vozes": [{"value": v.value, "label": v.value.capitalize()} for v in VoicePreset],
        "voz_instrucoes": [
            {"value": "brazilian_energetic", "label": "🇧🇷 Brasileiro Energético"},
            {"value": "brazilian_calm", "label": "🇧🇷 Brasileiro Calmo"},
            {"value": "narrator", "label": "🎙️ Narrador"},
            {"value": "friendly", "label": "😊 Amigável"},
            {"value": "dramatic", "label": "🎭 Dramático"},
        ],
        "formatos": [
            {"value": "vertical", "label": "📱 Vertical (TikTok/Reels)"},
            {"value": "horizontal", "label": "🖥️ Horizontal (YouTube)"},
        ],
        "idiomas": [
            {"value": "pt", "label": "🇧🇷 Português"},
            {"value": "en", "label": "🇺🇸 English"},
            {"value": "es", "label": "🇪🇸 Español"},
        ],
    }


@app.post("/api/generate")
async def api_generate(request: GenerateRequest) -> GenerateResponse:
    """
    Generate video directly (no approval step)
    
    Full pipeline: Script → Audio → Video
    """
    from .utils.logger import logger
    try:
        job_id = str(uuid.uuid4())[:8]
        
        # Step 1: Generate script
        logger.info(f"📦 REQUEST PAYLOAD: {request.model_dump()}")
        logger.info(f"📝 [{job_id}] Generating script: {request.tema}")
        logger.info(f"    Style: {request.estilo.value} | Duration: {request.duracao.value} | Edit: {request.edicao.value}")
        
        script = await generate_script(
            tema=request.tema,
            idioma=request.idioma,
            estilo=request.estilo,
            duracao=request.duracao,
            edicao=request.edicao
        )
        
        if not script:
            return GenerateResponse(success=False, error="Failed to generate script")
        
        logger.info(f"✅ [{job_id}] Script: {len(script.cenas)} scenes")
        
        # Step 2: Generate audio
        logger.info(f"🎤 [{job_id}] Generating audio (voice: {request.voz.value})")
        
        audio_dir = TEMP_DIR / job_id
        audio_result = generate_script_audio_segments(
            script=script,
            output_dir=str(audio_dir),
            voice=request.voz,
            voice_instruction=request.voz_instrucao,
            speed=request.velocidade
        )
        
        if not audio_result:
            return GenerateResponse(success=False, script=script, error="Failed to generate audio")

        audio_path, scene_audio_paths = audio_result
        logger.info(f"✅ [{job_id}] Audio generated")
        subs_arg = None
        
        # Step 3: Compose video
        logger.info(f"🎥 [{job_id}] Composing video")
        
        import time
        output_filename = f"video_{job_id}_{int(time.time())}.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        success = compose_video(
            script=script,
            audio_path=audio_path,
            scene_audio_paths=scene_audio_paths,
            output_path=str(output_path),
            subtitle_path=subs_arg,
            format=request.formato,
            style=request.estilo
        )
        
        if not success:
            return GenerateResponse(success=False, script=script, error="Failed to compose video")
        
        logger.info(f"🎉 [{job_id}] Video complete: {output_filename}")
        
        return GenerateResponse(
            success=True,
            video_path=f"/output/{output_filename}",
            script=script
        )
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return GenerateResponse(success=False, error=str(e))


@app.post("/api/generate-script")
async def api_generate_script(request: GenerateRequest) -> dict:
    """Generate only the script (for preview)"""
    script = await generate_script(
        tema=request.tema,
        idioma=request.idioma,
        estilo=request.estilo,
        duracao=request.duracao,
        edicao=request.edicao
    )
    
    if not script:
        raise HTTPException(status_code=500, detail="Failed to generate script")
    
    return {"success": True, "script": script.model_dump()}


@app.get("/api/download/{filename}")
async def download_video(filename: str):
    """Download a generated video"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(path=str(file_path), filename=filename, media_type="video/mp4")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
