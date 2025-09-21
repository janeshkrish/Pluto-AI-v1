# app.py - ENHANCED WITH WAKE WORD DETECTION
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
import re

# Import enhanced modules
try:
    from pluto_listener import listen_once
    print("✅ Using enhanced pluto_listener")
except ImportError:
    print("❌ Failed to import pluto_listener")

try:
    from command import get_ai_intent, execute_command, get_system_status
    print("✅ Successfully imported enhanced command module")
except ImportError as e:
    print(f"❌ Command import error: {e}")

try:
    from tts import speak, set_socketio_instance
    print("✅ Successfully imported TTS functions")
except ImportError as e:
    print(f"❌ TTS import error: {e}")
    def speak(text, lang="en"):
        print(f"[TTS FAILED] {text}")
    def set_socketio_instance(sio):
        pass

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pluto_enhanced_2025'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Share SocketIO with TTS
try:
    set_socketio_instance(socketio)
    print("✅ SocketIO shared with TTS")
except Exception as e:
    print(f"❌ SocketIO setup failed: {e}")

class AppState:
    def __init__(self):
        self.is_listening = True
        self.current_lang = "en"
        # Enhanced wake words with Tamil support [web:104][web:106]
        self.wake_words = [
            "pluto", "ghost", "hey pluto", "hey ghost",
            "pluto anna", "ghost anna"  # Tamil respectful address
        ]
        self.wake_word_detected = False

state = AppState()

def detect_wake_word(text: str) -> bool:
    """Enhanced wake word detection with Tamil support [web:104][web:106]"""
    if not text:
        return False
    
    text_lower = text.lower().strip()
    
    # Direct wake word matching
    for wake_word in state.wake_words:
        if wake_word in text_lower:
            return True
    
    # Fuzzy matching for speech recognition errors
    fuzzy_patterns = [
        r'\b(pluto|bluto|puto)\b',
        r'\b(ghost|gost|goast)\b',
        r'\bhey\s+(pluto|ghost)\b'
    ]
    
    for pattern in fuzzy_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False

def is_direct_command(text: str) -> bool:
    """Check if text is a direct command without wake word"""
    if not text:
        return False
    
    command_patterns = [
        r'\bopen\s+\w+',
        r'\bclose\s+\w+',
        r'\bsearch\s+',
        r'\w+\s+thorakku',  # Tamil: app_name + open
        r'\w+\s+muddu',     # Tamil: app_name + close
        r'\w+\s+pannu'      # Tamil: app_name + do/open
    ]
    
    text_lower = text.lower()
    for pattern in command_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False

def continuous_listener():
    """Enhanced listener with wake word detection [web:104][web:106]"""
    print("🎙️  Starting wake-word enabled listener...")
    
    # Display system status
    try:
        status = get_system_status()
        print(f"🤖 System: {status['connectivity']}")
        print(f"📱 Models: {status['available_models']}")
        print(f"🔧 Manual Apps: {status['manual_apps']}")
        print(f"🌐 Web Apps: {status['web_apps']}")
        
        socketio.emit('log_message', {
            'data': f"Enhanced system ready | Manual: {status['manual_apps']} | Web: {status['web_apps']} | Models: {len(status['available_models'])}", 
            'type': 'system'
        })
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    consecutive_failures = 0
    max_failures = 5
    
    while state.is_listening:
        try:
            socketio.emit('status_update', {'data': 'Listening for wake word or command...'})
            
            # Listen with shorter timeout for responsiveness
            text, detected_lang = listen_once(timeout=3, phrase_time_limit=6)
            
            if not text:
                consecutive_failures += 1
                if consecutive_failures > max_failures:
                    print("⚠️  Multiple listen failures, brief pause...")
                    time.sleep(2)
                    consecutive_failures = 0
                continue
            
            # Reset failure counter on successful recognition
            consecutive_failures = 0
            
            text_clean = text.strip()
            print(f"🎤 Heard: '{text_clean}' [{detected_lang}]")
            
            # Update language
            if detected_lang and detected_lang.startswith('ta'):
                state.current_lang = "ta"
            else:
                state.current_lang = "en"
            
            # Check for wake word [web:104][web:106]
            wake_word_found = detect_wake_word(text_clean)
            direct_command = is_direct_command(text_clean)
            
            if wake_word_found:
                print("🎯 Wake word detected!")
                socketio.emit('log_message', {
                    'data': f'Wake word: {text_clean}', 
                    'type': 'user',
                    'language': state.current_lang
                })
                socketio.emit('status_update', {'data': '🎯 Wake word detected! Listening for command...'})
                
                # Acknowledge wake word
                responses = {
                    "en": "Yes, how can I help?",
                    "ta": "Sollunga, enna help venum?"
                }
                speak(responses[state.current_lang], state.current_lang)
                
                # Listen for actual command with longer timeout
                command_text, cmd_lang = listen_once(timeout=8, phrase_time_limit=10)
                
                if command_text and len(command_text.strip()) > 2:
                    if cmd_lang and cmd_lang.startswith('ta'):
                        state.current_lang = "ta"
                    handle_command(command_text, state.current_lang)
                else:
                    no_command_responses = {
                        "en": "I didn't hear a command",
                        "ta": "Command kekkala"
                    }
                    speak(no_command_responses[state.current_lang], state.current_lang)
                    
            elif direct_command:
                print("⚡ Direct command detected!")
                socketio.emit('log_message', {
                    'data': f'Direct command: {text_clean}', 
                    'type': 'user',
                    'language': state.current_lang
                })
                handle_command(text_clean, state.current_lang)
            
            else:
                print(f"🔇 No wake word or command pattern: '{text_clean}'")
            
            time.sleep(0.2)  # Brief pause between listens
            
        except Exception as e:
            print(f"❌ Listener error: {e}")
            socketio.emit('status_update', {'data': f'Listener error: {str(e)}'})
            time.sleep(1)

