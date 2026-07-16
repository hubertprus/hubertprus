"""
Vertex Quant Core – Gemini AI Studio Client
Moduł integracji z Google AI Studio (Gemini API).
"""

import os
import json
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")

# Konfiguracja modelu
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# System prompt dla agenta Vertex Quant Core
VERTEX_QUANT_SYSTEM_PROMPT = """Jesteś wyspecjalizowanym agentem AI systemu Vertex Quant Core.
Twój twórca to programista i pasjonat technologii łączący architekturę Google Cloud,
automatyzację AI oraz produkcję muzyki elektronicznej.
Pomagasz w budowaniu platformy, generowaniu kodu, automatyzacji infrastruktury
oraz projektowaniu narzędzi wspierających produkcję muzyczną.
Odpowiadaj precyzyjnie, technicznie i po polsku, chyba że użytkownik pyta po angielsku."""


def clean_json_markdown(text: str) -> str:
    """Helper to strip markdown code blocks and parse raw JSON text safely."""
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return raw


def get_gemini_client():
    """Inicjalizuje i zwraca skonfigurowany model Gemini."""
    if not GOOGLE_AI_API_KEY:
        raise ValueError(
            "Brak klucza GOOGLE_AI_API_KEY. "
            "Ustaw go w pliku .env: GOOGLE_AI_API_KEY=twój_klucz"
        )
    genai.configure(api_key=GOOGLE_AI_API_KEY)
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=VERTEX_QUANT_SYSTEM_PROMPT,
    )


def chat_with_gemini(message: str, history: Optional[list] = None) -> str:
    """
    Wysyła wiadomość do Gemini i zwraca odpowiedź tekstową.

    Args:
        message: Wiadomość użytkownika.
        history: Opcjonalna historia konwersacji w formacie
                 [{"role": "user"/"model", "parts": ["tekst"]}]

    Returns:
        Odpowiedź modelu jako string.
    """
    model = get_gemini_client()

    if history:
        chat_session = model.start_chat(history=history)
    else:
        chat_session = model.start_chat()

    response = chat_session.send_message(message)
    return response.text


def generate_music_sequence(
    genre: str,
    bpm: int = 128,
    steps: int = 16,
    scale: str = "minor",
    key: str = "A",
) -> dict:
    """
    Generuje sekwencję muzyczną (nuty/kroki) dla podanego gatunku przez Gemini.

    Args:
        genre: Gatunek muzyczny (np. "techno", "trance", "deep house").
        bpm:   Tempo w BPM.
        steps: Liczba kroków sekwencji (16 lub 32).
        scale: Skala muzyczna ("minor" / "major").
        key:   Tonacja (np. "A", "C#", "F").

    Returns:
        Słownik z sekwencją, parametrami i opisem.
    """
    model = get_gemini_client()

    prompt = f"""Wygeneruj sekwencję muzyczną w formacie JSON dla:
- Gatunek: {genre}
- Tempo: {bpm} BPM
- Liczba kroków: {steps}
- Skala: {scale}
- Tonacja: {key}

Zwróć TYLKO poprawny JSON (bez markdown, bez komentarzy) w następującym formacie:
{{
  "genre": "{genre}",
  "bpm": {bpm},
  "key": "{key}",
  "scale": "{scale}",
  "steps": {steps},
  "kick_pattern": [lista {steps} wartości 0 lub 1],
  "snare_pattern": [lista {steps} wartości 0 lub 1],
  "hihat_pattern": [lista {steps} wartości 0 lub 1],
  "bass_notes": [lista {steps} nut jako string lub null, np. "A2", null, "C3"],
  "lead_notes": [lista {steps} nut jako string lub null],
  "description": "krótki opis charakteru sekwencji"
}}"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Usuń ewentualne bloki markdown ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Zwróć odpowiedź tekstową jeśli JSON się nie udał
        return {"raw_response": raw, "error": "Nie udało się sparsować JSON"}


def analyze_audio_params(description: str) -> dict:
    """
    Analizuje i sugeruje parametry audio/syntezatora na podstawie opisu.

    Args:
        description: Opis dźwięku lub brzmienia (np. "ciepły bas techno z distortionem").

    Returns:
        Słownik z sugerowanymi parametrami syntezatora.
    """
    model = get_gemini_client()

    prompt = f"""Zaproponuj parametry syntezatora dla: "{description}"

