import google.generativeai as genai
import os

GEMINI_API_KEY = "AIzaSyC_a03J5r5V9WBoOvwOxhr5Mld9U6b-Lgs"
genai.configure(api_key=GEMINI_API_KEY)

print("Listing models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
