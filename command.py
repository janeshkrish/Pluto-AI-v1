# command.py - ENHANCED WITH MEDIA CONTROL & CLIPBOARD AUTOMATION
import os
import re
import subprocess
import json
import webbrowser
import time
import winreg
from pathlib import Path
from typing import Dict, Optional, List
import socket
import requests
from datetime import datetime
import hashlib
import urllib.parse
import pyperclip  # For clipboard operations [web:150][web:156]
import pyautogui  # For automation [web:155][web:157]
from tts import speak

# Install required packages if not present
try:
    import pyperclip
    import pyautogui
except ImportError:
    print("Installing required packages...")
    os.system("pip install pyperclip pyautogui")
    import pyperclip
    import pyautogui

# --- Configuration ---
class AIConfig:
    TASK_MODELS = {
        "fast": "phi3:mini",
        "deep": "llama3:instruct",  
        "reasoning": "mistral:latest"
    }
    
    MODEL_FALLBACK = ["phi3:mini", "llama3:instruct", "mistral:latest"]
    CACHE_DURATION = 300
    MAX_CACHE_SIZE = 100
    FAST_TIMEOUT = 15
    NORMAL_TIMEOUT = 30
    REASONING_TIMEOUT = 45
    INTERNET_TIMEOUT = 5
    
    def __init__(self):
        self.response_cache = {}
        self.model_health = {}
        self.last_connectivity_check = 0
        self.is_online = False
        # Store last generated code for clipboard operations
        self.last_generated_code = ""
        
    def get_timeout_for_model(self, model: str) -> int:
        if "phi3" in model:
            return self.FAST_TIMEOUT
        elif "mistral" in model:
            return self.REASONING_TIMEOUT
        else:
            return self.NORMAL_TIMEOUT
        
    def check_model_availability(self, model: str) -> bool:
        try:
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, text=True, timeout=10
            )
            return model in result.stdout
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        available = []
        for model in self.MODEL_FALLBACK:
            if self.check_model_availability(model):
                available.append(model)
        return available

    def select_model_for_task(self, query: str, task_type: str = None) -> str:
        query_lower = query.lower()
        
        if task_type and task_type in self.TASK_MODELS:
            preferred_model = self.TASK_MODELS[task_type]
            if self.check_model_availability(preferred_model):
                return preferred_model
        
        fast_keywords = [
            "open", "close", "start", "stop", "launch", "quit", "exit",
            "play", "pause", "skip", "next", "previous", "volume",
            "shutdown", "restart", "sleep", "hibernate", "copy", "paste",
            "thorakku", "muddu", "pannu", "podu", "kelu", "ninruthu",
            "hello", "hi", "vanakkam", "thanks", "bye"
        ]
        
        deep_keywords = [
            "explain", "what is", "who is", "where is", "when did", "how does",
            "definition", "meaning", "history", "biography", "facts about",
            "tell me about", "describe", "overview", "summary", "information"
        ]
        
        reasoning_keywords = [
            "solve", "calculate", "compute", "analyze", "compare", "evaluate",
            "problem", "puzzle", "logic", "reasoning", "algorithm", "code",
            "generate code", "write code", "create program", "debug", "programming"
        ]
        
        fast_score = sum(1 for keyword in fast_keywords if keyword in query_lower)
        deep_score = sum(1 for keyword in deep_keywords if keyword in query_lower)
        reasoning_score = sum(1 for keyword in reasoning_keywords if keyword in query_lower)
        
        if reasoning_score > max(fast_score, deep_score):
            preferred_model = self.TASK_MODELS["reasoning"]
        elif deep_score > fast_score:
            preferred_model = self.TASK_MODELS["deep"] 
        else:
            preferred_model = self.TASK_MODELS["fast"]
        
        if self.check_model_availability(preferred_model):
            return preferred_model
        
        available_models = self.get_available_models()
        return available_models[0] if available_models else "phi3:mini"

ai_config = AIConfig()

def get_language_name(lang_code):
    language_map = {"en": "English", "ta": "Tamil"}
    return language_map.get(lang_code, "English")

def get_cache_key(prompt: str, model: str) -> str:
    return hashlib.md5(f"{prompt}:{model}".encode()).hexdigest()

def check_internet_connection() -> bool:
    current_time = time.time()
    if current_time - ai_config.last_connectivity_check < 30:
        return ai_config.is_online
    
    try:
        endpoints = [("www.google.com", 80), ("8.8.8.8", 53)]
        for host, port in endpoints:
            try:
                socket.create_connection((host, port), timeout=5)
                ai_config.is_online = True
                ai_config.last_connectivity_check = current_time
                return True
            except:
                continue
        ai_config.is_online = False
        return False
    except:
        ai_config.is_online = False
        return False

