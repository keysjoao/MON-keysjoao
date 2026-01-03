import asyncio
from app.services.script_gen import generate_script, ScriptStyle, VideoDuration, EditStyle, Language

async def main():
    print("🚀 Testing EXTRA LONG script generation with Gemini 2.5...")
    script = await generate_script(
        tema="Guia completo sobre a história da computação",
        idioma=Language.PT,
        estilo=ScriptStyle.EDUCATIONAL,
        duracao=VideoDuration.EXTRA_LONG, # 10 minutes test
        edicao=EditStyle.CALM
    )
    
    if script:
        print("✅ Success!")
        print(f"Title: {script.titulo}")
        print(f"Scenes: {len(script.cenas)}")
    else:
        print("❌ Failed.")

if __name__ == "__main__":
    asyncio.run(main())
