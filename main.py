from brain.llm import call_llm
from actions.desktop import open_browser, get_time, open_notepad
import json
from perception.listner import listen
from perception.tts import speak

SYSTEM_PROMPT = """
You are a desktop AI assistant.

If the user asks to open a website, return JSON:
{"tool": "open_browser", "args": {"url": "https://example.com"}}

If the user asks to search on YouTube, return JSON:
{"tool": "open_browser", "args": {"query": srearch_query}}

If the user asks for time:
{"tool": "get_time", "args": {}}

If the user asks to open notepad:
{"tool": "open_notepad", "args": {}}

Otherwise respond normally in text.
"""

TOOLS = {
    "open_browser": open_browser,
    "get_time": get_time,
    "open_notepad": open_notepad
}

def handle_response(response):
    try:
        data = json.loads(response)
        tool_name = data["tool"]
        args = data["args"]

        if tool_name in TOOLS:
            confirmation = input(f"⚠️ Execute {tool_name} with {args}? (yes/no): ")

            if confirmation.lower() == "yes":
                result = TOOLS[tool_name](**args)
                speak(f"{result}")
            else:
                speak("Okay, I will not execute that.")

        else:
            speak(response)

    except:
        speak(response)

while True:
    user_input = listen()

    full_prompt = SYSTEM_PROMPT + "\nUser: " + user_input
    response = call_llm(full_prompt)

    handle_response(response)