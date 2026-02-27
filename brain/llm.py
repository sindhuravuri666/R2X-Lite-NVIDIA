import requests
from config import LLM_MODEL

OLLAMA_URL = "http://localhost:11434/api/generate"

def call_llm(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]