# --- Enhanced App Discovery with Media Control ---
class MediaControlAppDiscovery:
    def __init__(self):
        self.installed_apps = {}
        self.process_map = {}
        self.manual_app_paths = {}
        self.web_apps = {}
        self.system_commands = {}
        self.media_platforms = {}
        self.refresh_apps()
        self.setup_manual_mappings()
        self.setup_web_apps()
        self.setup_system_commands()
        self.setup_media_platforms()

    def setup_manual_mappings(self):
        """Setup manual app path mappings"""
        try:
            username = os.getenv('USERNAME', 'User')
            
            app_search = {
                'chrome': [
                    f"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    f"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                    f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
                ],
                'firefox': [
                    f"C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                    f"C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
                ],
                'spotify': [
                    f"C:\\Users\\{username}\\AppData\\Roaming\\Spotify\\Spotify.exe",
                    f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\WindowsApps\\Spotify.exe"
                ],
                'whatsapp': [
                    f"C:\\Users\\{username}\\AppData\\Local\\WhatsApp\\WhatsApp.exe",
                    f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\WindowsApps\\WhatsApp.exe"
                ],
                'vscode': [
                    f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
                    f"C:\\Program Files\\Microsoft VS Code\\Code.exe"
                ],
                'notepad': ['notepad.exe'],
                'notepadplusplus': [
                    f"C:\\Program Files\\Notepad++\\notepad++.exe",
                    f"C:\\Program Files (x86)\\Notepad++\\notepad++.exe"
                ],
                'calculator': ['calc.exe'],
                'paint': ['mspaint.exe']
            }
            
            found_count = 0
            for app_name, paths in app_search.items():
                for path in paths:
                    if os.path.exists(path) or not path.startswith('C:'):
                        self.manual_app_paths[app_name] = path
                        found_count += 1
                        print(f"✅ Found {app_name}: {path}")
                        break
            
            print(f"✅ Manual mappings: {found_count} apps found")
            
        except Exception as e:
            print(f"❌ Manual mappings error: {e}")

    def setup_web_apps(self):
        """Setup web-based applications"""
        self.web_apps = {
            'youtube': 'https://www.youtube.com',
            'gmail': 'https://mail.google.com', 
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://www.twitter.com',
            'instagram': 'https://www.instagram.com',
            'netflix': 'https://www.netflix.com',
            'amazon': 'https://www.amazon.com',
            'github': 'https://www.github.com',
            'reddit': 'https://www.reddit.com'
        }
        print(f"✅ Web apps configured: {len(self.web_apps)} apps")

    def setup_system_commands(self):
        """Setup system control commands"""
        self.system_commands = {
            'shutdown': {
                'command': 'shutdown /s /t 5',
                'description': 'Shutdown computer in 5 seconds'
            },
            'restart': {
                'command': 'shutdown /r /t 5', 
                'description': 'Restart computer in 5 seconds'
            },
            'reboot': {
                'command': 'shutdown /r /t 5',
                'description': 'Reboot computer in 5 seconds'
            },
            'sleep': {
                'command': 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0',
                'description': 'Put computer to sleep'
            },
            'hibernate': {
                'command': 'shutdown /h',
                'description': 'Hibernate computer'
            },
            'logout': {
                'command': 'shutdown -l',
                'description': 'Log out current user'
            },
            'lock': {
                'command': 'rundll32.exe user32.dll,LockWorkStation',
                'description': 'Lock the workstation'
            }
        }
        print(f"✅ System commands configured: {len(self.system_commands)} commands")

    def setup_media_platforms(self):
        """Setup media platform URL patterns [web:133][web:137][web:139]"""
        self.media_platforms = {
            'youtube': {
                'base_url': 'https://www.youtube.com',
                'search_url': 'https://www.youtube.com/results?search_query={}',
                'play_url': 'https://www.youtube.com/results?search_query={}&autoplay=1',
                'app_launch': None  # Will open in browser
            },
            'spotify': {
                'base_url': 'https://open.spotify.com',
                'search_url': 'https://open.spotify.com/search/{}',
                'play_url': 'https://open.spotify.com/search/{}',
                'app_launch': 'spotify'  # Can launch desktop app
            },
            'soundcloud': {
                'base_url': 'https://soundcloud.com',
                'search_url': 'https://soundcloud.com/search?q={}',
                'play_url': 'https://soundcloud.com/search?q={}',
                'app_launch': None
            }
        }
        print(f"✅ Media platforms configured: {len(self.media_platforms)} platforms")

    def clean_app_name(self, name: str) -> str:
        name = re.sub(r'\s*\(.*?\)$', '', name).strip()
        name = re.sub(r'\s*(x64|64-bit|32-bit|build|version)[\s\d\.]*$', '', name, flags=re.IGNORECASE).strip()
        return name.lower()

    def scan_registry_apps(self) -> Dict[str, str]:
        apps = {}
        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        for path in registry_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        
                        try:
                            display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                            if display_icon.endswith('.exe'):
                                exe_path = display_icon.split(',')[0].strip('"')
                                if os.path.exists(exe_path):
                                    apps[self.clean_app_name(display_name)] = exe_path
                        except:
                            pass
                            
                        winreg.CloseKey(subkey)
                    except Exception: 
                        continue
                winreg.CloseKey(key)
            except Exception: 
                pass
        return apps

    def refresh_apps(self):
        print("Discovering apps with media control...")
        all_apps = {}
        all_apps.update(self.scan_registry_apps())
        self.installed_apps = all_apps
        self.build_process_map()
        print(f"Discovered {len(self.installed_apps)} apps from registry")

    def build_process_map(self):
        self.process_map = {
            'chrome': 'chrome.exe', 
            'firefox': 'firefox.exe', 
            'edge': 'msedge.exe', 
            'spotify': 'Spotify.exe', 
            'discord': 'Discord.exe', 
            'vscode': 'Code.exe', 
            'notepad': 'notepad.exe', 
            'notepadplusplus': 'notepad++.exe',
            'whatsapp': 'WhatsApp.exe',
            'calculator': 'Calculator.exe'
        }

    def find_app(self, app_name: str) -> Optional[str]:
        """Enhanced app finding with media platform support"""
        app_name_clean = self.clean_app_name(app_name)
        print(f"🔍 Searching for: '{app_name_clean}'")
        
        # Strategy 1: Check system commands
        if app_name_clean in self.system_commands:
            cmd_info = self.system_commands[app_name_clean]
            print(f"🔧 Found system command: {cmd_info['description']}")
            return f"system:{app_name_clean}"
        
        # Strategy 2: Check manual mappings
        if app_name_clean in self.manual_app_paths:
            path = self.manual_app_paths[app_name_clean]
            print(f"✅ Found in manual mappings: {path}")
            return path
        
        # Strategy 3: Check web apps
        if app_name_clean in self.web_apps:
            url = self.web_apps[app_name_clean]
            print(f"🌐 Found web app: {url}")
            return f"web:{url}"
        
        # Strategy 4: Check media platforms
        if app_name_clean in self.media_platforms:
            platform_info = self.media_platforms[app_name_clean]
            print(f"🎵 Found media platform: {platform_info['base_url']}")
            return f"media:{app_name_clean}"
        
        # Strategy 5: Check registry apps
        if app_name_clean in self.installed_apps:
            path = self.installed_apps[app_name_clean]
            if os.path.exists(path):
                print(f"✅ Found in registry: {path}")
                return path
        
        # Strategy 6: Partial matching
        for installed_app, path in self.installed_apps.items():
            if app_name_clean in installed_app and os.path.exists(path):
                print(f"✅ Found by partial match: {path}")
                return path
        
        print(f"❌ Not found: {app_name_clean}")
        return None

    def launch_app(self, app_path: str) -> bool:
        """Enhanced app launching with system and media support"""
        try:
            print(f"🚀 Launching: {app_path}")
            
            # System command execution
            if app_path.startswith("system:"):
                system_cmd = app_path[7:]  # Remove 'system:' prefix
                if system_cmd in self.system_commands:
                    cmd_info = self.system_commands[system_cmd]
                    command = cmd_info['command']
                    print(f"🔧 Executing system command: {command}")
                    
                    if system_cmd in ['shutdown', 'restart', 'reboot']:
                        print(f"⚠️  System will {system_cmd} in 5 seconds...")
                    
                    os.system(command)
                    return True
            
            # Web app launch
            elif app_path.startswith("web:"):
                url = app_path[4:]  # Remove 'web:' prefix
                print(f"🌐 Opening web app: {url}")
                webbrowser.open(url)
                return True
            
            # Media platform launch
            elif app_path.startswith("media:"):
                platform = app_path[6:]  # Remove 'media:' prefix
                if platform in self.media_platforms:
                    platform_info = self.media_platforms[platform]
                    
                    # Try to launch desktop app first if available
                    if platform_info['app_launch']:
                        desktop_path = self.find_app(platform_info['app_launch'])
                        if desktop_path and not desktop_path.startswith(('web:', 'media:', 'system:')):
                            print(f"🎵 Opening desktop {platform} app")
                            subprocess.Popen([desktop_path], shell=False)
                            return True
                    
                    # Fallback to web version
                    print(f"🌐 Opening web {platform}")
                    webbrowser.open(platform_info['base_url'])
                    return True
            
            # Executable launch
            elif app_path.endswith('.exe'):
                if os.path.exists(app_path):
                    subprocess.Popen([app_path], shell=False)
                    return True
                else:
                    subprocess.Popen([app_path], shell=True)
                    return True
            
            else:
                print(f"❌ Unknown app path type: {app_path}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to launch: {e}")
            return False

    def play_media(self, query: str, platform: str) -> bool:
        """Play media on specified platform [web:133][web:137]"""
        try:
            platform_clean = self.clean_app_name(platform)
            
            if platform_clean in self.media_platforms:
                platform_info = self.media_platforms[platform_clean]
                
                # URL encode the search query [web:133]
                encoded_query = urllib.parse.quote_plus(query.strip())
                
                # Try desktop app first for Spotify [web:137][web:139]
                if platform_clean == 'spotify' and platform_info['app_launch']:
                    desktop_path = self.find_app('spotify')
                    if desktop_path and not desktop_path.startswith(('web:', 'media:', 'system:')):
                        print(f"🎵 Opening Spotify desktop app for: {query}")
                        subprocess.Popen([desktop_path], shell=False)
                        time.sleep(3)  # Wait for app to load
                        
                        # Use Spotify web player as fallback with search
                        search_url = platform_info['search_url'].format(encoded_query)
                        webbrowser.open(search_url)
                        return True
                
                # Use web version with direct search [web:133]
                if platform_clean == 'youtube':
                    # YouTube search with auto-suggestion for first result
                    search_url = platform_info['search_url'].format(encoded_query)
                    print(f"🎬 Opening YouTube search: {search_url}")
                else:
                    # Other platforms
                    search_url = platform_info['play_url'].format(encoded_query)
                    print(f"🎵 Opening {platform} search: {search_url}")
                
                webbrowser.open(search_url)
                return True
            else:
                print(f"❌ Platform not supported: {platform}")
                return False
                
        except Exception as e:
            print(f"❌ Media play error: {e}")
            return False

