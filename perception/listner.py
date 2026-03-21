import sounddevice as sd
import numpy as np
import queue
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    q.put(indata.copy())

def listen():
    # some terminals on Windows can't print the microphone emoji; fall back if
    # a UnicodeEncodeError occurs
    try:
        print("🎤 Listening... Speak now.")
    except UnicodeEncodeError:
        print("Listening... Speak now.")

    with sd.InputStream(samplerate=16000, channels=1, callback=audio_callback):
        audio_data = []
        for _ in range(200):
            audio_data.append(q.get())
        while not q.empty():
            audio_data.append(q.get())

    audio_np = np.concatenate(audio_data, axis=0)
    if audio_np.ndim > 1:
        audio_np = audio_np.ravel()
    audio_np = audio_np.astype(np.float32)

    segments, _ = model.transcribe(audio_np, beam_size=5)

    text = ""
    for segment in segments:
        text += segment.text

    print(f"You said: {text.strip()}")
    return text.strip()