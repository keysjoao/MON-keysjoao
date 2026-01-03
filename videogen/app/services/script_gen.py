"""
Script Generator Service - Uses Gemini 2.5 Flash to generate video scripts
Supports: styles, duration presets, edit styles
Refined Prompts for Viral/Engaging Content
"""
import google.generativeai as genai
import json
import re
from typing import Optional

from ..models.schemas import Script, Scene, Language, Emotion, ScriptStyle, VideoDuration, EditStyle, SceneLayout


# Gemini API Key  
GEMINI_API_KEY = "AIzaSyC_a03J5r5V9WBoOvwOxhr5Mld9U6b-Lgs"
genai.configure(api_key=GEMINI_API_KEY)


# Duration settings
DURATION_CONFIG = {
    VideoDuration.SHORT: {"min_cenas": 3, "max_cenas": 5, "duracao_cena": 3},
    VideoDuration.MEDIUM: {"min_cenas": 5, "max_cenas": 8, "duracao_cena": 5},
    VideoDuration.LONG: {"min_cenas": 8, "max_cenas": 12, "duracao_cena": 6},
    VideoDuration.EXTRA_LONG: {"min_cenas": 40, "max_cenas": 60, "duracao_cena": 6},
}

EDIT_CONFIG = {
    EditStyle.TIKTOK: 2.5,   # 2.5s per scene
    EditStyle.CALM: 6.0,     # 6s per scene
    EditStyle.DYNAMIC: 3.5,  # Slightly faster dynamic
}