# Initialize enhanced app discovery
app_discovery = MediaControlAppDiscovery()

# --- AI Functions ---
def query_ollama_smart(prompt: str, query: str = "", task_type: str = None) -> str:
    selected_model = ai_config.select_model_for_task(query or prompt, task_type)
    timeout = ai_config.get_timeout_for_model(selected_model)
    
    print(f"🤖 Using {selected_model} (timeout: {timeout}s)")
    
    try:
        result = subprocess.run(
            ["ollama", "run", selected_model, prompt],
            capture_output=True, text=True, encoding="utf-8", 
            errors="ignore", timeout=timeout
        )
        
        response = result.stdout.strip()
        if response and "Error:" not in response and len(response) > 10:
            print(f"✅ Success with {selected_model}")
            
            # Store generated code for clipboard operations
            if "def " in response or "import " in response or "class " in response:
                ai_config.last_generated_code = response
                print("💾 Code stored for clipboard operations")
            
            return response
    except subprocess.TimeoutExpired:
        print(f"⏰ {selected_model} timed out")
    except Exception as e:
        print(f"❌ {selected_model} failed: {e}")
    
    return "{\"tool\": \"general_chat\", \"parameters\": {\"query\": \"AI model failed.\"}}"

def get_ai_intent(text: str) -> dict:
    """Enhanced AI intent recognition with media control and clipboard operations"""
    prompt = f"""
You are a command interpreter for Tamil and English voice commands.
Classify this command into JSON with EXACT parameter names.

TOOLS AVAILABLE:
- open_app: Open applications, websites, or system functions
- close_app: Close running applications  
- search_web: Search Google for information
- system_control: System commands (shutdown, restart, sleep)
- play_media: Play music/videos on platforms (YouTube, Spotify)
- clipboard_action: Copy/paste operations with apps
- general_chat: Conversations and questions

RULES:
- For apps: {{"tool": "open_app", "parameters": {{"app_name": "APP_NAME"}}}}
- For system: {{"tool": "system_control", "parameters": {{"action": "ACTION"}}}}
- For media: {{"tool": "play_media", "parameters": {{"query": "SEARCH_TERM", "platform": "PLATFORM"}}}}
- For clipboard: {{"tool": "clipboard_action", "parameters": {{"action": "copy/paste", "target_app": "APP_NAME"}}}}
- For closing: {{"tool": "close_app", "parameters": {{"app_name": "APP_NAME"}}}}
- For web search: {{"tool": "search_web", "parameters": {{"query": "SEARCH_QUERY"}}}}
- For chat: {{"tool": "general_chat", "parameters": {{"query": "USER_MESSAGE"}}}}

EXAMPLES:
- "play coolie songs on youtube" -> {{"tool": "play_media", "parameters": {{"query": "coolie songs", "platform": "youtube"}}}}
- "coolie songs youtube la play pannu" -> {{"tool": "play_media", "parameters": {{"query": "coolie songs", "platform": "youtube"}}}}
- "play tamil music on spotify" -> {{"tool": "play_media", "parameters": {{"query": "tamil music", "platform": "spotify"}}}}
- "copy code and paste in vscode" -> {{"tool": "clipboard_action", "parameters": {{"action": "copy_paste", "target_app": "vscode"}}}}
- "paste code in notepad" -> {{"tool": "clipboard_action", "parameters": {{"action": "paste", "target_app": "notepad"}}}}
- "open chrome" -> {{"tool": "open_app", "parameters": {{"app_name": "chrome"}}}}
- "shutdown computer" -> {{"tool": "system_control", "parameters": {{"action": "shutdown"}}}}

Command: "{text}"
Return ONLY the JSON object:
"""
    
    try:
        response = query_ollama_smart(prompt, text, "fast")
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = response[start:end]
            parsed = json.loads(json_str)
            print(f"📝 Parsed intent: {parsed}")
            return parsed
        return handle_fallback(text)
    except Exception as e:
        print(f"❌ Intent parsing error: {e}")
        return handle_fallback(text)

