import sys
import os
import json
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

print("[R2X] Loading Whisper model...")
from perception.listner import listen
print("[R2X] Whisper ready!")

from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from brain.llm import call_llm
from actions.desktop import open_browser, get_time, open_notepad
from perception.tts import speak
from perception.vision import capture_screen, analyze_screen

print("[R2X] All modules ready!")

SYSTEM_PROMPT = """You are R2X, a desktop AI assistant.

RULES:
- For tool actions, respond with ONLY a JSON object. No extra words, no explanation.
- For normal conversation, respond with plain text only. No JSON.

TOOLS (respond with ONLY the JSON shown):

Open a website:
{"tool": "open_browser", "args": {"url": "URL_HERE"}}

Search YouTube:
{"tool": "open_browser", "args": {"url": "https://www.youtube.com/results?search_query=QUERY_HERE"}}

Get current time:
{"tool": "get_time", "args": {}}

Open Notepad:
{"tool": "open_notepad", "args": {}}

Analyze screen:
{"tool": "analyze_screen", "args": {}}

EXAMPLES:
User: open youtube
{"tool": "open_browser", "args": {"url": "https://www.youtube.com"}}

User: what time is it
{"tool": "get_time", "args": {}}

User: search cats on youtube
{"tool": "open_browser", "args": {"url": "https://www.youtube.com/results?search_query=cats"}}

User: hello
Hello! How can I help you today?
"""

TOOLS = {
    "open_browser":   open_browser,
    "get_time":       get_time,
    "open_notepad":   open_notepad,
    "analyze_screen": lambda: analyze_screen(capture_screen()),
}

TOOL_CONFIRMATIONS = {
    "open_browser":   "Opening browser now.",
    "get_time":       None,
    "open_notepad":   "Opening Notepad.",
    "analyze_screen": "Analyzing your screen, please wait.",
}

def extract_json(text):
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    try:
        match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None


class AssistantWorker(QThread):
    set_state = pyqtSignal(str)
    done      = pyqtSignal()

    def run(self):
        try:
            # 1. LISTEN
            self.set_state.emit("listening")
            user_input = listen()
            print(f"You said: {user_input}")

            if not user_input.strip():
                self.done.emit()
                return

            # 2. THINK
            self.set_state.emit("thinking")
            response = call_llm(SYSTEM_PROMPT + "\nUser: " + user_input)
            print(f"AI: {response[:120]}")

            # 3. SPEAK — happens here in the worker, BEFORE done is emitted
            #    This means the mic is closed and the next cycle cannot start
            #    until speaking is fully finished.
            self.set_state.emit("speaking")
            data = extract_json(response)
            if data and "tool" in data:
                tool_name = data.get("tool")
                args      = data.get("args", {})
                if tool_name in TOOLS:
                    confirmation = TOOL_CONFIRMATIONS.get(tool_name)
                    if confirmation:
                        speak(confirmation)
                    result = TOOLS[tool_name](**args)
                    if confirmation is None and result:
                        speak(str(result))
                else:
                    speak(response)
            else:
                speak(response)

            self.set_state.emit("idle")

        except Exception as e:
            print(f"Worker error: {e}")
            speak("Sorry, something went wrong.")

        finally:
            # 4. Only NOW signal done — next cycle starts after speaking ends
            self.done.emit()


class AvatarWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.resize(150, 150)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 180, screen.height() - 180)

        print("✅ Avatar window initialized")

        self.label = QLabel(self)
        path = os.path.join(ROOT, "ui", "assets", "avatar.jpg")
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print("❌ Image failed to load")
        else:
            print("✅ Image loaded")

        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)
        self.label.resize(150, 150)

        self._worker = None
        self._busy   = False

        QTimer.singleShot(1000, self._start_cycle)

    def set_state(self, state):
        if state == "listening":
            self.setStyleSheet("border: 4px solid #00BFFF; border-radius: 75px; background: transparent;")
        elif state == "thinking":
            self.setStyleSheet("border: 4px solid #8A2BE2; border-radius: 75px; background: transparent;")
        elif state == "speaking":
            self.setStyleSheet("border: 4px solid #32CD32; border-radius: 75px; background: transparent;")
        else:
            self.setStyleSheet("border: none; background: transparent;")

    def _start_cycle(self):
        if self._busy:
            return
        self._busy   = True
        self._worker = AssistantWorker()
        self._worker.set_state.connect(self.set_state)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _on_done(self):
        self._busy = False
        # 1 second pause after speaking before listening again
        # so the mic doesn't catch the tail end of TTS audio
        QTimer.singleShot(1000, self._start_cycle)

    def show_avatar(self):
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AvatarWindow()
    window.show_avatar()
    print("🚀 Avatar running — look bottom-right of screen")
    sys.exit(app.exec())