import mss
import base64
import requests
from io import BytesIO
from PIL import Image
from config import VISION_MODEL

OLLAMA_URL = "http://localhost:11434/api/generate"

def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        img.thumbnail((800, 800))
        return img

def analyze_screen(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": VISION_MODEL,
                "prompt": "Describe what is visible on this screen in 2-3 sentences.",
                "images": [img_base64],
                "stream": False
            },
            timeout=60   # moondream is slow on CPU — give it a full minute
        )
        data = response.json()
        if "response" in data:
            return data["response"]
        return "I could not analyze the screen."
    except requests.exceptions.ReadTimeout:
        return "Screen analysis timed out. The vision model is taking too long on CPU."
    except Exception as e:
        return f"Screen analysis failed: {e}"