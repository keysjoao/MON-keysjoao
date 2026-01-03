print("1. Antes do import")
try:
    from rembg import remove
    print("2. Import sucesso")
except Exception as e:
    print(f"Erro import: {e}")
