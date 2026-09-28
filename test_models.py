import os
from google import genai
from dotenv import load_dotenv

# كيقرا الساروت من ملف .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ API Key is missing in .env file!")
else:
    client = genai.Client(api_key=api_key)
    print("✅ Available Models for your API Key:")
    for m in client.models.list():
        if "generateContent" in m.supported_actions:
            print(f" - {m.name}")
