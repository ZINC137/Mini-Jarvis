import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import requests
from google import genai
from gtts import gTTS
import os
import sys
import time

try:
    import vlc
    USE_VLC = True
except ImportError:
    USE_VLC = False

# ── Configuration ─────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "<Your Gemini Key Here>")
NEWS_API_KEY   = os.getenv("NEWS_API_KEY",   "<Your NewsAPI Key Here>")

if "<Your" in GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY env variable or paste your key above.")

# ── Gemini client ──────────────────────────────────────────────────────────────
client = genai.Client(api_key=GEMINI_API_KEY)

# ── Recogniser & offline TTS engine ──────────────────────────────────────────
recognizer = sr.Recognizer()
engine     = pyttsx3.init()

# ── Speech ────────────────────────────────────────────────────────────────────
def speak(text: str) -> None:
    print(f"[Jarvis] {text}")
    try:
        tts = gTTS(text, lang='en', tld='com')
        tts.save("temp.mp3")
        if USE_VLC:
            player = vlc.MediaPlayer("temp.mp3")
            player.rate = 1.4
            player.play()
            time.sleep(1)
            while player.is_playing():
                time.sleep(0.1)
            player.stop()
        else:
            if sys.platform == "darwin":
                os.system("afplay temp.mp3 -r 1.4")
            elif sys.platform == "win32":
                os.system("start /wait temp.mp3")
            else:
                os.system("ffplay -nodisp -autoexit temp.mp3 2>/dev/null")
        os.remove("temp.mp3")
    except Exception:
        engine.setProperty('rate', 200)
        engine.say(text)
        engine.runAndWait()


# ── AI processing (Gemini) ────────────────────────────────────────────────────
def ai_process(command: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"You are Jarvis, a concise voice assistant. Answer in under 3 sentences.\n\nUser: {command}"
    )
    return response.text.strip()


# ── Command processing ────────────────────────────────────────────────────────
SITE_MAP = {
    "open google":   "https://google.com",
    "open facebook": "https://facebook.com",
    "open youtube":  "https://youtube.com",
    "open linkedin": "https://linkedin.com",
    "open github":   "https://github.com",
    "open twitter":  "https://twitter.com",
    "open reddit":   "https://reddit.com",
}

def process_command(command: str) -> None:
    c = command.strip().lower()

    if any(word in c for word in ("exit", "quit", "stop", "goodbye", "bye")):
        speak("Goodbye Sir. Have a great day!")
        sys.exit(0)

    for phrase, url in SITE_MAP.items():
        if phrase in c:
            speak(f"Opening {phrase.split()[-1].capitalize()}")
            webbrowser.open(url)
            return

    if c.startswith("play"):
        parts = c.split(maxsplit=1)
        song  = parts[1] if len(parts) > 1 else ""
        if song in musicLibrary.music:
            speak(f"Playing {song}")
            webbrowser.open(musicLibrary.music[song])
        else:
            speak(f"Sorry, I don't have {song} in the library.")
        return

    if "news" in c:
        if "<Your" in NEWS_API_KEY:
            speak("News API key is not configured.")
            return
        try:
            r = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "in", "pageSize": 5, "apiKey": NEWS_API_KEY},
                timeout=5,
            )
            r.raise_for_status()
            articles = r.json().get("articles", [])
            speak(f"Here are the top {len(articles)} headlines.")
            for i, article in enumerate(articles, 1):
                speak(f"{i}. {article['title']}")
        except Exception as e:
            speak("Sorry, I couldn't fetch the news right now.")
            print(f"[News error] {e}")
        return

    speak("Let me think about that.")
    reply = ai_process(command)
    speak(reply)


# ── Listen helper ─────────────────────────────────────────────────────────────
def listen(prompt: str = "Listening...", timeout: int = 5, phrase_limit: int = 8) -> str | None:
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print(f"[Mic] {prompt}")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[Listen error] {e}")
            return None


# ── Main loop ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    speak("Initialising Jarvis. Say Jarvis to activate me.")

    while True:
        wake = listen(prompt="Waiting for wake word...", timeout=10, phrase_limit=3)
        if wake and "jarvis" in wake.lower():
            speak("Yes Sir?")
            command = listen(prompt="Awaiting command...", timeout=7, phrase_limit=10)
            if command:
                print(f"[Command] {command}")
                process_command(command)
            else:
                speak("I didn't catch that. Please try again.")