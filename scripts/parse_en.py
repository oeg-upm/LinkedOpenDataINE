from deep_translator import GoogleTranslator

# Traducción de un solo texto
with open("parsed_nombres.txt", "r", encoding="utf-8") as f:
    texto_es = f.read().strip()
texto_en = GoogleTranslator(source='es', target='en').translate(texto_es)
with open("parsed_nombres_en.txt", "w", encoding="utf-8") as f_out:
    f_out.write(texto_en)

#print(f"Español: {texto_es}")
print(f"Inglés: {texto_en}")