STYLE_PROMPTS = {
    ScriptStyle.EDUCATIONAL: """ATUE COMO: Um comunicador científico de classe mundial (estilo Kurzgesagt/VSauce).
OBJETIVO: Transformar tópicos complexos em 'Brain Candy' viciante que PARA o scroll.

🛑 HOOK OBRIGATÓRIO (Cena 1 - 3 segundos):
A PRIMEIRA FRASE deve ser um "scroll-stopper". Use uma destas técnicas:
- Pergunta chocante: "Por que 90% das pessoas FALHAM em...?"
- Afirmação contrária: "Tudo que te ensinaram sobre X está ERRADO."
- Número impactante: "97% das pessoas não sabem que..."
- Promessa forte: "Depois desse vídeo, você nunca mais vai ver X da mesma forma."

ESTRUTURA:
1. HOOK (3s): Pare o scroll. Seja URGENTE.
2. OPEN LOOP: Crie curiosidade ("E o pior? Eu vou te mostrar o motivo...")
3. Core Analogy: Use metáforas visuais FORTES e CONCRETAS.
4. PATTERN INTERRUPT (a cada 7-10s): Mude algo (emoção, ritmo, visual).
5. Payoff: Entregue o que prometeu.
6. CTA + Open Loop: "Comenta se você já sabia disso...".""",

    ScriptStyle.POLEMIC: """ATUE COMO: Um debatedor provocativo e contrarian (Viral Twitter/X Thread Writer).
OBJETIVO: POLARIZAR. Gerar debate. Fazer as pessoas comentarem discordando.

🛑 HOOK OBRIGATÓRIO (Cena 1):
- "ELES estão mentindo pra você sobre..."
- "Isso vai te irritar, mas precisa ser dito..."
- "Ninguém tem coragem de falar, mas..."

ESTRUTURA:
1. ATTACK: Ataque uma crença popular logo de cara.
2. EXPOSIÇÃO: Mostre a "verdade inconveniente" com dados.
3. NÓS VS ELES: Crie um vilão (o sistema, as empresas, etc).
4. DESAFIO: "Se você discorda, prove nos comentários."
5. CTA PROVOCATIVO: "Salva esse vídeo antes que apaguem.".""",

    ScriptStyle.NEWS: """ATUE COMO: Um âncora de Breaking News moderno (estilo TikTok News/Morning Brew).
OBJETIVO: URGÊNCIA. Informar em menos de 60 segundos com impacto máximo.

🛑 HOOK OBRIGATÓRIO (Cena 1):
- "ATENÇÃO: Acabou de sair..."
- "URGENTE: Isso muda TUDO..."
- "BREAKING: O que ninguém está te contando..."

ESTRUTURA:
1. URGÊNCIA: Vá direto ao ponto com energia.
2. FATO + IMPACTO: O que aconteceu e por que você deveria se importar.
3. DADOS VISUAIS: Use números (texto_tela).
4. CONSEQUÊNCIA: O que isso significa para VOCÊ.
5. CTA: "Compartilha com quem PRECISA saber.".""",

    ScriptStyle.STORYTELLING: """ATUE COMO: Um roteirista da Pixar focado em micro-narrativas emocionantes.
OBJETIVO: EMOCIONAR. Criar conexão instantânea através de história.

🛑 HOOK OBRIGATÓRIO (Cena 1):
- "Tudo estava normal, até que..."
- "Eu nunca vou esquecer o dia em que..."
- "Ninguém imaginava que uma simples [coisa] ia mudar tudo..."

ESTRUTURA:
1. INCIDENTE INCITANTE: O momento que muda tudo.
2. CONFLITO: O herói enfrenta um obstáculo VISUAL.
3. JORNADA: Mostre a luta (use emoções variadas).
4. CLÍMAX: O momento de virada (pause dramático).
5. RESOLUÇÃO: Lição moral ou twist inesperado.""",

    ScriptStyle.HUMOR: """ATUE COMO: Um comediante de Stand-up cínico (estilo Porta dos Fundos/Whindersson).
OBJETIVO: VIRALIZAR pelo humor. Fazer a pessoa rir e marcar os amigos.

🛑 HOOK OBRIGATÓRIO (Cena 1):
- "Sabe quando você [situação absurda]?"
- "Eu juro que eu não sou o único que..."
- "POV: Você acabou de [situação cômica]."

ESTRUTURA:
1. SETUP RELATABLE: Situação que TODO mundo passa.
2. ESCALADA ABSURDA: Leve ao extremo ridículo.
3. PUNCHLINE VISUAL: O auge da piada (use layout multi_image ou image_text).
4. FINAL AUTO-DEPRECIATIVO: Ria de si mesmo.""",

    ScriptStyle.PRIMATA: """ATUE COMO: O "Primo Primata" ou "Programador Primata" (Influenciador de Finanças/Tech).
OBJETIVO: Ensinar conceitos complexos para "macacos" usando BANANAS e GALHOS.
TOM: Didático, levemente sarcástico, gírias de selva, focado em "EVOLUÇÃO".

🛑 HOOK OBRIGATÓRIO (Cena 1):
- "Você está pulando de GALHO em GALHO sem sair do lugar?"
- "Te prometeram um cacho de BANANAS, mas te deram CASCAS."
- "Olha, MACACO VELHO aqui te avisando..."

VOCABULÁRIO (Use em CAIXA ALTA):
- BANANAS = Dinheiro / Recursos
- GALHO = Oportunidade / Emprego  
- SELVA = Mercado / Mundo Real
- EVOLUÇÃO = Crescimento / Promoção
- MACACO VELHO = Experiência

ESTRUTURA:
1. O PROBLEMA DA SELVA: Dor identificável.
2. A ILUSÃO DAS BANANAS: O que prometeram vs realidade.
3. A LEI DA EVOLUÇÃO: Conceito técnico via metáfora.
4. O PULO DO MACACO: Solução prática.
5. CTA: "Evolua seu bando agora.".""",

    ScriptStyle.AUTOLABS: """ATUE COMO: Um criador de conteúdo viral de ANIMAÇÃO (estilo MrBeast/Kurzgesagt com macacos).
OBJETIVO: Criar conteúdo EXTREMAMENTE dinâmico usando animações de macacos em diferentes situações.

🛑 HOOK OBRIGATÓRIO (Cena 1):
- Gancho VISUAL forte (use texto_tela impactante).
- Frase curta e direta que para o scroll.
- Use analogias visuais: "Você está trabalhando igual macaco..." (typing), "Ficou rico dormindo?" (rich).

🎬 ASSETS VISUAIS (use no campo `assets`):
O banco de imagens agora consiste em VÍDEOS animados (AutoLabs). Use a chave que melhor descreve a cena.

LISTA DE ASSETS (VÍDEOS) DISPONÍVEIS:
- Profissões/Ações: chef, cientist (cientista), doctor (médico), pilot, youtuber, youtuber2, filming (filmando), streaming, typing (digitando), reading (lendo), studing (estudando - sic), studing2, studing3, explaning (explicando), planning (planejando), cooking, cooking2, selling (vendendo), math (matemática/contas)
- Emoções/Estados: angry (bravo), sad (triste), thinking (pensando), rich (rico), senior (idoso), baby, son (filho), kissing (beijando), dancing (dançando), running (correndo), surfing, travel (viajando)
- Específicos/Fun: hero-ironman, hero-spiderman, monster, robot, robot2, talking-robot, oscar (prêmio), market, supermarket, garden, garden2, crochet, soap, soaping, tattoo, flighting (lutando/voando?)
- Logos & CTAs (Use prefixo 'logo:'): logo:chatgpt-logo, logo:claude-logo, logo:gemini-logo, logo:n8n-logo, logo:supabase-logo, logo:llm-logo, logo:like (curtir), logo:comenta (comentar), logo:inscreva (inscrever-se)

COMO USAR:
- Exemplo: `["hero-ironman"]`, `["angry"]`, `["typing"]`.
- Use 1 asset por cena.

🎯 REGRAS DE OURO:
1. Use APENAS as chaves da lista acima.
2. Priorize vídeos que combinem com a ação (ex: 'typing' para trabalho, 'running' para pressa).
3. texto_tela: 2-4 palavras IMPACTANTES.
4. Texto falado: Clara e envolvente.

ESTRUTURA SUGERIDA:
- Use assets de movimento ('running', 'dancing') para quebrar padrões.
- Use 'talking-robot' ou 'explaning' para partes educativas.""",
}