def handle_command(command_text: str, lang: str):
    """Enhanced command processing with better error handling"""
    try:
        command_clean = command_text.strip()
        
        if len(command_clean) < 2:
            return
        
        socketio.emit('log_message', {
            'data': command_clean, 
            'type': 'user',
            'language': lang
        })
        socketio.emit('status_update', {'data': '🤖 Processing with AI...'})
        
        print(f"🤖 Processing: '{command_clean}' [{lang}]")
        
        # Get AI intent
        intent = get_ai_intent(command_clean)
        print(f"📝 Intent: {intent}")
        
        # Validate intent structure
        if not isinstance(intent, dict) or 'tool' not in intent:
            print("❌ Invalid intent structure")
            error_responses = {
                "en": "Sorry, I didn't understand that command",
                "ta": "Command puriyala, marupadiyum sollunga"
            }
            speak(error_responses[lang], lang)
            return
        
        # Execute command
        execute_command(intent, lang)
        socketio.emit('status_update', {'data': '✅ Command completed'})
        print("✅ Command executed")
        
    except Exception as e:
        print(f"❌ Command handling error: {e}")
        error_responses = {
            "en": "Sorry, I had an error processing that",
            "ta": "Error aachu, mannichanga"
        }
        speak(error_responses[lang], lang)
        socketio.emit('status_update', {'data': f'❌ Error: {str(e)}'})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('🌐 Client connected')
    emit('log_message', {
        'data': 'Pluto Enhanced Voice Assistant with Wake Word Detection is online!', 
        'type': 'ai'
    })
    emit('status_update', {'data': '✅ Ready - Say "Pluto" or "Ghost" to activate'})
    
    # Start listener if not already running
    if not hasattr(handle_connect, 'listener_started'):
        threading.Thread(target=continuous_listener, daemon=True).start()
        handle_connect.listener_started = True

@socketio.on('user_message')
def on_user_message(data):
    """Handle typed messages from web interface"""
    command_text = data.get('data', '')
    if command_text:
        print(f"💬 Web message: {command_text}")
        handle_command(command_text, state.current_lang)

@socketio.on('toggle_listening')
def toggle_listening():
    """Toggle listening state"""
    state.is_listening = not state.is_listening
    status = "🎙️  Listening enabled" if state.is_listening else "🔇 Listening paused"
    emit('status_update', {'data': status})
    print(status)

@socketio.on('change_language')
def change_language(data):
    """Change system language"""
    new_lang = data.get('language', 'en')
    if new_lang in ['en', 'ta']:
        state.current_lang = new_lang
        lang_names = {'en': 'English', 'ta': 'Tamil'}
        emit('status_update', {'data': f'🌐 Language: {lang_names[new_lang]}'})
        print(f"Language: {lang_names[new_lang]}")

@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 Client disconnected')

if __name__ == '__main__':
    print("🚀 Starting Pluto Enhanced with Wake Word Detection...")
    print("📱 Web Interface: http://localhost:5000")
    print("🎙️  Wake Words: 'Pluto', 'Ghost', 'Hey Pluto'")
    print("💬 Direct Commands: 'open chrome', 'notepad thorakku'")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