Zwróć TYLKO poprawny JSON (bez markdown):
{{
  "oscillator": {{
    "waveform": "sawtooth|square|sine|triangle",
    "detune_cents": liczba od -100 do 100
  }},
  "filter": {{
    "type": "lowpass|highpass|bandpass",
    "cutoff_hz": liczba,
    "resonance": liczba od 0 do 1
  }},
  "envelope": {{
    "attack_ms": liczba,
    "decay_ms": liczba,
    "sustain": liczba od 0 do 1,
    "release_ms": liczba
  }},
  "effects": {{
    "reverb_mix": liczba od 0 do 1,
    "delay_ms": liczba,
    "distortion": liczba od 0 do 1
  }},
  "description": "opis brzmienia"
}}"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw, "error": "Nie udało się sparsować JSON"}


def analyze_fiverr_brief(brief: str) -> dict:
    """
    Analizuje brief z Fiverr przy użyciu Gemini 1.5 Flash.
    W przypadku braku klucza lub błędu, zwraca ustrukturyzowany fallback.
    """
    if not GOOGLE_AI_API_KEY:
        return mock_fiverr_brief_analysis(brief)

    try:
        # Możemy użyć dedykowanego modelu gemini-1.5-flash
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=VERTEX_QUANT_SYSTEM_PROMPT,
        )

        prompt = f"""Przeanalizuj poniższy brief zlecenia z Fiverr i wyodrębnij z niego kluczowe informacje.
Zwróć TYLKO i wyłącznie poprawny obiekt JSON (bez markdown ```json, bez komentarzy) o następującej strukturze:
{{
  "project_name": "krótka, chwytliwa nazwa projektu",
  "mood": "nastroje i emocje opisujące projekt (np. energetyczny, luksusowy, cyberpunkowy)",
  "style": "styl wizualny (np. neonowy, Cyber Gold, matowa czerń, 3D)",
  "scenes": [
    {{
      "scene_number": 1,
      "script": "sugerowana kwestia lektora lub napis na ekranie",
      "visual_prompt": "szczegółowy prompt wizualny dla modelu generatywnego Vertex AI w orientacji pionowej (vertical)"
    }}
  ]
}}

Brief do analizy:
"{brief}"
"""
        response = model.generate_content(prompt)
        cleaned = clean_json_markdown(response.text)
        return json.loads(cleaned)
    except Exception:
        return mock_fiverr_brief_analysis(brief)


def mock_fiverr_brief_analysis(brief: str) -> dict:
    """Zwraca ustrukturyzowany mock analizy briefu."""
    brief_lower = brief.lower()
    if "neon" in brief_lower or "pulse" in brief_lower or "energet" in brief_lower:
        name = "NeonPulse Energy Promo"
        mood = "Energetyczny, Cyberpunk, Futurystyczny"
        style = "Neon 3D / Cyber Gold"
    else:
        name = "Maszyna Viralowa Project"
        mood = "Luksusowy, Dynamiczny, Nowoczesny"
        style = "Obsidian Black / Cyber Gold Minimalist"

    return {
        "project_name": name,
        "mood": mood,
        "style": style,
        "scenes": [
            {
                "scene_number": 1,
                "script": "Kiedy noc przejmuje miasto, budzi się nowa energia. Czas na rewolucję.",
                "visual_prompt": "Futuristic 3D neon glowing can of beverage, cyber city background, volumetric lighting, luxury gold highlights, vertical 1080x1920"
            },
            {
                "scene_number": 2,
                "script": "Czysty, luksusowy impuls bez kompromisów. Poczuj to na własnej skórze.",
                "visual_prompt": "Macro shot of gold metallic can with water condensation droplets, cyber gold reflections, studio lighting, vertical 1080x1920"
            },
            {
                "scene_number": 3,
                "script": f"{name}. Twój nowy rytm nocy i dominacja w algorytmach.",
                "visual_prompt": "Abstract gold and black liquid ripple background with glowing neon text of logo, vertical 1080x1920"
            }
        ]
    }


