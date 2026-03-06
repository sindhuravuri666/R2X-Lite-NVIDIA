from brain.llm import call_llm
from actions.desktop import open_browser, get_time, open_notepad
import json
from perception.listner import listen
from perception.tts import speak
from perception.vision import capture_screen, analyze_screen

SYSTEM_PROMPT = """
You are a desktop AI assistant.

Always respond with **exactly one JSON object and nothing else** when you invoke a tool. Do not add any extra wording, punctuation, or newline characters before or after the JSON. The only allowed output from you when running a tool is the JSON object described below.

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

For any other question or conversational response, reply normally in plain text without using the tool format.
"""

def analyze_screen_tool():
    image = capture_screen()
    try:
        description = analyze_screen(image)
    except Exception as exc:
        # propagate as a string so handle_response can speak it
        return f"Failed to analyze screen: {exc}"
    return description

TOOLS = {
    "open_browser": open_browser,
    "get_time": get_time,
    "open_notepad": open_notepad,
    "analyze_screen": analyze_screen_tool
}

def handle_response(response):
    # print out the raw response for debugging; useful when things go wrong
    print(f"LLM returned: {repr(response)}")

    # try to parse the first JSON object in the response even if the model
    # emits extra text or newlines. This makes the system more robust when
    # the LLM returns salutations or trailing comments.
    try:
        data = json.loads(response)
    except json.JSONDecodeError as e:
        # attempt to salvage JSON from the response
        try:
            # strip leading/trailing whitespace and take last line
            candidate = response.strip().splitlines()[-1]
            data = json.loads(candidate)
        except Exception:
            # still can't parse; report error with repr to expose hidden chars
            speak(f"Error processing response: {e}\nResponse was: {repr(response)}")
            return

    tool_name = data.get("tool")
    args = data.get("args", {})

    if tool_name in TOOLS:
        try:
            result = TOOLS[tool_name](**args)
        except Exception as err:
            speak(f"Error executing tool '{tool_name}': {err}")
            return
        speak(result)
    else:
        # if there is no tool or it's unrecognized, just speak the raw text
        speak(response)




def main():
    while True:
        user_input = listen()

        full_prompt = SYSTEM_PROMPT + "\nUser: " + user_input
        response = call_llm(full_prompt)

        handle_response(response)

        follow_up = input("Do you want anything else? (yes/no): ")

        if follow_up.lower() != "yes":
            speak("Okay, stopping now.")
            break


if __name__ == "__main__":
    main()