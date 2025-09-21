# app_automation.py

import webbrowser
# Import the speak function from the new tts.py file
from tts import speak

def search_youtube(query: str):
    """
    Searches YouTube by constructing and opening a direct search URL.
    This method is fast and reliable.
    """
    try:
        # Replace spaces in the query with '+' for the URL
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        speak(f"Searching YouTube for {query}")
        return True
    except Exception as e:
        speak(f"Failed to search YouTube: {e}")
        return False
    