def handle_fallback(text: str) -> dict:
    """Enhanced fallback with media and clipboard support"""
    text_lower = text.lower()
    
    # Media control patterns [web:133][web:137]
    if any(word in text_lower for word in ["play", "kelu", "pottu"]):
        # Check for platform mentions
        platform = "youtube"  # default
        if "spotify" in text_lower:
            platform = "spotify"
        elif "soundcloud" in text_lower:
            platform = "soundcloud"
        
        # Extract search query
        query = text_lower
        for word in ["play", "kelu", "pottu", "on", "in", "la", platform]:
            query = query.replace(word, "").strip()
        
        # Clean up common words
        for word in ["songs", "music", "video", "pattu", "paadal"]:
            pass  # Keep these as part of search
        
        return {"tool": "play_media", "parameters": {"query": query, "platform": platform}}
    
    # Clipboard operations [web:150][web:156]
    if any(word in text_lower for word in ["copy", "paste", "clipboard"]):
        action = "copy_paste"
        if "paste" in text_lower and "copy" not in text_lower:
            action = "paste"
        elif "copy" in text_lower and "paste" not in text_lower:
            action = "copy"
        
        # Extract target application
        target_app = "notepad"  # default
        if "vscode" in text_lower or "vs code" in text_lower:
            target_app = "vscode"
        elif "notepad++" in text_lower:
            target_app = "notepadplusplus"
        
        return {"tool": "clipboard_action", "parameters": {"action": action, "target_app": target_app}}
    
    # System control patterns
    if any(word in text_lower for word in [
        "shutdown", "shut down", "power off", "turn off",
        "restart", "reboot", "reset", "reopen",
        "sleep", "suspend", "hibernate", 
        "logout", "log out", "sign out", "lock"
    ]):
        if any(word in text_lower for word in ["shutdown", "shut down", "power off", "turn off"]):
            action = "shutdown"
        elif any(word in text_lower for word in ["restart", "reboot", "reset"]):
            action = "restart" 
        elif any(word in text_lower for word in ["sleep", "suspend"]):
            action = "sleep"
        elif any(word in text_lower for word in ["hibernate"]):
            action = "hibernate"
        elif any(word in text_lower for word in ["logout", "log out", "sign out"]):
            action = "logout"
        elif any(word in text_lower for word in ["lock"]):
            action = "lock"
        else:
            action = "shutdown"
            
        return {"tool": "system_control", "parameters": {"action": action}}
    
    # Opening patterns
    if any(word in text_lower for word in [
        "open", "launch", "start", "run",
        "thorakku", "thoraku", "pannu", "podu"
    ]):
        app_name = text_lower
        for word in ["open", "launch", "start", "run", "thorakku", "thoraku", "pannu", "podu"]:
            app_name = app_name.replace(word, "").strip()
        
        for word in ["the", "app", "application", "please", "computer", "system"]:
            app_name = app_name.replace(word, "").strip()
        
        return {"tool": "open_app", "parameters": {"app_name": app_name}}
    
    # Closing patterns
    if any(word in text_lower for word in [
        "close", "quit", "exit", "stop",
        "muddu", "mudu"
    ]):
        app_name = text_lower
        for word in ["close", "quit", "exit", "stop", "muddu", "mudu"]:
            app_name = app_name.replace(word, "").strip()
        return {"tool": "close_app", "parameters": {"app_name": app_name}}
    
    # Search patterns
    if any(word in text_lower for word in ["search", "find", "lookup", "thedi", "google"]):
        query = text_lower
        for word in ["search for", "search", "find", "lookup", "thedi", "google", "on google", "in google"]:
            query = query.replace(word, "").strip()
        return {"tool": "search_web", "parameters": {"query": query}}
    
    # Default to chat
    return {"tool": "general_chat", "parameters": {"query": text}}

