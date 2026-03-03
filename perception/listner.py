import sounddevice as sd
import numpy as np
import queue
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    q.put(indata.copy())

def listen():
    print("🎤 Listening... Speak now.")

    with sd.InputStream(samplerate=16000, channels=1, callback=audio_callback):
        audio_data = []
        for _ in range(200): 
            #
            audio_data.append(q.get())

    # stack frames and ensure a 1‑D array; Whisper expects a flat waveform
    audio_np = np.concatenate(audio_data, axis=0)
    if audio_np.ndim > 1:
        audio_np = audio_np.ravel()

    # convert to float32 explicitly (audio device may provide float64)
    audio_np = audio_np.astype(np.float32)

    segments, _ = model.transcribe(audio_np, beam_size=5)

    text = ""
    for segment in segments:
        text += segment.text

    print(f"You said: {text.strip()}")
    return text.strip()