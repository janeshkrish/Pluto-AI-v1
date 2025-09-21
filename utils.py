
# utils.py
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 155)
engine.setProperty('volume', 1.0)

def speak(text):
    if not text or not str(text).strip():
        return
    print(f"[Pluto] {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error] {e}")
