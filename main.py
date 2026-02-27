while True:
    text = listen()

    if needs_screen_context(text):
        screen_info = capture_screen()
    else:
        screen_info = None

    response = llm_process(text, screen_info)

    if response.contains_tool:
        execute_tool(response.tool)

    speak(response.text)
    update_avatar_state()