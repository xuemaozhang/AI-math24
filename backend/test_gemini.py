import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")


genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Explain how AI works in a few words")
print(response.text)
