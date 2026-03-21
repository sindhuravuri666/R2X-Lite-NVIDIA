print("testing whisper...")
from faster_whisper import WhisperModel
print("faster_whisper imported")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("model loaded OK")