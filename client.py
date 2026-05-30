"""
client.py — Quick standalone test for the Gemini connection.
Run this first to verify your API key works before launching main.py.
"""
import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "<Your Gemini Key Here>")
if "<Your" in GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY env variable or paste your key above.")

client = genai.Client(api_key=GEMINI_API_KEY)

def ask(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"You are Jarvis, a concise voice assistant. Answer in under 3 sentences.\n\nUser: {prompt}"
    )
    return response.text.strip()


if __name__ == "__main__":
    print("Testing Gemini connection...\n")
    response = ask("Hello Jarvis! Introduce yourself in one sentence.")
    print(f"Jarvis: {response}")