# --- Enhanced Tool Functions ---
def open_app(app_name: str, lang: str = "en"):
    """Enhanced app opening with system support"""
    print(f"🚀 Opening: '{app_name}'")
    
    app_path = app_discovery.find_app(app_name)
    
    if not app_path:
        msg = f"I couldn't find {app_name}"
        if lang == "ta":
            msg = f"{app_name} kandupidikka mudiyala"
        speak(msg, lang)
        return
    
    success = app_discovery.launch_app(app_path)
    
    if success:
        if app_path.startswith("system:"):
            msg = f"Executing {app_name}"
            if lang == "ta":
                msg = f"{app_name} panren"
        else:
            msg = f"Opening {app_name}"
            if lang == "ta":
                msg = f"{app_name} thorakkuren"
        speak(msg, lang)
        print(f"✅ Success: {app_name}")
    else:
        msg = "Sorry, couldn't complete that action"
        if lang == "ta":
            msg = "Adhu panna mudiyala"
        speak(msg, lang)

def play_media(query: str, platform: str, lang: str = "en"):
    """Play media on specified platform [web:133][web:137]"""
    print(f"🎵 Playing '{query}' on {platform}")
    
    success = app_discovery.play_media(query, platform)
    
    if success:
        if platform.lower() == "youtube":
            msg = f"Playing {query} on YouTube"
            if lang == "ta":
                msg = f"{query} YouTube-la play panren"
        elif platform.lower() == "spotify":
            msg = f"Playing {query} on Spotify"
            if lang == "ta":
                msg = f"{query} Spotify-la kekka pottutten"
        else:
            msg = f"Playing {query} on {platform}"
            if lang == "ta":
                msg = f"{query} {platform}-la play panren"
        
        speak(msg, lang)
        print(f"✅ Media playing: {query} on {platform}")
    else:
        msg = f"Sorry, couldn't play {query} on {platform}"
        if lang == "ta":
            msg = f"{query} {platform}-la play panna mudiyala"
        speak(msg, lang)