def build_prompt(estilo: ScriptStyle, duracao: VideoDuration, edicao: EditStyle) -> str:
    """Build the system prompt with all configurations"""
    
    dur_config = DURATION_CONFIG[duracao]
    edit_dur = EDIT_CONFIG[edicao]
    
    style_base = STYLE_PROMPTS.get(estilo, STYLE_PROMPTS[ScriptStyle.EDUCATIONAL])
    
    available_assets = ", ".join([e.value for e in Emotion])

    duration_instruction = ""
    if duracao == VideoDuration.EXTRA_LONG:
        duration_instruction = """
⚠️ INSTRUÇÃO CRÍTICA DE DURAÇÃO (10 MINUTOS):
- Este vídeo será gerado em 3 PARTES. Esta é a PARTE ATUAL.
- Mantenha o foco EXCLUSIVO na seção pedida (início, meio ou fim).
- Seja profundo e detalhista.
"""
    else:
        duration_instruction = f"- Tempo alvo por cena: ~{edit_dur}s (seja conciso!)"

    return f"""{style_base}

CONFIGURAÇÕES TÉCNICAS:
- Cenas: {dur_config['min_cenas']} a {dur_config['max_cenas']}
{duration_instruction}
- Edição: {'CORTES RÁPIDOS E DINÂMICOS' if edicao == EditStyle.TIKTOK else 'Ritmo cadenciado'}

🎯 INTEGRAÇÃO VISUAL (CRÍTICO):
Este roteiro será ilustrado por uma IA que seleciona imagens baseada em PALAVRAS-CHAVE no seu texto.
Você TEM que usar palavras que ativem os seguintes personagens (use como ANALOGIAS):

1. PROFISSÕES (Use metaforicamente):
   - "Apague esse incêndio" -> ativa Bombeiro (firefighter)
   - "Diagnóstico preciso" -> ativa Médico (doctor)
   - "Investigue a fundo" -> ativa Detetive (detective) / Policial
   - "Decole sua carreira" -> ativa Astronauta (astronaut)
   - "Receita do sucesso" -> ativa Chef
   - "Construa seu futuro" -> ativa Construção (construction)
   - "Plante sementes" -> ativa Fazendeiro (farmer)
   - "A fórmula mágica" -> ativa Cientista (scientist) / Mágico (magician)
   - "No comando / Trono" -> ativa Rei (king)
   - "Aventure-se / Mapa" -> ativa Pirata / Viajante (traveler)
   - "Performance / Show" -> ativa Músico / Artista / Atleta

2. ESTADOS/EMOÇÕES:
   - Bebê/Criança (início, novo), Velho/Idoso (sabedoria, passado)
   - Rico (luxo, dinheiro), Pobre (falta, dívida)
   - Yoga (paz, calma), Business (negócios, dinheiro)

⚠️ REGRA DE OURO:
Não escreva apenas "ele ficou feliz". Escreva "Ele se sentiu como um REI no trono" (para mostrar o rei) ou "Ele decolou como um FOGUETE" (para mostrar astronauta).
USE O VOCABULÁRIO VISUAL ACIMA!

🎬 ESTILO VISUAL (OBRIGATÓRIO):
- Fundo branco, minimalista, com cenas variando entre: apenas texto, apenas imagem, texto + imagem, múltiplas imagens.
- Sempre dê instruções visuais para a cena usando `layout` e `assets`.
- `layout` deve ser UM destes valores: title, text_only, image_only, image_text, multi_image.
- `texto_tela` é o texto curto que aparece na tela (geralmente manuscrito).
- `assets` é uma lista de elementos visuais. Use categorias disponíveis ou `icon:<nome>` para ícones.
- Use `multi_image` quando precisar de 2+ personagens/elementos na mesma cena.
- SUGESTÃO: 1a cena quase sempre `title` com o tema do vídeo.

ASSETS DISPONÍVEIS (categorias): {available_assets}
Exemplos de ícones: icon:folder, icon:document, icon:warning, icon:code, icon:banana.

OUTPUT FORMAT (JSON ONLY):
{{
  "titulo": "Título Viral (Curto)",
  "cenas": [
    {{
      "id": 1, 
      "timestamp": "00:00-00:05",
      "texto": "Texto falado (com as palavras-chave visuais)...", 
      "emocao": "happy", 
      "duracao_estimada": {edit_dur}, 
      "texto_destaque": "PALAVRA CHAVE" (Max 2 palavras),
      "texto_tela": "Texto curto para aparecer na tela",
      "layout": "title | text_only | image_only | image_text | multi_image",
      "assets": ["business", "icon:folder"]
    }}
  ]
}}

Responda APENAS o JSON válido. Sem markdown (```json)."""


