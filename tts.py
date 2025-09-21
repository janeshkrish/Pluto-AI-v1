# tts.py
import pyttsx3
import threading
import platform
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Global SocketIO instance ---
# This will be set by the main app.py file
socketio_instance = None

def set_socketio_instance(sio):
    """Allows the main app to share its SocketIO instance with this module."""
    global socketio_instance
    socketio_instance = sio
    print("SocketIO instance set in TTS module")

class EnhancedTTS:
    """Enhanced Text-to-Speech engine with Tamil/English support"""
    
    def __init__(self):
        self.engine = None
        self.lock = threading.Lock()
        self.voice_map = {"en": None, "ta": None}
        self.initialize_engine()

    def initialize_engine(self):
        """Initialize TTS engine with error handling."""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            
            # Find English and Tamil voices
            for voice in voices:
                voice_name = voice.name.lower()
                if 'english' in voice_name or 'en' in voice.id.lower():
                    self.voice_map['en'] = voice.id
                if 'tamil' in voice_name or 'ta' in voice.id.lower():
                    self.voice_map['ta'] = voice.id
            
            # Fallback if specific voices aren't found
            if not self.voice_map['en'] and voices: 
                self.voice_map['en'] = voices[0].id
            if not self.voice_map['ta']: 
                self.voice_map['ta'] = self.voice_map['en']
            
            # Set default properties
            self.engine.setProperty('rate', 180)
            self.engine.setProperty('volume', 0.9)
            
            logger.info("TTS engine initialized successfully")
            logger.info(f"Available voices: EN={self.voice_map['en']}, TA={self.voice_map['ta']}")
            
        except Exception as e:
            logger.error(f"TTS initialization error: {e}")
            self.engine = None

    def speak(self, text: str, lang: str = "en", interrupt: bool = True):
        """Speak text and emit it to the frontend via SocketIO."""
        if not self.engine or not text or not text.strip():
            return
        
        with self.lock:
            try:
                # --- EMIT TO FRONTEND ---
                # If the socket instance is available, send the message to the UI
                if socketio_instance:
                    try:
                        socketio_instance.emit('log_message', {
                            'data': text, 
                            'type': 'ai',
                            'language': lang
                        })
                    except Exception as emit_error:
                        logger.warning(f"Failed to emit to frontend: {emit_error}")
                
                # Stop current speech if interrupting
                if interrupt:
                    self.engine.stop()
                
                # Set voice for the appropriate language
                voice_id = self.voice_map.get(lang, self.voice_map.get('en'))
                if voice_id:
                    self.engine.setProperty('voice', voice_id)
                
                # Adjust speech rate based on language
                rate = 160 if lang == 'ta' else 180
                self.engine.setProperty('rate', rate)
                
                # Log the speech
                lang_name = "TAMIL" if lang == 'ta' else "ENGLISH"
                logger.info(f"[PLUTO {lang_name}]: {text}")
                print(f"🔊 [PLUTO {lang_name}]: {text}")
                
                # Speak the text
                self.engine.say(text)
                self.engine.runAndWait()
                
            except Exception as e:
                logger.error(f"TTS speech error: {e}")
                # Try to reinitialize engine on error
                self.initialize_engine()

# Global TTS instance
tts_engine = EnhancedTTS()

def speak(text: str, lang: str = "en"):
    """Global speak function - Thread-safe speech synthesis."""
    if not text or not text.strip():
        return
    
    # Run TTS in a separate thread to avoid blocking
    def speak_async():
        try:
            tts_engine.speak(text, lang)
        except Exception as e:
            logger.error(f"Async speak error: {e}")
    
    # Start speech in background thread
    thread = threading.Thread(target=speak_async, daemon=True)
    thread.start()

def test_tts():
    """Test function for TTS functionality"""
    print("Testing TTS functionality...")
    
    # Test English
    speak("Hello, this is a test of the English text to speech system.", "en")
    
    # Test Tamil (romanized)
    speak("Vanakkam, idhu Tamil text to speech system test.", "ta")
    
    print("TTS test completed!")

# Initialize on module import
if __name__ == "__main__":
    test_tts()