def clipboard_action(action: str, target_app: str, lang: str = "en"):
    """Handle clipboard operations [web:150][web:156][web:157]"""
    print(f"📋 Clipboard action: {action} -> {target_app}")
    
    try:
        if action == "copy_paste":
            # Copy current generated code and paste in target app
            if ai_config.last_generated_code:
                print("📋 Copying generated code to clipboard...")
                pyperclip.copy(ai_config.last_generated_code)
                
                msg = "Code copied to clipboard"
                if lang == "ta":
                    msg = "Code clipboard-la copy pannitten"
                speak(msg, lang)
                
                time.sleep(1)
                
                # Open target app and paste
                app_path = app_discovery.find_app(target_app)
                if app_path:
                    success = app_discovery.launch_app(app_path)
                    if success:
                        time.sleep(2)  # Wait for app to open
                        
                        # Paste using keyboard shortcut [web:157]
                        pyautogui.hotkey('ctrl', 'v')
                        
                        msg = f"Code pasted in {target_app}"
                        if lang == "ta":
                            msg = f"Code {target_app}-la paste pannitten"
                        speak(msg, lang)
                        print(f"✅ Code pasted in {target_app}")
                    else:
                        msg = f"Couldn't open {target_app}"
                        if lang == "ta":
                            msg = f"{target_app} thorakka mudiyala"
                        speak(msg, lang)
                else:
                    msg = f"Couldn't find {target_app}"
                    if lang == "ta":
                        msg = f"{target_app} kandupidikka mudiyala"
                    speak(msg, lang)
            else:
                msg = "No code to copy"
                if lang == "ta":
                    msg = "Copy panna code illai"
                speak(msg, lang)
        
        elif action == "paste":
            # Just paste whatever is in clipboard
            app_path = app_discovery.find_app(target_app)
            if app_path:
                success = app_discovery.launch_app(app_path)
                if success:
                    time.sleep(2)
                    pyautogui.hotkey('ctrl', 'v')
                    
                    msg = f"Pasted in {target_app}"
                    if lang == "ta":
                        msg = f"{target_app}-la paste pannitten"
                    speak(msg, lang)
                    print(f"✅ Pasted in {target_app}")
        
        elif action == "copy":
            # Copy generated code to clipboard
            if ai_config.last_generated_code:
                pyperclip.copy(ai_config.last_generated_code)
                
                msg = "Code copied to clipboard"
                if lang == "ta":
                    msg = "Code clipboard-la copy pannitten"
                speak(msg, lang)
                print("✅ Code copied to clipboard")
            else:
                msg = "No code to copy"
                if lang == "ta":
                    msg = "Copy panna code illai"
                speak(msg, lang)
                
    except Exception as e:
        print(f"❌ Clipboard error: {e}")
        msg = "Clipboard operation failed"
        if lang == "ta":
            msg = "Clipboard operation fail aachu"
        speak(msg, lang)

