import os
import pandas as pd
from rembg import remove
from PIL import Image
import io
from pathlib import Path
import re

# Configuração dos caminhos
DOWNLOADS_DIR = Path("/Users/joao/Downloads/ImageFX_Images")
CSV_PATH = DOWNLOADS_DIR / "labs_imagefx_20251226_1452.csv"
OUTPUT_BASE_DIR = Path("/Users/joao/core-casts/chatterbox/videogen/assets/characters")

# Mapeamento de palavras-chave para categorias
# Tenta encontrar a palavra apos "monkey" ou adjetivos
def extract_category(prompt):
    prompt_lower = prompt.lower()
    
    # Lista de prioridade (profissões/emoções)
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
        "studying": "student",
        "study": "student",
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
        "confused": "confused",
        "magician": "magician",
        "magic": "magician",
        "athlete": "athlete",
        "running": "athlete",
        "yoga": "yoga",
        "traveler": "traveler",
        "backpack": "traveler"
    }
    
    for key, category in keywords.items():
        if key in prompt_lower:
            return category
            
    return "other"

def process_images():
    print("🚀 Iniciando processamento de imagens...")
    
    # Ler CSV
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"📄 CSV carregado: {len(df)} imagens encontradas.")
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return

    # Contadores para nomeação sequencial por categoria
    category_counts = {}

    for index, row in df.iterrows():
        original_name = row['Image Name']
        prompt = row['Prompt']
        
        # Corrigir extensão se necessario (no CSV pode estar .png mas arquivo ser .jpeg)
        # O list_dir mostrou que são .jpeg
        if original_name.endswith(".png"):
            original_name = original_name.replace(".png", ".jpeg")
            
        input_path = DOWNLOADS_DIR / original_name
        
        if not input_path.exists():
            print(f"⚠️ Arquivo não encontrado: {original_name}")
            continue
            
        # Determinar categoria
        category = extract_category(prompt)
        
        # Criar pasta de saida
        output_dir = OUTPUT_BASE_DIR / category
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome sequencial: happy_1.png, happy_2.png
        count = category_counts.get(category, 0) + 1
        category_counts[category] = count
        
        output_filename = f"{category}_{count}.png"
        output_path = output_dir / output_filename
        
        print(f"🔄 Processando [{category}]: {original_name} -> {output_filename}...")
        
        try:
            # Abrir imagem
            input_image = Image.open(input_path)
            
            # Remover fundo
            output_image = remove(input_image)
            
            # Salvar como PNG (com transparência)
            output_image.save(output_path, "PNG")
            
        except Exception as e:
            print(f"❌ Erro ao processar {original_name}: {e}")

    print("✅ Processamento concluído!")
    print("\nResumo:")
    for cat, count in category_counts.items():
        print(f"  - {cat}: {count} imagens")

if __name__ == "__main__":
    process_images()
