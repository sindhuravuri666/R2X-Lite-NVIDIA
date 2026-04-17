import pyttsx3

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 170)
    return _engine

def speak(text):
    if not text:
        return

    print("AI:", text)

    engine = _get_engine()
    engine.stop()  # clears any queued old speech
    engine.say(str(text))
    engine.runAndWait()