def estimate_duration(text: str, target: float = 4.0) -> float:
    """Estimate speech duration"""
    words = len(text.split())
    # Fala média: ~150 palavras/min = 2.5 palavras/seg
    estimated = words / 2.5
    return max(target * 0.7, min(estimated, target * 1.3))


async def _generate_part(
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 3
) -> Optional[dict]:
    """Helper to generate a single part of the script"""
    model = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                [system_prompt, user_prompt],
                generation_config={
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                }
            )
            
            response_text = response.text.strip()
            
            # Additional cleanup if needed
            response_text = response_text.replace("```json", "").replace("```", "")
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"⚠️ Error generating part (Attempt {attempt+1}/{max_retries}): {e}")
            continue
            
    print(f"❌ Failed to generate part after {max_retries} attempts.")
    return None

async def generate_script(
    tema: str,
    idioma: Language = Language.PT,
    estilo: ScriptStyle = ScriptStyle.EDUCATIONAL,
    duracao: VideoDuration = VideoDuration.MEDIUM,
    edicao: EditStyle = EditStyle.DYNAMIC
) -> Optional[Script]:
    """Generate a video script using Gemini (supports multi-part for extra long)"""
    
    system_prompt = build_prompt(estilo, duracao, edicao)
    
    language_map = {
        Language.PT: "Português Brasileiro (Natural e Conversacional)",
        Language.EN: "English (Native Speaker)", 
        Language.ES: "Español"
    }
    
    lang_str = language_map.get(idioma, 'Português')
    
    # --- STRATEGY SELECTION ---
    if duracao == VideoDuration.EXTRA_LONG:
        print("🚀 Starting Multi-Part Generation (Worker Strategy)...")
        parts_data = []
        
        # PART 1: INTRO
        print("🔹 Generating Part 1: Intro...")
        p1_prompt = f"""TEMA: {tema}
IDIOMA: {lang_str}
FASE: 1/3 - INTRODUÇÃO E PROBLEMA (Cenas 1 a 15)
OBJETIVO: Ganhar a atenção (Hook), apresentar o problema ("A Selva") e prometer a solução.
NÃO resolva tudo agora. Apenas prepare o terreno.
Lembre-se: Use analogias visuais!"""
        
        data_p1 = await _generate_part(system_prompt, p1_prompt)
        if not data_p1: return None
        parts_data.append(data_p1)
        
        # Review P1 to feed into P2 (Context)
        last_scene_text = data_p1.get("cenas", [])[-1].get("texto", "") if data_p1.get("cenas") else ""
        
        # PART 2: CORE
        print("🔹 Generating Part 2: Deep Dive...")
        p2_prompt = f"""TEMA: {tema}
IDIOMA: {lang_str}
FASE: 2/3 - CONTEÚDO DENSO (Cenas 16 a 45)
CONTEXTO ANTERIOR: O vídeo começou falando sobre: "{data_p1.get('titulo')}". A última frase foi: "{last_scene_text}".
OBJETIVO: Aprofundar no conteúdo. Explicar o "Como fazer". Passo a passo detalhado.
CONTINUE EXATAMENTE DE ONDE PAROU A PARTE 1.
Lembre-se: Use analogias visuais!"""
        
        data_p2 = await _generate_part(system_prompt, p2_prompt)
        if not data_p2: return None
        parts_data.append(data_p2)
        
        last_scene_text_p2 = data_p2.get("cenas", [])[-1].get("texto", "") if data_p2.get("cenas") else ""

        # PART 3: CONCLUSION
        print("🔹 Generating Part 3: Conclusion...")
        p3_prompt = f"""TEMA: {tema}
IDIOMA: {lang_str}
FASE: 3/3 - CONCLUSÃO E CTA (Cenas 46 a 60)
CONTEXTO ANTERIOR: Acabamos de explicar o conteúdo técnico. A última frase foi: "{last_scene_text_p2}".
OBJETIVO: Resumir os pontos chave, dar a lição moral final e fazer a CTA forte.
ENCERRE O VÍDEO COM IMPACTO.
Lembre-se: Use analogias visuais!"""
        
        data_p3 = await _generate_part(system_prompt, p3_prompt)
        if not data_p3: return None
        parts_data.append(data_p3)
        
        # MERGE
        print("✅ Merging parts...")
        full_scenes_data = []
        full_scenes_data.extend(data_p1.get("cenas", []))
        full_scenes_data.extend(data_p2.get("cenas", []))
        full_scenes_data.extend(data_p3.get("cenas", []))
        
        final_title = data_p1.get("titulo", tema) # Use title from Part 1
        
    else:
        # STANDARD SINGLE SHOT
        user_prompt = f"""TEMA DO VÍDEO: {tema}
IDIOMA: {lang_str}
Lembre-se: Use analogias visuais com as profissões listadas!"""
        
        data = await _generate_part(system_prompt, user_prompt)
        if not data: return None
        
        full_scenes_data = data.get("cenas", [])
        final_title = data.get("titulo", tema)

    # --- PROCESS SCENES (COMMON) ---
    target_dur = EDIT_CONFIG[edicao]
    scenes = []
    
    for cena_data in full_scenes_data:
        emocao_str = cena_data.get("emocao", "happy").lower()
        try:
            emocao = Emotion(emocao_str)
        except ValueError:
            emocao = Emotion.HAPPY
        
        texto = cena_data.get("texto", "")
        duracao_est = cena_data.get("duracao_estimada", estimate_duration(texto, target_dur))
        layout_value = cena_data.get("layout")
        if isinstance(layout_value, str):
            layout_value = layout_value.lower()
        try:
            layout = SceneLayout(layout_value) if layout_value else None
        except ValueError:
            layout = None
        
        assets = cena_data.get("assets")
        if isinstance(assets, str):
            assets = [assets]

        scene = Scene(
            id=len(scenes) + 1, # Auto-increment ID
            texto=texto,
            emocao=emocao,
            duracao_estimada=duracao_est,
            texto_destaque=cena_data.get("texto_destaque"),
            texto_tela=cena_data.get("texto_tela"),
            layout=layout,
            assets=assets
        )
        scenes.append(scene)
    
    # Inject CTA Scene around 30 seconds (Cumulative)
    final_scenes = []
    current_duration = 0.0
    cta_inserted = False
    
    for s in scenes:
        final_scenes.append(s)
        current_duration += s.duracao_estimada
        
        if not cta_inserted and current_duration >= 30.0:
            # Add CTA
            try:
                cta_scene = Scene(
                    id=999,
                    texto="E aproveita e comenta aqui embaixo: qual a sua opinião sobre isso? Eu quero saber!",
                    emocao=Emotion.HAPPY,
                    duracao_estimada=4.0,
                    texto_destaque="COMENTE",
                    texto_tela="COMENTE ABAIXO 👇",
                    layout=SceneLayout.IMAGE_TEXT,
                    assets=["logo:comenta"]
                )
                final_scenes.append(cta_scene)
                cta_inserted = True
            except Exception as e:
                print(f"Error creating CTA scene: {e}")
    
    # Final Re-index
    for i, s in enumerate(final_scenes):
        s.id = i + 1
    
    return Script(
        titulo=final_title,
        idioma=idioma,
        cenas=final_scenes
    )