def system_control(action: str, lang: str = "en"):
    """System control function"""
    print(f"🔧 System control: {action}")
    
    app_path = app_discovery.find_app(action)
    
    if app_path and app_path.startswith("system:"):
        action_messages = {
            "shutdown": ("Shutting down computer in 5 seconds", "5 seconds-la computer shutdown aagum"),
            "restart": ("Restarting computer in 5 seconds", "5 seconds-la computer restart aagum"), 
            "reboot": ("Rebooting computer in 5 seconds", "5 seconds-la computer reboot aagum"),
            "sleep": ("Putting computer to sleep", "Computer-a sleep mode-la pottu tharren"),
            "hibernate": ("Hibernating computer", "Computer-a hibernate panren"),
            "logout": ("Logging out", "Logout panren"),
            "lock": ("Locking computer", "Computer-a lock panren")
        }
        
        if action in action_messages:
            en_msg, ta_msg = action_messages[action]
            msg = ta_msg if lang == "ta" else en_msg
            speak(msg, lang)
        
        success = app_discovery.launch_app(app_path)
        
        if not success:
            msg = "Failed to execute system command"
            if lang == "ta":
                msg = "System command execute aagala"
            speak(msg, lang)
    else:
        msg = f"Unknown system action: {action}"
        if lang == "ta":
            msg = f"{action} theriyala"
        speak(msg, lang)

def close_app(app_name: str, lang: str = "en"):
    """Close application"""
    process_name = app_discovery.process_map.get(app_discovery.clean_app_name(app_name))
    
    if process_name:
        try:
            subprocess.run(["taskkill", "/f", "/im", process_name], check=True, capture_output=True)
            msg = f"Closed {app_name}"
            if lang == "ta":
                msg = f"{app_name} mudditten"
            speak(msg, lang)
        except subprocess.CalledProcessError:
            msg = f"{app_name} is not running"
            if lang == "ta":
                msg = f"{app_name} odala"
            speak(msg, lang)
    else:
        msg = f"Don't know how to close {app_name}"
        if lang == "ta":
            msg = f"{app_name} mudda theriyala"
        speak(msg, lang)

def search_web(query: str, lang: str = "en"):
    """Enhanced web search"""
    try:
        print(f"🔍 Searching Google for: '{query}'")
        
        encoded_query = urllib.parse.quote_plus(query.strip())
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        print(f"🌐 Opening: {search_url}")
        webbrowser.open(search_url)
        
        msg = f"Here's what I found for {query}"
        if lang == "ta":
            msg = f"{query} pathi Google-la search pannitten"
        speak(msg, lang)
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        msg = "Sorry, couldn't perform the search"
        if lang == "ta":
            msg = "Search panna mudiyala"
        speak(msg, lang)

