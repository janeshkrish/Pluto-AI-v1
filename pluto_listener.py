# pluto_listener.py - SIMPLIFIED FOR BETTER ACCURACY
import speech_recognition as sr
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple recognizer setup
r = sr.Recognizer()
r.energy_threshold = 3000  # Higher threshold for cleaner input
r.dynamic_energy_threshold = False
r.pause_threshold = 1.2
r.operation_timeout = None

def calibrate_microphone():
    """Simple calibration"""
    print("Calibrating microphone... Please stay quiet for 2 seconds.")
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=2)
            logger.info(f"Calibration complete. Energy threshold: {r.energy_threshold:.2f}")
    except Exception as e:
        logger.error(f"Calibration error: {e}")
        r.energy_threshold = 3000

# Calibrate on startup
calibrate_microphone()

def is_tamil_text(text: str) -> bool:
    """Simple Tamil detection"""
    if not text:
        return False
    
    tamil_words = [
        'thorakku', 'thoraku', 'muddu', 'mudu', 'pannu', 'podu',
        'vanakkam', 'sollunga', 'kekkala', 'kandupidikka', 'mudiyala'
    ]
    
    text_lower = text.lower()
    return any(word in text_lower for word in tamil_words)

def listen_once(timeout=10, phrase_time_limit=8):
    """Simplified, accurate speech recognition"""
    try:
        with sr.Microphone() as source:
            logger.info("Listening... (Say 'open chrome', 'notepad thorakku', etc.)")
            
            # Listen with timeout
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            # Use Google Speech Recognition (most accurate for English)
            try:
                # Try English first
                text = r.recognize_google(audio, language='en-US')
                if text and len(text.strip()) > 1:
                    text_clean = text.strip()
                    
                    # Detect if it contains Tamil words
                    if is_tamil_text(text_clean):
                        lang = "ta"
                        logger.info(f"✅ Tamil detected: '{text_clean}'")
                    else:
                        lang = "en"
                        logger.info(f"✅ English: '{text_clean}'")
                    
                    return text_clean, lang
                    
            except sr.UnknownValueError:
                logger.info("🔇 Could not understand audio")
                return "", "en"
            except sr.RequestError as e:
                logger.error(f"❌ Google Speech API error: {e}")
                return "", "en"
                
    except sr.WaitTimeoutError:
        return "", "en"
    except Exception as e:
        logger.error(f"❌ Listen error: {e}")
        return "", "en"

if __name__ == "__main__":
    print("Testing simplified speech recognition...")
    print("Try saying:")
    print("  - 'open chrome'")
    print("  - 'notepad thorakku'") 
    print("  - 'spotify muddu'")
    print("  - 'open youtube'")
    print("Say 'quit' to stop...")
    
    while True:
        text, lang = listen_once(timeout=8, phrase_time_limit=6)
        if text:
            lang_name = "Tamil" if lang == "ta" else "English"
            print(f"🎤 You said: '{text}' [{lang_name}]")
            if "quit" in text.lower():
                print("Testing stopped!")
                break
        time.sleep(0.5)
