import sys, os, traceback
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

print("step 1: PyQt6")
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
print("step 2: brain.llm")
from brain.llm import call_llm
print("step 3: actions.desktop")
from actions.desktop import open_browser, get_time, open_notepad
print("step 4: listner")
from perception.listner import listen
print("step 5: tts")
from perception.tts import speak
print("step 6: vision")
from perception.vision import capture_screen, analyze_screen
print("ALL OK")