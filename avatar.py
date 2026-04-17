import sys
import os
import json
import re
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

print("[Lyra] Loading listener module...")
from perception.listner import listen
print("[Lyra] Listener ready!")

from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from brain.llm import call_llm
from actions.desktop import open_browser, get_time, open_notepad
from perception.tts import speak
from perception.vision import capture_screen, analyze_screen

print("[Lyra] All modules ready!")

IS_SPEAKING = False

SYSTEM_PROMPT = """You are Lyra, a futuristic AI desktop assistant.

IMPORTANT RULES:
1. If a tool is needed, reply with ONLY valid JSON.
2. Do NOT add explanations.
3. Do NOT use markdown.
4. Do NOT use code fences.
5. Do NOT add any text before or after the JSON.
6. If no tool is needed, reply with plain text only.

TOOLS:
{"tool": "open_browser", "args": {"url": "URL"}}
{"tool": "get_time", "args": {}}
{"tool": "open_notepad", "args": {}}
{"tool": "analyze_screen", "args": {}}
"""

TOOLS = {
    "open_browser": open_browser,
    "get_time": get_time,
    "open_notepad": open_notepad,
    "analyze_screen": lambda: analyze_screen(capture_screen()),
}

TOOL_CONFIRMATIONS = {
    "open_browser": "Opening browser.",
    "get_time": None,
    "open_notepad": "Opening Notepad.",
    "analyze_screen": "Analyzing screen.",
}


def extract_json(text):
    if not text:
        return None

    text = text.strip()

    # direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # parse JSON inside code fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass

    # parse first broad JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None


def handle_direct_command(user_input):
    """
    Deterministic command routing for high-confidence local actions.
    Returns:
        ("tool", tool_name, args) or None
    """
    text = user_input.lower().strip()

    # screen analysis
    screen_phrases = [
        "what is on my screen",
        "what's on my screen",
        "whats on my screen",
        "analyze my screen",
        "analyse my screen",
        "describe my screen",
        "read my screen",
        "what do you see on my screen",
        "can you see my screen",
        "tell me what is on my screen",
    ]
    if any(p in text for p in screen_phrases):
        return ("tool", "analyze_screen", {})

    # time
    time_phrases = [
        "what time is it",
        "tell me the time",
        "current time",
        "what's the time",
        "whats the time",
    ]
    if any(p in text for p in time_phrases):
        return ("tool", "get_time", {})

    # notepad
    notepad_phrases = [
        "open notepad",
        "launch notepad",
        "start notepad",
    ]
    if any(p in text for p in notepad_phrases):
        return ("tool", "open_notepad", {})

    # browser
    browser_phrases = [
        "open browser",
        "launch browser",
        "start browser",
        "open google",
        "go to google",
    ]
    if any(p in text for p in browser_phrases):
        if "google" in text:
            return ("tool", "open_browser", {"url": "https://www.google.com"})
        return ("tool", "open_browser", {"url": "https://www.google.com"})

    return None


class AssistantWorker(QThread):
    set_state = pyqtSignal(str)

    def run(self):
        global IS_SPEAKING

        while True:
            try:
                if IS_SPEAKING:
                    time.sleep(0.2)
                    continue

                # LISTEN
                self.set_state.emit("listening")
                user_input = listen()

                if not isinstance(user_input, str):
                    user_input = ""

                user_input = user_input.strip()

                if not user_input:
                    self.set_state.emit("idle")
                    time.sleep(0.3)
                    continue

                print(f"[User]: {user_input}")

                # 1) deterministic direct routing first
                direct = handle_direct_command(user_input)

                if direct:
                    _, tool_name, args = direct
                    print(f"[Direct Tool Route]: {tool_name} {args}")

                    self.set_state.emit("speaking")
                    IS_SPEAKING = True

                    confirmation = TOOL_CONFIRMATIONS.get(tool_name)
                    if confirmation:
                        speak(confirmation)

                    result = TOOLS[tool_name](**args)

                    if result:
                        speak(str(result))

                    time.sleep(0.4)
                    IS_SPEAKING = False
                    self.set_state.emit("idle")
                    time.sleep(0.3)
                    continue

                # 2) otherwise ask the LLM
                self.set_state.emit("thinking")
                response = call_llm(SYSTEM_PROMPT + "\nUser: " + user_input)

                if not isinstance(response, str):
                    response = str(response)

                print(f"[Lyra]: {response[:200]}")

                data = extract_json(response)
                print("[Parsed JSON]:", data)

                self.set_state.emit("speaking")
                IS_SPEAKING = True

                if isinstance(data, dict) and "tool" in data:
                    tool_name = data.get("tool")
                    args = data.get("args", {})

                    if not isinstance(args, dict):
                        args = {}

                    if tool_name in TOOLS:
                        confirmation = TOOL_CONFIRMATIONS.get(tool_name)

                        if confirmation:
                            speak(confirmation)

                        result = TOOLS[tool_name](**args)

                        if result:
                            speak(str(result))
                    else:
                        speak("I don't recognize that tool.")
                else:
                    speak(response)

                time.sleep(0.4)
                IS_SPEAKING = False
                self.set_state.emit("idle")
                time.sleep(0.3)

            except Exception as e:
                print("Error:", e)
                IS_SPEAKING = False
                self.set_state.emit("idle")
                speak("Something went wrong.")
                time.sleep(0.5)


class AvatarWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(180, 180)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 220, screen.height() - 220)

        self.label = QLabel(self)
        self.label.resize(180, 180)

        self.movie = QMovie()
        self.label.setMovie(self.movie)

        self.set_state("idle")

        self.worker = AssistantWorker()
        self.worker.set_state.connect(self.set_state)
        self.worker.start()

    def set_state(self, state):
        path = os.path.join(ROOT, "ui", "assets")
        gifs = {
            "idle": "lyra.gif",
            "listening": "AI.gif",
            "thinking": "AI.gif",
            "speaking": "lyra.gif",
        }

        gif_path = os.path.join(path, gifs.get(state, "lyra.gif"))

        if os.path.exists(gif_path):
            self.movie.setFileName(gif_path)
            self.movie.start()
        else:
            print(f"Missing: {gif_path}")

    def show_avatar(self):
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AvatarWindow()
    window.show_avatar()
    print("🚀 Lyra is running...")
    sys.exit(app.exec())