def generate_reach_optimization(project_name: str, mood: str, style: str, scenes_summary: str) -> dict:
    """
    Generuje chwytliwe tytuły, viralowe opisy oraz tagi SEO dla TikToka/Shorts.
    """
    if not GOOGLE_AI_API_KEY:
        return mock_reach_optimization(project_name, mood, style)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=VERTEX_QUANT_SYSTEM_PROMPT,
        )

        prompt = f"""Wygeneruj viralowe parametry SEO (tytuł, opis, tagi) zoptymalizowane pod algorytmy TikToka i YouTube Shorts dla wideo o następujących cechach:
- Projekt: {project_name}
- Nastrój: {mood}
- Styl: {style}
- Scenariusz: {scenes_summary}

Zwróć TYLKO poprawny JSON (bez markdown):
{{
  "optimized_title": "chwytliwy tytuł z emoji i haczykiem",
  "optimized_description": "viralowy, angażujący opis ze sformułowaną korzyścią",
  "optimized_tags": "#tag1 #tag2 #tag3 ... oraz najpopularniejsze tagi"
}}
"""
        response = model.generate_content(prompt)
        cleaned = clean_json_markdown(response.text)
        return json.loads(cleaned)
    except Exception:
        return mock_reach_optimization(project_name, mood, style)


def mock_reach_optimization(project_name: str, mood: str, style: str) -> dict:
    """Zwraca ustrukturyzowany mock optymalizacji zasięgów."""
    return {
        "optimized_title": f"🚀 PRZEŁOM w marketingu! Poznaj {project_name}! 🔥",
        "optimized_description": f"Oto rewolucyjny spot stworzony w stylu {style}. Klimat {mood} rozbije bank i podbije algorytmy społecznościowe! Czy jesteś gotowy na nową jakość? Sprawdź to teraz!",
        "optimized_tags": "#viral #luxurytech #shorts #tiktok #marketing #vertexsong #cybergold #3d #hevc"
    }


def generate_audio_brief_text(project_name: str, mood: str, style: str) -> str:
    """
    Generuje tekst omawiający walory estetyczne i techniczne całego ekosystemu projektu.
    """
    if not GOOGLE_AI_API_KEY:
        return mock_audio_brief_text(project_name, mood, style)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=VERTEX_QUANT_SYSTEM_PROMPT,
        )

        prompt = f"""Napisz krótki, profesjonalny monolog lektora po polsku (maksymalnie 3 zdania, około 50 słów), który podsumowuje walory estetyczne i techniczne wygenerowanego projektu wideo.
Projekt: {project_name}
Nastrój: {mood}
Styl: {style}

Lektor powinien brzmieć luksusowo i dumnie, nawiązując do standardów Obsidian Black i Cyber Gold oraz formatu pionowego H.265.
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return mock_audio_brief_text(project_name, mood, style)


def mock_audio_brief_text(project_name: str, mood: str, style: str) -> str:
    """Zwraca ustrukturyzowany mock tekstu lektora."""
    return f"Witaj w Maszynie Viralowej Vertex Song. Przedstawiamy podsumowanie techniczne projektu {project_name}. Zaprojektowaliśmy unikalną identyfikację wizualną w klimacie {mood}, wykorzystując nowoczesną paletę barw opartą na głębokiej czerni Obsidian Black i technologicznym złocie Cyber Gold. Całość została wyrenderowana w standardzie H.265 w rozdzielczości pionowej dostosowanej pod algorytmy TikToka. Twój viralowy pakiet jest gotowy do publikacji."

