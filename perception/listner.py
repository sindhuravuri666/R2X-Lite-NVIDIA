import sounddevice as sd
import numpy as np
import queue
from faster_whisper import WhisperModel

q = queue.Queue()
model = None


def get_model():
    global model
    if model is None:
        print("[Lyra] Initializing Whisper...")
        model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8",# flloat16, int8, int4
            cpu_threads=2,
            num_workers=1
        )
        print("[Lyra] Whisper ready!")
    return model


def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(indata.copy())


def clear_queue():
    while not q.empty():
        q.get()


def listen():
    model = get_model()
    clear_queue()

    try:
        print("🎤 Listening...")
    except UnicodeEncodeError:
        print("Listening...")

    audio_data = []

    with sd.InputStream(samplerate=16000, channels=1, callback=audio_callback):
        for _ in range(80):   # around a few seconds depending on block size
            audio_data.append(q.get())

    while not q.empty():
        audio_data.append(q.get())

    if not audio_data:
        return ""

    audio_np = np.concatenate(audio_data, axis=0).astype(np.float32).flatten()

    segments, _ = model.transcribe(
        audio_np,
        beam_size=1,
        vad_filter=True
    )

    text = " ".join(seg.text for seg in segments).strip()
    print(f"[Heard]: {text}")
    return text