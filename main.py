from brain.llm import call_llm
from actions.desktop import open_browser, get_time, open_notepad
import json
from perception.listner import listen
from perception.tts import speak
from perception.vision import capture_screen, analyze_screen

SYSTEM_PROMPT = """
You are a desktop AI assistant..

If the user asks to open a website, return JSON:
{"tool": "open_browser", "args": {"url": "https://example.com"}}

If the user asks to search on YouTube, return JSON:
{"tool": "open_browser", "args": {"query": srearch_query}}

If the user asks for time:
{"tool": "get_time", "args": {}}

If the user asks to open notepad:
{"tool": "open_notepad", "args": {}}

If the user asks about the screen or what is visible,
respond with:
{"tool": "analyze_screen", "args": {}}

Otherwise respond normally in text.
"""

def analyze_screen_tool():
    image = capture_screen()
    description = analyze_screen(image)
    return description

TOOLS = {
    "open_browser": open_browser,
    "get_time": get_time,
    "open_notepad": open_notepad,
    "analyze_screen": analyze_screen_tool
}

def handle_response(response):
    try:
        data = json.loads(response)
        tool_name = data["tool"]
        args = data["args"]

        if tool_name in TOOLS:
            result = TOOLS[tool_name](**args)
            speak(result)
        else:
            speak(response)

    except Exception as e:
        speak(f"Error processing response: {e}" + "\nResponse was: " + response)

while True:
    user_input = listen()

    full_prompt = SYSTEM_PROMPT + "\nUser: " + user_input
    response = call_llm(full_prompt)

    handle_response(response)

    follow_up = input("Do you want anything else? (yes/no): ")

    if follow_up.lower() != "yes":
        speak("Okay, stopping now.")
        break