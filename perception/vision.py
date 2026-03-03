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

        # Resize for CPU performance
        img.thumbnail((800, 800))

        return img

def analyze_screen(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()

    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": VISION_MODEL,
            "prompt": "Describe what is visible on this screen.",
            "images": [img_base64],
            "stream": False
        }
    )

    data = response.json()

    if "response" in data:
        return data["response"]
    else:
        return f"Vision API returned unexpected data: {data}"