def general_chat(query: str, lang: str = "en"):
    """Enhanced chat with code generation support"""
    query_lower = query.lower()
    
    # Tamil greetings
    if any(greeting in query_lower for greeting in ["vanakkam", "hai", "hello"]):
        msg = "Hello! How can I help you?"
        if lang == "ta":
            msg = "Vanakkam! Enna help venum?"
        speak(msg, lang)
        return
    
    if any(phrase in query_lower for phrase in ["how are you", "epdi irukka"]):
        msg = "I'm doing well, thank you!"
        if lang == "ta":
            msg = "Naan nalla iruken, nandri!"
        speak(msg, lang)
        return
    
    if any(thanks in query_lower for thanks in ["thank you", "thanks", "nandri"]):
        msg = "You're welcome! Happy to help!"
        if lang == "ta":
            msg = "Paravala! Vera enna help venum?"
        speak(msg, lang)
        return
    
    # Check if it's a code generation request
    code_keywords = ["generate code", "write code", "create program", "code for", "program for", "script for"]
    is_code_request = any(keyword in query_lower for keyword in code_keywords)
    
    if is_code_request:
        # Use reasoning model for code generation
        code_prompt = f"Generate clean, well-commented code for: {query}\n\nProvide only the code with comments, no explanations:"
        response = query_ollama_smart(code_prompt, query, "reasoning")
        
        if response and ("def " in response or "import " in response or "class " in response):
            ai_config.last_generated_code = response
            msg = "Code generated! Say 'copy code and paste in vscode' to use it."
            if lang == "ta":
                msg = "Code generate pannitten! 'Copy code and paste in vscode' sollungal."
            speak(msg, lang)
            print("💾 Generated code stored for clipboard operations")
            print(f"📝 Generated code:\n{response}")
        else:
            speak(response, lang)
    else:
        # Regular chat
        context_prompt = f"Answer briefly and helpfully: {query}"
        response = query_ollama_smart(context_prompt, query, "fast")
        
        if response and "failed" not in response.lower():
            speak(response, lang)
        else:
            msg = "I'm not sure how to help with that"
            if lang == "ta":
                msg = "Adhu pathi enakku theriyala"
            speak(msg, lang)

# --- Tool Registry ---
TOOLS = {
    "open_app": open_app,
    "close_app": close_app,
    "search_web": search_web,
    "system_control": system_control,
    "play_media": play_media,
    "clipboard_action": clipboard_action,
    "general_chat": general_chat
}

def execute_command(intent: dict, lang: str = "en"):
    """Enhanced command execution with media and clipboard support"""
    try:
        tool_name = intent.get("tool")
        parameters = intent.get("parameters", {})
        
        if tool_name in TOOLS:
            tool_function = TOOLS[tool_name]
            if 'lang' in tool_function.__code__.co_varnames:
                parameters['lang'] = lang
            tool_function(**parameters)
        else:
            general_chat(query="I'm not sure what you mean", lang=lang)
    except Exception as e:
        print(f"❌ Execution error: {e}")
        msg = "Sorry, I had an error processing that"
        if lang == "ta":
            msg = "Error aachu, mannichanga"
        speak(msg, lang)

def get_system_status():
    """System status for debugging"""
    is_online = check_internet_connection()
    available_models = ai_config.get_available_models()
    
    return {
        "connectivity": "Online" if is_online else "Offline",
        "available_models": available_models,
        "manual_apps": len(app_discovery.manual_app_paths),
        "web_apps": len(app_discovery.web_apps),
        "system_commands": len(app_discovery.system_commands),
        "media_platforms": len(app_discovery.media_platforms),
        "discovered_apps": len(app_discovery.installed_apps),
        "last_generated_code": bool(ai_config.last_generated_code)
    }

if __name__ == "__main__":
    print("🧪 Testing Enhanced Media Control & Clipboard System")
    status = get_system_status()
    print(f"Manual apps: {status['manual_apps']}")
    print(f"Web apps: {status['web_apps']}")
    print(f"System commands: {status['system_commands']}")
    print(f"Media platforms: {status['media_platforms']}")
    print(f"Registry apps: {status['discovered_apps']}")
    
    # Test media platforms
    print(f"\n🎵 Available Media Platforms:")
    for platform, info in app_discovery.media_platforms.items():
        print(f"  {platform}: {info['base_url']}")
    
    # Test clipboard functionality
    print(f"\n📋 Clipboard Features:")
    print(f"  - Code generation and storage")
    print(f"  - Automatic app opening and pasting")
    print(f"  - VS Code and Notepad support")
    
    print(f"\n✅ Enhanced system ready!")
